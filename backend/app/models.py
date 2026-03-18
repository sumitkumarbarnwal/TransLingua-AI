"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class SourceLanguage(str, Enum):
    NEPALI = "nepali"
    SINHALESE = "sinhalese"


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Source text to translate")
    language: SourceLanguage = Field(..., description="Source language")


class TranslationResponse(BaseModel):
    success: bool
    source_text: str
    translated_text: str
    source_language: str
    target_language: str = "english"
    confidence: Optional[float] = None
    error: Optional[str] = None


class OCRResponse(BaseModel):
    success: bool
    text: str
    language: str
    confidence: float
    word_count: int
    error: Optional[str] = None


class FullPipelineResponse(BaseModel):
    success: bool
    filename: str
    source_language: str
    ocr_result: dict
    translation_result: dict
    pages: Optional[List[dict]] = None
    error: Optional[str] = None


class FeedbackRequest(BaseModel):
    source_text: str = Field(..., description="Original source text")
    machine_translation: str = Field(..., description="Machine-generated translation")
    corrected_translation: str = Field(..., description="Human-corrected translation")
    source_language: SourceLanguage = Field(..., description="Source language")
    rating: int = Field(ge=1, le=5, description="Quality rating 1-5")


class ModelStatusResponse(BaseModel):
    models: dict
    tesseract_available: bool
    tesseract_languages: list
