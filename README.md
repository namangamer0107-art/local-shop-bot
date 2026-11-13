# Turnkey WhatsApp Bot for Local Shops (SaaS Architecture)

An end-to-end, multi-tenant WhatsApp AI booking, ordering, and FAQ bot platform tailored for local business owners (Salons, Bakeries, Clinics, Cafes, Retail Shops).

---

## 💼 Business & Sales Model
- **Setup Fee:** $150 – $350 (one-time config: menus, services, hours, business information).
- **Monthly Subscription:** $30 – $80 / month (covers hosting, WhatsApp Cloud API messages, AI token costs, catalog updates).
- **Pitch Strategy & Client Proposal:** See [PROJECT_BLUEPRINT.md](file:///d:/Prozoo/local_bot/PROJECT_BLUEPRINT.md).

---

## 🚀 Key Features Built-In
1. **Official WhatsApp Cloud API Integration:** Zero risk of number bans; supports interactive quick-reply buttons and clickable lists.
2. **Deterministic Booking Flow:** Eliminates AI hallucinations for dates, times, and pricing.
3. **Gemini 2.5 Flash Powered Q&A:** Answers unstructured questions in any language (directions, parking, payment methods, policies).
4. **Multi-Tenant Config Architecture:** Add a new local shop in 2 minutes simply by creating a JSON configuration file under `tenants/`.
5. **Simulated Sandbox Mode:** Allows live end-to-end testing without needing active Meta API credentials.

---

## 📁 Project Structure

```
local_bot/
├── tenants/
│   └── salon_demo.json            # Business profile, services, slots, and FAQs
├── src/
│   ├── app.py                     # FastAPI webhook receiver and simulation API
│   ├── config.py                  # Environment variable configuration
│   └── services/
│       ├── ai_brain.py            # Gemini AI fallback for natural language questions
│       ├── conversation_flow.py   # State machine for buttons, lists, and booking
│       ├── tenant_manager.py      # Multi-tenant business profile loader
│       └── whatsapp.py            # WhatsApp Cloud API payload generator
├── tests/
│   └── test_simulation.py        # End-to-end simulation test suite
├── .env.example                   # Meta & Gemini credentials template
└── requirements.txt               # Dependencies
```

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Verification Simulation
```bash
python -m tests.test_simulation
```

### 3. Start the Webhook Server
```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```
