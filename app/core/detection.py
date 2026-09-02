from typing import Dict, List
import logging
from difflib import SequenceMatcher
import time

from app.config import get_settings

logger = logging.getLogger(__name__)

SCAM_KEYWORDS = [
    "blocked", "suspended", "verify", "urgent", "immediately",
    "account", "upi", "otp", "kyc", "refund", "prize",
    "final", "warning", "expire", "deactivate", "confirm"
]

URGENCY_WORDS = ["now", "today", "immediately", "within", "asap", "hurry", "quick", "fast"]
THREAT_WORDS = ["blocked", "suspended", "legal", "terminated", "action", "penalty", "fine"]
ESCALATION_WORDS = ["final", "last", "ultimate", "warning", "chance"]

# Import Groq client for LLM-based detection
groq_client = None
try:
    from groq import Groq
    settings = get_settings()
    if settings.groq_api_key:
        groq_client = Groq(api_key=settings.groq_api_key)
        logger.info("[OK] Groq client initialized for LLM-based scam detection")
except Exception as e:
    logger.warning(f"Failed to initialize Groq for detection: {e}")


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def detect_repetition(message: str, message_history: List[str], threshold: float = 0.7) -> Dict:
    """
    Detect if message is repetitive compared to history.
    
    Args:
        message: Current message
        message_history: List of previous messages
        threshold: Similarity threshold to consider repetition
        
    Returns:
        Dictionary with repetition detection results
    """
    if not message_history:
        return {"is_repetitive": False, "similarity": 0.0, "repeated_count": 0}
    
    # Check similarity with recent messages (last 5)
    recent_messages = message_history[-5:]
    max_similarity = 0.0
    repeated_count = 0
    
    for prev_message in recent_messages:
        similarity = calculate_similarity(message, prev_message)
        max_similarity = max(max_similarity, similarity)
        
        if similarity >= threshold:
            repeated_count += 1
    
    is_repetitive = max_similarity >= threshold
    
    if is_repetitive:
        logger.info(
            f"Repetitive message detected",
            extra={
                "similarity": round(max_similarity, 2),
                "repeated_count": repeated_count,
                "threshold": threshold
            }
        )
    
    return {
        "is_repetitive": is_repetitive,
        "similarity": round(max_similarity, 2),
        "repeated_count": repeated_count
    }


def detect_escalation(message: str, behavior_patterns: Dict[str, int]) -> Dict:
    """
    Detect escalation patterns in scammer behavior.
    
    Args:
        message: Current message
        behavior_patterns: Dictionary tracking behavior pattern counts
        
    Returns:
        Dictionary with escalation detection results
    """
    message_lower = message.lower()
    escalation_detected = False
    escalation_type = None
    
    # Check for escalation keywords
    has_escalation_words = any(word in message_lower for word in ESCALATION_WORDS)
    
    # Check for increasing urgency
    urgency_count = behavior_patterns.get("urgency", 0)
    threat_count = behavior_patterns.get("threat", 0)
    
    # Escalation if multiple threats or urgency messages
    if urgency_count >= 2 or threat_count >= 2:
        escalation_detected = True
        escalation_type = "repeated_pressure"
    
    # Escalation if using "final warning" type language
    if has_escalation_words:
        escalation_detected = True
        escalation_type = "final_warning"
    
    if escalation_detected:
        logger.warning(
            f"Escalation pattern detected",
            extra={
                "escalation_type": escalation_type,
                "urgency_count": urgency_count,
                "threat_count": threat_count
            }
        )
    
    return {
        "is_escalating": escalation_detected,
        "escalation_type": escalation_type,
        "urgency_count": urgency_count,
        "threat_count": threat_count
    }


