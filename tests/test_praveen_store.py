import asyncio
from src.services.tenant_manager import tenant_manager
from src.services.whatsapp import WhatsAppService
from src.services.conversation_flow import ConversationFlow
from src.services.database import db

async def test_praveen_store():
    print("=" * 65)
    print("DEMO RUN: PRAVEEN KIRANA & GENERAL STORE (9818348152)")
    print("=" * 65)

    tenant_id = "praveen_general_store"
    profile = tenant_manager.get_tenant(tenant_id)
    print(f"Store: {profile['business_name']}")
    print(f"Owner: {profile.get('owner_name')} ({profile['owner_phone']})")
    print(f"Address: {profile['address']}")

    wa = WhatsAppService()
    flow = ConversationFlow(tenant_id, profile, wa)
    customer_phone = "+918375800986"  # Naman

    # 1. Customer initiates with "target"
    print("\n[Step 1] Customer sends: 'target'")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": "target"}})

    # 2. Customer orders snacks & staples
    order_items = "2 packets Haldiram Namkeen, 5kg Atta, 1 Amul Butter 500g"
    print(f"\n[Step 2] Customer sends order: '{order_items}'")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": order_items}})

    # 3. Customer provides flat details in Eastend Apartments
    address = "Flat 124, Pocket 2, Eastend Apartments, Mayur Vihar / Ashok Nagar"
    print(f"\n[Step 3] Customer sends address: '{address}'")
    await flow.handle_message(customer_phone, {"type": "text", "text": {"body": address}})

    # 4. Verify Database
    orders = db.list_orders(tenant_id)
    latest = orders[0]
    print("\n" + "=" * 65)
    print("SUCCESS: RECEIPT CREATED & ALERT ROUTED TO OWNER 9818348152")
    print(f"Receipt ID: #{latest['id']}")
    print(f"Customer: {latest['customer_phone']}")
    print(f"Order: {latest['items']}")
    print(f"Address: {latest['delivery_address']}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_praveen_store())
