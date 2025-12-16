#!/usr/bin/env bash
set -e

FB_APP_SECRET="0187146a6926437ecdaa2cc1d25e8bd6"
NGROK_URL="https://46a395eb51af.ngrok-free.app"

payload='{"entry":[{"messaging":[{"sender":{"id":"TEST_USER_123"},"message":{"text":"Hello from test - forwarding to Telegram!"}}]}]}'

sig=$(printf '%s' "$payload" | openssl dgst -sha256 -hmac "$FB_APP_SECRET" -binary | xxd -p -c 256)

echo "Sending signed webhook to ${NGROK_URL}/webhook ..."
echo "Payload: $payload"
echo "Signature: sha256=$sig"
echo ""

response=$(curl -s -X POST "${NGROK_URL}/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$sig" \
  -d "$payload")

echo "Response:"
echo "$response" | jq . || echo "$response"
