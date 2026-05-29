import logging
 
logger = logging.getLogger(__name__)
 
# Minimum score to be included in approved output
QUALITY_THRESHOLD = 50
 
 
def calculate_quality_score(tc: dict) -> int:
    score = 0
 
    # Scenario present and meaningful (10)
    scenario = tc.get("scenario", "")
    if scenario and len(scenario.strip()) > 10:
        score += 10
 
    # Preconditions present (10)
    if tc.get("preconditions"):
        score += 10
 
    # Steps — list with at least 3 entries (20)
    steps = tc.get("steps", [])
    if isinstance(steps, list) and len(steps) >= 3:
        score += 20
 
    # Expected result — present and not N/A (20)
    expected = tc.get("expected_result", "")
    if expected and expected.strip() not in ["", "N/A", "Pending"] and len(expected.strip()) > 10:
        score += 20
 
    # test_data — BONUS only, not penalised if absent (15)
    # Accessibility, UI, and colour contrast TCs
    # legitimately have no input data — don't punish them
    test_data = tc.get("test_data", {})
    if isinstance(test_data, dict) and len(test_data) > 0:
        score += 15
 
    # automation_candidate = True (10)
    if tc.get("automation_candidate") is True:
        score += 10
 
    # Priority is Critical or High (10)
    if tc.get("priority") in ["Critical", "High"]:
        score += 10
 
    # Security category bonus (5)
    if tc.get("category") == "Security":
        score += 5
 
    return min(score, 100)
 
 
def score_test_cases(test_cases: list) -> list:
    logger.info("Scoring test case quality")
 
    scored = []
 
    for tc in test_cases:
        quality_score = calculate_quality_score(tc)
        tc["quality_score"] = quality_score
 
        if quality_score >= QUALITY_THRESHOLD:
            scored.append(tc)
        else:
            logger.warning(
                f"Low quality TC removed: "
                f"{tc.get('id')} (score={quality_score})"
            )
 
    logger.info(f"{len(scored)} high-quality test cases retained")
    return scored