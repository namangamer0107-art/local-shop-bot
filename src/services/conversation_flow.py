import logging
from typing import Dict, Any
from src.services.whatsapp import WhatsAppService
from src.services.ai_brain import AIBrain
from src.services.database import db

logger = logging.getLogger(__name__)

class ConversationFlow:
    def __init__(self, tenant_id: str, tenant_profile: Dict[str, Any], whatsapp_service: WhatsAppService):
        self.tenant_id = tenant_id
        self.profile = tenant_profile
        self.wa = whatsapp_service
        self.ai = AIBrain(tenant_profile)

    async def handle_message(self, sender_id: str, message_data: Dict[str, Any]):
        """Dispatch incoming WhatsApp message and log all user activity for Super Admin."""
        db.register_customer(sender_id, self.tenant_id)

        msg_type = message_data.get("type")
        state = db.get_user_state(sender_id, self.tenant_id)

        # 1. Handle Interactive Buttons
        if msg_type == "interactive":
            interactive = message_data.get("interactive", {})
            i_type = interactive.get("type")

            if i_type == "button_reply":
                button_id = interactive["button_reply"]["id"]
                db.log_activity(self.tenant_id, sender_id, "BUTTON_CLICK", f"Clicked: {button_id}")
                await self._handle_button(sender_id, button_id, state)
                return

            elif i_type == "list_reply":
                item_id = interactive["list_reply"]["id"]
                item_title = interactive["list_reply"]["title"]
                db.log_activity(self.tenant_id, sender_id, "LIST_SELECT", f"Selected: {item_title}")
                await self._handle_list_choice(sender_id, item_id, item_title, state)
                return

        # 2. Handle Text Messages
        text = message_data.get("text", {}).get("body", "").strip()
        lower_text = text.lower()

        # Log every incoming message for Super Admin audit trail
        db.log_activity(self.tenant_id, sender_id, "USER_MESSAGE", text)

        # Check for greeting or "target" trigger
        if "target" in lower_text or lower_text in ["hi", "hello", "hey", "start", "order", "namaste", "pranam"]:
            db.save_user_state(sender_id, self.tenant_id, "waiting_for_items", {})
            welcome = (
                f"🙏 जय जिनेन्द्र! Welcome to *{self.profile.get('business_name')}*.\n\n"
                f"📍 *Shop:* {self.profile.get('address')}\n"
                f"🕒 *Timings:* {self.profile.get('hours')}\n"
                f"🚚 *Delivery:* {self.profile.get('delivery_info')}\n\n"
                f"🛒 *Please send what you would like to order:*\n"
                f"(Example: 5kg Chakki Atta, 500g Haldi, 250g Mirch)"
            )
            await self.wa.send_text(sender_id, welcome)
            return

        # Step 2: Customer provides order items
        if state.get("step") == "waiting_for_items" or any(k in lower_text for k in ["kg", "packet", "gm", "atta", "haldi", "mirch", "dhaniya", "masala"]):
            db.save_user_state(
                sender_id,
                self.tenant_id,
                "waiting_for_address",
                {"items_raw": text}
            )
            db.log_activity(self.tenant_id, sender_id, "ORDER_ITEMS_SUBMITTED", text)
            prompt = (
                f"📝 *Order List Received:*\n{text}\n\n"
                f"📍 Please reply with your *Full Delivery Address & House/Flat No.* to generate your official receipt:"
            )
            await self.wa.send_text(sender_id, prompt)
            return

        # Step 3: Customer provides address -> Create Order & Alert Owner
        if state.get("step") == "waiting_for_address":
            delivery_address = text
            order_items = state.get("data", {}).get("items_raw", "Custom order")
            customer_name = state.get("data", {}).get("customer_name", "Customer")

            order_id = db.add_order(
                tenant_id=self.tenant_id,
                customer_phone=sender_id,
                items=[{"raw_list": order_items}],
                total="Payable on Delivery (Cash / UPI)",
                customer_name=customer_name,
                address=delivery_address
            )

            db.save_user_state(sender_id, self.tenant_id, "idle", {})
            db.log_activity(self.tenant_id, sender_id, "ORDER_COMPLETED", f"Receipt #{order_id} to {delivery_address}")

            receipt = (
                f"🧾 *OFFICIAL ORDER RECEIPT #{order_id}*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🏪 *Store:* {self.profile.get('business_name')}\n"
                f"📞 *Admin/Owner:* {self.profile.get('owner_phone', 'Store Owner')}\n"
                f"👤 *Customer Number:* {sender_id}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📦 *Items Ordered:*\n{order_items}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📍 *Delivery Address:* {delivery_address}\n"
                f"🚚 *Estimated Delivery:* Within 2 Days (Fresh Grind & Pack)\n"
                f"💵 *Delivery Charge:* FREE (if above ₹999)\n"
                f"💳 *Payment Mode:* Cash on Delivery / UPI upon arrival\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"✨ Thank you for shopping with us! Send *'target'* anytime to place another order."
            )
            await self.wa.send_text(sender_id, receipt)

            owner_phone = self.profile.get("owner_phone")
            if owner_phone:
                alert = (
                    f"🔔 *NEW ORDER RECEIVED! (Receipt #{order_id})*\n\n"
                    f"📱 *Customer Mobile:* {sender_id}\n"
                    f"📦 *Items:*\n{order_items}\n\n"
                    f"📍 *Delivery Address:*\n{delivery_address}\n\n"
                    f"🚚 *Deadline:* Deliver within 2 days"
                )
                await self.wa.send_text(owner_phone, alert)
            return

        # 4. Freeform Inquiry -> Gemini AI Answer + Prompt Order
        ai_reply = await self.ai.answer_query(text)
        db.log_activity(self.tenant_id, sender_id, "AI_ANSWERED", f"Question: {text} | Reply: {ai_reply[:60]}...")
        prompt_again = f"{ai_reply}\n\n🛒 *Ready to order?* Just reply with your item list or send *'target'*!"
        await self.wa.send_text(sender_id, prompt_again)

    async def _handle_button(self, sender_id: str, button_id: str, state: Dict[str, Any]):
        if button_id == "btn_masale_order":
            db.save_user_state(sender_id, self.tenant_id, "waiting_for_items", {})
            prompt = "📝 *Type what you need (e.g. 5kg Chakki Atta, 500g Haldi) and we will pack it for you!*"
            await self.wa.send_text(sender_id, prompt)

        elif button_id == "btn_popular_items":
            items = self.profile.get("featured_items", [])
            rows = [{"id": f"item_{it['id']}", "title": it["name"][:24], "description": it["price"]} for it in items]
            sections = [{"title": "Price List", "rows": rows}]
            await self.wa.send_list_menu(sender_id, "Here is our current price list:", "View Prices", sections)

        elif button_id == "btn_hours_delivery":
            info = (
                f"🏢 *{self.profile.get('business_name')}*\n\n"
                f"🕒 *Shop Timings:* {self.profile.get('hours')}\n"
                f"📍 *Address:* {self.profile.get('address')}\n"
                f"📞 *Owner:* {self.profile.get('phone')}\n"
                f"🚚 *Delivery Time:* Delivered to your doorstep *within 2 Days*\n"
                f"🎉 *Free Delivery:* On all orders above ₹999!"
            )
            buttons = [
                {"id": "btn_masale_order", "title": "🛍️ Order Now"},
                {"id": "btn_popular_items", "title": "⭐ Price List"},
            ]
            await self.wa.send_quick_reply_buttons(sender_id, info, buttons)

    async def _handle_list_choice(self, sender_id: str, item_id: str, item_title: str, state: Dict[str, Any]):
        if item_id.startswith("item_"):
            prompt = f"🛒 Selected: *{item_title}*.\n\nPlease reply with the quantity (e.g., 5kg) & your Delivery Address:"
            db.save_user_state(sender_id, self.tenant_id, "waiting_for_address", {"items_raw": item_title})
            await self.wa.send_text(sender_id, prompt)
