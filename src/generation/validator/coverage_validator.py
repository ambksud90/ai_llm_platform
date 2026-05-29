import logging
from collections import Counter

logger = logging.getLogger(__name__)


REQUIRED_CATEGORIES = [
    "Functional",
    "Negative",
    "Security",
    "Performance",
    "Accessibility",
    "Cross-Browser",
    "UI",
    "Data Integrity",
    "Error Handling"
]


CATEGORY_MAP = {

    "happy path":"Functional",
    "positive":"Functional",
    "functional":"Functional",
    "edge":"Functional",
    "edge case":"Functional",

    "negative":"Negative",
    "invalid input":"Negative",
    "missing required fields":"Negative",
    "boundary":"Negative",
    "boundary value":"Negative",

    "security":"Security",
    "csrf":"Security",
    "session fixation":"Security",
    "session hijacking":"Security",
    "idor":"Security",
    "xss":"Security",
    "sql injection":"Security",
    "brute force":"Security",
    "sensitive data":"Security",

    "performance":"Performance",
    "load testing":"Performance",
    "dashboard load":"Performance",
    "concurrent":"Performance",
    "nfr":"Performance",

    "accessibility":"Accessibility",
    "keyboard":"Accessibility",
    "screen reader":"Accessibility",
    "colour contrast":"Accessibility",
    "focus indicator":"Accessibility",

    "cross-browser":"Cross-Browser",
    "browser":"Cross-Browser",
    "mobile":"Cross-Browser",

    "ui":"UI",
    "ux":"UI",
    "dashboard":"UI",

    "data integrity":"Data Integrity",
    "transaction":"Data Integrity",
    "fund transfer":"Data Integrity",

    "error handling":"Error Handling",
    "failed transaction":"Error Handling",
    "user-friendly error":"Error Handling",

    "invalid credentials": "Negative",
    "password complexity rules": "Security",
    "account lockout": "Security",
    "login": "Cross-Browser",
    "transfer amount = 0": "Negative",
    "amount exceeds balance": "Negative",
    "invalid ifsc code": "Negative"
}


def normalise_category(raw: str):

    raw = raw.lower().strip()

    # partial match instead of exact match
    for keyword, standard in CATEGORY_MAP.items():

        if keyword in raw:
            return standard

    return raw


def validate_coverage(test_cases):

    logger.info(
        "Running coverage validation"
    )

    normalised=[]

    for tc in test_cases:

        category = normalise_category(
            tc.get(
                "category",
                ""
            )
        )

        tc["category"]=category

        normalised.append(
            category
        )

    counter=Counter(
        normalised
    )

    logger.info(
        "Coverage Summary:"
    )

    missing=[]

    for category in REQUIRED_CATEGORIES:

        count=counter.get(
            category,
            0
        )

        logger.info(
            f"{category}: {count}"
        )

        if count==0:

            missing.append(
                category
            )

            logger.warning(
                f"Missing coverage for: "
                f"{category}"
            )

    return missing