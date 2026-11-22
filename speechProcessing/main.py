"""Speech transcription API: bounded inputs, safe temporary files, no model preload in tests."""
import asyncio
from io import BytesIO
import subprocess
import wave
from functools import lru_cache
import logging
import os
from pathlib import Path
import tempfile
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

app = FastAPI()
logger = logging.getLogger("translify.speech")
MAX_AUDIO = 15 * 1024 * 1024
MAX_AUDIO_SECONDS = 120
transcription_semaphore = asyncio.Semaphore(1)
ALLOWED_LANGUAGES = {"en", "es", "fr"}


@lru_cache(maxsize=1)
def get_model():
    from faster_whisper import WhisperModel
    return WhisperModel("base", device="cpu", compute_type="int8")


class InvalidAudio(Exception):
    pass


def audio_format(data):
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            with wave.open(BytesIO(data), "rb") as recording:
                if (recording.getnchannels() not in (1, 2) or
                    not 8000 <= recording.getframerate() <= 96000 or
                    recording.getnframes() == 0 or
                    recording.getnframes() / recording.getframerate() > MAX_AUDIO_SECONDS):
                    raise wave.Error("Unsupported audio recording")
        except (wave.Error, EOFError):
            raise HTTPException(status_code=400, detail="Upload a valid WAV recording up to 2 minutes") from None
        return ".wav"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return ".mp3"
    if data[4:8] == b"ftyp" and data[8:12] in {b"M4A ", b"isom", b"mp42", b"mp41"}:
        return ".m4a"
    raise HTTPException(status_code=400, detail="Upload valid WAV, MP3, or M4A audio")


def transcribe_bytes(data, language, suffix):
    # The client filename never becomes part of a filesystem path.
    fd, path = tempfile.mkstemp(prefix="translify-speech-", suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as temp:
            temp.write(data)
        if suffix in (".mp3", ".m4a"):
            try:
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", path],
                    capture_output=True, text=True, timeout=5, check=True,
                )
                duration = float(probe.stdout.strip())
                if not 0 < duration <= MAX_AUDIO_SECONDS:
                    raise InvalidAudio()
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
                raise InvalidAudio() from None
        segments, info = get_model().transcribe(path, language=language)
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        return {"text": text[:5000], "language": info.language}
    finally:
        Path(path).unlink(missing_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/speech/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = Form(...)):
    if language not in ALLOWED_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported speech language")
    data = bytearray()
    try:
        while True:
            chunk = await file.read(min(65536, MAX_AUDIO + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > MAX_AUDIO:
                raise HTTPException(status_code=413, detail="Audio too large")
    finally:
        await file.close()
    if not data:
        raise HTTPException(status_code=400, detail="Audio is empty")
    suffix = audio_format(data)
    async with transcription_semaphore:
        try:
            return await run_in_threadpool(transcribe_bytes, bytes(data), language, suffix)
        except InvalidAudio:
            raise HTTPException(status_code=400, detail="Audio is invalid or longer than 2 minutes") from None
        except Exception as exc:
            logger.error("speech_processing_failed type=%s", type(exc).__name__)
            raise HTTPException(status_code=503, detail="Speech recognition temporarily unavailable") from None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
