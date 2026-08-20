"""Generate reproducible Week 8 local-CI RAG closeout evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.rag.chunker import Chunker
from ai.rag.embedder import Embedder
from ai.rag.rag_pipeline import RAGPipeline
from ai.rag.retriever import Retriever
from ai.rag.vector_store import VectorStore


SOURCE_FILES = (
    "ai/rag/rag_pipeline.py",
    "ai/rag/retriever.py",
    "ai/rag/vector_store.py",
    "ai/rag/scripts/week8_generate_rag_evidence.py",
)
DOCUMENT_ID = "doc_dataflow_technical_report"
FILE_NAME = "DataFlow_Technical_Report.pdf"
QUESTION = "What is the DataFlow pipeline?"
DOCUMENT_TEXT = (
    "The DataFlow pipeline consists of three main stages: ingestion, processing, and output. "
    "The ingestion stage collects and validates raw data from databases, APIs, and file systems. "
    "The processing stage transforms data using ETL operations and applies business rules. "
    "The output stage delivers processed data to downstream systems and generates reports. "
    "Data quality checks, logging, and lineage metadata are preserved throughout the pipeline. "
    "This evidence document intentionally contains enough detail to exercise deterministic "
    "chunking, retrieval, citation validation, and duplicate-safe repeated indexing."
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _source_hash() -> str:
    digest = hashlib.sha256()
    for relative_path in SOURCE_FILES:
        blob = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(blob)
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_citations(response: dict) -> list[str]:
    chunks = {item["chunk_id"]: item for item in response["retrieved_chunks"]}
    errors: list[str] = []
    for citation in response["citations"]:
        chunk = chunks.get(citation.get("chunk_id"))
        if chunk is None:
            errors.append(f"missing retrieved chunk: {citation.get('chunk_id')}")
            continue
        if citation.get("file_name") != chunk.get("file_name"):
            errors.append(f"file mismatch: {citation.get('chunk_id')}")
        if citation.get("page_number") != chunk.get("page_number"):
            errors.append(f"page mismatch: {citation.get('chunk_id')}")
        if abs(float(citation.get("similarity", 0)) - float(chunk.get("similarity_score", 0))) > 1e-12:
            errors.append(f"similarity mismatch: {citation.get('chunk_id')}")
    return errors


def generate(output_root: Path) -> dict:
    embedder = Embedder(model_name="ci-token-hash-384", mode="deterministic")
    vector_store = VectorStore(use_pgvector=False)
    chunker = Chunker(chunk_size=512, overlap=20)
    retriever = Retriever(embedder=embedder, vector_store=vector_store, top_k=3)
    pipeline = RAGPipeline(
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        retriever=retriever,
        chunk_size=512,
        overlap=20,
        top_k=3,
    )

    metadata = {
        "file_name": FILE_NAME,
        "source": FILE_NAME,
        "document_external_id": DOCUMENT_ID,
        "page_number": 4,
    }
    before = len(vector_store.in_memory_store)
    first = pipeline.ingest_document(DOCUMENT_TEXT, DOCUMENT_ID, metadata)
    after_first = len(vector_store.in_memory_store)
    second = pipeline.ingest_document(DOCUMENT_TEXT, DOCUMENT_ID, metadata)
    after_second = len(vector_store.in_memory_store)
    response = pipeline.query(QUESTION, top_k=3, min_score=0.0, document_id=DOCUMENT_ID)

    response["model"] = "ci-token-hash-384"
    response["metadata"].update(
        {
            "retrieval_backend": "in_memory",
            "embedding_mode": "deterministic_ci",
            "embedding_dimension": 384,
            "production_model": "sentence-transformers/all-MiniLM-L6-v2",
            "production_evidence": False,
        }
    )
    citation_errors = _validate_citations(response)
    response["metadata"]["citation_valid"] = not citation_errors
    response["metadata"]["citation_errors"] = citation_errors

    source_sha = _git("rev-parse", "HEAD")
    evidence = {
        "schema_version": 1,
        "evidence_type": "local_ci_pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "owner_repository": "https://github.com/QuanSkillOfficial/DataVision_Lap",
            "owner_branch": "codex/lap-week8-evidence-closeout",
            "source_commit_sha": source_sha,
            "source_commit_url": f"https://github.com/QuanSkillOfficial/DataVision_Lap/commit/{source_sha}",
            "canonical_repository": "https://github.com/QuanSkillOfficial/DataVision_Duy",
            "canonical_pull_request": 5,
            "canonical_paths": ["ai/rag", "ai/ai_tests", "outputs/ui_fixtures/lap_rag_response_real.json"],
        },
        "source_sha256": _source_hash(),
        "source_files": list(SOURCE_FILES),
        "configuration": {
            "backend": "in_memory",
            "chunk_size": 512,
            "overlap": 20,
            "top_k": 3,
            "min_score": 0.0,
        },
        "embedding": {
            "identity": "ci-token-hash-384",
            "dimension": 384,
            "purpose": "CI-only deterministic substitute; not live pgvector production evidence",
        },
        "indexing": {
            "before": before,
            "after_first": after_first,
            "after_second": after_second,
            "first": first,
            "second": second,
            "duplicate_free": after_first == after_second and second["chunks_inserted"] == 0,
        },
        "response": response,
    }

    if not response["answer"]:
        raise RuntimeError("RAG evidence answer must not be empty")
    if citation_errors:
        raise RuntimeError(f"RAG evidence citations are invalid: {citation_errors}")
    if not evidence["indexing"]["duplicate_free"]:
        raise RuntimeError("Repeated indexing created duplicate chunks")

    evidence_path = output_root / "rag" / "week8_rag_evidence.json"
    response_path = output_root / "ui_fixtures" / "lap_rag_response_real.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    response_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "outputs")
    args = parser.parse_args()
    evidence = generate(args.output_root.resolve())
    print(json.dumps({
        "status": "passed",
        "source_commit_sha": evidence["provenance"]["source_commit_sha"],
        "answer_non_empty": bool(evidence["response"]["answer"]),
        "citation_valid": evidence["response"]["metadata"]["citation_valid"],
        "after_first": evidence["indexing"]["after_first"],
        "after_second": evidence["indexing"]["after_second"],
        "duplicate_free": evidence["indexing"]["duplicate_free"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
