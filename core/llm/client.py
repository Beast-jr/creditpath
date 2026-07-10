"""Production Gemini wrapper: disk cache, backoff+jitter, hard timeout. Never burns quota twice."""

import hashlib
import json
import os
import random
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
CACHE_PATH = Path("data/cache/llm_cache.json")
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
REQUEST_TIMEOUT_SECONDS = 15
MAX_RETRIES = 3
BACKOFF_BASE = 1.0
BACKOFF_MAX_WAIT = 10.0


class GeminiClient:
    """Wraps Gemini with an on-disk cache, timeout, and retry (see generate)."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(GEMINI_MODEL)
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cache from disk, dropping entries older than the TTL."""
        if not CACHE_PATH.exists():
            return {}
        with open(CACHE_PATH, "r") as f:
            raw = json.load(f)
        now = time.time()
        return {k: v for k, v in raw.items() if now - v["timestamp"] < CACHE_TTL_SECONDS}

    def _save_cache(self) -> None:
        """Persist the current cache to disk, creating the folder if needed."""
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump(self._cache, f, indent=2)

    @staticmethod
    def _cache_key(prompt: str) -> str:
        """SHA-256 of the prompt — identical prompts hit the same cache entry."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _call_api(self, prompt: str) -> str:
        """One live call to Gemini with a hard timeout. Raises on failure."""
        response = self._model.generate_content(
            prompt,
            request_options={"timeout": REQUEST_TIMEOUT_SECONDS},
        )
        return response.text

    def generate(self, prompt: str, schema: dict = None) -> str:
        """Return Gemini's response for a prompt, using cache and retrying on 429.

        If schema is provided, JSON-schema enforcement is appended to the prompt.
        """
        if schema is not None:
            prompt = f"{prompt}\n\nReturn ONLY valid JSON matching this schema:\n{json.dumps(schema)}"

        key = self._cache_key(prompt)
        if key in self._cache:
            return self._cache[key]["response"]

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._call_api(prompt)
                self._cache[key] = {"response": response, "timestamp": time.time()}
                self._save_cache()
                return response
            except Exception as e:
                last_error = e
                if "429" not in str(e):
                    raise
                wait = min(BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 1), BACKOFF_MAX_WAIT)
                time.sleep(wait)

        raise RuntimeError(f"Gemini failed after {MAX_RETRIES} retries: {last_error}")