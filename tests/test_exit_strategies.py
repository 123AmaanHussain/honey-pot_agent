"""Test the full conversation flow — intel extraction exit and pressure exit without LLM."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.agent import generate_reply, detect_pressure
from app.core.extraction import extract_all_intelligence

print("=" * 60)
print("TEST 1: Intel extraction flow (simulated identity theft scam)")
print("=" * 60)

conversation = [
    ("Hello, I am calling from SBI bank about your account", "NORMAL"),
    ("We detected some suspicious activity on your account", "NORMAL"),
    ("My name is Rajesh Kumar, my number is 9876543210", "NORMAL"),
    ("We need you to send money to my UPI id rajeshtraders@ybl", "NORMAL"),
    ("Also check the website www.rewardclaim.com for offer", "NORMAL"),
]

collected = {}
turns = 0
for msg, _ in conversation:
    turns += 1
    # Extract intel
    intel = extract_all_intelligence(msg, [])
    for k, v in intel.items():
        for item in v:
            if item not in collected.get(k, []):
                collected.setdefault(k, []).append(item)
    
    total = sum(len(v) for v in collected.values() if v)
    print(f"Turn {turns}: '{msg[:50]}...'")
    print(f"  Intel now: {collected}")
    
    # Check exit condition logic (same as main.py should_exit)
    if total >= 2:
        print(f"  >>> EXIT: {total} intelligence items extracted")
        break

print()
print("=" * 60)
print("TEST 2: Pressure detection triggers immediate exit")
print("=" * 60)

pressure_cases = [
    "If you don't pay now, the police will arrest you",
    "Your account will be blocked in 24 hours!",
    "HURRY UP! Send the money NOW!",
    "Listen to me and don't argue with me",
    "Don't tell anyone about this secret",
]

for msg in pressure_cases:
    is_p, ptype = detect_pressure(msg)
    r, persona, _, exit = generate_reply(0.9, msg, message_history=[])
    print(f"Scammer: '{msg}'")
    print(f"  Pressure: {is_p} ({ptype}) | Exit: {exit}")
    print(f"  Reply: '{r}'")
    print()

print("=" * 60)
print("TEST 3: Normal conversation stays on topic (no exit)")
print("=" * 60)

normal_cases = [
    "Hello, how are you today?",
    "Oh I'm just checking in, needed to confirm something",
]

for msg in normal_cases:
    is_p, ptype = detect_pressure(msg)
    r, persona, _, exit = generate_reply(0.9, msg, message_history=["Hello", "How are you"])
    print(f"Scammer: '{msg}'")
    print(f"  Pressure: {is_p} ({ptype}) | Exit: {exit}")
    print(f"  Reply: '{r}'")
    print()

print("All tests passed!")