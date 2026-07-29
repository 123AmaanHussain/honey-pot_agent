"""
🍯 Honey-Pot — Gmail Local Monitor
=====================================
Monitors your Gmail inbox for scam emails.
When a scam is detected, auto-replies on your behalf.

Uses Gmail API (OAuth2 — acts as you).

Requirements:
    pip install google-auth google-auth-oauthlib google-api-python-client requests python-dotenv

Setup:
    1. Go to https://console.cloud.google.com/
    2. Create a project → Enable Gmail API
    3. Create OAuth2 credentials → Desktop App
    4. Download credentials.json → place in this folder
    5. Run: python gmail_monitor.py (first run: browser login)
"""

import os
import base64
import time
import logging
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from session_cache import add_message, get_history

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────
HONEYPOT_URL = os.getenv("HONEYPOT_URL", "https://honey-pot-agent.onrender.com/honeypot/message")
HONEYPOT_KEY = os.getenv("HONEYPOT_API_KEY", "")
POLL_INTERVAL = int(os.getenv("GMAIL_POLL_SECONDS", "30"))  # Check every 30 seconds

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("GmailMonitor")


# ─── Gmail Auth ─────────────────────────────────────────────────────────────────
def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


# ─── Email Helpers ───────────────────────────────────────────────────────────────
def get_email_body(service, msg_id: str) -> tuple[str, str, str]:
    """Returns (sender_email, subject, body_text)."""
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    sender = headers.get("From", "unknown")
    subject = headers.get("Subject", "(no subject)")

    # Extract plain text body
    body = ""
    parts = msg["payload"].get("parts", [msg["payload"]])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part["body"].get("data", "")
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            break

    return sender, subject, body


def send_reply(service, original_msg_id: str, to: str, subject: str, reply_text: str):
    """Send a reply email as the user."""
    message = MIMEText(reply_text)
    message["to"] = to
    message["subject"] = f"Re: {subject}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": original_msg_id}
    ).execute()


def mark_as_read(service, msg_id: str):
    service.users().messages().modify(
        userId="me", id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


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
                "metadata": {"channel": "Gmail"}
            },
            headers={"x-api-key": HONEYPOT_KEY},
            timeout=15
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

    service = get_gmail_service()
    log.info("[OK] Gmail connected — Honey-Pot monitor active!")
    log.info(f"[POLL] Polling every {POLL_INTERVAL}s for new messages...")

    seen_ids = set()  # Track processed message IDs

    while True:
        try:
            results = service.users().messages().list(
                userId="me", labelIds=["INBOX", "UNREAD"], maxResults=10
            ).execute()
            messages = results.get("messages", [])

            for msg_meta in messages:
                msg_id = msg_meta["id"]
                if msg_id in seen_ids:
                    continue

                seen_ids.add(msg_id)
                sender, subject, body = get_email_body(service, msg_id)

                if not body.strip():
                    continue

                session_id = f"gmail_{sender.split('<')[-1].strip('>').replace('@','_')}"
                log.info(f"📩 Email from {sender}: {subject[:50]}")

                reply = check_message(session_id, body)

                if reply:
                    log.warning(f"[SCAM] SCAM email detected! Auto-replying...")
                    send_reply(service, msg_id, sender, subject, reply)
                    log.info(f"[OK] Reply sent to {sender}")
                else:
                    log.info(f"[OK] Safe email — no action taken")

                mark_as_read(service, msg_id)

        except Exception as e:
            log.error(f"Error in poll loop: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
