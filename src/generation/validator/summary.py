from collections import Counter


def generate_test_summary(test_cases):

    total = len(test_cases)

    # ─────────────────────────────────────────
    # COUNT BY MODULE
    # ─────────────────────────────────────────

    module_counter = Counter()

    for tc in test_cases:

        module = tc.get(
            "module",
            "Unknown"
        )

        module_counter[module] += 1

    # ─────────────────────────────────────────
    # COUNT BY CATEGORY
    # ─────────────────────────────────────────

    category_counter = Counter()

    for tc in test_cases:

        category = tc.get(
            "category",
            "Unknown"
        )

        category_counter[category] += 1

    return {

        "total_test_cases": total,

        "module_summary":
            dict(module_counter),

        "category_summary":
            dict(category_counter)
    }