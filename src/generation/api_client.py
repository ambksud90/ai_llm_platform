import requests
import time
import logging
import os

from requests.exceptions import ReadTimeout, ConnectionError, HTTPError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PROVIDER CONFIG
# ─────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN     = os.getenv("HF_TOKEN")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HF_API_URL   = "https://router.huggingface.co/v1/chat/completions"


GROQ_MODEL_MAP = {

    "Qwen/Qwen2.5-7B-Instruct":
        "llama-3.1-8b-instant",

    "Qwen/Qwen2.5-72B-Instruct":
        "llama-3.1-8b-instant",

    "mistralai/Mistral-7B-Instruct-v0.3":
        "mixtral-8x7b-32768",

    "meta-llama/Llama-3.1-8B-Instruct":
        "llama-3.1-8b-instant",
}


MAX_RETRIES     = 3
RETRY_WAIT      = 30
REQUEST_TIMEOUT = 300

RETRYABLE_CODES = {503, 502, 429, 504}


def _get_provider() -> str:
    """Prefer Groq if key is present, fall back to HuggingFace."""
    if GROQ_API_KEY:
        return "groq"
    if HF_TOKEN:
        return "huggingface"
    raise EnvironmentError(
        "No API key found. Set GROQ_API_KEY or HF_TOKEN in your .env file."
    )


def _build_request(payload: dict, provider: str) -> tuple[str, dict, dict]:
    """
    Returns (url, headers, payload) for the chosen provider.
    Mutates a copy of payload so the original is unchanged.
    """
    import copy
    p = copy.deepcopy(payload)

    if provider == "groq":
        original_model = p.get("model", "")
        p["model"] = GROQ_MODEL_MAP.get(
            original_model,
            "llama-3.3-70b-versatile"   # safe default
        )
        # Groq does not support top_p + temperature together reliably
        p.pop("top_p", None)

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type":  "application/json",
        }
        return GROQ_API_URL, headers, p

    else:  # huggingface
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type":  "application/json",
        }
        return HF_API_URL, headers, p


def call_api(payload: dict,
             retries: int = MAX_RETRIES,
             wait: int = RETRY_WAIT) -> str:

    provider = _get_provider()

    url, headers, payload = _build_request(
        payload,
        provider
    )

    model = payload.get(
        "model",
        "unknown-model"
    )

    logger.info(
        f"Provider: {provider.upper()} — "
        f"model: {model}"
    )

    last_error = None

    MAX_WAIT = 30

    for attempt in range(
        1,
        retries + 1
    ):

        logger.info(
            f"Attempt {attempt}/{retries}"
        )

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            # SUCCESS
            if response.status_code == 200:

                logger.info(
                    "API request successful"
                )

                content = response.json()[
                    "choices"
                ][0][
                    "message"
                ][
                    "content"
                ]

                return content.strip()


            # RATE LIMIT
            if response.status_code == 429:

                exponential_wait = min(
                    2 ** attempt,
                    MAX_WAIT
                )

                logger.warning(
                    f"Rate limited (429). "
                    f"Retrying in "
                    f"{exponential_wait}s..."
                )

                time.sleep(
                    exponential_wait
                )

                last_error = (
                    "HTTP 429"
                )

                continue


            # SERVER ERRORS
            if response.status_code in {

                502,
                503,
                504

            }:

                server_wait = min(
                    wait * attempt,
                    MAX_WAIT
                )

                logger.warning(
                    f"HTTP {response.status_code}. "
                    f"Retrying in "
                    f"{server_wait}s..."
                )

                time.sleep(
                    server_wait
                )

                last_error = (
                    f"HTTP "
                    f"{response.status_code}"
                )

                continue


            logger.error(
                f"HTTP {response.status_code}"
            )

            logger.error(
                response.text[:500]
            )

            raise RuntimeError(

                f"API failed: "
                f"{response.status_code}"

            )

        except ReadTimeout:

            timeout_wait = min(
                wait,
                MAX_WAIT
            )

            logger.warning(
                f"Request timeout. "
                f"Retrying in "
                f"{timeout_wait}s..."
            )

            time.sleep(
                timeout_wait
            )

            last_error = "Timeout"


        except ConnectionError as e:

            connection_wait = min(
                wait,
                MAX_WAIT
            )

            logger.warning(
                f"Connection error: {e}"
            )

            time.sleep(
                connection_wait
            )

            last_error = str(e)


    raise RuntimeError(

        f"Failed after "
        f"{retries} retries. "
        f"Last error: "
        f"{last_error}"
    )