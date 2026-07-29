# 🍯 Honey-Pot Agent — Project Roadmap

> **Last Updated:** 2026-02-28  
> A living checklist of planned features, phases, and development workflows.  
> Work through each phase one-by-one. Check off tasks as you go!

---

## 📋 Table of Contents

1. [Phase 1 — Admin Dashboard UI](#phase-1--admin-dashboard-ui)
2. [Phase 2 — Persistent Storage](#phase-2--persistent-storage)
3. [Phase 3 — Smarter Detection & AI Upgrades](#phase-3--smarter-detection--ai-upgrades)
4. [Phase 4 — Real-Time Integrations](#phase-4--real-time-integrations)
5. [Phase 5 — Security & Ops Hardening](#phase-5--security--ops-hardening)
6. [Phase 6 — Analytics & Reporting](#phase-6--analytics--reporting)
7. [Development Workflows](#development-workflows)

---

## Phase 1 — Admin Dashboard UI

> **Goal:** Build a visual dashboard to see all sessions, intelligence, and metrics in one place.  
> **Why first:** All data already exists in your API — just needs a UI on top.

### Tasks
- [ ] Create `dashboard/index.html` — main dashboard shell
- [ ] Create `dashboard/styles.css` — dashboard styling (dark theme, cards, tables)
- [ ] Create `dashboard/app.js` — JavaScript fetch logic for API calls
- [ ] **Live Feed page** — real-time session list with confidence scores
- [ ] **Intelligence Board page** — table of all UPI IDs, phones, URLs, bank accounts with copy/export
- [ ] **Session Explorer** — click a session → see conversation replay + persona switches
- [ ] **Scammer Type Breakdown** — pie chart (BANKING vs TECH_SUPPORT vs ROMANCE etc.)
- [ ] **Metrics Cards** — total scams, avg turns, success rate
- [ ] Serve `dashboard/` as static files from FastAPI (`app.mount("/dashboard", StaticFiles(...))`)
- [ ] Add API key prompt on dashboard load (store in `localStorage`)

### Tech Stack
- Plain HTML + Vanilla JS + CSS (no framework needed)
- Chart.js (CDN) for charts
- Fetch API to call existing `/intelligence`, `/metrics`, `/health/detailed`, `/sessions/{id}` endpoints

---

## Phase 2 — Persistent Storage

> **Goal:** Save all session data to a database so it survives server restarts.  
> **Why:** Currently sessions are in-memory — every Render restart wipes all data.

### Tasks
- [ ] Choose database: **PostgreSQL** (recommended via Supabase free tier) or MongoDB Atlas
- [ ] Install dependencies: `sqlalchemy`, `alembic`, `asyncpg` (for async Postgres)
- [ ] Create `database.py` — SQLAlchemy engine + session factory
- [ ] Create `db_models.py` — ORM models:
  - `Session` table: `session_id`, `confidence`, `turns`, `scammer_type`, `completed`, `created_at`, `completed_at`
  - `ExtractedIntel` table: `session_id`, `type` (upi/phone/url/bank), `value`, `extracted_at`
  - `Message` table: `session_id`, `direction` (in/out), `text`, `persona`, `timestamp`
- [ ] Run `alembic init` and create migrations
- [ ] Update `main.py` — replace `SESSIONS: Dict` with DB reads/writes
- [ ] Add `SESSION_DATABASE_URL` to `.env` and `.env.example`
- [ ] Add Redis (optional) for fast active-session cache; flush to DB on session complete
- [ ] Update Render environment variables with DB URL
- [ ] Test: restart Render and verify sessions persist

### Schema Sketch
```sql
sessions (session_id PK, confidence FLOAT, turns INT, scammer_type VARCHAR,
          completed BOOL, created_at TIMESTAMP, completed_at TIMESTAMP)

extracted_intel (id SERIAL PK, session_id FK, type VARCHAR, value TEXT, extracted_at TIMESTAMP)

messages (id SERIAL PK, session_id FK, direction VARCHAR, text TEXT,
          persona VARCHAR, timestamp TIMESTAMP)
```

---

## Phase 3 — Smarter Detection & AI Upgrades

> **Goal:** Make the scam detection and agent responses more accurate and human-like.

### Tasks
- [ ] **Conversation-aware detection** — track if "urgency" flags appear across 3+ turns and escalate confidence decay faster
- [ ] **Hindi/Hinglish keyword support** — add detection keywords:
  - `"aapka account band"`, `"turant payment karo"`, `"OTP dena hoga"`, `"lottery jeeta hai"`
- [ ] **Multilingual extraction** — extend `extraction.py` to handle mixed-script UPI IDs and phone patterns
- [ ] **Response humanization** — add random 1–3s delay before replies + occasional typo injection to avoid bot detection
- [ ] **Emotional escalation tracking** — detect aggression words (`"immediately"`, `"or else"`, `"last warning"`) and switch persona faster
- [ ] **Fine-tuned scammer classifier** *(advanced)* — train a small DistilBERT model on labeled scam messages, replace keyword regex for `is_scam` prediction
- [ ] **Image OCR improvements** — fix `process_image_for_intel()` (currently uses wrong `model` variable), test QR code extraction
- [ ] Add more persona types: `HARD_OF_HEARING`, `NON_ENGLISH_SPEAKER`
- [ ] Unit tests for all new detection patterns in `tests/`

---

## Phase 4 — Real-Time Integrations

> **Goal:** Connect the honey-pot to real messaging channels so actual scammers interact with it automatically.

### Tasks

#### 4A — Telegram Bot
- [ ] Create a Telegram bot via BotFather → get `TELEGRAM_BOT_TOKEN`
- [ ] Install `python-telegram-bot` library
- [ ] Create `integrations/telegram_bot.py`
- [ ] Map incoming Telegram messages → `POST /honeypot/message` (use Telegram user_id as session_id)
- [ ] Map API reply → send back to Telegram chat
- [ ] Add `TELEGRAM_BOT_TOKEN` to `.env`
- [ ] Deploy: run bot as a background service on Render

#### 4B — WhatsApp (via Twilio)
- [ ] Set up a Twilio account + WhatsApp sandbox number
- [ ] Create `integrations/whatsapp_webhook.py` — receive Twilio webhook → forward to `/honeypot/message`
- [ ] Add Twilio credentials to `.env`
- [ ] Register Twilio webhook URL on Render

#### 4C — Discord Alert Webhook
- [ ] Create a Discord server + webhook URL
- [ ] Update `webhook_manager.py` → on `notify_intel_extracted`, POST to Discord with intel summary
- [ ] Add `DISCORD_WEBHOOK_URL` to `.env`
- [ ] Alert format: `"🚨 New Intel: UPI ID scammer123@paytm detected in session XYZ"`

#### 4D — Cybercrime Report Generator
- [ ] Create `reports/generate_report.py`
- [ ] Add `GET /report/{session_id}` endpoint that returns a formatted complaint draft:
  - Scammer phone, UPI, URLs, profile type, conversation summary
  - Ready to paste into [cybercrime.gov.in](https://cybercrime.gov.in)
- [ ] Export as PDF (use `reportlab` or `weasyprint`)

---

## Phase 5 — Security & Ops Hardening

> **Goal:** Make the system production-grade and secure.

### Tasks
- [ ] **JWT authentication** — replace static `API_KEY` header with JWT tokens (`python-jose`)
  - `POST /auth/token` endpoint for login
  - Protected routes use `Bearer <token>` in Authorization header
- [ ] **Session cleanup background task** — use `asyncio` + APScheduler:
  - Every 30 min: purge sessions older than `SESSION_TIMEOUT_MINUTES` from memory
  - After Phase 2: archive expired sessions to DB before purging
- [ ] **Per-session-ID rate limiting** — extend `RateLimitMiddleware` to track limits per session, not just global
- [ ] **Input sanitization** — strip HTML/script tags from incoming `message.text` before processing
- [ ] **Secrets scanning** — add `detect-secrets` pre-commit hook so `.env` values never leak to Git
- [ ] **Audit log table** *(after Phase 2)* — immutable append-only log: `(timestamp, session_id, action, actor, details)`
- [ ] **Render auto-deploy health check** — configure Render to call `/health` and restart if unhealthy
- [ ] Add `SECURITY.md` with responsible disclosure policy

---

## Phase 6 — Analytics & Reporting

> **Goal:** Gain insights from collected scam data over time.

### Tasks
- [ ] **Weekly digest email** — send yourself a summary every Monday:
  - Scams caught, intel collected, top scammer types, new trends
  - Use `smtplib` or SendGrid API
- [ ] **Scammer trend tracking** — store daily counts of each `ScammerType` in DB → query for week-over-week trends
- [ ] **Phone number geolocation** — use a free API (e.g., `numverify`) to map extracted phone numbers to states/operators
- [ ] **Intel heatmap** — on the dashboard, show a map of India with density of scam activity by region
- [ ] **Session quality score** — calculate how many turns it took to extract intel; track improvement over time
- [ ] **Export to CSV/JSON** — `GET /intelligence/export?format=csv` endpoint for bulk download

---

## 🔄 Development Workflows

### Local Development
```bash
# 1. Clone and setup
git clone https://github.com/123AmaanHussain/honey-pot_agent
cd honey-pot_project

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run development server
uvicorn main:app --reload --port 8000

# 6. Open API docs
# http://localhost:8000/docs
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_extraction.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Git Workflow
```bash
# Start a new feature (e.g., Phase 1)
git checkout -b feature/phase-1-dashboard

# Work on your changes...
git add .
git commit -m "feat: add admin dashboard HTML shell"

# Push and open PR
git push origin feature/phase-1-dashboard
# Open PR on GitHub → merge to main → Render auto-deploys
```

### Deploying to Render
```bash
# Render auto-deploys on push to main branch.
# To trigger manual deploy: push any commit to main.

# Check deployment logs on Render dashboard:
# https://dashboard.render.com → your service → Logs

# Environment variables to set on Render:
# GEMINI_API_KEY, GROQ_API_KEY, API_KEY, CALLBACK_URL, etc.
# (See .env.example for full list)
```

### Adding a New Phase Feature
```
1. Create a feature branch: git checkout -b feature/phase-X-feature-name
2. Write code in the appropriate file or create a new module
3. Add unit tests in tests/test_<module>.py
4. Update requirements.txt if new packages added: pip freeze > requirements.txt
5. Test locally with uvicorn --reload
6. Commit with conventional commit message: feat/fix/chore: description
7. Push → PR → merge to main → auto-deploy
```

### Adding New Environment Variables
```
1. Add to your local .env file
2. Add the key (with blank/example value) to .env.example
3. Add to Render environment variables dashboard
4. Add to config.py (Settings class) with a default if optional
5. Commit .env.example (NEVER commit .env itself)
```

---

## 📊 Progress Tracker

| Phase | Status | Started | Completed |
|-------|--------|---------|-----------|
| Phase 1 — Dashboard UI | ⏳ Todo | — | — |
| Phase 2 — Persistent Storage | ⏳ Todo | — | — |
| Phase 3 — Smarter AI | ⏳ Todo | — | — |
| Phase 4 — Integrations | ⏳ Todo | — | — |
| Phase 5 — Security Hardening | ⏳ Todo | — | — |
| Phase 6 — Analytics | ⏳ Todo | — | — |

> Update the Status column as you progress:  
> `⏳ Todo` → `🔄 In Progress` → `✅ Done`
