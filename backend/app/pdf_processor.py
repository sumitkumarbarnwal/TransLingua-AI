"""
PDF Processor Module — Converts PDF pages into images for OCR processing.
Uses PyMuPDF (fitz) for high-quality PDF rendering.
"""
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
import io
import logging

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    """
    Convert each page of a PDF to a PIL Image.

    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution for rendering (higher = better OCR but slower)

    Returns:
        List of dicts with page_number and PIL Image
    """
    pages = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        logger.info(f"Processing PDF with {total_pages} pages at {dpi} DPI")

        zoom = dpi / 72  # 72 is the default PDF DPI
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(total_pages):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            pages.append({
                "page_number": page_num + 1,
                "image": image,
                "width": pix.width,
                "height": pix.height,
            })

            logger.info(f"Converted page {page_num + 1}/{total_pages}")

        doc.close()

    except Exception as e:
        logger.error(f"PDF processing failed: {str(e)}")
        raise

    return pages


def get_pdf_info(pdf_path: str) -> dict:
    """
    Get metadata and information about a PDF file.
    """
    try:
        doc = fitz.open(pdf_path)
        info = {
            "total_pages": len(doc),
            "metadata": doc.metadata,
            "page_sizes": [],
        }
        for page in doc:
            rect = page.rect
            info["page_sizes"].append({
                "width": rect.width,
                "height": rect.height,
            })
        doc.close()
        return info
    except Exception as e:
        logger.error(f"Failed to get PDF info: {str(e)}")
        return {"total_pages": 0, "error": str(e)}
