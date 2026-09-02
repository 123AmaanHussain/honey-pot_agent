import os
import time
import logging
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import base64

from app.config import get_settings
from app.core.persona_manager import get_persona_manager
from app.models import ScammerType

load_dotenv()

logger = logging.getLogger(__name__)

# 🔑 STEP 1 — Set Up Gemini
# 🔑 STEP 1 — Set Up Gemini and Groq
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)

# Configure Gemini model (fallback/vision)
gemini_model = genai.GenerativeModel(settings.llm_model)

# Configure Groq client if key exists
groq_client = None
if settings.groq_api_key:
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.groq_api_key)
        logger.info("[OK] Groq client initialized for high-speed inference")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

# Get persona manager
persona_manager = get_persona_manager()

# 🧠 STEP 2 — Decide "MODE"
def decide_mode(confidence, is_pressure: bool = False):
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    
    # If pressure is detected, force exit mode regardless of confidence
    if is_pressure:
        return "EXIT"
    
    if confidence < 0.25:
        return "EXIT"
    elif confidence < 0.5:
        return "DEFLECTION"
    else:
        return "NORMAL"

# 🧠 STEP 3 — Detect Topic
def detect_topic(message):
    msg = message.lower()
    if "fee" in msg or "payment" in msg:
        return "PAYMENT"
    if "otp" in msg:
        return "OTP"
    if "link" in msg or "click" in msg:
        return "LINK"
    if "bank" in msg or "upi" in msg:
        return "BANK"
    return "GENERAL"


def detect_pressure(message: str) -> tuple[bool, str]:
    """
    Detect if the scammer is using pressure tactics.
    
    Args:
        message: The scammer's message
        
    Returns:
        Tuple of (is_pressure, pressure_type)
    """
    msg = message.lower()
    
    pressure_indicators = {
        "urgency": ["hurry", "quickly", "immediately", "right now", "fast", "asap", "urgent", "don't wait", "dont wait", "time is running", "limited time"],
        "threat": ["police", "arrest", "legal action", "court", "jail", "case", "fraud", "crime", "investigation", "serious", "consequences"],
        "fear": ["account blocked", "account suspended", "account will be blocked", "lose money", "stolen", "hack", "security breach", "compromised", "danger", "24 hours", "24hrs", "locked", "freeze"],
        "authority": ["government", "official", "regulatory", "compliance", "mandatory", "required", "must", "have to"],
        "isolation": ["don't tell anyone", "dont tell anyone", "keep secret", "confidential", "only you", "private", "nobody else", "don't tell", "dont tell"],
        "aggression": ["listen to me", "do as i say", "you must", "don't argue", "dont argue", "just do it", "stop asking", "follow instructions"]
    }
    
    detected_pressures = []
    for pressure_type, indicators in pressure_indicators.items():
        for indicator in indicators:
            if indicator in msg:
                detected_pressures.append(pressure_type)
                break
    
    if detected_pressures:
        return True, ", ".join(detected_pressures)
    
    return False, ""

# 🤖 STEP 4 — Call LLM (Text-Only via Groq, or Gemini Fallback)
def call_llm(prompt):
    """
    Call LLM with hybrid strategy:
    1. Try Groq (Llama 3) first for speed
    2. Fallback to Gemini if Groq fails or not configured
    """
    settings = get_settings()
    
    # STRATEGY 1: Groq (Fastest)
    if groq_client and settings.groq_model:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=settings.groq_model,
                temperature=settings.llm_temperature,
                max_tokens=350,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq call failed, falling back to Gemini: {e}")
            # Fall through to Gemini
            
    # STRATEGY 2: Gemini (Reliable Fallback)
    for attempt in range(3):
        try:
            response = gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.llm_temperature
                )
            )
            return response.text.strip()

        except (exceptions.ResourceExhausted, ConnectionError, Exception) as e:
            error_str = str(e).lower()
            if "quota" in error_str or "connection" in error_str or "remote" in error_str:
                wait_time = 2 * (attempt + 1)
                logger.warning(f"Gemini call failed, retrying in {wait_time}s... (attempt {attempt + 1}/3)")
                time.sleep(wait_time)
                continue

            logger.error(f"Gemini error: {e}", exc_info=True)
            return "I'm having trouble understanding. Can you repeat that?"

    return "System busy, please try later."


