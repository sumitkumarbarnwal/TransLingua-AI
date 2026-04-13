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
import os
import requests
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    TRANSLATION_MODELS, MODELS_DIR, 
    USE_LLM, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
)

logger = logging.getLogger(__name__)


class TranslationEngine:
    """
    Neural Machine Translation engine.
    Supports local MarianMT models and LLM APIs (OpenAI, Groq, etc.)
    """

    def __init__(self):
        self._models = {}
        self._tokenizers = {}
        self._loaded = set()
        
        # Initialize LLM API if using LLM
        self.use_llm_api = USE_LLM and LLM_API_KEY
        if self.use_llm_api:
            logger.info(f"LLM Translation enabled. Model: {LLM_MODEL}, Base URL: {LLM_BASE_URL}")

    def _get_cache_dir(self, language: str) -> Path:
        """Get the local cache directory for a model."""
        return MODELS_DIR / language

    def load_model(self, language: str) -> bool:
        """
        Load a translation model for the given language.
        Only used if USE_LLM is false or API is unavailable.
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
            logger.info(f"Loading local translation model for {language}: {model_name}")
            local_model_path = cache_dir / "model"
            
            if local_model_path.exists():
                self._tokenizers[language] = MarianTokenizer.from_pretrained(str(local_model_path))
                self._models[language] = MarianMTModel.from_pretrained(str(local_model_path))
            else:
                self._tokenizers[language] = MarianTokenizer.from_pretrained(model_name)
                self._models[language] = MarianMTModel.from_pretrained(model_name)
                
                # Save locally
                self._tokenizers[language].save_pretrained(str(local_model_path))
                self._models[language].save_pretrained(str(local_model_path))

            self._loaded.add(language)
            return True
        except Exception as e:
            logger.error(f"Failed to load local model for {language}: {str(e)}")
            return False

    def translate(self, text: str, language: str = "nepali", max_length: int = 512) -> dict:
        """
        Translate text from Nepali or Sinhalese to English using LLM or local model.
        """
        if not text or not text.strip():
            return {"success": True, "translated_text": "", "source_language": language, "target_language": "english"}

        # Try LLM Translation first if configured
        if USE_LLM and LLM_API_KEY:
            result = self._translate_llm(text, language)
            if result["success"]:
                return result
            logger.warning(f"LLM translation failed, falling back to local model: {result.get('error')}")

        # Fallback to local model
        return self._translate_local(text, language, max_length)

    def _translate_llm(self, text: str, language: str) -> dict:
        """Translate using LLM API (OpenAI/Groq) via direct HTTP requests."""
        if not self.use_llm_api:
            return {"success": False, "error": "LLM translation not configured"}
        
        try:
            api_url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in South Asian languages (Nepali and Sinhalese). Provide accurate, natural-sounding English translations."
                    },
                    {
                        "role": "user",
                        "content": f"Translate the following {language} text to English. Provide only the translated text, nothing else.\n\nText: {text}"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
            
            logger.debug(f"Calling LLM API: {api_url}")
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"LLM API error {response.status_code}: {error_msg}")
                return {"success": False, "error": f"API error {response.status_code}"}
            
            result = response.json()
            translated_text = result["choices"][0]["message"]["content"].strip()
            
            return {
                "success": True,
                "translated_text": translated_text,
                "source_language": language,
                "target_language": "english",
                "method": "llm_api"
            }
            
        except requests.exceptions.Timeout:
            logger.error("LLM API request timed out")
            return {"success": False, "error": "LLM API request timed out"}
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            return {"success": False, "error": f"API request failed: {str(e)}"}
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse LLM API response: {e}")
            return {"success": False, "error": f"Invalid API response: {str(e)}"}
        except Exception as e:
            logger.error(f"LLM translation error: {e}")
            return {"success": False, "error": str(e)}

    def _translate_local(self, text: str, language: str, max_length: int) -> dict:
        """Legacy local translation logic using MarianMT."""
        if not self.load_model(language):
            return {
                "success": False, 
                "translated_text": "", 
                "error": "Local translation model not available."
            }

        try:
            tokenizer = self._tokenizers[language]
            model = self._models[language]
            chunks = self._split_text(text)
            translated_chunks = []

            for chunk in chunks:
                if not chunk.strip():
                    translated_chunks.append("")
                    continue

                inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
                translated_ids = model.generate(**inputs, max_length=max_length, num_beams=4)
                translated = tokenizer.decode(translated_ids[0], skip_special_tokens=True)
                translated_chunks.append(translated)

            return {
                "success": True,
                "translated_text": "\n".join(translated_chunks),
                "source_language": language,
                "target_language": "english",
                "method": "local_model"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _split_text(self, text: str, max_chars: int = 400) -> list:
        """Split text into chunks for local translation."""
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
                sentences = re.split(r'(?<=[।\.\?\!])\s+', para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_chars:
                        current_chunk += (" " if current_chunk else "") + sentence
                    else:
                        if current_chunk: chunks.append(current_chunk)
                        current_chunk = sentence
                if current_chunk: chunks.append(current_chunk)
        return chunks

    def get_model_status(self) -> dict:
        """Get the status of models and API."""
        return {
            "llm_api": {
                "enabled": USE_LLM,
                "configured": bool(LLM_API_KEY),
                "model": LLM_MODEL,
                "base_url": LLM_BASE_URL
            },
            "local_models": {lang: lang in self._loaded for lang in TRANSLATION_MODELS}
        }


# Singleton instance
translator = TranslationEngine()