def detect_scam_llm(message: str, message_history: List[Dict] = None, sender_info: Dict = None) -> Dict:
    """
    Detect if a message is a scam using LLM-based analysis with sender context.
    
    Integrates the feedback-driven self-learning layer:
    1. FP Cache — skips LLM entirely if a corrected version of this message exists
    2. Few-shot Augmentation — injects past human corrections into the prompt
    3. Pattern Override — adjusts confidence based on extracted correction patterns
    
    Args:
        message: The message to analyze
        message_history: Previous messages in the conversation (optional)
        sender_info: Dictionary containing sender information (email, phone, profile, name)
        
    Returns:
        Dictionary with detection results
    """
    if message_history is None:
        message_history = []
    if sender_info is None:
        sender_info = {}

    # ──────────────────────────────────────────────────────────────────
    # LAYER 1: FP Cache — skip LLM if this message was corrected before
    # ──────────────────────────────────────────────────────────────────
    try:
        from app.core.feedback import find_cached_correction
        cached = find_cached_correction(message)
        if cached and cached["correction_type"] == "fp":
            # This message (or very similar) was previously a false positive.
            # Return "legitimate" immediately — 0 LLM calls, 0 latency.
            logger.info(
                f"FP cache hit — bypassing LLM, returning legitimate",
                extra={"cached_id": cached["id"], "similarity": "high"},
            )
            return {
                "is_scam": False,
                "confidence": 0.95,
                "flags": ["cached_correction"],
                "reasoning": f"Human-corrected: {cached.get('notes', 'Previously flagged as false positive')}",
                "scam_type": "LEGITIMATE",
                "cached": True,
            }

    except ImportError:
        pass  # feedback module not available
    # ──────────────────────────────────────────────────────────────────
    # LAYER 1.5: Trust Profile — read sender history for context/override.
    # (Profile is UPDATED with the real result AFTER detection so that
    #  scam flags are recorded accurately.)
    # ──────────────────────────────────────────────────────────────────
    sender_context = ""
    trust_level = "unknown"
    msg_type = "casual"
    try:
        from app.core.trust import (
            get_sender_context, classify_message_type,
            get_trust_profile, TrustLevel
        )

        phone = sender_info.get("sender_phone", "")
        name = sender_info.get("sender_name", "")
        session_id = sender_info.get("session_id", "")

        # Get sender trust profile
        profile = get_trust_profile(phone=phone, name=name, session_id=session_id)
        trust_level = profile["trust_level"]

        # Classify the current message type (for later trust update)
        msg_type = classify_message_type(message)

        # Get context string for the LLM prompt
        sender_context = get_sender_context(phone=phone, name=name, session_id=session_id)

        # TRUST-BASED OVERRIDE: Known contacts get benefit of doubt
        # If sender is TRUSTED and current message is casual/greeting → skip LLM
        if trust_level == TrustLevel.TRUSTED and msg_type in ("greeting", "casual"):
            # Log this interaction + flag as clean (updates profile correctly)
            try:
                from app.core.trust import update_trust_profile
                update_trust_profile(
                    phone=phone, name=name, session_id=session_id,
                    message_type=msg_type, is_scam=False,
                    notes="TRUSTED contact, casual/greeting message — override",
                )
            except ImportError:
                pass
            logger.info(
                f"Trust override: TRUSTED sender with casual message — returning legitimate",
                extra={"sender_key": profile["key"], "msg_type": msg_type},
            )
            return {
                "is_scam": False,
                "confidence": 0.98,
                "flags": ["trusted_contact"],
                "reasoning": f"Known trusted contact ({profile['name'] or profile['phone']}) — casual message, not a scam",
                "scam_type": "LEGITIMATE",
                "trust_override": True,
            }

        # KNOWN contacts: lower scam confidence unless strong evidence
        # (the LLM will still analyze, but we inject context to help it decide)

    except ImportError:
        pass  # Trust module not available — continue without trust context
    except ImportError:
        pass  # feedback module not available — continue with LLM

    # ──────────────────────────────────────────────────────────────────
    # Build conversation history text
    # ──────────────────────────────────────────────────────────────────
    history_text = ""
    if message_history:
        parts = []
        for msg in message_history[-5:]:
            if isinstance(msg, dict):
                parts.append(f"{msg.get('sender', 'unknown')}: {msg.get('text', '')}")
            else:
                parts.append(str(msg))
        history_text = "\n".join(parts)
    
    # Build sender information text
    sender_text = ""
    if sender_info:
        sender_parts = []
        if sender_info.get('sender_email'):
            sender_parts.append(f"Email: {sender_info['sender_email']}")
        if sender_info.get('sender_phone'):
            sender_parts.append(f"Phone: {sender_info['sender_phone']}")
        if sender_info.get('sender_name'):
            sender_parts.append(f"Name: {sender_info['sender_name']}")
        if sender_info.get('sender_profile'):
            sender_parts.append(f"Profile: {sender_info['sender_profile']}")
        
        if sender_parts:
            sender_text = "\n".join(sender_parts)

    # ──────────────────────────────────────────────────────────────────
    # LAYER 2: Few-shot Augmentation — inject past corrections
    # ──────────────────────────────────────────────────────────────────
    fewshot_section = ""
    try:
        from app.core.feedback import get_fewshot_examples, build_fewshot_prompt_section
        examples = get_fewshot_examples(message, correction_type="fp")
        fewshot_section = build_fewshot_prompt_section(examples)
        if examples:
            logger.info(f"Injecting {len(examples)} few-shot correction examples into prompt")
    except ImportError:
        pass
    
    # Build LLM prompt for scam detection
    prompt = f"""
You are an expert scam detection AI. Analyze the CURRENT MESSAGE to determine if it is a scam.

CRITICAL RULE: You are analyzing ONLY the CURRENT MESSAGE below. Do NOT flag messages as scam just because the conversation history contains scam-like content. Judge each message on its own merits.

SENDER INFORMATION:
{sender_text if sender_text else "No sender information provided"}

SENDER TRUST PROFILE:
{sender_context if sender_context else "No trust history available — treat as unknown sender."}

CONVERSATION HISTORY (for context only — do NOT use to flag the current message):
{history_text if history_text else "No conversation history"}
{fewshot_section}
CURRENT MESSAGE TO ANALYZE:
"{message}"

ANALYSIS STEPS:

STEP 0: SENDER TRUST CHECK (most important)
   - If sender is TRUSTED (long history, never suspicious):
     → Give HIGH benefit of doubt. Only flag if there are STRONG scam indicators.
     → A trusted contact asking for money once is NOT automatically a scam.
   - If sender is KNOWN (some history, normal behavior):
     → Give moderate benefit of doubt. Consider their history.
   - If sender is UNKNOWN (first interaction):
     → No benefit of doubt. Apply full scam analysis.
   - If sender is SUSPICIOUS (known but flagged before):
     → Extra scrutiny. They may have a compromised account.

STEP 1: Is the current message a greeting, casual chat, or friendly message?
   - "Hello", "Hey", "How are you?", "Good morning", "Happy birthday" → LIKELY LEGITIMATE
   - Do NOT flag greetings as scam just because later messages in history ask for money
   - For TRUSTED/KNOWN contacts: greetings and casual chat are ALWAYS legitimate

STEP 2: Does the current message contain ANY of these scam indicators?
   - Asks for money, UPI, bank details, OTP, or personal information
   - Creates urgency ("send NOW", "within 24 hours", "immediately")
   - Threatens consequences ("account blocked", "legal action", "arrest")
   - Offers prizes/lottery requiring payment
   - Impersonates authority (CBI, police, bank officer)

STEP 3: Conversation flow analysis
   - If the scammer built trust first (greetings, casual chat) THEN later asks for money, that is a ROMANCE or TRUST-BUILDING scam pattern
   - The FIRST greeting message is NOT a scam — it's the trust-building phase
   - The SCAM begins when money/personal info is requested

STEP 4: Minimum evidence requirement
   - A message needs AT LEAST 2 scam indicators to be flagged as scam
   - Single keywords like "account" or "money" alone are NOT enough
   - Casual conversation about money ("I need money for rent") is NOT a scam
   - For KNOWN/TRUSTED contacts: require 3+ indicators (higher bar)

STEP 5: Compromised account detection
   - If sender is KNOWN/TRUSTED but suddenly sends messages with 3+ scam indicators
     → This may be a COMPROMISED ACCOUNT. Flag as scam but note it.
   - If a known contact asks for money in an unusual way (UPI, crypto, gift cards)
     → Treat as potential compromise unless the request is normal for that contact

LEGITIMATE INDICATORS (mark as NOT scam if these apply):
- Bank transaction alerts (credits, debits, EMI) from known banks
- OTP messages for transaction verification
- Greetings, casual conversation, friendly messages
- Messages from known contacts about routine matters
- Work-related messages (meetings, deadlines, projects)
- Service notifications (delivery, orders, ride completion)

SCAM INDICATORS (mark as scam if 2+ present):
- Requests for money via UPI/crypto/gift cards
- Urgency + threat combination
- Prize/lottery requiring payment to claim
- Authority impersonation demanding payment
- Requests for OTP or bank PIN
- Phishing links or suspicious URLs

Provide your analysis in this EXACT format:
IS_SCAM: [true/false]
CONFIDENCE: [0.0 to 1.0]
FLAGS: [comma-separated list of detected indicators]
REASONING: [explain which step led to your conclusion]
SCAM_TYPE: [one of: PHISHING, IMPERSONATION, FINANCIAL_FRAUD, TECH_SUPPORT, PRIZE_SCAM, LOTTERY_SCAM, ADVANCE_FEE_SCAM, TRUST_BUILDING, LEGITIMATE, UNKNOWN]
"""
    
    # LLM-based detection only (no rule-based fallback)
    if groq_client and settings.groq_model:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=settings.groq_model,
                temperature=0.1,  # Low temperature for consistent detection
                max_tokens=500,
            )
            response = chat_completion.choices[0].message.content.strip()
            
            # Debug: Log the raw LLM response
            logger.info(f"Raw LLM response: {response[:200]}")
            
            # Parse LLM response
            result = parse_llm_detection_response(response)
            
            if result:
                # ──────────────────────────────────────────────────────
                # LAYER 3: Pattern Override — adjust from corrections
                # ──────────────────────────────────────────────────────
                try:
                    from app.core.feedback import get_patterns
                    patterns = get_patterns()
                    if result["is_scam"] and patterns:
                        msg_lower = message.lower()
                        for pat in patterns:
                            if pat["type"] == "keyword_override":
                                if pat["keyword"] in msg_lower:
                                    result["confidence"] = max(0.3, result["confidence"] - 0.3)
                                    result["flags"].append(f"pattern_override:{pat['keyword']}")
                                    logger.info(
                                        f"Pattern override applied: '{pat['keyword']}'",
                                        extra={"new_confidence": result["confidence"]},
                                    )
                            elif pat["type"] == "category_override":
                                # Category overrides need category context —
                                # skip for now (handled by few-shot examples)
                                pass
                except ImportError:
                    pass

                logger.info(
                    f"LLM-based scam detection completed",
                    extra={
                        "is_scam": result["is_scam"],
                        "confidence": result["confidence"],
                        "scam_type": result["scam_type"],
                        "flags": result["flags"],
                        "reasoning": result["reasoning"][:100]
                    }
                )
                # Record the detection result into the sender's trust profile
                _record_trust(
                    sender_info, msg_type,
                    is_scam=result["is_scam"],
                    confidence=result["confidence"],
                    notes=f"LLM:{result['scam_type']}"
                )
                return result
            else:
                logger.warning("Failed to parse LLM response")
                
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
    
    # Return default result if LLM fails
    return {
        "is_scam": False,
        "confidence": 0.0,
        "flags": [],
        "reasoning": "LLM detection unavailable - unable to analyze message",
        "scam_type": "UNKNOWN"
    }


