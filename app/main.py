"""
Production-Ready Honey-Pot Scam Detection API
AI-powered agentic system that detects scam messages and autonomously engages scammers.
"""
import os
import logging
import time
import json
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from logging.handlers import RotatingFileHandler

from app.config import get_settings, Settings
from app.models import (
    IncomingRequest, MessageResponse, ErrorResponse,
    HealthResponse, DetailedHealthResponse, MetricsResponse,
    SessionResponse, SessionData, ExtractedIntelligence,
    IntelligenceResponse, ScammerType
)
from app.middleware import (
    RequestIDMiddleware, RequestLoggingMiddleware,
    SecurityHeadersMiddleware, RateLimitMiddleware
)
from app.core.detection import detect_scam, detect_scam_llm, update_confidence
from app.core.agent import generate_reply, generate_exit_message, profile_scammer
from app.callback import send_final_callback
from app.core.extraction import extract_all_intelligence, merge_intelligence
from app.webhook_manager import EventManager
from app.db import client as db_client
from app.db import repository as db_repo


# -------------------------
# Logging Setup
# -------------------------

def setup_logging(settings: Settings):
    """Configure application logging with file rotation."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count
    )
    file_handler.setLevel(settings.log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={settings.log_level}, file={settings.log_file}")


# -------------------------
# Application Lifecycle
# -------------------------

# Track application start time for uptime metrics
app_start_time = time.time()

# In-memory session store
SESSIONS: Dict[str, SessionData] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    settings = get_settings()
    setup_logging(settings)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("=" * 60)

    # ── Neon DB Init ─────────────────────────────────────────
    if settings.db_enabled and settings.database_url:
        connected = db_client.init_db(settings.database_url)
        if connected:
            logger.info("[OK] Neon PostgreSQL connected and pool initialized")
            
            # Hydrate in-memory SESSIONS from DB
            try:
                db_sessions = db_repo.get_all_sessions()
                for row in db_sessions:
                    sid = row.pop("id")
                    
                    # Group intelligence fields
                    intel_data = {
                        "upiIds": row.pop("upi_ids", []) or [],
                        "phoneNumbers": row.pop("phone_numbers", []) or [],
                        "phishingLinks": row.pop("phishing_links", []) or [],
                        "bankAccounts": row.pop("bank_accounts", []) or [],
                        "suspiciousKeywords": row.pop("suspicious_keywords", []) or [],
                        "scannedText": row.pop("scanned_text", []) or []
                    }
                    
                    # Parse JSON fields if they are strings (psycopg2 RealDictCursor might return strings or dicts)
                    if isinstance(row.get("persona_history"), str):
                        row["persona_history"] = json.loads(row["persona_history"])
                    if isinstance(row.get("behavior_patterns"), str):
                        row["behavior_patterns"] = json.loads(row["behavior_patterns"])
                        
                    row["extracted"] = ExtractedIntelligence(**intel_data)
                    SESSIONS[sid] = SessionData(**row)
                
                logger.info(f"Loaded {len(SESSIONS)} existing sessions from database")
            except Exception as e:
                logger.error(f"Failed to hydrate sessions from DB: {e}")
                
        else:
            logger.warning("[FAIL] Neon PostgreSQL connection failed, running in-memory only.")
    else:
        logger.info("DB_ENABLED=false — running in memory-only mode (set DATABASE_URL + DB_ENABLED=true to persist)")

    # ── Start Session Cleanup Task ─────────────────────────────
    async def cleanup_expired_sessions():
        """Background task to auto-complete expired sessions."""
        while True:
            try:
                timeout_minutes = settings.session_timeout_minutes
                expired_count = 0
                
                for session_id, session in list(SESSIONS.items()):
                    if not session.completed and session.is_expired(timeout_minutes):
                        session.completed = True
                        session.update_activity()
                        expired_count += 1
                        logger.info(f"Auto-completed expired session: {session_id}")
                        
                        # Persist to DB
                        db_repo.upsert_session(session_id, session.dict())
                        db_repo.upsert_intelligence(session_id, session.extracted.dict())
                
                if expired_count > 0:
                    logger.info(f"Auto-completed {expired_count} expired sessions")
                    
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
            
            # Wait for next cleanup interval
            await asyncio.sleep(settings.session_cleanup_interval_minutes * 60)
    
    # Start the cleanup task
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    logger.info(f"Total sessions processed: {len(SESSIONS)}")
    
    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    db_client.close_db()


# -------------------------
# FastAPI Application
# -------------------------

app = FastAPI(
    title=get_settings().api_title,
    version=get_settings().api_version,
    description=get_settings().api_description,
    lifespan=lifespan,
    docs_url="/docs" if get_settings().debug else None,
    redoc_url="/redoc" if get_settings().debug else None,
)

logger = logging.getLogger(__name__)


# -------------------------
# Middleware Configuration
# -------------------------

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters - first added is outermost)
app.add_middleware(SecurityHeadersMiddleware)
if get_settings().rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=get_settings().rate_limit_requests)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# -------------------------
# Exception Handlers
# -------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"Validation error",
        extra={
            "request_id": request_id,
            "errors": exc.errors(),
        }
    )
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error",
            message="Invalid request data",
            detail=str(exc.errors()),
            request_id=request_id
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"http_{exc.status_code}",
            message=exc.detail,
            request_id=request_id
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unexpected error",
        extra={
            "request_id": request_id,
            "error": str(exc),
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            detail=str(exc) if get_settings().debug else None,
            request_id=request_id
        ).dict()
    )


# -------------------------
# Dependency Injection
# -------------------------

def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """Verify API key from request header."""
    settings = get_settings()
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# -------------------------
# Health Check Endpoints
# -------------------------

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.
    Returns simple status to verify the API is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with system information.
    Includes component status and basic metrics.
    """
    settings = get_settings()
    
    # Check components
    components = {
        "api": "healthy",
        "sessions": "healthy",
        "logging": "healthy",
        "database": "connected" if db_client.is_connected() else "memory-only",
    }
    
    # Basic metrics
    metrics = {
        "total_sessions": len(SESSIONS),
        "active_sessions": sum(1 for s in SESSIONS.values() if not s.completed),
        "uptime_seconds": int(time.time() - app_start_time),
    }
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        environment=settings.environment,
        components=components,
        metrics=metrics
    )


