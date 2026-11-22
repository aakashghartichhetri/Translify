import httpx
from app.config import TRANSLATE_SERVICE, SUPPORTED_LANGUAGES
from app.upstream import checked_post, UpstreamError


class TranslationService:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        text = text.strip()
        if not text or len(text) > 5000:
            raise ValueError("Text must contain between 1 and 5000 characters.")
        if source_language not in SUPPORTED_LANGUAGES or target_language not in SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported language.")
        if source_language == target_language:
            return text
        if self.client is None:
            async with httpx.AsyncClient() as client:
                return await TranslationService(client).translate_text(text, source_language, target_language)
        data = await checked_post(
            self.client, "Translation service", f"{TRANSLATE_SERVICE}/translate", timeout=30.0,
            json={"text": text, "sourceLanguage": source_language, "targetLanguage": target_language},
        )
        result = data.get("translatedText")
        if not isinstance(result, str) or not result.strip() or len(result) > 10000:
            raise UpstreamError("Translation service", 502)
        return result.strip()
