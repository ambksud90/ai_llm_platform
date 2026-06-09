import json
import logging
from pathlib import Path

from retriever import TestCaseRetriever, format_examples_for_prompt

logger = logging.getLogger(__name__)

DEFAULT_TC_PATH = str(
    Path(__file__).parent.parent.parent / "outputs" / "test_cases.json"
)

# ─────────────────────────────────────────────
#  SHARED SYSTEM PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Principal QA Engineer with 15+ years of experience in enterprise software testing
across banking, fintech, healthcare, e-commerce, and SaaS platforms.

Your test cases are used directly by QA teams in production pipelines.
They must be precise, unambiguous, executable, and complete.
Every single test case object MUST contain ALL required fields — never omit a field.
Never truncate your response mid-object. If you reach a limit, close the JSON array cleanly.

CRITICAL CORRECTNESS RULE:
For ALL security test cases, the expected_result MUST describe the system
BLOCKING or REJECTING the attack — never describe a successful attack or breach.
  CORRECT: "Server returns 403 Forbidden and denies access to the account."
  WRONG:   "Server displays the other user's account details."

OUTPUT FORMAT RULE:
Output ONLY a valid JSON array starting with [ on the very first character.
No prose, no markdown, no explanation before or after the array.
""".strip()


# ─────────────────────────────────────────────
#  CALL 1 — FUNCTIONAL CORE PROMPT
#  Covers: login, security, auth, session, UI,
#          accessibility, error handling, data integrity
# ─────────────────────────────────────────────

PROMPT_CALL1 = """
You are given a Software Requirements Specification (SRS) document.
Generate test cases covering ONLY the dimensions listed below.
Do NOT generate fund transfer, NFR/performance, or cross-browser tests — those are handled separately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SRS DOCUMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rag_examples}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR SCOPE FOR THIS CALL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] USER LOGIN & AUTHENTICATION
    - Valid login happy path
    - Invalid username / invalid password / empty fields
    - Password complexity — one TC per rule, test_data password must ACTUALLY violate the rule:
        * Less than 8 chars          e.g. "P@sw1"
        * No uppercase letter        e.g. "p@ssw0rd"   (zero uppercase)
        * No number                  e.g. "P@ssword"   (zero digits)
        * No special character       e.g. "Passw0rd"   (zero special chars)
    - Account lockout after 3 failed attempts (lockout for 15 minutes)
    - Locked account error message displayed

[2] SECURITY (OWASP Top 10)
    - SQL Injection in username field: {{"username": "' OR '1'='1' --", "password": "anything"}}
    - SQL Injection in password field: {{"username": "john_doe", "password": "' OR '1'='1' --"}}
    - XSS reflected: {{"input": "<script>alert('XSS')</script>"}}
    - XSS stored: inject payload into a form field; verify it does NOT execute on retrieval
    - CSRF: submit transfer without valid token {{"csrf_token": "invalid_or_missing"}}
    - Session fixation: {{"pre_login_session_id": "ATTACKER_FIXED_SESSION_ABC123"}}
    - Session hijacking after logout: {{"stolen_session_token": "eyJhbGciOiJIUzI1NiJ9.stolen"}}
    - IDOR — access another user's account via URL manipulation:
      {{"target_account_id": "OTHER_USER_99999"}}
      expected_result MUST say access is DENIED (403), not that data is shown
    - Privilege escalation: {{"user_role": "customer", "target_endpoint": "/admin/users"}}
      expected_result MUST say the request is REJECTED
    - Password stored as hash — verify plain text never appears in DB or logs
    - Sensitive data not exposed in API responses or URLs

[3] SESSION MANAGEMENT
    - Session expiry after 10 min inactivity:
      steps: (1) Log in. (2) Stay idle 10 min. (3) Attempt to navigate to dashboard.
      (4) Verify redirect to login with "session expired" message.
      test_data: {{"inactivity_duration_minutes": 10, "action_after_timeout": "navigate to dashboard"}}
    - Logout clears session — back button must not restore authenticated page:
      steps: (1) Log in. (2) Click logout. (3) Press browser back button.
      (4) Attempt direct URL access to dashboard.
      expected_result: "User is redirected to login; dashboard is not accessible."

[4] DASHBOARD
    - Account summary and available balance displayed after login
    - Dashboard loads within 3 seconds (measure from login click to fully rendered)

[5] UI / UX VALIDATION
    - Required field indicators visible on login form
    - Inline validation error on blur for each field
    - Error messages are user-friendly and specific (not generic "error occurred")
    - Success message shown after login
    - Loading spinner shown during async login operation
    - Submit button disabled while login is processing (prevent double-submit)