# -------------------------
# Metrics Endpoint
# -------------------------

@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Get application metrics.
    Returns statistics about sessions, messages, and scam detection.
    """
    total_sessions = len(SESSIONS)
    active_sessions = sum(1 for s in SESSIONS.values() if not s.completed)
    completed_sessions = sum(1 for s in SESSIONS.values() if s.completed)
    total_messages = sum(s.turns for s in SESSIONS.values())
    scams_detected = sum(1 for s in SESSIONS.values() if s.confidence < 0.5)
    
    # Calculate average confidence
    if SESSIONS:
        avg_confidence = sum(s.confidence for s in SESSIONS.values()) / len(SESSIONS)
    else:
        avg_confidence = 0.0
    
    return MetricsResponse(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        total_messages=total_messages,
        scams_detected=scams_detected,
        average_confidence=round(avg_confidence, 2),
        uptime_seconds=time.time() - app_start_time
    )


@app.get("/metrics/prometheus", tags=["Monitoring"])
async def get_prometheus_metrics():
    """
    Expose application metrics in Prometheus text exposition format.
    Can be scraped directly by Prometheus or viewed in the ops dashboard.
    """
    total_sessions = len(SESSIONS)
    active_sessions = sum(1 for s in SESSIONS.values() if not s.completed)
    completed_sessions = sum(1 for s in SESSIONS.values() if s.completed)
    total_messages = sum(s.turns for s in SESSIONS.values())
    scams_detected = sum(1 for s in SESSIONS.values() if s.confidence < 0.5)
    avg_confidence = (sum(s.confidence for s in SESSIONS.values()) / len(SESSIONS)) if SESSIONS else 0.0
    uptime_seconds = int(time.time() - app_start_time)

    metrics_text = "\n".join([
        "# HELP honeypot_total_sessions Total number of sessions tracked",
        "# TYPE honeypot_total_sessions gauge",
        f"honeypot_total_sessions {total_sessions}",
        "# HELP honeypot_active_sessions Currently active (in-progress) sessions",
        "# TYPE honeypot_active_sessions gauge",
        f"honeypot_active_sessions {active_sessions}",
        "# HELP honeypot_completed_sessions Sessions marked complete",
        "# TYPE honeypot_completed_sessions gauge",
        f"honeypot_completed_sessions {completed_sessions}",
        "# HELP honeypot_messages_total Total messages exchanged across sessions",
        "# TYPE honeypot_messages_total counter",
        f"honeypot_messages_total {total_messages}",
        "# HELP honeypot_scams_detected_total Scam conversations detected",
        "# TYPE honeypot_scams_detected_total counter",
        f"honeypot_scams_detected_total {scams_detected}",
        "# HELP honeypot_avg_confidence Average scam confidence (0-1)",
        "# TYPE honeypot_avg_confidence gauge",
        f"honeypot_avg_confidence {round(avg_confidence, 4)}",
        "# HELP honeypot_uptime_seconds Server uptime in seconds",
        "# TYPE honeypot_uptime_seconds gauge",
        f"honeypot_uptime_seconds {uptime_seconds}",
    ])

    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# -------------------------
# Geo Analytics Endpoint
# -------------------------

# Phone country-code -> (country code, country name) map for geo aggregation.
# Pairs with the frontend WorldThreatMap country positions table.
COUNTRY_PREFIXES = {
    "977": ("NP", "Nepal"), "880": ("BD", "Bangladesh"), "234": ("NG", "Nigeria"),
    "212": ("MA", "Morocco"), "254": ("KE", "Kenya"), "963": ("SY", "Syria"),
    "233": ("GH", "Ghana"), "91": ("IN", "India"), "92": ("PK", "Pakistan"),
    "94": ("LK", "Sri Lanka"), "55": ("BR", "Brazil"), "52": ("MX", "Mexico"),
    "63": ("PH", "Philippines"), "84": ("VN", "Vietnam"), "62": ("ID", "Indonesia"),
    "90": ("TR", "Turkey"), "27": ("ZA", "South Africa"), "20": ("EG", "Egypt"),
    "49": ("DE", "Germany"), "33": ("FR", "France"), "39": ("IT", "Italy"),
    "44": ("GB", "United Kingdom"), "34": ("ES", "Spain"), "48": ("PL", "Poland"),
    "86": ("CN", "China"), "81": ("JP", "Japan"), "82": ("KR", "South Korea"),
    "66": ("TH", "Thailand"), "60": ("MY", "Malaysia"), "65": ("SG", "Singapore"),
    "61": ("AU", "Australia"), "1": ("US", "United States"), "7": ("RU", "Russia"),
}


def _resolve_country(phone: str):
    """Return (country_code, country_name) for a phone number, defaulting to India."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    for prefix_len in (3, 2, 1):
        prefix = digits[:prefix_len]
        if prefix in COUNTRY_PREFIXES:
            return COUNTRY_PREFIXES[prefix]
    return ("IN", "India")


