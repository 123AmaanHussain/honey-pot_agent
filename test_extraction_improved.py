"""
Test improved extraction with the scammer conversation example.
"""
from extraction import extract_all_intelligence

# The scammer conversation text
conversation_text = """
URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. 
Share your account number and OTP immediately to verify your identity.

Madam/Sir, this is SBI Security Department. OTP is One-Time Password sent to your mobile. 
For your safety, please share the 6-digit code you just received. Hurry - only 1 hour left 
to save your account! I can share my official ID first: UPI ID scammer.fraud@fakebank for verification.

Madam, going to bank will take too long! Your account will be blocked in 30 minutes! 
For immediate help, just tell me last 4 digits of your account number and OTP. 
Here's my official SBI verification number: +91-9876543210. Trust me, I'm here to help you!

Madam, the website won't show pending security threats! This is an emergency action by RBI. 
To protect your money, just share your registered mobile number and last transaction amount 
for verification. Here's my official SBI account for your reference: 1234567890123456. 
Time is running out!

Madam, RBI portal updates take 24 hours! By then your account will be compromised! 
For immediate protection, just confirm your registered mobile number - I'll send direct 
verification link from SBI server. Here's my RBI authorization ID: SCAM/2024/RBI/45678. 
Quick action needed!

Madam, the RBI directory won't show real-time fraud alerts! Your branch can't help in this 
emergency - we need to secure your account NOW! Just share your UPI ID and last 3 transactions 
for verification. Here's my official UPI for your reference: scammer.fraud@fakebank. 
Every second counts!

Madam, your branch manager can't access the RBI security server! This is a national-level 
fraud alert! Just share your registered mobile number - I'll send instant OTP verification 
from +91-9876543210 (official SBI fraud helpline). Your account will be blocked in 10 minutes 
if we don't act now!

Madam, the incident reference is SCAM/2024/URGENT/7890 but there's NO TIME for branch visits! 
Your account is already showing suspicious transactions! For immediate freeze, just confirm 
your debit card last 4 digits and expiry date. Here's my verified SBI officer ID: 
1234567890123456 - we must act in next 5 minutes!

Madam, the branch verification will take 48 hours! By then, fraudsters will empty your account! 
For instant protection, just share your registered mobile number - I'll send priority OTP from 
RBI servers. Here's my official authorization: Employee ID SBI/SCM/4567, verified UPI 
scammer.fraud@fakebank. Your last chance to secure funds!

Madam, time is running out! Visit www.sbi-official-security-alert.in (RBI approved portal) 
for procedure details. But first confirm your mobile number - I need to generate emergency 
OTP immediately to stop ₹82,500 fraudulent transfer in progress! My verified credentials: 
Account 1234567890123456, UPI scammer.fraud@fakebank. Delay will freeze ALL your accounts!
"""

# Extract intelligence
intel = extract_all_intelligence(conversation_text, [])

print("=" * 60)
print("IMPROVED EXTRACTION TEST RESULTS")
print("=" * 60)
print(f"\n✅ UPI IDs: {intel['upiIds']}")
print(f"✅ Phone Numbers: {intel['phoneNumbers']}")
print(f"✅ Phishing Links: {intel['phishingLinks']}")
print(f"✅ Bank Accounts: {intel['bankAccounts']}")
print(f"✅ Suspicious Keywords: {intel['suspiciousKeywords'][:10]}...")  # First 10
print("\n" + "=" * 60)

# Expected results
expected = {
    "upiIds": ["scammer.fraud@fakebank"],
    "phoneNumbers": ["9876543210"],
    "phishingLinks": ["www.sbi-official-security-alert.in"],
    "bankAccounts": ["1234567890123456"],
}

print("\nEXPECTED vs ACTUAL:")
print("=" * 60)
for key, expected_val in expected.items():
    actual_val = intel[key]
    match = "✅" if set(expected_val).issubset(set(actual_val)) else "❌"
    print(f"{match} {key}: Expected {expected_val}, Got {actual_val}")

print("\n" + "=" * 60)
