import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.generation.pdf_loader import extract_pdf_text
from src.generation.orchestrator import generate_all_modules
from src.generation.retriever import TestCaseRetriever
from src.generation.validator.pipeline import (
    validate_test_suite
)
from src.generation.validator.summary import (
    generate_test_summary
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="AI QA Test Generator",
    layout="wide"
)

st.title("AI-Powered QA Test Case Generator")

st.markdown(
    """
Generate intelligent QA test cases from
Software Requirement Specifications using:

- RAG Retrieval
- LLM Generation
- Validation Pipelines
- Coverage Analysis
"""
)

# ─────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "Upload SRS PDF",
    type=["pdf"]
)

# ─────────────────────────────────────────────
# GENERATE BUTTON
# ─────────────────────────────────────────────

if uploaded_file:

    if st.button("Generate Test Cases"):

        with st.spinner(
            "Generating test cases..."
        ):

            # Save uploaded file temporarily

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(
                    uploaded_file.read()
                )

                pdf_path = tmp.name

            # ─────────────────────────────
            # LOAD REQUIREMENTS
            # ─────────────────────────────

            requirement = extract_pdf_text(
                pdf_path
            )

            # ─────────────────────────────
            # INITIALISE RAG
            # ─────────────────────────────

            retriever = TestCaseRetriever()

            # ─────────────────────────────
            # GENERATE TEST CASES
            # ─────────────────────────────

            raw_cases = generate_all_modules(
                requirement=requirement,
                retriever=retriever,
                delay_between_calls=10
            )

            # ─────────────────────────────
            # VALIDATION
            # ─────────────────────────────

            result = validate_test_suite(
                raw_cases
            )

            approved_cases = result[
                "approved_cases"
            ]

            # ─────────────────────────────
            # SUMMARY
            # ─────────────────────────────

            summary = generate_test_summary(
                approved_cases
            )

            # ─────────────────────────────
            # METRICS
            # ─────────────────────────────

            st.success(
                "Generation completed!"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Approved Cases",
                    summary[
                        "total_test_cases"
                    ]
                )

            with col2:
                st.metric(
                    "Modules Covered",
                    len(
                        summary[
                            "module_summary"
                        ]
                    )
                )

            with col3:
                st.metric(
                    "Categories Covered",
                    len(
                        summary[
                            "category_summary"
                        ]
                    )
                )

            # ─────────────────────────────
            # MODULE SUMMARY
            # ─────────────────────────────

            st.subheader(
                "Coverage by Module"
            )

            module_df = pd.DataFrame(

                summary[
                    "module_summary"
                ].items(),

                columns=[
                    "Module",
                    "Count"
                ]
            )

            st.dataframe(
                module_df,
                use_container_width=True
            )

            # ─────────────────────────────
            # CATEGORY SUMMARY
            # ─────────────────────────────

            st.subheader(
                "Coverage by Category"
            )

            category_df = pd.DataFrame(

                summary[
                    "category_summary"
                ].items(),

                columns=[
                    "Category",
                    "Count"
                ]
            )

            st.dataframe(
                category_df,
                use_container_width=True
            )

            # ─────────────────────────────
            # TEST CASE TABLE
            # ─────────────────────────────

            st.subheader(
                "Generated Test Cases"
            )

            df = pd.DataFrame(
                approved_cases
            )

            st.dataframe(
                df,
                use_container_width=True
            )

            # ─────────────────────────────
            # DOWNLOAD JSON
            # ─────────────────────────────

            json_data = json.dumps(
                approved_cases,
                indent=2
            )

            st.download_button(

                label="Download JSON",

                data=json_data,

                file_name="test_cases.json",

                mime="application/json"
            )