def _record_trust(
    sender_info: Dict,
    msg_type: str,
    is_scam: bool,
    confidence: float,
    notes: str = "",
) -> None:
    """
    Record a detection result into the sender's trust profile.
    Only writes for senders with identifying info (phone/name),
    so random strangers without contact info aren't tracked.
    
    This runs AFTER detection, so scam flags are recorded accurately
    and known contacts correctly escalate to SUSPICIOUS when compromised.
    """
    if not sender_info:
        return
    phone = sender_info.get("sender_phone", "")
    name = sender_info.get("sender_name", "")
    session_id = sender_info.get("session_id", "")
    # Only track senders we can identify
    if not (phone or name):
        return
    try:
        from app.core.trust import update_trust_profile
        update_trust_profile(
            phone=phone,
            name=name,
            session_id=session_id,
            message_type=msg_type,
            is_scam=is_scam,
            notes=f"{notes} | confidence={confidence}"
        )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to record trust: {e}")


def parse_llm_detection_response(response: str) -> Dict:
    """
    Parse the LLM detection response.
    
    Args:
        response: LLM response string
        
    Returns:
        Parsed detection results or None if parsing fails
    """
    try:
        result = {
            "is_scam": False,
            "confidence": 0.0,
            "flags": [],
            "reasoning": "",
            "scam_type": "UNKNOWN"
        }
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("IS_SCAM:"):
                result["is_scam"] = "true" in line.lower()
            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(line.split(":")[1].strip())
                except:
                    result["confidence"] = 0.5
            elif line.startswith("FLAGS:"):
                flags_str = line.split(":")[1].strip()
                result["flags"] = [f.strip() for f in flags_str.split(",") if f.strip()]
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
            elif line.startswith("SCAM_TYPE:"):
                result["scam_type"] = line.split(":")[1].strip().upper()
        
        # Validate required fields
        if result["confidence"] >= 0.0 and result["scam_type"]:
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return None


