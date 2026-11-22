#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PYTEST'
import json, urllib.request, urllib.parse, urllib.error, secrets
base = 'http://127.0.0.1:8000'

def request(path, payload=None, token=None, form=False):
    headers = {}
    if token: headers['Authorization'] = f'Bearer {token}'
    body = None
    if payload is not None:
        if form:
            body = urllib.parse.urlencode(payload).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = json.dumps(payload).encode('utf-8')
            headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(base+path, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, json.load(resp)

status, data = request('/health')
assert status == 200 and data['status'] == 'ok'
email = f'demo-{secrets.token_hex(4)}@example.org'
password = secrets.token_urlsafe(20)
status, _ = request('/signup', {'email': email, 'password': password})
assert status == 201
status, login = request('/login', {'username': email, 'password': password},form=True)
assert status == 200 and login['access_token']
status, translated = request('/translate', {'text': 'hello', 'source_language': 'en',
  'target_language':'es', 'store_history':True}, token=login['access_token'])
assert status == 200 and translated['translated_text'].startswith('[DEMO — NOT TRANSLATED]')
status, hist = request('/history',token=login['access_token'])
assert status == 200 and hist['count'] == 1
print('PASS: /health, signup, login, demo text translation and opted-in history')
print('NOTE: demo AI does not perform real OCR, speech recognition, or translation.')
PYTEST
