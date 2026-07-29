"""
🍯 Honey-Pot Local Agent — Session Cache
=========================================
Simple in-memory conversation history tracker.
Each platform monitor shares this to build multi-turn
conversationHistory payloads for the API.
"""

from typing import Dict, List

# session_id -> list of {"sender": "scammer"|"agent", "text": str}
_history: Dict[str, List[dict]] = {}


def add_message(session_id: str, sender: str, text: str):
    """Append a message to a session's history."""
    if session_id not in _history:
        _history[session_id] = []
    _history[session_id].append({"sender": sender, "text": text})
    # Keep last 20 messages to avoid huge payloads
    if len(_history[session_id]) > 20:
        _history[session_id] = _history[session_id][-20:]


def get_history(session_id: str) -> List[dict]:
    """Return the conversation history for a session."""
    return list(_history.get(session_id, []))


def clear_history(session_id: str):
    """Clear history for a completed session."""
    _history.pop(session_id, None)
