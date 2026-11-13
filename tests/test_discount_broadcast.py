import asyncio
from src.services.database import db
from src.services.whatsapp import WhatsAppService
from src.services.broadcast import BroadcastService

async def test_discount_broadcast():
    print("=" * 65)
    print("TESTING CUSTOM DISCOUNT (%) WHATSAPP BROADCAST")
    print("=" * 65)

    tenant_id = "jain_shubh_masale"

    # Register mock customers in the store database
    db.register_customer("+919958240721", tenant_id, "Shop Owner Test")
    db.register_customer("+919811223344", tenant_id, "Suresh Gupta")
    
    subscribers = db.get_broadcast_subscribers(tenant_id)
    print(f"Total Customers in Audience: {len(subscribers)}")

    # Owner triggers a 15% discount offer for Sunday
    wa = WhatsAppService()
    broadcast = BroadcastService(wa)
    
    result = await broadcast.send_broadcast(
        tenant_id=tenant_id,
        discount_percent=15,
        item_focus="Fresh Chakki Atta (₹65/kg) and Pure Ground Spices",
        validity="Sunday 10 AM to 7 PM Only",
        custom_note="Free doorstep delivery on all orders above ₹999 within 2 days!"
    )

    print("\nMessage Delivered to Customers:")
    print("-" * 50)
    print(result["message_sent"])
    print("-" * 50)
    print(f"Dispatched successfully to {result['sent_count']} customers!")

    print("\n" + "=" * 65)
    print("CUSTOM DISCOUNT FEATURE READY!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_discount_broadcast())
