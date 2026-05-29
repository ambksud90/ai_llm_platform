import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

# Lightweight local embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Persistent Chroma database location
CHROMA_DB_PATH = (
    Path(__file__).parent.parent.parent
    / "knowledge_base"
    / "chroma_db"
)

# Chroma collection
COLLECTION_NAME = "test_case_library"

# Default retrieval size
TOP_K = 5

# Similarity threshold
SIMILARITY_THRESHOLD = 0.65


# ─────────────────────────────────────────────
# RETRIEVER CLASS
# ─────────────────────────────────────────────

class TestCaseRetriever:

    def __init__(self):

        logger.info("Initialising RAG retriever...")

        # Load embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")

        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # Create DB directory if missing
        CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

        # Persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH)
        )

        # Create / load collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(
            f"RAG retriever ready — "
            f"{self.collection.count()} test cases in KB"
        )

    # ─────────────────────────────────────────
    # INDEX TEST CASES
    # ─────────────────────────────────────────

    def index_test_cases(self, json_path: str) -> int:

        path = Path(json_path)

        if not path.exists():

            logger.warning(
                f"Test case file not found: {json_path}"
            )

            return 0

        # Load JSON
        with open(path, "r") as f:

            test_cases = json.load(f)

        if not isinstance(test_cases, list):

            logger.warning("Invalid test case JSON structure")

            return 0

        if len(test_cases) == 0:

            logger.warning("No test cases found")

            return 0

        logger.info(
            f"Indexing {len(test_cases)} test cases..."
        )

        ids = []
        documents = []
        metadatas = []

        for tc in test_cases:

            # Original TC ID
            tc_id = tc.get("id", "UNKNOWN")

            # Generate UNIQUE vector DB ID
            unique_id = f"{tc_id}_{uuid.uuid4().hex[:8]}"

            # Build richer semantic fingerprint
            steps_text = " ".join(
                tc.get("steps", [])
            )

            fingerprint = f"""
            Module: {tc.get('module', '')}

            Category: {tc.get('category', '')}

            Type: {tc.get('test_type', '')}

            Scenario:
            {tc.get('scenario', '')}

            Expected Result:
            {tc.get('expected_result', '')}

            Execution Steps:
            {steps_text}
            """

            ids.append(unique_id)

            documents.append(fingerprint)

            metadatas.append({

                "id": tc_id,

                "module": tc.get("module", ""),

                "category": tc.get("category", ""),

                "test_type": tc.get("test_type", ""),

                "priority": tc.get("priority", ""),

                "scenario": tc.get("scenario", ""),

                "quality_score": tc.get(
                    "quality_score",
                    0
                ),

                "source_file": str(path.name),

                "indexed_at": datetime.now().isoformat(),

                "full_tc": json.dumps(tc)
            })

        # Generate embeddings
        embeddings = self.embedder.encode(
            documents,
            show_progress_bar=False
        ).tolist()

        # Upsert into Chroma
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(
            f"Successfully indexed {len(ids)} test cases"
        )

        return len(ids)

    # ─────────────────────────────────────────
    # RETRIEVE SIMILAR TEST CASES
    # ─────────────────────────────────────────

    def retrieve(
        self,
        srs_text: str,
        top_k: int = TOP_K
    ) -> list[dict]:

        if self.collection.count() == 0:

            logger.warning(
                "Knowledge base empty"
            )

            return []

        # Enriched retrieval query
        query_text = f"""
        Software testing requirements:

        {srs_text}

        Focus on:
        functional testing,
        security testing,
        negative testing,
        performance testing,
        boundary testing,
        accessibility testing
        """

        # Generate query embedding
        query_embedding = self.embedder.encode(
            query_text
        ).tolist()

        actual_top_k = min(
            top_k,
            self.collection.count()
        )

        # Query vector DB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_top_k,
            include=["metadatas", "distances"]
        )

        retrieved = []

        for metadata, distance in zip(
            results["metadatas"][0],
            results["distances"][0]
        ):

            similarity = round(
                1 - distance,
                3
            )

            tc = json.loads(
                metadata["full_tc"]
            )

            tc["_similarity_score"] = similarity

            tc["_quality_score"] = metadata.get(
                "quality_score",
                0
            )

            # Filter irrelevant results
            if similarity >= SIMILARITY_THRESHOLD:

                retrieved.append(tc)

        # Sort by quality + similarity
        retrieved.sort(
            key=lambda x: (
                x.get("_quality_score", 0),
                x.get("_similarity_score", 0)
            ),
            reverse=True
        )

        if retrieved:

            logger.info(
                f"Retrieved {len(retrieved)} relevant test cases "
                f"(best similarity: "
                f"{retrieved[0]['_similarity_score']})"
            )

        else:

            logger.info(
                "No sufficiently relevant test cases found"
            )

        return retrieved

    # ─────────────────────────────────────────
    # KB STATS
    # ─────────────────────────────────────────

    def get_stats(self) -> dict:

        return {

            "total_test_cases":
                self.collection.count(),

            "embedding_model":
                EMBEDDING_MODEL,

            "collection":
                COLLECTION_NAME,

            "db_path":
                str(CHROMA_DB_PATH)
        }


# ─────────────────────────────────────────────
# FORMAT RETRIEVED EXAMPLES
# ─────────────────────────────────────────────

def format_examples_for_prompt(
    retrieved_tcs: list[dict],
    max_examples: int = 3
) -> str:

    if not retrieved_tcs:

        return ""

    examples = retrieved_tcs[:max_examples]

    lines = [
        "REFERENCE TEST CASE EXAMPLES",
        "=" * 60
    ]

    for i, tc in enumerate(examples, 1):

        similarity = tc.get(
            "_similarity_score",
            "N/A"
        )

        quality = tc.get(
            "_quality_score",
            0
        )

        # Remove internal metadata
        clean_tc = {
            k: v for k, v in tc.items()
            if not k.startswith("_")
        }

        lines.append(
            f"\nExample {i}"
        )

        lines.append(
            f"Similarity Score: {similarity}"
        )

        lines.append(
            f"Quality Score: {quality}"
        )

        lines.append(
            json.dumps(clean_tc, indent=2)
        )

        lines.append("-" * 60)

    lines.append(
        "Generate NEW test cases following the same structure, "
        "completeness, and quality level."
    )

    lines.append(
        "Do NOT duplicate these examples."
    )

    return "\n".join(lines)