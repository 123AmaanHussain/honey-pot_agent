# 🍯 Honey-Pot: AI-Powered Cybercrime Detection & Intelligence System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)

> **An autonomous AI agent that silently monitors messaging channels, detects scam messages with a hybrid LLM engine, engages scammers using human-like adaptive personas, extracts actionable cybercrime intelligence in real-time, and terminates engagements intelligently — all while leaving legitimate conversations completely untouched.**

---

## Table of Contents

1. [What It Does — High-Level Overview](#1-what-it-does--high-level-overview)
2. [End-to-End Flow](#2-end-to-end-flow)
3. [Layer 1 — Channel Monitoring](#3-layer-1--channel-monitoring)
4. [Layer 2 — Scam Detection Engine](#4-layer-2--scam-detection-engine)
5. [Layer 3 — Self-Learning Feedback System](#5-layer-3--self-learning-feedback-system)
6. [Layer 4 — Sender Trust Profiles](#6-layer-4--sender-trust-profiles)
7. [Layer 5 — Persona Engine & Reply Generation](#7-layer-5--persona-engine--reply-generation)
8. [Layer 6 — Intelligence Extraction](#8-layer-6--intelligence-extraction)
9. [Layer 7 — Exit Strategy](#9-layer-7--exit-strategy)
10. [Layer 8 — Persistence, Webhooks & Callbacks](#10-layer-8--persistence-webhooks--callbacks)
11. [Layer 9 — Dashboard & Analytics](#11-layer-9--dashboard--analytics)
12. [Architecture Diagram](#12-architecture-diagram)
13. [API Reference](#13-api-reference)
14. [Performance Benchmarks](#14-performance-benchmarks)
15. [Tech Stack](#15-tech-stack)
16. [Quick Start](#16-quick-start)
17. [Configuration Reference](#17-configuration-reference)
18. [Project Structure](#18-project-structure)
19. [Use Cases](#19-use-cases)

---

## 1. What It Does — High-Level Overview

Honey-Pot sits invisibly between your messaging channels (WhatsApp, Telegram, Email, SMS) and the user. Every incoming message passes through the system. For **legitimate messages**, the system does absolutely nothing — the message flows through to the user without any delay or modification (**Pass-Through Mode**).

When a **scam message** is detected, the system takes full control of the conversation. It replies to the scammer using a dynamically selected AI persona — never from a template, always live-generated — while simultaneously extracting criminal intelligence from the conversation (UPI IDs, phone numbers, phishing links, bank account numbers). Once sufficient intelligence is collected or the scammer escalates to threatening behaviour, the agent terminates the engagement gracefully and files a complete intelligence report.

**What makes it different from a spam filter:**
- A spam filter *blocks* messages. Honey-Pot *engages* scammers — wasting their time, extracting their infrastructure details, and building a dossier on their tactics.
- It adapts. The personas switch dynamically based on real-time scam confidence. No two conversations look the same.
- It learns. Human corrections feed a three-layer self-learning system that permanently improves future detection accuracy.
- It tracks identities. A trust profile system tracks sender behaviour across sessions, specifically to detect when a trusted contact's account has been compromised.

---

## 2. End-to-End Flow

```
Incoming Message (WhatsApp / Telegram / Email / SMS)
        │
        ▼
┌─────────────────────────────────┐
│   Channel Monitor               │  Receives raw message via platform API
│   (whatsapp-web.js / Telethon   │  Forwards to /honeypot/message endpoint
│    / Gmail IMAP / ADB SMS)      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   API Gateway (FastAPI)         │  Auth, rate limiting, request ID tracking
│   Middleware Stack              │  Security headers, per-IP rate limiting
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Session Manager               │  Load/create in-memory session
│                                 │  Append message to rolling history (10 msgs)
│                                 │  Update last_activity timestamp
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Scam Detection Engine         │  5-step hybrid analysis:
│   (app/core/detection.py)       │  1. Keyword match (16 scam keywords)
│                                 │  2. Repetition analysis (SequenceMatcher)
│                                 │  3. Escalation pattern detection
│                                 │  4. Feedback cache check (skip LLM if hit)
│                                 │  5. LLM analysis (Groq → Gemini fallback)
└────────────────┬────────────────┘
                 │
          ┌──────┴──────┐
          │             │
     NOT SCAM        SCAM DETECTED
          │             │
          ▼             ▼
   Pass-Through    ┌────────────────────────────┐
   reply=None      │  Intelligence Extraction    │
   agent_engaged   │  (app/core/extraction.py)   │
   =False          │  UPI IDs, phone numbers,    │
                   │  phishing URLs, bank accts  │
                   └────────────┬───────────────┘
                                │
                                ▼
                   ┌────────────────────────────┐
                   │  Confidence Score Update    │
                   │  Multi-factor decay:        │
                   │  base keywords + repetition │
                   │  + escalation multipliers   │
                   └────────────┬───────────────┘
                                │
                                ▼
                   ┌────────────────────────────┐
                   │  Scammer Profiling          │
                   │  (after turn 2)             │
                   │  Tech Support / Banking /   │
                   │  Romance / Job / Prize...   │
                   └────────────┬───────────────┘
                                │
                                ▼
                   ┌────────────────────────────┐
                   │  Exit Decision              │
                   │  - Confidence ≤ threshold?  │
                   │  - Intel collected + 3 turns│
                   │  - Turn limit reached (15)? │
                   │  - Pressure detected?       │
                   └────────────┬───────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
                 CONTINUE               EXIT SESSION
                    │                        │
                    ▼                        ▼
          ┌──────────────────┐    ┌──────────────────────┐
          │  Persona Engine  │    │  Exit Message Gen     │
          │  Select/Switch   │    │  Persona-appropriate  │
          │  persona by conf │    │  natural disengagement│
          │  Generate reply  │    │  Final callback fire  │
          │  via LLM (Groq)  │    │  Completion webhook   │
          └────────┬─────────┘    └──────────────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  DB Persistence  │
          │  (Neon PostgreSQL│
          │  or memory-only) │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  API Response    │
          │  {status, reply, │
          │   confidence,    │
          │   intel, turns}  │
          └──────────────────┘
```

---

## 3. Layer 1 — Channel Monitoring

The system monitors four messaging channels simultaneously. Each channel runs as an independent subprocess and forwards messages to the central FastAPI backend.

### WhatsApp (`local_agent/` — Node.js, whatsapp-web.js)
- Authenticates via QR code scan (no official API required)
- Uses the WhatsApp Web protocol to receive all messages in real-time
- Forwards each message as a POST to `/honeypot/message`
- Sends the agent's reply back through the same WhatsApp session
- Start/stop controlled via REST API (`/monitor/whatsapp/start`, `/monitor/whatsapp/stop`)

### Telegram (`local_agent/` — Python, Telethon MTProto)
- Connects as a user account (not a bot) using MTProto protocol
- Listens to all private messages and group messages
- Forwards and replies through the same Telethon session
- Start/stop controlled via REST API (`/monitor/telegram/start`, `/monitor/telegram/stop`)

### Email (Gmail IMAP Polling)
- Polls Gmail inbox via IMAP every N seconds
- Parses incoming email subjects and bodies
- Replies via SMTP to the sender's address
- Credentials stored encrypted in the database (Fernet symmetric encryption)

### Android SMS (ADB-based)
- Reads SMS messages via Android Debug Bridge
- Forwards to the backend for analysis
- Desktop notifications (Win10toast/plyer) for scam alerts

### Pass-Through Architecture
Every monitor implements the same contract: if `reply` in the API response is `null`, the message is **not** a scam and is passed through to the user completely untouched. If `reply` contains text, the agent sends it to the scammer directly.

---

## 4. Layer 2 — Scam Detection Engine

**File:** [`app/core/detection.py`](app/core/detection.py)

Detection is a 5-step pipeline. All steps must contribute before a message is flagged as a scam. A minimum of 2 evidence indicators is required — single-keyword matches alone do not trigger engagement.

### Step 1 — Keyword Analysis
16 scam-relevant keywords are checked against the message:
```
blocked, suspended, verify, urgent, immediately, account, upi, otp,
kyc, refund, prize, final, warning, expire, deactivate, confirm
```
Each keyword match adds a flag to the detection result.

### Step 2 — Repetition Detection
Uses Python's `difflib.SequenceMatcher` to compare the current message against the last 5 messages in the session history. A similarity ratio ≥ 0.7 marks the message as repetitive — a strong scam signal (scammers repeat pressure messages when ignored).

```python
# Example: "Your account is blocked. Pay now." vs "Account blocked! Pay immediately!"
# Similarity ratio: ~0.74 → repetition_detected = True
```

### Step 3 — Escalation Detection
Tracks `urgency` and `threat` pattern counts from `session.behavior_patterns`. If either reaches ≥ 2 occurrences, or if the message contains final-warning language ("final", "last", "ultimate", "warning", "chance"), escalation is flagged. Escalation events trigger an `SCAMMER_AGGRESSIVE` webhook event.

### Step 4 — Self-Learning Feedback Cache Check
Before calling the LLM, the system checks the FP (False Positive) cache. If an identical or near-identical message (similarity ≥ 0.85) has been human-corrected before, the cached result is returned instantly — the LLM call is skipped entirely. This drastically reduces latency for repeated message patterns and stops the model from making the same mistakes twice.

### Step 5 — LLM-Based Analysis (Groq → Gemini Fallback)
A structured prompt is sent to the Groq API (Qwen 3.8B/27B) asking it to evaluate the message across five dimensions:
1. **Sender trust signals** — does it look like an authoritative impersonator?
2. **Greeting analysis** — normal greetings are not scams even if they mention accounts
3. **Scam indicator scanning** — UPI requests, OTP asks, urgency, prizes, threats
4. **Conversation flow analysis** — romance scams build trust over multiple turns before asking for money
5. **Minimum evidence gate** — requires ≥ 2 confirmed indicators before flagging

If Groq is unavailable, Google Gemini is used as the fallback with an automatic retry loop.

### Confidence Scoring
Every flagged detection returns a confidence score that is used to decay the session's trust score:

```
new_confidence = old_confidence × decay_factor
```

Decay factors compound: base keyword decay + repetition multiplier + escalation multiplier. A session that starts at `confidence = 1.0` drops toward `0.0` as the scammer becomes more aggressive and repetitive.

---

## 5. Layer 3 — Self-Learning Feedback System

**File:** [`app/core/feedback.py`](app/core/feedback.py)

The feedback system has three independent learning mechanisms that activate automatically from human corrections submitted via the `/feedback` endpoint.

### Mechanism 1 — False Positive (FP) Cache
Every human correction (FP or FN) is stored in `data/feedback.json`. Before each detection, the system checks whether the incoming message matches any corrected message at ≥ 85% similarity using `SequenceMatcher`. A cache hit returns the corrected label immediately — no LLM call, no latency, guaranteed correct result.

### Mechanism 2 — Few-Shot Example Injection
When the LLM is called, the system retrieves the top-4 most relevant past corrections (ranked by similarity to the current message). These are injected into the LLM prompt as labelled examples:

```
IMPORTANT CORRECTIONS FROM HUMAN REVIEWERS:
Example 1:
  Message: "Your bank account has been blocked due to KYC..."
  Correct label: legitimate
  Category: bank_notification
  Why: Automated bank notifications use this phrasing — not a scam
```

This teaches the LLM the specific patterns it tends to get wrong in this deployment context, without any fine-tuning.

### Mechanism 3 — Pattern Extraction
When 3+ false positives accumulate in the same category, the system automatically extracts a pattern rule:

```python
# Example extracted pattern:
{
    "type": "category_override",
    "category": "bank_notification",
    "action": "reduce_scam_score",
    "reason": "5 false positives in 'bank_notification' — likely legitimate"
}
```

Keywords appearing in 3+ FP messages are also flagged as unreliable scam indicators and suppressed in future detections.

---

## 6. Layer 4 — Sender Trust Profiles

**File:** [`app/core/trust.py`](app/core/trust.py)

Every sender gets a persistent trust profile stored in `data/trust_profiles.json`. The profile tracks:
- Total interaction count
- Message type breakdown (greetings, casual, requests, scam_indicators)
- Timestamp of first and last interaction
- All scam flags with timestamps

### Trust Level Progression

```
UNKNOWN  ──(2+ normal interactions)──►  KNOWN
KNOWN    ──(5+ interactions, 0 flags)──► TRUSTED
ANY      ──(1+ scam flag detected)───►  SUSPICIOUS
```

### Compromised Account Detection
This is the system's most sophisticated trust feature. A contact who has been interacting normally for months and is marked `TRUSTED` — if they suddenly send a message with scam indicators — gets flagged as `SUSPICIOUS` rather than being treated as a random scammer.

This is the fingerprint of a **compromised account**: the account owner's contact list is being exploited by a scammer who has taken over the account. The system immediately alerts the user that a trusted contact may have been hacked.

### Trust-Based Detection Bypass
Contacts with `TRUSTED` status who send casual messages (greetings, everyday conversation) have their messages skip the LLM detection step entirely. This reduces false positive rates for frequent legitimate contacts and cuts unnecessary API calls.

---

## 7. Layer 5 — Persona Engine & Reply Generation

**Files:** [`app/core/persona_manager.py`](app/core/persona_manager.py), [`app/core/agent.py`](app/core/agent.py)

### 7 Adaptive Personas

Each persona is mapped to a confidence score range. As the session confidence decays (scammer becomes more aggressive), the persona switches automatically:

| Confidence Range | Persona | Voice Style |
|---|---|---|
| 0.85 – 1.0 | 🤔 **Confused User** | "wait what?", "huh?", wrong assumptions, easily distracted |
| 0.70 – 0.85 | 💼 **Busy Professional** | "make it quick", "I'm in a meeting", one-word answers |
| 0.55 – 0.70 | 👴 **Nervous Elder** | "oh my", "I need to ask my son", worried but cooperative |
| 0.40 – 0.55 | 🎓 **Curious Student** | "oh wow really?", "how does that work?", genuinely interested |
| 0.25 – 0.40 | 🙏 **Over-Polite** | "oh no no, I'm so sorry!", excessive apologies |
| 0.10 – 0.25 | 😰 **Paranoid User** | "how did you get my number?", suspicious of everything |
| 0.00 – 0.10 | 🖥️ **Tech-Savvy Skeptic** | "hmm interesting, let me verify that", demands proof |

### Reply Generation Pipeline

1. **Pressure Detection** — scans for 6 categories of pressure tactics (urgency, threat, fear, authority, isolation, aggression). If detected, mode is forced to `EXIT` regardless of confidence level.

2. **Mode Decision**:
   - `confidence > 0.5` → `NORMAL` mode (engage, extract intel)
   - `0.25 < confidence ≤ 0.5` → `DEFLECTION` mode (stall, buy time)
   - `confidence ≤ 0.25` → `EXIT` mode (disengage)

3. **Topic Detection** — identifies the conversation topic (PAYMENT, OTP, LINK, BANK, GENERAL) to keep the persona's questions contextually relevant.

4. **Persona Prompt Construction** — builds a detailed prompt including:
   - Full persona description and behavioural traits
   - Anti-hallucination rules (never invent facts not in conversation)
   - Conversation history (last N turns for context)
   - Extracted intel so far (to avoid asking for same info twice)
   - Sender trust context from the trust profile system
   - Few-shot correction examples from the feedback system
   - Current mode (NORMAL / DEFLECTION / EXIT) with specific instructions

5. **LLM Call (Groq → Gemini fallback)** — the prompt is sent to Groq (Qwen 3.8B/27B) for real-time generation. Max 350 tokens per reply.

6. **Response Validation** — the generated reply is checked for:
   - Robotic/corporate phrases that break the persona (`"I understand your concern"`, `"I apologize for the inconvenience"`)
   - Word count limits (too long = unnatural)
   - Hallucinated content (numbers or names not present in the conversation)
   - If validation fails, a safe fallback response is used

7. **Response Humanisation** — applies natural language variations: contractions, hesitation markers, incomplete thoughts, emotional reactions.

8. **Vision/OCR Support** — if the scammer sends an image (`imageData` field in the request), Gemini Vision analyses the image for UPI QR codes, screenshots of fake banking pages, or phishing links embedded in images.

### Persona Switching & History
Every time the persona switches, the event is recorded in `session.persona_history` with the turn number and confidence at the time of switch. This creates a full audit trail of how the conversation evolved.

---

## 8. Layer 6 — Intelligence Extraction

**File:** [`app/core/extraction.py`](app/core/extraction.py)

Every scam message is scanned for five types of cybercrime intelligence using compiled regex patterns:

### UPI ID Extraction
```python
Pattern: [\w\.\-]+@[\w\.\-]+
```
Validated against known UPI providers: `paytm`, `phonepe`, `googlepay`, `ybl`, `oksbi`, `okhdfcbank`, `okicici`, `okaxis`, and generic `bank`/`pay`/`wallet` suffixes. Extracted UPI IDs directly identify the scammer's payment collection infrastructure.

### Indian Phone Numbers
```python
Pattern: (?:(?<!\d)\+91[\s\-]?|(?<!\d)91[\s\-]?|(?<!\d))[6-9]\d{9}(?!\d)
```
Handles `+91`, `91`, and plain 10-digit formats. Normalised to bare 10-digit format, deduplicated. Numbers are geo-lookup-ready for operator and state mapping.

### Phishing URLs
```python
Pattern: (?:https?://)?(?:www\.)?[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-z]{2,}(?:/[\w\-\./?%&=]*)?
```
Filtered by TLD validation (`com`, `org`, `net`, `in`, `io`, `co`, `gov`, `edu`). UPI ID false-matches (containing `@`) are excluded. Short matches (< 8 chars) discarded.

### Bank Account Numbers
```python
Pattern: \b\d{11,18}\b
```
Matches 11–18 digit sequences (Indian bank accounts). Excludes 10-digit sequences (phone numbers) and repeated-digit numbers (e.g., `1111111111111`).

### Suspicious Keywords
Keywords extracted directly from detection flags (e.g., `keyword:otp`, `keyword:blocked`) for intelligence tagging and pattern analysis.

### Deduplication & Merging
Each new extraction is merged with the session's existing intelligence using set operations — no duplicates are stored. Intelligence is also merged at the aggregate `/intelligence` endpoint across all sessions.

### Webhook on New Intel
Every time new intelligence is found (items not already in the session), an `INTEL_EXTRACTED` webhook event fires immediately — enabling real-time integration with downstream systems (e.g., cybercrime reporting portals, OSINT platforms).

---

## 9. Layer 7 — Exit Strategy

**File:** [`app/main.py`](app/main.py) — `should_exit()` function

The agent does not engage indefinitely. Three exit conditions are checked after every turn:

### Exit Condition 1 — Confidence Threshold
If `session.confidence ≤ EXIT_CONFIDENCE_THRESHOLD` (configurable, default ~0.1), the conversation has provided overwhelming evidence of scam activity. The agent terminates engagement.

### Exit Condition 2 — Intel Complete
If the session has extracted at least one piece of critical intelligence (UPI ID, phone number, phishing link, bank account, or scanned image text) **and** has completed at least 3 turns, the mission is accomplished. Continuing the conversation beyond this point offers diminishing returns.

This is the key departure from traditional honeypots: **Honey-Pot exits when the job is done**, not when the scammer gives up.

### Exit Condition 3 — Safety Turn Limit
Hard limit of 15 turns per session, regardless of other conditions. Prevents runaway sessions.

### Pressure-Triggered Emergency Exit
If the agent's reply generation detects pressure tactics (any of the 6 pressure categories), `should_exit = True` is returned immediately from `generate_reply()`. The session is marked completed, the exit message is generated, and no further engagement occurs — even if intel has not yet been extracted.

This protects the agent from being baited into an escalating, adversarial situation.

### Exit Message Generation
`generate_exit_message()` creates a persona-appropriate, natural disengagement message that does not reveal the system's identity. The scammer receives a plausible human excuse for ending the conversation.

### Session Completion Events
On exit:
1. `send_final_callback()` — HTTP POST to the organiser endpoint with full session intelligence
2. `EventManager.notify_session_completed()` — real-time completion webhook
3. `session.completed = True` — session frozen, no further processing
4. Full persistence to PostgreSQL

---

## 10. Layer 8 — Persistence, Webhooks & Callbacks

### Database (Neon PostgreSQL)
**Files:** [`app/db/client.py`](app/db/client.py), [`app/db/repository.py`](app/db/repository.py)

Four tables store all system state:

| Table | Contents |
|---|---|
| `sessions` | Session metadata: confidence, turns, persona, scammer_type, completed flag |
| `intelligence` | Extracted UPI IDs, phone numbers, links, bank accounts per session |
| `messages` | Full message history — scammer messages and agent replies, with sender tag |
| `configuration` | Encrypted bot tokens and monitor credentials (Fernet symmetric encryption) |

Write-through persistence: every API call that mutates session state triggers an immediate database write. On startup, sessions are hydrated from the database so state survives server restarts.

**Graceful Degradation:** If the database is unavailable (misconfigured, network issue), the system runs entirely in-memory with zero downtime. The database is re-tried on the next restart.

### Webhooks (Real-Time Events)
**File:** [`app/webhook_manager.py`](app/webhook_manager.py)

Three event types are fired via async HTTP POST to the configured webhook URL:

| Event | Trigger |
|---|---|
| `INTEL_EXTRACTED` | New UPI ID / phone / link / bank account discovered |
| `SCAMMER_AGGRESSIVE` | Escalation pattern detected in scammer behaviour |
| `SESSION_COMPLETED` | Agent terminates the engagement (any exit condition) |

Delivery is fire-and-forget in a background thread — webhook failures do not affect the main request path.

### Final Callback
**File:** [`app/callback.py`](app/callback.py)

On session completion, a structured HTTP POST is sent to the organiser/hackathon endpoint with:
- Full extracted intelligence
- Scammer type classification and profile
- Session timeline (turns, persona history, confidence trajectory)
- Reason for exit

Retry with exponential backoff ensures reliable delivery even under temporary network issues.

---

## 11. Layer 9 — Dashboard & Analytics

**Directory:** [`frontend/`](frontend/)

A Next.js 16 / React 19 dashboard provides real-time visibility into all system activity.

### Command Center (`/`)
- Live metrics cards: total sessions, active sessions, scams detected, intel items collected
- System status panel (backend health, database connectivity, monitor statuses)
- Quick-start guide and scam education content

### Intelligence Hub (`/intelligence`)
- Aggregated view of all extracted intelligence across all sessions
- UPI IDs, phone numbers, phishing links, bank accounts in searchable tables
- One-click links to `cybercrime.gov.in` for reporting extracted scammer data
- PDF report generation (jsPDF) for offline evidence filing

### Session Logs (`/sessions`)
- Session table with per-session detail view
- Confidence trajectory, persona history, turn count
- Full message history (scammer messages + agent replies)
- End/Delete session controls

### Live Chat Simulator (`/multi-simulator`)
- Send test scam messages directly against the API
- See detection results, confidence scores, and agent replies in real-time
- Useful for testing detection accuracy and persona behaviour

### World Threat Map (`/map`)
- Real GeoJSON world map (equirectangular projection)
- Live scam infrastructure clusters by GeoIP lookup of extracted phone numbers/IPs
- Visualises geographic distribution of scammer sources

### Monitor Control Panels (`/telemetry`)
- Start/stop WhatsApp, Telegram, and Email monitors from the UI
- Live terminal output from monitor subprocesses (QR code display, connection status)
- Per-monitor status badges

### Self-Learning Dashboard (`/feedback`)
- View all human corrections submitted
- FP/FN correction breakdown by category
- Extracted pattern rules
- Sender trust profile statistics (UNKNOWN / KNOWN / TRUSTED / SUSPICIOUS counts)

### Prometheus Metrics (`/metrics/prometheus`)
Exposes standard metrics for Grafana integration:
- `honeypot_sessions_total`
- `honeypot_scams_detected_total`
- `honeypot_intel_items_total`
- `honeypot_active_sessions`
- `honeypot_api_requests_total`

---

## 12. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CHANNEL LAYER                                  │
│   WhatsApp (Node.js)  │  Telegram (Telethon)  │  Gmail  │  ADB SMS     │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │  HTTP POST /honeypot/message
┌─────────────────────────────▼───────────────────────────────────────────┐
│                        API GATEWAY (FastAPI)                            │
│   RequestID → RateLimit → SecurityHeaders → Auth → RequestLogging       │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
         ┌────────────────────┼───────────────────────┐
         │                    │                       │
┌────────▼────────┐  ┌────────▼────────┐   ┌─────────▼────────┐
│  Session Manager│  │  Detection      │   │  Trust Profiles  │
│  (in-memory +   │  │  Engine         │   │  (JSON store)    │
│   PostgreSQL)   │  │  Groq + Gemini  │   │  UNKNOWN→TRUSTED │
└─────────────────┘  └────────┬────────┘   └──────────────────┘
                              │
                 ┌────────────┼──────────────┐
                 │                           │
        ┌────────▼────────┐       ┌─────────▼────────┐
        │  Feedback Layer │       │  Intel Extractor  │
        │  FP Cache       │       │  UPI, Phone, URL  │
        │  Few-shot       │       │  Bank Accounts    │
        │  Patterns       │       └─────────┬─────────┘
        └─────────────────┘                 │
                                   ┌────────▼────────┐
                                   │  Persona Engine  │
                                   │  7 Personas      │
                                   │  Groq LLM Reply  │
                                   │  Vision OCR      │
                                   └────────┬─────────┘
                                            │
                          ┌─────────────────┼──────────────────┐
                          │                 │                  │
                 ┌────────▼───┐   ┌─────────▼──────┐  ┌───────▼──────┐
                 │  Webhooks  │   │  DB Persistence│  │  Callback    │
                 │  INTEL     │   │  (Neon Postgres│  │  (Organiser) │
                 │  AGGRESSIVE│   │   + Fernet     │  └──────────────┘
                 │  COMPLETED │   │   encryption)  │
                 └────────────┘   └────────────────┘
                                            │
                                   ┌────────▼────────┐
                                   │  Next.js 16     │
                                   │  Dashboard      │
                                   │  + Grafana      │
                                   └─────────────────┘
```

---

## 13. API Reference

All authenticated endpoints require the `x-api-key` header.

### Core Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/honeypot/message` | ✅ | Process message, get agent reply |
| `GET` | `/intelligence` | ✅ | Aggregated intel from all sessions |
| `GET` | `/sessions` | ✅ | List all sessions (paginated) |
| `GET` | `/sessions/{id}` | ✅ | Full detail for one session |
| `GET` | `/sessions/completed` | ✅ | Completed sessions with full intel |
| `DELETE` | `/sessions/{id}` | ✅ | Delete a session |
| `DELETE` | `/sessions/completed` | ✅ | Bulk-clear completed sessions |

### Self-Learning Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/feedback` | ✅ | Submit human correction (FP/FN) |
| `GET` | `/feedback/stats` | ✅ | Correction statistics by category |
| `GET` | `/feedback/patterns` | ✅ | Extracted pattern rules |

### Trust Profile Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/trust/stats` | ✅ | Trust level distribution stats |
| `GET` | `/trust/profile/{id}` | ✅ | Individual sender trust profile |

### Monitor Control Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/monitor/whatsapp/start` | ✅ | Start WhatsApp monitor |
| `POST` | `/monitor/whatsapp/stop` | ✅ | Stop WhatsApp monitor |
| `GET` | `/monitor/whatsapp/status` | ✅ | Monitor status + QR code |
| `POST` | `/monitor/telegram/start` | ✅ | Start Telegram monitor |
| `POST` | `/monitor/telegram/stop` | ✅ | Stop Telegram monitor |
| `GET` | `/monitor/telegram/status` | ✅ | Telegram connection status |

### Analytics & Monitoring

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/analytics/geo` | ✅ | Geographic scammer distribution |
| `GET` | `/metrics` | ❌ | Session/detection metrics |
| `GET` | `/metrics/prometheus` | ❌ | Prometheus-format metrics |
| `GET` | `/health` | ❌ | Basic health check |
| `GET` | `/health/detailed` | ❌ | Component health + uptime |

### Example — Process a Message

```bash
curl -X POST "http://localhost:8000/honeypot/message" \
     -H "x-api-key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{
       "sessionId": "session-001",
       "message": {
         "sender": "+919876543210",
         "text": "URGENT: Your SBI account is BLOCKED! Send OTP to 9876543210@paytm NOW to unblock!",
         "timestamp": 1770005528731
       },
       "conversationHistory": [],
       "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
     }'
```

**Response (scam detected):**
```json
{
  "status": "success",
  "reply": "oh wait blocked?? but i didnt do anything... do i need to call someone or what",
  "confidence": 0.62,
  "session_id": "session-001",
  "turns": 1,
  "agent_engaged": true,
  "scam_detected": true
}
```

**Response (legitimate message):**
```json
{
  "status": "success",
  "reply": null,
  "confidence": 1.0,
  "session_id": "session-001",
  "turns": 0,
  "agent_engaged": false,
  "scam_detected": false
}
```

---

## 14. Performance Benchmarks

Evaluated against an **86-message dataset** across **18 scam categories** (49 scam, 37 legitimate):

| Metric | Value | Notes |
|---|---|---|
| **Accuracy** | **87.21%** | Overall correct classifications |
| **Recall (Sensitivity)** | **100%** | Zero missed scams |
| **Precision** | **81.67%** | Some legitimate messages flagged |
| **F1-Score** | **89.91%** | Harmonic mean of precision + recall |
| **False Positive Rate** | **29.73%** | Legitimate messages incorrectly flagged |
| **False Negative Rate** | **0%** | No scams missed — safety-critical target |

> **Design intent:** The system is tuned for zero false negatives. In a honeypot context, missing a scam (false negative) is catastrophically worse than engaging with a legitimate message (false positive). The self-learning feedback system's primary job is to drive the false positive rate down over time without sacrificing the 100% recall.

**Scam category coverage (18 types):**
Banking, UPI fraud, OTP phishing, Tech support, Prize/lottery, KYC expiry, Romance, Job offer, Government impersonation, Delivery fraud, Investment fraud, Loan fraud, Insurance fraud, Customs fraud, Tax fraud, Police/legal threat, Electricity disconnection, and Social media account recovery.

---

## 15. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn/Gunicorn | REST API, async request handling |
| **Primary LLM** | Groq (Qwen 3.8B/27B) | High-speed inference for detection + reply |
| **Fallback LLM** | Google Gemini (Flash/Pro) | Backup LLM + vision/OCR for images |
| **Database** | PostgreSQL (Neon cloud) via psycopg2 | Session/intel persistence |
| **Frontend** | Next.js 16, React 19, Recharts, jsPDF | Dashboard, analytics, reports |
| **Encryption** | Fernet symmetric encryption | Encrypted config storage |
| **WhatsApp** | whatsapp-web.js (Node.js) | WhatsApp Web protocol monitor |
| **Telegram** | Telethon (Python MTProto) | Telegram user-account monitor |
| **Email** | Gmail IMAP / SMTP (Python) | Email monitoring + replies |
| **SMS** | ADB (Android Debug Bridge) | Android SMS monitor |
| **Metrics** | Prometheus client | Grafana-ready metrics export |
| **CI/CD** | GitHub Actions + Render | Auto-deploy on push |

---

## 16. Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend and WhatsApp monitor)
- Groq API Key — [console.groq.com](https://console.groq.com)
- Google Gemini API Key — [aistudio.google.com](https://aistudio.google.com) (fallback, optional)
- PostgreSQL database URL (optional — runs in-memory without it)

### Installation

```bash
# Clone the repository
git clone https://github.com/123AmaanHussain/honey-pot_agent.git
cd honey-pot_agent

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration Reference below)
```

### Run the Backend

```bash
# Development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production (2 workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs` (debug mode only)

### Run the Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at: `http://localhost:3000`

---

## 17. Configuration Reference

```env
# ── Authentication ──────────────────────────────────────────────
API_KEY=your_secret_api_key_here          # Required. All API calls need this.

# ── Primary LLM (Groq) ─────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here       # Required for detection + reply generation
GROQ_MODEL=qwen/qwen3.8-27b              # Model to use (Qwen recommended for speed)

# ── Fallback LLM (Gemini) ───────────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key_here   # Optional — used if Groq is unavailable
GEMINI_MODEL=gemini-1.5-flash            # Also used for image/OCR processing

# ── Database ────────────────────────────────────────────────────
DATABASE_URL=postgresql://user:pass@host/db  # Optional — memory-only mode without this
DB_ENABLED=true

# ── Webhooks ────────────────────────────────────────────────────
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://your-webhook-endpoint.com

# ── Callback (Organiser / Hackathon) ───────────────────────────
CALLBACK_URL=https://your-callback-endpoint.com
CALLBACK_ENABLED=true

# ── Rate Limiting ───────────────────────────────────────────────
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100                   # Requests per minute per IP

# ── Detection Tuning ────────────────────────────────────────────
EXIT_CONFIDENCE_THRESHOLD=0.10            # Exit when confidence drops to this
LLM_TEMPERATURE=0.7                       # LLM creativity (lower = more consistent)

# ── Frontend (Next.js) ──────────────────────────────────────────
# Add these to frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_secret_api_key_here
```

---

## 18. Project Structure

```
honey-pot_project/
├── app/
│   ├── main.py                    # FastAPI app — all endpoints, session lifecycle
│   ├── core/
│   │   ├── agent.py               # LLM reply engine, mode decision, pressure exit
│   │   ├── persona_manager.py     # 7 personas, confidence-based switching, prompt builder
│   │   ├── detection.py           # Hybrid detection: keywords + repetition + escalation + LLM
│   │   ├── feedback.py            # Self-learning: FP cache, few-shot injection, patterns
│   │   ├── trust.py               # Sender trust profiles, compromised-account detection
│   │   └── extraction.py          # UPI / phone / URL / bank account extraction (regex)
│   ├── models.py                  # Pydantic models — all request/response schemas
│   ├── config.py                  # Environment-based settings (pydantic-settings)
│   ├── middleware.py              # RequestID, logging, security headers, rate limiting
│   ├── callback.py                # Final session callback with retry/backoff
│   └── webhook_manager.py         # Real-time event notifications (INTEL, AGGRESSIVE, DONE)
├── db/
│   ├── client.py                  # PostgreSQL (Neon) connection management
│   └── repository.py              # CRUD: sessions, intelligence, messages, config
├── data/
│   ├── feedback.json              # Human corrections + extracted patterns (auto-managed)
│   └── trust_profiles.json        # Sender trust profiles (auto-managed)
├── frontend/
│   └── src/app/
│       ├── page.js                # Command Center dashboard
│       ├── sessions/              # Session browser + detail view
│       ├── intelligence/          # Intel hub + PDF export
│       ├── map/                   # GeoJSON world threat map
│       ├── feedback/              # Self-learning + trust stats dashboard
│       ├── telemetry/             # Monitor control panels + live output
│       └── multi-simulator/       # Multi-agent scam simulation tool
├── local_agent/                   # Platform monitors (WhatsApp, Telegram)
├── grafana/                       # Grafana dashboard configs
├── docs/                          # Architecture diagrams, roadmap docs
├── scripts/                       # Utility scripts
├── requirements.txt
└── .env                           # Environment configuration (not committed)
```

---

## 19. Use Cases

| Use Case | How Honey-Pot Helps |
|---|---|
| **Personal Protection** | Deploy on your own phone to automatically handle WhatsApp/Telegram scammers |
| **Cybercrime Intelligence** | Aggregate UPI IDs and phone numbers for bulk reporting to cybercrime.gov.in |
| **Compromised-Contact Protection** | Detect when a trusted contact's account has been hacked |
| **Enterprise Security** | Protect employees from business email compromise and fake vendor scams |
| **Law Enforcement** | Generate structured intelligence reports for police investigations |
| **Scam Research** | Study scammer tactics, message patterns, and pressure escalation strategies |
| **Offensive Deception** | Waste scammers' time and resources at scale, reducing their ROI |

---

## Contact

- **GitHub**: [github.com/123AmaanHussain/honey-pot_agent](https://github.com/123AmaanHussain/honey-pot_agent)
- **Issues**: [github.com/123AmaanHussain/honey-pot_agent/issues](https://github.com/123AmaanHussain/honey-pot_agent/issues)

---

## Acknowledgements

- **Groq** — ultra-fast LLM inference (Qwen 3.8B/27B)
- **Google Gemini** — vision/OCR and fallback LLM
- **FastAPI** — async Python web framework
- **Next.js / React** — modern dashboard
- **Neon** — serverless PostgreSQL

---

*Built for safer digital communications and cybercrime prevention.*