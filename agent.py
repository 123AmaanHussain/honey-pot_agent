import os
import time
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

# 🔑 STEP 1 — Set Up Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is required")
genai.configure(api_key=api_key)

# We use 'gemini-flash-latest' which points to the stable 1.5 Flash model
# This model is faster and has higher rate limits than 2.0
model = genai.GenerativeModel('models/gemini-flash-latest')

# 🧠 STEP 2 — Decide “MODE”
def decide_mode(confidence):
    """
    Selects a control mode label based on a confidence score.
    
    Parameters:
        confidence (float): Confidence score in the range [0, 1].
    
    Returns:
        mode (str): One of "EXIT", "DEFLECTION", or "NORMAL".
            - "EXIT" when confidence < 0.25
            - "DEFLECTION" when 0.25 <= confidence < 0.5
            - "NORMAL" when confidence >= 0.5
    
    Raises:
        ValueError: If `confidence` is not between 0 and 1.
    """
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
    """
    Categorizes a text message into a predefined topic label.
    
    Parameters:
        message (str): The message text to classify.
    
    Returns:
        str: One of the topic labels "PAYMENT", "OTP", "LINK", "BANK", or "GENERAL".
    """
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

# 🧠 STEP 4 — Build CONTROLLED PROMPT
def build_prompt(topic, mode, scammer_message):
    """
    Constructs a controlled prompt that instructs the LLM to produce a single, constrained human-like reply based on the conversation topic, behavior mode, and the provided scammer message.
    
    Parameters:
    	topic (str): Conversation topic label (e.g., "PAYMENT", "OTP", "LINK", "BANK", "GENERAL").
    	mode (str): Behavior mode guiding reply style (e.g., "EXIT", "DEFLECTION", "NORMAL").
    	scammer_message (str): The incoming message from the scammer to be embedded in the prompt.
    
    Returns:
    	prompt (str): A formatted prompt string containing role, topic, mode, explicit rules, and the embedded scammer message.
    """
    return f"""
You are a real human user chatting with a service agent.
You do NOT know this is a scam.

Conversation topic: {topic}
Behavior mode: {mode}

Rules:
- Stay strictly on the topic.
- Sound natural and human.
- Ask relevant clarification or show minor difficulty.
- Do NOT accuse or mention scam.
- Keep reply under 2 short sentences.

Scammer message:
"{scammer_message}"

Write ONE reply only.
"""

# 🤖 STEP 5 — Call Gemini (With Auto-Retry)
# ... keep your imports and setup the same ...

def call_llm(prompt):
    # Try up to 3 times for Rate Limits OR Connection drops
    """
    Generate text for the given prompt using the configured Gemini model, with retry handling for transient quota or connection errors.
    
    Attempts up to three generation tries on transient errors; on success returns the model's generated text stripped of surrounding whitespace. If a non-retryable error occurs returns the fallback message "I'm having trouble understanding. Can you repeat that?"; if all retries fail returns "System busy, please try later."
    
    Parameters:
        prompt (str): The prompt text to send to the model.
    
    Returns:
        str: The model's generated reply (stripped), or a fallback/system-busy message on error.
    """
    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4
                )
            )
            return response.text.strip()

        except (exceptions.ResourceExhausted, ConnectionError, Exception) as e:
            # Check if it's a fatal error or a retry-able network error
            error_str = str(e).lower()
            if "quota" in error_str or "connection" in error_str or "remote" in error_str:
                wait_time = 2 * (attempt + 1)
                print(f"   [Connection/Limit Issue. Retrying in {wait_time}s...]")
                time.sleep(wait_time)
                continue # Try loop again

            # If it's a real code error (like syntax), print and return fallback
            print(f"DEBUG Error: {e}")
            return "I'm having trouble understanding. Can you repeat that?"

    return "System busy, please try later."

# ... keep the rest of the file same ...

# 🧩 STEP 6 — FINAL FUNCTION
def generate_agent_reply(last_message, confidence):
    """
    Generate a single agent-style reply to the provided last message based on a confidence score.
    
    Parameters:
        last_message (str): The most recent message from the conversation (e.g., a suspected scammer message) to respond to.
        confidence (float): A value between 0 and 1 indicating the system's confidence; used to determine the behavior mode.
    
    Returns:
        reply (str): A short, single response generated for the given message following the selected topic and behavior mode.
    """
    topic = detect_topic(last_message)
    mode = decide_mode(confidence)
    prompt = build_prompt(topic, mode, last_message)
    reply = call_llm(prompt)
    return reply

# # 🧪 STEP 7 — TEST BLOCK
# if __name__ == "__main__":
#     print("Test 1 (Payment):", generate_agent_reply("Pay exam fee immediately", 0.42))
#     # We add a small manual pause here just to be safe
#     time.sleep(1)
#     print("Test 2 (OTP):", generate_agent_reply("HI", 0.8))
#     time.sleep(1)
#     print("Test 3 (Low Conf):", generate_agent_reply("who are you?", 0.9))