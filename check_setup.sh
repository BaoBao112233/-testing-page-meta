#!/usr/bin/env bash
set -e

source .env

echo "=== Current ngrok public URL ==="
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url // "no tunnel"')
echo "$NGROK_URL"
echo ""
echo "Your webhook callback URL should be: ${NGROK_URL}/webhook"
echo ""

echo "=== Checking Page ${PAGE_ID} subscription status ==="
curl -s "https://graph.facebook.com/v17.0/${PAGE_ID}/subscribed_apps?access_token=${PAGE_ACCESS_TOKEN}" | jq .

echo ""
echo "=== Re-subscribing Page to messages field ==="
response=$(curl -s -X POST "https://graph.facebook.com/v17.0/${PAGE_ID}/subscribed_apps" \
  -d "subscribed_fields=messages,messaging_postbacks,message_deliveries,message_reads" \
  -d "access_token=${PAGE_ACCESS_TOKEN}")

echo "$response" | jq .

if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
  echo ""
  echo "✓ Page subscribed successfully!"
  echo ""
  echo "IMPORTANT: Make sure your Facebook webhook Callback URL is set to:"
  echo "  ${NGROK_URL}/webhook"
  echo ""
  echo "And Verify Token is: ${FB_VERIFY_TOKEN}"
else
  echo ""
  echo "✗ Subscription failed. Check response above."
fi
