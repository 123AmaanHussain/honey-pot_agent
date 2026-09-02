"""
Trust Profile System — tracks sender behavior over time to detect anomalies.

Core idea: If a known contact suddenly starts acting like a scammer,
that's a behavioral anomaly (compromised account), not a random scammer.

Trust levels:
  - UNKNOWN: first interaction, no history
  - KNOWN: multiple interactions, established pattern
  - TRUSTED: long history, never suspicious
  - SUSPICIOUS: known contact behaving abnormally (compromised account?)
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRUST_FILE = DATA_DIR / "trust_profiles.json"


# ── Trust Levels ───────────────────────────────────────────────────────────────

class TrustLevel:
    UNKNOWN = "unknown"       # First interaction, no history
    KNOWN = "known"           # 2+ interactions, normal behavior
    TRUSTED = "trusted"       # 5+ interactions, never suspicious
    SUSPICIOUS = "suspicious" # Known contact but behaving abnormally


# ── Trust Profile Store ────────────────────────────────────────────────────────

def _load_profiles() -> dict:
    if TRUST_FILE.exists():
        with open(TRUST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"senders": {}, "updated_at": datetime.utcnow().isoformat()}


def _save_profiles(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.utcnow().isoformat()
    with open(TRUST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _sender_key(phone: str = "", name: str = "", session_id: str = "") -> str:
    """Generate a unique key for a sender."""
    if phone:
        return f"phone:{phone.strip()}"
    if name:
        return f"name:{name.strip().lower()}"
    if session_id:
        return f"session:{session_id}"
    return "unknown"


def get_trust_profile(phone: str = "", name: str = "", session_id: str = "") -> dict:
    """Get or create a trust profile for a sender."""
    profiles = _load_profiles()
    key = _sender_key(phone, name, session_id)

    if key not in profiles["senders"]:
        profiles["senders"][key] = {
            "key": key,
            "phone": phone,
            "name": name,
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "interaction_count": 0,
            "message_types": {  # Track what kinds of messages they send
                "greetings": 0,
                "casual": 0,
                "requests": 0,
                "scam_indicators": 0,
            },
            "trust_level": TrustLevel.UNKNOWN,
            "flags": [],
            "notes": "",
        }
        _save_profiles(profiles)

    return profiles["senders"][key]


def update_trust_profile(
    phone: str = "",
    name: str = "",
    session_id: str = "",
    message_type: str = "casual",  # greeting, casual, request, scam_indicator
    is_scam: bool = False,
    notes: str = "",
) -> dict:
    """
    Update a sender's trust profile based on their latest message.
    Returns the updated profile.
    """
    profiles = _load_profiles()
    key = _sender_key(phone, name, session_id)

    if key not in profiles["senders"]:
        profiles["senders"][key] = {
            "key": key,
            "phone": phone,
            "name": name,
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "interaction_count": 0,
            "message_types": {
                "greetings": 0,
                "casual": 0,
                "requests": 0,
                "scam_indicators": 0,
            },
            "trust_level": TrustLevel.UNKNOWN,
            "flags": [],
            "notes": "",
        }

    profile = profiles["senders"][key]
    profile["last_seen"] = datetime.utcnow().isoformat()
    profile["interaction_count"] += 1

    # Track message type
    if message_type in profile["message_types"]:
        profile["message_types"][message_type] += 1

    # Track scam flags
    if is_scam:
        profile["flags"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": message_type,
            "notes": notes,
        })

    # Recalculate trust level
    profile["trust_level"] = _calculate_trust_level(profile)

    _save_profiles(profiles)
    logger.info(
        f"Trust profile updated: {key}",
        extra={
            "trust_level": profile["trust_level"],
            "interaction_count": profile["interaction_count"],
            "message_type": message_type,
        },
    )
    return profile


def _calculate_trust_level(profile: dict) -> str:
    """Calculate trust level based on interaction history."""
    count = profile["interaction_count"]
    scam_flags = len(profile["flags"])
    msg_types = profile["message_types"]

    # If they've ever been flagged as scam, stay suspicious
    if scam_flags > 0:
        return TrustLevel.SUSPICIOUS

    # Build trust over time
    if count >= 5 and msg_types["scam_indicators"] == 0:
        return TrustLevel.TRUSTED
    elif count >= 2:
        return TrustLevel.KNOWN
    else:
        return TrustLevel.UNKNOWN


def classify_message_type(message: str) -> str:
    """Classify a message into a type for trust tracking."""
    msg_lower = message.lower().strip()

    # Greetings
    greeting_words = [
        "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
        "happy birthday", "congratulations", "how are you", "what's up",
        "namaste", "salaam", "bye", "good night", "see you",
    ]
    if any(word in msg_lower for word in greeting_words):
        return "greeting"

    # Money/personal info requests (scam indicators)
    scam_words = [
        "send money", "send rs", "upi", "otp", "bank account", "pin",
        "credit card", "aadhaar", "pan card", "urgent", "immediately",
        "block", "suspended", "won", "prize", "lottery",
    ]
    if any(word in msg_lower for word in scam_words):
        return "scam_indicator"

    # General requests
    request_words = ["can you", "please", "help me", "need", "send", "transfer"]
    if any(word in msg_lower for word in request_words):
        return "request"

    return "casual"


def is_known_contact(phone: str = "", name: str = "", session_id: str = "") -> bool:
    """Check if this sender is a known contact (has history)."""
    profile = get_trust_profile(phone, name, session_id)
    return profile["trust_level"] in (TrustLevel.KNOWN, TrustLevel.TRUSTED, TrustLevel.SUSPICIOUS)


def get_sender_context(phone: str = "", name: str = "", session_id: str = "") -> str:
    """
    Get a context string about the sender to inject into the LLM prompt.
    Tells the LLM about the sender's history and trust level.
    """
    profile = get_trust_profile(phone, name, session_id)

    trust = profile["trust_level"]
    count = profile["interaction_count"]
    scam_flags = len(profile["flags"])
    msg_types = profile["message_types"]

    parts = []

    if trust == TrustLevel.UNKNOWN:
        parts.append(f"Sender is UNKNOWN (first interaction, no history).")
    elif trust == TrustLevel.KNOWN:
        parts.append(f"Sender is a KNOWN contact ({count} previous interactions, normal behavior).")
    elif trust == TrustLevel.TRUSTED:
        parts.append(f"Sender is a TRUSTED contact ({count} interactions, never suspicious).")
    elif trust == TrustLevel.SUSPICIOUS:
        parts.append(f"Sender is SUSPICIOUS — known contact but has been flagged for scam behavior {scam_flags} time(s).")

    # Add behavioral summary
    total = sum(msg_types.values()) or 1
    if msg_types["greetings"] > 0:
        parts.append(f"History: {msg_types['greetings']} greetings, {msg_types['casual']} casual, {msg_types['requests']} requests.")
    if scam_flags > 0:
        parts.append(f"Previous scam flags: {scam_flags}.")

    return " ".join(parts)


def get_trust_stats() -> dict:
    """Get overall trust statistics."""
    profiles = _load_profiles()
    senders = profiles.get("senders", {})

    stats = {
        "total_senders": len(senders),
        "unknown": 0,
        "known": 0,
        "trusted": 0,
        "suspicious": 0,
    }

    for profile in senders.values():
        level = profile.get("trust_level", TrustLevel.UNKNOWN)
        if level in stats:
            stats[level] += 1

    return stats
