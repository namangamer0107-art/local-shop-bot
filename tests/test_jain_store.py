import asyncio
from src.services.tenant_manager import tenant_manager
from src.services.whatsapp import WhatsAppService
from src.services.conversation_flow import ConversationFlow
from src.services.database import db

async def test_jain_store():
    print("=" * 65)
    print("DEMO RUN: JAIN PROVISION STORE (WHATSAPP KIRANA BOT)")
    print("=" * 65)

    tenant_id = "jain_provision_store"
    profile = tenant_manager.get_tenant(tenant_id)
    print(f"Store: {profile['business_name']}")
    print(f"Address: {profile['address']}")
    
    wa = WhatsAppService()
    flow = ConversationFlow(tenant_id, profile, wa)
    customer_phone = "+919811223344"

    # Step 1: Customer sends greeting
    print("\n--- 1. Customer: 'Namaste! Are you open right now and do you deliver?' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": "Namaste! Are you open right now and do you deliver?"}})

    # Step 2: Customer taps 'Featured Prices' button
    print("\n--- 2. Customer clicks '⭐ Featured Prices' ---")
    await flow.handle_message(
        customer_phone,
        {
            "type": "interactive",
            "interactive": {
                "type": "button_reply",
                "button_reply": {"id": "btn_popular_items", "title": "⭐ Featured Prices"}
            }
        }
    )

    # Step 3: Customer sends their actual grocery list
    grocery_list = "1. 5kg Aashirvaad Atta\n2. 1L Fortune Refined Oil\n3. 1kg Tata Salt\n4. 2 packets Amul Butter"
    print(f"\n--- 3. Customer sends Grocery List:\n{grocery_list} ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": grocery_list}})

    # Step 4: Customer provides their flat & colony address
    address = "Flat 302, Tower B, Near Metro Pillar 11, Ashok Nagar"
    print(f"\n--- 4. Customer sends Delivery Address: '{address}' ---")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": address}})

    # Step 5: Verify Order in Database
    print("\n--- 5. Verifying Database Storage for Jain Provision Store ---")
    orders = db.list_orders(tenant_id)
    print(f"Total Orders Recorded: {len(orders)}")
    for o in orders:
        print(f" -> Order #{o['id']} | Phone: {o['customer_phone']} | Status: {o['status']} | Address: {o['delivery_address']}")

    print("\n" + "=" * 65)
    print("JAIN PROVISION STORE BOT READY TO PITCH & DEPLOY!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_jain_store())
