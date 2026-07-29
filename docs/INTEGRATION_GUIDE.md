# 🔌 Honey-Pot API — Platform Integration Guide

> This guide explains how to connect the Honey-Pot Scam Detection API to different messaging platforms (SMS, WhatsApp, Telegram, Gmail, etc.).

**Live API Base URL:** `https://honey-pot-agent.onrender.com`

---

## 🧠 Core Concept — The Bridge Pattern

The Honey-Pot API is **platform-agnostic**. For every platform, the integration follows the same 3-step pattern:

```
[Incoming Message from Platform]
        ↓
[Bridge/Webhook Handler]   ← you write this per platform
        ↓
POST /honeypot/message     ← your Honey-Pot API
        ↓
[Reply sent back to Platform]
```

### Minimum Required Payload

```json
{
  "sessionId": "<unique-sender-id>",
  "message": {
    "sender": "scammer",
    "text": "<message content>"
  },
  "metadata": {
    "channel": "<PLATFORM_NAME>"
  }
}
```

### API Response

- **Scam detected** → `{ "status": "success", "reply": "Agent's response..." }`
- **Legitimate message** → `{ "status": "success", "reply": null }` — pass through to real user, do not auto-reply.

---

## 📱 Platform Integrations

---

### 1. Telegram (Easiest)

**Mechanism:** Telegram Bot API Webhooks

**Steps:**
1. Create a bot via [@BotFather](https://t.me/BotFather) and get the bot token.
2. Set a webhook on your bridge server:
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-bridge.com/telegram
   ```
3. Bridge code (Python/Flask example):

```python
from flask import Flask, request
import requests

app = Flask(__name__)
TELEGRAM_TOKEN = "your_bot_token"
HONEYPOT_API = "https://honey-pot-agent.onrender.com/honeypot/message"
HONEYPOT_KEY = "your_api_key"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.json
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    # Call Honey-Pot API
    response = requests.post(HONEYPOT_API, json={
        "sessionId": f"telegram_{chat_id}",
        "message": {"sender": "scammer", "text": text},
        "metadata": {"channel": "Telegram"}
    }, headers={"x-api-key": HONEYPOT_KEY})

    reply = response.json().get("reply")

    # Send reply back to Telegram only if scam detected
    if reply:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )

    return "OK"
```

---

### 2. WhatsApp

**Mechanism:** [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp) or Twilio for WhatsApp

**Steps:**
1. Set up a WhatsApp Business Account (Meta) or use Twilio sandbox.
2. Configure a webhook that receives incoming messages.
3. Bridge code (Twilio example):

```python
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

app = Flask(__name__)
HONEYPOT_API = "https://honey-pot-agent.onrender.com/honeypot/message"
HONEYPOT_KEY = "your_api_key"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    sender = request.form.get("From")   # e.g. whatsapp:+919876543210
    text = request.form.get("Body", "")

    response = requests.post(HONEYPOT_API, json={
        "sessionId": f"whatsapp_{sender}",
        "message": {"sender": "scammer", "text": text},
        "metadata": {"channel": "WhatsApp"}
    }, headers={"x-api-key": HONEYPOT_KEY})

    reply = response.json().get("reply")

    twiml = MessagingResponse()
    if reply:
        twiml.message(reply)

    return str(twiml)
```

> **Note:** WhatsApp Business API requires business verification from Meta. For testing, use the **Twilio WhatsApp Sandbox**.

---

### 3. SMS (via Twilio / MSG91)

**Mechanism:** Incoming SMS webhook

**Steps:**
1. Buy a Twilio phone number and configure the webhook URL.
2. Bridge code:

```python
from flask import Flask, request
from twilio.rest import Client
import requests

app = Flask(__name__)
TWILIO_SID = "your_account_sid"
TWILIO_TOKEN = "your_auth_token"
TWILIO_NUMBER = "+1XXXXXXXXXX"
HONEYPOT_API = "https://honey-pot-agent.onrender.com/honeypot/message"
HONEYPOT_KEY = "your_api_key"

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

@app.route("/sms", methods=["POST"])
def sms_webhook():
    sender = request.form.get("From")
    text = request.form.get("Body", "")

    response = requests.post(HONEYPOT_API, json={
        "sessionId": f"sms_{sender}",
        "message": {"sender": "scammer", "text": text},
        "metadata": {"channel": "SMS"}
    }, headers={"x-api-key": HONEYPOT_KEY})

    reply = response.json().get("reply")

    if reply:
        twilio_client.messages.create(
            body=reply,
            from_=TWILIO_NUMBER,
            to=sender
        )

    return "OK"
