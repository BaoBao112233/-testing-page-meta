import os
import hmac
import hashlib
import logging
import json
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Header, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "changeme_verify_token")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

app = FastAPI(title="FB Messenger -> Telegram Bridge")


def verify_signature(body: bytes, signature_header: Optional[str]) -> bool:
    if not signature_header:
        logger.warning("No X-Hub-Signature-256 header present")
        return False if FB_APP_SECRET else True

    try:
        sig_type, sig_hash = signature_header.split("=", 1)
    except Exception:
        logger.exception("Malformed signature header")
        return False

    if sig_type != "sha256":
        logger.warning("Unsupported signature type: %s", sig_type)
        return False

    if not FB_APP_SECRET:
        logger.warning("FB_APP_SECRET not set, skipping signature verification")
        return True

    expected = hmac.new(FB_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_hash)


async def forward_to_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram bot token or chat id not set, skipping forward")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=payload, timeout=10.0)
            r.raise_for_status()
            logger.info("Forwarded to Telegram: %s", text)
            return True
        except Exception:
            logger.exception("Failed to forward to Telegram")
            return False


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/webhook")
async def fb_verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        logger.info("Webhook verified with challenge: %s", challenge)
        return int(challenge) if challenge and challenge.isdigit() else challenge
    logger.warning("Webhook verification failed: mode=%s token=%s", mode, token)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def fb_webhook(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256):
        logger.warning("Signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except Exception:
        logger.exception("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Facebook sends objects with 'entry' array
    entries = payload.get("entry", [])
    forwarded = 0

    for entry in entries:
        messaging = entry.get("messaging", []) or entry.get("changes", [])
        for event in messaging:
            # Common Messenger message
            sender = event.get("sender", {}).get("id") or event.get("from", {}).get("id")
            message = event.get("message") or event.get("value") or {}
            text = None
            if isinstance(message, dict):
                text = message.get("text")

            # Build a friendly notify message
            parts = [f"FB Msg from {sender}"]
            if text:
                parts.append(text)
            else:
                parts.append("(non-text event)")

            # add quick raw dump for debugging
            try:
                short = json.dumps(event, ensure_ascii=False)
                if len(short) > 800:
                    short = short[:800] + "..."
                parts.append(f"\n--- event preview ---\n{short}")
            except Exception:
                pass

            notify_text = "\n".join(parts)
            ok = await forward_to_telegram(notify_text)
            if ok:
                forwarded += 1

    return {"status": "received", "forwarded": forwarded}
