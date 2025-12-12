import os
import hmac
import hashlib
import json
import requests

# load .env values
from pathlib import Path
env_file = Path('.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k,v = line.split('=',1)
            os.environ.setdefault(k.strip(), v.strip())

FB_APP_SECRET = os.getenv('FB_APP_SECRET')
URL = os.getenv('WEBHOOK_URL','http://127.0.0.1:8000/webhook')

payload = {"entry":[{"messaging":[{"sender":{"id":"TEST_SENDER"},"message":{"text":"Hello from FB test"}}]}]}
body = json.dumps(payload, ensure_ascii=False)

sig = hmac.new(FB_APP_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest() if FB_APP_SECRET else ''
headers = {'Content-Type':'application/json'}
if sig:
    headers['X-Hub-Signature-256'] = 'sha256=' + sig

print('Posting to', URL)
print('Headers:', headers)
print('Body:', body)

r = requests.post(URL, headers=headers, data=body)
print('Status:', r.status_code)
try:
    print('Response JSON:', r.json())
except Exception:
    print('Response Text:', r.text)
