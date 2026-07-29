"""
🍯 Honey-Pot — Telegram Local Monitor
=======================================
Runs silently in background. Monitors YOUR Telegram account for incoming messages.
When a scam is detected, the bot auto-replies on YOUR behalf.

Uses Telethon (Telegram MTProto User API — acts AS you, not as a bot).

Requirements:
    pip install telethon requests python-dotenv

Setup:
    1. Get API credentials from https://my.telegram.org/apps
    2. Add to .env:  TG_API_ID, TG_API_HASH, HONEYPOT_API_KEY
    3. Run: python telegram_monitor.py
    4. First run will ask for your phone number + OTP (one-time login)
"""

import os
import logging
import asyncio
import requests
from telethon import TelegramClient, events
from dotenv import load_dotenv

from session_cache import add_message, get_history, clear_history

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────
TG_API_ID       = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH     = os.getenv("TG_API_HASH", "")
HONEYPOT_URL    = os.getenv("HONEYPOT_URL", "https://honey-pot-agent.onrender.com/honeypot/message")
HONEYPOT_KEY    = os.getenv("HONEYPOT_API_KEY", "")
SESSION_NAME    = "honeypot_monitor"   # Local session file name

# Chats to IGNORE auto-reply (add your groups/channels/trusted contacts here)
IGNORED_SENDERS = set()  # e.g. {123456789, 987654321}  ← Telegram user IDs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("TelegramMonitor")

# ─── Honey-Pot API Call ─────────────────────────────────────────────────────────
def check_message(session_id: str, text: str) -> str | None:
    """
    Send message to Honey-Pot API with full conversation history.
    Returns the agent reply if scam detected, None if safe.
    """
    try:
        add_message(session_id, "scammer", text)
        history = get_history(session_id)
        resp = requests.post(
            HONEYPOT_URL,
            json={
                "sessionId": session_id,
                "message": {
                    "sender": "scammer",
                    "text": text
                },
                "conversationHistory": history[:-1],  # exclude current msg
                "metadata": {"channel": "Telegram"}
            },
            headers={"x-api-key": HONEYPOT_KEY},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        reply = data.get("reply")
        if reply:
            add_message(session_id, "agent", reply)
        return reply
    except Exception as e:
        log.error(f"API error: {e}")
        return None  # On error, do NOT auto-reply (safe default)


# ─── Main Monitor ───────────────────────────────────────────────────────────────
async def main():
    if not TG_API_ID or not TG_API_HASH:
        log.error("[FAIL] Missing TG_API_ID / TG_API_HASH in .env")
        return
    if not HONEYPOT_KEY:
        log.error("[FAIL] Missing HONEYPOT_API_KEY in .env")
        return

    client = TelegramClient(SESSION_NAME, TG_API_ID, TG_API_HASH)
    await client.start()   # First run: will ask for phone + OTP

    me = await client.get_me()
    log.info(f"[OK] Logged in as: {me.first_name} (@{me.username})")
    log.info("[ACTIVE] Honey-Pot monitor active — watching for scams silently...")

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        # Only monitor private (1-on-1) messages, not group chats
        if not event.is_private:
            return

        sender = await event.get_sender()
        sender_id = sender.id
        text = event.raw_text.strip()

        # Skip empty messages and whitelisted senders
        if not text or sender_id in IGNORED_SENDERS:
            return

        session_id = f"tg_{sender_id}"
        log.info(f"📩 Message from {getattr(sender, 'first_name', sender_id)}: {text[:60]}...")

        # Call Honey-Pot API
        reply = check_message(session_id, text)

        if reply:
            log.warning(f"[SCAM] SCAM DETECTED — auto-replying on your behalf")
            await event.reply(reply)   # Sends as YOU, not as a bot
            log.info(f"[OK] Reply sent: {reply[:80]}...")
        else:
            log.info(f"[OK] Safe message — no action taken")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
