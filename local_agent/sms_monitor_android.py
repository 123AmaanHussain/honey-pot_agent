"""
🍯 Honey-Pot — Android SMS Monitor
=====================================
Monitors incoming SMS messages on your Android phone via ADB.
When a scam is detected, automatically sends a reply SMS.

Requires:
  - Android phone with USB debugging enabled, connected to PC via USB
  - ADB installed on PC (https://developer.android.com/tools/adb)
  - pip install requests python-dotenv

How it works:
  - Polls Android SMS content provider via ADB shell commands
  - Sends new messages to Honey-Pot API
  - Replies via ADB (using Android SMS send intent)
  
NOTE: For wireless mode, enable ADB over WiFi after first USB connection.
"""

import os
import time
import logging
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

from session_cache import add_message, get_history

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────
HONEYPOT_URL   = os.getenv("HONEYPOT_URL", "https://honey-pot-agent.onrender.com/honeypot/message")
HONEYPOT_KEY   = os.getenv("HONEYPOT_API_KEY", "")
POLL_INTERVAL  = int(os.getenv("SMS_POLL_SECONDS", "10"))  # Check every 10 seconds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("SMSMonitor")


# ─── ADB Helpers ────────────────────────────────────────────────────────────────
def adb(cmd: str) -> str:
    """Run an ADB shell command and return output."""
    result = subprocess.run(
        f"adb shell {cmd}",
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_latest_inbox_sms(limit: int = 10) -> list[dict]:
    """
    Read latest SMS from Android inbox using content provider query.
    Returns list of {address, body, date, _id}
    """
    output = adb(
        "content query --uri content://sms/inbox "
        "--projection _id,address,body,date "
        f"--sort 'date DESC' --limit {limit}"
    )
    messages = []
    for line in output.splitlines():
        if "Row:" in line:
            msg = {}
            for field in ["_id", "address", "body", "date"]:
                if f"{field}=" in line:
                    start = line.index(f"{field}=") + len(f"{field}=")
                    end = line.index(",", start) if "," in line[start:] else len(line)
                    msg[field] = line[start:end].strip()
            if "_id" in msg and "body" in msg:
                messages.append(msg)
    return messages


def send_sms_reply(phone_number: str, text: str):
    """Send an SMS reply via ADB using Android Intent."""
    # Escape for shell
    safe_text = text.replace("'", "\\'").replace('"', '\\"')
    cmd = (
        f"am start -a android.intent.action.SENDTO "
        f"-d sms:{phone_number} "
        f"--es sms_body '{safe_text}' "
        f"--ez exit_on_sent true"
    )
    adb(cmd)
    log.info(f"📤 SMS reply triggered to {phone_number}")


def check_adb_connected() -> bool:
    result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
    lines = [l for l in result.stdout.splitlines() if "\tdevice" in l]
    return len(lines) > 0


# ─── Honey-Pot API Call ─────────────────────────────────────────────────────────
def check_message(session_id: str, text: str) -> str | None:
    try:
        add_message(session_id, "scammer", text)
        history = get_history(session_id)
        resp = requests.post(
            HONEYPOT_URL,
            json={
                "sessionId": session_id,
                "message": {"sender": "scammer", "text": text},
                "conversationHistory": history[:-1],
                "metadata": {"channel": "SMS"}
            },
            headers={"x-api-key": HONEYPOT_KEY},
            timeout=10
        )
        reply = resp.json().get("reply")
        if reply:
            add_message(session_id, "agent", reply)
        return reply
    except Exception as e:
        log.error(f"API error: {e}")
        return None


# ─── Main Poll Loop ──────────────────────────────────────────────────────────────
def main():
    if not HONEYPOT_KEY:
        log.error("[FAIL] HONEYPOT_API_KEY not set in .env")
        return

    if not check_adb_connected():
        log.error("[FAIL] No Android device found via ADB. Connect phone via USB with debugging enabled.")
        return

    log.info("[OK] Android device connected! Honey-Pot SMS monitor active.")
    log.info(f"[POLL] Polling every {POLL_INTERVAL}s for new SMS...")

    seen_ids = set()

    # Pre-load existing messages so we don't process old ones
    for msg in get_latest_inbox_sms():
        seen_ids.add(msg["_id"])
    log.info(f"Skipping {len(seen_ids)} existing SMS messages.")

    while True:
        try:
            messages = get_latest_inbox_sms()
            for msg in messages:
                msg_id = msg.get("_id")
                if not msg_id or msg_id in seen_ids:
                    continue

                seen_ids.add(msg_id)
                phone = msg.get("address", "unknown")
                body = msg.get("body", "").strip()

                if not body:
                    continue

                session_id = f"sms_{phone.replace('+', '').replace(' ', '')}"
                log.info(f"📩 SMS from {phone}: {body[:60]}...")

                reply = check_message(session_id, body)

                if reply:
                    log.warning(f"[SCAM] SCAM SMS detected! Auto-replying...")
                    send_sms_reply(phone, reply)
                    log.info(f"[OK] Reply sent to {phone}")
                else:
                    log.info(f"[OK] Safe SMS — no action taken")

        except Exception as e:
            log.error(f"Error in poll loop: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
