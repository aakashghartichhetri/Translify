"""Demo service contract tests (not translation quality tests)."""
from fastapi.testclient import TestClient
from demo_ai.main import app

client = TestClient(app)


def test_demo_has_obvious_disclaimer():
    assert client.get('/health').json()['mode'] == 'demo-fixture-no-real-ai'
    response = client.post('/translate',json={
        'text': 'Hello', 'sourceLanguage': 'en','targetLanguage': 'es',
    })
    assert response.status_code == 200
    assert response.json()['translatedText'].startswith('[DEMO — NOT TRANSLATED]')


def test_demo_upload_response_contracts():
    image = client.post('/capture',files={'image':('test.png',b'123','image/png')})
    assert image.status_code == 200
    assert image.json()['contents'][0]['bbox']['w'] > 0
    speech = client.post('/speech/transcribe',data={'language':'en'},files={'file':('voice.wav',b'123','audio/wav')})
    assert speech.status_code == 200
    assert speech.json()['language'] == 'en'
    assert 'Demo' in speech.json()['text']
