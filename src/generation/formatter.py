import logging

logger = logging.getLogger(__name__)


def print_test_cases(cases: list[dict]) -> None:

    logger.info("Printing formatted test cases")

    separator = "─" * 64

    print(f"\n{'═' * 64}")
    print(f" GENERATED TEST CASES ({len(cases)} total)")
    print(f"{'═' * 64}")

    for tc in cases:

        print(f"\n{separator}")

        # ── Header ───────────────────────────────────────────────────────
        print(f"[{tc.get('id', 'N/A')}] {tc.get('scenario', 'N/A')}")
        print(
            f"Module: {tc.get('module', 'N/A')} | "
            f"Category: {tc.get('category', 'N/A')} | "
            f"Type: {tc.get('test_type', 'N/A')} | "   # ← was 'type' (wrong)
            f"Priority: {tc.get('priority', 'N/A')} | "
            f"Risk: {tc.get('risk_level', 'N/A')} | "
            f"Automation: {tc.get('automation_candidate', 'N/A')}"
        )

        print(separator)

        # ── Preconditions ─────────────────────────────────────────────────
        preconditions = tc.get("preconditions", "")
        if preconditions:
            print(f"Preconditions: {preconditions}")

        # ── Test Data ─────────────────────────────────────────────────────
        test_data = tc.get("test_data", {})
        if test_data:
            print("Test Data:")
            for key, value in test_data.items():
                print(f"  {key}: {value}")

        # ── Steps ─────────────────────────────────────────────────────────
        print("Steps:")
        for i, step in enumerate(tc.get("steps", []), 1):
            print(f"  {i}. {step}")

        # ── Expected Result ───────────────────────────────────────────────
        print(f"\nExpected: {tc.get('expected_result', 'N/A')}")  # ← was 'expected' (wrong)
        print(f"Status:   {tc.get('status', 'Not Executed')}\n")