import json
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Similarity threshold
SIMILARITY_THRESHOLD = 0.92


# ─────────────────────────────────────────────
# TEXT SIMILARITY
# ─────────────────────────────────────────────

def similarity(a: str, b: str) -> float:

    return SequenceMatcher(
        None,
        a.lower().strip(),
        b.lower().strip()
    ).ratio()


# ─────────────────────────────────────────────
# REMOVE DUPLICATES
# ─────────────────────────────────────────────

def remove_duplicates(test_cases):

    logger.info("Running deduplication")

    unique_cases = []

    duplicate_count = 0

    exact_seen = set()

    for tc in test_cases:

        scenario = tc.get(
            "scenario",
            ""
        ).strip()

        test_data = json.dumps(
            tc.get("test_data", {}),
            sort_keys=True
        )

        # Exact duplicate key
        exact_key = (
            scenario.lower(),
            test_data
        )

        # Skip exact duplicates
        if exact_key in exact_seen:

            duplicate_count += 1

            logger.warning(
                f"Exact duplicate removed: "
                f"{tc.get('id')}"
            )

            continue

        # Semantic duplicate detection
        is_duplicate = False

        for existing in unique_cases:

            existing_scenario = existing.get(
                "scenario",
                ""
            )

            score = similarity(
                scenario,
                existing_scenario
            )

            # Similar scenario + same category
            if (
                score >= SIMILARITY_THRESHOLD
                and
                tc.get("category")
                ==
                existing.get("category")
            ):

                duplicate_count += 1

                logger.warning(
                    f"Semantic duplicate removed: "
                    f"{tc.get('id')} "
                    f"(similarity={round(score, 2)})"
                )

                is_duplicate = True

                break

        if not is_duplicate:

            exact_seen.add(exact_key)

            unique_cases.append(tc)

    logger.info(
        f"Deduplication complete — "
        f"removed {duplicate_count} duplicates, "
        f"{len(unique_cases)} unique test cases remain"
    )

    return unique_cases