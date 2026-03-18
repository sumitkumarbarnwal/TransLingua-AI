"""
Translation Module — Translates Nepali and Sinhalese text to English
using pre-trained MarianMT neural machine translation models from HuggingFace.

Models are downloaded once and cached locally for offline use.
"""
from transformers import MarianMTModel, MarianTokenizer
from pathlib import Path
import logging
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TRANSLATION_MODELS, MODELS_DIR

logger = logging.getLogger(__name__)


class TranslationEngine:
    """
    Neural Machine Translation engine using MarianMT models.
    Supports Nepali → English and Sinhalese → English translation.
    Models are cached locally for offline operation.
    """

    def __init__(self):
        self._models = {}
        self._tokenizers = {}
        self._loaded = set()

    def _get_cache_dir(self, language: str) -> Path:
        """Get the local cache directory for a model."""
        return MODELS_DIR / language

    def load_model(self, language: str) -> bool:
        """
        Load a translation model and tokenizer for the given language.
        Downloads from HuggingFace if not cached locally.

        Args:
            language: 'nepali' or 'sinhalese'

        Returns:
            True if model loaded successfully
        """
        if language in self._loaded:
            return True

        model_name = TRANSLATION_MODELS.get(language)
        if not model_name:
            logger.error(f"No translation model configured for: {language}")
            return False

        cache_dir = self._get_cache_dir(language)
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Loading translation model for {language}: {model_name}")

            # Try loading from local cache first
            local_model_path = cache_dir / "model"
            if local_model_path.exists():
                logger.info(f"Loading from local cache: {local_model_path}")
                self._tokenizers[language] = MarianTokenizer.from_pretrained(
                    str(local_model_path)
                )
                self._models[language] = MarianMTModel.from_pretrained(
                    str(local_model_path)
                )
            else:
                logger.info(f"Downloading model from HuggingFace: {model_name}")
                self._tokenizers[language] = MarianTokenizer.from_pretrained(model_name)
                self._models[language] = MarianMTModel.from_pretrained(model_name)

                # Save locally for offline use
                logger.info(f"Caching model locally at: {local_model_path}")
                self._tokenizers[language].save_pretrained(str(local_model_path))
                self._models[language].save_pretrained(str(local_model_path))

            self._loaded.add(language)
            logger.info(f"Model loaded successfully for {language}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model for {language}: {str(e)}")
            return False

    def translate(
        self,
        text: str,
        language: str = "nepali",
        max_length: int = 512
    ) -> dict:
        """
        Translate text from Nepali or Sinhalese to English.

        Args:
            text: Source text to translate
            language: Source language ('nepali' or 'sinhalese')
            max_length: Maximum output token length

        Returns:
            dict with translated text and metadata
        """
        if not text or not text.strip():
            return {
                "success": True,
                "translated_text": "",
                "source_language": language,
                "target_language": "english",
            }

        # Ensure model is loaded
        if not self.load_model(language):
            return {
                "success": False,
                "translated_text": "",
                "source_language": language,
                "target_language": "english",
                "error": f"Translation model not available for {language}. "
                         f"Please ensure internet connection for first-time model download.",
            }

        try:
            tokenizer = self._tokenizers[language]
            model = self._models[language]

            # Split text into manageable chunks (sentences/paragraphs)
            chunks = self._split_text(text)
            translated_chunks = []

            for chunk in chunks:
                if not chunk.strip():
                    translated_chunks.append("")
                    continue

                # Tokenize
                inputs = tokenizer(
                    chunk,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=max_length
                )

                # Generate translation
                translated_ids = model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=4,
                    length_penalty=0.6,
                    early_stopping=True
                )

                # Decode
                translated = tokenizer.decode(
                    translated_ids[0],
                    skip_special_tokens=True
                )
                translated_chunks.append(translated)

            full_translation = "\n".join(translated_chunks)

            return {
                "success": True,
                "translated_text": full_translation,
                "source_language": language,
                "target_language": "english",
                "chunks_processed": len(chunks),
            }

        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return {
                "success": False,
                "translated_text": "",
                "source_language": language,
                "target_language": "english",
                "error": str(e),
            }

    def _split_text(self, text: str, max_chars: int = 400) -> list:
        """
        Split text into chunks suitable for translation.
        Tries to split on paragraph boundaries, then sentence boundaries.
        """
        # First split by paragraphs
        paragraphs = text.split("\n")
        chunks = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                chunks.append("")
                continue

            if len(para) <= max_chars:
                chunks.append(para)
            else:
                # Split long paragraphs into sentences
                sentences = re.split(r'(?<=[।\.\?\!])\s+', para)
                current_chunk = ""

                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_chars:
                        current_chunk += (" " if current_chunk else "") + sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence

                if current_chunk:
                    chunks.append(current_chunk)

        return chunks

    def get_model_status(self) -> dict:
        """Get the status of loaded models."""
        status = {}
        for lang, model_name in TRANSLATION_MODELS.items():
            cache_dir = self._get_cache_dir(lang)
            local_model_path = cache_dir / "model"
            status[lang] = {
                "model_name": model_name,
                "loaded": lang in self._loaded,
                "cached_locally": local_model_path.exists(),
            }
        return status


# Singleton instance
translator = TranslationEngine()