@app.get("/analytics/geo", tags=["Analytics"])
async def get_geo_analytics():
    """
    Country-level threat distribution derived from phone numbers
    extracted across all honeypot sessions.
    """
    distribution = {}
    total_messages = sum(s.turns for s in SESSIONS.values())
    total_scams = sum(1 for s in SESSIONS.values() if s.confidence < 0.5)

    for session in SESSIONS.values():
        phones = session.extracted.phoneNumbers or []
        countries = {_resolve_country(p) for p in phones}
        if not countries:
            continue
        is_scam = session.confidence < 0.5
        for code, country in countries:
            entry = distribution.setdefault(
                code,
                {"code": code, "country": country, "messages": 0, "scams": 0},
            )
            entry["messages"] += session.turns
            if is_scam:
                entry["scams"] += 1

    for entry in distribution.values():
        ratio = entry["scams"] / entry["messages"] if entry["messages"] else 0
        if ratio >= 0.75:
            entry["risk"] = "critical"
        elif ratio >= 0.5:
            entry["risk"] = "high"
        elif ratio >= 0.25:
            entry["risk"] = "medium"
        else:
            entry["risk"] = "low"

    return {
        "distribution": list(distribution.values()),
        "total_messages": total_messages,
        "total_scams": total_scams,
    }


# -------------------------
# Intelligence Aggregation Endpoint
# -------------------------

