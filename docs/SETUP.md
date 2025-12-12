# FB Messenger -> Telegram Bridge — Setup & Test Guide

This document explains step-by-step how to configure, run and test the project that receives Facebook Messenger webhook events and forwards them to Telegram.

Contents
- Requirements
- Files in this repo
- Environment variables
- Run locally (dev) with ngrok
- Register and verify webhook on Facebook
- Subscribe Page to events
- Test end-to-end (real message)
- Troubleshooting
- Security and production notes
- Optional next steps

---

## Requirements
- Python 3.10+ (we used a conda env in development)
- Node/npm only if you plan to use `localtunnel` (optional)
- ngrok (or alternative tunnel) for exposing local server over HTTPS in dev
- A Facebook Developer account and access to the target Page
- A Telegram bot token and chat id (group or user)

## Files in this repo (important)
- `app/main.py` — FastAPI application that verifies FB signature and forwards messages to Telegram
- `requirements.txt` — Python dependencies
- `.env.example` — example environment variables
- `test_send_webhook.py` / `test_ngrok_webhook.sh` — test scripts to simulate FB webhook
- `README.md` and this `docs/SETUP.md` — docs

## Environment variables
Create a `.env` file in the repo root (do NOT commit it). Example values are shown in `.env.example`.

Required variables:
- `FB_VERIFY_TOKEN` — a secret string you choose for webhook verification (e.g. `testing1234`). This is NOT provided by Facebook; you define it and enter the same value in the FB dashboard.
- `FB_APP_SECRET` — your Facebook App Secret (from Facebook Developer Dashboard → Settings → Basic). Used to verify `X-Hub-Signature-256`.
- `PAGE_ACCESS_TOKEN` — Page access token for the target Page (used to subscribe via API or to send messages as Page). Keep secret.
- `PAGE_ID` — numeric Facebook Page ID.
- `TELEGRAM_BOT_TOKEN` — token from `@BotFather` for your Telegram bot.
- `TELEGRAM_CHAT_ID` — numeric chat id (group or user) where notifications are sent.

Example `.env`:
```
FB_VERIFY_TOKEN=testing1234
FB_APP_SECRET=your_app_secret_here
PAGE_ACCESS_TOKEN=EAA...ZDZD
PAGE_ID=1234567890

TELEGRAM_BOT_TOKEN=123456:ABCDEF...
TELEGRAM_CHAT_ID=-1001234567890
```

## Install dependencies

Prefer to create a virtualenv/conda environment.

```bash
python -m pip install -r requirements.txt
```

Confirm `httpx` import works:

```bash
python -c "import httpx; print(httpx.__version__)"
```

## Run app locally

Load environment and start uvicorn using the same Python interpreter you installed dependencies into:

```bash
# set env vars from .env
set -a; . .env; set +a

# start with the Python interpreter from your venv/conda
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Tip: use `python -m uvicorn` to ensure the same interpreter is used.

## Expose local server with ngrok (dev)

Install and authenticate ngrok (you can use alternatives listed below):

```bash
# register at https://ngrok.com and get authtoken
ngrok authtoken YOUR_AUTHTOKEN

ngrok http 8000
```

Copy the HTTPS forwarding URL, e.g. `https://abcd1234.ngrok-free.app`.
Your callback URL will be `https://abcd1234.ngrok-free.app/webhook`.

Alternatives if you don't want ngrok:
- `localtunnel` (npm): `lt --port 8000`
- `cloudflared` (Cloudflare)
- `smee.io` relay

## Register webhook on Facebook (Developer Dashboard)

1. Open https://developers.facebook.com and select your App.
2. In left menu choose **Messenger** → **Settings** → **Webhooks**.
3. In the Configure Webhooks section, add the Callback URL and Verify Token:
   - Callback URL: `https://<your-tunnel-host>/webhook`
   - Verify token: value of `FB_VERIFY_TOKEN` in your `.env` (e.g. `testing1234`)
4. Click **Verify and Save**. Facebook will send a GET with `hub.challenge` and your server must return that value — the code in `app/main.py` does this.

