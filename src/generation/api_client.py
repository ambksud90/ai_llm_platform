import requests
import time
import logging
import os

from requests.exceptions import ReadTimeout, ConnectionError, HTTPError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

HF_TOKEN  = os.getenv("HF_TOKEN")
API_URL   = "https://router.huggingface.co/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type":  "application/json",
}

# Retry config
MAX_RETRIES       = 3
RETRY_WAIT        = 30   # seconds between retries
REQUEST_TIMEOUT   = 300  # seconds — enough for 8 000-token generation on 7B model

# Status codes that are worth retrying
RETRYABLE_CODES = {503, 502, 429, 504}


def call_api(payload: dict,
             retries: int = MAX_RETRIES,
             wait:    int = RETRY_WAIT) -> str:
    """
    Call the HuggingFace inference router with retry logic.

    Retries on:
      - HTTP 503 / 502  (model loading or gateway error)
      - HTTP 429        (rate limit — backs off with longer wait)
      - ReadTimeout     (model took too long — retries with same timeout)
      - ConnectionError (transient network blip)

    Raises RuntimeError after all retries are exhausted.
    """

    # ── Guard: token present ──────────────────────────────────────────────
    if not HF_TOKEN:
        raise EnvironmentError(
            "HF_TOKEN is not set. Add it to your .env file."
        )

    # ── Detect model from payload (single source of truth = prompt_builder) ──
    model = payload.get("model", "unknown-model")

    last_error = None

    for attempt in range(1, retries + 1):

        logger.info(f"Attempt {attempt}/{retries} — model: {model}")

        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            # ── Success ───────────────────────────────────────────────────
            if response.status_code == 200:
                logger.info("API request successful")
                content = response.json()["choices"][0]["message"]["content"]
                return content.strip()

            # ── Rate limited — back off longer ────────────────────────────
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", wait * 2))
                logger.warning(
                    f"Rate limited (429). Waiting {retry_after}s before retry..."
                )
                time.sleep(retry_after)
                last_error = f"HTTP 429 rate limit"
                continue

            # ── Model loading / gateway errors — short wait then retry ───
            if response.status_code in RETRYABLE_CODES:
                logger.warning(
                    f"HTTP {response.status_code} — model may be loading. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
                last_error = f"HTTP {response.status_code}"
                continue

            # ── Non-retryable error (400, 401, 403, 404, etc.) ───────────
            logger.error(f"Non-retryable API error: HTTP {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")

            if response.status_code == 401:
                raise RuntimeError(
                    "Authentication failed (HTTP 401). Check your HF_TOKEN in .env."
                )
            if response.status_code == 400:
                raise RuntimeError(
                    f"Bad request (HTTP 400). Check your payload.\n"
                    f"Details: {response.text[:300]}"
                )

            raise RuntimeError(
                f"API error HTTP {response.status_code}: {response.text[:300]}"
            )

        # ── Timeout — retry, don't crash ──────────────────────────────────
        except ReadTimeout:
            logger.warning(
                f"Request timed out after {REQUEST_TIMEOUT}s "
                f"(attempt {attempt}/{retries}). "
                f"Retrying in {wait}s..."
            )
            last_error = f"ReadTimeout after {REQUEST_TIMEOUT}s"
            if attempt < retries:
                time.sleep(wait)
            continue

        # ── Network blip — retry ──────────────────────────────────────────
        except ConnectionError as e:
            logger.warning(
                f"Connection error (attempt {attempt}/{retries}): {e}. "
                f"Retrying in {wait}s..."
            )
            last_error = str(e)
            if attempt < retries:
                time.sleep(wait)
            continue

    # ── All retries exhausted ─────────────────────────────────────────────
    raise RuntimeError(
        f"Pipeline failed after {retries} attempts. "
        f"Last error: {last_error}"
    )