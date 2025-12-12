# FB Messenger -> Telegram webhook bridge (FastAPI)

This small example receives Facebook Messenger webhook events and forwards a short notification to Telegram.

Quick start

1. Copy `.env.example` to `.env` and fill in values:

```
FB_VERIFY_TOKEN=your_verify_token_here
FB_APP_SECRET=your_facebook_app_secret_here
TELEGRAM_BOT_TOKEN=123456:ABC-DEF_your_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run the app:

```bash
# from repo root
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Expose to the internet for Facebook (use `ngrok`):

```bash
ngrok http 8000
```

5. In Facebook Developer console, set your webhook URL to `https://<ngrok-host>/webhook` and the verify token to the same `FB_VERIFY_TOKEN` you set.

6. Subscribe your Page to the webhook events (Pages -> Webhooks / or via Graph API) and test messaging the Page. Incoming messages will be forwarded to your Telegram chat.

Notes
- The app checks `X-Hub-Signature-256` header using `FB_APP_SECRET`. If you leave `FB_APP_SECRET` empty it will skip verification (not recommended for production).
- Adjust message parsing in `app/main.py` to suit other event shapes (attachments, postbacks, etc.).