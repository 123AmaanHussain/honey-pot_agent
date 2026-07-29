# ============================================================
#  Honey-Pot API — cURL Test Commands Reference
#  All commands for Windows PowerShell
# ============================================================

$API_KEY = "test_secret_key_12345"
$BASE = "http://localhost:8000"

# 1. Basic health check
curl.exe -s $BASE/health

# 2. Detailed health (shows DB: connected / memory-only)
curl.exe -s $BASE/health/detailed | python -m json.tool

# 3. Scam message — agent engages, returns reply + intelligence
curl.exe -s -X POST $BASE/honeypot/message `
  -H "Content-Type: application/json" `
  -H "x-api-key: $API_KEY" `
  -d '{"sessionId":"test-scam-001","message":{"sender":"scammer","text":"URGENT: Your account is BLOCKED! Pay 500 to fraud@upi immediately or face legal action!"}}' `
  | python -m json.tool

# 4. Safe message — passes through, reply is null
curl.exe -s -X POST $BASE/honeypot/message `
  -H "Content-Type: application/json" `
  -H "x-api-key: $API_KEY" `
  -d '{"sessionId":"test-safe-001","message":{"sender":"friend","text":"Hey, what time does the movie start?"}}' `
  | python -m json.tool

# 5. UPI extraction test
curl.exe -s -X POST $BASE/honeypot/message `
  -H "Content-Type: application/json" `
  -H "x-api-key: $API_KEY" `
  -d '{"sessionId":"test-upi-001","message":{"sender":"scammer","text":"Verify your KYC urgently, send 100 Rs to scammer@paytm or your account will be suspended!"}}' `
  | python -m json.tool

# 6. Phone number extraction test
curl.exe -s -X POST $BASE/honeypot/message `
  -H "Content-Type: application/json" `
  -H "x-api-key: $API_KEY" `
  -d '{"sessionId":"test-phone-001","message":{"sender":"scammer","text":"Call our bank helpline immediately: 9876543210. Your OTP expires in 2 minutes!"}}' `
  | python -m json.tool

# 7. Multi-turn session (follow-up message to same session)
curl.exe -s -X POST $BASE/honeypot/message `
  -H "Content-Type: application/json" `
  -H "x-api-key: $API_KEY" `
  -d '{"sessionId":"test-multi-001","message":{"sender":"scammer","text":"FINAL WARNING: Account suspended. Transfer 1000 to 112233445566 immediately!"}}' `
  | python -m json.tool

# 8. Aggregated intelligence report
curl.exe -s $BASE/intelligence `
  -H "x-api-key: $API_KEY" `
  | python -m json.tool

# 9. API metrics
curl.exe -s $BASE/metrics | python -m json.tool

# 10. Get specific session details
curl.exe -s $BASE/sessions/test-scam-001 `
  -H "x-api-key: $API_KEY" `
  | python -m json.tool
