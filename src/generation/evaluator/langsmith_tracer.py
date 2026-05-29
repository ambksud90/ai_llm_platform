from langsmith import Client
from datetime import datetime, timezone
import os


def trace_generation(requirement: str, generated_cases: list) -> None:

    client = Client(api_key=os.getenv("LANGCHAIN_API_KEY"))

    start = datetime.now(timezone.utc)

    run = client.create_run(
        name="test_case_generation",
        run_type="chain",
        project_name=os.getenv("LANGCHAIN_PROJECT", "QA-TestCase-Agent"),
        inputs={"requirement_length": len(requirement)},
        start_time=start,
    )

    client.update_run(
        run.id,
        outputs={
            "cases_generated": len(generated_cases),
            "case_ids": [c.get("id") for c in generated_cases],
        },
        end_time=datetime.now(timezone.utc),
    )