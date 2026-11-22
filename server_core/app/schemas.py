from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.config import SUPPORTED_LANGUAGES


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LanguageFields(BaseModel):
    source_language: str = Field(min_length=2, max_length=10)
    target_language: str = Field(min_length=2, max_length=10)

    @field_validator("source_language", "target_language")
    @classmethod
    def supported(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported language")
        return value


class TranslationRequest(LanguageFields):
    text: str = Field(min_length=1, max_length=5000)
    mode: Literal["text"] = "text"
    store_history: bool = False


class TranslationResponse(LanguageFields):
    original_text: str
    translated_text: str
    mode: str = "text"


class OCRBlock(BaseModel):
    text: str = Field(max_length=5000)
    bbox: dict[str, int] | None = None


class OCRResult(BaseModel):
    text: str = Field(default="", max_length=5000)
    contents: list[OCRBlock] = Field(default_factory=list, max_length=40)


class SpeechResult(BaseModel):
    text: str = Field(max_length=5000)
    language: str | None = Field(default=None, max_length=20)
