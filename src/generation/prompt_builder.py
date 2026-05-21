import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  SYSTEM PROMPT  —  Senior Test Engineer Persona
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Principal QA Engineer with 15+ years of experience in enterprise software testing
across banking, fintech, healthcare, e-commerce, and SaaS platforms.

You specialise in:
- IEEE 829 / ISO 29119 test documentation standards
- Risk-based testing and coverage analysis
- OWASP Top 10 security test design
- Regulatory compliance testing (PCI-DSS, GDPR, HIPAA, SOX)
- Performance and load test scenario design
- Accessibility testing (WCAG 2.1 AA)

Your test cases are used directly by QA teams in production pipelines.
They must be precise, unambiguous, executable, and complete.
Every single test case object MUST contain ALL required fields — never omit a field.
Never truncate your response mid-object. If you reach a limit, close the JSON array cleanly.
""".strip()


# ─────────────────────────────────────────────
#  USER PROMPT TEMPLATE
# ─────────────────────────────────────────────

PROMPT_TEMPLATE = """
You are given a Software Requirements Specification (SRS) document below.

Your task is to generate a COMPREHENSIVE, PRODUCTION-GRADE test suite that achieves
maximum requirements coverage across ALL testing dimensions listed in the TESTING MANDATE.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SRS DOCUMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{requirement}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TESTING MANDATE — You MUST cover ALL of the following:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] FUNCTIONAL TESTING
    - Happy path for every stated user action
    - All CRUD operations where applicable
    - Every business rule and validation constraint
    - Each stated success confirmation and feedback message
    - Every workflow from entry point to completion

[2] NEGATIVE TESTING
    - Invalid input for every input field (wrong type, wrong format, out-of-range values)
    - Missing required fields (individually and in combination)
    - Boundary value violations (one below min, one above max)
    - Duplicate submission attempts
    - Operations on non-existent or deleted resources

[3] BOUNDARY VALUE ANALYSIS
    - Exact minimum valid value
    - Exact maximum valid value
    - One below minimum (invalid)
    - One above maximum (invalid)
    - Zero and null values where applicable

[4] EDGE CASES & STATE TRANSITIONS
    - Concurrent/simultaneous operations (e.g. double-click submit)
    - Operations at system limits (max users, max balance, max file size)
    - Re-entry after error (user corrects and resubmits)
    - Interrupted flows (close browser mid-transaction, network loss)
    - Expired sessions mid-flow

[5] SECURITY TESTING (OWASP Top 10)
    - SQL Injection in every input field — test_data MUST contain the actual payload
      e.g.  {{"username": "' OR '1'='1' --", "password": "anything"}}
    - Cross-Site Scripting (XSS) reflected — test_data MUST contain the script tag
      e.g. {{"input": "<script>alert('XSS')</script>"}}
    - Cross-Site Scripting (XSS) stored — inject payload, then verify it does NOT execute on retrieval
    - CSRF — submit a state-changing request without a valid CSRF token and verify rejection
      test_data MUST include {{"csrf_token": "invalid_or_missing"}}
    - Brute force / rate limiting — simulate N rapid failed attempts and verify lockout triggers
      test_data MUST include {{"attempt_count": 10, "interval_seconds": 5}}
    - Session fixation — set a known session ID before login, verify server regenerates it after auth
      test_data MUST include {{"pre_login_session_id": "ATTACKER_FIXED_SESSION_ABC123"}}
    - Session hijacking — attempt to reuse a session token after logout
      test_data MUST include {{"stolen_session_token": "eyJhbGciOiJIUzI1NiJ9.stolen"}}
    - IDOR — access another user's resource by manipulating the resource ID in the URL
      test_data MUST include {{"target_account_id": "OTHER_USER_ACCOUNT_99999"}}
    - Privilege escalation — use a regular-user token to call an admin-only endpoint
      test_data MUST include {{"user_role": "customer", "target_endpoint": "/admin/users"}}
    - Sensitive data exposure — verify passwords/tokens never appear in logs, URLs, or API responses
    - JWT expiry — use an expired token and verify the server returns 401

[6] AUTHENTICATION & AUTHORISATION
    - Valid login with correct credentials
    - Login with each type of invalid credential
    - Account lockout policy enforcement
    - Password policy enforcement (length, complexity, each rule separately)
    - Role-based access control — each role can only access permitted resources
    - Logout clears session completely
    - Automatic session timeout after inactivity
    - Remember-me / persistent session behaviour

[7] PERFORMANCE & NON-FUNCTIONAL
    - Page / API response time within stated SLA
    - Behaviour under stated concurrent user load
    - Graceful degradation when load exceeds limit
    - Large data set rendering (e.g. 10,000 row transaction history)

[8] UI / UX VALIDATION
    - Required field indicators present
    - Inline validation messages appear at correct trigger point (on blur / on submit)
    - Error messages are user-friendly, specific, and actionable
    - Success messages confirm the correct action
    - Loading states / spinners shown during async operations
    - Disabled state of submit button while processing (prevent double submit)

[9] CROSS-BROWSER & CROSS-DEVICE
    - Chrome (latest)
    - Firefox (latest)
    - Safari (latest)
    - Edge (latest)
    - Mobile viewport — iOS Safari and Android Chrome

[10] ACCESSIBILITY (WCAG 2.1 AA)
    - All interactive elements keyboard navigable
    - Screen reader announces form errors correctly
    - Colour contrast meets AA standard
    - Focus indicators visible on all interactive elements

