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
        """Translate text using LLM API. Returns safe dict even on error."""
        try:
            if not text or not text.strip():
                return {
                    "success": True, 
                    "translated_text": "",
                    "method": "none"
                }

            # Try LLM first (production - Groq API)
            if self.use_llm_api:
                logger.info(f"Using LLM API for {language} translation")
                result = self._translate_llm(text, language)
                if result["success"]:
                    logger.info("LLM translation successful")
                    return result
                logger.warning(f"LLM translation failed: {result.get('error')}")
                return result

            # Fallback if LLM not configured
            logger.warning("LLM not configured, using fallback response")
            return {
                "success": False,
                "translated_text": text,
                "error": "LLM not configured"
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in translate(): {str(e)}", exc_info=True)
            return {
                "success": False,
                "translated_text": text,
                "error": f"Internal error: {str(e)}"
            }

    def _translate_llm(self, text: str, language: str) -> dict:
        """Translate using Groq LLM API via HTTP."""
        try:
            if not LLM_API_KEY:
                logger.error("LLM_API_KEY not configured")
                return {"success": False, "error": "LLM_API_KEY not configured"}

            # Validate and construct URL safely
            base_url = LLM_BASE_URL.rstrip('/') if LLM_BASE_URL else "https://api.groq.com/openai/v1"
            
            # Ensure it looks like a real URL
            if not base_url.startswith(('http://', 'https://')):
                base_url = "https://api.groq.com/openai/v1"
                logger.warning(f"Invalid LLM_BASE_URL, using default: {base_url}")
            
            url = f"{base_url}/chat/completions"
            logger.info(f"LLM API URL: {url}")

            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": LLM_MODEL or "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a professional translator. Translate the given text to English."},
                    {"role": "user", "content": f"Translate the following {language} text to English:\n\n{text}"}
                ],
                "temperature": 0.3,
                "max_tokens": 2048
            }

            logger.info(f"Calling LLM: model={payload['model']}, text_len={len(text)}")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            
            logger.info(f"LLM response status: {res.status_code}")

            if res.status_code != 200:
                error_msg = res.text[:500]
                logger.error(f"LLM API error {res.status_code}: {error_msg}")
                return {"success": False, "error": f"API error {res.status_code}: {error_msg}"}

            data = res.json()
            
            if "choices" not in data or not data["choices"]:
                logger.error(f"Invalid response structure: {list(data.keys())}")
                return {"success": False, "error": "Invalid API response"}
            
            translated = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Translation successful: {len(translated)} chars")

            return {"success": True, "translated_text": translated, "method": "llm_api"}

        except Exception as e:
            logger.error(f"LLM error: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Translation failed: {str(e)}"}

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