## Subscribe Page to app events

Using the Dashboard:
- In Messenger -> Settings -> Webhooks, choose **Subscribe a Page** and pick your Page. Select fields: `messages`, `messaging_postbacks`, `message_deliveries`, `message_reads`.

Using Graph API (scriptable):

```bash
PAGE_ID=your_page_id
PAGE_ACCESS_TOKEN=EAA...ZDZD

curl -X POST "https://graph.facebook.com/v17.0/${PAGE_ID}/subscribed_apps" \
  -d "subscribed_fields=messages,messaging_postbacks,message_deliveries,message_reads" \
  -d "access_token=${PAGE_ACCESS_TOKEN}"
```

Response should be `{"success":true}`.

## Obtain Telegram Chat ID

1. Add your bot to the Telegram group (or chat the bot directly).
2. If `getUpdates` is empty, send a message to the bot or group.
3. Run:

```bash
export BOT_TOKEN="$(grep '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2- | tr -d '"')"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates" | jq .
```

Look for `message.chat.id` in the result and set `TELEGRAM_CHAT_ID` accordingly.

## Test end-to-end with a real Page message

1. Ensure server is running and ngrok (or alternative) is active.
2. Ensure `FB_VERIFY_TOKEN` and `FB_APP_SECRET` in `.env` match your app values and env is loaded when starting the server.
3. Ensure Page is subscribed to app events and bot/chat id are configured.
4. Send a message to the Page (use Messenger). In development mode, the sender must be admin/tester of the app.
5. Check server logs — should show POST `/webhook` handling and forwarding to Telegram. Telegram group should receive a notification.

## Simulate webhook (if you want to test without actually messaging Page)

There are test scripts in the repo. Example: `test_send_webhook.py` or `test_ngrok_webhook.sh`.

Example manual cURL (signed) to ngrok URL:

```bash
payload='{"entry":[{"messaging":[{"sender":{"id":"TEST"},"message":{"text":"Hello test"}}]}]}'
FB_APP_SECRET="your_app_secret"
sig=$(printf '%s' "$payload" | openssl dgst -sha256 -hmac "$FB_APP_SECRET" -binary | xxd -p -c 256)

curl -X POST "https://<ngrok-url>/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$sig" \
  -d "$payload"
```

## Troubleshooting
- If `getUpdates` returns empty for Telegram: make sure your bot received a message (send one) and delete webhook if previously set: `deleteWebhook`.
- If `uvicorn` says `ModuleNotFoundError: No module named 'httpx'`, ensure you start uvicorn with the same Python interpreter where `httpx` is installed: `python -m uvicorn app.main:app`.
- If ngrok returns authentication errors, run `ngrok authtoken <token>`.
- If webhook verification fails: check the Verify Token matches and server is accessible by Facebook.

## Security & production notes
- Store secrets in environment variables or secret manager; do not commit `.env`.
- Keep `FB_APP_SECRET` private; rotate if leaked.
- Validate `X-Hub-Signature-256` on every POST (app/main.py does this when `FB_APP_SECRET` is set).
- Add logging, retry/backoff for Telegram API calls; consider queueing events to avoid dropped events.
- For production use a proper hosting (Cloud Run / VPS / Heroku) with HTTPS and a stable domain; do not rely on ngrok for production.

## Optional: Dockerfile (quick idea)

Create a Dockerfile that installs dependencies and runs `uvicorn app.main:app` and use a secret store for envs.

## Next steps & app review
- If you want to serve messages from the Page to public users (not just app admins/testers), you must request the `pages_messaging` permission via App Review. Prepare a screencast demonstrating your app, a privacy policy, and test users.

---

If you want, I can:
- generate a shell script that automates register-subscribe steps via Graph API (you provide `APP_ID`, `APP_SECRET`, `PAGE_ID`, `PAGE_ACCESS_TOKEN`),
- add a `Dockerfile` and a sample `systemd` unit for deployment, or
- create a short screencast checklist for App Review assets.

Saved file: `docs/SETUP.md`
