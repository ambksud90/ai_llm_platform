import logging
 
logger = logging.getLogger(__name__)
 
REQUIRED_FIELDS = [
    "id",
    "module",
    "category",
    "test_type",
    "priority",
    "scenario",
    "preconditions",
    "steps",
    "test_data",
    "expected_result",
    "actual_result",
    "status",
    "risk_level",
    "automation_candidate"
]
 
# Fields where an empty value is a WARNING (not rejection)
# test_data is legitimately empty for UI/accessibility TCs
# e.g. colour contrast check, focus indicator — no input data needed
OPTIONAL_EMPTY_FIELDS = {"test_data"}
 
# Fields where N/A counts as a valid value (LLM sometimes sets these)
NA_ALLOWED_FIELDS = {"risk_level", "automation_candidate"}
 
 
def validate_single_test_case(tc) -> bool:

    # ─────────────────────────────────────────
    # TYPE CHECK
    # ─────────────────────────────────────────

    if not isinstance(tc, dict):

        logger.warning(
            f"Schema error: expected dict, "
            f"got {type(tc).__name__}"
        )

        return False

    tc_id = tc.get(
        "id",
        "UNKNOWN"
    )

    # ─────────────────────────────────────────
    # REQUIRED FIELDS
    # ─────────────────────────────────────────

    for field in REQUIRED_FIELDS:

        # Missing field
        if field not in tc:

            logger.warning(
                f"Missing field '{field}' "
                f"in {tc_id}"
            )

            return False

        value = tc[field]

        # Empty string / None
        if value in [None, ""]:

            if field in OPTIONAL_EMPTY_FIELDS:

                logger.warning(
                    f"Empty field '{field}' "
                    f"in {tc_id} (allowed)"
                )

                continue

            logger.warning(
                f"Empty field '{field}' "
                f"in {tc_id}"
            )

            return False

        # Empty list
        if isinstance(value, list) and len(value) == 0:

            logger.warning(
                f"Empty list field '{field}' "
                f"in {tc_id}"
            )

            return False

        # Empty dict
        if isinstance(value, dict) and len(value) == 0:

            if field in OPTIONAL_EMPTY_FIELDS:

                logger.warning(
                    f"Empty dict '{field}' "
                    f"in {tc_id} (allowed)"
                )

                continue

            logger.warning(
                f"Empty dict '{field}' "
                f"in {tc_id}"
            )

            return False

        # N/A validation
        if isinstance(value, str) and \
        value.strip().lower() in {

            "n/a",
            "na"

        } and \
                field not in NA_ALLOWED_FIELDS:

            if field in OPTIONAL_EMPTY_FIELDS:

                logger.warning(
                    f"N/A field '{field}' "
                    f"in {tc_id} (allowed)"
                )

                continue

            logger.warning(
                f"N/A value in "
                f"required field '{field}' "
                f"in {tc_id}"
            )

            return False

    # ─────────────────────────────────────────
    # STEPS FORMAT
    # ─────────────────────────────────────────

    if not isinstance(
        tc.get("steps"),
        list
    ):

        logger.warning(
            f"Invalid steps format "
            f"in {tc_id}"
        )

        return False

    # ─────────────────────────────────────────
    # TEST DATA FORMAT
    # ─────────────────────────────────────────

    if not isinstance(
        tc.get("test_data"),
        dict
    ):

        logger.warning(
            f"Invalid test_data format "
            f"in {tc_id}"
        )

        return False

    return True
 
def validate_schema(test_cases: list) -> list:
    logger.info("Running schema validation")
 
    valid_cases = []
    invalid_count = 0
 
    for tc in test_cases:
        if validate_single_test_case(tc):
            valid_cases.append(tc)
        else:
            invalid_count += 1
 
    logger.info(
        f"Schema validation complete — "
        f"{len(valid_cases)} valid, {invalid_count} invalid"
    )
    return valid_cases