"""
🍯 Honey-Pot Local Agent — User Notifier
=========================================
Sends desktop / toast notifications when a scam session completes,
summarizing what intelligence was collected so the user knows
exactly what happened on their behalf.

Cross-platform fallback: prints to console and logs to file.
"""

import os
import sys
import logging
from typing import Dict, List, Any

log = logging.getLogger("Notifier")


def _format_summary(data: Dict[str, Any]) -> str:
    """Create a concise human-readable summary of a completed session."""
    platform_name = data.get("platform", "unknown").upper()
    scammer_type = data.get("scammer_type", "unknown")
    turns = data.get("turns", 0)

    items: List[str] = []
    intel = data.get("intelligence", {})
    for key, label in [
        ("upiIds", "UPI ID"),
        ("phoneNumbers", "phone number"),
        ("phishingLinks", "phishing link"),
        ("bankAccounts", "bank account"),
    ]:
        vals = intel.get(key, []) or []
        if vals:
            items.append(f"{len(vals)} {label}{'s' if len(vals) > 1 else ''}")

    summary = f"Scammer blocked on {platform_name}"
    if items:
        summary += f" — collected: {', '.join(items)}"
    else:
        summary += f" — {turns} messages exchanged"
    return summary


def _format_details(data: Dict[str, Any]) -> str:
    """Create a detailed multi-line description for console/logs."""
    lines = [
        "[ALERT] HONEY-POT SESSION COMPLETE",
        f"Platform: {data.get('platform', 'unknown').upper()}",
        f"Scammer Type: {data.get('scammer_type', 'unknown')}",
        f"Turns: {data.get('turns', 0)}",
        f"Final Confidence: {data.get('confidence', 0)}",
    ]
    intel = data.get("intelligence", {})
    for key, label in [
        ("upiIds", "UPI IDs"),
        ("phoneNumbers", "Phone Numbers"),
        ("phishingLinks", "Phishing Links"),
        ("bankAccounts", "Bank Accounts"),
        ("suspiciousKeywords", "Keywords"),
    ]:
        vals = intel.get(key, []) or []
        if vals:
            lines.append(f"{label}: {', '.join(str(v) for v in vals)}")
    return "\n".join(lines)


def notify_user(data: Dict[str, Any]):
    """
    Notify the user that a scam session has completed.
    Uses plyer desktop notifications, falls back to console/log.
    """
    title = "🍯 Honey-Pot Alert — Scammer Engaged & Blocked"
    summary = _format_summary(data)
    details = _format_details(data)

    notified = False

    # Desktop notification (plyer — cross-platform)
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=summary,
            timeout=10,
        )
        notified = True
    except Exception as e:
        log.debug(f"plyer notification failed: {e}")

    # Console + log fallback (always works)
    if not notified:
        print(f"\n{'=' * 50}")
        print(f"  {title}")
        print(f"{'=' * 50}")
        print(details)
        print(f"{'=' * 50}\n")

    # Always log to file
    log.info(f"NOTIFICATION — Session complete: {summary}")
    log.info(f"DETAILS:\n{details}")


def notify_startup(platforms: List[str]):
    """Notify that the local agent has started monitoring."""
    msg = f"Monitoring: {', '.join(platforms)}"
    try:
        from plyer import notification
        notification.notify(
            title="🍯 Honey-Pot Agent Started",
            message=msg,
            timeout=5,
        )
    except Exception:
        print(f"\n🍯 Honey-Pot Agent Started — {msg}\n")


def notify_error(error_msg: str):
    """Notify about a runtime error in the agent."""
    log.error(f"AGENT ERROR: {error_msg}")
    try:
        from plyer import notification
        notification.notify(
            title="🍯 Honey-Pot Agent Error",
            message=error_msg[:120],
            timeout=10,
        )
    except Exception:
        pass
