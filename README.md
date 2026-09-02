# 🍯 Honey-Pot: AI-Powered Cybercrime Detection & Intelligence System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Advanced autonomous AI agent that detects scam messages, engages scammers with human-like personas, extracts high-value intelligence in real-time, and provides comprehensive analytics for cybercrime prevention.**

---

## 🌟 Key Features

### 🎭 **7 Dynamic Human Personas (Human-Like Replies)**
Adaptive AI personas that switch based on scammer behavior and confidence levels — each with a distinct, natural conversational voice:
- **Confused User** — easily distracted by tech, "wait what?", "huh?"
- **Nervous Elder** — worried but brave, "oh my", "I need to ask my son"
- **Over-Polite** — apologizes a lot, "oh no no, I'm so sorry!"
- **Tech-Savvy Skeptic** — "hmm interesting, let me check that"
- **Busy Professional** — "ugh, make it quick, I'm in a meeting"
- **Curious Student** — "oh wow really? how does that work?"
- **Paranoid User** — "how did you even get my number?"

**Human-Like Response Engine:**
- **Live LLM generation** (Groq Qwen 3.8-27B, Gemini as backup if Groq is unavailable) — no predefined message templates
- **Context-aware replies** — stays on-topic, remembers UPI IDs/names/amounts mentioned earlier
- **Anti-hallucination** — never invents facts not present in conversation
- **Subtle intel gathering** — naturally asks about UPI/phone/link/bank details to funnel them
- Natural speech: contractions, slang, emotional reactions, incomplete thoughts
- Response validation filters robotic/corporate phrasing

### 🧠 **Hybrid Scam Detection**
- **LLM-first** detection with 5-step analysis: sender trust, greetings, scam indicators, conversation flow (trust-building romance scams), minimum 2-indicator evidence
- **3-layer self-learning feedback loop:**
  - **FP Cache** — human-corrected false positives skip the LLM instantly
  - **Few-shot injection** — past corrections shown to the LLM as examples
  - **Pattern override** — keyword rules adjust confidence
- **Trust-based behavioral anomaly detection** — compromised-account detection

### 👥 **Sender Trust Profiles**
Tracks sender behavior over time to catch compromised accounts:
- `UNKNOWN` → `KNOWN` (2+ interactions) → `TRUSTED` (5+ normal) → `SUSPICIOUS`
- Trusted contacts get **benefit of doubt** (casual messages skip the LLM)
- **Compromised-account detection**: A trusted contact suddenly sending scam indicators is flagged `SUSPICIOUS` — their account is likely hacked

### 🚪 **Intelligent Exit Strategy**
- **Intel-complete exit**: safely leaves after extracting 2+ pieces of intelligence (UPI + phone, link + bank, etc.) — no infinite engagement
- **Pressure-triggered emergency exit**: immediate disengagement with a natural safe-exit message (no more engagement)

### ⚠️ **Pressure Detection (6 tactic types)**
Immediate safe exit with zero further engagement:
- **Urgency**: "hurry", "immediately", "right now", "limited time"
- **Threat**: "police", "arrest", "legal action", "jail"
- **Fear**: "account blocked", "lose money", "security breach", "24 hours"
- **Authority**: "government", "official", "mandatory"
- **Isolation**: "don't tell anyone", "keep secret", "confidential"
- **Aggression**: "do as i say", "don't argue", "just do it"

### 🛡️ **Pass-Through Mode**
- Silently monitors all messages
- Only engages when scam is detected
- Legitimate messages pass through untouched — zero disruption to real conversations

### 📊 **Full Intelligence Extraction**
- UPI IDs, Indian phone numbers (10-digit), bank account numbers (11-18 digits)
- Phishing URLs, suspicious keywords
- OCR-scanned text from images (via Gemini Vision)

### 📈 **Analytics & Visualization**
- **Real GeoJSON world threat map** (equirectangular projection) — live scam infrastructure clusters
- Geographic (GeoIP) analytics of scammer sources
- Prometheus metrics + Grafana-ready endpoints
- Full session management with End/Delete controls

