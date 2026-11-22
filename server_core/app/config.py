"""Fail-closed runtime configuration. Environment files are never loaded implicitly."""
import os
from sqlalchemy.engine import URL


def positive_int(name: str, default: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return value


SECRET_KEY = os.environ.get("SECRET_KEY", "")
if len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("SECRET_KEY must be set to a random secret of at least 32 bytes")

# Do not accept an algorithm chosen from deployment configuration.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = positive_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30, 1440)
SUPPORTED_LANGUAGES = tuple(lang.strip() for lang in os.getenv("SUPPORTED_LANGUAGES", "en,es,fr").split(",") if lang.strip())
ALLOWED_ORIGINS = [s.strip() for s in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if s.strip()]
if "*" in ALLOWED_ORIGINS:
    raise RuntimeError("CORS_ALLOWED_ORIGINS must list explicit trusted origins")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.environ["DATABASE_URL"]
else:
    required = ("DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_NAME", "DATABASE_SOCKET")
    absent = [name for name in required if not os.getenv(name)]
    if absent:
        raise RuntimeError("Database environment variables are missing: " + ", ".join(absent))
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
        database=os.environ["DATABASE_NAME"],
        host=os.environ["DATABASE_SOCKET"],
    )

TRANSLATE_SERVICE = os.getenv("TRANSLATE_SERVICE", "http://127.0.0.1:8003").rstrip("/")
IMAGE_TO_TEXT_SERVICE = os.getenv("IMAGE_TO_TEXT_SERVICE", "http://127.0.0.1:8001").rstrip("/")
SPEECH_TO_TEXT_SERVICE = os.getenv("SPEECH_TO_TEXT_SERVICE", "http://127.0.0.1:8002").rstrip("/")
MAX_IMAGE_BYTES = positive_int("MAX_IMAGE_BYTES", 5 * 1024 * 1024, 20 * 1024 * 1024)
MAX_AUDIO_BYTES = positive_int("MAX_AUDIO_BYTES", 15 * 1024 * 1024, 50 * 1024 * 1024)