[6] ACCESSIBILITY (WCAG 2.1 AA)
    - All login form fields navigable by keyboard alone
    - Screen reader (NVDA) announces validation error on empty form submit
    - Colour contrast on login page meets WCAG 2.1 AA
    - Focus indicator visible on all interactive elements

[7] ERROR HANDLING
    - User-friendly error for failed transaction
    - Log entry generated for every failed transaction
    - User not double-charged on retry after network failure
    - Error messages are specific and actionable

[8] DATA INTEGRITY
    - Data saved matches data entered
    - Calculations (balances, totals) are correct
    - Audit log created for every state-changing operation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD RULES (every object must have ALL fields):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- "id"                   : "TC_001" format, starting from TC_001
- "module"               : SRS section name
- "category"             : Functional | Negative | Boundary | Security | UI | Accessibility | Error Handling | Data Integrity | Session Management
- "test_type"            : Happy Path | Negative | Boundary Value | Edge Case | Security | NFR | Regression
- "priority"             : Critical | High | Medium | Low
- "scenario"             : one clear sentence
- "preconditions"        : exact system state before test
- "steps"                : array of atomic strings — one action per step
- "test_data"            : object with real concrete values (no placeholders)
- "expected_result"      : precise, measurable, observable outcome
- "actual_result"        : "Pending"
- "status"               : "Not Executed"
- "risk_level"           : High | Medium | Low
- "automation_candidate" : boolean

Begin the JSON array immediately with [ on the first character.
""".strip()


# ─────────────────────────────────────────────
#  CALL 2 — GAPS FOCUS PROMPT
#  Covers: fund transfer, transaction confirmation,
#          NFR/performance, cross-browser, secure logout, OTP
# ─────────────────────────────────────────────

PROMPT_CALL2 = """
You are given a Software Requirements Specification (SRS) document.
Generate test cases covering ONLY the dimensions listed below.
Do NOT generate login, general security, or accessibility tests — those are handled separately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SRS DOCUMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR SCOPE FOR THIS CALL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] FUND TRANSFER — generate ALL of these sub-cases, in order:

    Happy path (all valid fields):
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "HDFC0001234", "amount": 500.00, "available_balance": 1000.00}}
      expected_result: "Transfer succeeds; confirmation message displayed; unique transaction ID generated."

    Amount = 0 (boundary — invalid):
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "HDFC0001234", "amount": 0.00, "available_balance": 1000.00}}
      expected_result: "Error: Amount must be greater than 0."

    Amount negative:
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "HDFC0001234", "amount": -100.00, "available_balance": 1000.00}}
      expected_result: "Error: Amount must be greater than 0."

    Amount exceeds available balance:
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "HDFC0001234", "amount": 9999.00, "available_balance": 200.00}}
      expected_result: "Error: Amount cannot exceed available balance."

    Amount exactly equals available balance (boundary — valid):
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "HDFC0001234", "amount": 200.00, "available_balance": 200.00}}
      expected_result: "Transfer succeeds; full balance transferred."

    Invalid IFSC code format:
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "12345ZZZZZ", "amount": 100.00}}
      expected_result: "Error: Invalid IFSC code format."

    Non-existent beneficiary account:
      test_data: {{"beneficiary_account": "0000000000", "ifsc_code": "HDFC0001234", "amount": 100.00}}
      expected_result: "Error: Beneficiary account does not exist."

    Empty beneficiary account field:
      test_data: {{"beneficiary_account": "", "ifsc_code": "HDFC0001234", "amount": 100.00}}
      expected_result: "Error: Beneficiary account is required."

    Empty IFSC field:
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "", "amount": 100.00}}
      expected_result: "Error: IFSC code is required."

[2] TRANSACTION CONFIRMATION & UNIQUE ID

    Confirmation message shown after successful transfer:
      test_data: {{"beneficiary_account": "9876543210", "ifsc_code": "HDFC0001234", "amount": 250.00}}
      expected_result: "Confirmation message displayed with beneficiary, amount, and unique transaction ID."

    Transaction IDs are unique across multiple transfers:
      test_data: {{"transfer_1_amount": 100.00, "transfer_2_amount": 200.00}}
      steps: perform transfer 1 and record transaction ID; perform transfer 2 and record transaction ID;
             assert both IDs are different.
      expected_result: "Both transfers have distinct, non-duplicate transaction IDs."

    Balance updates correctly after successful transfer:
      test_data: {{"initial_balance": 1000.00, "transfer_amount": 300.00, "expected_balance": 700.00}}
      expected_result: "Dashboard shows updated balance of $700.00 immediately after transfer."

