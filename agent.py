import os
import time
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

# 🔑 STEP 1 — Set Up Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# We use 'gemini-flash-latest' which points to the stable 1.5 Flash model
# This model is faster and has higher rate limits than 2.0
model = genai.GenerativeModel('models/gemini-flash-latest')

# 🧠 STEP 2 — Decide “MODE”
def decide_mode(confidence):
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

# 🧠 STEP 4 — Build CONTROLLED PROMPT
def build_prompt(topic, mode, scammer_message):
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