# 🧩 STEP 5 — FINAL FUNCTION
def validate_response(response: str, persona_name: str) -> tuple[bool, str]:
    """
    Validate that the response is human-like and follows persona rules.
    
    Args:
        response: Generated response
        persona_name: Name of the persona used
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not response or not response.strip():
        return False, "Empty response"
    
    # Check response length (should be short and human-like)
    word_count = len(response.split())
    if word_count > 80:
        return False, f"Response too long ({word_count} words), should be under 80 words"
    
    if word_count < 1:
        return False, f"Response too short ({word_count} words)"
    
    # Check for robotic/corporate patterns that real humans never say
    robotic_phrases = [
        "I understand your concern",
        "Thank you for reaching out",
        "I apologize for the inconvenience",
        "Please be advised that",
        "As per our policy",
        "We regret to inform you",
        "I appreciate your patience",
        "Let me assist you with that",
        "I'd be happy to help"
    ]
    
    for phrase in robotic_phrases:
        if phrase.lower() in response.lower():
            return False, f"Response contains corporate phrase: '{phrase}'"
    
    return True, "Response validated"


def humanize_response(response: str, persona_name: str) -> str:
    """
    Post-process response to make it more human-like.
    """
    # Remove quotes if the LLM wrapped the response in quotes
    response = response.strip()
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    if response.startswith("'") and response.endswith("'"):
        response = response[1:-1]
    
    # Remove "As [persona]:" or "Response:" prefixes the LLM sometimes adds
    for prefix in ["As " + persona_name + ":", "Response:", "Reply:", persona_name + ":"]:
        if response.startswith(prefix):
            response = response[len(prefix):].strip()
    
    # Ensure contractions are used (humans use contractions)
    contractions = [
        ("I am", "I'm"), ("do not", "don't"), ("does not", "doesn't"),
        ("will not", "won't"), ("cannot", "can't"), ("would not", "wouldn't"),
        ("should not", "shouldn't"), ("could not", "couldn't"), ("did not", "didn't"),
        ("is not", "isn't"), ("are not", "aren't"), ("was not", "wasn't"),
        ("has not", "hasn't"), ("have not", "haven't"), ("let me", "lemme"),
        ("going to", "gonna"), ("want to", "wanna"), ("got to", "gotta"),
    ]
    for full, short in contractions:
        response = response.replace(full, short)
    
    # Remove excessive punctuation
    while response.endswith(".."):
        response = response[:-1]
    while response.endswith("!!"):
        response = response[:-1]
    while response.startswith("!"):
        response = response[1:]
    
    # Clean up double spaces
    while "  " in response:
        response = response.replace("  ", " ")
    
    return response.strip()


def generate_reply(
    confidence: float,
    last_message: str = "Hello",
    current_persona: Optional[str] = None,
    extracted_intelligence: Optional[Dict] = None,
    image_data: Optional[str] = None,
    message_history: List[str] = None
) -> tuple[str, str, List[str], bool]:
    """
    Generate agent reply with optional image processing and chat memory.
    
    Returns:
        Tuple of (reply, persona_type, scanned_intelligence, should_exit)
    """
    # Detect pressure tactics
    is_pressure, pressure_type = detect_pressure(last_message)
    if is_pressure:
        logger.warning(f"Pressure detected: {pressure_type}", extra={"pressure_type": pressure_type})
    
    # Select appropriate persona
    persona = persona_manager.select_persona(confidence, current_persona)
    
    # Detect topic and mode (mode will be EXIT if pressure detected)
    topic = detect_topic(last_message)
    mode = decide_mode(confidence, is_pressure)
    
    scanned_intelligence = []
    if image_data:
        scanned_intelligence = process_image_for_intel(image_data)
        if scanned_intelligence:
            logger.info(f"Vision analysis extracted {len(scanned_intelligence)} items")
    
    # ... prompt building ...
    prompt = persona_manager.build_persona_prompt(
        persona=persona,
        topic=topic,
        mode=mode,
        scammer_message=last_message,
        message_history=message_history,
        pressure_detected=is_pressure
    )
    
    # If we have scanned intel, add it to the prompt context
    if scanned_intelligence:
        prompt = f"Additional Context from Image OCR: {', '.join(scanned_intelligence)}\n\n{prompt}"
    
    # If pressure detected, add pressure context to prompt
    if is_pressure:
        prompt = f"⚠️ PRESSURE DETECTED: The scammer is using {pressure_type} tactics. You should feel uncomfortable and want to exit the conversation.\n\n{prompt}"
    
    # Generate reply with validation
    max_retries = 3
    reply = ""
    
    for attempt in range(max_retries):
        reply = call_llm(prompt)
        
        # Validate the response
        is_valid, validation_msg = validate_response(reply, persona.name)
        
        if is_valid:
            # Humanize the response
            reply = humanize_response(reply, persona.name)
            logger.info(f"Response validated and humanized (attempt {attempt + 1})")
            break
        else:
            logger.warning(f"Response validation failed: {validation_msg} (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                # Retry with stronger prompt
                prompt += f"\n\nPREVIOUS ATTEMPT FAILED: {validation_msg}\nPlease try again with a shorter, more natural response."
            else:
                # Use fallback response
                logger.warning(f"Using fallback response after {max_retries} attempts")
                reply = get_fallback_response(persona, mode, is_pressure)
    
    # Determine if session should exit
    should_exit = (mode == "EXIT") or is_pressure
    
    if should_exit:
        logger.info("Session marked for exit", extra={
            "mode": mode,
            "pressure_detected": is_pressure,
            "pressure_type": pressure_type if is_pressure else None
        })
    
    # If pressure detected, send a clear safe-exit message that ends engagement
    if is_pressure:
        reply = get_pressure_exit_reply(persona, pressure_type)
        logger.info("Pressure detected — sending safe exit, no more engagement", extra={
            "pressure_type": pressure_type,
            "persona": persona.name
        })
        return reply, persona.persona_type.value, scanned_intelligence, True
    
    return reply, persona.persona_type.value, scanned_intelligence, should_exit


def get_pressure_exit_reply(persona, pressure_type: str = "") -> str:
    """
    Generate a safe exit message when the scammer applies pressure.
    The reply clearly ends engagement without being confrontational.
    """
    import random
    
    # Pressure-type-aware exit responses that naturally end the conversation
    exit_replies = {
        "urgency": [
            "okay okay, slow down. i'll handle this through the bank app myself, thanks.",
            "no no, don't rush me. i'll deal with this on my own time.",
            "i need to take a breath here. i'll call the bank directly."
        ],
        "threat": [
            "whoa, that's a bit aggressive. i'm going to talk to my husband about this first.",
            "i don't respond well to threats. i'll be contacting the authorities myself.",
            "i'm going to end this call and verify things on my own."
        ],
        "fear": [
            "i really shouldn't be giving info over a call like this. i'll go to the branch myself.",
            "this is making me uncomfortable. i'll handle it at the actual bank.",
            "i think i should hang up and call the official number instead."
        ],
        "authority": [
            "i'll verify this through official channels myself. good day.",
            "if this is urgent, i'll reach out through proper channels. busy right now.",
            "i prefer dealing with these things face to face. i'll drop by the branch."
        ],
        "isolation": [
            "why should i keep it a secret? that makes me uneasy. i'll mention it to my family.",
            "i don't like being told to keep things secret. i'll talk to my son about this.",
            "secret? no thanks, i'll let my family know about this first."
        ],
        "aggression": [
            "i don't appreciate being spoken to like that. i'm done here.",
            "this conversation is over. i'll report this.",
            "no, i'm not going to do that. i'm ending this."
        ]
    }
    
    # If specific pressure type known, use related exits; else generic
    if pressure_type in exit_replies:
        return random.choice(exit_replies[pressure_type])
    
    # Generic safe exits based on persona
    generic_exits = {
        "Confused User": [
            "this is getting too complicated. i'll ask my son to help me deal with it.",
            "i think i should stop and talk to someone first. thanks anyway."
        ],
        "Busy Professional": [
            "look, i've got to go. i'll handle this through the bank's official line.",
            "i'm done here, i'll deal with this at the branch myself."
        ],
        "Curious Student": [
            "hmm, i think i'd rather check about this properly first. thanks for the info though.",
            "i should probably ask my professor about this. i'll get back to you."
        ],
        "Over-Polite User": [
            "oh i'm so sorry, but i really must go now! thank you, bye!",
            "i thank you for calling but i'll handle this with the bank directly. so sorry!"
        ],
        "Paranoid User": [
            "yeah, i knew something was off. i'm not comfortable with this anymore.",
            "no thanks, i'll verify things myself. i don't trust this."
        ],
        "Tech-Savvy Skeptic": [
            "this doesn't sit right. i'll verify through official channels.",
            "yeah, i'll look into this. i'll use the official app only."
        ],
        "Nervous Elder": [
            "oh dear, i really need to speak to my son first. i'll call you back.",
            "this is all too fast for me. i'll visit the branch myself, thank you."
        ]
    }
    
    # First try persona-specific
    if persona.name in generic_exits:
        exit_list = generic_exits[persona.name]
    else:
        exit_list = [
            "i think i need to stop here and handle this properly. good day.",
            "i'll take care of this through official channels. thanks."
        ]
    
    return random.choice(exit_list)


def get_fallback_response(persona, mode: str, is_pressure: bool = False) -> str:
    """
    Get a safe fallback response when validation fails.
    """
    if is_pressure:
        # Pressure-specific fallback responses
        pressure_responses = {
            "Confused User": "I'm uncomfortable with this. I'm going to stop now.",
            "Busy Professional": "This is getting too aggressive. I'm ending this conversation.",
            "Nervous Elder": "I'm scared and I don't want to continue this.",
            "Curious Student": "This doesn't feel right. I'm not going to do this.",
            "Over-Polite User": "I'm sorry, but I can't continue with this. Thank you.",
            "Paranoid User": "I knew something was wrong. I'm done with this.",
            "Tech-Savvy Skeptic": "This is clearly suspicious. I'm ending this now."
        }
        return pressure_responses.get(persona.name, "I'm not comfortable with this anymore.")
    
    # Regular fallback responses — use these when LLM fails completely
    fallback_responses = {
        "Confused User": [
            "wait what? i'm a little lost here, can you start from the beginning",
            "hmm ok, i think i get it... but not really lol",
            "oh uh ok, that makes sense i guess"
        ],
        "Busy Professional": [
            "look i'm in the middle of something, can you just text me the important part",
            "ok got it, but can we speed this up? i've got a meeting in 10",
            "yeah yeah i hear you, just tell me what i need to do"
        ],
        "Nervous Elder": [
            "oh my, this is a lot to take in... let me write this down",
            "um ok, my son usually handles these things for me but i'll try",
            "i'm not sure about all this technology stuff but ok"
        ],
        "Curious Student": [
            "oh that's interesting, i never knew that! so what happens next?",
            "wait really? that's kinda cool actually, can you tell me more",
            "huh ok, so how does that work exactly"
        ],
        "Over-Polite User": [
            "oh no no, i'm so sorry for the confusion! yes of course",
            "thank you so much for explaining, i really appreciate it!",
            "oh i'm sorry, i didn't mean to waste your time! let me try again"
        ],
        "Paranoid User": [
            "hold on, that doesn't add up... why would that be the case",
            "ok but how do i know this is legit? sounds kinda suspicious",
            "wait wait wait, slow down. something doesn't feel right here"
        ],
        "Tech-Savvy Skeptic": [
            "hmm that's interesting, but i'm not sure that's how it works",
            "ok show me the source on that, because i've never heard of it",
            "right, and what's the verification process for that exactly"
        ]
    }
    
    import random
    responses = fallback_responses.get(persona.name, ["ok, give me a sec to think about this"])
    return random.choice(responses)


def process_image_for_intel(base64_image: str) -> List[str]:
    """
    Use Gemini Vision to extract text, QR codes, and logos.
    """
    try:
        # Decode base64 to parts
        image_parts = [
            {
                "mime_type": "image/jpeg",  # Assume JPEG, could be improved
                "data": base64_image
            }
        ]
        
        prompt = """
        Analyze this image for scam indicators. 
        Extract any of the following if found:
        - Bank account numbers
        - UPI IDs
        - Phone numbers
        - Any visible text related to money or threats
        - Any website links or QR code content
        
        Return ONLY a comma-separated list of extracted items. If none, return 'None'.
        """
        
        response = gemini_model.generate_content([prompt, image_parts[0]])
        result = response.text.strip()
        
        if result.lower() == "none":
            return []
            
        return [item.strip() for item in result.split(",")]
        
    except Exception as e:
        logger.error(f"Vision processing failed: {e}")
        return []


def generate_exit_message(
    current_persona: Optional[str] = None,
    extracted_intelligence: Optional[Dict] = None
) -> str:
    """
    Generate natural exit message based on persona.
    
    Args:
        current_persona: Current persona type
        extracted_intelligence: Extracted intelligence data
        
    Returns:
        Natural exit message
    """
    # Get current persona or default
    if current_persona:
        persona = persona_manager.get_persona_by_type(current_persona)
    else:
        persona = persona_manager.select_persona(0.2)  # Low confidence persona
    
    if not persona:
        # Fallback exit message
        return "I will visit the bank branch directly. Thank you."
    
    # Always assign exit_message before use
    exit_message = persona_manager.get_exit_message(persona, extracted_intelligence or {})
    
    if not exit_message:
        exit_message = "I will visit the bank branch directly. Thank you."
    
    logger.info(
        f"Generated exit message",
        extra={
            "persona": persona.persona_type.value,
            "has_intelligence": bool(extracted_intelligence)
        }
    )
    
    return exit_message


def profile_scammer(message_history: List[str]) -> tuple[ScammerType, str]:
    """
    Analyze message history to profile the scammer type.
    
    Args:
        message_history: List of messages in the conversation
        
    Returns:
        Tuple of (ScammerType, profile_description)
    """
    if not message_history:
        return ScammerType.UNKNOWN, "Insufficient conversation history"

    history_text = "\n".join(message_history[-5:])  # Use last 5 messages
    
    prompt = f"""
