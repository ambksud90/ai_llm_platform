import json
import logging
import os
from pathlib import Path



from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATION_DIR = Path(__file__).resolve().parent

env_path = PROJECT_ROOT / ".env"

if env_path.exists():

    load_dotenv(env_path)

    print(f"[DEBUG] Loaded .env: {env_path}")

else:

    print(f"[DEBUG] .env not found: {env_path}")

key = os.getenv("LANGCHAIN_API_KEY", "")

print(
    f"[DEBUG] API Key Loaded: "
    f"{'YES' if key else 'NO'}"
)

if key:

    print(
        f"[DEBUG] Key Prefix: "
        f"{key[:8]}..."
    )

print(
    f"[DEBUG] Tracing  : "
    f"{os.getenv('LANGCHAIN_TRACING_V2')}"
)

print(
    f"[DEBUG] Project  : "
    f"{os.getenv('LANGCHAIN_PROJECT')}"
)

print(
    f"[DEBUG] Endpoint : "
    f"{os.getenv('LANGCHAIN_ENDPOINT')}"
)



from pdf_loader import extract_pdf_text
from orchestrator import generate_all_modules
from formatter import print_test_cases
from retriever import TestCaseRetriever

from validator.pipeline import validate_test_suite
from validator.summary import generate_test_summary

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

pdf_path = (
    GENERATION_DIR
    / "requirements"
    / "requirment.pdf"
)

output_path = (
    PROJECT_ROOT
    / "outputs"
    / "test_cases.json"
)

# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

try:

    logger.info(
        "Starting AI Test Generation Pipeline "
        "(RAG + Validation + LangSmith)"
    )

    # ─────────────────────────────────────────
    # STEP 1 — LOAD REQUIREMENTS
    # ─────────────────────────────────────────

    requirement = extract_pdf_text(
        str(pdf_path)
    )

    logger.info(
        f"SRS loaded "
        f"({len(requirement)} chars)"
    )

    # ─────────────────────────────────────────
    # STEP 2 — INITIALISE RAG
    # ─────────────────────────────────────────

    retriever = None

    try:

        retriever = TestCaseRetriever()

        stats = retriever.get_stats()

        logger.info(
            f"RAG ready — "
            f"{stats['total_test_cases']} "
            f"existing TCs"
        )

    except Exception as e:

        logger.warning(
            f"RAG init failed: {e}"
        )

    # ─────────────────────────────────────────
    # STEP 3 — GENERATE TEST CASES
    # ─────────────────────────────────────────

    raw_test_cases = generate_all_modules(
        requirement=requirement,
        retriever=retriever,
        delay_between_calls=12
    )

    logger.info(
        f"Generated "
        f"{len(raw_test_cases)} "
        f"raw test cases"
    )

    # ─────────────────────────────────────────
    # STEP 4 — VALIDATION
    # ─────────────────────────────────────────

    logger.info(
        "Running validation pipeline..."
    )

    validation_result = validate_test_suite(
        raw_test_cases
    )

    if not isinstance(
        validation_result,
        dict
    ):

        raise ValueError(
            "validate_test_suite() "
            "must return dict"
        )

    approved_cases = validation_result.get(
        "approved_cases",
        []
    )

    missing_coverage = validation_result.get(
        "missing_coverage",
        []
    )

    logger.info(
        f"{len(approved_cases)} "
        f"approved test cases"
    )

    if missing_coverage:

        logger.warning(
            f"Missing coverage: "
            f"{missing_coverage}"
        )

    else:

        logger.info(
            "All required coverage present"
        )

    from src.generation.evaluator.hallucination import (
    check_hallucinations
    )

    requirement_chunks = [

        chunk.strip()

        for chunk in requirement.split("\n")

        if len(chunk.strip()) > 40
    ]

    hallucination_result = (
        check_hallucinations(
            requirement_chunks,
            approved_cases
        )
    )

    grounded_cases = (
        hallucination_result[
            "grounded_cases"
        ]
    )

    hallucinated_cases = (
        hallucination_result[
            "hallucinated_cases"
        ]
    )

    logger.info(
        f"Grounded Cases: "
        f"{len(grounded_cases)}"
    )

    logger.warning(
        f"Possible Hallucinations: "
        f"{len(hallucinated_cases)}"
    )

    # Keep BOTH sets for reporting
    approved_cases = (
        grounded_cases
        + hallucinated_cases
    )
    # ─────────────────────────────────────────
    # STEP 5 — SUMMARY DASHBOARD
    # ─────────────────────────────────────────

    summary = generate_test_summary(
        approved_cases
    )

    logger.info(
        "\n══════════════════════════════════════"
    )

    logger.info(
        " TEST SUITE SUMMARY "
    )

    logger.info(
        "══════════════════════════════════════"
    )

    logger.info(
        f"Total Approved: "
        f"{summary['total_test_cases']}"
    )

    logger.info(
        "\nCoverage by Module:"
    )

    

    for module, count in \
            summary["module_summary"].items():

        logger.info(
            f"  {module}: {count}"
        )

    logger.info(
        "\nCoverage by Category:"
    )

    for category, count in \
            summary["category_summary"].items():

        logger.info(
            f"  {category}: {count}"
        )


    # ─────────────────────────────────────────
    # STEP 6 — DISPLAY TEST CASES
    # ─────────────────────────────────────────

    print_test_cases(
        approved_cases
    )

    # ─────────────────────────────────────────
    # STEP 7 — SAVE OUTPUT
    # ─────────────────────────────────────────

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            approved_cases,
            f,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"Saved to: {output_path}"
    )

    # ─────────────────────────────────────────
    # STEP 8 — UPDATE VECTOR DB
    # ─────────────────────────────────────────

    if retriever and approved_cases:

        try:

            added = retriever.index_test_cases(
                str(output_path)
            )

            logger.info(
                f"Indexed {added} "
                f"approved TCs"
            )

        except Exception as e:

            logger.warning(
                f"Vector DB update failed: {e}"
            )

    # ─────────────────────────────────────────
    # FINAL SUCCESS
    # ─────────────────────────────────────────

    logger.info(
        "Pipeline completed successfully"
    )

except Exception as error:

    logger.exception(
        f"Pipeline failed: {error}"
    )