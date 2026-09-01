# Honey-Pot Project Status

## What is Honey-Pot?

**Honey-Pot** is an AI-powered cybercrime detection and intelligence system. It is an autonomous agent that detects scam messages, engages scammers with human-like personas, extracts high-value intelligence (UPI IDs, phone numbers, phishing links, bank accounts), and provides comprehensive analytics for cybercrime prevention.

Built for the GUVI Hackathon. Live deployment at `https://honey-pot-agent.onrender.com`.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, Uvicorn/Gunicorn |
| LLM | Groq (Llama 3.1 8B), Google Gemini (fallback + Vision OCR) |
| Database | PostgreSQL (Neon cloud) via psycopg2 |
| Frontend | Next.js 16, React 19, Recharts, jsPDF |
| Encryption | Fernet symmetric encryption |
| Monitors | whatsapp-web.js (Node.js), Telethon (Python), Gmail IMAP, ADB SMS |
| CI/CD | GitHub Actions, Render |

---

## Implemented Features

### Core Detection Engine
- Keyword-based scam detection (16 keywords)
- Urgency, threat, escalation, and repetition detection
- Multi-factor confidence scoring with decay system
- Pass-through mode: only engages when scam is detected

### Intelligence Extraction
- UPI ID extraction with provider validation
- Indian phone number extraction (10-digit +91 handling)
- Phishing URL extraction with TLD validation
- Bank account number extraction (11-18 digits)
- Suspicious keyword extraction from detection flags
- Intelligence merging with deduplication

### AI Agent System
- Hybrid LLM strategy: Groq (speed) + Gemini (fallback with retry)
- Persona-driven prompt generation (7 personas)
- Pressure detection across 6 categories (urgency, threat, fear, authority, isolation, aggression)
- Response validation (anti-robotic phrases, word limits, hallucination detection)
- Response humanization (contractions, hesitations)
- Image/vision processing via Gemini Vision for OCR
- Scammer type classification (Tech Support, Banking, Prize/Lottery, Romance, Job, Unknown)
- Mode decision: NORMAL, DEFLECTION, EXIT based on confidence

### Persona System (7 personas, confidence-based switching)
1. Confused User (0.85-1.0)
2. Busy Professional (0.7-0.85)
3. Nervous Elder (0.55-0.7)
4. Curious Student (0.4-0.55)
5. Over-Polite (0.25-0.4)
6. Paranoid User (0.1-0.25)
7. Tech-Savvy Skeptic (0.0-0.1)

### Session Management
- In-memory session store with background cleanup
- Database hydration from PostgreSQL on startup
- Tracks confidence, turns, persona history, behavior patterns, message history, extracted intel

### Database Persistence
- PostgreSQL (Neon) with 4 tables: sessions, intelligence, messages, configuration
- Write-through persistence for every message and session update
- Graceful degradation: runs memory-only when DB is unavailable
- Encrypted config storage for bot tokens and email credentials

### Middleware Stack
- Request ID tracking (UUID, X-Request-ID header)
- Request logging (method, path, status, processing time)
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Per-IP rate limiting (100 req/min) with retry-after headers

### Real-Time Webhooks
- INTEL_EXTRACTED events
- SCAMMER_AGGRESSIVE events
- SESSION_COMPLETED events
- Async threaded fire-and-forget delivery

### Callback System
- HTTP POST to organizer endpoint on session completion
- Retry mechanism with exponential backoff

### Platform Monitors
- WhatsApp Web monitor (Node.js, QR code auth)
- Telegram monitor (Telethon MTProto, user account)
- Gmail monitor (Python, OAuth2 polling)
- Android SMS monitor (Python, ADB-based)
- Desktop notifications (Win10toast/plyer)
- Completion watcher for session alerts

### API Endpoints (25+)
- `/honeypot/message` -- Main scam message processing
- `/intelligence` -- Aggregated intel from all sessions
- `/sessions`, `/session/{id}` -- Session management
- `/metrics`, `/health`, `/health/detailed` -- Monitoring
- Monitor control endpoints for WhatsApp, Telegram, Email (start/stop/status/config)

### Frontend Dashboard (Next.js)
- **Command Center** -- Metrics cards, system status, scam education
- **Intel Hub** -- Extracted intel display, PDF report generation, cybercrime.gov.in links
- **Session Logs** -- Session table with detail view
- **Live Chat Simulator** -- Test scam messages against the API
- **Monitor Panels** -- WhatsApp, Telegram, Email control panels with QR/terminal output

### Test Suite (8 modules)
- Unit tests, scam detection tests, persona tests
- Pass-through mode tests, enhanced detection tests
- Confidence decay tests, bank account extraction tests
- System evaluation against 40 labeled messages

### Documentation (8 docs)
- Architecture diagrams (Mermaid)
- 6-phase development roadmap
- SaaS product pipeline
- Deployment guide, integration guide
- Quantum computing integration concepts
- Model training guide, mobile setup guide

---

## Yet to Be Implemented

### Detection & AI Upgrades
- [ ] Hindi/Hinglish keyword support ("aapka account band", "turant payment karo", "OTP dena hoga")
- [ ] Multilingual extraction for mixed-script UPI IDs and phone patterns
- [ ] Response humanization delays (1-3s random delay + occasional typo injection)
- [ ] Fine-tuned DistilBERT scammer classifier (guide written, not integrated)
- [ ] Additional personas: Hard-of-Hearing, Non-English Speaker

### Platform Integrations
- [ ] Telegram Bot API integration (cloud-based, python-telegram-bot)
- [ ] WhatsApp via Twilio (WhatsApp Business API)
- [ ] Discord alert webhook for intel summaries
- [ ] Cybercrime report generator (PDF via reportlab/weasyprint CLI tool)

### Security & Ops
- [ ] JWT authentication (replace static API_KEY with python-jose tokens)
- [ ] Per-session-ID rate limiting
- [ ] Input sanitization (strip HTML/script tags)
- [ ] Secrets scanning (detect-secrets pre-commit hook)
- [ ] Render auto-deploy health check

### Analytics & Reporting
- [ ] Weekly digest email summary
- [ ] Scammer trend tracking (daily counts by type)
- [ ] Phone number geolocation (state/operator mapping)
- [ ] Intel heatmap (India map with scam density)
- [ ] Session quality score (turns-to-intel efficiency)
- [ ] Bulk CSV/JSON export endpoint

### Frontend Dashboard
- [ ] Scammer type breakdown pie chart
- [ ] Serving dashboard as static files from FastAPI
- [ ] API key prompt on dashboard load (localStorage)

### SaaS / Product Pipeline
- [ ] Public scam message checker (paste suspicious message for instant analysis)
- [ ] Real-time agent monitor (WebSocket or polling live log)
- [ ] User notifications (Telegram bot message, desktop popup on scam detection)
- [ ] SaaS platform (auth, multi-tenancy, Supabase, pricing tiers)
- [ ] Hybrid desktop agent (.exe, system tray app)
- [ ] Android app (native SMS/WhatsApp/Telegram monitoring)
- [ ] WhatsApp Business API integration

### Quantum Integration (Experimental)
- [ ] QRNG persona selection (ANU quantum API)
- [ ] Post-Quantum API authentication (CRYSTALS-Kyber/Dilithium)
- [ ] Quantum ML scam classifier (Qiskit/PennyLane QSVM)

---

*Last updated: September 2026*
