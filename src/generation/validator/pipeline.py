import logging
from src.generation.validator.deduplicator import (
    remove_duplicates
)

from src.generation.validator.schema_validator import (
    validate_schema
)

from src.generation.validator.coverage_validator import (
    validate_coverage
)

from src.generation.validator.quality_scorer import (
    score_test_cases
)


logger = logging.getLogger(__name__)


def validate_test_suite(test_cases):

    logger.info(
        "Starting validation pipeline"
    )

    # ─────────────────────────────────────────
    # STEP 1 — DEDUPLICATION
    # ─────────────────────────────────────────

    logger.info(
        "Running deduplication"
    )

    deduped_cases = remove_duplicates(
        test_cases
    )

    logger.info(
        f"Deduplication complete — "
        f"{len(deduped_cases)} unique test cases remain"
    )

    # ─────────────────────────────────────────
    # STEP 2 — FILTER INVALID OBJECTS
    # ─────────────────────────────────────────

    cleaned_cases = []

    skipped = 0

    for tc in deduped_cases:

        # Skip None
        if tc is None:

            skipped += 1

            logger.warning(
                "Skipping None object"
            )

            continue

        # Skip strings
        if isinstance(tc, str):

            skipped += 1

            logger.warning(
                f"Skipping string object: "
                f"{tc[:100]}"
            )

            continue

        # Skip anything not dict
        if not isinstance(tc, dict):

            skipped += 1

            logger.warning(
                f"Skipping invalid object type: "
                f"{type(tc)}"
            )

            continue

        cleaned_cases.append(tc)

    logger.info(
        f"Object cleanup complete — "
        f"removed {skipped} invalid objects"
    )

    # ─────────────────────────────────────────
    # STEP 3 — SCHEMA VALIDATION
    # ─────────────────────────────────────────

    logger.info(
        "Running schema validation"
    )

    valid_cases = validate_schema(
        cleaned_cases
    )

    invalid_count = (
        len(cleaned_cases)
        - len(valid_cases)
    )

    logger.info(
        f"Schema validation complete — "
        f"{len(valid_cases)} valid, "
        f"{invalid_count} invalid"
    )       

    # ─────────────────────────────────────────
    # STEP 4 — COVERAGE
    # ─────────────────────────────────────────

    logger.info(
        "Running coverage validation"
    )

    missing_coverage = validate_coverage(
        valid_cases
    )

    # ─────────────────────────────────────────
    # STEP 5 — QUALITY SCORING
    # ─────────────────────────────────────────

    logger.info(
        "Scoring quality"
    )

    approved_cases = score_test_cases(
        valid_cases
    )

    logger.info(
        f"Validation complete — "
        f"{len(approved_cases)} approved"
    )

    return {

        "approved_cases":
            approved_cases,

        "missing_coverage":
            missing_coverage
    }