@app.get("/intelligence", response_model=IntelligenceResponse, tags=["Intelligence"])
async def get_intelligence(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Get aggregated intelligence from all sessions.
    
    Returns all extracted scammer data including:
    - UPI IDs
    - Phone numbers
    - Phishing links
    - Suspicious keywords
    
    Requires API key authentication.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        f"Intelligence aggregation requested",
        extra={"request_id": request_id}
    )
    
    # Aggregate all intelligence from all sessions
    all_upi_ids = []
    all_phone_numbers = []
    all_phishing_links = []
    all_bank_accounts = []
    all_keywords = []
    sessions_with_data = []
    scam_count = 0
    
    for session_id, session_data in SESSIONS.items():
        extracted = session_data.extracted
        
        # Check if session has any extracted intelligence
        has_intelligence = (
            extracted.upiIds or 
            extracted.phoneNumbers or 
            extracted.phishingLinks or 
            extracted.bankAccounts or 
            extracted.suspiciousKeywords
        )
        
        if has_intelligence:
            sessions_with_data.append({
                "session_id": session_id,
                "confidence": session_data.confidence,
                "turns": session_data.turns,
                "completed": session_data.completed,
                "scammer_type": session_data.scammer_type,
                "scammer_profile": session_data.scammer_profile,
                "extracted": extracted.dict(),
                "created_at": session_data.created_at.isoformat() if session_data.created_at else None,
            })
            
            # Aggregate all data
            all_upi_ids.extend(extracted.upiIds)
            all_phone_numbers.extend(extracted.phoneNumbers)
            all_phishing_links.extend(extracted.phishingLinks)
            all_bank_accounts.extend(extracted.bankAccounts)
            all_keywords.extend(extracted.suspiciousKeywords)
        
        # Count scam sessions (confidence < 1.0)
        if session_data.confidence < 1.0:
            scam_count += 1
    
    # Create aggregated intelligence with unique values
    aggregated = ExtractedIntelligence(
        upiIds=list(set(all_upi_ids)),  # Remove duplicates
        phoneNumbers=list(set(all_phone_numbers)),
        phishingLinks=list(set(all_phishing_links)),
        bankAccounts=list(set(all_bank_accounts)),
        suspiciousKeywords=list(set(all_keywords))
    )
    
    # Count unique items
    unique_counts = {
        "unique_upi_ids": len(aggregated.upiIds),
        "unique_phone_numbers": len(aggregated.phoneNumbers),
        "unique_phishing_links": len(aggregated.phishingLinks),
        "unique_bank_accounts": len(aggregated.bankAccounts),
        "unique_keywords": len(aggregated.suspiciousKeywords),
        "total_unique_items": (
            len(aggregated.upiIds) + 
            len(aggregated.phoneNumbers) + 
            len(aggregated.phishingLinks) + 
            len(aggregated.bankAccounts) + 
            len(aggregated.suspiciousKeywords)
        )
    }
    
    logger.info(
        f"Intelligence aggregation completed",
        extra={
            "request_id": request_id,
            "total_sessions": len(SESSIONS),
            "sessions_with_intelligence": len(sessions_with_data),
            "unique_items": unique_counts["total_unique_items"]
        }
    )
    
    return IntelligenceResponse(
        total_sessions=len(SESSIONS),
        scam_sessions=scam_count,
        aggregated_intelligence=aggregated,
        unique_counts=unique_counts,
        sessions_with_intelligence=sessions_with_data
    )


# -------------------------
# Debug Endpoint (for organizer testing)
# -------------------------

@app.post("/honeypot/message/debug", tags=["Debug"])
async def debug_message(request: Request, api_key: str = Depends(verify_api_key)):
    """Debug endpoint to see exactly what organizers are sending."""
    try:
        body = await request.json()
        logger.info(f"[INFO] Received JSON keys: {list(body.keys())}")
        logger.info(f"[INFO] Received body: {json.dumps(body, indent=2)}")
        return {
            "status": "debug_success",
            "received": body,
            "message": "This is a debug endpoint. Use /honeypot/message for actual testing."
        }
    except Exception as e:
        logger.error(f"DEBUG - Error: {str(e)}")
        return {"status": "debug_error", "error": str(e)}


# -------------------------
# Main Honeypot Endpoint
# -------------------------