### 🔌 **Multi-Channel Monitoring**
- WhatsApp, Telegram, and Email monitors
- Multi-simulator for stress-testing the agent
- Real-time webhooks (`INTEL_EXTRACTED`, `SCAMMER_AGGRESSIVE`, `SESSION_COMPLETED`)

---

## 📦 What's New (Latest Updates)

| Change | Description |
|--------|-------------|
| **+ Self-Learning Feedback Layer** | Human corrections permanently improve detection via FP cache, few-shot, and patterns |
| **+ Sender Trust Profiles** | Behavioral tracking catches compromised/hacked accounts |
| **+ Trust-Based Detection** | Known/trusted contacts get benefit of doubt |
| **+ Human-Like Reply Engine** | Live LLM personas with context awareness, no more generic "I don't understand" |
| **+ New Exit Strategy** | Exits when intel is complete OR when pressured — no infinite engagement |
| **+ World Threat Map** | Real GeoJSON world map replacing placeholder amoeba graphic |
| **+ Sessions UI** | End/Delete buttons for conversation lifecycle management |
| **~ Improved Detection** | Greetings pass, conversation-flow analysis, minimum 2-indicator evidence |
| **~ Refined Personas** | Each persona now has a distinct natural voice instead of generic deflect-and-clarify |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Groq API Key (primary LLM) · Google Gemini API Key (optional backup)
- PostgreSQL database (optional, for persistence)

### Installation

```bash
# Clone the repository
git clone https://github.com/123AmaanHussain/honey-pot_agent.git
cd honey-pot_agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Update `.env` with your credentials:

```env
# Required
API_KEY=your_secret_api_key_here

# Primary LLM provider (Groq)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b

# Optional backup LLM (Gemini — used only if Groq is unavailable)
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost/honeypot

# Webhooks
WEBHOOK_ENABLED=True
WEBHOOK_URL=https://your-webhook-endpoint.com

# Frontend API (Next.js)
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_secret_api_key_here
```

### Run the Server

```bash
# Backend (FastAPI)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# Frontend (Next.js) — in frontend/ directory
npm install
npm run dev
```

Backend: `http://localhost:8000` · API docs: `http://localhost:8000/docs`

---

## 📡 Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/honeypot/message` | POST | Process incoming message, get agent reply |
| `/intelligence` | GET | Aggregated scam intelligence from all sessions |
| `/sessions` | GET | List all sessions |
| `/sessions/{id}` | DELETE | Delete a session |
| `/sessions/completed` | DELETE | Clear completed sessions |
| `/feedback` | POST | Submit human correction (false positive/negative) |
| `/feedback/stats` | GET | Self-learning correction statistics |
| `/feedback/patterns` | GET | Learned detection patterns |
| `/trust/stats` | GET | Sender trust profile statistics |
| `/trust/profile/{id}` | GET | Individual sender trust profile |
| `/analytics/geo` | GET | Geographic scammer distribution |
| `/metrics/prometheus` | GET | Prometheus metrics |
| `/health` | GET | Service health check |

### Process a Message

```bash
curl -X POST "http://localhost:8000/honeypot/message" \
     -H "x-api-key: test_secret_key_12345" \
     -H "Content-Type: application/json" \
     -d '{
       "sessionId": "session-123",
       "message": {
         "sender": "scammer",
         "text": "Your account is BLOCKED! Pay 500 to 9876543210@paytm NOW!",
         "timestamp": 1770005528731
       },
       "conversationHistory": [],
       "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
     }'
```

---

## 🏗️ Architecture

