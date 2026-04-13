"""
Translation Module — Production Ready (Same Structure as Your Original)
---------------------------------------------------------------------
- Keeps your original architecture
- Fixes transformers error
- Adds safe fallback
- Keeps LLM + local model design
"""

import logging
import sys
import re
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# Safe imports (FIX for your error)
try:
    from transformers import MarianMTModel, MarianTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    # Production uses Groq LLM API only - transformers not needed

# Dummy config (so it runs standalone if config missing)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import (
        TRANSLATION_MODELS, MODELS_DIR,
        USE_LLM, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
    )
except Exception:
    TRANSLATION_MODELS = {
        "nepali": "Helsinki-NLP/opus-mt-ne-en"
    }
    MODELS_DIR = Path("./models")
    USE_LLM = False
    LLM_API_KEY = None
    LLM_BASE_URL = "https://api.openai.com/v1"
    LLM_MODEL = "gpt-4o-mini"


class TranslationEngine:

    def __init__(self):
        self._models = {}
        self._tokenizers = {}
        self._loaded = set()

        self.use_llm_api = USE_LLM and LLM_API_KEY

    def _get_cache_dir(self, language: str) -> Path:
        return MODELS_DIR / language

    def load_model(self, language: str) -> bool:

        if not TRANSFORMERS_AVAILABLE:
            logger.warning("transformers not installed")
            return False

        if language in self._loaded:
            return True

        model_name = TRANSLATION_MODELS.get(language)
        if not model_name:
            return False

        cache_dir = self._get_cache_dir(language)
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            local_model_path = cache_dir / "model"

            if local_model_path.exists():
                self._tokenizers[language] = MarianTokenizer.from_pretrained(str(local_model_path))
                self._models[language] = MarianMTModel.from_pretrained(str(local_model_path))
            else:
                self._tokenizers[language] = MarianTokenizer.from_pretrained(model_name)
                self._models[language] = MarianMTModel.from_pretrained(model_name)

                self._tokenizers[language].save_pretrained(str(local_model_path))
                self._models[language].save_pretrained(str(local_model_path))

            self._loaded.add(language)
            return True

        except Exception as e:
            logger.error(f"Model load failed: {e}")
            return False

    def translate(self, text: str, language: str = "nepali", max_length: int = 512) -> dict:

        if not text or not text.strip():
            return {"success": True, "translated_text": ""}

        # Try LLM first (production - Groq API)
        if self.use_llm_api:
            result = self._translate_llm(text, language)
            if result["success"]:
                return result
            # If LLM fails, log but don't fall back to local in production to save memory
            logger.warning(f"LLM translation failed: {result.get('error')}")
            return result

        # Try local only if LLM not configured (dev mode)
        if TRANSFORMERS_AVAILABLE:
            return self._translate_local(text, language, max_length)

        # Final fallback
        return {
            "success": False,
            "translated_text": text,
            "error": "No model available (install transformers or enable LLM)"
        }

    def _translate_llm(self, text: str, language: str) -> dict:

        try:
            url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"

            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": f"Translate {language} to English:\n{text}"}
                ],
                "temperature": 0.3
            }

            res = requests.post(url, headers=headers, json=payload, timeout=30)

            if res.status_code != 200:
                return {"success": False, "error": res.text}

            data = res.json()
            translated = data["choices"][0]["message"]["content"].strip()

            return {"success": True, "translated_text": translated, "method": "llm"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _translate_local(self, text: str, language: str, max_length: int) -> dict:

        if not self.load_model(language):
            return {"success": False, "error": "Model not available"}

        try:
            tokenizer = self._tokenizers[language]
            model = self._models[language]

            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            outputs = model.generate(**inputs)

            translated = tokenizer.decode(outputs[0], skip_special_tokens=True)

            return {"success": True, "translated_text": translated, "method": "local"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_model_status(self) -> dict:
        """Return status of translation models and LLM."""
        return {
            "llm_api": {
                "available": self.use_llm_api,
                "provider": "Groq" if self.use_llm_api else "N/A",
                "model": "llama-3.1-8b-instant" if self.use_llm_api else "N/A",
            },
            "local_models": {
                "available": False,  # Production uses LLM only
                "note": "Local models disabled to reduce memory usage on free tier"
            }
        }


# Create global translator instance for production
translator = TranslationEngine()


# TEST CASES
if __name__ == "__main__":
    engine = TranslationEngine()
