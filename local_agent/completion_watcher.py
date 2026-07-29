"""
🍯 Honey-Pot Local Agent — Completion Watcher
==============================================
Polls the Honey-Pot API for completed scam sessions and notifies
the user with a summary of what intelligence was collected.

Runs as a background thread alongside the platform monitors.
"""

import os
import time
import logging
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

from notifier import notify_user, notify_error

load_dotenv()

HONEYPOT_URL = os.getenv("HONEYPOT_URL", "https://honey-pot-agent.onrender.com")
HONEYPOT_KEY = os.getenv("HONEYPOT_API_KEY", "")
# Normalize URL: strip trailing slash and /honeypot/message suffix
_base = HONEYPOT_URL.rstrip("/")
if "/honeypot/message" in _base:
    _base = _base.replace("/honeypot/message", "")
API_BASE = _base

POLL_INTERVAL = int(os.getenv("WATCHER_POLL_SECONDS", "30"))

log = logging.getLogger("CompletionWatcher")


def _fetch_completed(since: str = ""):
    """Fetch completed sessions from the API."""
    try:
        url = f"{API_BASE}/sessions/completed"
        params = {"since": since} if since else {}
        resp = requests.get(
            url,
            headers={"x-api-key": HONEYPOT_KEY},
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        # API returns list directly, not {"sessions": [...]}
        if isinstance(data, list):
            return data
        return data.get("sessions", []) if isinstance(data, dict) else []
    except Exception as e:
        log.error(f"Failed to fetch completed sessions: {e}")
        return []


def watcher_loop():
    """Background loop that polls for completed sessions."""
    if not HONEYPOT_KEY:
        log.error("[FAIL] HONEYPOT_API_KEY not set — completion watcher cannot start")
        return

    log.info(f"[WATCH] Completion watcher started (polling every {POLL_INTERVAL}s)")

    # Track already-notified session IDs
    notified_ids: set = set()

    # Initial poll with no "since" filter to avoid spamming old sessions.
    # We only care about sessions completed AFTER the watcher starts.
    # Use naive UTC to match the API's datetime.utcnow() format.
    start_time = datetime.utcnow().isoformat()

    # Small initial delay so the API has time to boot if running locally
    time.sleep(5)

    while True:
        try:
            sessions = _fetch_completed(since=start_time)
            new_count = 0

            for session in sessions:
                sid = session.get("session_id")
                if not sid or sid in notified_ids:
                    continue
                notified_ids.add(sid)
                notify_user(session)
                new_count += 1

            if new_count:
                log.info(f"🔔 Notified user about {new_count} completed session(s)")

        except Exception as e:
            log.error(f"Watcher loop error: {e}")
            notify_error(f"Completion watcher error: {str(e)[:100]}")

        time.sleep(POLL_INTERVAL)


def start_watcher():
    """Start the completion watcher in a daemon thread."""
    t = threading.Thread(target=watcher_loop, name="CompletionWatcher", daemon=True)
    t.start()
    log.info("[OK] Completion watcher thread started")
    return t


if __name__ == "__main__":
    # Standalone test mode
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    watcher_loop()
