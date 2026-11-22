"""Bounded, serialized access to the shared NLLB model."""
import asyncio
from functools import lru_cache
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

logger = logging.getLogger("translify.translation")
app = FastAPI()
model_semaphore = asyncio.Semaphore(1)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    sourceLanguage: str = Field(pattern="^(en|es|fr)$")
    targetLanguage: str = Field(pattern="^(en|es|fr)$")


class TranslationResponse(BaseModel):
    translatedText: str


@lru_cache(maxsize=1)
def get_engine():
    from translationEngine import TranslationEngine
    return TranslationEngine(modelName="facebook/nllb-200-distilled-600M")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    async with model_semaphore:
        try:
            result = await run_in_threadpool(
                get_engine().translate, request.text,
                request.sourceLanguage, request.targetLanguage,
            )
        except ValueError:
            raise HTTPException(status_code=422, detail="Unsupported language or input") from None
        except Exception as exc:
            logger.error("translation_processing_failed type=%s", type(exc).__name__)
            raise HTTPException(status_code=503, detail="Translation engine temporarily unavailable") from None
    if not isinstance(result, str) or not result.strip():
        raise HTTPException(status_code=503, detail="Translation engine returned no text")
    return TranslationResponse(translatedText=result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
