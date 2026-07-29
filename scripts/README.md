# Honey-Pot API — cURL Commands Reference

> **Base URL**: `http://localhost:8000`  
> **API Key**: Set in `.env` as `API_KEY=test_secret_key_12345`

---

## Quick Commands

| # | Command | What It Tests |
|---|---------|---------------|
| 1 | Health Check | Server is running |
| 2 | Detailed Health | DB connection status |
| 3 | Scam Message | Agent engagement + reply |
| 4 | Safe Message | Pass-through (reply = null) |
| 5 | UPI Extraction | Extracts `scammer@paytm` |
| 6 | Phone Extraction | Extracts `9876543210` |
| 7 | Multi-Turn | Session continuation |
| 8 | Intelligence | Aggregated scam data |
| 9 | Metrics | Session statistics |

---

## How to Run

### Option A — Run All Tests at Once (Windows CMD)
```cmd
scripts\test_api.bat
```

### Option B — Run Individual Commands (PowerShell)
```powershell
# Copy-paste any block from scripts\test_api.ps1
```

---

## 1. Health Check
```cmd
curl.exe -s http://localhost:8000/health
```
**Expected:** `{"status":"healthy","timestamp":"..."}`

---

## 2. Detailed Health (Check DB Connection)
```cmd
curl.exe -s http://localhost:8000/health/detailed | python -m json.tool
```
**Expected:** `"database": "connected"` (if Neon is configured) or `"memory-only"`

---

## 3. Scam Message — Agent Engages
```cmd
curl.exe -s -X POST http://localhost:8000/honeypot/message -H "Content-Type: application/json" -H "x-api-key: test_secret_key_12345" -d "{\"sessionId\":\"test-scam-001\",\"message\":{\"sender\":\"scammer\",\"text\":\"URGENT: Your account is BLOCKED! Pay 500 to fraud@upi immediately or face legal action!\"}}" | python -m json.tool
```
**Expected:** `"agent_engaged": true`, `"reply": "..."`, `"scam_detected": true`

---

## 4. Safe Message — Pass-Through
```cmd
curl.exe -s -X POST http://localhost:8000/honeypot/message -H "Content-Type: application/json" -H "x-api-key: test_secret_key_12345" -d "{\"sessionId\":\"test-safe-001\",\"message\":{\"sender\":\"friend\",\"text\":\"Hey, what time does the movie start?\"}}" | python -m json.tool
```
**Expected:** `"agent_engaged": false`, `"reply": null`

---

## 5. UPI ID Extraction
```cmd
curl.exe -s -X POST http://localhost:8000/honeypot/message -H "Content-Type: application/json" -H "x-api-key: test_secret_key_12345" -d "{\"sessionId\":\"test-upi-001\",\"message\":{\"sender\":\"scammer\",\"text\":\"Verify your KYC urgently, send 100 Rs to scammer@paytm or your account will be suspended!\"}}" | python -m json.tool
```
**Expected:** Intelligence contains `scammer@paytm` in UPI IDs

---

## 6. Phone Number Extraction
```cmd
curl.exe -s -X POST http://localhost:8000/honeypot/message -H "Content-Type: application/json" -H "x-api-key: test_secret_key_12345" -d "{\"sessionId\":\"test-phone-001\",\"message\":{\"sender\":\"scammer\",\"text\":\"Call our bank helpline immediately: 9876543210. Your OTP expires in 2 minutes!\"}}" | python -m json.tool
```
**Expected:** `9876543210` extracted in phone numbers

---

## 7. Multi-Turn Session
```cmd
curl.exe -s -X POST http://localhost:8000/honeypot/message -H "Content-Type: application/json" -H "x-api-key: test_secret_key_12345" -d "{\"sessionId\":\"test-multi-001\",\"message\":{\"sender\":\"scammer\",\"text\":\"FINAL WARNING: Account suspended. Transfer 1000 to 112233445566 immediately!\"}}" | python -m json.tool
```
**Expected:** Confidence score decreases, persona may switch

---

## 8. Intelligence Report
```cmd
curl.exe -s http://localhost:8000/intelligence -H "x-api-key: test_secret_key_12345" | python -m json.tool
```
**Expected:** All UPI IDs, phone numbers, and links extracted from all sessions

---

## 9. API Metrics
```cmd
curl.exe -s http://localhost:8000/metrics | python -m json.tool
```
**Expected:** Total sessions, messages, scams detected, uptime

---

## 10. Session Details
```cmd
curl.exe -s http://localhost:8000/sessions/test-scam-001 -H "x-api-key: test_secret_key_12345" | python -m json.tool
```
**Expected:** Full session state including confidence, turns, extracted intelligence

---

## Connecting Neon DB

Once you have Neon credentials, add to `.env`:
```ini
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
DB_ENABLED=true
```

Then run the schema in Neon SQL Editor:
```
app/db/migrations/001_initial.sql
```

Restart the server — health check will show `"database": "connected"`.
