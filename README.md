#  AI-Powered RAG Test Case Generator


**Enterprise AI platform for intelligent test case generation and evaluation using LLMs and RAG.**

Given a plain-language software requirement, the platform calls an LLM, parses the structured response, and outputs a formatted, saved set of test cases ,ready for QA pipelines or manual review.
=======
> Automatically generate structured, grounded, and evaluated test cases from Software Requirement Specification (SRS) documents using RAG pipelines, LLMs, and multi-layer AI evaluation.


---

##  What it does

Upload a requirements PDF — get back a complete, validated test suite in seconds.

This tool doesn't just wrap an LLM. It implements a full GenAI engineering pipeline: it parses your SRS, builds a semantic knowledge base, retrieves relevant context, generates structured test cases, and then evaluates each one for quality, completeness, and hallucinations — all before anything reaches your screen.

---

##  Architecture

```
SRS PDF
  │
  ▼
Requirement Parser      ← PDF extraction + text chunking
  │
  ▼
Embedding Model         ← Sentence Transformers
  │
  ▼
Vector Store            ← Semantic similarity index
  │
  ▼
RAG Retriever           ← Context-aware retrieval
  │
  ▼
LLM Generator           ← Structured JSON test case generation
  │
  ├──────────────────────────────────┐
  ▼                ▼                 ▼
Schema Validator   Hallucination     Quality Scorer
                   Detector
  │
  ▼
Deduplication Engine
  │
  ▼
Final Test Suite (JSON)
  │
  ▼
Streamlit UI
```

---

##  Features

- **RAG-powered generation** — test cases are grounded in your actual requirements, not hallucinated from thin air
- **Multi-layer evaluation** — every generated test case is scored for schema validity, completeness, automation suitability, and requirement grounding
- **Hallucination detection** — semantic similarity scoring flags unsupported or invented test steps
- **Deduplication engine** — removes redundant cases before output
- **Structured JSON output** — ready for import into test management tools
- **Streamlit UI** — drag-and-drop SRS upload, live pipeline progress, and result dashboard
- **LangSmith observability** — full LLM tracing, token analysis, and prompt monitoring

---

##  Tech Stack

| Layer | Technologies |
|---|---|
| LLM APIs | Groq, Gemini / OpenAI-compatible |
| Embeddings | `sentence-transformers`, HuggingFace Transformers |
| Vector Search | FAISS / ChromaDB |
| Document Processing | PDF loaders, text extraction pipelines |
| Evaluation | Custom schema + hallucination + quality evaluators |
| Observability | LangSmith |
| UI | Streamlit |
| Language | Python 3.10+ |

---

##  Installation

### Prerequisites

- Python 3.10+
- An API key for your chosen LLM provider (Groq, Gemini, or OpenAI-compatible)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/your-username/ai-test-case-generator.git
cd ai-test-case-generator

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Environment variables

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key       # optional
LANGSMITH_API_KEY=your_langsmith_key     # optional, for tracing
LANGSMITH_PROJECT=your_project_name      # optional
```

---

##  Running the app

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

> **Note:** On first run, the embedding model downloads automatically (~90MB). Subsequent runs use the cached model.

---

## How the pipeline works

### 1. Document ingestion
The SRS PDF is parsed, cleaned, and split into semantic chunks. Each chunk is embedded using a Sentence Transformer model and stored in a vector index.

### 2. Context retrieval (RAG)
For each test area being generated, the most relevant requirement chunks are retrieved via cosine similarity search and injected into the LLM prompt as grounding context.

### 3. Test case generation
A structured system prompt instructs the LLM to generate test cases as valid JSON, covering happy paths, negative scenarios, boundary values, security, and accessibility.

### 4. Evaluation pipeline
Each generated test case passes through three evaluators:

| Evaluator | What it checks |
|---|---|
| Schema validator | Required fields, correct types, no missing data |
| Quality scorer | Test depth, completeness, automation suitability |
| Hallucination detector | Grounding score vs. SRS embeddings, unsupported content |

### 5. Deduplication + output
Near-duplicate test cases are removed. The final validated suite is returned as structured JSON and visualised in the UI.

---

## 📊 Evaluation metrics

Each test case receives scores across four dimensions:

- **Schema score** — are all required fields present and correctly typed?
- **Completeness score** — does it have preconditions, steps, test data, and expected results?
- **Automation suitability** — can this case be automated, and is it written to support that?
- **Grounding score** — how semantically similar is the test case to the source requirements? Low scores flag potential hallucinations.

---

## 🗂️ Project structure

```
ai-test-case-generator/
├── app.py                   # Streamlit entry point
├── pipeline/
│   ├── parser.py            # PDF ingestion + chunking
│   ├── embedder.py          # Sentence Transformer embedding
│   ├── retriever.py         # Vector similarity search
│   ├── generator.py         # LLM test case generation
│   └── evaluator.py         # Schema + quality + hallucination eval
├── utils/
│   ├── deduplicator.py      # Duplicate detection
│   └── json_repair.py       # LLM output parsing + repair
├── prompts/
│   └── system_prompt.py     # Prompt templates
├── requirements.txt
├── .env.example
└── README.md
```

---

##  Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

```bash
# Run with hot-reload for development
streamlit run app.py --server.runOnSave true
```



##  Author

Built by [Ambika Sudhakar]

