"""Local demonstration-only AI contracts.

These endpoints intentionally do NOT recognize audio/images or translate text.
Never deploy this service as a translation engine or use for accuracy evaluation.
"""
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Translify development fixtures")

class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    sourceLanguage: str
    targetLanguage: str

@app.get('/health')
def health():
    return {"status": "ok", "mode": "demo-fixture-no-real-ai"}

@app.post('/translate')
def translate(request: TranslationRequest):
    if request.sourceLanguage not in {"en", "es", "fr"} or request.targetLanguage not in {"en", "es", "fr"}:
        raise HTTPException(status_code=422,detail="Unsupported demo language")
    return {"translatedText": f"[DEMO — NOT TRANSLATED] {request.text}"}

@app.post('/capture')
async def capture(image: UploadFile = File(...)):
    # The gateway already validates the original media file. No image processing here.
    if not await image.read(1):
        raise HTTPException(status_code=400,detail="Empty image")
    text = "Demo image text (no OCR performed)"
    return {"text": text, "contents": [{"text": text, "bbox": {"x": 0, "y": 0, "w": 50, "h": 20}}]}

@app.post('/speech/transcribe')
async def transcribe(file: UploadFile = File(...), language: str = Form(...)):
    if language not in {"en","es","fr"}:
        raise HTTPException(status_code=422,detail="Unsupported demo language")
    if not await file.read(1):
        raise HTTPException(status_code=400,detail="Empty audio")
    return {"text": "Demo speech transcript (no recognition performed)", "language": language}
