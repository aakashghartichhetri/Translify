"""Service tests use disposable SQLite and mocked upstream HTTP; no model downloads."""
import os
import tempfile
from pathlib import Path

_tmp = tempfile.TemporaryDirectory(prefix="translify-tests-")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{Path(_tmp.name) / 'test.db'}"
os.environ["SECRET_KEY"] = "unit-test-only-not-for-deployment-key-12345678901234567890"
os.environ["CORS_ALLOWED_ORIGINS"] = "https://trusted.example"

import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routes import get_http_client
from app.database import Base, engine
from app import models  # noqa: F401


@pytest.fixture
def mock_upstreams():
    responses = {"/translate": {"translatedText": "hello translated"},
                 "/capture": {"text": "hello", "contents": [{"text": "hello", "bbox": {"x": 1, "y": 2, "w": 3, "h": 4}}]},
                 "/speech/transcribe": {"text": "hello", "language": "en"}}
    failures = {}

    def handler(request: httpx.Request):
        if request.url.path in failures:
            failure = failures[request.url.path]
            if isinstance(failure, Exception):
                raise failure
            return failure
        return httpx.Response(200, json=responses.get(request.url.path, {}))

    async def mock_http_client():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            yield client

    app.dependency_overrides[get_http_client] = mock_http_client
    yield responses, failures
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_upstreams):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login(client):
    def _login(email="user@example.com", password="correct-password-123"):
        signup = client.post("/signup", json={"email": email, "password": password})
        assert signup.status_code == 201, signup.text
        auth = client.post("/login", data={"username": email, "password": password})
        assert auth.status_code == 200, auth.text
        return {"Authorization": f"Bearer {auth.json()['access_token']}"}
    return _login
