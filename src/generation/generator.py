import json
import time
import requests

# ── Config ────────────────────────────────────────────────────────────────────
HF_TOKEN = "Your_HuggingFace_API_Token_Here"  # Replace with your actual token

API_URL  = "https://router.huggingface.co/v1/chat/completions"   
MODEL = "Qwen/Qwen2.5-72B-Instruct"

HEADERS  = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type":  "application/json",
}

# ── Requirement ───────────────────────────────────────────────────────────────
requirement = """
User can reset password using email OTP:
- User requests a password reset from the login page
- System sends a 6-digit OTP to the registered email
- OTP expires after 10 minutes
- User enters the OTP and sets a new password
"""

# ── Payload ───────────────────────────────────────────────────────────────────
PAYLOAD = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": (
                "You are a senior QA engineer. When given a software requirement, "
                "generate structured test cases as a valid JSON array only. "
                "Never include markdown fences or any text outside the JSON array."
            ),
        },
        {
            "role": "user",
            "content": f"""Generate 5 test cases for the requirement below.

Requirement:
{requirement}

Return a JSON array where each object has exactly these keys:
- "id"       : string like "TC-001"
- "scenario" : short test case title
- "type"     : one of "Functional", "Negative", "Edge Case", "Security"
- "priority" : one of "High", "Medium", "Low"
- "steps"    : list of action strings
- "expected" : expected result string

Return ONLY the JSON array. No explanation, no markdown.""",
        },
    ],
    "max_tokens":  1200,
    "temperature": 0.3,
}


# ── Call API with retry ───────────────────────────────────────────────────────
def call_api(retries: int = 3, wait: int = 25) -> str:
    for attempt in range(1, retries + 1):
        print(f"Attempt {attempt}/{retries} — model: {MODEL}")
        resp = requests.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=90)

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()

        if resp.status_code == 503:
            print(f"  Model loading (503) — waiting {wait}s...")
            time.sleep(wait)
            continue

        print(f"  Status : {resp.status_code}")
        print(f"  Detail : {resp.text[:300]}")
        raise RuntimeError(f"API error {resp.status_code}")

    raise RuntimeError("Model unavailable after all retries.")


# ── Parse JSON safely ─────────────────────────────────────────────────────────
def extract_json(text: str) -> list[dict]:
    if "```" in text:
        for part in text.split("```"):
            cleaned = part.lstrip("json").strip()
            if cleaned.startswith("["):
                text = cleaned
                break
    start, end = text.find("["), text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array in model output.")
    return json.loads(text[start:end])


# ── Pretty Print ──────────────────────────────────────────────────────────────
def print_test_cases(cases: list[dict]) -> None:
    SEP = "─" * 64
    print(f"\n{'═' * 64}")
    print(f"  GENERATED TEST CASES  ({len(cases)} total)")
    print(f"{'═' * 64}")
    for tc in cases:
        print(f"\n{SEP}")
        print(f"  [{tc.get('id','—')}]  {tc.get('scenario','')}")
        print(f"  Type: {tc.get('type','—')}    Priority: {tc.get('priority','—')}")
        print(SEP)
        print("  Steps:")
        for i, step in enumerate(tc.get("steps", []), 1):
            print(f"    {i}. {step}")
        print(f"\n  Expected: {tc.get('expected','—')}\n")


# ── Main ──────────────────────────────────────────────────────────────────────
try:
    raw = call_api()
    test_cases = extract_json(raw)
    print_test_cases(test_cases)

    with open("test_cases.json", "w") as f:
        json.dump(test_cases, f, indent=2)
    print("Saved to test_cases.json")

except (json.JSONDecodeError, ValueError) as e:
    print(f"JSON parse error: {e}\nRaw output:\n{raw}")
except RuntimeError as e:
    print(f"Error: {e}")