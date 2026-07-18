"""Audit and record the Week 7 Duy-to-Lap integration boundary.

The Lap repository is a sibling checkout and is intentionally read-only from
this repository. This script therefore produces an auditable mapping report
instead of silently changing Lap-owned files.

The report distinguishes:

* a valid Duy handoff contract;
* a real Lap pgvector execution proof; and
* fixture-shaped outputs that are useful for UI development but are not DB
  evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_LAP_ROOT = PROJECT_ROOT.parent / "DataVision_Lap"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs/lap_handoff/lap_week7_mapping_summary.json"
PROOF_OUTPUT = PROJECT_ROOT / "logs/lap_handoff/lap_week7_external_proof.json"

DATAFLOW_EXTERNAL_ID = "doc_dataflow_technical_report"
DATAFLOW_FILE_NAME = "DataFlow_Technical_Report.pdf"
EXPECTED_PAGE_COUNT = 36
EXPECTED_CHARACTER_COUNT = 129028
EXPECTED_SOURCE_ID = 4
EXPECTED_DOCUMENT_DB_ID = 1

LAP_ACTIVE_FILES = [
    "ai/__init__.py",
    "ai/rag/chunker.py",
    "ai/rag/document_loader.py",
    "ai/rag/embedder.py",
    "ai/rag/vector_store.py",
    "ai/rag/retriever.py",
    "ai/rag/rag_pipeline.py",
    "ai/rag/rag_service.py",
    "ai/rag/load_document_pages_to_pgvector.py",
    "ai/rag/scripts/week7_pgvector_smoke_test.py",
    "ai/rag/scripts/week7_rag_ci_smoke_test.py",
    "ai/ai_tests/fakes.py",
]

LAP_OUTPUT_FILES = {
    "chunk_insert_result": "outputs/rag/week7_chunk_insert_summary.json",
    "query_result": "outputs/rag/week7_pgvector_query_result.json",
    "query_log_payload": "outputs/rag/week7_rag_query_log_payload.json",
    "ui_fixture": "outputs/ui_fixtures/lap_rag_response_real.json",
}

LAP_LEGACY_CANDIDATES = [
    {
        "path": "ai/rag/notebooks/week6_real_pgvector_rag_demo.ipynb",
        "reason": "Week 6 notebook is not an executed Week 7 proof artifact.",
        "action": "archive outside the active RAG path or replace with an executed Week 7 proof",
    },
    {
        "path": "ai/rag/evaluation/retrieval_eval_results_week3.md",
        "reason": "Week 3 evaluation is outside the current shared-repo contract.",
        "action": "archive under a historical folder",
    },
    {
        "path": "ai/rag/evaluation/retrieval_test_cases_completed.csv",
        "reason": "Legacy evaluation file predates the Week 7 DataFlow evaluation.",
        "action": "archive or clearly mark as historical",
    },
    {
        "path": "ai/rag/evaluation/week6_retrieval_eval_results.md",
        "reason": "Week 6 fixture evaluation must not be presented as live pgvector proof.",
        "action": "archive or label fixture-only",
    },
    {
        "path": "ai/rag/evaluation/week6_retrieval_test_cases_dataflow.csv",
        "reason": "Superseded by the Week 7 DataFlow evaluation cases.",
        "action": "archive or label fixture-only",
    },
    {
        "path": "ai/WEEK_6_SUMMARY.md",
        "reason": "Historical summary duplicates current Week 7 documentation.",
        "action": "move to an archive folder",
    },
    {
        "path": "ai/week6_rag_to_schema_v4_mapping.md",
        "reason": "Historical schema mapping is superseded by the Week 7 mapping.",
        "action": "move to an archive folder",
    },
    {
        "path": "week6_team_integration_handoff.md",
        "reason": "Root-level Week 6 handoff duplicates the current Week 7 contracts.",
        "action": "archive after confirming no external consumer depends on it",
    },
    {
        "path": "sql/",
        "reason": "Legacy schema/setup SQL duplicates Phat's Week 7 database owner files.",
        "action": "remove from the active Lap module or archive as historical reference",
    },
]


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-16")


def _read_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(_read_text(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Expected an object at {path}:{line_number}")
        rows.append(value)
    return rows


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    if resolved == PROJECT_ROOT.resolve():
        return "DataVision_Duy"
    if resolved == (PROJECT_ROOT.parent / "DataVision_Lap").resolve():
        return "DataVision_Lap"
    for base in (PROJECT_ROOT.resolve(), PROJECT_ROOT.parent.resolve()):
        try:
            return resolved.relative_to(base).as_posix()
        except ValueError:
            continue
    return f"external/{path.name}"


def _git_head(repository_root: Path) -> str | None:
    head_path = repository_root / ".git" / "HEAD"
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="ascii").strip()
    if not head.startswith("ref: "):
        return head or None
    ref_name = head.removeprefix("ref: ").strip()
    ref_path = repository_root / ".git" / ref_name
    if ref_path.exists():
        return ref_path.read_text(encoding="ascii").strip() or None
    packed_refs = repository_root / ".git" / "packed-refs"
    if packed_refs.exists():
        for line in packed_refs.read_text(encoding="ascii").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == ref_name:
                    return commit
    return None


def _relative_files(root: Path, paths: list[str]) -> dict[str, bool]:
    return {path: (root / path).exists() for path in paths}


def inspect_duy_handoff() -> dict[str, Any]:
    manifest_path = PROJECT_ROOT / "outputs/rag_handoff/week7_rag_handoff_manifest.json"
    pages_path = PROJECT_ROOT / "outputs/rag_handoff/week7_document_pages_db_enriched.jsonl"
    metadata_path = PROJECT_ROOT / "outputs/rag_handoff/pdf_metadata.json"
    manifest = _read_json(manifest_path)
    pages = _read_jsonl(pages_path)
    metadata = _read_json(metadata_path)

    required_fields = {
        "document_external_id",
        "document_db_id",
        "source_id",
        "file_name",
        "page_number",
        "text",
        "char_count",
        "word_count",
        "is_empty",
        "ingestion_run_id",
    }
    missing_fields = sorted(
        field
        for field in required_fields
        if any(field not in page for page in pages)
    )
    ids = {page.get("document_external_id") for page in pages}
    file_names = {page.get("file_name") for page in pages}
    page_numbers = [page.get("page_number") for page in pages]
    char_count_matches = all(
        page.get("char_count") == len(page.get("text") or "") for page in pages
    )
    word_count_matches = all(
        page.get("word_count") == len((page.get("text") or "").split())
        for page in pages
    )
    non_empty_pages = sum(not bool(page.get("is_empty")) for page in pages)
    total_characters = sum(int(page.get("char_count") or 0) for page in pages)
    errors: list[str] = []
    if ids != {DATAFLOW_EXTERNAL_ID}:
        errors.append(f"unexpected document_external_id values: {sorted(ids)}")
    if file_names != {DATAFLOW_FILE_NAME}:
        errors.append(f"unexpected file_name values: {sorted(file_names)}")
    if missing_fields:
        errors.append(f"missing page fields: {missing_fields}")
    if page_numbers != list(range(1, EXPECTED_PAGE_COUNT + 1)):
        errors.append("page_number sequence is not 1..36")
    if not char_count_matches:
        errors.append("char_count does not match len(text)")
    if not word_count_matches:
        errors.append("word_count does not match text.split()")
    if len(pages) != EXPECTED_PAGE_COUNT:
        errors.append(f"expected {EXPECTED_PAGE_COUNT} pages, got {len(pages)}")
    if non_empty_pages != EXPECTED_PAGE_COUNT:
        errors.append(f"expected {EXPECTED_PAGE_COUNT} non-empty pages, got {non_empty_pages}")
    if total_characters != EXPECTED_CHARACTER_COUNT:
        errors.append(
            f"expected {EXPECTED_CHARACTER_COUNT} characters, got {total_characters}"
        )
    if manifest.get("document_db_id") != EXPECTED_DOCUMENT_DB_ID:
        errors.append("manifest document_db_id is not 1")
    if manifest.get("source_id") != EXPECTED_SOURCE_ID:
        errors.append("manifest source_id is not 4")

    return {
        "status": "passed" if not errors else "failed",
        "files": {
            "document_pages": _portable_path(pages_path),
            "manifest": _portable_path(manifest_path),
            "pdf_metadata": _portable_path(metadata_path),
        },
        "document_external_id": DATAFLOW_EXTERNAL_ID,
        "document_db_id": manifest.get("document_db_id"),
        "source_id": manifest.get("source_id"),
        "file_name": metadata.get("file_name"),
        "ingestion_run_id": manifest.get("ingestion_run_id"),
        "page_count": len(pages),
        "non_empty_pages": non_empty_pages,
        "total_characters": total_characters,
        "total_words": sum(int(page.get("word_count") or 0) for page in pages),
        "required_page_fields": sorted(required_fields),
        "errors": errors,
    }


def _result_rows(query_result: dict[str, Any]) -> list[dict[str, Any]]:
    return list(
        query_result.get("retrieved_chunks")
        or query_result.get("results")
        or []
    )


def inspect_lap_outputs(lap_root: Path) -> dict[str, Any]:
    paths = {name: lap_root / relative for name, relative in LAP_OUTPUT_FILES.items()}
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        return {
            "status": "missing",
            "files": {name: _portable_path(path) for name, path in paths.items()},
            "missing_files": missing,
            "errors": [f"missing Lap output files: {missing}"],
        }

    insert_result = _read_json(paths["chunk_insert_result"])
    query_result = _read_json(paths["query_result"])
    query_log = _read_json(paths["query_log_payload"])
    ui_fixture = _read_json(paths["ui_fixture"])
    rows = _result_rows(query_result)
    context = ui_fixture.get("retrieved_context") or []
    citations = ui_fixture.get("citations") or []

    fixture_errors: list[str] = []
    if ui_fixture.get("document_external_id") != DATAFLOW_EXTERNAL_ID:
        fixture_errors.append("UI fixture has the wrong document_external_id")
    if ui_fixture.get("file_name") != DATAFLOW_FILE_NAME:
        fixture_errors.append("UI fixture has the wrong file_name")
    if ui_fixture.get("document_db_id") != EXPECTED_DOCUMENT_DB_ID:
        fixture_errors.append("UI fixture does not carry document_db_id=1")
    if ui_fixture.get("metadata", {}).get("retrieval_backend") != "pgvector":
        fixture_errors.append("UI fixture does not declare pgvector backend")
    if ui_fixture.get("metadata", {}).get("embedding_dimension") != 384:
        fixture_errors.append("UI fixture does not declare embedding_dimension=384")
    if not context or not citations:
        fixture_errors.append("UI fixture has no retrieved context or citations")
    for item in context:
        for field in (
            "chunk_id",
            "document_db_id",
            "document_external_id",
            "file_name",
            "page_number",
            "chunk_text",
            "similarity_score",
        ):
            if field not in item:
                fixture_errors.append(f"UI context item is missing {field}")
    if query_log.get("query_text") and not query_log.get("user_query"):
        query_log_contract_issue = (
            "Lap output uses query_text, while the current insert_rag_query_log "
            "implementation expects user_query for Phat's schema."
        )
    else:
        query_log_contract_issue = None

    return {
        "status": "passed",
        "files": {name: _portable_path(path) for name, path in paths.items()},
        "chunk_insert": {
            "status": insert_result.get("status"),
            "pages_loaded": insert_result.get("pages_loaded", insert_result.get("total_pages_processed")),
            "chunks_created": insert_result.get("chunks_created", insert_result.get("total_chunks_generated")),
            "chunks_inserted": insert_result.get("chunks_inserted", insert_result.get("total_chunks_inserted")),
            "document_db_id": insert_result.get("document_db_id"),
            "embedding_dimension": insert_result.get("embedding_dimension"),
            "errors": insert_result.get("errors", []),
        },
        "query": {
            "status": query_result.get("status"),
            "document_db_id": query_result.get("document_db_id"),
            "retrieved_count": len(rows),
            "top_k": query_result.get("top_k"),
            "has_citations": bool(query_result.get("citations")),
            "errors": query_result.get("errors", []),
        },
        "query_log_payload": {
            "document_id": query_log.get("document_id"),
            "query_field": "user_query" if query_log.get("user_query") else "query_text",
            "retrieved_chunk_count": len(query_log.get("retrieved_chunk_ids") or []),
            "top_k": query_log.get("top_k"),
            "status": query_log.get("status"),
            "contract_issue": query_log_contract_issue,
        },
        "ui_fixture": {
            "status": ui_fixture.get("status"),
            "document_external_id": ui_fixture.get("document_external_id"),
            "document_db_id": ui_fixture.get("document_db_id"),
            "context_count": len(context),
            "citation_count": len(citations),
            "retrieval_backend": ui_fixture.get("metadata", {}).get("retrieval_backend"),
            "embedding_dimension": ui_fixture.get("metadata", {}).get("embedding_dimension"),
            "contract_status": "passed" if not fixture_errors else "failed",
            "errors": fixture_errors,
        },
        "live_execution_proof": {
            "chunk_inserted": insert_result.get("status") == "success"
            and int(insert_result.get("chunks_inserted") or 0) > 0,
            "query_retrieved": query_result.get("status") == "success"
            and bool(rows),
            "query_log_payload_present": bool(query_log.get("retrieved_chunk_ids")),
            "ui_fixture_is_not_db_proof": True,
        },
    }


def inspect_lap_code(lap_root: Path) -> dict[str, Any]:
    files = _relative_files(lap_root, LAP_ACTIVE_FILES)
    vector_store_path = lap_root / "ai/rag/vector_store.py"
    loader_path = lap_root / "ai/rag/load_document_pages_to_pgvector.py"
    service_path = lap_root / "ai/rag/rag_service.py"
    vector_text = _read_text(vector_store_path) if vector_store_path.exists() else ""
    loader_text = _read_text(loader_path) if loader_path.exists() else ""
    service_text = _read_text(service_path) if service_path.exists() else ""

    findings: list[dict[str, str]] = []
    if "from torch import chunk" in vector_text:
        findings.append(
            {
                "severity": "blocking",
                "path": "ai/rag/vector_store.py",
                "finding": "unused torch import breaks clean test collection when torch is absent",
                "fix": "remove the import; torch is not needed by VectorStore",
            }
        )
    if (
        "self.use_pgvector = False" in vector_text
        and "except ImportError" in vector_text
        and "except Exception as e" in vector_text
    ):
        findings.append(
            {
                "severity": "high",
                "path": "ai/rag/vector_store.py",
                "finding": "pgvector connection/schema failures silently switch to in-memory mode",
                "fix": "raise a clear error when use_pgvector=True; only use in-memory mode when explicitly requested",
            }
        )
    if re.search(r"document_id\s*=\s*None", vector_text):
        findings.append(
            {
                "severity": "high",
                "path": "ai/rag/vector_store.py",
                "finding": "unresolved document IDs can be converted to None before insert",
                "fix": "fail before INSERT when documents.id cannot be resolved",
            }
        )
    if "embeddings = embeddings[:len(chunks)]" in loader_text:
        findings.append(
            {
                "severity": "high",
                "path": "ai/rag/load_document_pages_to_pgvector.py",
                "finding": "duplicate filtering truncates embeddings by position and can misalign chunk/embedding pairs",
                "fix": "filter chunks and embeddings with the same kept-index list",
            }
        )
    if "embedding_dimension" not in vector_text or "384" not in vector_text:
        findings.append(
            {
                "severity": "high",
                "path": "ai/rag/vector_store.py",
                "finding": "the DB path does not visibly enforce vector dimension 384",
                "fix": "validate shape == 384 before insert and query",
            }
        )
    if "user_query" in service_text and "query_text" not in service_text:
        findings.append(
            {
                "severity": "medium",
                "path": "ai/rag/rag_service.py",
                "finding": "RAG log insertion uses user_query while the checked output payload uses query_text",
                "fix": "normalize one canonical field before INSERT; Phat schema_v4 uses user_query",
            }
        )

    return {
        "active_files": files,
        "active_files_complete": all(files.values()),
        "findings": findings,
        "loader_command": (
            "python -m ai.rag.load_document_pages_to_pgvector "
            "--document-pages <shared>/outputs/rag_handoff/"
            "week7_document_pages_db_enriched.jsonl "
            "--document-external-id doc_dataflow_technical_report "
            "--output-result outputs/rag/week7_chunk_insert_summary.json"
        ),
        "query_command": (
            "python ai/rag/scripts/week7_pgvector_smoke_test.py "
            "--query \"What is the DataFlow pipeline?\" "
            "--document-external-id doc_dataflow_technical_report "
            "--top-k 5 "
            "--output-result outputs/rag/week7_pgvector_query_result.json"
        ),
    }


def run_lap_unit_tests(lap_root: Path) -> dict[str, Any]:
    """Run the no-cache Lap unit-test command without modifying Lap files."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "ai/ai_tests/",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    display_command = "python -m pytest ai/ai_tests/ -q -p no:cacheprovider"
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            command,
            cwd=lap_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "error",
            "command": display_command,
            "error": str(exc),
        }
    combined_output = f"{completed.stdout}\n{completed.stderr}"
    error_summary = [
        line.strip()
        for line in combined_output.splitlines()
        if "Error" in line or "ERROR" in line or "error" in line
    ][-10:]

    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "command": display_command,
        "error_summary": error_summary,
    }


