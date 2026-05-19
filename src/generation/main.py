import json
import logging

from api_client import call_api
from parser import extract_json
from formatter import print_test_cases
from prompt_builder import build_prompt

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def get_requirement() -> str:

    print("\nEnter software requirement:\n")

    requirement = input("> ")

    return requirement


try:

    logger.info("Starting AI test generation pipeline")

    # Dynamic user input
    requirement = get_requirement()

    # Build prompt dynamically
    payload = build_prompt(requirement)

    # Call LLM
    raw_response = call_api(payload)

    # Parse JSON
    parsed_test_cases = extract_json(raw_response)

    # Print formatted output
    print_test_cases(parsed_test_cases)

    # Save output
    with open("../../outputs/test_cases.json", "w") as file:

        json.dump(parsed_test_cases, file, indent=2)

    logger.info("Saved generated test cases")

except Exception as error:

    logger.exception(f"Pipeline failed: {error}")