[3] NON-FUNCTIONAL REQUIREMENTS (NFR)

    API response time under 2 seconds:
      test_data: {{"endpoint": "/api/transfer", "method": "POST", "sla_seconds": 2}}
      steps: (1) Send a valid fund transfer API request. (2) Measure response time.
      expected_result: "API responds in under 2 seconds."

    Dashboard load time under 3 seconds:
      test_data: {{"action": "login and navigate to dashboard", "sla_seconds": 3}}
      steps: (1) Log in with valid credentials. (2) Start timer. (3) Wait for dashboard to fully render.
             (4) Stop timer.
      expected_result: "Dashboard fully rendered within 3 seconds."

    System handles 10,000 concurrent users:
      test_data: {{"concurrent_users": 10000, "test_duration_seconds": 60, "target_api": "/login", "tool": "JMeter or k6"}}
      steps: (1) Configure load test tool with 10,000 virtual users.
             (2) Run test for 60 seconds against /login endpoint.
             (3) Monitor response times and error rate.
      expected_result: "No crashes or 5xx errors; response times remain within SLA under full load."

    Sensitive data encrypted in transit:
      test_data: {{"capture_tool": "Wireshark or browser DevTools", "action": "login with credentials"}}
      steps: (1) Start network traffic capture. (2) Perform login. (3) Inspect captured packets.
      expected_result: "All traffic uses HTTPS; no plain-text credentials visible in network traffic."

    Graceful degradation above 10,000 users:
      test_data: {{"concurrent_users": 12000, "test_duration_seconds": 30, "target_api": "/login"}}
      expected_result: "System returns a graceful error or queuing response; no unhandled crashes."

[4] CROSS-BROWSER COMPATIBILITY
    For each browser below, cover the full critical path: login → fund transfer → logout.

    Chrome (latest):
      test_data: {{"browser": "Chrome", "version": "latest", "os": "Windows 10"}}
      expected_result: "All features work correctly on Chrome; no console errors."

    Firefox (latest):
      test_data: {{"browser": "Firefox", "version": "latest", "os": "Windows 10"}}
      expected_result: "All features work correctly on Firefox; no console errors."

    Edge (latest):
      test_data: {{"browser": "Edge", "version": "latest", "os": "Windows 10"}}
      expected_result: "All features work correctly on Edge; no console errors."

    Safari (latest):
      test_data: {{"browser": "Safari", "version": "latest", "os": "macOS"}}
      expected_result: "All features work correctly on Safari; no console errors."

[5] SECURE LOGOUT & OTP

    Explicit logout invalidates session server-side:
      test_data: {{"username": "john_doe", "password": "P@ssw0rd"}}
      steps: (1) Log in. (2) Note session cookie/token value. (3) Click logout.
             (4) Press browser back button. (5) Attempt direct URL access to dashboard.
      expected_result: "User is redirected to login; dashboard is inaccessible after logout."

    OTP required for transfer above $10,000:
      test_data: {{"amount": 10001.00, "otp_provided": false}}
      steps: (1) Log in. (2) Initiate transfer of $10,001. (3) Attempt to confirm without OTP.
      expected_result: "System blocks transfer and prompts for OTP before proceeding."

    OTP not triggered for transfer at exactly $10,000 (boundary):
      test_data: {{"amount": 10000.00, "otp_provided": false}}
      expected_result: "Transfer proceeds without OTP prompt (threshold is above $10,000, not at)."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD RULES (every object must have ALL fields):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- "id"                   : "TC_001" format, starting from TC_001 (will be re-numbered on merge)
- "module"               : use the most specific SRS section name e.g. "Fund Transfer", "Transaction Confirmation", "Cross-Browser", "NFR"
- "category"             : Functional | Negative | Boundary | Performance | Cross-Browser | Security | Edge
- "test_type"            : Happy Path | Negative | Boundary Value | Edge Case | Security | NFR | Regression
- "priority"             : Critical | High | Medium | Low
- "scenario"             : one clear sentence
- "preconditions"        : exact system state before test
- "steps"                : array of atomic strings — one action per step
- "test_data"            : object with real concrete values (no placeholders)
- "expected_result"      : precise, measurable, observable outcome
- "actual_result"        : "Pending"
- "status"               : "Not Executed"
- "risk_level"           : High | Medium | Low
- "automation_candidate" : boolean

