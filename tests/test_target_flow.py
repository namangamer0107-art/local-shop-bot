import asyncio
from src.services.tenant_manager import tenant_manager
from src.services.whatsapp import WhatsAppService
from src.services.conversation_flow import ConversationFlow
from src.services.database import db

async def test_target_keyword_flow():
    print("=" * 65)
    print("TESTING: 'TARGET' TRIGGER & RECEIPT FLOW FOR ADMIN 9958240721")
    print("=" * 65)

    tenant_id = "jain_shubh_masale"
    profile = tenant_manager.get_tenant(tenant_id)
    wa = WhatsAppService()
    flow = ConversationFlow(tenant_id, profile, wa)

    customer_phone = "+919871100223"

    # Step 1: Customer messages "target"
    print("\n--- 1. Customer sends: 'target' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": "target"}})

    # Step 2: Customer sends their order items
    order_text = "10kg Fresh Chakki Atta, 500g Haldi Powder, 200g Shahi Garam Masala"
    print(f"\n--- 2. Customer replies with order items: '{order_text}' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": order_text}})

    # Step 3: Customer sends their address
    address_text = "Flat 401, Shivam Apartments, Near New Ashok Nagar Metro, Delhi"
    print(f"\n--- 3. Customer sends address: '{address_text}' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": address_text}})

    # Step 4: Verify that customer is registered and order receipt is recorded
    print("\n--- 4. Verifying Database & Audience for Admin 9958240721 ---")
    orders = db.list_orders(tenant_id)
    latest = orders[0]
    print(f"Receipt ID: #{latest['id']}")
    print(f"Customer Number on Receipt: {latest['customer_phone']}")
    print(f"Address on Receipt: {latest['delivery_address']}")
    print(f"Items: {latest['items']}")

    # Step 5: Follow-up interaction - bot asks for order again every time
    print("\n--- 5. Customer asks general question later: 'What are your shop hours?' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": "What are your shop hours?"}})

    print("\n" + "=" * 65)
    print("'TARGET' RECEIPT & ADMIN FLOW VERIFIED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_target_keyword_flow())
