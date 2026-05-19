import json
import logging

logger = logging.getLogger(__name__)


def extract_json(text: str) -> list[dict]:

    logger.info("Extracting JSON from model response")

    if "```" in text:

        for part in text.split("```"):

            cleaned = part.lstrip("json").strip()

            if cleaned.startswith("["):

                text = cleaned
                break

    start = text.find("[")
    end = text.rfind("]") + 1

    if start == -1 or end == 0:

        logger.error("No JSON array found in response")

        raise ValueError("No JSON array found")

    parsed = json.loads(text[start:end])

    logger.info(f"Successfully parsed {len(parsed)} test cases")

    return parsed