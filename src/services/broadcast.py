import logging
from typing import Dict, Any, List, Optional
from src.services.database import db
from src.services.whatsapp import WhatsAppService
from src.services.tenant_manager import tenant_manager

logger = logging.getLogger(__name__)

class BroadcastService:
    def __init__(self, whatsapp_service: WhatsAppService):
        self.wa = whatsapp_service

    def build_discount_template(
        self,
        business_name: str,
        discount_percent: int,
        item_focus: str = "all products",
        validity: str = "today only",
        extra_note: str = ""
    ) -> str:
        """
        Creates a high-converting WhatsApp promotional offer message with custom discount %.
        """
        note_str = f"\n💡 *Note:* {extra_note}\n" if extra_note else ""
        return (
            f"🎉 *SPECIAL OFFER from {business_name}* 🎉\n\n"
            f"🔥 Flat *{discount_percent}% OFF* on {item_focus}!\n"
            f"⏰ *Validity:* {validity}\n"
            f"🚚 *Free Home Delivery* on orders above ₹999 within 2 days.\n"
            f"{note_str}\n"
            f"🛒 *How to Order:* Simply reply to this message with your required items and your delivery address. We will pack it fresh for you!"
        )

    async def send_broadcast(
        self,
        tenant_id: str,
        offer_message: Optional[str] = None,
        discount_percent: Optional[int] = None,
        item_focus: Optional[str] = None,
        validity: Optional[str] = None,
        custom_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an automatic broadcast message (custom discount % or custom update)
        to all customers who have contacted or ordered from this store.
        """
        subscribers = db.get_broadcast_subscribers(tenant_id)
        if not subscribers:
            return {"status": "no_subscribers", "sent_count": 0}

        profile = tenant_manager.get_tenant(tenant_id) or {}
        business_name = profile.get("business_name", "Our Store")

        # If discount percentage was provided, format message automatically
        if discount_percent:
            final_message = self.build_discount_template(
                business_name=business_name,
                discount_percent=discount_percent,
                item_focus=item_focus or "all pure spices and fresh flour",
                validity=validity or "today only",
                extra_note=custom_note or ""
            )
        else:
            final_message = offer_message or f"Namaste! {business_name} is now taking fresh orders. Reply with your list for doorstep delivery!"

        sent_count = 0
        for customer in subscribers:
            phone = customer["customer_phone"]
            try:
                await self.wa.send_text(phone, final_message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {phone}: {e}")

        broadcast_id = db.record_broadcast(tenant_id, final_message, sent_count)

        return {
            "status": "success",
            "broadcast_id": broadcast_id,
            "sent_count": sent_count,
            "total_subscribers": len(subscribers),
            "message_sent": final_message
        }
