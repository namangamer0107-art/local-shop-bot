import asyncio
from src.services.tenant_manager import tenant_manager
from src.services.whatsapp import WhatsAppService
from src.services.conversation_flow import ConversationFlow
from src.services.database import db

async def simulate_naman_order():
    print("=" * 65)
    print("SIMULATING CUSTOMER 'NAMAN' (8375800986) ORDERING FROM STORE")
    print("=" * 65)

    tenant_id = "jain_shubh_masale"
    profile = tenant_manager.get_tenant(tenant_id)
    wa = WhatsAppService()
    flow = ConversationFlow(tenant_id, profile, wa)

    naman_phone = "+918375800986"

    # Step 1: Naman texts "target" on WhatsApp
    print("\n[Step 1] Naman sends: 'target'")
    await flow.handle_message(naman_phone, {"type": "text", "text": {"body": "target"}})

    # Step 2: Naman sends his spice & flour order
    naman_order = "5kg Chakki Atta, 500g Haldi, 500g Lal Mirch, 100g Hing"
    print(f"\n[Step 2] Naman sends his order:\n'{naman_order}'")
    await flow.handle_message(naman_phone, {"type": "text", "text": {"body": naman_order}})

    # Step 3: Naman sends his delivery address
    naman_address = "House No. 12, Block B, Near Metro Station, New Ashok Nagar"
    print(f"\n[Step 3] Naman sends his delivery address:\n'{naman_address}'")
    await flow.handle_message(naman_phone, {"type": "text", "text": {"body": naman_address}})

    # Step 4: Verify generated receipt in database
    orders = db.list_orders(tenant_id)
    latest = orders[0]
    print("\n" + "=" * 65)
    print("OFFICIAL RECEIPT STORED IN DATABASE & SENT TO ADMIN 9958240721:")
    print(f"Receipt ID: #{latest['id']}")
    print(f"Customer Name: Naman")
    print(f"Customer Phone: {latest['customer_phone']}")
    print(f"Items: {latest['items']}")
    print(f"Address: {latest['delivery_address']}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(simulate_naman_order())
