import logging

from sentence_transformers import (
    SentenceTransformer,
    util
)

logger = logging.getLogger(__name__)

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

HALLUCINATION_THRESHOLD = 0.45


def check_hallucinations(
    requirement_chunks,
    test_cases
):

    logger.info(
        "Running hallucination evaluation"
    )

    if not requirement_chunks:

        logger.warning(
            "No requirement chunks found"
        )

        return {

            "grounded_cases":
                test_cases,

            "hallucinated_cases":
                []
        }

    chunk_embeddings = model.encode(
        requirement_chunks,
        convert_to_tensor=True
    )

    hallucinated = []

    grounded = []

    for tc in test_cases:

        text_to_validate = " ".join([

            tc.get("scenario", ""),

            tc.get("preconditions", ""),

            " ".join(
                tc.get("steps", [])
            ),

            tc.get(
                "expected_result",
                ""
            )
        ])

        tc_embedding = model.encode(
            text_to_validate,
            convert_to_tensor=True
        )

        similarities = util.cos_sim(
            tc_embedding,
            chunk_embeddings
        )[0]

        best_score = max(
            similarities
        ).item()

        best_match_index = similarities.argmax().item()

        supporting_requirement = (
            requirement_chunks[
                best_match_index
            ]
        )

        tc["grounding_score"] = round(
            best_score,
            3
        )

        tc[
            "supporting_requirement"
        ] = supporting_requirement

        # ─────────────────────────
        # RISK LEVEL
        # ─────────────────────────

        if best_score < 0.45:

            risk = "High"

        elif best_score < 0.60:

            risk = "Medium"

        else:

            risk = "Low"

        tc[
            "hallucination_risk"
        ] = risk

        # ─────────────────────────
        # FLAGGING
        # ─────────────────────────

        if best_score < \
                HALLUCINATION_THRESHOLD:

            tc[
                "hallucination_flag"
            ] = True

            hallucinated.append(tc)

            logger.warning(
                f"Possible hallucination: "
                f"{tc.get('id')} "
                f"(score={best_score:.2f})"
            )

        else:

            tc[
                "hallucination_flag"
            ] = False

            grounded.append(tc)

    logger.info(
        f"Grounded: {len(grounded)} | "
        f"Hallucinated: {len(hallucinated)}"
    )

    return {

        "grounded_cases":
            grounded,

        "hallucinated_cases":
            hallucinated
    }