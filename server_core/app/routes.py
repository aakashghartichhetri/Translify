"""Authentication and translation routes. No request bodies or upstream errors in logs."""
from io import BytesIO
import wave
import logging
import httpx
import jwt
from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.auth_service import AuthService
from app.config import (
    ALGORITHM, SECRET_KEY, TRANSLATE_SERVICE, IMAGE_TO_TEXT_SERVICE,
    SPEECH_TO_TEXT_SERVICE, MAX_AUDIO_BYTES, MAX_IMAGE_BYTES,
)
from app.database import get_db
from app.models import TranslationHistory, User
from app.schemas import (
    SignUpRequest, TokenResponse, TranslationRequest, TranslationResponse,
    UserResponse, LanguageFields, OCRResult, SpeechResult,
)
from app.translate_service import TranslationService
from app.upstream import checked_post, UpstreamError

router = APIRouter()
auth_service = AuthService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
logger = logging.getLogger("translify")


async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client


def get_translation_service(client: httpx.AsyncClient = Depends(get_http_client)):
    return TranslationService(client)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    error = HTTPException(
        status_code=401, detail="Invalid authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
        email = payload.get("sub")
        if not isinstance(email, str) or not email:
            raise error
    except jwt.PyJWTError:
        raise error from None
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise error
    return user


def save_history(db: Session, *, user_id: int, original_text: str, translated_text: str,
                 source_language: str, target_language: str, mode: str, store_history: bool):
    if not store_history:
        return
    try:
        db.add(TranslationHistory(
            user_id=user_id, original_text=original_text,
            translated_text=translated_text, source_language=source_language,
            target_language=target_language, mode=mode, store_history=True,
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise


def validate_languages(source_language: str, target_language: str):
    try:
        LanguageFields(source_language=source_language, target_language=target_language)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Select two supported languages.") from None


async def limited_file(file: UploadFile, max_bytes: int) -> bytes:
    if file.size is not None and file.size > max_bytes:
        raise HTTPException(status_code=413, detail="File is too large.")
    chunks = bytearray()
    while True:
        chunk = await file.read(min(65536, max_bytes + 1 - len(chunks)))
        if not chunk:
            break
        chunks.extend(chunk)
        if len(chunks) > max_bytes:
            raise HTTPException(status_code=413, detail="File is too large.")
    if not chunks:
        raise HTTPException(status_code=400, detail="File is empty.")
    return bytes(chunks)


def validate_image(data: bytes):
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Only JPEG and PNG images are allowed.")
            if image.width * image.height > 20_000_000:
                raise ValueError("Image dimensions are too large.")
            media_type = "image/jpeg" if image.format == "JPEG" else "image/png"
            image.verify()
            return media_type
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Upload a valid JPEG or PNG image of at most 20 megapixels.") from None


def validate_audio(data: bytes) -> str:
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            with wave.open(BytesIO(data), "rb") as reader:
                if (reader.getnchannels() not in (1, 2) or
                    not 8000 <= reader.getframerate() <= 96000 or
                    reader.getnframes() == 0 or
                    reader.getnframes() / reader.getframerate() > 120):
                    raise ValueError("Unsupported WAV recording")
        except (wave.Error, EOFError, ValueError):
            raise HTTPException(status_code=400, detail="Upload a valid WAV recording up to 2 minutes.") from None
        return "audio/wav"
    if data[:3] == b"ID3" or (len(data) >= 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return "audio/mpeg"
    if len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in {b"M4A ", b"isom", b"mp42", b"mp41"}:
        return "audio/mp4"
    raise HTTPException(status_code=400, detail="Upload a valid WAV, MP3, or M4A audio file.")


@router.get("/services/health")
async def services_health(client: httpx.AsyncClient = Depends(get_http_client)):
    statuses = {}
    for name, url in (
        ("translation", TRANSLATE_SERVICE), ("ocr", IMAGE_TO_TEXT_SERVICE),
        ("speech", SPEECH_TO_TEXT_SERVICE),
    ):
        try:
            response = await client.get(f"{url}/health", timeout=3.0)
            statuses[name] = "healthy" if response.status_code == 200 else "unhealthy"
        except httpx.RequestError:
            statuses[name] = "unreachable"
    return {"server_core": "healthy", "services": statuses}


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.create_user(db, request.email, request.password)
    except ValueError:
        raise HTTPException(status_code=409, detail="Email already registered.") from None


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password.",
                            headers={"WWW-Authenticate": "Bearer"})
    return TokenResponse(access_token=auth_service.create_access_token(user.email))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/history")
def get_translation_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = (
        db.query(TranslationHistory)
        .filter(TranslationHistory.user_id == current_user.id)
        .order_by(TranslationHistory.created_at.desc(), TranslationHistory.id.desc())
        .limit(50).all()
    )
    return {"count": len(history), "items": [
        {"id": item.id, "original_text": item.original_text,
         "translated_text": item.translated_text, "source_language": item.source_language,
         "target_language": item.target_language, "mode": item.mode,
         "created_at": item.created_at} for item in history
    ]}


@router.delete("/history")
def delete_translation_history(db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    try:
        db.query(TranslationHistory).filter(TranslationHistory.user_id == current_user.id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    logger.info("history_deleted user_id=%d", current_user.id)
    return {"status": "deleted"}


@router.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    service: TranslationService = Depends(get_translation_service)):
    try:
        translated = await service.translate_text(request.text, request.source_language, request.target_language)
    except ValueError:
        raise HTTPException(status_code=422, detail="Provide valid text and supported languages.") from None
    save_history(db, user_id=current_user.id, original_text=request.text,
                 translated_text=translated, source_language=request.source_language,
                 target_language=request.target_language, mode="text", store_history=request.store_history)
    logger.info("translation_completed mode=text stored=%s", request.store_history)
    return TranslationResponse(original_text=request.text, translated_text=translated,
                               source_language=request.source_language, target_language=request.target_language)


@router.post("/translate/image-to-text")
async def translate_image_to_text(source_language: str = Form(...), target_language: str = Form(...),
                                  image: UploadFile = File(...), store_history: bool = Form(False),
                                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
                                  client: httpx.AsyncClient = Depends(get_http_client),
                                  service: TranslationService = Depends(get_translation_service)):
    validate_languages(source_language, target_language)
    try:
        raw = await limited_file(image, MAX_IMAGE_BYTES)
        mime = validate_image(raw)
    finally:
        await image.close()
    payload = await checked_post(
        client, "OCR service", f"{IMAGE_TO_TEXT_SERVICE}/capture", timeout=45.0,
        files={"image": ("upload.jpg" if mime == "image/jpeg" else "upload.png", raw, mime)},
    )
    try:
        result = OCRResult.model_validate(payload)
    except ValidationError:
        raise UpstreamError("OCR service") from None
    blocks = []
    if result.contents:
        for item in result.contents:
            text = item.text.strip()
            if not text:
                continue
            translated = await service.translate_text(text, source_language, target_language)
            blocks.append({"original_text": text, "translated_text": translated, "bbox": item.bbox})
    elif result.text.strip():
        text = result.text.strip()
        translated = await service.translate_text(text, source_language, target_language)
        blocks.append({"original_text": text, "translated_text": translated, "bbox": None})
    if not blocks:
        raise HTTPException(status_code=422, detail="No readable text was found in the image.")
    original = " ".join(block["original_text"] for block in blocks)
    translated = " ".join(block["translated_text"] for block in blocks)
    save_history(db, user_id=current_user.id, original_text=original,
                 translated_text=translated, source_language=source_language,
                 target_language=target_language, mode="image", store_history=store_history)
    logger.info("translation_completed mode=image stored=%s", store_history)
    return {"mode": "image", "source_language": source_language, "target_language": target_language,
            "original_text": original, "translated_text": translated, "blocks": blocks}


@router.post("/translate/speech-to-text")
async def translate_speech_to_text(source_language: str = Form(...), target_language: str = Form(...),
                                   recording: UploadFile = File(...), store_history: bool = Form(False),
                                   db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
                                   client: httpx.AsyncClient = Depends(get_http_client),
                                   service: TranslationService = Depends(get_translation_service)):
    validate_languages(source_language, target_language)
    try:
        raw = await limited_file(recording, MAX_AUDIO_BYTES)
        mime = validate_audio(raw)
    finally:
        await recording.close()
    payload = await checked_post(
        client, "Speech service", f"{SPEECH_TO_TEXT_SERVICE}/speech/transcribe", timeout=90.0,
        files={"file": ("recording", raw, mime)}, data={"language": source_language},
    )
    try:
        speech = SpeechResult.model_validate(payload)
    except ValidationError:
        raise UpstreamError("Speech service") from None
    original = speech.text.strip()
    if not original:
        raise HTTPException(status_code=422, detail="No speech was detected. Please record again.")
    translated = await service.translate_text(original, source_language, target_language)
    save_history(db, user_id=current_user.id, original_text=original,
                 translated_text=translated, source_language=source_language,
                 target_language=target_language, mode="speech", store_history=store_history)
    logger.info("translation_completed mode=speech stored=%s", store_history)
    return {"mode": "speech", "source_language": source_language, "target_language": target_language,
            "detected_language": speech.language, "original_text": original,
            "translated_text": translated}
