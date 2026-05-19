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

        print(f"[{tc.get('id', 'N/A')}] {tc.get('scenario', '')}")

        print(
            f"Type: {tc.get('type', '')} | "
            f"Priority: {tc.get('priority', '')}"
        )

        print(separator)

        print("Steps:")

        for i, step in enumerate(tc.get("steps", []), 1):

            print(f"  {i}. {step}")

        print(f"\nExpected: {tc.get('expected', '')}\n")