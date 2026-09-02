"""
Database CRUD repository for sessions, intelligence, and messages.
All functions degrade gracefully (return False/empty) when DB is not connected,
allowing the app to run in memory-only mode without any changes.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from .client import get_db, is_connected

try:
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Configuration CRUD
# ─────────────────────────────────────────────

def upsert_config(key: str, value: str, encrypt: bool = False) -> bool:
    """
    Insert or update a configuration value in the database.
    
    Args:
        key: Configuration key (e.g., 'telegram_bot_token')
        value: Configuration value
        encrypt: Whether to encrypt the value before storing (for sensitive data)
        
    Returns:
        True on success, False if DB unavailable or error
    """
    if not is_connected():
        return False
    
    try:
        # Encrypt sensitive values
        if encrypt:
            try:
                from app.utils.encryption import encrypt_data
                value = encrypt_data(value)
            except Exception as e:
                logger.error(f"Failed to encrypt config {key}: {e}")
                return False
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO configuration (key, value, updated_at)
                    VALUES (%s, %s, now())
                    ON CONFLICT (key) 
                    DO UPDATE SET value = %s, updated_at = now()
                    """,
                    (key, value, value)
                )
                conn.commit()
                return True
    except Exception as e:
        logger.error(f"Failed to upsert config {key}: {e}")
        return False


