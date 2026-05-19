import logging

logger = logging.getLogger(__name__)


def build_prompt(requirement: str) -> dict:

    logger.info("Building prompt payload")

    system_prompt = (
        "You are a senior QA engineer. "
        "Generate structured software test cases "
        "as valid JSON only."
    )

    user_prompt = f"""
Generate 5 software test cases for the requirement below.

Requirement:
{requirement}

Return a JSON array where each object contains:
- id
- scenario
- type
- priority
- steps
- expected

Rules:
- Include functional scenarios
- Include negative scenarios
- Include edge cases
- Include security-related scenarios
- Return ONLY JSON
"""

    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "max_tokens": 1200,
        "temperature": 0.3
    }

    logger.info("Prompt payload created successfully")

    return payload