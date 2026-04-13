"""
Main FastAPI Application — Nepali & Sinhalese to English Translation System.

Endpoints:
    POST /api/ocr           — Extract text from uploaded image/PDF
    POST /api/translate      — Translate text to English
    POST /api/pipeline       — Full pipeline: OCR + Translation
    POST /api/feedback       — Submit translation feedback for ML improvement
    GET  /api/status         — System and model status
    GET  /                   — Web interface
"""
import os
import sys
import json
import uuid
import shutil
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    UPLOAD_DIR, FEEDBACK_DIR, FRONTEND_DIR,
    ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, ALLOWED_IMAGE_EXTENSIONS
)
from app.ocr import extract_text_from_image, extract_text_from_pil_image
from app.pdf_processor import pdf_to_images, get_pdf_info
from app.translator import translator
from app.models import (
    TranslationRequest, FeedbackRequest, SourceLanguage
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nepali & Sinhalese → English Translation System",
    description="AI/ML-powered OCR and translation for Nepali and Sinhalese texts",
    version="1.0.0",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def _save_upload(file: UploadFile) -> Path:
    """Save uploaded file and return the path."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / unique_name

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check file size
    file_size_mb = save_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        save_path.unlink()
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size_mb:.1f}MB). Maximum is {MAX_FILE_SIZE_MB}MB."
        )

    return save_path


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main web interface."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


@app.post("/api/ocr")
async def extract_text(
    file: UploadFile = File(...),
    language: str = Form("nepali"),
):
    """
    Extract text from an uploaded image or PDF.
    Supports Nepali (Devanagari) and Sinhalese (Sinhala) scripts.
    """
    save_path = _save_upload(file)

    try:
        ext = save_path.suffix.lower()

        if ext in ALLOWED_IMAGE_EXTENSIONS:
            # Process single image
            result = extract_text_from_image(str(save_path), language=language)
            return {
                "success": result["success"],
                "filename": file.filename,
                "language": language,
                "text": result["text"],
                "confidence": result["confidence"],
                "word_count": result["word_count"],
                "error": result.get("error"),
            }

        elif ext == ".pdf":
            # Process PDF — convert pages to images, then OCR each
            pages = pdf_to_images(str(save_path))
            all_text = []
            total_confidence = 0
            page_results = []

            for page_data in pages:
                page_result = extract_text_from_pil_image(
                    page_data["image"],
                    language=language
                )
                all_text.append(page_result["text"])
                total_confidence += page_result["confidence"]
                page_results.append({
                    "page_number": page_data["page_number"],
                    "text": page_result["text"],
                    "confidence": page_result["confidence"],
                })

            avg_confidence = total_confidence / len(pages) if pages else 0

            return {
                "success": True,
                "filename": file.filename,
                "language": language,
                "text": "\n\n--- Page Break ---\n\n".join(all_text),
                "confidence": round(avg_confidence, 2),
                "word_count": sum(len(t.split()) for t in all_text),
                "total_pages": len(pages),
                "pages": page_results,
            }

    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup uploaded file
        if save_path.exists():
            save_path.unlink()


@app.post("/api/translate")
async def translate_text(request: TranslationRequest):
    """
    Translate Nepali or Sinhalese text to English.
    """
    try:
        result = translator.translate(
            text=request.text,
            language=request.language.value
        )

        return {
            "success": result["success"],
            "source_text": request.text,
            "translated_text": result.get("translated_text", ""),
            "source_language": request.language.value,
            "target_language": "english",
            "method": result.get("method", "unknown"),
            "chunks_processed": result.get("chunks_processed", 0),
            "error": result.get("error"),
        }
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "source_text": request.text,
            "translated_text": "",
            "source_language": request.language.value,
            "target_language": "english",
            "method": "error",
            "error": str(e),
        }


@app.post("/api/pipeline")
async def full_pipeline(
    file: UploadFile = File(...),
    language: str = Form("nepali"),
):
    """
    Full pipeline: Upload image/PDF → OCR extraction → Translation to English.
    Returns both the extracted source text and the English translation.
    """
    save_path = _save_upload(file)

    try:
        ext = save_path.suffix.lower()
        ocr_results = []

        if ext in ALLOWED_IMAGE_EXTENSIONS:
            result = extract_text_from_image(str(save_path), language=language)
            ocr_results.append({
                "page": 1,
                "text": result["text"],
                "confidence": result["confidence"],
            })

        elif ext == ".pdf":
            pages = pdf_to_images(str(save_path))
            for page_data in pages:
                page_result = extract_text_from_pil_image(
                    page_data["image"],
                    language=language
                )
                ocr_results.append({
                    "page": page_data["page_number"],
                    "text": page_result["text"],
                    "confidence": page_result["confidence"],
                })

        # Combine all extracted text
        full_text = "\n".join(r["text"] for r in ocr_results if r["text"])
        avg_confidence = (
            sum(r["confidence"] for r in ocr_results) / len(ocr_results)
            if ocr_results else 0
        )

        # Translate
        translation = translator.translate(text=full_text, language=language)

        return {
            "success": True,
            "filename": file.filename,
            "source_language": language,
            "ocr_result": {
                "text": full_text,
                "confidence": round(avg_confidence, 2),
                "total_pages": len(ocr_results),
                "pages": ocr_results,
            },
            "translation_result": {
                "translated_text": translation["translated_text"],
                "success": translation["success"],
                "error": translation.get("error"),
            },
        }

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if save_path.exists():
            save_path.unlink()


@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit translation feedback for ML improvement.
    Stores human corrections that can be used for model fine-tuning.
    """
    try:
        feedback_data = {
            "id": uuid.uuid4().hex,
            "timestamp": datetime.now().isoformat(),
            "source_language": feedback.source_language.value,
            "source_text": feedback.source_text,
            "machine_translation": feedback.machine_translation,
            "corrected_translation": feedback.corrected_translation,
            "rating": feedback.rating,
        }

        # Save feedback as JSONL (one JSON object per line)
        feedback_file = FEEDBACK_DIR / f"feedback_{feedback.source_language.value}.jsonl"
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")

        logger.info(f"Feedback saved: {feedback_data['id']}")

        return {
            "success": True,
            "message": "Feedback saved successfully. Thank you for helping improve translations!",
            "feedback_id": feedback_data["id"],
        }

    except Exception as e:
        logger.error(f"Failed to save feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def system_status():
    """
    Get system status including model availability and Tesseract configuration.
    """
    # Check Tesseract
    tesseract_available = False
    tesseract_languages = []
    try:
        import pytesseract
        tesseract_languages = pytesseract.get_languages()
        tesseract_available = True
    except Exception:
        pass

    # Check translation models
    model_status = translator.get_model_status()

    # Count feedback entries
    feedback_counts = {}
    for lang in ["nepali", "sinhalese"]:
        feedback_file = FEEDBACK_DIR / f"feedback_{lang}.jsonl"
        if feedback_file.exists():
            with open(feedback_file, "r") as f:
                feedback_counts[lang] = sum(1 for _ in f)
        else:
            feedback_counts[lang] = 0

    return {
        "status": "operational",
        "tesseract": {
            "available": tesseract_available,
            "languages": tesseract_languages,
            "nepali_support": "nep" in tesseract_languages,
            "sinhalese_support": "sin" in tesseract_languages,
        },
        "translation_models": model_status,
        "feedback_entries": feedback_counts,
    }


@app.get("/api/feedback/export/{language}")
async def export_feedback(language: str):
    """Export feedback data for a given language (for model fine-tuning)."""
    feedback_file = FEEDBACK_DIR / f"feedback_{language}.jsonl"
    if not feedback_file.exists():
        return {"entries": [], "count": 0}

    entries = []
    with open(feedback_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    return {"entries": entries, "count": len(entries)}


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT, DEBUG
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
