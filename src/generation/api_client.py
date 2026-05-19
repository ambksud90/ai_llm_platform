import requests
import time
import logging
import os
from dotenv import load_dotenv


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# API Config
HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-72B-Instruct"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}


def call_api(payload: dict, retries: int = 3, wait: int = 25) -> str:

    for attempt in range(1, retries + 1):

        logger.info(f"Attempt {attempt}/{retries} using model: {MODEL}")

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=90
        )

        if response.status_code == 200:

            logger.info("API request successful")

            return response.json()["choices"][0]["message"]["content"].strip()

        if response.status_code == 503:

            logger.warning(f"Model loading... retrying in {wait} seconds")

            time.sleep(wait)

            continue

        logger.error(f"API Error {response.status_code}")
        logger.error(response.text[:300])

        raise RuntimeError(f"API Error {response.status_code}")

    raise RuntimeError("Model unavailable after retries")