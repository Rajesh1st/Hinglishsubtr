#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FASTAPI APP - SRT HINGLISH TRANSLATOR
----------------------------------------
Swagger UI testing ke liye: http://<your-vps-ip>:8000/docs
Wahan se .srt file upload karo, translated file wapas download hogi.

RUN:
    uvicorn main:app --host 0.0.0.0 --port 8000

Bot bhi isi API ko call kar sakta hai POST /translate-upload pe
(multipart file upload), taaki heavy translation logic bot ke andar
duplicate na karna pade.
"""

import os
import tempfile
import uuid

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse

from translator import AnythingTranslateHinglish, translate_srt_content

app = FastAPI(
    title="SRT Hinglish Translator API",
    version="1.0.0",
    description=(
        "Upload a .srt subtitle file and get it back translated to Hinglish "
        "(Roman-script Hindi), using anythingtranslate.com's Hinglish engine "
        "with character-based batching + automatic per-line fallback."
    ),
)


@app.get("/health")
def health():
    """Simple health check."""
    return {"ok": True}


@app.post("/translate-upload", summary="Upload an .srt file and get it translated")
async def translate_upload(
    file: UploadFile = File(..., description="The .srt subtitle file to translate"),
    batch_chars: int = Query(450, ge=50, le=2000,
                              description="Max characters per translation batch"),
    delay: float = Query(0.5, ge=0.0, le=5.0,
                          description="Delay (seconds) between requests, raise if rate-limited"),
):
    if not file.filename.lower().endswith(".srt"):
        raise HTTPException(status_code=400, detail="Only .srt files are allowed")

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("latin-1", errors="ignore")

    translator = AnythingTranslateHinglish()
    out_content, stats = translate_srt_content(
        content, translator, batch_chars=batch_chars, delay=delay
    )

    tmpdir = tempfile.gettempdir()
    base_name = os.path.splitext(os.path.basename(file.filename))[0]
    out_filename = f"{base_name}-hinglish.srt"
    out_path = os.path.join(tmpdir, f"{uuid.uuid4().hex[:8]}-{out_filename}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_content)

    # Stats attached as response headers so bot/Swagger can see them too
    headers = {
        "X-Total-Batches": str(stats["total_batches"]),
        "X-Batch-Success": str(stats["batch_success"]),
        "X-Batch-Fallback": str(stats["batch_fallback"]),
        "X-Line-Fail": str(stats["line_fail"]),
    }

    return FileResponse(
        out_path,
        media_type="application/x-subrip",
        filename=out_filename,
        headers=headers,
    )


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "SRT Hinglish Translator API",
        "docs": "/docs",
        "endpoints": [
            "GET /health",
            "POST /translate-upload  (multipart file upload, query params: batch_chars, delay)",
        ],
    }
