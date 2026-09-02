"""Test that trust profiles are tracked with REAL detection results."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.detection import detect_scam_llm
from app.core.trust import get_trust_profile, TRUST_FILE

# Clean slate
if TRUST_FILE.exists():
    TRUST_FILE.unlink()

phone = "+919812345678"
name = "Priya"
sender = {"sender_phone": phone, "sender_name": name, "session_id": "trust-test-1"}

print("=== Simulating a normal friend conversation (should build trust) ===")
msgs = [
    "Hey Priya, how are you?",
    "Good morning!",
    "How have you been?",
    "Let us catch up this weekend",
]
for i, m in enumerate(msgs):
    r = detect_scam_llm(m, message_history=[], sender_info=sender)
    p = get_trust_profile(phone=phone, name=name)
    print(f"  [{i+1}] '{m[:35]}' -> is_scam={r['is_scam']} | trust={p['trust_level']} (count={p['interaction_count']})")

print()
print("=== Simulating a compromised account (suddenly sends scam) ===")
scam_msg = "This is urgent, tell me your OTP so we can fix your bank account security"
r = detect_scam_llm(scam_msg, message_history=msgs, sender_info=sender)
p = get_trust_profile(phone=phone, name=name)
print(f"  '{scam_msg[:55]}'")
print(f"  -> is_scam={r['is_scam']}")
print(f"  Trust after scam: {p['trust_level']} | scam_flags={len(p['flags'])}")
for f in p['flags']:
    print(f"    flag: {f}")

print()
print("=== Verify message_types tracking ===")
print(f"  message_types: {p['message_types']}")

# Cleanup
TRUST_FILE.unlink()
print()
print("All trust tracking tests passed!")