"""TrOCR service with bounded uploads and no retained images or recognized-text logs."""
import asyncio
from functools import lru_cache
from io import BytesIO
import logging
import os

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
import config

logger = logging.getLogger("translify.ocr")
app = FastAPI()
ocr_semaphore = asyncio.Semaphore(1)
MAX_UPLOAD = 5 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000


@lru_cache(maxsize=1)
def get_model():
    # Lazy initialization permits health checks and unit tests without downloading models.
    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = TrOCRProcessor.from_pretrained(config.MODEL_ID)
    model = VisionEncoderDecoderModel.from_pretrained(config.MODEL_ID).to(device)
    model.eval()
    return processor, model, device, torch


def select_best_channel(bgr):
    best = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    best_score = -1
    for channel in cv2.split(bgr):
        for candidate in (channel, cv2.bitwise_not(channel)):
            _, binary = cv2.threshold(candidate, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            fg, bg = candidate[binary == 255], candidate[binary == 0]
            if len(fg) == 0 or len(bg) == 0:
                continue
            score = abs(float(np.mean(fg)) - float(np.mean(bg)))
            if score > best_score:
                best, best_score = candidate.copy(), score
    _, binary = cv2.threshold(best, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.bitwise_not(best) if (binary == 255).mean() < 0.5 else best


def preprocess_for_ocr(gray, bgr=None):
    if bgr is not None:
        gray = select_best_channel(bgr)
    avg = np.mean(gray)
    if avg < config.GAMMA_VERY_DARK:
        gamma = 0.5
    elif avg < config.GAMMA_DARK:
        gamma = 0.75
    elif avg > config.GAMMA_BRIGHT:
        gamma = 1.5
    else:
        gamma = 1.0
    if gamma != 1.0:
        lookup = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
        gray = cv2.LUT(gray, lookup)
    if bgr is None and np.mean(gray) < config.INVERT_THRESHOLD:
        gray = cv2.bitwise_not(gray)
    return cv2.fastNlMeansDenoising(gray, h=config.DENOISE_H)


def detect_text_regions(gray):
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        config.ADAPTIVE_BLOCK_SIZE, config.ADAPTIVE_C,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (config.H_KERNEL_WIDTH, 1))
    contours, _ = cv2.findContours(cv2.dilate(binary, kernel, iterations=1), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    height, width = gray.shape
    regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < config.MIN_REGION_W or h < config.MIN_REGION_H:
            continue
        if h > height * config.MAX_LINE_HEIGHT_RATIO or (w > width * .95 and h > height * .95):
            continue
        regions.append((x, y, w, h))
    regions.sort(key=lambda box: (box[1], box[0]))
    return regions[:200]


def merge_regions_into_lines(regions):
    lines, used = [], [False] * len(regions)
    for i, region in enumerate(regions):
        if used[i]:
            continue
        group = [region]
        used[i] = True
        for j in range(i + 1, len(regions)):
            if used[j]:
                continue
            candidate = regions[j]
            if any(
                max(0, min(g[1] + g[3], candidate[1] + candidate[3]) - max(g[1], candidate[1])) /
                max(1, min(g[3], candidate[3])) >= config.VERTICAL_OVERLAP_THRESH
                for g in group
            ):
                group.append(candidate)
                used[j] = True
        x = min(g[0] for g in group)
        y = min(g[1] for g in group)
        right = max(g[0] + g[2] for g in group)
        bottom = max(g[1] + g[3] for g in group)
        lines.append((x, y, right - x, bottom - y))
    return sorted(lines, key=lambda box: (box[1], box[0]))[:40]


def recognize_crop(crop):
    if min(crop.shape[:2]) < config.MIN_CROP_PX:
        return ""
    processor, model, device, torch = get_model()
    image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    pixels = processor(images=image, return_tensors="pt").pixel_values.to(device)
    with torch.no_grad():
        result = model.generate(
            pixels, num_beams=config.NUM_BEAMS, max_new_tokens=config.MAX_NEW_TOKENS,
            output_scores=True, return_dict_in_generate=True,
        )
    if result.sequences_scores[0].item() < config.MIN_CONFIDENCE:
        return ""
    return processor.batch_decode(result.sequences, skip_special_tokens=True)[0].strip()


def run_ocr(image_bytes):
    frame = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Invalid image")
    height, width = frame.shape[:2]
    scale = config.UPSCALE_MIN_WIDTH / width if width < config.UPSCALE_MIN_WIDTH else 1.0
    scaled = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC) if scale > 1 else frame
    gray = preprocess_for_ocr(cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY), bgr=scaled)
    regions = merge_regions_into_lines(detect_text_regions(gray))
    contents = []
    for sx, sy, sw, sh in regions:
        crop = scaled[sy:sy + sh, sx:sx + sw]
        if not crop.size:
            continue
        line = recognize_crop(crop)
        if not line:
            continue
        ox, oy, ow, oh = [int(v / scale) for v in (sx, sy, sw, sh)]
        bx, by = max(ox - 4, 0), max(oy - 4, 0)
        bx2, by2 = min(ox + ow + 4, width), min(oy + oh + 4, height)
        contents.append({"text": line, "bbox": {"x": bx, "y": by, "w": bx2 - bx, "h": by2 - by}})
    return "\n".join(item["text"] for item in contents), contents


async def read_limited(file):
    data = bytearray()
    while True:
        chunk = await file.read(min(65536, MAX_UPLOAD + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_UPLOAD:
            raise HTTPException(status_code=413, detail="Image too large")
    if not data:
        raise HTTPException(status_code=400, detail="Image is empty")
    return bytes(data)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/capture")
async def capture(image: UploadFile = File(...)):
    try:
        data = await read_limited(image)
        try:
            with Image.open(BytesIO(data)) as picture:
                if picture.format not in {"JPEG", "PNG"} or picture.width * picture.height > 20_000_000:
                    raise ValueError("Invalid image")
                picture.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise HTTPException(status_code=400, detail="Upload a valid JPEG or PNG image") from None
        async with ocr_semaphore:
            try:
                text, contents = await run_in_threadpool(run_ocr, data)
            except Exception as exc:
                logger.error("ocr_processing_failed type=%s", type(exc).__name__)
                raise HTTPException(status_code=503, detail="OCR temporarily unavailable") from None
        return {"text": text, "contents": contents}
    finally:
        await image.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
