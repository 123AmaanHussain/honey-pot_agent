# 📱 Honey-Pot — Mobile & Multi-User Setup Guide

> This guide explains how regular users (on phones & desktop) can use the Honey-Pot scam detection system — without writing any code themselves.

---

## 🗺️ Overview: Two Deployment Modes

### Mode A — Centralized (Recommended for most users)
The API runs on a **shared server** (like Render). Users just talk through a bot or app — the server does all the work.

```
User's Phone → Telegram/WhatsApp Bot → Honey-Pot Server → Auto-reply
```

### Mode B — Self-Hosted
Advanced users run the server themselves on a PC/laptop and expose it via a tunnel.

---

## 🟢 Mode A: Shared Server — Setup for End Users

### Option 1: Telegram Bot (Zero-Install for Users)

This is the **easiest path** for mobile users. No app install needed — Telegram is free and works on all phones.

#### For the Operator (One-Time Setup)

1. **Create a Telegram Bot**
   - Open Telegram → search `@BotFather` → type `/newbot`
   - Get your `BOT_TOKEN`

2. **Deploy the bridge** (if not already done — see `INTEGRATION_GUIDE.md`)

3. **Tell your users:**
   > "Send scam messages to our bot: `t.me/YourBotName`"

#### For the User (Phone Setup)

1. Install **Telegram** (Android / iOS — free)
2. Open the link your operator shares: `t.me/YourBotName`
3. Tap **Start**
4. Paste/forward any suspicious message → the bot auto-replies if it's a scam
5. If `reply = null` → message is likely safe

✅ **Works on: Android, iPhone, any browser**

---

### Option 2: WhatsApp Bot

#### For the Operator

1. Sign up for [Twilio WhatsApp Sandbox](https://www.twilio.com/console/sms/whatsapp/sandbox)
2. Deploy the WhatsApp bridge from `INTEGRATION_GUIDE.md`
3. Share your WhatsApp number with users

#### For the User (Phone Setup)

1. Save the WhatsApp bot number to contacts
2. Send the join code (provided by Twilio sandbox): e.g., `join sky-bright`
3. After that, forward any suspicious message to the number
4. The bot auto-responds with the scam assessment

✅ **Works on: Android, iPhone**

---

### Option 3: Web Interface (Any Browser on Any Device)

You can build a simple web UI on top of the API that anyone can open in their phone browser.

**Sample minimal web page** (`web_client.html`):

```html
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scam Checker</title>
</head>
<body>
  <h2>🍯 Scam Message Checker</h2>
  <textarea id="msg" rows="5" placeholder="Paste the suspicious message here..." style="width:100%"></textarea><br><br>
  <button onclick="check()">Check for Scam</button>
  <p id="result"></p>

  <script>
    async function check() {
      const text = document.getElementById("msg").value;
      const res = await fetch("https://honey-pot-agent.onrender.com/honeypot/message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": "your_api_key_here"
        },
        body: JSON.stringify({
          sessionId: "web_" + Date.now(),
          message: { sender: "scammer", text: text },
          metadata: { channel: "WebApp" }
        })
      });
      const data = await res.json();
      document.getElementById("result").innerText = data.reply
        ? "⚠️ SCAM DETECTED! Agent reply: " + data.reply
        : "✅ Looks safe — no scam indicators found.";
    }
  </script>
</body>
</html>
```

Host this on **GitHub Pages**, **Netlify**, or **Vercel** for free — users open it on any phone browser.

---

## 🔴 Mode B: Self-Hosted (Your Own Device as Server)

If you want to run the Honey-Pot API locally (on your laptop/PC) and let users connect to it:

### Step 1 — Run the API locally

```bash
# Clone the project
git clone https://github.com/123AmaanHussain/honey-pot_agent.git
cd honey-pot_agent

# Install dependencies
pip install -r requirements.txt

# Copy and fill in your .env
cp .env.example .env
# Add your API_KEY and GEMINI_API_KEY

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server is now live at `http://localhost:8000`

### Step 2 — Expose to the Internet (for others to use)

Use **ngrok** (free tool) to create a public URL from your local server:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000
```

ngrok gives you a public URL like:
```
https://abc123.ngrok.io
```

Share this URL. Now anyone can call your API at:
```
https://abc123.ngrok.io/honeypot/message
```

> ⚠️ The ngrok free tier URL changes every time you restart. Use a paid plan or deploy to Render for a permanent URL.

---

### Step 3 — Running on Android (Advanced)

You can actually run the Python server directly on an Android phone using **Termux**:

```bash
# Install Termux from F-Droid (not Play Store)
# Open Termux and run:

pkg update && pkg install python git
pip install fastapi uvicorn google-generativeai pydantic httpx python-dotenv
git clone https://github.com/123AmaanHussain/honey-pot_agent.git
cd honey-pot_agent
# Set up .env manually
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will run on `http://localhost:8000` on the phone itself.

> This is useful for offline or local testing — not recommended for production.

---

## 👥 Multi-User Scenarios

### Scenario 1: Community Scam Shield (Shared Telegram Bot)
- One person hosts the server (Render / VPS)
- One Telegram bot created and shared with the community
- Each user gets their own session (based on their chat ID)
- All intelligence aggregates to `/intelligence` endpoint

### Scenario 2: Family Safety Tool
- Host the simple web page on GitHub Pages
- Share the URL with family members
- Seniors can access it on phone browser, paste suspicious messages
- Completely no-install needed

### Scenario 3: Organization / NGO Deployment
- Deploy the API on Render (free tier available)
- Create a WhatsApp Business number
- Share the number with beneficiaries
- Monitor `/intelligence` endpoint via dashboard for collected scammer data

---

## 🔐 Security Notes for Multi-User Deployment

| Practice | Why It Matters |
|----------|---------------|
| Set a strong `API_KEY` in `.env` | Prevents unauthorized API access |
| Don't expose the API key in frontend code | Anyone can abuse it; use a backend proxy instead |
| Enable rate limiting (`RATE_LIMIT_ENABLED=True`) | Prevents single user from flooding the server |
| Use HTTPS always | Encrypts data in transit; Render provides this automatically |
| Consider Redis for session store | In-memory sessions are lost on restart; critical for production |

---

## 🔧 Environment Configuration Reference

```env
# .env file
API_KEY=your_strong_secret_key        # Required: protect your API
GEMINI_API_KEY=your_gemini_key        # Required: for AI reply generation

WEBHOOK_ENABLED=True                   # Optional: real-time notifications
WEBHOOK_URL=https://your-webhook.com   # Optional: where to send alerts

CALLBACK_URL=https://...              # Optional: GUVI hackathon callback

RATE_LIMIT_ENABLED=True               # Recommended for public deployments
RATE_LIMIT_REQUESTS=100               # Max requests per minute per IP
```

---

## ✅ Quick Comparison: Which Setup Suits You?

| Use Case | Recommended Setup |
|----------|------------------|
| Just testing yourself | Run locally with `python main.py` |
| Share with a few friends | Local + ngrok tunnel |
| Share with family (non-tech) | Web page hosted on GitHub Pages |
| Community / public use | Deploy on Render + Telegram Bot |
| Organization / enterprise | VPS + WhatsApp Business API + Redis |

---

*For platform-specific integration code, see [`INTEGRATION_GUIDE.md`](./INTEGRATION_GUIDE.md)*
*For architecture overview, see [`ARCHITECTURE.md`](./ARCHITECTURE.md)*
