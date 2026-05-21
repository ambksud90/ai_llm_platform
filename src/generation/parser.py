import json
import logging
import re
from json_repair import repair_json

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    """Strip markdown code fences and leading/trailing whitespace."""
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def _extract_json_block(text: str) -> str:
    """
    Extract the outermost JSON object or array from raw text.
    Tries array first (LLMs often return a list of test cases),
    then falls back to object.
    """
    # Try array [ ... ]
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)

    # Try object { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)

    raise ValueError("No JSON array or object found in response")


def extract_json(text: str):
    logger.info("Extracting JSON from model response")

    text = _clean_text(text)

    # Strategy 1: direct parse on full cleaned text
    try:
        parsed = json.loads(text)
        logger.info("JSON parsed successfully (direct)")
        return parsed
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract JSON block then parse
    try:
        json_block = _extract_json_block(text)
        parsed = json.loads(json_block)
        logger.info("JSON parsed successfully (extracted block)")
        return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 3: repair then parse (handles missing commas, trailing commas, etc.)
    try:
        json_block = _extract_json_block(text)
        repaired = repair_json(json_block)
        parsed = json.loads(repaired)
        logger.info("JSON parsed successfully (repaired)")
        return parsed
    except Exception:
        pass

    # Strategy 4: repair the full text as last resort
    try:
        repaired = repair_json(text)
        parsed = json.loads(repaired)
        logger.info("JSON parsed successfully (full text repaired)")
        return parsed
    except Exception as error:
        logger.error(f"JSON parsing failed after all strategies: {error}")
        with open("broken_response.txt", "w") as f:
            f.write(text)
        logger.info("Saved broken response to broken_response.txt for debugging")
        raise