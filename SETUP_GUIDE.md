# 🚀 Setup Guide: Connecting WhatsApp to Jain Provision Store

Follow these 4 simple steps to connect the live WhatsApp Business API to your bot.

---

## 📌 Prerequisites (What You Need)
1. A **Meta Developer Account** (Free, takes 1 minute at [developers.facebook.com](https://developers.facebook.com)).
2. Any phone number to receive WhatsApp messages for testing (Meta provides a **free test number** immediately).
3. A Gemini API Key (Free tier from [aistudio.google.com](https://aistudio.google.com)).

---

## 🛠️ Step 1: Get Free Meta WhatsApp Cloud API Credentials (5 mins)

1. Go to **[Meta for Developers](https://developers.facebook.com/)** and log in with your Facebook account.
2. Click **My Apps** (top right) $\to$ **Create App**.
3. Select **Other** $\to$ choose **Business** as the app type $\to$ give it a name like `Jain Store Bot`.
4. In the App Dashboard, scroll down to **WhatsApp** and click **Set up**.
5. You will see the **API Setup** page:
   - **Temporary Access Token:** (Click copy).
   - **Phone Number ID:** (A 15-digit number, click copy).
   - **Test Phone Number:** Meta gives you a free sandbox number!

---

## ⚙️ Step 2: Configure Your `.env` File

In `d:\Prozoo\local_bot\`, copy `.env.example` to `.env` (or edit `.env`) and paste your keys:

```ini
META_API_TOKEN=EAAxxxxxxx... (Your copied Access Token)
WHATSAPP_PHONE_NUMBER_ID=1092837465xxxxx (Your copied Phone Number ID)
VERIFY_TOKEN=jain_store_secret_token_123
GEMINI_API_KEY=AIzaxxxxxxx... (Your Gemini API key)
DEFAULT_TENANT=jain_provision_store
```

---

## 🌐 Step 3: Run the Bot Server & Expose via Ngrok

### 1. Start the FastAPI Bot Engine
Open PowerShell in `d:\Prozoo\local_bot` and run:
```powershell
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Make it Reachable to Meta (Using Free Ngrok or Localtunnel)
Meta needs a public HTTPS URL to send incoming customer messages to your computer:
```powershell
# In a second terminal window:
npx localtunnel --port 8000
# OR if you have ngrok:
ngrok http 8000
```
You will get a public URL like: `https://cool-shop-url.loca.lt` (or `https://xxxx.ngrok-free.app`).

---

## 🔗 Step 4: Link the Webhook in Meta Dashboard

1. Go back to your **Meta Developer App** $\to$ **WhatsApp** $\to$ **Configuration**.
2. Under **Webhook**, click **Edit**:
   - **Callback URL:** `https://your-public-url/webhook`
   - **Verify Token:** `jain_store_secret_token_123` (Same as in your `.env`)
3. Click **Verify and Save**.
4. Under **Webhook fields**, click **Manage** $\to$ click **Subscribe** next to `messages`.

---

## 🎉 Test It Live on WhatsApp!
1. Add your personal WhatsApp number under **"To"** in Meta's **API Setup** page.
2. Send **"Hi"** from your phone to Meta's test WhatsApp number!
3. The bot will reply with **Jain Provision Store's** welcome buttons and take grocery orders directly into your SQLite database and live dashboard (`http://localhost:8000/dashboard`).