def build_mapping_summary(lap_root: Path = DEFAULT_LAP_ROOT) -> dict[str, Any]:
    duy_handoff = inspect_duy_handoff()
    lap_outputs = inspect_lap_outputs(lap_root)
    lap_code = inspect_lap_code(lap_root)
    output_proof = lap_outputs.get("live_execution_proof", {})
    blocking_findings = [
        finding for finding in lap_code.get("findings", [])
        if finding["severity"] in {"blocking", "high"}
    ]
    if lap_outputs.get("chunk_insert", {}).get("status") != "success":
        blocking_findings.append(
            {
                "severity": "blocking",
                "path": LAP_OUTPUT_FILES["chunk_insert_result"],
                "finding": "no executed chunk insertion proof",
                "fix": "run the loader against Phat's PostgreSQL and save a success result",
            }
        )
    if lap_outputs.get("query", {}).get("status") != "success":
        blocking_findings.append(
            {
                "severity": "blocking",
                "path": LAP_OUTPUT_FILES["query_result"],
                "finding": "no executed pgvector retrieval proof",
                "fix": "run the pgvector smoke query and save retrieved chunks/citations",
            }
        )
    if lap_outputs.get("query_log_payload", {}).get("contract_issue"):
        blocking_findings.append(
            {
                "severity": "medium",
                "path": LAP_OUTPUT_FILES["query_log_payload"],
                "finding": lap_outputs["query_log_payload"]["contract_issue"],
                "fix": "rename query_text to user_query at the DB boundary or update the shared contract",
            }
        )
    if not lap_code.get("active_files_complete", False):
        blocking_findings.append(
            {
                "severity": "high",
                "path": "DataVision_Lap/ai/rag",
                "finding": "one or more Week 7 active RAG files are missing",
                "fix": "restore the canonical active file set before merge",
            }
        )

    contract_passed = duy_handoff["status"] == "passed"
    live_proof_passed = bool(
        output_proof.get("chunk_inserted")
        and output_proof.get("query_retrieved")
    )
    status = "passed" if contract_passed and live_proof_passed and not blocking_findings else "blocked_on_lap_execution"

    return {
        "schema_version": "duy_lap_week7_mapping_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "handoff_contract_passed": contract_passed,
        "live_pgvector_proof_passed": live_proof_passed,
        "source_repositories": {
            "duy": _portable_path(PROJECT_ROOT),
            "lap": _portable_path(lap_root),
            "lap_commit": _git_head(lap_root),
        },
        "canonical_identity": {
            "source_id": EXPECTED_SOURCE_ID,
            "document_external_id": DATAFLOW_EXTERNAL_ID,
            "document_db_id": EXPECTED_DOCUMENT_DB_ID,
            "ingestion_run_id": duy_handoff.get("ingestion_run_id"),
            "rule": (
                "source_id is Phat sources.id; document_db_id is Phat documents.id; "
                "ingestion_run_id is a Duy run UUID and is never used as source_id"
            ),
        },
        "duy_input_contract": duy_handoff,
        "lap_output_contract": lap_outputs,
        "lap_code_audit": lap_code,
        "lap_unit_test_execution": {
            "status": "not_run",
            "command": "python -m pytest ai/ai_tests/ -q -p no:cacheprovider",
            "note": "Use --run-lap-tests to record an observed result.",
        },
        "cleanup_candidates": LAP_LEGACY_CANDIDATES,
        "blocking_findings": blocking_findings,
        "required_lap_actions": [
            "Remove the unused torch import and make ai/ai_tests collection pass in a clean environment.",
            "Make use_pgvector=True fail loudly instead of silently falling back to in-memory storage.",
            "Fail before INSERT when document_external_id cannot resolve to documents.id.",
            "Validate every embedding and query vector as dimension 384.",
            "Fix duplicate filtering so chunk/embedding pairs stay aligned.",
            "Normalize the RAG query log field to Phat's user_query column.",
            "Run the loader and pgvector query against the shared Phat database and replace pending output files with executed results.",
        ],
        "commands_after_lap_patch": {
            "lap_unit_tests": "python -m pytest ai/ai_tests/ -q",
            "lap_ci_smoke": "python ai/rag/scripts/week7_rag_ci_smoke_test.py",
            "lap_pgvector_loader": lap_code.get("loader_command"),
            "lap_pgvector_query": lap_code.get("query_command"),
        },
        "notes": [
            "The DataFlow UI fixture is contract-shaped and useful for UI validation.",
            "A fixture or payload is not counted as PostgreSQL execution proof.",
            "Phat's external database evidence separately confirms source_id=4, document_db_id=1, document_chunks=293 and rag_query_logs=1.",
            "The Lap-owned repository was audited read-only; cleanup candidates require a Lap-owner commit.",
        ],
    }


