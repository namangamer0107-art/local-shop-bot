# WhatsApp Automation & AI Assistant for Local Shops: Architecture & Commercial Playbook

---

## 1. Executive Summary & Value Proposition

Local shops (salons, bakeries, dental/physio clinics, grocery/kirana stores, restaurants) lose 20–40% of inbound sales because:
1. They cannot respond immediately during peak shop hours.
2. After-hours queries (8 PM to 9 AM) go unanswered.
3. Taking manual orders and booking slots via phone calls or chat is messy and prone to error.

### The Commercial Offer
* **Setup Fee:** $150 – $350 (one-time config: catalog upload, business hours, FAQs, template approvals).
* **Monthly Retainer:** $30 – $80 / month (covers hosting, WhatsApp Cloud API message units, AI token overhead, minor catalog updates).
* **Target ROI for Shop Owner:** Paying for itself with just 3 to 5 extra orders or bookings saved each month.

---

## 2. Core Feature Matrix for Local Businesses

| Capability | What It Does | Shop Owner Benefit |
| :--- | :--- | :--- |
| **Instant FAQ Responder** | Answers timing, location, parking, payment methods, return policy, and services menu. | Eliminates repetitive phone calls. |
| **Interactive Catalog & Ordering** | Sends interactive list messages / buttons for items; generates order summary + delivery address prompt. | Clean orders formatted directly into shop owner's WhatsApp / Google Sheet. |
| **Appointment Booking** | Displays available time slots, collects customer name & service, confirms slot, sets reminders. | Fewer no-shows; salon/clinic scheduling on autopilot. |
| **Human Takeover / Alert** | Notifies shop owner instantly when a customer requests a real person or asks about a custom request. | Zero risk of AI hallucinating prices or making unauthorized promises. |
| **Multi-Language Support** | Seamlessly switches between English, Hindi, Spanish, or regional dialects using Gemini LLM. | Non-English customers feel right at home. |

---

## 3. Recommended Technical Architecture

```
┌──────────────────┐
│  End Customer    │
│  (WhatsApp App)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│ Meta WhatsApp Cloud API                      │
│ (Official Webhook & Messaging API)           │
└────────┬─────────────────────────────────────┘
         │ Webhook Event (Incoming Message)
         ▼
┌──────────────────────────────────────────────┐
│ FastAPI Backend (Python)                     │
│ - Webhook verification & deduplication       │
│ - Session state machine (Conversation State) │
│ - Multi-Tenant Business Configuration Router │
└────────┬─────────────────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
┌─────────────────────────┐   ┌───────────────────────────┐
│ Gemini 2.5 Flash API    │   │ Database & Integrations   │
│ - Intent Classification │   │ - SQLite / JSON DB        │
│ - Smart Q&A extraction │   │ - Google Sheets (Orders)  │
│ - Natural conversation  │   │ - Google Calendar / Slots │
└─────────────────────────┘   └───────────────────────────┘
```

### Why Meta WhatsApp Cloud API (Official)?
* Free tier provides **1,000 service (user-initiated) conversations free per month**.
* Zero risk of phone number ban compared to unofficial QR/Web scraper tools.
* Supports **Interactive Buttons, List Messages, and Location Messages**.

---

## 4. Multi-Tenant Turnkey System Structure

To scale this to 10–50 local shops effortlessly without rewriting code, the system is designed to be **multi-tenant** (config-driven):

```
local_bot/
├── src/
│   ├── app.py                 # FastAPI Webhook listener & entrypoint
│   ├── config.py              # Environment variables & API credentials
│   ├── services/
│   │   ├── whatsapp.py        # Meta Cloud API message sender (text, buttons, lists)
│   │   ├── ai_brain.py        # Gemini API prompt runner & structured extractor
│   │   ├── booking.py         # Slot calculation & calendar/sheet sync
│   │   └── order.py           # Cart management & order summarizer
│   └── tenants/               # Separate shop configuration files
│       ├── salon_demo.json    # Services, hours, prices, FAQ knowledge base
│       └── bakery_demo.json   # Menu, dietary info, delivery radius
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```
