#!/usr/bin/env bash
set -e

PAGE_ID="924903834036727"
PAGE_ACCESS_TOKEN="EAALZCrK2SRwsBQHk1Khw5QqlwAUWvR3hN059n6zTRHyCt4ZCuRhiOm0LkOzMFJ3TshGQA4oXG3si2vDZA7CRUspCaUUmEusoVe7ULBdz8tMYarZCwO8UrjNOlsJn70wLqLg76JNELCl1NiZAbkdQkT4LzZBn9qRuEpaOrX1W1HFEQqZBcSUaQfhqM4PMl7x5gowMqkxuAZDZD"

echo "=== Checking current Page subscriptions ==="
curl -s "https://graph.facebook.com/v17.0/${PAGE_ID}/subscribed_apps?access_token=${PAGE_ACCESS_TOKEN}" | jq .

echo ""
echo "=== Re-subscribing Page to webhook fields ==="
response=$(curl -s -X POST "https://graph.facebook.com/v17.0/${PAGE_ID}/subscribed_apps" \
  -d "subscribed_fields=messages,messaging_postbacks,message_deliveries,message_reads" \
  -d "access_token=${PAGE_ACCESS_TOKEN}")

echo "$response" | jq .

if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
  echo ""
  echo "✓ Page subscribed successfully!"
else
  echo ""
  echo "✗ Subscription may have failed. Check response above."
fi
