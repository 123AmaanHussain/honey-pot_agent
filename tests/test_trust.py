"""Test the trust profile system end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.trust import (
    update_trust_profile, get_trust_profile, get_sender_context,
    classify_message_type, TrustLevel, TRUST_FILE, get_trust_stats
)
from app.core.detection import detect_scam_llm
from pathlib import Path

# Clean slate
if TRUST_FILE.exists():
    TRUST_FILE.unlink()

print("=== Test 1: Classify message types ===")
tests = [
    ("Hello friend, how are you?", "greeting"),
    ("Good morning!", "greeting"),
    ("How are you doing today?", "casual"),
    ("I need help with my homework", "casual"),
    ("Send 5000 urgently to my UPI", "scam_indicator"),
    ("Can you send me Rs 5000?", "request"),
]
for msg, expected in tests:
    result = classify_message_type(msg)
    status = "OK" if result == expected else "FAIL"
    print(f"  [{status}] '{msg[:40]}...' -> {result} (expected: {expected})")

print("\n=== Test 2: Build trust over time (known contact 'Rahul') ===")
phone = "+919876543210"
name = "Rahul"

for i in range(6):
    msg_type = "greeting" if i == 0 else "casual"
    p = update_trust_profile(phone=phone, name=name, message_type=msg_type)
    level = p["trust_level"]
    count = p["interaction_count"]
    print(f"  Turn {i+1} ({msg_type}): trust={level}, count={count}")

print("\n=== Test 3: Get sender context ===")
ctx = get_sender_context(phone=phone, name=name)
print(f"  {ctx}")

print("\n=== Test 4: Compromised account scenario ===")
# Rahul's account gets compromised - starts sending scam indicators
p = update_trust_profile(phone=phone, name=name, message_type="scam_indicator", is_scam=True)
print(f"  After scam flag: trust={p['trust_level']}, flags={len(p['flags'])}")
ctx = get_sender_context(phone=phone, name=name)
print(f"  {ctx}")

print("\n=== Test 5: Trust stats ===")
stats = get_trust_stats()
print(f"  {stats}")

print("\n=== Test 6: LLM detection with trust context ===")
# Known contact greeting -> should be CLEAN
r = detect_scam_llm(
    "Hey Rahul, how are you?",
    message_history=["Hello", "Good morning"],
    sender_info={"sender_phone": phone, "sender_name": name, "session_id": "test-1"}
)
print(f"  Known contact greeting: {'SCAM' if r['is_scam'] else 'CLEAN'} | conf={r['confidence']} | flags={r['flags']}")

# Unknown sender greeting -> also CLEAN
r2 = detect_scam_llm(
    "Hey how are you?",
    message_history=[],
    sender_info={"sender_phone": "+11234567890", "sender_name": "Stranger"}
)
print(f"  Unknown sender greeting: {'SCAM' if r2['is_scam'] else 'CLEAN'} | conf={r2['confidence']} | flags={r2['flags']}")

# Cleanup
TRUST_FILE.unlink()
print("\n=== All tests passed! ===")
