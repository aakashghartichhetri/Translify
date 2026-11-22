# PR 3 — security: remove OCR snapshots and isolate speech temporary files

**Head:** `security/processing-services`  
**Base:** `security/backend-boundaries`

**Problem / evidence:** The TrOCR implementation persisted a user's annotated photo and served `/captured_image`; recognition text was printed. The speech worker constructed a disk path directly from the client filename, risking path injection and leftover recordings on errors. Models loaded at import time.

**Solution / reasoning:** Stop tracking the generated `captured_frame.jpg` without deleting the local file. Use no saved OCR image or cross-user snapshot endpoint; redact recognition-content logs. Introduce bounded uploads, strict file-type checks, serialized model inference, lazy initialization, health endpoints, random speech temporary filenames with guaranteed cleanup, and non-root Docker users. The translation service now validates requests and handles model failures safely.

**Tests:** Model-free endpoint tests (included in the following test branch) passed locally. Docker builds, TrOCR/faster-whisper/NLLB inference, and quality benchmarking remain unverified.

**Risks / follow-up:** The recognition preprocessing is refactored and requires real-image regression checks. MP3/M4A require `ffprobe` (installed by speech Dockerfile); cold-start loading, GPU support, input abuse, ingress exposure and model concurrency need live deployment verification.
