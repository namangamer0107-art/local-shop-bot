import httpx
import logging
from typing import List, Dict, Any, Optional
from src.config import settings

logger = logging.getLogger(__name__)

META_GRAPH_URL = "https://graph.facebook.com/v21.0"

class WhatsAppService:
    def __init__(self, phone_number_id: Optional[str] = None, token: Optional[str] = None):
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.token = token or settings.META_API_TOKEN
        self.endpoint = f"{META_GRAPH_URL}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Send standard text message to recipient."""
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULATED OUTGOING TEXT to {recipient_id}]: {text}")
            return {"status": "simulated", "recipient_id": recipient_id, "text": text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, headers=self.headers, json=payload, timeout=10.0)
            return resp.json()

    async def send_quick_reply_buttons(
        self, recipient_id: str, body_text: str, buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send up to 3 quick-reply buttons.
        buttons format: [{"id": "btn_1", "title": "View Services"}, ...]
        """
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULATED BUTTONS to {recipient_id}]: {body_text} -> Buttons: {buttons}")
            return {"status": "simulated", "buttons": buttons}

        formatted_buttons = [
            {
                "type": "reply",
                "reply": {"id": btn["id"], "title": btn["title"][:20]},
            }
            for btn in buttons[:3]
        ]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": formatted_buttons},
            },
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, headers=self.headers, json=payload, timeout=10.0)
            return resp.json()

    async def send_list_menu(
        self,
        recipient_id: str,
        body_text: str,
        button_title: str,
        sections: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Send interactive select list message (e.g. Services, Menu, Time Slots)."""
        if not self.token or not self.phone_number_id:
            logger.info(f"[SIMULATED LIST to {recipient_id}]: {body_text}")
            return {"status": "simulated", "sections": sections}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_title[:20],
                    "sections": sections,
                },
            },
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, headers=self.headers, json=payload, timeout=10.0)
            return resp.json()