```

---

### 4. Gmail

**Mechanism:** Gmail API + Google Cloud Pub/Sub push subscription

**Steps:**
1. Enable the Gmail API in [Google Cloud Console](https://console.cloud.google.com/).
2. Set up a Pub/Sub topic and grant Gmail permission to publish to it.
3. Create a push subscription pointing to your bridge server.
4. Bridge code:

```python
import base64, json
from flask import Flask, request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests

app = Flask(__name__)
HONEYPOT_API = "https://honey-pot-agent.onrender.com/honeypot/message"
HONEYPOT_KEY = "your_api_key"

@app.route("/gmail", methods=["POST"])
def gmail_push():
    envelope = request.json
    message_data = base64.urlsafe_b64decode(envelope["message"]["data"]).decode()
    notification = json.loads(message_data)

    # Use Gmail API to fetch the actual email content
    email_id = notification.get("historyId")
    sender = notification.get("emailAddress", "unknown@gmail.com")
    email_body = fetch_email_body(email_id)  # implement using Gmail API

    response = requests.post(HONEYPOT_API, json={
        "sessionId": f"gmail_{sender}",
        "message": {"sender": "scammer", "text": email_body},
        "metadata": {"channel": "Gmail"}
    }, headers={"x-api-key": HONEYPOT_KEY})

    reply = response.json().get("reply")

    if reply:
        send_gmail_reply(sender, reply)  # implement using Gmail API

    return "OK"
```

> **Note:** Gmail integration is the most complex. It requires OAuth2, service accounts, and Pub/Sub. Best suited for automated monitoring pipelines rather than real-time chat.

---

### 5. Custom Chat Application

If you have your own messaging app (React, Flutter, etc.), call the API directly:

```javascript
// Frontend JavaScript example
async function sendToHoneypot(sessionId, messageText) {
  const response = await fetch("https://honey-pot-agent.onrender.com/honeypot/message", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": "your_api_key"
    },
    body: JSON.stringify({
      sessionId: sessionId,
      message: { sender: "scammer", text: messageText },
      metadata: { channel: "CustomApp" }
    })
  });

  const data = await response.json();

  if (data.reply) {
    // Scam detected — show agent's reply
    displayMessage(data.reply);
  } else {
    // Legitimate message — show original to user
    displayMessage(messageText);
  }
}
```

---

## 🖼️ Image/Screenshot Support

Your API supports **multimodal vision** (OCR + QR code analysis). To send an image, add a `imageData` field:

```json
{
  "sessionId": "session-001",
  "message": {
    "sender": "scammer",
    "text": "See this payment proof",
    "imageData": "<base64-encoded-image>"
  }
}
```

This works across all platforms — just extract the image, base64-encode it, and include it in the payload.

---

## ⚠️ Important Limitations

| Issue | Details |
|-------|---------|
| **In-memory sessions** | Sessions are lost on server restart. For production use across multiple platforms, integrate a **Redis** or **database** backend. |
| **Rate limit** | 100 requests/minute. Monitor usage if running on multiple busy platforms simultaneously. |
| **India-focused detection** | Keywords like UPI, KYC, OTP, Paytm are India-centric. Expand `SCAM_KEYWORDS` in `detection.py` for global platforms. |
| **No reply persistence** | The API does not store sent replies. Add logging in your bridge layer for audit trails. |

---

## 🏗️ Recommended Architecture for Multi-Platform Use

```
                  ┌─────────────────────────────┐
                  │     Universal Bridge Server  │
                  │  (Flask / FastAPI / Node.js)  │
                  └───────────┬─────────────────┘
          ┌────────┬──────────┼──────────┬────────┐
          ▼        ▼          ▼          ▼        ▼
       Telegram  WhatsApp   Gmail      SMS    Custom App
       Webhook   Webhook   Pub/Sub   Twilio  Direct HTTP
          │        │          │          │        │
          └────────┴──────────┴──────────┴────────┘
                              │
                              ▼
              POST /honeypot/message
          (Honey-Pot Scam Detection API)
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Intelligence Store   │
                  │  GET /intelligence    │
                  └───────────────────────┘
```

---

## 🔑 API Endpoints Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/honeypot/message` | POST | API Key | Main scam detection endpoint |
| `/intelligence` | GET | API Key | All aggregated scammer intel |
| `/session/{id}` | GET | API Key | Specific session details |
| `/health` | GET | None | Server health check |
| `/metrics` | GET | None | Usage statistics |

**Header required for authenticated endpoints:**
```
x-api-key: your_api_key_here
```

---

*Built for the GUVI Hackathon — Honey-Pot AI Scam Detection System*
