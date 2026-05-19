# Readme · MDCopyai_llm_platform
Enterprise AI platform for intelligent test case generation and evaluation using LLMs and RAG.
Given a plain-language software requirement, the platform calls an LLM, parses the structured response, and outputs a formatted, saved set of test cases — ready for QA pipelines or manual review.

Table of Contents

Overview
Architecture
Project Structure
Getting Started
Usage
Sample Output
Configuration
Roadmap
Tech Stack


Overview
Manual test case creation is slow and inconsistent. This platform automates it: you describe a software requirement in natural language, and the LLM generates structured, actionable test cases covering happy paths, edge cases, and failure scenarios.
Core capabilities:

Dynamic prompt construction from user-supplied requirements
LLM API integration for test case generation
Structured JSON output parsing and validation
Formatted terminal display + file persistence
Modular, extensible architecture (generation pipeline, RAG evaluation — coming soon)


Architecture
User Input (requirement)
        │
        ▼
┌─────────────────┐
│  prompt_builder │  Constructs structured LLM prompt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   api_client    │  Calls LLM API (e.g. HuggingFace / OpenAI-compatible)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     parser      │  Extracts and validates JSON from LLM response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   formatter     │  Prints test cases to terminal
└────────┬────────┘
         │
         ▼
  outputs/test_cases.json

Project Structure
ai_llm_platform/
├── src/
│   └── generation/
│       ├── main.py            # Pipeline entry point
│       ├── api_client.py      # LLM API call handler
│       ├── prompt_builder.py  # Dynamic prompt construction
│       ├── parser.py          # JSON extraction from LLM response
│       └── formatter.py       # Terminal output formatting
├── outputs/
│   └── test_cases.json        # Generated test cases (auto-saved)
├── requirements.txt
├── .gitignore
└── README.md

Getting Started
Prerequisites

Python 3.10+
A HuggingFace API token (or compatible LLM API key)

Installation
bash# Clone the repository
git clone https://github.com/ambksud90/ai_llm_platform.git
cd ai_llm_platform

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
Environment Setup
Create a .env file in the root directory (see .env.example):
bashcp .env.example .env
Fill in your API credentials:
envHF_API_TOKEN=your_huggingface_token_here
MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2   # or your preferred model
API_BASE_URL=https://api-inference.huggingface.co/models

Usage
bashcd src/generation
python main.py
You will be prompted to enter a software requirement:
Enter software requirement:

> User should be able to log in with email and password
The pipeline will call the LLM, parse the response, display the test cases in the terminal, and save them to outputs/test_cases.json.

Sample Output
json[
  {
    "test_id": "TC_001",
    "title": "Successful login with valid credentials",
    "preconditions": "User account exists with verified email",
    "steps": [
      "Navigate to login page",
      "Enter valid email address",
      "Enter correct password",
      "Click 'Login' button"
    ],
    "expected_result": "User is authenticated and redirected to dashboard",
    "category": "Happy Path"
  },
  {
    "test_id": "TC_002",
    "title": "Login fails with incorrect password",
    "preconditions": "User account exists",
    "steps": [
      "Navigate to login page",
      "Enter valid email address",
      "Enter incorrect password",
      "Click 'Login' button"
    ],
    "expected_result": "Error message displayed: 'Invalid credentials'",
    "category": "Negative Test"
  }
]

Configuration
VariableDescriptionDefaultHF_API_TOKENHuggingFace API tokenRequiredMODEL_NAMELLM model to usemistralai/Mistral-7B-Instruct-v0.2API_BASE_URLAPI endpoint base URLHuggingFace Inference API

Roadmap

 LLM-based test case generation pipeline
 Modular architecture (api_client, parser, formatter, prompt_builder)
 JSON output persistence
 RAG module — retrieve relevant test case examples to improve generation quality
 Evaluation module — score generated test cases for coverage and correctness
 REST API / FastAPI interface
 Support for multiple LLM providers (OpenAI, Anthropic, local models via Ollama)
 CI/CD pipeline with GitHub Actions


Tech Stack
LayerTechnologyLanguagePython 3.10+LLM FrameworkHuggingFace Transformers, LangChainModelsMistral, LLaMA (via HuggingFace Inference API)ML LibrariesPyTorch, Tokenizers, SafetensorsExperiment TrackingWeights & Biases, TensorBoardContainerisationDocker (coming soon)OutputJSON

Author
Ambika Sudhakar — Data & AI Engineer
MSc Artificial Intelligence, FAU Erlangen-Nürnberg
LinkedIn · GitHubai_llm_platform
Enterprise AI platform for intelligent test case generation and evaluation using LLMs and RAG.
