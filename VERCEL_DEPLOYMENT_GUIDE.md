# 🚀 Vercel Deployment & Meta Production Callback Setup

This guide walks you through deploying your WhatsApp bot onto Vercel and connecting the permanent HTTPS Callback URL into Meta Developer Portal.

---

## 🔒 1. Shopkeeper Secret Phone + PIN Authentication
Each shopkeeper accesses their live portal at:
`https://your-vercel-domain.vercel.app/login`

* **Praveen Kirana & General Store:**
  - Phone: `9818348152`
  - Secret PIN: `7890` (Configured in `tenants/praveen_general_store.json`)
* **Master PIN (You / Admin):** `7890` opens any shop.

Only you and the authorized shopkeeper know the PIN.

---

## ☁️ 2. Deploy to Vercel (Takes 2 Minutes)

### Option A: Via GitHub & Vercel Web Dashboard (Easiest)
1. Push `d:\Prozoo\local_bot` to your GitHub account repository (public or private).
2. Go to **[vercel.com](https://vercel.com/)** and click **"Add New" $\to$ "Project"**.
3. Select your GitHub repository.
4. Under **Environment Variables**, add:
   - `META_API_TOKEN` = (Your token from Meta Developer portal)
   - `WHATSAPP_PHONE_NUMBER_ID` = `1479360331925107`
   - `VERIFY_TOKEN` = `jain_shubh_masale_secret_123`
   - `DEFAULT_TENANT` = `praveen_general_store`
5. Click **Deploy**!
   - Vercel will give you a permanent HTTPS URL, for example:
     `https://jain-bot-platform.vercel.app`

---

## 🔗 3. Connecting Meta Production Callback URL

Once deployed on Vercel:
1. Go to your **[Meta Developer Portal](https://developers.facebook.com/apps)** $\to$ Open `Jain Provision Store Bot`.
2. Look on the left menu: **WhatsApp** $\to$ **Configuration** (or Step 2 Webhooks).
3. Under **Webhook**, enter:
   - **Callback URL:**
     ```
     https://your-vercel-domain.vercel.app/webhook
     ```
   - **Verify Token:**
     ```
     jain_shubh_masale_secret_123
     ```
4. Click **Verify and Save**.
5. Click **Manage** (Webhook fields) $\to$ check **Subscribe** next to `messages`.

Your bot is now permanently online 24/7 without needing your laptop to stay awake!
