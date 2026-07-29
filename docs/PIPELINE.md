# 🍯 Honey-Pot — Product Roadmap & Development Pipeline

Complete priority-ordered roadmap from current state to full SaaS product.

> **Current State**: Local agent running on PC (WhatsApp + Telegram + Gmail monitors) + API deployed on Render.

---

## ✅ Already Done

| Feature | Status |
|---------|--------|
| Core scam detection API (FastAPI on Render) | ✅ Live |
| Scammer intelligence extraction (UPI, phone, URLs, bank) | ✅ Done |
| WhatsApp local monitor (`whatsapp_monitor.js`) | ✅ Done |
| Telegram local monitor (`telegram_monitor.py`) | ✅ Done |
| Gmail local monitor (`gmail_monitor.py`) | ✅ Done |
| Android SMS monitor script (`sms_monitor_android.py`) | ✅ Done |
| `/intelligence` aggregation endpoint | ✅ Done |

---

## 🔴 Phase 1 — Core Enhancements *(Do First)*

**Priority: High | Effort: 1–3 days each**

### 1.1 User Notifications
When the bot detects a scam and auto-replies, notify the user so they always know what's happening.

- [ ] Send a **Telegram message to yourself** (using Bot API — easiest)
- [ ] **Desktop popup** via `plyer` library (Windows/Mac/Linux)
- [ ] Include: sender info, message snippet, reply sent, intel extracted

### 1.2 Cybercrime Report Generator
After engaging a scammer and collecting intel, auto-generate a formatted report.

- [ ] Pull all extracted intel from the session (UPI, phone, URLs, screenshots)
- [ ] Generate a **pre-filled PDF or text report** in the format expected by cybercrime.gov.in
- [ ] User submits manually (no API exists for auto-submission)
- [ ] Add a CLI command: `python generate_report.py --session <session_id>`

---

## 🟠 Phase 2 — Web Dashboard *(High Impact)*

**Priority: High | Effort: 1–2 weeks**

A beautiful web app that visualizes everything the honey-pot collects.

### 2.1 Scammer Intelligence Dashboard
- [ ] Reads from `/intelligence` API endpoint
- [ ] Shows: total scams caught, UPI IDs, phone numbers, URLs found
- [ ] Session timeline — how long each scammer was engaged
- [ ] Filter/search by channel (WhatsApp, Telegram, Gmail)
- [ ] Export intel as PDF (cybercrime report ready)

### 2.2 Public Scam Message Checker
- [ ] Anyone pastes a suspicious message → instant analysis
- [ ] Shows: **Scam ⚠️ / Safe ✅** verdict with reason
- [ ] Publicly shareable — drives traffic and awareness

### 2.3 Real-time Agent Monitor
- [ ] Live log view — shows messages being processed right now
- [ ] WebSocket or polling from local agent → dashboard
- [ ] Status indicator: agent online/offline per channel

**Tech Stack**: Next.js + Tailwind + your existing Render API

---

## 🟡 Phase 3 — SaaS Platform *(Multi-user)*

**Priority: Medium | Effort: 3–5 weeks**

Transform the single-user setup into a multi-tenant SaaS product.

### 3.1 Auth & Multi-tenancy
- [ ] User sign-up / login (Supabase Auth)
- [ ] Each user gets their own **API key + session namespace**
- [ ] Supabase database stores users, sessions, intel per user

### 3.2 Gmail Cloud Integration *(Free Tier Feature)*
- [ ] User clicks "Connect Gmail" → standard Google OAuth flow
- [ ] Your server runs Gmail polling for each user (no install needed)
- [ ] Fully cloud — no desktop agent required

### 3.3 Telegram Cloud Integration *(Pro Tier Feature)*
- [ ] User provides their `TG_API_ID` + `TG_API_HASH` (from my.telegram.org)
- [ ] Your server runs a Telethon session per user
- [ ] Session isolated per user, stored encrypted

### 3.4 Pricing Tiers
| Plan | Features | Price |
|------|----------|-------|
| **Free** | Gmail monitoring only (cloud) | ₹0 |
| **Pro** | Gmail + Telegram (cloud) + WhatsApp (local agent) + Dashboard | ₹199/mo |
| **Business** | All above + WhatsApp Business API + cybercrime reports | ₹499/mo |