def detect_scam(message: str, message_history: List[str] = None, behavior_patterns: Dict[str, int] = None, use_llm: bool = True) -> Dict:
    """
    Unified scam detection function that uses LLM by default with rule-based fallback.
    
    Args:
        message: Message text to analyze
        message_history: Optional list of previous messages for context
        behavior_patterns: Optional behavior pattern tracking (for rule-based)
        use_llm: Whether to use LLM-based detection (default: true)
        
    Returns:
        Dictionary with detection results
    """
    if use_llm:
        return detect_scam_llm(message, message_history)
    else:
        return detect_scam_rule_based(message, message_history, behavior_patterns)


def detect_scam_rule_based(message: str, message_history: List[str] = None, behavior_patterns: Dict[str, int] = None) -> Dict:
    settings = get_settings()
    message_lower = message.lower()
    flags: List[str] = []
    
    # Initialize optional parameters
    if message_history is None:
        message_history = []
    if behavior_patterns is None:
        behavior_patterns = {}

    # Keyword detection
    for keyword in SCAM_KEYWORDS:
        if keyword in message_lower:
            flags.append(f"keyword:{keyword}")

    # Urgency detection
    if any(word in message_lower for word in URGENCY_WORDS):
        flags.append("urgency")

    # Threat detection
    if any(word in message_lower for word in THREAT_WORDS):
        flags.append("threat")
    
    # Repetition detection
    repetition_result = detect_repetition(message, message_history)
    if repetition_result["is_repetitive"]:
        flags.append(f"repetition:{repetition_result['similarity']}")
    
    # Escalation detection
    escalation_result = detect_escalation(message, behavior_patterns)
    if escalation_result["is_escalating"]:
        flags.append(f"escalation:{escalation_result['escalation_type']}")

    confidence = min(1.0, len(flags) * 0.2)
    is_scam = confidence >= settings.scam_confidence_threshold
    
    if is_scam:
        logger.warning(
            f"Scam detected in message",
            extra={
                "confidence": round(confidence, 2),
                "flags": flags,
                "threshold": settings.scam_confidence_threshold,
                "message_preview": message[:50] + "..." if len(message) > 50 else message
            }
        )

    return {
        "is_scam": is_scam,
        "confidence": round(confidence, 2),
        "flags": flags,
        "repetition": repetition_result,
        "escalation": escalation_result
    }


