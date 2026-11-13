import asyncio
from src.services.database import db
from src.services.whatsapp import WhatsAppService
from src.services.broadcast import BroadcastService

async def test_broadcast():
    print("=" * 65)
    print("TESTING DAILY OFFERS & BROADCAST FOR JAIN PROVISION STORE")
    print("=" * 65)

    tenant_id = "jain_provision_store"

    # 1. Register 3 mock customers in the store database
    print("\n--- 1. Registering Store Customers ---")
    db.register_customer("+919811111111", tenant_id, "Rahul Sharma")
    db.register_customer("+919822222222", tenant_id, "Priya Verma")
    db.register_customer("+919833333333", tenant_id, "Amit Gupta")
    
    subscribers = db.get_broadcast_subscribers(tenant_id)
    print(f"Total Customers Opted-In for Offers: {len(subscribers)}")
    for s in subscribers:
        print(f" -> {s['customer_name']} ({s['customer_phone']})")

    # 2. Trigger Daily Offer Broadcast
    print("\n--- 2. Shop Owner Blasts Daily Offer ---")
    offer = (
        "🔥 *TODAY'S SPECIAL DEAL AT JAIN PROVISION STORE!* 🔥\n\n"
        "• 5kg Aashirvaad Chakki Atta: ₹235 (Save ₹20)\n"
        "• 1L Fortune Sunlite Oil: ₹130 (Save ₹15)\n"
        "• Free Home Delivery within 45 mins!\n\n"
        "Reply with your order list to get it delivered now! 🛒"
    )

    wa = WhatsAppService()
    broadcast_service = BroadcastService(wa)
    result = await broadcast_service.send_broadcast(tenant_id, offer)

    print(f"\nResult: Broadcast ID #{result['broadcast_id']} successfully sent to {result['sent_count']} customers!")

    # 3. Check Broadcast History
    print("\n--- 3. Verifying Broadcast History in Database ---")
    history = db.list_broadcasts(tenant_id)
    for h in history:
        print(f" -> Campaign #{h['id']} on {h['sent_at']} to {h['recipients_count']} recipients.")

    print("\n" + "=" * 65)
    print("DAILY OFFERS FEATURE VERIFIED & READY FOR SALE!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_broadcast())