---

## 🟡 Phase 4 — Hybrid Desktop Agent *(WhatsApp Personal)*

**Priority: Medium | Effort: 2–3 weeks**

Package the local WhatsApp monitor as a downloadable app — no code required for users.

### Why Hybrid?
WhatsApp personal accounts cannot be monitored from the cloud (ToS + ban risk).
Solution: run the agent locally on the user's PC, but **connect it to their SaaS account**.

### How it Works
```
User logs into SaaS → goes to "Connect WhatsApp" page
       ↓
Clicks "Download Agent" button (served directly from dashboard)
       ↓
Installs .exe → scans WhatsApp QR once → done forever
       ↓  (sends detections via Agent Token)
SaaS dashboard shows all detections + intel in real-time
```

### Implementation Steps
- [ ] Package `whatsapp_monitor.js` into a standalone `.exe` using **`pkg`**
- [ ] Build a **system tray app** (Electron) with a 🍯 tray icon
  - On/Off toggle
  - Live scam log
  - "Open Dashboard" button
- [ ] Replace hardcoded API key with **Agent Token** from SaaS account
- [ ] **Host the installer on the SaaS dashboard** — "Connect WhatsApp" page has a single download button (`.exe` / `.dmg` / `.AppImage`)
- [ ] Agent Token pre-baked into the download — user never touches config files
- [ ] Auto-update mechanism (check for new versions on launch)
- [ ] Installers: `.exe` (Windows), `.dmg` (Mac), `.AppImage` (Linux)

---

## 🟢 Phase 5 — Android App *(On-device Monitor)*

**Priority: Medium | Effort: 2–3 weeks**

Native Android app that monitors SMS + notifications without needing a PC.

### Planned Features
- [ ] **SMS auto-monitor** — `SmsReceiver` BroadcastReceiver
- [ ] **WhatsApp / Telegram notifications** — `NotificationListenerService`
- [ ] **Auto-reply** through same channel
- [ ] **Background service** — survives phone restarts, 24/7
- [ ] **Minimal UI** — on/off toggle + live scam log
- [ ] Connected to SaaS account via Agent Token (same as desktop)

### Tech Stack Options
- [ ] **Flutter** — cross-platform (Android + iOS someday)
- [ ] **React Native** — reuse JS knowledge
- [ ] **Native Kotlin** — best OS-level access

### Platform Capability
| Channel | Auto-Monitor | Auto-Reply |
|---------|:---:|:---:|
| SMS | ✅ Full | ✅ Full |
| WhatsApp | ✅ Notifications | ⚠️ Limited |
| Telegram | ✅ Notifications | ⚠️ Limited |
| Gmail | ⚠️ Snippet only | ⚠️ Limited |

---

## ⚪ Phase 6 — WhatsApp Business API *(Business Tier)*

**Priority: Low | Effort: 1 week (after Meta approval)**

For users who want a **dedicated trap number** (not their personal WhatsApp).

- [ ] Register WhatsApp Business number via Meta Cloud API
- [ ] Set up incoming message webhook → Honey-Pot API
- [ ] Auto-reply via Meta API
- [ ] No local install needed — fully cloud
- [ ] Offer as **Business tier** feature on SaaS

**Limitation**: Requires a separate phone number (not user's personal WhatsApp).

---

## ⚪ Phase 7 — Other Improvements

**Priority: Low**

| Feature | Description |
|---------|-------------|
| Redis session store | Persist sessions across API restarts |
| Multi-language detection | Expand scam keywords beyond English/Hindi (Tamil, Telugu, etc.) |
| Scam pattern crowdsourcing | Users contribute new scam patterns to improve detection |
| iOS app | Investigate Screen Time API / enterprise MDM — very limited |

---

## 🗺️ Recommended Build Order

```
Phase 1  →  Phase 2  →  Phase 3  →  Phase 4  →  Phase 5  →  Phase 6
Core fixes   Dashboard    SaaS auth    .exe agent   Android     WhatsApp Biz
(days)       (weeks)      (weeks)      (weeks)      (weeks)     (after biz)
```

---

*Current working solution: `local_agent/` on PC — see [`LOCAL_AGENT_GUIDE.md`](local_agent/LOCAL_AGENT_GUIDE.md)*
