"""
Production-Ready Honey-Pot Scam Detection API
AI-powered agentic system that detects scam messages and autonomously engages scammers.
"""
import os
import logging
import time
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from logging.handlers import RotatingFileHandler

from config import get_settings, Settings
from models import (
    IncomingRequest, MessageResponse, ErrorResponse,
    HealthResponse, DetailedHealthResponse, MetricsResponse,
    SessionResponse, SessionData, ExtractedIntelligence,
    IntelligenceResponse, ScammerType
)
from middleware import (
    RequestIDMiddleware, RequestLoggingMiddleware,
    SecurityHeadersMiddleware, RateLimitMiddleware
)
from detection import detect_scam, update_confidence
from agent import generate_reply, generate_exit_message, profile_scammer
from callback import send_final_callback
from extraction import extract_all_intelligence, merge_intelligence
from webhook_manager import EventManager

# Neon PostgreSQL persistence (gracefully degrades when not configured)
try:
    from app.db.client import init_db, is_connected
    from app.db import repository as db_repo
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False


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
    
    # Console handler (force UTF-8 on Windows to avoid cp1252 emoji errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.log_level)
    # Reconfigure stdout encoding if needed (Windows cp1252 fix)
    try:
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
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


def _persist_to_db(session_id: str, session: SessionData, save_message: tuple[str, str] = None):
    """
    Persist session state, intelligence, and optional message to Neon PostgreSQL.
    Gracefully degrades when DB is unavailable.
    """
    if not DB_AVAILABLE or not is_connected():
        return
    try:
        db_repo.upsert_session(session_id, session.dict())
        db_repo.upsert_intelligence(session_id, session.extracted.dict())
        if save_message:
            sender, text = save_message
            db_repo.save_message(session_id, sender, text)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"DB persistence failed for {session_id}: {e}")


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
    
    # Initialize Neon PostgreSQL if configured
    if DB_AVAILABLE and settings.db_enabled and settings.database_url:
        db_ok = init_db(settings.database_url)
        if db_ok:
            logger.info("[OK] Neon PostgreSQL persistence enabled")
        else:
            logger.warning("[WARN] Neon PostgreSQL init failed — running in memory-only mode")
    else:
        logger.info("[INFO] Database persistence disabled (set db_enabled=True and DATABASE_URL to enable)")
    
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    logger.info(f"Total sessions processed: {len(SESSIONS)}")


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
        logger.info(f"DEBUG - Received body: {json.dumps(body, indent=2)}")
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
        else:
            message_text = str(message_obj)
        
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
    
    # Persist session + incoming message to Neon
    _persist_to_db(session_id, session, save_message=("scammer", message_text))
    
    # Add message to history for pattern detection (keep last 10)
    session.message_history.append(message_text)
    if len(session.message_history) > 10:
        session.message_history = session.message_history[-10:]
    
    # -------------------------
    # Enhanced Scam Detection
    # -------------------------
    detection = detect_scam(
        message_text,
        message_history=session.message_history[:-1],  # Exclude current message
        behavior_patterns=session.behavior_patterns
    )
    
    # -------------------------
    # PASS-THROUGH MODE: If NOT scam, let user handle it
    # -------------------------
    if not detection["is_scam"]:
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
    
    # Persist updated session + intelligence to Neon
    _persist_to_db(session_id, session)
    
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
        # Exit condition 1: Confidence threshold reached
        if session.confidence <= settings.exit_confidence_threshold:
            return True, "confidence_threshold"
        
        # Exit condition 2: Sufficient intelligence collected
        has_critical_intel = (
            len(session.extracted.upiIds) > 0 or
            len(session.extracted.phoneNumbers) > 0 or
            len(session.extracted.phishingLinks) > 0 or
            len(session.extracted.bankAccounts) > 0 or
            len(session.extracted.scannedText) > 0
        )
        if has_critical_intel and session.turns >= 3:
            return True, "intelligence_collected"
        
        # Exit condition 3: Too many turns (safety limit)
        if session.turns >= 15:
            return True, "max_turns_reached"
        
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
        
        # Persist completed session to Neon
        _persist_to_db(session_id, session)
        
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
                image_data=image_data
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
    
    # Persist agent reply to Neon
    if reply:
        _persist_to_db(session_id, session, save_message=("agent", reply))
    
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
    
    return SessionResponse(
        session_id=session_id,
        data=SESSIONS[session_id]
    )


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
    Return completed sessions with full intelligence.
    Used by the local agent to poll for newly completed scam sessions
    and notify the user.
    
    Query param `since` is an ISO timestamp; only sessions completed
    after that time are returned.
    """
    completed = []
    for sid, data in SESSIONS.items():
        if not data.completed:
            continue
        if since and data.last_activity and data.last_activity.isoformat() < since:
            continue
        completed.append({
            "session_id": sid,
            "platform": getattr(data, "platform", "unknown"),
            "scammer_type": data.scammer_type.value,
            "scammer_profile": data.scammer_profile,
            "confidence": data.confidence,
            "turns": data.turns,
            "completed_at": data.last_activity.isoformat() if data.last_activity else None,
            "intelligence": data.extracted.dict(),
            "current_persona": data.current_persona,
        })
    
    # Also pull from DB if available (covers sessions from previous restarts)
    if DB_AVAILABLE and is_connected():
        try:
            db_sessions = db_repo.get_all_sessions()
            existing_ids = {s["session_id"] for s in completed}
            for row in db_sessions:
                if row.get("id") in existing_ids:
                    continue
                if not row.get("completed"):
                    continue
                if since and row.get("last_activity") and row["last_activity"].isoformat() < since:
                    continue
                completed.append({
                    "session_id": row.get("id"),
                    "platform": row.get("platform", "unknown"),
                    "scammer_type": row.get("scammer_type", "unknown"),
                    "scammer_profile": row.get("scammer_profile"),
                    "confidence": row.get("confidence"),
                    "turns": row.get("turns"),
                    "completed_at": row.get("last_activity").isoformat() if row.get("last_activity") else None,
                    "intelligence": {
                        "upiIds": row.get("upi_ids", []) or [],
                        "phoneNumbers": row.get("phone_numbers", []) or [],
                        "phishingLinks": row.get("phishing_links", []) or [],
                        "bankAccounts": row.get("bank_accounts", []) or [],
                        "suspiciousKeywords": row.get("suspicious_keywords", []) or [],
                        "scannedText": row.get("scanned_text", []) or [],
                    },
                    "current_persona": row.get("current_persona"),
                })
        except Exception as e:
            logger.warning(f"DB query for completed sessions failed: {e}")
    
    return {
        "total": len(completed),
        "sessions": completed
    }


# -------------------------
# WhatsApp Monitor Control Endpoints
# -------------------------

from whatsapp_manager import start_monitor, stop_monitor, get_status, get_recent_output


@app.post("/monitor/whatsapp/start", tags=["Monitor"])
async def start_whatsapp_monitor(api_key: str = Depends(verify_api_key)):
    """
    Start the WhatsApp monitor subprocess.
    Returns status and PID of the monitor process.
    """
    logger.info("Starting WhatsApp monitor via API request")
    result = start_monitor()
    return result


@app.post("/monitor/whatsapp/stop", tags=["Monitor"])
async def stop_whatsapp_monitor(api_key: str = Depends(verify_api_key)):
    """
    Stop the WhatsApp monitor subprocess.
    """
    logger.info("Stopping WhatsApp monitor via API request")
    result = stop_monitor()
    return result


@app.get("/monitor/whatsapp/status", tags=["Monitor"])
async def get_whatsapp_status(api_key: str = Depends(verify_api_key)):
    """
    Get current WhatsApp monitor status.
    Includes QR code generation status and connection status.
    """
    status = get_status()
    return status


@app.get("/monitor/whatsapp/output", tags=["Monitor"])
async def get_whatsapp_output(
    lines: int = 20,
    api_key: str = Depends(verify_api_key)
):
    """
    Get recent output from WhatsApp monitor.
    Useful for displaying QR code and connection messages.
    """
    output = get_recent_output(lines=lines)
    return output


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
