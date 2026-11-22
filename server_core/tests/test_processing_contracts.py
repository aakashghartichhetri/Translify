"""Processing API contract tests without Whisper/TrOCR/NLLB model downloads."""
import importlib.util
import io
import wave
from pathlib import Path
import sys
from types import SimpleNamespace
from fastapi.testclient import TestClient
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_speech_processing_endpoint_is_bounded_and_does_not_use_client_filename(monkeypatch):
    service = load_module("speech_main_test", ROOT / "speechProcessing" / "main.py")
    seen = []

    class FakeWhisper:
        def transcribe(self, path, language):
            seen.append(Path(path))
            assert Path(path).is_file()
            assert "../../" not in path
            return [SimpleNamespace(text="hello there")], SimpleNamespace(language=language)

    monkeypatch.setattr(service, "get_model", lambda: FakeWhisper())
    client = TestClient(service.app)
    assert client.get("/health").status_code == 200
    audio = io.BytesIO()
    with wave.open(audio, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\0\0" * 1600)
    waveform = audio.getvalue()
    response = client.post("/speech/transcribe", data={"language": "en"},
                           files={"file": ("../../unsafe.wav", waveform, "audio/wav")})
    assert response.status_code == 200
    assert response.json()["text"] == "hello there"
    assert len(seen) == 1 and not seen[0].exists()
    assert client.post("/speech/transcribe", data={"language": "en"},
                       files={"file": ("a.wav", b"wrong", "audio/wav")}).status_code == 400
    assert client.post("/speech/transcribe", data={"language": "en"},
                       files={"file": ("a.wav", b"x" * (service.MAX_AUDIO + 1), "audio/wav")}).status_code == 413
    assert client.post("/speech/transcribe", data={"language": "xx"},
                       files={"file": ("a.wav", waveform, "audio/wav")}).status_code == 422


def test_image_service_does_not_retain_snapshot_or_load_model(monkeypatch):
    pytest.importorskip("cv2")
    pytest.importorskip("numpy")
    sys.path.insert(0, str(ROOT / "imageProcessing"))
    try:
        ocr = load_module("ocr_main_test", ROOT / "imageProcessing" / "Trocr.py")
        monkeypatch.setattr(ocr, "run_ocr", lambda raw: ("hello", [{"text": "hello", "bbox": {"x": 1, "y": 1, "w": 2, "h": 2}}]))
        client = TestClient(ocr.app)
        output = io.BytesIO()
        Image.new("RGB", (16, 16)).save(output, "PNG")
        assert client.get("/health").status_code == 200
        assert client.get("/captured_image").status_code == 404
        response = client.post("/capture", files={"image": ("test.png", output.getvalue(), "image/png")})
        assert response.status_code == 200
        assert response.json()["contents"][0]["text"] == "hello"
        assert client.post("/capture", files={"image": ("fake.png", b"not png", "image/png")}).status_code == 400
        assert client.post("/capture", files={"image": ("big.png", b"x" * (ocr.MAX_UPLOAD + 1), "image/png")}).status_code == 413
    finally:
        sys.path.remove(str(ROOT / "imageProcessing"))


def test_translation_engine_contract_without_model_download(monkeypatch):
    service = load_module("translation_main_test", ROOT / "translationEngine" / "main.py")

    class FakeEngine:
        def translate(self, text, source, target):
            return "translated"

    monkeypatch.setattr(service, "get_engine", lambda: FakeEngine())
    client = TestClient(service.app)
    assert client.get("/health").status_code == 200
    good = {"text": "hello", "sourceLanguage": "en", "targetLanguage": "es"}
    assert client.post("/translate", json=good).json()["translatedText"] == "translated"
    assert client.post("/translate", json={**good, "text": ""}).status_code == 422
    assert client.post("/translate", json={**good, "sourceLanguage": "zz"}).status_code == 422