Begin the JSON array immediately with [ on the first character.
""".strip()


# ─────────────────────────────────────────────
#  MERGE HELPER
# ─────────────────────────────────────────────

def merge_and_resequence(call1_json: str, call2_json: str) -> list:
    """
    Parse both JSON arrays, deduplicate by scenario, and re-number IDs
    from TC_001 sequentially.

    Args:
        call1_json : raw JSON string from Call 1
        call2_json : raw JSON string from Call 2

    Returns:
        list of merged, deduplicated, re-sequenced test case dicts
    """
    def safe_parse(raw: str, label: str) -> list:
        raw = raw.strip()
        # Strip accidental markdown code fences if the model added them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        # Ensure array is closed — model may truncate at token limit
        if not raw.endswith("]"):
            last_brace = raw.rfind("}")
            if last_brace != -1:
                raw = raw[: last_brace + 1] + "]"
                logger.warning(f"{label}: JSON was truncated — auto-closed at last complete object")
        try:
            data = json.loads(raw)
            logger.info(f"{label}: parsed {len(data)} test cases")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"{label}: JSON parse error — {e}")
            return []

    tcs1 = safe_parse(call1_json, "Call 1")
    tcs2 = safe_parse(call2_json, "Call 2")

    merged = tcs1 + tcs2

    # Deduplicate: keep first occurrence of each unique scenario
    seen_scenarios: set = set()
    unique: list = []
    for tc in merged:
        key = tc.get("scenario", "").strip().lower()
        if key and key not in seen_scenarios:
            seen_scenarios.add(key)
            unique.append(tc)
        elif not key:
            unique.append(tc)  # keep TCs with no scenario (shouldn't happen)

    # Re-sequence IDs TC_001, TC_002 ...
    for i, tc in enumerate(unique, start=1):
        tc["id"] = f"TC_{i:03d}"

    logger.info(
        f"Merge complete — Call 1: {len(tcs1)}, Call 2: {len(tcs2)}, "
        f"after dedup: {len(unique)} total TCs"
    )
    return unique


# ─────────────────────────────────────────────
#  PAYLOAD BUILDERS
# ─────────────────────────────────────────────

def _base_payload(system: str, user: str) -> dict:
    """Shared payload structure for both calls."""
    return {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens":  4000,
        "temperature": 0.2,
        "top_p":       0.9,
        "stream":      False,
    }


def build_prompt(
    requirement: str,
    tc_json_path: str = DEFAULT_TC_PATH,
    use_rag: bool = True,
) -> dict:
    """
    Original single-call interface — now returns CALL 1 payload only.
    Used for backwards compatibility if any caller expects a single dict.
    For full coverage use build_prompts_split() instead.
    """
    return build_prompts_split(requirement, tc_json_path, use_rag)["call1"]


def build_prompts_split(
    requirement: str,
    tc_json_path: str = DEFAULT_TC_PATH,
    use_rag: bool = True,
) -> dict:
    """
    Build TWO API payload dicts — one focused on functional core,
    one focused on the previously missing areas.

    Returns:
        {
            "call1": <payload dict for functional core>,
            "call2": <payload dict for gaps focus>,
        }

    Callers should:
        1. Send both payloads (sequentially or in parallel)
        2. Pass both raw response strings to merge_and_resequence()
        3. Write the resulting list to test_cases.json
    """
    logger.info("Building split prompt payloads (Call 1 + Call 2)")

    if not requirement or not requirement.strip():
        raise ValueError("Requirement text is empty. Cannot build prompts.")

    req = requirement.strip()

    # ── RAG examples (only injected into Call 1 — functional core benefits most) ──
    rag_block = ""
    if use_rag:
        try:
            retriever = TestCaseRetriever()
            added = retriever.index_test_cases(tc_json_path)
            if added > 0:
                logger.info(f"Knowledge base updated: {added} test cases indexed")

            stats = retriever.get_stats()
            logger.info(f"Knowledge base stats: {stats}")

            if stats["total_test_cases"] > 0:
                retrieved = retriever.retrieve(req, top_k=5)
                rag_block = format_examples_for_prompt(retrieved, max_examples=3)
                logger.info(f"RAG: injecting {min(3, len(retrieved))} examples into Call 1")
            else:
                logger.info("RAG: knowledge base empty — first run, no examples")

        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e} — continuing without examples")
            rag_block = ""

    rag_section = rag_block or "No reference examples available — generate from SRS alone."

    call1_user = PROMPT_CALL1.format(requirement=req, rag_examples=rag_section)
    call2_user = PROMPT_CALL2.format(requirement=req)

    call1_payload = _base_payload(SYSTEM_PROMPT, call1_user)
    call2_payload = _base_payload(SYSTEM_PROMPT, call2_user)

    logger.info(
        f"Payloads ready — model: {call1_payload['model']}, "
        f"max_tokens: {call1_payload['max_tokens']} each, "
        f"RAG: {'enabled' if rag_block else 'disabled/empty'}"
    )

    return {"call1": call1_payload, "call2": call2_payload}