def build_external_proof(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "duy_lap_week7_external_mapping_audit",
        "status": summary["status"],
        "handoff_contract_passed": summary["handoff_contract_passed"],
        "live_pgvector_proof_passed": summary["live_pgvector_proof_passed"],
        "canonical_identity": summary["canonical_identity"],
        "lap_commit": summary["source_repositories"].get("lap_commit"),
        "lap_outputs": summary["lap_output_contract"].get("files", {}),
        "blocking_findings": summary["blocking_findings"],
        "required_lap_actions": summary["required_lap_actions"],
        "generated_at": summary["generated_at"],
    }


def write_outputs(summary: dict[str, Any]) -> tuple[Path, Path]:
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PROOF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    PROOF_OUTPUT.write_text(
        json.dumps(build_external_proof(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return SUMMARY_OUTPUT, PROOF_OUTPUT


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an auditable Duy-to-Lap Week 7 mapping summary"
    )
    parser.add_argument("--lap-root", type=Path, default=DEFAULT_LAP_ROOT)
    parser.add_argument(
        "--run-lap-tests",
        action="store_true",
        help="Run Lap pytest with cache disabled and include the observed result",
    )
    args = parser.parse_args()
    summary = build_mapping_summary(args.lap_root)
    if args.run_lap_tests:
        summary["lap_unit_test_execution"] = run_lap_unit_tests(args.lap_root)
        if summary["lap_unit_test_execution"]["status"] != "passed":
            summary["blocking_findings"].append(
                {
                    "severity": "blocking",
                    "path": "ai/ai_tests/",
                    "finding": "Lap unit-test command failed in the audit run",
                    "fix": "apply the listed Lap code fixes and rerun the command",
                }
            )
    summary_path, proof_path = write_outputs(summary)
    print(f"Wrote Lap mapping summary: {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"Wrote Lap external proof: {proof_path.relative_to(PROJECT_ROOT)}")
    print(f"Handoff contract: {summary['handoff_contract_passed']}")
    print(f"Live pgvector proof: {summary['live_pgvector_proof_passed']}")
    print(f"Mapping status: {summary['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
