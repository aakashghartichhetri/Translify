"""Legacy entrypoint retained for compatibility; uses the privacy-safe TrOCR API.

The old implementation persisted recognized images and exposed /captured_image.
"""
from Trocr import app, capture, run_ocr  # noqa: F401
