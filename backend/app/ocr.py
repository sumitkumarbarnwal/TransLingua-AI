"""
OCR Module — Extracts text from images using Tesseract OCR (primary) or EasyOCR (fallback).
Supports Nepali (Devanagari) and Sinhalese (Sinhala) scripts.
"""
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError as e:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception as e:
    easyocr = None
    EASYOCR_AVAILABLE = False
    print(f"Warning: EasyOCR import failed: {type(e).__name__}: {e}")
    
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import logging
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TESSERACT_CMD, OCR_LANGUAGES

logger = logging.getLogger(__name__)
logger.info(f"OCR Module loaded - Tesseract: {PYTESSERACT_AVAILABLE}, EasyOCR: {EASYOCR_AVAILABLE}")

# Configure Tesseract path
if PYTESSERACT_AVAILABLE and os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Initialize EasyOCR reader (global, loaded once)
_easyocr_readers = {}


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Apply preprocessing to improve OCR accuracy.
    - Convert to grayscale
    - Enhance contrast
    - Apply sharpening
    - Binarize (threshold)
    """
    # Convert to grayscale
    img = image.convert("L")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Sharpen image
    img = img.filter(ImageFilter.SHARPEN)

    # Enhance brightness slightly
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)

    # Apply median filter to reduce noise
    img = img.filter(ImageFilter.MedianFilter(size=3))

    return img


def extract_text_from_image(
    image_path: str,
    language: str = "nepali",
    preprocess: bool = True,
    config_options: str = "--psm 6"
) -> dict:
    """
    Extract text from an image file using Tesseract OCR (primary) or EasyOCR (fallback).

    Args:
        image_path: Path to the image file
        language: Source language ('nepali' or 'sinhalese')
        preprocess: Whether to apply image preprocessing (Tesseract only)
        config_options: Tesseract configuration options

    Returns:
        dict with extracted text, confidence, and metadata
    """
    # Try Tesseract first
    if PYTESSERACT_AVAILABLE:
        logger.info("Attempting OCR with Tesseract...")
        result = extract_text_from_image_tesseract(image_path, language, preprocess, config_options)
        if result["success"]:
            return result
        logger.warning(f"Tesseract OCR failed: {result.get('error')}. Trying EasyOCR fallback...")
    
    # Fallback to EasyOCR
    if EASYOCR_AVAILABLE:
        logger.info("Attempting OCR with EasyOCR...")
        return extract_text_with_easyocr(image_path, language)
    
    # No OCR available
    logger.error("No OCR engine available (install tesseract or easyocr)")
    return {
        "success": False,
        "text": "",
        "language": language,
        "confidence": 0,
        "word_count": 0,
        "words": [],
        "error": "No OCR engine available. Install tesseract or easyocr.",
    }


def extract_text_from_image_tesseract(
    image_path: str,
    language: str = "nepali",
    preprocess: bool = True,
    config_options: str = "--psm 6"
) -> dict:
    """Tesseract OCR extraction."""
    if not PYTESSERACT_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "language": language,
            "confidence": 0,
            "word_count": 0,
            "words": [],
            "error": "Tesseract/pytesseract not installed",
        }
    
    try:
        lang_code = OCR_LANGUAGES.get(language, "nep")
        image = Image.open(image_path)

        original_size = image.size
        original_mode = image.mode

        if preprocess:
            processed_image = preprocess_image(image)
        else:
            processed_image = image

        # Extract text with confidence data
        ocr_data = pytesseract.image_to_data(
            processed_image,
            lang=lang_code,
            config=config_options,
            output_type=pytesseract.Output.DICT
        )

        # Extract plain text
        text = pytesseract.image_to_string(
            processed_image,
            lang=lang_code,
            config=config_options
        ).strip()

        # Calculate average confidence
        confidences = [
            int(c) for c in ocr_data["conf"] if str(c).lstrip("-").isdigit() and int(c) > 0
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Extract word-level data for highlighting
        words = []
        for i in range(len(ocr_data["text"])):
            word = ocr_data["text"][i].strip()
            if word:
                words.append({
                    "text": word,
                    "confidence": int(ocr_data["conf"][i]),
                    "x": ocr_data["left"][i],
                    "y": ocr_data["top"][i],
                    "width": ocr_data["width"][i],
                    "height": ocr_data["height"][i],
                })

        return {
            "success": True,
            "text": text,
            "language": language,
            "confidence": round(avg_confidence, 2),
            "word_count": len(words),
            "words": words,
            "image_info": {
                "size": original_size,
                "mode": original_mode,
            },
        }

    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        return {
            "success": False,
            "text": "",
            "language": language,
            "confidence": 0,
            "word_count": 0,
            "words": [],
            "error": str(e),
        }


def extract_text_with_easyocr(
    image_path: str,
    language: str = "nepali"
) -> dict:
    """
    Extract text from an image using EasyOCR (Python-based, no external dependencies).
    Works on Windows, Mac, and Linux without additional system installations.
    
    Args:
        image_path: Path to the image file
        language: Source language ('nepali' or 'sinhalese')
    
    Returns:
        dict with extracted text and confidence
    """
    if not EASYOCR_AVAILABLE:
        logger.error("EasyOCR not installed. Install with: pip install easyocr")
        return {
            "success": False,
            "text": "",
            "language": language,
            "confidence": 0,
            "word_count": 0,
            "words": [],
            "error": "EasyOCR not installed",
        }
    
    try:
        # Map language to EasyOCR code
        lang_map = {"nepali": "ne", "sinhalese": "si"}
        ocr_lang = lang_map.get(language, "en")
        
        # Initialize reader if not already done
        if ocr_lang not in _easyocr_readers:
            logger.info(f"Loading EasyOCR model for {language}...")
            _easyocr_readers[ocr_lang] = easyocr.Reader([ocr_lang], gpu=False)
        
        reader = _easyocr_readers[ocr_lang]
        
        # Read image
        image = Image.open(image_path)
        
        # Convert PIL to numpy array for EasyOCR
        import numpy as np
        image_array = np.array(image)
        
        # Extract text
        results = reader.readtext(image_array)
        
        # Parse results
        text_lines = []
        words = []
        confidences = []
        
        for (bbox, text, confidence) in results:
            text_lines.append(text)
            confidences.append(confidence)
            
            # Extract bounding box coordinates
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            
            words.append({
                "text": text,
                "confidence": round(confidence * 100, 2),
                "x": int(min(x_coords)),
                "y": int(min(y_coords)),
                "width": int(max(x_coords) - min(x_coords)),
                "height": int(max(y_coords) - min(y_coords)),
            })
        
        full_text = " ".join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "success": True,
            "text": full_text.strip(),
            "language": language,
            "confidence": round(avg_confidence * 100, 2),
            "word_count": len(words),
            "words": words,
            "image_info": {
                "size": image.size,
                "mode": image.mode,
            },
            "method": "easyocr",
        }
    
    except Exception as e:
        logger.error(f"EasyOCR extraction failed: {str(e)}")
        return {
            "success": False,
            "text": "",
            "language": language,
            "confidence": 0,
            "word_count": 0,
            "words": [],
            "error": str(e),
        }


def extract_text_from_pil_image(
    image: Image.Image,
    language: str = "nepali",
    preprocess: bool = True,
    config_options: str = "--psm 6"
) -> dict:
    """
    Extract text from a PIL Image object directly.
    Used when processing PDF pages converted to images.
    """
    if not pytesseract:
        logger.error("Tesseract/pytesseract not installed. Cannot perform OCR.")
        return {
            "success": False,
            "text": "",
            "language": language,
            "confidence": 0,
            "word_count": 0,
            "words": [],
            "error": "Tesseract OCR not installed",
        }
    
    try:
        lang_code = OCR_LANGUAGES.get(language, "nep")

        if preprocess:
            processed_image = preprocess_image(image)
        else:
            processed_image = image

        text = pytesseract.image_to_string(
            processed_image,
            lang=lang_code,
            config=config_options
        ).strip()

        ocr_data = pytesseract.image_to_data(
            processed_image,
            lang=lang_code,
            config=config_options,
            output_type=pytesseract.Output.DICT
        )

        confidences = [
            int(c) for c in ocr_data["conf"] if str(c).lstrip("-").isdigit() and int(c) > 0
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            "success": True,
            "text": text,
            "confidence": round(avg_confidence, 2),
        }

    except Exception as e:
        logger.error(f"PIL OCR extraction failed: {str(e)}")
        return {
            "success": False,
            "text": "",
            "confidence": 0,
            "error": str(e),
        }