Analyze the following conversation history and categorize the scammer's approach:
"{history_text}"

Categorize into exactly ONE of these types:
- TECH_SUPPORT: Impersonating Microsoft, Google, Apple, Antivirus, tech support.
- BANKING: Impersonating a bank, credit card company, or financial institution.
- PRIZE_LOTTERY: Claiming the user won a prize, lottery, or windfall.
- ROMANCE: Attempting to build a relationship or emotional bond.
- JOB: Offering fake job opportunities or tasks for money.
- UNKNOWN: If none of the above match clearly.

Also provide a brief (1 sentence) description of their specific tactics (e.g., "Using fear of account suspension to demand immediate UPI payment").

Format:
TYPE: [ONE_OF_THE_ABOVE_TYPES]
PROFILE: [BRIEF_DESCRIPTION]
"""

    result = call_llm(prompt)
    
    # Parse results
    scammer_type = ScammerType.UNKNOWN
    profile = "No profile generated"
    
    lines = result.split("\n")
    for line in lines:
        if line.startswith("TYPE:"):
            type_str = line.replace("TYPE:", "").strip().upper()
            try:
                scammer_type = ScammerType[type_str]
            except KeyError:
                # Handle potential mismatch
                if "TECH" in type_str: scammer_type = ScammerType.TECH_SUPPORT
                elif "BANK" in type_str: scammer_type = ScammerType.BANKING
                elif "PRIZE" in type_str: scammer_type = ScammerType.PRIZE_LOTTERY
                elif "ROMANCE" in type_str: scammer_type = ScammerType.ROMANCE
                elif "JOB" in type_str: scammer_type = ScammerType.JOB
        
        if line.startswith("PROFILE:"):
            profile = line.replace("PROFILE:", "").strip()

    logger.info(f"Scammer profiled: {scammer_type.value}", extra={"profile": profile})
    
    return scammer_type, profile

