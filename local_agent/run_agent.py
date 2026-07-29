"""
🍯 Honey-Pot — Local Agent Runner
===================================
Unified launcher that runs all monitors simultaneously
in background threads on your local machine.

Usage:
    python run_agent.py                  # All platforms
    python run_agent.py --telegram       # Telegram only
    python run_agent.py --whatsapp       # WhatsApp only (opens browser)
    python run_agent.py --gmail          # Gmail only
    python run_agent.py --sms            # Android SMS only

Requirements:
    pip install telethon requests python-dotenv google-auth google-api-python-client google-auth-oauthlib
"""

import sys
import os
import time
import signal
import logging
import argparse
import threading
import subprocess
from dotenv import load_dotenv

from notifier import notify_startup
from completion_watcher import start_watcher

load_dotenv()

# Global shutdown event so all threads can check it
_shutdown_event = threading.Event()

# Track WhatsApp node process so we can kill it on exit
_whatsapp_proc = None

def _signal_handler(signum, frame):
    """Handle Ctrl+C (SIGINT) cleanly."""
    _shutdown_event.set()
    logging.getLogger("HoneypotAgent").info("\n🛑 Shutdown signal received, stopping...")
    # Also kill WhatsApp node process if running
    if _whatsapp_proc is not None:
        try:
            _whatsapp_proc.terminate()
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("HoneypotAgent")


def run_telegram():
    """Start Telegram monitor in the current thread."""
    import asyncio
    log.info("[START] Starting Telegram monitor...")
    # Import here so other monitors still start even if telethon is missing
    from telegram_monitor import main
    asyncio.run(main())


def run_gmail():
    """Start Gmail monitor in a thread."""
    log.info("[START] Starting Gmail monitor...")
    from gmail_monitor import main
    main()


def run_sms():
    """Start Android SMS monitor in a thread."""
    log.info("[START] Starting Android SMS monitor...")
    from sms_monitor_android import main
    main()


def run_whatsapp():
    """Start WhatsApp monitor as a subprocess (Node.js)."""
    log.info("[START] Starting WhatsApp monitor (Node.js)...")
    global _whatsapp_proc
    node_script = os.path.join(os.path.dirname(__file__), "whatsapp_monitor.js")
    if not os.path.exists(node_script):
        log.error("whatsapp_monitor.js not found!")
        return
    _whatsapp_proc = subprocess.Popen(
        ["node", node_script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    # Read and log subprocess output so it doesn't hang
    try:
        while not _shutdown_event.is_set():
            line = _whatsapp_proc.stdout.readline()
            if line:
                log.info(f"[WhatsApp] {line.strip()}")
            elif _whatsapp_proc.poll() is not None:
                break
            else:
                time.sleep(0.1)
    except Exception:
        pass
    if _whatsapp_proc.poll() is None:
        _whatsapp_proc.terminate()


def validate_env():
    key = os.getenv("HONEYPOT_API_KEY", "")
    if not key:
        log.error("[FAIL] HONEYPOT_API_KEY is not set in your .env file!")
        log.error("   Copy .env.local_agent.example → .env and fill in your API key.")
        sys.exit(1)
    log.info(f"[OK] API key loaded ({key[:6]}...)")


def main():
    parser = argparse.ArgumentParser(description="🍯 Honey-Pot Local Agent Runner")
    parser.add_argument("--telegram",  action="store_true", help="Enable Telegram monitor")
    parser.add_argument("--whatsapp",  action="store_true", help="Enable WhatsApp monitor")
    parser.add_argument("--gmail",     action="store_true", help="Enable Gmail monitor")
    parser.add_argument("--sms",       action="store_true", help="Enable Android SMS monitor")
    args = parser.parse_args()

    # Default: run all if none specified
    run_all = not any([args.telegram, args.whatsapp, args.gmail, args.sms])

    validate_env()

    log.info("=" * 55)
    log.info("    🍯  HONEY-POT LOCAL AGENT  —  Always On")
    log.info("=" * 55)

    threads = []

    if run_all or args.telegram:
        t = threading.Thread(target=run_telegram, name="Telegram", daemon=True)
        threads.append(t)

    if run_all or args.gmail:
        t = threading.Thread(target=run_gmail, name="Gmail", daemon=True)
        threads.append(t)

    if run_all or args.sms:
        t = threading.Thread(target=run_sms, name="SMS", daemon=True)
        threads.append(t)

    if run_all or args.whatsapp:
        t = threading.Thread(target=run_whatsapp, name="WhatsApp", daemon=True)
        threads.append(t)

    if not threads:
        log.error("No monitors enabled. Use --telegram / --whatsapp / --gmail / --sms")
        sys.exit(1)

    for t in threads:
        t.start()

    # Start completion watcher (notifies user when scam sessions finish)
    watcher_thread = start_watcher()

    active_platforms = [t.name for t in threads]
    notify_startup(active_platforms)

    log.info(f"[OK] {len(threads)} monitor(s) + watcher running. Press Ctrl+C to stop.")

    try:
        # Poll thread alive status in a loop so KeyboardInterrupt works on Windows
        while not _shutdown_event.is_set():
            alive = any(t.is_alive() for t in threads)
            if not alive:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("\n🛑 Honey-Pot agent stopped by user.")
        _shutdown_event.set()
        if _whatsapp_proc is not None and _whatsapp_proc.poll() is None:
            _whatsapp_proc.terminate()


if __name__ == "__main__":
    main()