```
honey-pot_project/
├── app/
│   ├── main.py                    # FastAPI app, all endpoints + session lifecycle
│   ├── core/
│   │   ├── agent.py               # LLM reply engine, persona switching, pressure exit
│   │   ├── persona_manager.py     # 7 personas + human-like prompt builder
│   │   ├── detection.py           # LLM-first detection + feedback & trust integration
│   │   ├── feedback.py            # Self-learning: FP cache, few-shot, patterns
│   │   ├── trust.py               # Sender trust profiles + compromised detection
│   │   ├── extraction.py          # UPI / phone / URL / bank account extraction
│   │   └── config.py              # Environment-based configuration
│   ├── models.py                  # Pydantic models & data structures
│   ├── middleware.py              # Security, rate limiting, logging
│   ├── callback.py                # Final callback handling
│   └── webhook_manager.py         # Real-time event notifications
├── db/
│   ├── client.py                  # PostgreSQL (Neon) connection
│   └── repository.py              # Session/intel CRUD
├── data/
│   ├── feedback.json              # Human corrections store
│   └── trust_profiles.json        # Sender trust profiles
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.js            # Command Center dashboard
│       │   ├── sessions/          # Session management UI
│       │   ├── intelligence/      # Intelligence Hub
│       │   ├── map/               # World threat map
│       │   ├── feedback/          # Self-learning & trust dashboard
│       │   ├── telemetry/         # Live monitoring
│       │   └── multi-simulator/   # Multi-agent simulator
│       └── components/
│           ├── Sidebar.js         # Navigation
│           └── WorldThreatMap.js  # GeoJSON threat map
├── tests/                         # Test + evaluation suite
│   ├── test_comprehensive.py      # Smart eval runner (86 messages, caching)
│   ├── evaluation_dataset_v2.json # 86-message evaluation dataset
│   ├── test_feedback.py           # Self-learning tests
│   ├── test_trust.py              # Trust profile tests
│   └── test_trust_tracking.py     # Real-result trust tracking tests
├── requirements.txt
└── .env
```

---

## 🧪 Evaluation

Evaluated against an **86-message dataset** across **18 scam categories** (49 scam, 37 legitimate):

| Metric | Value |
|--------|-------|
| **Accuracy** | **87.21%** |
| **Recall (Sensitivity)** | **100%** |
| **Precision** | **81.67%** |
| **F1-Score** | **89.91%** |
| **False Positive Rate** | **29.73%** |
| **False Negative Rate** | **0%** |

**Key insight:** The system prioritizes catching every scam (0 false negatives) over avoiding all false positives — appropriate for a honeypot where the agent only engages on high-confidence scams and passes everything else through untouched.

**Note:** Earlier evaluations (40-message) showed 67.5% accuracy / 40% recall. The current results reflect major detection and prompt improvements.

---

## 🎯 Use Cases

- **WhatsApp / Telegram / Email Scam Detection** — monitor channels for scam patterns
- **Cybercrime Intelligence** — aggregate scammer infrastructure for takedowns
- **Compromised-Contact Protection** — alert users when known contacts act suspiciously
- **Enterprise Security** — protect employees from business email compromise
- **Law Enforcement** — actionable intelligence for investigations
- **Offensive Deception** — waste scammers' time and resources at scale

---

## 🔒 Security Features

- ✅ **API Key Authentication** — required for all endpoints
- ✅ **Rate Limiting** — protection against abuse
- ✅ **Sensitive Data Protection** — API keys excluded from logs
- ✅ **Data Encryption** — extracted intelligence encrypted (Fernet)
- ✅ **Graceful Degradation** — Groq → Gemini (backup) → fallback chain
- ✅ **Safe Exits** — pressure-triggered immediate disengagement

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---

## 📝 License

MIT License — see the [LICENSE](LICENSE) file.

---

## 📧 Contact

- **GitHub**: https://github.com/123AmaanHussain/honey-pot_agent
- **Issues**: https://github.com/123AmaanHussain/honey-pot_agent/issues

---

## 🙏 Acknowledgments

- **Groq** — ultra-fast LLM inference (Qwen 3.8-27B)
- **Google Gemini** — backup LLM + vision intelligence
- **FastAPI** — web framework
- **Next.js / React** — modern dashboard

---

**Built with ❤️ for safer digital communications and cybercrime prevention**