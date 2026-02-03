"""
Real-time Webhook Notification System for Honey-Pot Agent.
Handles triggering notifications for intelligence extraction, aggression, and session events.
"""
import logging
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Thread

from config import get_settings

logger = logging.getLogger(__name__)


def send_webhook_async(event_type: str, payload: Dict[str, Any]):
    """Send webhook in a background thread to avoid blocking main loop."""
    settings = get_settings()
    
    if not settings.webhook_enabled or not settings.webhook_url:
        return

    def _send():
        try:
            full_payload = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            }
            
            response = requests.post(
                settings.webhook_url,
                json=full_payload,
                timeout=settings.webhook_timeout
            )
            
            if response.status_code >= 400:
                logger.warning(
                    f"Webhook failed for event {event_type}",
                    extra={
                        "status_code": response.status_code,
                        "url": settings.webhook_url
                    }
                )
            else:
                logger.info(f"Webhook sent: {event_type}")
                
        except Exception as e:
            logger.error(f"Webhook error ({event_type}): {e}")

    # Fire and forget
    Thread(target=_send, daemon=True).start()


class EventManager:
    """Manages system events and triggers webhooks."""
    
    @staticmethod
    def notify_intel_extracted(session_id: str, intelligence: Dict[str, Any]):
        """Trigger notification for new intelligence extracted."""
        payload = {
            "session_id": session_id,
            "intelligence": intelligence
        }
        send_webhook_async("INTEL_EXTRACTED", payload)

    @staticmethod
    def notify_aggression_detected(session_id: str, escalation_data: Dict[str, Any]):
        """Trigger notification for detected scammer aggression/escalation."""
        payload = {
            "session_id": session_id,
            "escalation": escalation_data
        }
        send_webhook_async("SCAMMER_AGGRESSIVE", payload)

    @staticmethod
    def notify_session_completed(session_id: str, session_data: Dict[str, Any]):
        """Trigger notification for session completion."""
        # Clean session data for webhook (remove excessive history if needed)
        clean_data = session_data.copy()
        if "message_history" in clean_data:
            clean_data["message_history"] = clean_data["message_history"][-5:]
            
        payload = {
            "session_id": session_id,
            "summary": clean_data
        }
        send_webhook_async("SESSION_COMPLETED", payload)
