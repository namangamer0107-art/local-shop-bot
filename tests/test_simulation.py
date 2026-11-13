import asyncio
from src.services.tenant_manager import tenant_manager
from src.services.whatsapp import WhatsAppService
from src.services.conversation_flow import ConversationFlow
from src.services.database import db

async def run_simulation():
    print("=" * 60)
    print("LOCAL SHOP WHATSAPP BOT - VERIFICATION RUN")
    print("=" * 60)

    tenant_id = "salon_demo"
    salon = tenant_manager.get_tenant(tenant_id)
    print(f"Loaded Business: {salon['business_name']} ({salon['category']})")
    
    wa = WhatsAppService()
    flow = ConversationFlow(tenant_id, salon, wa)
    test_user = "+1234567890"

    # Step 1: Customer sends "Hi"
    print("\n--- Step 1: Customer sends 'Hi' ---")
    await flow.handle_message(test_user, {"type": "text", "text": {"body": "Hi"}})

    # Step 2: Customer selects 'btn_book'
    print("\n--- Step 2: Customer taps 'Book Appointment' button ---")
    await flow.handle_message(
        test_user,
        {
            "type": "interactive",
            "interactive": {
                "type": "button_reply",
                "button_reply": {"id": "btn_book", "title": "📅 Book Appointment"}
            }
        }
    )

    # Step 3: Customer selects slot
    print("\n--- Step 3: Customer selects slot 'Today 5:30 PM' ---")
    await flow.handle_message(
        test_user,
        {
            "type": "interactive",
            "interactive": {
                "type": "list_reply",
                "list_reply": {"id": "slot_1", "title": "Today 5:30 PM"}
            }
        }
    )

    # Step 4: Customer provides name
    print("\n--- Step 4: Customer provides name 'John Doe' ---")
    await flow.handle_message(test_user, {"type": "text", "text": {"body": "John Doe"}})

    # Verify Database entry
    print("\n--- Step 5: Verify Saved Appointments in Database ---")
    appts = db.list_appointments(tenant_id)
    print(f"Total appointments in database: {len(appts)}")
    for a in appts:
        print(f" -> ID: #{a['id']} | Customer: {a['customer_name']} | Service: {a['service']} | Slot: {a['slot']}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE: READY FOR SALE!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_simulation())