@app.get("/session/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def get_session_details(session_id: str, x_api_key: str = Depends(verify_api_key)):
    """Get detailed information about a specific session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = SESSIONS[session_id]
    return SessionResponse(
        status="success",
        session_id=session_id,
        data=session
    )


@app.post("/honeypot/message", tags=["Honeypot"])
async def handle_message(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Process incoming scam message and generate intelligent response.
    
    ORGANIZER-COMPATIBLE ENDPOINT
    Returns simple format: {"status": "success", "reply": "..."}
    
    This endpoint:
    1. Detects scam indicators in the message
    2. Extracts intelligence (UPI IDs, phone numbers, URLs)
    3. Updates confidence score
    4. Generates appropriate response
    5. Sends callback when scam is confirmed
    
    Requires valid API key in x-api-key header.
    """
    settings = get_settings()
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Get raw body for debugging
    try:
        raw_body = await request.body()
        logger.info(f"Raw request body: {raw_body.decode('utf-8')[:500]}")
    except Exception as e:
        logger.error(f"Could not read raw body: {e}")
    
    
    # Parse and validate payload - ULTRA PERMISSIVE for organizer compatibility
    try:
        body_json = await request.json()
        logger.info(f"Received JSON keys: {list(body_json.keys())}")
        
        # Extract fields manually (permissive)
        session_id = body_json.get("sessionId") or body_json.get("session_id") or "unknown"
        
        # Handle message field
        message_obj = body_json.get("message", {})
        if isinstance(message_obj, dict):
            message_text = message_obj.get("text", "")
            # Extract sender information if available
            sender_info = {
                'sender_email': message_obj.get("sender_email"),
                'sender_phone': message_obj.get("sender_phone"),
                'sender_profile': message_obj.get("sender_profile"),
                'sender_name': message_obj.get("sender_name")
            }
        else:
            message_text = str(message_obj)
            sender_info = {}
        
        # Validate we have minimum required data
        if not message_text or not message_text.strip():
            raise HTTPException(status_code=400, detail="Message text is required")
            
        logger.info(f"Extracted - session_id: {session_id}, message: {message_text[:50]}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
    
    logger.info(
        f"Processing message",
        extra={
            "request_id": request_id,
            "session_id": session_id,
            "message_length": len(message_text),
        }
    )
    
    # -------------------------
    # Create or load session
    # -------------------------
    if session_id not in SESSIONS:
        logger.info(f"Creating new session", extra={"session_id": session_id})
        SESSIONS[session_id] = SessionData(
            confidence=1.0,
            turns=0,
            completed=False,
            extracted=ExtractedIntelligence(),
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
    
    session = SESSIONS[session_id]
    session.update_activity()
    
    # Add message to history for pattern detection (keep last 10)
    session.message_history.append(message_text)
    if len(session.message_history) > 10:
        session.message_history = session.message_history[-10:]
    
    # -------------------------
    # Enhanced Scam Detection (LLM-only with sender context)
    # -------------------------
    detection = detect_scam_llm(
        message_text,
        message_history=session.message_history[:-1],  # Exclude current message
        sender_info=sender_info
    )
    
    # -------------------------
    # PASS-THROUGH MODE: If NOT scam, let user handle it
    # We only pass through if it's the first message AND it's not a scam.
    # If the agent is already engaged (turns > 0), we must keep engaging!
    # -------------------------
    is_already_engaged = session.turns > 0
    if not detection["is_scam"] and not is_already_engaged:
        logger.info(
            f"No scam detected - passing through to user",
            extra={
                "session_id": session_id,
                "message_preview": message_text[:50] + "..." if len(message_text) > 50 else message_text,
            }
        )
        
        return MessageResponse(
            status="success",
            reply=None,  # No agent reply - user handles this
            confidence=1.0,
            session_id=session_id,
            turns=session.turns,
            agent_engaged=False,
            scam_detected=False
        )
    
    # -------------------------
    # SCAM DETECTED: Agent takes control
    # -------------------------
    logger.warning(
        f"Scam indicators detected - agent engaging",
        extra={
            "session_id": session_id,
            "flags": detection["flags"],
            "detection_confidence": detection["confidence"],
            "repetition": detection.get("repetition", {}),
            "escalation": detection.get("escalation", {}),
        }
    )
    
    # Update behavior patterns
    if "urgency" in detection["flags"]:
        session.behavior_patterns["urgency"] = session.behavior_patterns.get("urgency", 0) + 1
    if "threat" in detection["flags"]:
        session.behavior_patterns["threat"] = session.behavior_patterns.get("threat", 0) + 1
    
    # Trigger Aggression Webhook
    if detection.get("escalation"):
        EventManager.notify_aggression_detected(session_id, detection["escalation"])
    
    # Update session confidence with enhanced decay
    session.confidence = update_confidence(
        session.confidence,
        detection["flags"],
        repetition_data=detection.get("repetition"),
        escalation_data=detection.get("escalation")
    )
    
    # Extract intelligence
    new_intelligence = extract_all_intelligence(message_text, detection["flags"])
    
    # Check if NEW text-based intelligence was found
    has_new_intel = any(
        (len(new_intelligence.get(k, [])) > 0 and 
         any(item not in session.extracted.dict().get(k, []) for item in new_intelligence[k]))
        for k in ["upiIds", "phoneNumbers", "phishingLinks", "bankAccounts"]
    )
    
    if has_new_intel:
        EventManager.notify_intel_extracted(session_id, new_intelligence)
        
    session.extracted = ExtractedIntelligence(
        **merge_intelligence(session.extracted.dict(), new_intelligence)
    )
    
    session.turns += 1
    
    # -------------------------
    # Scammer Profiling (Experimental)
    # -------------------------
    # Profile the scammer after a few turns to understand their tactics
    if session.turns >= 2 and session.scammer_type == ScammerType.UNKNOWN:
        try:
            scammer_type, profile = profile_scammer(session.message_history)
            if scammer_type != ScammerType.UNKNOWN:
                session.scammer_type = scammer_type
                session.scammer_profile = profile
                logger.info(
                    f"Scammer profiled successfully",
                    extra={
                        "session_id": session_id,
                        "type": scammer_type.value,
                        "profile": profile
                    }
                )
        except Exception as e:
            logger.error(f"Failed to profile scammer: {e}")
    
    # -------------------------
    # Intelligent Exit Strategy
    # -------------------------
    def should_exit() -> tuple[bool, str]:
        """Determine if agent should exit conversation."""
        # Exit condition 1: Confidence threshold reached (False positive / Safe user)
        if session.confidence <= settings.exit_confidence_threshold:
            return True, "confidence_threshold"
        
        # Exit condition 2: Escalation detected (Agent performs safe exit to avoid harassment)
        if detection.get("escalation", {}).get("is_escalating", False):
            return True, "escalation_detected"
            
        # Hard safety limit to prevent absolute infinite loops with other bots
        if session.turns >= 50:
            return True, "max_turns_reached"
        
        # Otherwise, stay engaged indefinitely to extract max intelligence
        return False, None
    
    exit_needed, exit_reason = should_exit()
    
    if exit_needed and not session.completed:
        logger.info(
            f"Exit condition met, ending conversation",
            extra={
                "session_id": session_id,
                "exit_reason": exit_reason,
                "final_confidence": session.confidence,
                "turns": session.turns,
                "intelligence_items": (
                    len(session.extracted.upiIds) +
                    len(session.extracted.phoneNumbers) +
                    len(session.extracted.phishingLinks) +
                    len(session.extracted.bankAccounts) +
                    len(session.extracted.scannedText)
                ),
            }
        )
        
        # Send final callback (uses settings defaults)
        send_final_callback(session_id, session.dict())
        
        # Also trigger real-time completion webhook
        EventManager.notify_session_completed(session_id, session.dict())
        
        session.completed = True
        
        # Generate persona-appropriate exit message
        reply = generate_exit_message(
            current_persona=session.current_persona,
            extracted_intelligence=session.extracted.dict()
        )
    else:
        # Generate intelligent reply with persona switching
        try:
            # Extract imageData if present
            image_data = None
            if isinstance(body_json.get("message"), dict):
                image_data = body_json["message"].get("imageData")
            
            # Generate intelligent reply with persona switching and vision support
            reply, new_persona, scanned_intel, should_exit = generate_reply(
                confidence=session.confidence,
                last_message=message_text,
                current_persona=session.current_persona,
                extracted_intelligence=session.extracted.dict(),
                image_data=image_data,
                message_history=session.message_history
            )
            
            # If pressure detected or exit mode triggered, mark session for completion
            if should_exit:
                session.completed = True
                logger.warning(
                    f"Session marked for exit due to pressure or exit mode",
                    extra={"session_id": session_id, "should_exit": should_exit}
                )
            
            # Merge scanned intelligence if any
            if scanned_intel:
                session.extracted.scannedText = list(set(session.extracted.scannedText + scanned_intel))
                # Trigger webhook for intel-from-image
                EventManager.notify_intel_extracted(session_id, {"scannedText": scanned_intel})
            
            # Track persona changes
            if new_persona != session.current_persona:
                session.persona_history.append({
                    "from": session.current_persona,
                    "to": new_persona,
                    "turn": session.turns,
                    "confidence": session.confidence
                })
                session.current_persona = new_persona
                
        except Exception as e:
            logger.error(
                f"Error generating reply",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            reply = "I'm not sure I understand. Can you explain more?"
    
    logger.info(
        f"Message processed successfully - agent engaged",
        extra={
            "session_id": session_id,
            "confidence": session.confidence,
            "turns": session.turns,
            "completed": session.completed,
            "current_persona": session.current_persona,
        }
    )
    
    # ── Write-Through DB Persistence ───────────────────────────
    # Persist session state and intelligence to Neon (no-op if DB not connected)
    db_repo.upsert_session(session_id, session.dict())
    db_repo.upsert_intelligence(session_id, session.extracted.dict())
    db_repo.save_message(session_id, "scammer", message_text)
    if reply:
        db_repo.save_message(session_id, "agent", reply)

    # Return full response (includes organizer-compatible status + reply AND test-compatible fields)
    return MessageResponse(
        status="success",
        reply=reply,
        confidence=session.confidence,
        session_id=session_id,
        turns=session.turns,
        agent_engaged=True,
        scam_detected=True
    )


# -------------------------
# Admin Endpoints (Optional)
# -------------------------

@app.get("/sessions", tags=["Admin"])
async def list_sessions(
    api_key: str = Depends(verify_api_key),
    limit: int = 100
):
    """
    List all sessions.
    Requires valid API key.
    """
    # Convert to list format
    sessions_list = [
        {"session_id": sid, "data": data.dict()}
        for sid, data in list(SESSIONS.items())[:limit]
    ]
    
    return {
        "total": len(SESSIONS),
        "returned": len(sessions_list),
        "sessions": sessions_list
    }


@app.get("/sessions/completed", tags=["Admin"])
async def get_completed_sessions(
    api_key: str = Depends(verify_api_key),
    since: str = ""
):
    """
    Retrieve a list of completed scam sessions.
    Optionally filter by 'since' timestamp to get only recently completed sessions.
    """
    from datetime import datetime
    completed_sessions = []
    for session_id, session in SESSIONS.items():
        if session.completed:
            if since:
                since_dt = datetime.fromisoformat(since)
                # Handle timezone mismatch: make both naive for comparison
                if session.last_activity:
                    last_act = session.last_activity
                    if last_act.tzinfo is not None and since_dt.tzinfo is None:
                        last_act = last_act.replace(tzinfo=None)
                    elif last_act.tzinfo is None and since_dt.tzinfo is not None:
                        since_dt = since_dt.replace(tzinfo=None)
                    if last_act < since_dt:
                        continue
            # Add session_id to the session data for the response
            session_dict = session.dict()
            session_dict["session_id"] = session_id
            completed_sessions.append(session_dict)
    return completed_sessions


@app.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Admin"])
async def get_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get session details by ID.
    Requires valid API key.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = []
    if get_settings().db_enabled:
        messages = db_repo.get_messages(session_id)
        
    return SessionResponse(
        session_id=session_id,
        data=SESSIONS[session_id],
        messages=messages
    )


# -------------------------
# Session Lifecycle (manual end / delete)
# -------------------------

@app.post("/sessions/{session_id}/complete", tags=["Admin"])
async def complete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually end a session. Finalizes the conversation, persists the extracted
    intelligence (which flows into the Intel Hub aggregation) and fires the
    completion callback + webhook. Idempotent: completing twice is a no-op.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    session = SESSIONS[session_id]
    if not session.completed:
        session.completed = True
        session.update_activity()

        send_final_callback(session_id, session.dict())
        EventManager.notify_session_completed(session_id, session.dict())

        # Persist finalized state + intelligence
        db_repo.upsert_session(session_id, session.dict())
        db_repo.upsert_intelligence(session_id, session.extracted.dict())
        logger.info(f"Session manually completed: {session_id}")

    return {
        "status": "success",
        "session_id": session_id,
        "completed": session.completed,
        "intelligence_saved": len(session.extracted.dict()) > 0,
    }


@app.delete("/sessions/completed", tags=["Admin"])
async def delete_completed_sessions(api_key: str = Depends(verify_api_key)):
    """
    Delete all completed sessions (logs + intelligence + messages).
    """
    deleted = []
    for session_id in list(SESSIONS.keys()):
        if SESSIONS[session_id].completed:
            deleted.append(session_id)
            del SESSIONS[session_id]
            db_repo.delete_session(session_id)

    logger.info(f"Deleted {len(deleted)} completed sessions: {deleted}")
    return {"status": "success", "deleted": len(deleted), "session_ids": deleted}


@app.delete("/sessions", tags=["Admin"])
async def delete_all_sessions(api_key: str = Depends(verify_api_key)):
    """
    Delete every session log (logs + intelligence + messages).
    """
    deleted = list(SESSIONS.keys())
    SESSIONS.clear()
    for session_id in deleted:
        db_repo.delete_session(session_id)

    logger.info(f"Deleted all sessions ({len(deleted)} total)")
    return {"status": "success", "deleted": len(deleted)}


@app.delete("/sessions/{session_id}", tags=["Admin"])
async def delete_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a single session log (logs + intelligence + messages).
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    del SESSIONS[session_id]
    db_repo.delete_session(session_id)
    logger.info(f"Deleted session: {session_id}")

    return {"status": "success", "deleted": 1, "session_id": session_id}


# -------------------------
# WhatsApp Monitor Control Endpoints
# -------------------------

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whatsapp_manager import start_monitor, stop_monitor, get_status, get_recent_output
from telegram_manager import start_monitor as start_telegram_monitor, stop_monitor as stop_telegram_monitor, get_status as get_telegram_status, get_recent_output as get_telegram_recent_output, set_bot_token, bot_token
from email_manager import start_monitor as start_email_monitor, stop_monitor as stop_email_monitor, get_status as get_email_status, get_recent_output as get_email_recent_output, set_email_config, email_config


@app.post("/monitor/whatsapp/start", tags=["Monitor"])
async def start_whatsapp_monitor():
    """
    Start the WhatsApp monitor subprocess.
    Returns status and PID of the monitor process.
    """
    logger.info("Starting WhatsApp monitor via API request")
    result = start_monitor()
    return result


@app.post("/monitor/whatsapp/stop", tags=["Monitor"])
async def stop_whatsapp_monitor():
    """
    Stop the WhatsApp monitor subprocess.
    """
    logger.info("Stopping WhatsApp monitor via API request")
    result = stop_monitor()
    return result


@app.get("/monitor/whatsapp/status", tags=["Monitor"])
async def get_whatsapp_status():
    """
    Get current WhatsApp monitor status.
    """
    status = get_status()
    return status


@app.get("/monitor/whatsapp/output", tags=["Monitor"])
async def get_whatsapp_output(
    lines: int = 20
):
    """
    Get recent output from WhatsApp monitor.
    """
    output = get_recent_output(lines)
    return output


# Telegram Monitor Endpoints
@app.post("/monitor/telegram/set-token", tags=["Monitor"])
async def set_telegram_token_endpoint(
    token: str
):
    """
    Set the Telegram bot token for the monitor and save encrypted to database.
    """
    logger.info("Setting Telegram bot token")
    set_bot_token(token)
    
    # Save to database
    db_repo.upsert_config('telegram_bot_token', token, encrypt=True)
    return {"status": "success", "message": "Bot token set and encrypted successfully"}


@app.get("/monitor/telegram/token-status", tags=["Monitor"])
async def get_telegram_token_status():
    """
    Check if Telegram bot token is set.
    """
    return {
        "token_set": bool(bot_token),
        "has_token": bool(bot_token)
    }


@app.post("/monitor/telegram/start", tags=["Monitor"])
async def start_telegram_monitor_endpoint():
    """
    Start the Telegram monitor subprocess.
    Returns status and PID of the monitor process.
    """
    logger.info("Starting Telegram monitor via API request")
    result = start_telegram_monitor()
    return result


@app.post("/monitor/telegram/stop", tags=["Monitor"])
async def stop_telegram_monitor_endpoint():
    """
    Stop the Telegram monitor subprocess.
    """
    logger.info("Stopping Telegram monitor via API request")
    result = stop_telegram_monitor()
    return result


@app.get("/monitor/telegram/status", tags=["Monitor"])
async def get_telegram_monitor_status():
    """
    Get the current status of the Telegram monitor.
    """
    result = get_telegram_status()
    return result


@app.get("/monitor/telegram/output", tags=["Monitor"])
async def get_telegram_monitor_output(lines: int = 20):
    """
    Get recent output from the Telegram monitor.
    """
    result = get_telegram_recent_output(lines)
    return result


# Email Monitor Endpoints
@app.post("/monitor/email/set-config", tags=["Monitor"])
async def set_email_config_endpoint(
    imap_host: str,
    imap_port: str = "993",
    imap_user: str = "",
    imap_pass: str = ""
):
    """
    Set the email configuration for the monitor and save encrypted to database.
    """
    logger.info("Setting email configuration")
    set_email_config(imap_host, imap_port, imap_user, imap_pass)
    # Save to database with encryption for persistence
    db_repo.upsert_config('email_imap_host', imap_host, encrypt=True)
    db_repo.upsert_config('email_imap_port', imap_port, encrypt=False)
    db_repo.upsert_config('email_imap_user', imap_user, encrypt=True)
    db_repo.upsert_config('email_imap_pass', imap_pass, encrypt=True)
    return {"status": "success", "message": "Email configuration set and encrypted successfully"}


@app.get("/monitor/email/config-status", tags=["Monitor"])
async def get_email_config_status():
    """
    Check if email configuration is set.
    """
    return {
        "config_set": bool(email_config),
        "has_config": bool(email_config)
    }


@app.post("/monitor/email/start", tags=["Monitor"])
async def start_email_monitor_endpoint():
    """
    Start the email monitor subprocess.
    Returns status and PID of the monitor process.
    """
    logger.info("Starting email monitor via API request")
    result = start_email_monitor()
    return result


@app.post("/monitor/email/stop", tags=["Monitor"])
async def stop_email_monitor_endpoint():
    """
    Stop the email monitor subprocess.
    """
    logger.info("Stopping email monitor via API request")
    result = stop_email_monitor()
    return result


@app.get("/monitor/email/status", tags=["Monitor"])
async def get_email_monitor_status():
    """
    Get the current status of the email monitor.
    """
    result = get_email_status()
    return result


@app.get("/monitor/email/output", tags=["Monitor"])
async def get_email_monitor_output(lines: int = 20):
    """
    Get recent output from the email monitor.
    """
    result = get_email_recent_output(lines)
    return result


# -------------------------
# Root Endpoint
# -------------------------

@app.get("/", tags=["Info"])
async def root():
    """
    API information endpoint.
    """
    settings = get_settings()
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