[11] DATA INTEGRITY & PERSISTENCE
    - Data saved correctly matches data entered
    - Calculations (totals, balances) are mathematically correct
    - Audit trail / transaction log created for state-changing operations
    - Data survives page refresh mid-flow where expected

[12] ERROR HANDLING & RECOVERY
    - System displays user-friendly message for all error states
    - Logs generated for every failed transaction / system error
    - Retry mechanism works correctly after transient failure
    - User is not double-charged / double-processed on retry

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT OUTPUT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Output ONLY a valid JSON array. No prose, no markdown, no explanation before or after.
2. Every object MUST contain ALL of these fields — never omit any:
   - "id"              : string  — format TC_001, TC_002 ... TC_NNN (zero-padded to 3 digits)
   - "module"          : string  — the SRS section this test belongs to (e.g. "User Login", "Fund Transfer")
   - "category"        : string  — one of: Functional | Negative | Boundary | Edge | Security | Performance | UI | Accessibility | Cross-Browser | Data Integrity | Error Handling
   - "test_type"       : string  — one of: Happy Path | Negative | Boundary Value | Edge Case | Security | NFR | Regression
   - "priority"        : string  — one of: Critical | High | Medium | Low
   - "scenario"        : string  — one clear sentence describing what is being tested
   - "preconditions"   : string  — exact state the system must be in before the test starts
   - "steps"           : array of strings — numbered, atomic, executable steps (no ambiguity)
   - "test_data"       : object  — concrete input values to use (e.g. {{"username": "test@bank.com", "password": "P@ssw0rd!"}})
   - "expected_result" : string  — precise, measurable, observable outcome
   - "actual_result"   : string  — always set to "Pending"
   - "status"          : string  — always set to "Not Executed"
   - "risk_level"      : string  — one of: High | Medium | Low — based on business impact if this fails
   - "automation_candidate" : boolean — true if this test is suitable for automation

3. The "steps" array must be granular. Each step is ONE action. No compound steps like
   "Enter username and password" — these must be two separate steps.

4. "test_data" must contain REAL, CONCRETE values — not placeholders like "<valid email>".
   Use realistic-looking fake data: emails like "amara.okonkwo@testbank.com",
   amounts like 5000.00, IBANs like "DE89370400440532013000".

5. Cover EVERY module mentioned in the SRS. Do not silently skip any section.

6. If the JSON array would be very long, prioritise Critical and High priority test cases first,
   then Medium, then Low — but always close the JSON array properly with ] at the end.

7. Never truncate a test case object mid-way. Either include it fully or omit it entirely.

8. DEDUPLICATION — Before writing each test case, check: does an existing TC already have
   the same scenario AND the same test_data values?
   If yes, DO NOT repeat it. Instead vary the attack vector, field under test, or condition.
   Duplicate test cases waste execution time and signal poor test design.
   Examples of what counts as a duplicate:
   - Two SQL injection TCs both injecting "' OR '1'='1'" into the username field = DUPLICATE
   - Two performance TCs both asserting "login completes within 3 seconds" = DUPLICATE
   - Two XSS TCs both using "<script>alert('XSS')</script>" in the same field = DUPLICATE

9. MANDATORY MODULES — Generate at least one test case for EACH of the following before
   generating any other category. These are non-negotiable and must appear in the output
   even if the SRS does not mention them explicitly:

   [M1] Session timeout
        Scenario: User is automatically logged out after 10 minutes of inactivity.
        test_data: {{"inactivity_duration_minutes": 10, "action_after_timeout": "navigate to dashboard"}}

   [M2] Transaction history
        Scenario: Logged-in user views their full transaction history.
        test_data: {{"username": "amara.okonkwo@testbank.com", "expected_transaction_count": 25}}

   [M3] Concurrent load
        Scenario: System handles 10,000 simultaneous users without degradation.
        test_data: {{"concurrent_users": 10000, "test_duration_seconds": 60, "target_api": "/login"}}

   [M4] Cross-browser — one TC per browser
        Browsers: Chrome 124, Firefox 125, Safari 17, Edge 124
        test_data must include {{"browser": "Chrome 124", "version": "124.0"}} etc.

   [M5] Accessibility
        Scenario: All login form fields are navigable by keyboard alone (no mouse).
        test_data: {{"input_method": "keyboard_only", "assistive_technology": "VoiceOver/NVDA"}}
        Scenario: Screen reader correctly announces validation error on invalid login.
        test_data: {{"screen_reader": "NVDA", "trigger": "submit empty form"}}

Begin the JSON array immediately with [ on the first character of your response.
""".strip()


# ─────────────────────────────────────────────
#  PAYLOAD BUILDER
# ─────────────────────────────────────────────

def build_prompt(requirement: str) -> dict:
    """
    Build the full API payload for the LLM.
    Accepts a plain-text or PDF-extracted requirement string.
    Returns a dict ready to pass to call_api().
    """
    logger.info("Building prompt payload")

    if not requirement or not requirement.strip():
        raise ValueError("Requirement text is empty. Cannot build prompt.")

    user_message = PROMPT_TEMPLATE.format(requirement=requirement.strip())

    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "max_tokens": 10000,
        "temperature": 0.2,       # Low temp = consistent, deterministic test cases
        "top_p": 0.9,
        "stream": False
    }

    logger.info(f"Prompt payload created — model: {payload['model']}, max_tokens: {payload['max_tokens']}")
    return payload