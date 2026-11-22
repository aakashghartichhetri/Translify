"""API setup: startup is side-effect free; run migrations separately."""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.config import ALLOWED_ORIGINS, MAX_AUDIO_BYTES, MAX_IMAGE_BYTES
from app.body_limit import BodyLimitMiddleware
from app.routes import router
from app.upstream import UpstreamError

logger = logging.getLogger("translify")
app = FastAPI(title="Translify Server", version="0.2.0")
app.add_middleware(BodyLimitMiddleware, max_bytes=max(MAX_AUDIO_BYTES, MAX_IMAGE_BYTES) + 1024 * 1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(UpstreamError)
async def handle_upstream_error(request: Request, exc: UpstreamError):
    logger.warning("upstream_failure service=%s code=%d", exc.service, exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def handle_database_error(request: Request, exc: SQLAlchemyError):
    logger.error("database_failure type=%s", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable. Please try again."})


app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
