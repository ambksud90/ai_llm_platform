"""
orchestrator.py — Multi-call test generation pipeline
"""

import json
import logging
import time
import os
from src.generation.api_client import call_api
from src.generation.parser import extract_json
from src.generation.validator.deduplicator import (
    remove_duplicates
)
from langsmith import traceable

logger = logging.getLogger(__name__)



MODULES = [
    {
        "name": "User Login & Authentication",
        "focus": """
Generate test cases ONLY for User Login and Authentication covering:
- Happy path: valid login
- Invalid username, invalid password, empty fields
- Password complexity rules (each rule as a separate TC):
    * less than 8 characters
    * no uppercase letter
    * no number
    * no special character
- Account lockout after 3 failed attempts (15 min lock)
- Locked account error message
- Brute force protection (rapid repeated attempts)
- SQL injection in username field: test_data must include {"username": "' OR '1'='1' --"}
- XSS in username field: test_data must include {"username": "<script>alert('XSS')</script>"}

"""
    },
    {
        "name": "Dashboard & Session",
        "focus": """
Generate test cases ONLY for Dashboard and Session Management covering:
- Account summary visible after login
- Available balance displayed correctly
- Dashboard loads within 3 seconds
- Session expires automatically after 10 minutes inactivity:
    test_data must include {"inactivity_duration_minutes": 10}
- User cannot access dashboard without logging in (redirect to login)
- Session is fully cleared after logout

"""
    },
    {
        "name": "Fund Transfer",
        "focus": """
Generate test cases ONLY for Fund Transfer covering:
- Happy path: successful transfer with confirmation + unique transaction ID
- Insufficient balance
- Invalid IFSC code
- Non-existent beneficiary account
- Missing required fields (each field individually)
- Transfer amount = 0 (boundary)
- Transfer amount = minimum valid (0.01)
- Amount exceeds balance (boundary)
- OTP verification required for transactions above $10,000:
    test_data must include {"transfer_amount": 15000.00, "otp": "123456"}
- Transaction history shows the completed transfer

"""
    },
    {
        "name": "Security",
        "focus": """
Generate test cases ONLY for Security covering:
- CSRF: submit fund transfer without valid CSRF token:
    test_data must include {"csrf_token": "invalid_or_missing"}
- Session fixation: set known session ID before login, verify server regenerates it:
    test_data must include {"pre_login_session_id": "ATTACKER_FIXED_SESSION_ABC123"}
- Session hijacking: reuse token after logout:
    test_data must include {"stolen_session_token": "eyJhbGciOiJIUzI1NiJ9.stolen"}
- IDOR: access another user's account by manipulating account ID in URL:
    test_data must include {"target_account_id": "OTHER_USER_99999"}
- Privilege escalation: customer token used on admin endpoint:
    test_data must include {"user_role": "customer", "target_endpoint": "/admin/users"}
- Password stored as hash (not plain text) in database

"""
    },
    {
        "name": "Performance & Cross-Browser",
        "focus": """
Generate test cases ONLY for Performance and Cross-Browser compatibility covering:
- API response time under 2 seconds
- Dashboard loads within 3 seconds
- System supports 10,000 concurrent users:
    test_data must include {"concurrent_users": 10000, "test_duration_seconds": 60}
- Login works correctly in Chrome 124:
    test_data must include {"browser": "Chrome", "version": "124"}
- Login works correctly in Firefox 125:
    test_data must include {"browser": "Firefox", "version": "125"}
- Login works correctly in Safari 17:
    test_data must include {"browser": "Safari", "version": "17"}
- Login works correctly in Edge 124:
    test_data must include {"browser": "Edge", "version": "124"}
- Login works on iOS Safari (mobile viewport)
- Login works on Android Chrome (mobile viewport)

"""
    },
    {
        "name": "Accessibility & Error Handling",
        "focus": """
Generate test cases ONLY for Accessibility and Error Handling covering:
- All login form fields navigable by keyboard alone (no mouse):
    test_data must include {"input_method": "keyboard_only"}
- Screen reader (NVDA) announces validation error on invalid login:
    test_data must include {"screen_reader": "NVDA", "trigger": "submit empty form"}
- Colour contrast on login page meets WCAG 2.1 AA standard
- Focus indicator visible on all interactive elements
- System displays user-friendly error for failed transaction
- System generates a log entry for every failed transaction
- User is not double-charged on retry after network failure
- Error messages are specific and actionable (not generic "error occurred")

"""
    }
]