def update_confidence(old_confidence: float, flags: List[str], repetition_data: Dict = None, escalation_data: Dict = None) -> float:
    """
    Update confidence score with enhanced decay based on scammer behavior.
    
    Args:
        old_confidence: Previous confidence score
        flags: Detection flags
        repetition_data: Repetition detection results
        escalation_data: Escalation detection results
        
    Returns:
        Updated confidence score
    """
    decay = 0.0

    # Base decay for urgency
    if "urgency" in flags:
        decay += 0.1

    # Keyword-based decay
    keyword_count = len([f for f in flags if f.startswith("keyword:")])
    if keyword_count >= 3:
        decay += 0.15
    elif keyword_count >= 2:
        decay += 0.08

    # Threat-based decay
    if "threat" in flags:
        decay += 0.2
    
    # Repetition-based decay (scammer repeating same message)
    if repetition_data and repetition_data.get("is_repetitive"):
        similarity = repetition_data.get("similarity", 0.0)
        repeated_count = repetition_data.get("repeated_count", 0)
        
        # Higher decay for more repetition
        decay += 0.1 * similarity
        if repeated_count >= 2:
            decay += 0.1  # Extra penalty for multiple repetitions
    
    # Escalation-based decay (scammer getting aggressive)
    if escalation_data and escalation_data.get("is_escalating"):
        escalation_type = escalation_data.get("escalation_type")
        
        if escalation_type == "final_warning":
            decay += 0.15  # Strong signal of scam
        elif escalation_type == "repeated_pressure":
            decay += 0.12
    
    new_confidence = round(max(0.0, old_confidence - decay), 2)
    
    logger.info(
        f"Confidence updated",
        extra={
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "decay": round(decay, 2),
            "flags": flags
        }
    )

    return new_confidence
