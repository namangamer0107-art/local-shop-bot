import json
import logging
from typing import Dict, Any, Optional
from src.config import settings

logger = logging.getLogger(__name__)

class AIBrain:
    def __init__(self, tenant_profile: Dict[str, Any]):
        self.profile = tenant_profile
        self.api_key = settings.GEMINI_API_KEY
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}")

    def build_system_prompt(self) -> str:
        items = self.profile.get("services") or self.profile.get("featured_items") or []
        items_text = "\n".join([f"- {i.get('name')}: {i.get('price')}" for i in items])
        
        faq_text = "\n".join(
            [f"Q: {f['question']}\nA: {f['answer']}" for f in self.profile.get("faq", [])]
        )
        categories_text = ", ".join(self.profile.get("popular_categories", []))

        return f"""You are the friendly, polite WhatsApp assistant for '{self.profile.get("business_name")}'.
Business Category: {self.profile.get("category")}
Address: {self.profile.get("address")} (New Ashok Nagar)
Phone: {self.profile.get("phone")} (+919958240721)
Opening Hours: {self.profile.get("hours")} (10:00 AM to 7:00 PM)
Delivery Details: {self.profile.get("delivery_info")} (Delivery within 2 days, FREE above ₹999)
Payment Options: {self.profile.get("payment_methods", "Cash & UPI")}

Popular Categories:
{categories_text}

Featured Items / Services & Prices:
{items_text}

Frequently Asked Questions:
{faq_text}

Rules:
1. Chakki Atta price is ₹65 / kg.
2. Delivery takes within 2 days. Free delivery on orders above ₹999.
3. Address is New Ashok Nagar and contact is +919958240721.
4. Timings: 10:00 AM to 7:00 PM.
5. Keep replies conversational, concise, and natural for WhatsApp (1 to 3 short sentences).
6. Answer in the same language the customer texts in (Hindi, Hinglish, or English).
"""

    async def answer_query(self, user_text: str, conversation_history: Optional[str] = None) -> str:
        """Answer customer inquiries with accurate store details."""
        if not self.client:
            lower = user_text.lower()
            if "atta" in lower:
                return (
                    f"🌾 *Fresh Shudh Chakki Atta:*\n"
                    f"Price: *₹65 / kg* (100% ताज़ा और शुद्ध)\n\n"
                    f"🚚 Delivery: *Within 2 Days* (FREE on orders above ₹999!)\n\n"
                    f"How many kg would you like to order? Send quantity & address to book!"
                )
            if "deliver" in lower or "delivery" in lower or "free" in lower:
                return (
                    f"🚚 *Delivery Information:*\n\n"
                    f"• *Delivery Time:* Delivered within 2 Days\n"
                    f"• *Free Delivery:* On all orders above *₹999*! 🎉\n"
                    f"• Deliveries across New Ashok Nagar & nearby areas."
                )
            if "time" in lower or "open" in lower or "timing" in lower or "hours" in lower:
                return (
                    f"🕒 *Shop Timings:*\n"
                    f"10:00 AM to 7:00 PM (Mon-Sat)\n\n"
                    f"You can place orders anytime on WhatsApp!"
                )
            if "address" in lower or "where" in lower or "location" in lower or "kahan" in lower or "phone" in lower or "contact" in lower:
                return (
                    f"📍 *Shop Address:*\n"
                    f"New Ashok Nagar, Delhi / NCR\n\n"
                    f"📞 *Call / WhatsApp:* +919958240721"
                )
            if "masale" in lower or "haldi" in lower or "mirch" in lower or "price" in lower:
                items = self.profile.get("featured_items", [])
                items_str = "\n".join([f"• {it['name']} - *{it['price']}*" for it in items[:5]])
                return f"🌶️ *Popular Masale & Flours:*\n\n{items_str}\n\nSend your list to order!"
            
            return (
                f"Namaste! 🙏 Welcome to *{self.profile.get('business_name')}*.\n\n"
                f"📍 New Ashok Nagar | 📞 +919958240721\n"
                f"• Fresh Chakki Atta: ₹65/kg\n"
                f"• Timings: 10:00 AM - 7:00 PM\n"
                f"• Free Delivery on orders above ₹999 (within 2 days)\n\n"
                f"How can we help you today?"
            )

        prompt = f"""System Instructions:
{self.build_system_prompt()}

Customer Message: {user_text}

Reply directly to the customer as the WhatsApp assistant:"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return f"Namaste from {self.profile.get('business_name')}! How can we assist you with spices or fresh atta today?"