SYSTEM_PROMPT = """
You are a Principal QA Engineer with 15+ years of enterprise software testing experience.
Your test cases are used directly in production QA pipelines.
Every test case object MUST contain ALL 14 fields — never omit any.
Never truncate a test case object mid-way.
Output ONLY a valid JSON array starting with [ and ending with ].
No prose, no markdown, no explanation.
""".strip()


FOCUSED_PROMPT_TEMPLATE = """
You are generating test cases for ONE specific module of an Online Banking Web Application.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SRS CONTEXT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK — MODULE: {module_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{module_focus}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rag_examples}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT RULES:
1. JSON array only — starts with [ ends with ]
2. Every object MUST have ALL of these fields:
   "id", "module", "category", "test_type", "priority", "scenario",
   "preconditions", "steps", "test_data", "expected_result",
   "actual_result" (= "Pending"), "status" (= "Not Executed"),
   "risk_level", "automation_candidate"
3. "test_data" must contain REAL concrete values — no placeholders
4. Each step is ONE atomic action
5. IDs start from {id_start} — format TC_{id_start:03d}, TC_{id_next:03d}...
6. Generate ONLY meaningful, unique,
   high-value test cases.

7. Avoid repetitive or near-identical
   test cases.

8. Prioritize coverage depth over quantity.

9. NEVER invent business rules,
   thresholds, lock durations,
   OTP limits, or validation rules
   unless explicitly stated in the SRS.

10. STRICT LIMIT:
    generate a MAXIMUM of {max_tcs}
    test cases then stop.

Begin with [ immediately.
""".strip()


def _build_focused_payload(
    requirement: str,
    module: dict,
    id_start: int,
    rag_block: str = ""
) -> dict:
    max_tcs = 10

    user_message = FOCUSED_PROMPT_TEMPLATE.format(
        requirement=requirement.strip(),
        module_name=module["name"],
        module_focus=module["focus"].strip(),
        rag_examples=rag_block or "No reference examples available.",
        id_start=id_start,
        id_next=id_start + 1,
        max_tcs=max_tcs
    )

    return {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        "max_tokens":  3000,
        "temperature": 0.2,
        "top_p":       0.9,
        "stream":      False
    }


@traceable(name="generate_all_modules", project_name="QA-TestCase-Agent")
def generate_all_modules(
    requirement: str,
    retriever=None,
    delay_between_calls: int = 5
) -> list[dict]:
    """
    Run one focused API call per module, merge results, deduplicate.
    """
    all_test_cases = []
    id_counter = 1

    for i, module in enumerate(MODULES, 1):
        logger.info(
            f"[{i}/{len(MODULES)}] Generating test cases for: {module['name']}"
        )

        rag_block = ""
        if retriever:
            try:
                retrieved = retriever.retrieve(
                    module["focus"] + " " + requirement[:500],
                    top_k=3
                )
                if retrieved:
                    from src.generation.retriever import format_examples_for_prompt
                    rag_block = format_examples_for_prompt(retrieved, max_examples=2)
                    logger.info(f"  RAG: {len(retrieved)} examples retrieved")
            except Exception as e:
                logger.warning(f"  RAG retrieval failed for module: {e}")

        payload = _build_focused_payload(
            requirement=requirement,
            module=module,
            id_start=id_counter,
            rag_block=rag_block
        )

        try:
            raw_response = call_api(payload)
            module_tcs   = extract_json(raw_response)

            if not isinstance(module_tcs, list):
                logger.warning(f"  Unexpected response format — skipping module")
                continue

            for tc in module_tcs:
                if not tc.get("module"):
                    tc["module"] = module["name"]

            logger.info(f"  Generated {len(module_tcs)} test cases")
            all_test_cases.extend(module_tcs)
            id_counter += len(module_tcs)

        except Exception as e:
            logger.error(f"  Module '{module['name']}' failed: {e} — continuing")

        if i < len(MODULES):
            logger.info(f"  Waiting {delay_between_calls}s before next call...")
            time.sleep(delay_between_calls)

    logger.info(f"All modules complete. Total before dedup: {len(all_test_cases)}")
    final = remove_duplicates(all_test_cases)
    logger.info(f"Final test suite: {len(final)} unique test cases")
    return final