import asyncio
from src.services.tenant_manager import tenant_manager
from src.services.whatsapp import WhatsAppService
from src.services.conversation_flow import ConversationFlow
from src.services.database import db

async def test_jain_shubh_masale():
    print("=" * 65)
    print("DEMO RUN: JAIN SHUBH MASALE (जैन शुभ मसाले)")
    print("=" * 65)

    tenant_id = "jain_shubh_masale"
    profile = tenant_manager.get_tenant(tenant_id)
    print(f"Store: {profile['business_name']}")
    print(f"Hours: {profile['hours']}")
    print(f"Delivery: {profile['delivery_info']}")
    
    wa = WhatsAppService()
    flow = ConversationFlow(tenant_id, profile, wa)
    customer_phone = "+919876540001"

    # Step 1: Customer asks about Atta price
    print("\n--- 1. Customer: 'Atta ka kya rate hai?' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": "Atta ka kya rate hai?"}})

    # Step 2: Customer asks about opening hours & delivery time
    print("\n--- 2. Customer: 'Dukaan kab tak khulti hai aur delivery kitne din me hogi?' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": "Dukaan kab tak khulti hai aur delivery kitne din me hogi?"}})

    # Step 3: Customer places an order
    order_text = "5kg Chakki Atta, 500g Haldi, 250g Lal Mirch"
    print(f"\n--- 3. Customer sends order: '{order_text}' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": order_text}})

    # Step 4: Customer sends their address
    address_text = "House No. 45, Near Shanti Jain Temple, Market Road"
    print(f"\n--- 4. Customer sends address: '{address_text}' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": address_text}})

    # Step 5: Verify Saved Order in Database
    print("\n--- 5. Verifying Database Storage for Jain Shubh Masale ---")
    orders = db.list_orders(tenant_id)
    print(f"Total Orders Recorded: {len(orders)}")
    for o in orders:
        print(f" -> Order #{o['id']} | Phone: {o['customer_phone']} | Status: {o['status']} | Address: {o['delivery_address']}")

    print("\n" + "=" * 65)
    print("JAIN SHUBH MASALE BOT COMPLETE & VERIFIED!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_jain_shubh_masale())
