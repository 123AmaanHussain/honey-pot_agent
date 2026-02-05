import os
import time
import logging
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any
import base64

from config import get_settings
from persona_manager import get_persona_manager
from models import ScammerType

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
        logger.info("✅ Groq client initialized for high-speed inference")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

# Get persona manager
persona_manager = get_persona_manager()

# 🧠 STEP 2 — Decide "MODE"
def decide_mode(confidence):
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
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
                max_tokens=150,
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
def generate_reply(
    confidence: float,
    last_message: str = "Hello",
    current_persona: Optional[str] = None,
    extracted_intelligence: Optional[Dict] = None,
    image_data: Optional[str] = None
) -> tuple[str, str, List[str]]:
    """
    Generate agent reply with optional image processing.
    """
    # Select appropriate persona
    persona = persona_manager.select_persona(confidence, current_persona)
    
    # Detect topic and mode
    topic = detect_topic(last_message)
    mode = decide_mode(confidence)
    
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
        scammer_message=last_message
    )
    
    # If we have scanned intel, add it to the prompt context
    if scanned_intelligence:
        prompt = f"Additional Context from Image OCR: {', '.join(scanned_intelligence)}\n\n{prompt}"
    
    # Generate reply
    reply = call_llm(prompt)
    
    return reply, persona.persona_type.value, scanned_intelligence


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
        
        response = model.generate_content([prompt, image_parts[0]])
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
    
    exit_message = persona_manager.get_exit_message(persona, extracted_intelligence or {})
    
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