def get_config(key: str, decrypt: bool = False) -> Optional[str]:
    """
    Get a configuration value from the database.
    
    Args:
        key: Configuration key
        decrypt: Whether to decrypt the value after retrieving (for sensitive data)
        
    Returns:
        Configuration value or None if not found/DB unavailable
    """
    if not is_connected():
        return None
    
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT value FROM configuration WHERE key = %s",
                    (key,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                
                value = row['value']
                
                # Decrypt sensitive values
                if decrypt:
                    try:
                        from app.utils.encryption import decrypt_data
                        value = decrypt_data(value)
                    except Exception as e:
                        logger.error(f"Failed to decrypt config {key}: {e}")
                        return None
                
                return value
    except Exception as e:
        logger.error(f"Failed to get config {key}: {e}")
        return None


# ─────────────────────────────────────────────
# Session CRUD
# ─────────────────────────────────────────────

def upsert_session(session_id: str, session_data: dict) -> bool:
    """
    Insert or update a session in the database.
    Uses ON CONFLICT DO UPDATE (upsert) pattern.

    Args:
        session_id: Unique session identifier
        session_data: Dict matching SessionData fields

    Returns:
        True on success, False if DB unavailable or error
    """
    if not is_connected():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sessions (
                        id, confidence, turns, completed,
                        scammer_type, scammer_profile,
                        current_persona, persona_history,
                        behavior_patterns, created_at, last_activity
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        confidence        = EXCLUDED.confidence,
                        turns             = EXCLUDED.turns,
                        completed         = EXCLUDED.completed,
                        scammer_type      = EXCLUDED.scammer_type,
                        scammer_profile   = EXCLUDED.scammer_profile,
                        current_persona   = EXCLUDED.current_persona,
                        persona_history   = EXCLUDED.persona_history,
                        behavior_patterns = EXCLUDED.behavior_patterns,
                        last_activity     = EXCLUDED.last_activity
                    """,
                    (
                        session_id,
                        session_data.get("confidence", 1.0),
                        session_data.get("turns", 0),
                        session_data.get("completed", False),
                        session_data.get("scammer_type", "unknown"),
                        session_data.get("scammer_profile"),
                        session_data.get("current_persona"),
                        json.dumps(session_data.get("persona_history", [])),
                        json.dumps(session_data.get("behavior_patterns", {})),
                        datetime.now(timezone.utc),  # Store UTC time
                        datetime.now(timezone.utc),  # Store UTC time
                    ),
                )
        return True
    except Exception as e:
        logger.error(f"upsert_session failed for {session_id}: {e}")
        return False


def get_session(session_id: str) -> Optional[Dict]:
    """
    Load a session + its intelligence from Neon.

    Returns:
        Dict with session + intel fields, or None if not found / DB unavailable
    """
    if not is_connected():
        return None

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        s.*,
                        i.upi_ids, i.phone_numbers, i.phishing_links,
                        i.bank_accounts, i.suspicious_keywords, i.scanned_text
                    FROM sessions s
                    LEFT JOIN intelligence i ON s.id = i.session_id
                    WHERE s.id = %s
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_session failed for {session_id}: {e}")
        return None


def get_all_sessions() -> List[Dict]:
    """
    Return all sessions with their intelligence data.
    Used by the /intelligence endpoint.
    """
    if not is_connected():
        return []

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        s.*,
                        i.upi_ids, i.phone_numbers, i.phishing_links,
                        i.bank_accounts, i.suspicious_keywords, i.scanned_text
                    FROM sessions s
                    LEFT JOIN intelligence i ON s.id = i.session_id
                    ORDER BY s.created_at DESC
                    """
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_all_sessions failed: {e}")
        return []


# ─────────────────────────────────────────────
# Intelligence CRUD
# ─────────────────────────────────────────────

def upsert_intelligence(session_id: str, intel: dict) -> bool:
    """
    Insert or update extracted intelligence for a session.
    Arrays are stored as PostgreSQL native TEXT[] arrays.

    Args:
        session_id: Session to link intel to
        intel: Dict with keys: upiIds, phoneNumbers, phishingLinks,
               bankAccounts, suspiciousKeywords, scannedText
    """
    if not is_connected():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO intelligence (
                        session_id, upi_ids, phone_numbers,
                        phishing_links, bank_accounts,
                        suspicious_keywords, scanned_text, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        upi_ids             = EXCLUDED.upi_ids,
                        phone_numbers       = EXCLUDED.phone_numbers,
                        phishing_links      = EXCLUDED.phishing_links,
                        bank_accounts       = EXCLUDED.bank_accounts,
                        suspicious_keywords = EXCLUDED.suspicious_keywords,
                        scanned_text        = EXCLUDED.scanned_text,
                        updated_at          = EXCLUDED.updated_at
                    """,
                    (
                        session_id,
                        intel.get("upiIds", []),
                        intel.get("phoneNumbers", []),
                        intel.get("phishingLinks", []),
                        intel.get("bankAccounts", []),
                        intel.get("suspiciousKeywords", []),
                        intel.get("scannedText", []),
                        datetime.now(timezone.utc),
                    ),
                )
        return True
    except Exception as e:
        logger.error(f"upsert_intelligence failed for {session_id}: {e}")
        return False


# ─────────────────────────────────────────────
# Messages CRUD
# ─────────────────────────────────────────────

def save_message(session_id: str, sender: str, text: str) -> bool:
    """
    Persist a single message to the messages table.

    Args:
        session_id: Owning session ID
        sender: Who sent this message (scammer / agent / user)
        text: Message content
    """
    if not is_connected():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (session_id, sender, text) VALUES (%s, %s, %s)",
                    (session_id, sender, text),
                )
        return True
    except Exception as e:
        logger.error(f"save_message failed for {session_id}: {e}")
        return False


def get_messages(session_id: str) -> List[Dict]:
    """Return all messages for a session, ordered chronologically."""
    if not is_connected():
        return []

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT sender, text, created_at
                    FROM messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    """,
                    (session_id,),
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_messages failed for {session_id}: {e}")
        return []


def delete_session(session_id: str) -> bool:
    """
    Permanently remove a session and all its related rows
    (intelligence + message transcripts) from the database.

    Args:
        session_id: Session to delete

    Returns:
        True on success, False if DB unavailable or error
    """
    if not is_connected():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM intelligence WHERE session_id = %s", (session_id,))
                cur.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
                cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
        logger.info(f"Deleted session from DB: {session_id}")
        return True
    except Exception as e:
        logger.error(f"delete_session failed for {session_id}: {e}")
        return False
