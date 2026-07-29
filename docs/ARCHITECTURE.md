# 🍯 Honey-Pot Scam Detection API — Architecture

> AI-powered FastAPI backend that intercepts scam messages, engages scammers with realistic personas, and extracts intelligence (UPI IDs, phone numbers, phishing links, bank accounts).

---

## Module Architecture

```mermaid
flowchart TD
    EXT["🌐 External Client\n(Organizer / Test Script)"]
    MW["🛡️ Middleware Stack\nmiddleware.py\n─────────────────\n① RequestIDMiddleware\n② RateLimitMiddleware\n③ RequestLoggingMiddleware\n④ SecurityHeadersMiddleware"]
    MAIN["🚀 FastAPI App\nmain.py\n─────────────────\nPOST /honeypot/message\nGET  /intelligence\nGET  /health\nGET  /metrics\nGET  /sessions/{id}"]
    SESSION["📦 In-Memory Session Store\nDict session_id → SessionData\n─────────────────\n• confidence score\n• turns count\n• message_history\n• behavior_patterns\n• scammer_type & profile\n• current_persona"]
    DET["🔍 detection.py\n─────────────────\n• detect_scam()\n• detect_repetition()\n• detect_escalation()\n• update_confidence()"]
    EXT_MOD["🧠 extraction.py\n─────────────────\n• extract_upi_ids()\n• extract_phone_numbers()\n• extract_urls()\n• extract_bank_accounts()\n• merge_intelligence()"]
    AGENT["🤖 agent.py\n─────────────────\n• generate_reply()\n• generate_exit_message()\n• profile_scammer()\n• process_image_for_intel()"]
    PM["🎭 persona_manager.py\n─────────────────\n7 Personas by confidence band:\n1.0→0.8  Confused User\n0.8→0.6  Busy Professional\n0.6→0.5  Nervous Elder\n0.5→0.4  Curious Student\n0.4→0.3  Over-Polite\n0.3→0.15 Paranoid User\n0.15→0.0 Tech-Savvy"]
    LLM["☁️ LLM Layer\n─────────────────\nPrimary:  Groq - Llama 3\nFallback: Gemini Flash\nVision:   Gemini Vision"]
    WH["📡 webhook_manager.py\nEventManager\n─────────────────\nINTEL_EXTRACTED\nSCAMMER_AGGRESSIVE\nSESSION_COMPLETED"]
    CB["📬 callback.py\nsend_final_callback()\n─────────────────\nHTTP POST to organizer\nwhen session ends"]
    CFG["⚙️ config.py\nSettings - Pydantic\n─────────────────\nAPI keys, thresholds,\nwebhook URLs, model names"]
    MODELS["📐 models.py\nPydantic Schemas\n─────────────────\nSessionData\nExtractedIntelligence\nScammerType Enum\nMessageResponse, etc."]

    EXT -->|"POST /honeypot/message"| MW
    MW --> MAIN
    MAIN -->|"load / create"| SESSION
    MAIN -->|"message + behavior_patterns"| DET
    DET -->|"is_scam, flags, confidence delta"| MAIN
    MAIN -->|"message text + flags"| EXT_MOD
    EXT_MOD -->|"upiIds, phoneNumbers, links, accounts"| MAIN
    MAIN -->|"confidence + message + persona + imageData"| AGENT
    AGENT -->|"select persona"| PM
    AGENT -->|"build prompt"| LLM
    LLM -->|"text reply"| AGENT
    AGENT -->|"reply, new_persona, scanned_intel"| MAIN
    MAIN -->|"notify on intel / aggression / completion"| WH
    MAIN -->|"session completed"| CB
    CFG -.->|"settings"| MAIN
    CFG -.->|"settings"| AGENT
    CFG -.->|"settings"| WH
    MODELS -.->|"type definitions"| MAIN
    MODELS -.->|"type definitions"| AGENT
```

---

## Request Lifecycle — `POST /honeypot/message`

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as Middleware
    participant API as main.py
    participant DET as detection.py
    participant EXT as extraction.py
    participant AGT as agent.py
    participant LLM as Groq / Gemini
    participant WH as webhook_manager

    C->>MW: POST /honeypot/message
    MW->>API: attach request_id, check rate-limit, log
    API->>API: load or create SessionData
    API->>DET: detect_scam(message, history, behavior)
    DET-->>API: is_scam, flags, confidence, repetition, escalation

    alt Not a scam
        API-->>C: reply null, agent_engaged false
    else Scam detected
        API->>EXT: extract_all_intelligence(message, flags)
        EXT-->>API: upiIds, phones, links, accounts, keywords
        API->>WH: notify_intel_extracted() async
        API->>AGT: generate_reply(confidence, message, persona, image?)
        AGT->>LLM: prompt with persona context
        LLM-->>AGT: reply text
        AGT-->>API: reply, new_persona, scanned_intel
        opt Exit condition met
            API->>AGT: generate_exit_message()
            API->>WH: notify_session_completed() async
        end
        API-->>C: status success, reply text
    end
```

---

## Persona Switching by Confidence

```mermaid
flowchart LR
    C10["confidence ≥ 0.8\n😕 Confused User"]
    C08["0.6 – 0.8\n💼 Busy Professional"]
    C06["0.5 – 0.6\n👴 Nervous Elder"]
    C05["0.4 – 0.5\n🎓 Curious Student"]
    C04["0.3 – 0.4\n🙏 Over-Polite"]
    C03["0.15 – 0.3\n😰 Paranoid User"]
    C015["< 0.15\n🔬 Tech-Savvy Skeptic"]
    EXIT["🚪 Exit + Final Callback"]

    C10 -->|"confidence drops"| C08
    C08 --> C06
    C06 --> C05
    C05 --> C04
    C04 --> C03
    C03 --> C015
    C015 -->|"exit triggered"| EXIT
```

---

## Intelligence Extraction Targets

| Category | Regex Pattern | Example |
|---|---|---|
| **UPI IDs** | `user@provider` | `scammer@paytm` |
| **Phone Numbers** | `+91` / `91` / `6-9XXXXXXXXX` | `9876543210` |
| **Phishing Links** | `http://`, `www.`, `domain.tld` | `verifybank.co/login` |
| **Bank Accounts** | 11–18 digit numbers | `012345678901` |
| **Suspicious Keywords** | Scam keyword flags | `urgent`, `otp`, `kyc` |
| **Image OCR** | Gemini Vision on base64 image | QR codes, UPI screenshots |

---

## Key Files

| File | Role |
|---|---|
| `main.py` | FastAPI app, all endpoints, session store, orchestration |
| `detection.py` | Rule-based scam detection, confidence scoring |
| `extraction.py` | Regex-based intelligence extraction |
| `agent.py` | LLM reply generation, image OCR, scammer profiling |
| `persona_manager.py` | 7 dynamic personas, confidence-based switching |
| `middleware.py` | Request ID, logging, rate limiting, security headers |
| `webhook_manager.py` | Async real-time event notifications |
| `callback.py` | Final session-end HTTP callback to organizer |
| `config.py` | All settings via Pydantic (env vars) |
| `models.py` | All Pydantic schemas and enums |
