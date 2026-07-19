"""Audit the Week 7 Duy-to-Phi/Hung UI integration boundary.

Phi/Hung owns the Streamlit repository, so this script treats the sibling
checkout as read-only and writes an auditable report in the Duy repository.
The report separates:

* fixture contract validity;
* real lineage/freshness of the copied fixtures;
* backend and CI contract readiness; and
* cleanup candidates that need an owner commit.

Run from the Duy repository:

    python scripts/week7_build_phi_hung_mapping_summary.py --run-hung-checks
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HUNG_ROOT = PROJECT_ROOT.parent / "DataVision_Hung"
SUMMARY_OUTPUT = (
    PROJECT_ROOT / "outputs/hung_handoff/hung_week7_mapping_summary.json"
)
PROOF_OUTPUT = PROJECT_ROOT / "logs/hung_handoff/hung_week7_external_proof.json"
WINDOWS_ABSOLUTE_PATH = re.compile(
    r'(?<![A-Za-z])[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*'
)


def _redact_machine_paths(text: str, repo_root: Path, label: str) -> str:
    portable = text.replace(str(repo_root), label)
    return WINDOWS_ABSOLUTE_PATH.sub("<local-path>", portable)

DATAFLOW_EXTERNAL_ID = "doc_dataflow_technical_report"
DATAFLOW_FILE_NAME = "DataFlow_Technical_Report.pdf"
EXPECTED_SOURCE_ID = 4
EXPECTED_DOCUMENT_DB_ID = 1
EXPECTED_RECORDS = 11524
EXPECTED_PAGES = 36
EXPECTED_CHUNKS = 293
EXPECTED_RAG_QUERY_LOGS = 1
EXPECTED_PREDICTION_LOGS = 10
EXPECTED_SOURCE_IDS = {
    "superstore_sales_csv": 1,
    "product_sales_region_excel": 2,
    "dummyjson_products_api": 3,
    "dataflow_technical_report_pdf": 4,
}
VALID_PREDICTION_STATUSES = {
    "accepted",
    "needs_review",
    "waiting_for_source",
    "failed",
}
REQUIRED_VIEWS = {
    "v_dashboard_overview",
    "v_latest_ingestion_runs",
    "v_data_quality_dashboard",
    "v_document_rag_readiness",
    "v_prediction_review_queue",
    "v_recent_activity",
}

ACTIVE_FILES = [
    "demo/streamlit_app.py",
    "demo/config.py",
    "demo/services/service_client.py",
    "demo/services/mock_client.py",
    "demo/services/backend_client.py",
    "demo/services/fixture_validator.py",
    "demo/views/dashboard_page.py",
    "demo/views/prediction_page.py",
    "demo/views/chatbot_page.py",
    "demo/views/suggestions_page.py",
    "demo/views/reports_page.py",
    "demo/views/upload_page.py",
    "scripts/week7_refresh_fixtures.py",
    "scripts/week7_ui_ci_smoke_test.py",
    "tests/test_week7_fixture_validation.py",
    "tests/test_backend_contract_smoke.py",
    "tests/test_backend_client_error_handling.py",
    "docs/backend_api_contract_for_ui.md",
    "docs/week7_ui_runbook.md",
    "docs/week7_github_actions_ui_job.md",
    "docs/week7_backend_route_alignment_summary.md",
    "backend_stub/main.py",
    ".github/workflows/ci.yml",
    "tests",
    "demo/fixtures/week7",
    "screenshots/week7_staging_ready_ui",
]

FIXTURE_FILES = {
    "duy": "demo/fixtures/week7/duy_latest_ingestion_summary.json",
    "phat": "demo/fixtures/week7/phat_dashboard_views_sample.json",
    "lap": "demo/fixtures/week7/lap_rag_response_real.json",
    "tuong_batch": "demo/fixtures/week7/tuong_prediction_batch_response.json",
    "tuong_queue": (
        "demo/fixtures/week7/tuong_prediction_review_queue_sample.json"
    ),
}

UI_CLEANUP_CANDIDATES = [
    {
        "path": "demo/fixtures/*.json",
        "reason": "Root fixtures contain pre-Week 7 vendor/refund-policy and synthetic prediction data.",
        "action": "Archive after confirming all active tests use demo/fixtures/week7/.",
    },
    {
        "path": "docs/Task Week 1-6.md",
        "reason": "Historical task document is large and contains superseded mock paths and contracts.",
        "action": "Move to docs/archive/ or clearly mark as historical.",
    },
    {
        "path": "materials/, frontend/, powerbi/, database/, data_engineering/",
        "reason": "These folders are not part of the active Streamlit Week 7 runtime boundary.",
        "action": "Keep only if owned deliverables still depend on them; otherwise archive outside the shared UI module.",
    },
    {
        "path": "screenshots/week2_*, screenshots/week3_*, screenshots/week5_*, screenshots/week6_*",
        "reason": "Historical screenshots can be mistaken for the Week 7 staging demo.",
        "action": "Archive and keep screenshots/week7_staging_ready_ui/ as the active demo evidence.",
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


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
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
    head = _read_text(head_path).strip()
    if not head.startswith("ref: "):
        return head or None
    ref_path = repository_root / ".git" / head.removeprefix("ref: ").strip()
    if ref_path.exists():
        return _read_text(ref_path).strip() or None
    return None


def _unwrap_data(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else {}


def _list_value(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    return value if isinstance(value, list) else []


def _status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(item.get("status") for item in items).items()))


def _required_paths(root: Path, paths: list[str]) -> dict[str, bool]:
    return {path: (root / path).exists() for path in paths}


def _duy_canonical() -> dict[str, Any]:
    path = PROJECT_ROOT / "outputs/ui_fixtures/duy_week7_database_enriched_summary.json"
    if not path.exists():
        return {"status": "missing", "path": _portable_path(path)}
    payload = _read_json(path)
    document = payload.get("latest_document") or {}
    return {
        "status": "passed",
        "path": _portable_path(path),
        "total_sources": payload.get("total_sources"),
        "total_runs": payload.get("total_runs"),
        "total_records_read": payload.get("total_records_read"),
        "average_data_quality_score": payload.get(
            "average_data_quality_score"
        ),
        "latest_document": {
            "source_id": document.get("source_id"),
            "document_db_id": document.get("document_db_id"),
            "document_external_id": document.get("document_external_id"),
            "file_name": document.get("file_name"),
            "file_hash_sha256": document.get("file_hash_sha256"),
            "ingestion_run_id": document.get("ingestion_run_id"),
        },
        "database_identity_status": payload.get("database_identity_status"),
    }


def _audit_duy_fixture(hung_root: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    path = hung_root / FIXTURE_FILES["duy"]
    if not path.exists():
        return {
            "status": "missing",
            "path": _portable_path(path),
            "errors": ["Week 7 Duy fixture is missing"],
        }
    payload = _read_json(path)
    document = payload.get("latest_document") or {}
    expected = canonical.get("latest_document", {})
    errors: list[str] = []
    for field in (
        "total_sources",
        "total_runs",
        "total_records_read",
        "average_data_quality_score",
    ):
        if payload.get(field) != canonical.get(field):
            errors.append(
                f"{field}={payload.get(field)!r} does not match Duy "
                f"{canonical.get(field)!r}"
            )
    for field in (
        "source_id",
        "document_db_id",
        "document_external_id",
        "file_name",
        "file_hash_sha256",
        "ingestion_run_id",
    ):
        if document.get(field) != expected.get(field):
            errors.append(
                f"latest_document.{field}={document.get(field)!r} does not "
                f"match Duy {expected.get(field)!r}"
            )
    if payload.get("database_identity_status") != "database_ids_confirmed":
        errors.append("database_identity_status is not database_ids_confirmed")
    metadata_source = str((payload.get("metadata") or {}).get("source_path", ""))
    if "code_by_others" in metadata_source:
        errors.append("fixture metadata points to ignored code_by_others path")
    return {
        "status": "passed" if not errors else "stale_or_incomplete",
        "path": _portable_path(path),
        "errors": errors,
        "source_id": document.get("source_id"),
        "document_db_id": document.get("document_db_id"),
        "document_external_id": document.get("document_external_id"),
        "ingestion_run_id": document.get("ingestion_run_id"),
        "database_identity_status": payload.get("database_identity_status"),
    }


def _audit_phat_fixture(hung_root: Path) -> dict[str, Any]:
    path = hung_root / FIXTURE_FILES["phat"]
    if not path.exists():
        return {
            "status": "missing",
            "path": _portable_path(path),
            "errors": ["Week 7 Phat dashboard fixture is missing"],
        }
    payload = _read_json(path)
    data = _unwrap_data(payload)
    errors: list[str] = []
    missing_views = sorted(REQUIRED_VIEWS - set(data))
    if missing_views:
        errors.append(f"missing required views: {missing_views}")
    overview = _list_value(data, "v_dashboard_overview")
    if not overview:
        errors.append("v_dashboard_overview is empty")
    else:
        row = overview[0]
        for field, expected in (
            ("total_sources", 4),
            ("total_documents", 1),
            ("successful_ingestions", 4),
        ):
            if row.get(field) != expected:
                errors.append(
                    f"v_dashboard_overview.{field}={row.get(field)!r}, "
                    f"expected {expected!r}"
                )
    source_rows = _list_value(data, "v_source_quality_summary")
    source_map = {
        row.get("source_name"): row.get("source_id") for row in source_rows
    }
    if source_map != EXPECTED_SOURCE_IDS:
        errors.append(f"source ID map {source_map!r} differs from {EXPECTED_SOURCE_IDS!r}")
    readiness = _list_value(data, "v_document_rag_readiness")
    if not readiness:
        errors.append("v_document_rag_readiness is empty")
    else:
        row = readiness[0]
        if row.get("document_external_id") != DATAFLOW_EXTERNAL_ID:
            errors.append("RAG readiness has the wrong document_external_id")
        if row.get("page_count") != EXPECTED_PAGES:
            errors.append("RAG readiness does not report 36 pages")
        if row.get("total_chunks") != EXPECTED_CHUNKS:
            errors.append("RAG readiness does not report 293 chunks")
    review_rows = _list_value(data, "v_prediction_review_queue")
    missing_review_external_ids = sum(
        row.get("document_external_id") is None for row in review_rows
    )
    if missing_review_external_ids:
        errors.append(
            f"{missing_review_external_ids} review-queue rows are missing "
            "document_external_id"
        )
    return {
        "status": "passed" if not errors else "stale_or_incomplete",
        "path": _portable_path(path),
        "errors": errors,
        "view_names": sorted(data),
        "view_row_counts": {
            name: len(_list_value(data, name)) for name in data
        },
        "source_id_map": source_map,
        "rag_readiness_rows": len(readiness),
        "review_queue_rows": len(review_rows),
        "review_rows_missing_document_external_id": missing_review_external_ids,
        "metadata": payload.get("metadata", {}),
    }


def _audit_lap_fixture(hung_root: Path) -> dict[str, Any]:
    path = hung_root / FIXTURE_FILES["lap"]
    if not path.exists():
        return {
            "status": "missing",
            "path": _portable_path(path),
            "errors": ["Week 7 Lap RAG fixture is missing"],
        }
    payload = _read_json(path)
    data = _unwrap_data(payload)
    metadata = payload.get("metadata") or {}
    errors: list[str] = []
    if data.get("question") != "What is the DataFlow pipeline?":
        errors.append("RAG question is not the canonical DataFlow query")
    if data.get("document_external_id") != DATAFLOW_EXTERNAL_ID:
        errors.append("RAG fixture has the wrong document_external_id")
    if data.get("document_db_id") != EXPECTED_DOCUMENT_DB_ID:
        errors.append("RAG fixture does not contain document_db_id=1")
    if data.get("file_name") != DATAFLOW_FILE_NAME:
        errors.append("RAG fixture has the wrong file name")
    if metadata.get("retrieval_backend") != "pgvector":
        errors.append("RAG metadata does not identify pgvector")
    if metadata.get("embedding_dimension") != 384:
        errors.append("RAG metadata does not identify 384 dimensions")
    context = _list_value(data, "retrieved_context")
    citations = _list_value(data, "citations")
    if not context or not citations:
        errors.append("RAG fixture has no retrieved context or citations")
    for citation in citations:
        if citation.get("document_external_id") != DATAFLOW_EXTERNAL_ID:
            errors.append("citation has the wrong document_external_id")
        if citation.get("document_db_id") != EXPECTED_DOCUMENT_DB_ID:
            errors.append("citation is missing document_db_id=1")
    return {
        "status": "passed" if not errors else "stale_or_incomplete",
        "path": _portable_path(path),
        "errors": errors,
        "status_value": data.get("status"),
        "document_external_id": data.get("document_external_id"),
        "document_db_id": data.get("document_db_id"),
        "context_rows": len(context),
        "citation_rows": len(citations),
        "retrieval_backend": metadata.get("retrieval_backend"),
        "embedding_dimension": metadata.get("embedding_dimension"),
    }


def _audit_tuong_fixture(hung_root: Path) -> dict[str, Any]:
    batch_path = hung_root / FIXTURE_FILES["tuong_batch"]
    queue_path = hung_root / FIXTURE_FILES["tuong_queue"]
    errors: list[str] = []
    if not batch_path.exists() or not queue_path.exists():
        return {
            "status": "missing",
            "batch_path": _portable_path(batch_path),
            "queue_path": _portable_path(queue_path),
            "errors": ["One or more Tuong UI fixtures are missing"],
        }
    batch = _read_json(batch_path)
    queue = _read_json(queue_path)
    results = batch.get("results") or []
    review_items = queue.get("review_items") or []
    if not results:
        errors.append("prediction batch is empty")
    if not review_items:
        errors.append("prediction review queue is empty")
    statuses = _status_counts(results)
    unsupported = sorted(set(statuses) - VALID_PREDICTION_STATUSES)
    if unsupported:
        errors.append(f"unsupported prediction statuses: {unsupported}")
    missing_source_ids = sum(item.get("source_id") is None for item in results)
    missing_document_ids = sum(item.get("document_db_id") is None for item in results)
    if missing_source_ids:
        errors.append(f"{missing_source_ids} batch items have null source_id")
    if missing_document_ids:
        errors.append(f"{missing_document_ids} batch items have null document_db_id")
    queue_missing_ids = sum(
        item.get("document_db_id") is None for item in review_items
    )
    if queue_missing_ids:
        errors.append(
            f"{queue_missing_ids} review items have null document_db_id"
        )
    return {
        "status": "passed" if not errors else "stale_or_incomplete",
        "batch_path": _portable_path(batch_path),
        "queue_path": _portable_path(queue_path),
        "errors": errors,
        "batch_count": len(results),
        "queue_count": len(review_items),
        "status_counts": statuses,
        "batch_missing_source_id": missing_source_ids,
        "batch_missing_document_db_id": missing_document_ids,
        "queue_missing_document_db_id": queue_missing_ids,
    }


def _audit_code_and_docs(hung_root: Path) -> dict[str, Any]:
    files = _required_paths(hung_root, ACTIVE_FILES)
    missing = sorted(path for path, present in files.items() if not present)
    config_text = _read_text(hung_root / "demo/config.py") if (hung_root / "demo/config.py").exists() else ""
    contract_path = hung_root / "docs/backend_api_contract_for_ui.md"
    contract_text = _read_text(contract_path) if contract_path.exists() else ""
    backend_client_path = hung_root / "demo/services/backend_client.py"
    backend_client_text = (
        _read_text(backend_client_path) if backend_client_path.exists() else ""
    )
    validator_path = hung_root / "demo/services/fixture_validator.py"
    validator_text = _read_text(validator_path) if validator_path.exists() else ""
    refresh_path = hung_root / "scripts/week7_refresh_fixtures.py"
    refresh_text = _read_text(refresh_path) if refresh_path.exists() else ""
    smoke_path = hung_root / "scripts/week7_ui_ci_smoke_test.py"
    smoke_text = _read_text(smoke_path) if smoke_path.exists() else ""
    docs_findings: list[dict[str, str]] = []
    if "PREDICTION_CONFIDENCE_THRESHOLD: float = 0.60" in config_text:
        docs_findings.append(
            {
                "path": "demo/config.py",
                "finding": "UI config still uses 0.60 as the prediction threshold",
                "fix": "Use Tuong's 0.80 staging acceptance threshold; keep 0.60 only as a display band if explicitly named.",
            }
        )
    duplicate_api_lines = [
        line.strip()
        for line in backend_client_text.splitlines()
        if "/api/api/" in line
    ]
    if "confidence >= 0.60" in contract_text or '"source_id": "src-' in contract_text:
        docs_findings.append(
            {
                "path": "docs/backend_api_contract_for_ui.md",
                "finding": "prediction API example/rule is still on the legacy 0.60/string-ID contract",
                "fix": "Use integer source_id, document_db_id -> prediction_logs.document_id, and the 0.80 staging gate.",
            }
        )
    if duplicate_api_lines:
        docs_findings.append(
            {
                "path": "docs/backend_api_contract_for_ui.md",
                "finding": "backend contract contains a duplicate /api/ route",
                "fix": "Keep BACKEND_BASE_URL ending in /api and use route paths without a second /api prefix.",
            }
        )
    if "document_db_id" not in validator_text or "source_id" not in validator_text:
        docs_findings.append(
            {
                "path": "demo/services/fixture_validator.py",
                "finding": "fixture validator does not cover all lineage fields",
                "fix": "Validate source_id, document_external_id, document_db_id, and ingestion_run_id for DB-enriched fixtures.",
            }
        )
    if 'OTHERS = ROOT / "code_by_others"' in refresh_text:
        docs_findings.append(
            {
                "path": "scripts/week7_refresh_fixtures.py",
                "finding": "fixture refresh depends on ignored code_by_others/ checkout",
                "fix": "Accept explicit sibling repository paths and fail if the source is not the current Week 7 output.",
            }
        )
    if "validate_all_week7_fixtures" not in smoke_text:
        docs_findings.append(
            {
                "path": "scripts/week7_ui_ci_smoke_test.py",
                "finding": "UI smoke test does not validate all fixture contracts first",
                "fix": "Run fixture validation as the first smoke-test gate.",
            }
        )
    route_contract = {
        "base_url_has_api": "http://localhost:8000/api" in contract_text,
        # The contract documentation intentionally mentions `/api/api/` as an
        # anti-pattern. Only executable client routes should fail this gate.
        "duplicate_api_route_in_client": bool(duplicate_api_lines),
        "backend_stub_present": (hung_root / "backend_stub/main.py").exists(),
        "workflow_present": (hung_root / ".github/workflows/ci.yml").exists(),
    }
    return {
        "status": "passed" if not missing else "incomplete",
        "missing_active_files": missing,
        "active_file_count": len(files) - len(missing),
        "active_file_total": len(files),
        "findings": docs_findings,
        "route_contract": route_contract,
    }


def _audit_screenshots(hung_root: Path) -> dict[str, Any]:
    required = [
        "01_dashboard_overview.png",
        "02_ingestion_quality.png",
        "03_prediction_review_queue.png",
        "04_prediction_manual_correction.png",
        "05_chatbot_rag_citations.png",
        "06_suggestions_with_evidence.png",
        "07_report_evidence_table.png",
        "08_backend_mode_config.png",
    ]
    directory = hung_root / "screenshots/week7_staging_ready_ui"
    present = [name for name in required if (directory / name).exists()]
    return {
        "status": "passed" if len(present) == len(required) else "incomplete",
        "directory": _portable_path(directory),
        "required_count": len(required),
        "present_count": len(present),
        "missing": [name for name in required if name not in present],
        "note": "File presence is verified; screenshot freshness must be confirmed against refreshed fixtures.",
    }


def _run_hung_command(
    hung_root: Path, command: list[str], display_command: str
) -> dict[str, Any]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            command,
            cwd=hung_root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "error",
            "command": display_command,
            "returncode": None,
            "error_summary": [
                _redact_machine_paths(
                    str(exc), hung_root, "<phi-hung-repo>"
                )
            ],
        }
    output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    output = _redact_machine_paths(output, hung_root, "<phi-hung-repo>")
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "command": display_command,
        "returncode": result.returncode,
        "output_tail": output[-3000:],
    }


def _run_hung_checks(hung_root: Path) -> dict[str, Any]:
    return {
        "unit_tests": _run_hung_command(
            hung_root,
            [
                sys.executable,
                "-m",
                "pytest",
                "tests",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            "python -m pytest tests -q -p no:cacheprovider",
        ),
        "ui_smoke": _run_hung_command(
            hung_root,
            [sys.executable, "scripts/week7_ui_ci_smoke_test.py"],
            "python scripts/week7_ui_ci_smoke_test.py",
        ),
    }


def _build_summary(hung_root: Path) -> dict[str, Any]:
    canonical = _duy_canonical()
    duy_fixture = _audit_duy_fixture(hung_root, canonical)
    phat_fixture = _audit_phat_fixture(hung_root)
    lap_fixture = _audit_lap_fixture(hung_root)
    tuong_fixture = _audit_tuong_fixture(hung_root)
    code_docs = _audit_code_and_docs(hung_root)
    screenshots = _audit_screenshots(hung_root)

    structural_passed = code_docs["status"] == "passed"
    fixture_contract_passed = all(
        item["status"] == "passed"
        for item in (duy_fixture, phat_fixture, lap_fixture, tuong_fixture)
    )
    real_lineage_passed = all(
        [
            duy_fixture.get("status") == "passed",
            lap_fixture.get("status") == "passed",
            tuong_fixture.get("status") == "passed",
        ]
    )

    findings: list[dict[str, Any]] = []
    for name, result in (
        ("duy_fixture", duy_fixture),
        ("phat_fixture", phat_fixture),
        ("lap_fixture", lap_fixture),
        ("tuong_fixture", tuong_fixture),
        ("ui_code_and_docs", code_docs),
        ("screenshots", screenshots),
    ):
        for error in result.get("errors", []):
            findings.append(
                {
                    "severity": "blocking"
                    if name in {"duy_fixture", "lap_fixture", "tuong_fixture"}
                    else "high",
                    "area": name,
                    "finding": error,
                }
            )
        for finding in result.get("findings", []):
            findings.append(
                {
                    "severity": "high",
                    "area": name,
                    **finding,
                }
            )

    if not screenshots["status"] == "passed":
        findings.append(
            {
                "severity": "medium",
                "area": "screenshots",
                "finding": "Week 7 staging screenshot set is incomplete",
            }
        )

    gates = {
        "fixture_contract_passed": fixture_contract_passed,
        "duy_fixture_lineage_passed": duy_fixture.get("status") == "passed",
        "phat_dashboard_contract_passed": phat_fixture.get("status") == "passed",
        "lap_rag_fixture_passed": lap_fixture.get("status") == "passed",
        "tuong_fixture_contract_passed": tuong_fixture.get("status") == "passed",
        "ui_structure_passed": structural_passed,
        "ui_code_docs_passed": not code_docs.get("findings"),
        "real_lineage_passed": real_lineage_passed,
        "screenshots_present": screenshots["status"] == "passed",
    }

    required_actions: list[str] = []
    if duy_fixture.get("status") != "passed":
        required_actions.append(
            "Refresh demo/fixtures/week7/duy_latest_ingestion_summary.json "
            "from Duy's current DB-enriched fixture."
        )
    if phat_fixture.get("status") != "passed":
        required_actions.append(
            "Refresh Phat dashboard view samples and preserve document_external_id "
            "alongside integer document_id values."
        )
    if lap_fixture.get("status") != "passed":
        required_actions.append(
            "Replace the active RAG fixture with Lap's current DataFlow pgvector "
            "result and complete citation lineage."
        )
    if tuong_fixture.get("status") != "passed":
        required_actions.append(
            "Replace Tuong batch and review-queue fixtures with DB-enriched outputs "
            "that preserve non-null source_id, document_db_id, and ingestion_run_id."
        )
    if code_docs.get("status") != "passed" or code_docs.get("findings"):
        required_actions.append(
            "Resolve the UI code and contract findings listed in "
            "ui_code_and_docs_audit, then rerun this audit."
        )
    if screenshots.get("status") != "passed":
        required_actions.append(
            "Regenerate the complete Week 7 staging screenshot set after fixture refresh."
        )

    notes = [
        "Duy, Phat, Lap, and Tuong fixture results are calculated from the current sibling-repository snapshots.",
        "Code, documentation, and screenshot checks are reported separately from fixture lineage and executable tests.",
        "The audit is read-only against the sibling Phi/Hung repository; owner fixes require a Phi/Hung commit.",
    ]
    return {
        "schema_version": "duy_phi_hung_week7_mapping_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_owner_refresh"
        if not fixture_contract_passed or not structural_passed
        else "ready_with_lineage_caveat"
        if not real_lineage_passed
        else "passed",
        "source_repositories": {
            "duy": "DataVision_Duy",
            "phi_hung": "DataVision_Hung",
            "hung_commit": _git_head(hung_root),
        },
        "canonical_identity": {
            "source_id_map": EXPECTED_SOURCE_IDS,
            "document_external_id": DATAFLOW_EXTERNAL_ID,
            "document_db_id": EXPECTED_DOCUMENT_DB_ID,
            "source_id": EXPECTED_SOURCE_ID,
            "file_name": DATAFLOW_FILE_NAME,
            "records": EXPECTED_RECORDS,
            "pages": EXPECTED_PAGES,
            "chunks": EXPECTED_CHUNKS,
            "rag_query_logs": EXPECTED_RAG_QUERY_LOGS,
            "prediction_logs": EXPECTED_PREDICTION_LOGS,
            "rule": "UI must display source_id as Phat integer, document_db_id as documents.id, and ingestion_run_id as Duy run UUID.",
        },
        "duy_canonical_fixture": canonical,
        "hung_fixture_audit": {
            "duy": duy_fixture,
            "phat": phat_fixture,
            "lap": lap_fixture,
            "tuong": tuong_fixture,
        },
        "ui_code_and_docs_audit": code_docs,
        "screenshots_audit": screenshots,
        "gates": gates,
        "blocking_findings": findings,
        "cleanup_candidates": UI_CLEANUP_CANDIDATES,
        "required_phi_hung_actions": required_actions,
        "commands_after_phi_hung_patch": {
            "unit_tests": "python -m pytest tests -q",
            "ui_smoke": "python scripts/week7_ui_ci_smoke_test.py",
            "fixture_refresh": "python scripts/week7_refresh_fixtures.py --duy-root ... --phat-root ... --lap-root ... --tuong-root ...",
            "streamlit": "streamlit run demo/streamlit_app.py",
            "backend_stub": "python backend_stub/main.py",
        },
        "notes": notes,
    }


def _write_outputs(summary: dict[str, Any]) -> None:
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PROOF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    proof = {
        "schema_version": summary["schema_version"],
        "generated_at": summary["generated_at"],
        "status": summary["status"],
        "hung_commit": summary["source_repositories"]["hung_commit"],
        "gates": summary["gates"],
        "blocking_findings": summary["blocking_findings"],
        "cleanup_candidates": summary["cleanup_candidates"],
    }
    PROOF_OUTPUT.write_text(
        json.dumps(proof, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an auditable Duy-to-Phi/Hung Week 7 mapping summary"
    )
    parser.add_argument("--hung-root", type=Path, default=DEFAULT_HUNG_ROOT)
    parser.add_argument(
        "--run-hung-checks",
        action="store_true",
        help="Run Hung pytest and UI smoke commands with caches disabled",
    )
    args = parser.parse_args()

    summary = _build_summary(args.hung_root)
    if args.run_hung_checks:
        summary["hung_execution"] = _run_hung_checks(args.hung_root)
        summary["gates"]["hung_unit_tests_passed"] = (
            summary["hung_execution"]["unit_tests"]["status"] == "passed"
        )
        summary["gates"]["ui_smoke_passed"] = (
            summary["hung_execution"]["ui_smoke"]["status"] == "passed"
        )
        if not (
            summary["gates"]["hung_unit_tests_passed"]
            and summary["gates"]["ui_smoke_passed"]
        ):
            summary["blocking_findings"].append(
                {
                    "severity": "blocking",
                    "area": "hung_execution",
                    "finding": "Phi/Hung tests or UI smoke test failed",
                    "fix": "Install the pinned UI requirements and rerun both commands.",
                }
            )
            summary["required_phi_hung_actions"].append(
                "Install the pinned Phi/Hung requirements and rerun both the full "
                "test suite and UI smoke test."
            )
    else:
        summary["hung_execution"] = {
            "unit_tests": {
                "status": "not_run",
                "command": "python -m pytest tests -q -p no:cacheprovider",
            },
            "ui_smoke": {
                "status": "not_run",
                "command": "python scripts/week7_ui_ci_smoke_test.py",
            },
        }

    if summary["blocking_findings"]:
        summary["status"] = "blocked_on_phi_hung_refresh"
    elif summary["status"] != "passed":
        summary["status"] = "ready_with_lineage_caveat"
    _write_outputs(summary)

    print(f"Wrote Phi/Hung mapping summary: {SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote Phi/Hung external proof: {PROOF_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"UI fixture contract: {summary['gates']['fixture_contract_passed']}")
    print(f"Real lineage: {summary['gates']['real_lineage_passed']}")
    print(f"UI structure: {summary['gates']['ui_structure_passed']}")
    print(f"Mapping status: {summary['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
