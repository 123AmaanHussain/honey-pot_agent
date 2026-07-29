# 🍯 Local Agent Setup Guide — Always-On Scam Monitor

> **What this does:** Runs silently on your device (PC/laptop), monitors your Telegram, WhatsApp, Gmail, and SMS **as you** — automatically engages scammers on your behalf. You don't need to forward anything manually.

---

## 📁 Files in This Folder

```
local_agent/
├── run_agent.py              ← Unified launcher (run this)
├── telegram_monitor.py       ← Monitors Telegram as your user account
├── whatsapp_monitor.js       ← Monitors WhatsApp via WhatsApp Web
├── gmail_monitor.py          ← Monitors Gmail inbox (polls every 30s)
├── sms_monitor_android.py    ← Monitors Android SMS via USB/ADB
└── .env.example              ← Copy to .env and fill in
```

---

## ⚡ Quick Start

### Step 1 — Copy and fill in your .env

```bash
cd local_agent
cp .env.example .env
# Open .env and fill in your HONEYPOT_API_KEY
```

### Step 2 — Install Python dependencies

```bash
pip install telethon requests python-dotenv \
            google-auth google-auth-oauthlib google-api-python-client
```

### Step 3 — Install Node.js dependencies (WhatsApp only)

```bash
npm install whatsapp-web.js qrcode-terminal axios dotenv
```

### Step 4 — Run the agent

```bash
# Run ALL monitors at once
python run_agent.py

# OR run specific ones:
python run_agent.py --telegram        # Telegram only
python run_agent.py --telegram --gmail   # Telegram + Gmail
node whatsapp_monitor.js              # WhatsApp (separate terminal)
```

---

## 📱 Per-Platform Setup

---

### 🔵 Telegram

**How it works:** Logs into your Telegram account using the official MTProto User API (Telethon). Reads incoming private messages and auto-replies as you.

**One-time setup:**
1. Go to **https://my.telegram.org/apps** (log in with your phone number)
2. Create an app → copy the `API ID` and `API Hash`
3. Add to `.env`:
   ```
   TG_API_ID=12345678
   TG_API_HASH=abcdef1234567890abcdef
   ```
4. Run the agent. First run will ask for your phone + OTP:
   ```
   Please enter your phone (or bot token): +919876543210
   Please enter the code you received: 12345
   ```
5. After that, it runs silently — no login needed again (session saved locally).

> ✅ **No need to install anything on your phone.** It works through Telegram's official API.

---

### 🟢 WhatsApp

**How it works:** Opens WhatsApp Web in a hidden browser window, scanning it as a "Linked Device". Reads your messages and auto-replies as you.

**One-time setup:**
1. Run:
   ```bash
   node whatsapp_monitor.js
   ```
2. A QR code appears in the terminal. Scan it with your phone:
   - WhatsApp → Settings → Linked Devices → Link a Device
3. Done! The session is saved — **no QR needed after first scan.**

> ✅ Works exactly like WhatsApp Web. Your phone stays connected as normal.

> ⚠️ Keep your PC running — WhatsApp Web requires an active internet connection.

---

### 📧 Gmail

**How it works:** Uses the official Gmail API (OAuth2). Polls your inbox every 30 seconds. When a scam email is found, auto-replies as you.

**One-time setup:**
1. Go to **https://console.cloud.google.com/**
2. Create a project → **Enable Gmail API**
3. Go to **APIs & Services → Credentials**
4. Create **OAuth 2.0 Client ID** → Desktop App
5. Download `credentials.json` → place it in the `local_agent/` folder
6. Run the agent. First run opens a browser window for Google login:
   ```bash
   python run_agent.py --gmail
   ```
7. Allow permissions → a `token.json` is saved. No login needed again.

> ✅ Official Google API — safe and authenticated.

---

### 📱 Android SMS (via USB)

**How it works:** Uses Android Debug Bridge (ADB) to read your SMS inbox and send replies directly from your phone — through your PC.

**Setup:**

**On your Android phone:**
1. Settings → About Phone → tap **Build Number** 7 times (enables Developer Options)
2. Settings → Developer Options → enable **USB Debugging**
3. Connect phone to PC via USB
4. Accept the "Allow USB Debugging" popup on phone

**On your PC:**
1. Install ADB:
   - Download [Platform Tools](https://developer.android.com/tools/releases/platform-tools)
   - Extract and add to PATH
   - Verify: `adb devices` → your phone should appear
2. Run:
   ```bash
   python run_agent.py --sms
   ```

**Wireless ADB (optional, no USB after first connection):**
```bash
adb tcpip 5555
adb connect <your-phone-IP>:5555
# Unplug USB — now works over WiFi
```

> ⚠️ ADB must stay connected (USB or WiFi). Keep PC running.

---

## 🖥️ Running as a Background Service (Always On)

### Windows — Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Set trigger: **At log on** / **At startup**
3. Action: Start a program
   - Program: `python`
   - Arguments: `E:\honey-pot_project\local_agent\run_agent.py`
   - Start in: `E:\honey-pot_project\local_agent`
4. Enable: "Run whether user is logged on or not"

### Windows — Run at startup (simple)

Create `start_honeypot.bat` on your Desktop:
```bat
@echo off
cd /d E:\honey-pot_project\local_agent
python run_agent.py
```
Place a shortcut in: `shell:startup` (Win+R → type this)

### Linux/Mac — systemd service

```ini
# /etc/systemd/system/honeypot.service
[Unit]
Description=Honey-Pot Local Scam Monitor
After=network.target

[Service]
WorkingDirectory=/path/to/local_agent
ExecStart=python run_agent.py
Restart=always
User=your_username

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable honeypot
sudo systemctl start honeypot
```

---

## 🧠 How the Auto-Reply Logic Works

```
Incoming Message (Telegram / WhatsApp / SMS / Gmail)
          ↓
   Honey-Pot API receives message text
          ↓
   ┌─ Scam detected? ──┐
   │                   │
  NO                  YES
   │                   │
   ↓                   ↓
Do nothing    Generate AI reply (as one of 7 personas)
(safe msg)    Auto-send reply as YOU to the scammer
                       ↓
           Scammer thinks they're talking to a real person
                       ↓
         Intelligence extracted (UPI/phone/links/accounts)
```

The real user **never sees the scam conversation** — the agent handles it silently.

---

## ⚠️ Important Notes

| Note | Details |
|------|---------|
| **Reply is null** | Safe message — agent does nothing, message goes to you normally |
| **Your account safety** | Telethon and whatsapp-web.js use official protocols. Not against ToS if used responsibly. |
| **WhatsApp rate limits** | Don't send too many auto-replies too fast — WhatsApp may flag the account. |
| **Privacy** | All messages are sent to your Honey-Pot API. If using the Render deployment, they pass through Render's servers. For maximum privacy, run the API locally too. |
| **Sessions stored in RAM** | Restart the Honey-Pot API = sessions lost. Consider Redis for persistence. |

---

## 🔐 Run the API Locally Too (Maximum Privacy)

If you want everything fully local (no cloud):

```bash
# Terminal 1 — Run the Honey-Pot API
cd E:\honey-pot_project
uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Run the local agent monitors
cd E:\honey-pot_project\local_agent
# Set in .env:
# HONEYPOT_URL=http://127.0.0.1:8000/honeypot/message
python run_agent.py
```

Everything stays on your machine. No data leaves your device.

---

*For platform bridge integration (not local), see [`INTEGRATION_GUIDE.md`](../INTEGRATION_GUIDE.md)*
