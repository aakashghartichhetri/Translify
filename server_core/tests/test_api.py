import io
import wave
from datetime import datetime, timedelta, timezone
import httpx
import jwt
from PIL import Image
from sqlalchemy.exc import OperationalError
from app.config import ALGORITHM, MAX_AUDIO_BYTES, MAX_IMAGE_BYTES, SECRET_KEY
from app.database import get_db
from app.main import app


def png():
    output = io.BytesIO()
    Image.new("RGB", (10, 10)).save(output, format="PNG")
    return output.getvalue()


def wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\0\0" * 1600)
    return output.getvalue()


def translate(client, auth, **params):
    return client.post("/translate", json={"text": "hello", "source_language": "en", "target_language": "es", **params}, headers=auth)


def image(client, auth, payload=None, **fields):
    return client.post("/translate/image-to-text", headers=auth,
                       files={"image": ("photo.png", png() if payload is None else payload, "image/png")},
                       data={"source_language": "en", "target_language": "es", **fields})


def speech(client, auth, payload=None, **fields):
    return client.post("/translate/speech-to-text", headers=auth,
                       files={"recording": ("voice.wav", wav() if payload is None else payload, "audio/wav")},
                       data={"source_language": "en", "target_language": "es", **fields})


def test_health_and_restricted_cors(client):
    assert client.get("/health").json() == {"status": "ok"}
    trusted = client.options("/translate", headers={"Origin": "https://trusted.example", "Access-Control-Request-Method": "POST"})
    assert trusted.headers["access-control-allow-origin"] == "https://trusted.example"
    evil = client.options("/translate", headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in evil.headers


def test_signup_login_validation_and_duplicate(client):
    assert client.post("/signup", json={"email": "bad", "password": "long-enough"}).status_code == 422
    assert client.post("/signup", json={"email": "a@b.com", "password": "short"}).status_code == 422
    user = client.post("/signup", json={"email": "Someone@example.com", "password": "long-enough"})
    assert user.status_code == 201
    assert user.json()["email"] == "someone@example.com"
    assert "password_hash" not in user.json()
    assert client.post("/signup", json={"email": "someone@example.com", "password": "long-enough"}).status_code == 409
    assert client.post("/login", data={"username": "someone@example.com", "password": "wrong-pass"}).status_code == 401
    token = client.post("/login", data={"username": "someone@example.com", "password": "long-enough"})
    assert token.status_code == 200
    assert client.get("/me", headers={"Authorization": f"Bearer {token.json()['access_token']}"}).status_code == 200


def test_authentication_expired_missing_and_inactive(client, login):
    auth = login()
    for endpoint in ("/me", "/history", "/translate"):
        request = client.post(endpoint, json={"text":"hello", "source_language":"en", "target_language":"es"}) if endpoint == "/translate" else client.get(endpoint)
        assert request.status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired = jwt.encode({"sub": "user@example.com", "iat": past - timedelta(hours=1), "exp": past}, SECRET_KEY, algorithm=ALGORITHM)
    assert client.get("/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    missing_exp = jwt.encode({"sub": "user@example.com", "iat": past}, SECRET_KEY, algorithm=ALGORITHM)
    assert client.get("/me", headers={"Authorization": f"Bearer {missing_exp}"}).status_code == 401
    from app.database import SessionLocal
    from app.models import User
    with SessionLocal() as db:
        db.query(User).filter(User.email == "user@example.com").update({"is_active": False})
        db.commit()
    assert client.get("/me", headers=auth).status_code == 401


def test_history_opt_in_out_and_user_isolation(client, login):
    alice, bob = login("alice@example.com"), login("bob@example.com")
    assert translate(client, alice).status_code == 200
    assert client.get("/history", headers=alice).json()["count"] == 0
    assert translate(client, alice, store_history=True).status_code == 200
    assert translate(client, alice, store_history=False).status_code == 200
    assert client.get("/history", headers=alice).json()["count"] == 1
    assert client.get("/history", headers=bob).json()["count"] == 0
    assert translate(client, bob, store_history=True).status_code == 200
    assert client.get("/history", headers=bob).json()["count"] == 1
    assert client.get("/history", headers=alice).json()["count"] == 1


def test_text_translation_payload_validation(client, login, mock_upstreams):
    auth = login()
    assert translate(client, auth, text=" ").status_code == 422
    assert translate(client, auth, text="x" * 5001).status_code == 422
    assert translate(client, auth, source_language="xx").status_code == 422
    mock_upstreams[0]["/translate"] = {"translatedText": []}
    assert translate(client, auth).status_code == 502


def test_invalid_and_oversized_uploads(client, login):
    auth = login()
    assert image(client, auth, payload=b"not-an-image").status_code == 400
    assert speech(client, auth, payload=b"not-audio").status_code == 400
    assert image(client, auth, payload=b"x" * (MAX_IMAGE_BYTES + 1)).status_code == 413
    assert speech(client, auth, payload=b"x" * (MAX_AUDIO_BYTES + 1)).status_code == 413
    assert image(client, auth, payload=b"").status_code == 400
    assert speech(client, auth, payload=b"").status_code == 400
    assert image(client, auth, source_language="xx").status_code == 422


def test_image_flow_and_malformed_ocr(client, login, mock_upstreams):
    auth = login()
    result = image(client, auth, store_history="true")
    assert result.status_code == 200, result.text
    assert result.json()["blocks"][0]["bbox"]["x"] == 1
    assert client.get("/history", headers=auth).json()["items"][0]["mode"] == "image"
    mock_upstreams[0]["/capture"] = {"contents": "malformed"}
    assert image(client, auth).status_code == 502
    mock_upstreams[0]["/capture"] = {"text": "", "contents": []}
    assert image(client, auth).status_code == 422


def test_speech_flow_and_empty_transcript(client, login, mock_upstreams):
    auth = login()
    response = speech(client, auth, store_history="true")
    assert response.status_code == 200, response.text
    assert response.json()["detected_language"] == "en"
    assert client.get("/history", headers=auth).json()["items"][0]["mode"] == "speech"
    mock_upstreams[0]["/speech/transcribe"] = {"text": "", "language": "en"}
    assert speech(client, auth).status_code == 422
    mock_upstreams[0]["/speech/transcribe"] = {"text": ["bad"]}
    assert speech(client, auth).status_code == 502


def test_unreachable_services_and_timeouts(client, login, mock_upstreams):
    auth = login()
    mock_upstreams[1]["/translate"] = httpx.ConnectError("private upstream details")
    response = translate(client, auth)
    assert response.status_code == 503
    assert "private" not in response.text
    mock_upstreams[1]["/translate"] = httpx.ReadTimeout("private upstream details")
    assert translate(client, auth).status_code == 504
    mock_upstreams[1].clear()
    mock_upstreams[1]["/capture"] = httpx.ConnectError("private OCR host")
    assert image(client, auth).status_code == 503
    mock_upstreams[1].clear()
    mock_upstreams[1]["/speech/transcribe"] = httpx.ReadTimeout("private speech host")
    assert speech(client, auth).status_code == 504
    mock_upstreams[1].clear()
    mock_upstreams[1]["/translate"] = httpx.Response(500, text="stacktrace secret")
    response = translate(client, auth)
    assert response.status_code == 502
    assert "stacktrace" not in response.text


def test_database_errors_are_sanitized(client):
    def broken_db():
        raise OperationalError("SELECT sensitive", (), Exception("secret: database"))
        yield
    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.post("/signup", json={"email": "yes@example.com", "password": "my-password"})
        assert response.status_code == 503
        assert "secret" not in response.text
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_delete_history_is_user_scoped(client, login):
    alice = login("alice@example.com")
    bob = login("bob@example.com")
    assert translate(client, alice, store_history=True).status_code == 200
    assert translate(client, bob, store_history=True).status_code == 200
    assert client.delete("/history", headers=alice).status_code == 200
    assert client.get("/history", headers=alice).json()["count"] == 0
    assert client.get("/history", headers=bob).json()["count"] == 1
    assert client.delete("/history").status_code == 401


def test_entire_request_size_limit(client):
    oversized = b"x" * (max(MAX_IMAGE_BYTES, MAX_AUDIO_BYTES) + 1024 * 1024 + 1)
    response = client.post("/login", content=oversized,
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 413


def test_chunked_request_limit(client):
    def body():
        for _ in range((MAX_AUDIO_BYTES + 1024 * 1024) // 65536 + 2):
            yield b"x" * 65536
    response = client.post("/login", content=body(),
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 413
