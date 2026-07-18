"""Audit the Week 7 Duy-to-Tuong prediction integration boundary.

The Tuong repository is a sibling checkout and is intentionally treated as
read-only. This script records what Duy currently provides, what Tuong
currently returns, and which execution or contract gaps still block the
shared Week 7 acceptance gate.
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
DEFAULT_TUONG_ROOT = PROJECT_ROOT.parent / "DataVision_Tuong"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs/tuong_handoff/tuong_week7_mapping_summary.json"
PROOF_OUTPUT = PROJECT_ROOT / "logs/tuong_handoff/tuong_week7_external_proof.json"

VALID_STATUSES = {
    "accepted",
    "needs_review",
    "waiting_for_source",
    "failed",
}
EXPECTED_SOURCE_IDS = {
    "superstore_sales_csv": 1,
    "product_sales_region_excel": 2,
    "dummyjson_products_api": 3,
    "dataflow_technical_report_pdf": 4,
}
DATAFLOW_EXTERNAL_ID = "doc_dataflow_technical_report"
EXPECTED_DOCUMENT_DB_ID = 1
EXPECTED_PAYLOAD_COUNT = 20
EXPECTED_ADDITIONAL_COUNT = 10

TUONG_ACTIVE_FILES = [
    "ai/prediction/config.py",
    "ai/prediction/feature_builder.py",
    "ai/prediction/inference.py",
    "ai/prediction/batch_inference.py",
    "ai/prediction/prediction_service.py",
    "ai/prediction/prediction_log_payload_builder.py",
    "ai/prediction/models/best_document_type_classifier.joblib",
    "ai/prediction/models/model_card.json",
    "scripts/run_real_payloads.py",
    "scripts/week7_prediction_ci_smoke_test.py",
    "scripts/insert_prediction_logs_to_postgres.py",
    "scripts/build_rag_filter_metadata.py",
    "scripts/build_retraining_dataset_from_feedback.py",
    "tests/ai_tests",
]

TUONG_OUTPUT_FILES = {
    "input_copy": "outputs/prediction_payloads/tuong_week7_prediction_payloads.json",
    "prediction_results": "outputs/week7_duy_prediction_results.json",
    "prediction_log_payloads": "outputs/db_integration/week7_prediction_log_payloads.json",
    "prediction_log_insert_result": (
        "outputs/db_integration/week7_prediction_log_insert_result.json"
    ),
    "rag_filter_metadata": "outputs/rag_metadata/document_type_filter_payload.json",
    "ui_single": "outputs/ui_fixtures/tuong_prediction_response_real.json",
    "ui_batch": "outputs/ui_fixtures/tuong_prediction_batch_response.json",
    "ui_review_queue": (
        "outputs/ui_fixtures/tuong_prediction_review_queue_sample.json"
    ),
}

TUONG_CLEANUP_CANDIDATES = [
    {
        "path": "**/__pycache__/",
        "reason": "runtime caches are present across ai/, scripts/ and tests/",
        "action": "delete the cache directories and add a root .gitignore for Python artifacts",
    },
    {
        "path": "scripts/test_prediction_on_duy_outputs.py",
        "reason": (
            "legacy script assigns ingestion run UUIDs to source_id and uses the "
            "old document_id string contract"
        ),
        "action": "archive it and keep scripts/run_real_payloads.py as the official runner",
    },
    {
        "path": "scripts/data/duy_dataflow_real_payload.json",
        "reason": "stale single-payload fixture carries old IDs and run lineage",
        "action": "archive it or regenerate it from Duy's Week 7 batch",
    },
    {
        "path": "docs/prediction_contract.md",
        "reason": (
            "still documents the old 0.60 acceptance threshold and says accepted "
            "predictions are safe automatic RAG filters"
        ),
        "action": "update it to the 0.80 staging policy or archive it as historical",
    },
    {
        "path": "docs/prediction_log_contract.md",
        "reason": (
            "maps document_db_id to a non-existent prediction_logs.document_db_id "
            "column and still documents the 0.60 policy"
        ),
        "action": "map document_db_id to prediction_logs.document_id and use the Week 7 policy",
    },
    {
        "path": "docs/model_card_document_classifier.md",
        "reason": "contains the old 0.60 operational acceptance rule",
        "action": "separate model training metadata from the staging acceptance policy",
    },
    {
        "path": "docs/model_report_week3.md",
        "reason": "historical Week 3 report is not an active shared-repo contract",
        "action": "move it to docs/archive/",
    },
    {
        "path": "docs/tuong_week3_summary_report.md",
        "reason": "historical Week 3 summary duplicates current Week 7 documentation",
        "action": "move it to docs/archive/",
    },
    {
        "path": "week1/",
        "reason": "historical planning artifacts are not active prediction runtime files",
        "action": "exclude from the shared merge or move under an archive area",
    },
    {
        "path": "week2/",
        "reason": "historical notebook/training artifacts duplicate the active model package",
        "action": "retain outside the active shared module or archive explicitly",
    },
    {
        "path": "Tuong tasks w7.pdf",
        "reason": "manager source PDF should not sit in the active repository root",
        "action": "move to docs/archive/manager_inputs/ or exclude from the shared merge",
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


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(_read_text(path))


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    named_roots = {
        PROJECT_ROOT.resolve(): "DataVision_Duy",
        DEFAULT_TUONG_ROOT.resolve(): "DataVision_Tuong",
    }
    if resolved in named_roots:
        return named_roots[resolved]
    for base in (PROJECT_ROOT.resolve(), PROJECT_ROOT.parent.resolve()):
        try:
            return resolved.relative_to(base).as_posix()
        except ValueError:
            continue
    return f"external/{path.name}"


def _git_head(repository_root: Path) -> str | None:
    head_path = repository_root / ".git/HEAD"
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="ascii").strip()
    if not head.startswith("ref: "):
        return head or None
    ref_name = head.removeprefix("ref: ").strip()
    ref_path = repository_root / ".git" / ref_name
    if ref_path.exists():
        return ref_path.read_text(encoding="ascii").strip() or None
    packed_refs = repository_root / ".git/packed-refs"
    if packed_refs.exists():
        for line in packed_refs.read_text(encoding="ascii").splitlines():
            if line and not line.startswith(("#", "^")):
                commit, name = line.split(" ", 1)
                if name == ref_name:
                    return commit
    return None


def _as_object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("status")) for row in rows))


def inspect_duy_payloads() -> dict[str, Any]:
    primary_path = (
        PROJECT_ROOT
        / "outputs/prediction_payloads/tuong_week7_prediction_payloads.json"
    )
    additional_path = (
        PROJECT_ROOT
        / "outputs/prediction_payloads/tuong_week7_additional_prediction_payloads.json"
    )
    individual_dir = PROJECT_ROOT / "outputs/prediction_payloads/week7"
    primary = _as_object_list(_read_json(primary_path, []))
    additional = _as_object_list(_read_json(additional_path, []))
    individual_files = sorted(individual_dir.glob("*.json"))

    required_model_fields = {
        "file_name",
        "file_type",
        "file_size",
        "text_length",
        "num_pages",
        "source_system",
        "extracted_text",
    }
    required_handoff_keys = {
        "source_id",
        "source_name",
        "document_db_id",
        "ingestion_run_id",
        "data_quality_score",
        "file_hash_sha256",
    }
    errors: list[str] = []
    if len(primary) != EXPECTED_PAYLOAD_COUNT:
        errors.append(
            f"expected {EXPECTED_PAYLOAD_COUNT} primary payloads, got {len(primary)}"
        )
    if len(additional) != EXPECTED_ADDITIONAL_COUNT:
        errors.append(
            f"expected {EXPECTED_ADDITIONAL_COUNT} additional payloads, got {len(additional)}"
        )
    if primary[10:] != additional:
        errors.append("primary cases 11-20 do not exactly match the additional batch")
    if len(individual_files) != EXPECTED_PAYLOAD_COUNT:
        errors.append(
            f"expected {EXPECTED_PAYLOAD_COUNT} individual payload files, got "
            f"{len(individual_files)}"
        )

    invalid_case_names = {
        "missing_required_file_name",
        "missing_document_external_id",
        "invalid_file_size_type",
    }
    for index, payload in enumerate(primary, 1):
        test_case = payload.get("test_case")
        if test_case not in invalid_case_names:
            missing_model = sorted(required_model_fields - payload.keys())
            if missing_model:
                errors.append(f"case {index} is missing model fields: {missing_model}")
        missing_handoff = sorted(required_handoff_keys - payload.keys())
        if missing_handoff:
            errors.append(f"case {index} is missing handoff keys: {missing_handoff}")
        source_name = payload.get("source_name")
        expected_source_id = EXPECTED_SOURCE_IDS.get(str(source_name))
        if expected_source_id is not None and payload.get("source_id") != expected_source_id:
            errors.append(
                f"case {index} source_id does not match {source_name}: "
                f"{payload.get('source_id')} != {expected_source_id}"
            )
        if payload.get("source_id") == payload.get("ingestion_run_id"):
            errors.append(f"case {index} confuses source_id with ingestion_run_id")

    full_document = next(
        (
            payload
            for payload in primary
            if payload.get("document_external_id") == DATAFLOW_EXTERNAL_ID
        ),
        {},
    )
    if full_document.get("source_id") != 4:
        errors.append("full DataFlow payload does not carry source_id=4")
    if full_document.get("document_db_id") != EXPECTED_DOCUMENT_DB_ID:
        errors.append("full DataFlow payload does not carry document_db_id=1")

    return {
        "status": "passed" if not errors else "failed",
        "files": {
            "primary_batch": _portable_path(primary_path),
            "additional_batch": _portable_path(additional_path),
            "individual_directory": _portable_path(individual_dir),
        },
        "primary_count": len(primary),
        "additional_count": len(additional),
        "individual_file_count": len(individual_files),
        "status_hint_counts": dict(
            Counter(str(payload.get("expected_status_hint")) for payload in primary)
        ),
        "source_id_map": EXPECTED_SOURCE_IDS,
        "full_document_identity": {
            "source_id": full_document.get("source_id"),
            "document_external_id": full_document.get("document_external_id"),
            "document_db_id": full_document.get("document_db_id"),
            "ingestion_run_id": full_document.get("ingestion_run_id"),
        },
        "document_external_ids": [
            payload.get("document_external_id") for payload in primary
        ],
        "test_cases": [payload.get("test_case") for payload in primary],
        "errors": errors,
    }


def inspect_tuong_input_copy(
    tuong_root: Path,
    duy_contract: dict[str, Any],
) -> dict[str, Any]:
    path = tuong_root / TUONG_OUTPUT_FILES["input_copy"]
    copied = _as_object_list(_read_json(path, []))
    duy_ids = duy_contract.get("document_external_ids", [])
    copied_ids = [payload.get("document_external_id") for payload in copied]
    stale_source_ids = sum(
        payload.get("source_id") != EXPECTED_SOURCE_IDS.get(str(payload.get("source_name")))
        for payload in copied
        if str(payload.get("source_name")) in EXPECTED_SOURCE_IDS
    )
    errors: list[str] = []
    if len(copied) != EXPECTED_PAYLOAD_COUNT:
        errors.append(
            f"Tuong input copy contains {len(copied)} payloads instead of "
            f"{EXPECTED_PAYLOAD_COUNT}"
        )
    if copied_ids != duy_ids:
        errors.append("Tuong input copy does not match Duy's current ordered batch")
    if stale_source_ids:
        errors.append(f"{stale_source_ids} copied payloads have stale or null source_id")
    return {
        "status": "passed" if not errors else "stale",
        "path": _portable_path(path),
        "payload_count": len(copied),
        "document_external_ids": copied_ids,
        "stale_or_null_source_id_count": stale_source_ids,
        "errors": errors,
    }


def _required_result_fields_missing(rows: list[dict[str, Any]]) -> list[str]:
    required = {
        "predicted_document_type",
        "confidence",
        "top_predictions",
        "status",
        "review_reason",
        "source_id",
        "source_name",
        "document_external_id",
        "document_db_id",
        "ingestion_run_id",
        "model_name",
        "model_version",
        "created_at",
    }
    return sorted(
        field
        for field in required
        if any(field not in row for row in rows)
    )


def inspect_tuong_outputs(
    tuong_root: Path,
    duy_contract: dict[str, Any],
) -> dict[str, Any]:
    paths = {
        name: tuong_root / relative
        for name, relative in TUONG_OUTPUT_FILES.items()
    }
    results = _as_object_list(_read_json(paths["prediction_results"], []))
    log_payloads = _as_object_list(
        _read_json(paths["prediction_log_payloads"], [])
    )
    insert_result = _read_json(paths["prediction_log_insert_result"])
    rag_metadata = _as_object_list(
        _read_json(paths["rag_filter_metadata"], [])
    )
    ui_single = _read_json(paths["ui_single"], {})
    ui_batch = _as_object_list(_read_json(paths["ui_batch"], []))
    ui_review = _as_object_list(_read_json(paths["ui_review_queue"], []))

    expected_ids = duy_contract.get("document_external_ids", [])
    result_ids = [row.get("document_external_id") for row in results]
    missing_result_fields = _required_result_fields_missing(results)
    invalid_statuses = sorted(
        {
            row.get("status")
            for row in results
            if row.get("status") not in VALID_STATUSES
        },
        key=str,
    )
    result_errors: list[str] = []
    if len(results) != EXPECTED_PAYLOAD_COUNT:
        result_errors.append(
            f"prediction result contains {len(results)} rows instead of "
            f"{EXPECTED_PAYLOAD_COUNT}"
        )
    if result_ids != expected_ids:
        result_errors.append("prediction result lineage does not match Duy's ordered batch")
    if missing_result_fields:
        result_errors.append(f"result rows are missing fields: {missing_result_fields}")
    if invalid_statuses:
        result_errors.append(f"invalid result statuses: {invalid_statuses}")
    if len(results) and not {
        row.get("status") for row in results
    }.intersection({"waiting_for_source", "failed"}):
        result_errors.append(
            "the current result omits Duy's quality-gate or validation-error cases"
        )
    stale_result_ids = sum(
        row.get("source_id") != EXPECTED_SOURCE_IDS.get(str(row.get("source_name")))
        for row in results
        if str(row.get("source_name")) in EXPECTED_SOURCE_IDS
    )
    if stale_result_ids:
        result_errors.append(
            f"{stale_result_ids} results have stale or null source_id"
        )

    log_errors: list[str] = []
    if len(log_payloads) != EXPECTED_PAYLOAD_COUNT:
        log_errors.append(
            f"prediction log file contains {len(log_payloads)} rows instead of "
            f"{EXPECTED_PAYLOAD_COUNT}"
        )
    required_log_fields = {
        "source_id",
        "document_external_id",
        "document_id",
        "model_name",
        "model_version",
        "input_payload",
        "prediction_result",
        "predicted_label",
        "confidence_score",
        "status",
        "review_reason",
        "ingestion_run_id",
        "created_at",
    }
    missing_log_fields = sorted(
        field
        for field in required_log_fields
        if any(field not in row for row in log_payloads)
    )
    if missing_log_fields:
        log_errors.append(f"prediction log rows are missing fields: {missing_log_fields}")

    insert_status = (
        insert_result.get("status")
        if isinstance(insert_result, dict)
        else "missing"
    )
    inserted_count = (
        insert_result.get("inserted_count")
        or insert_result.get("prediction_logs_inserted")
        or 0
        if isinstance(insert_result, dict)
        else 0
    )
    db_insert_proof_passed = (
        insert_status in {"passed", "success"} and int(inserted_count or 0) > 0
    )

    allowed_source_ids = set(EXPECTED_SOURCE_IDS.values())
    ui_rows = [
        row
        for row in [ui_single, *ui_batch, *ui_review]
        if isinstance(row, dict) and row
    ]
    ui_invalid_source_ids = sorted(
        {
            row.get("source_id")
            for row in ui_rows
            if row.get("source_id") not in allowed_source_ids
        },
        key=str,
    )
    ui_external_ids = {
        row.get("document_external_id")
        for row in ui_rows
        if row.get("document_external_id") is not None
    }
    known_external_ids = {
        value for value in expected_ids if value is not None
    }
    ui_unknown_document_ids = sorted(ui_external_ids - known_external_ids)
    ui_contract_fields = {
        "status",
        "confidence",
        "predicted_document_type",
        "top_predictions",
        "review_reason",
        "manual_review_required",
        "document_external_id",
        "document_db_id",
        "source_id",
        "ingestion_run_id",
    }
    ui_missing_fields = sorted(
        field
        for field in ui_contract_fields
        if any(field not in row for row in ui_rows)
    )

    rag_hard_filter_count = sum(
        bool(row.get("use_for_rag_filtering")) for row in rag_metadata
    )
    rag_rule_passed = all(
        not row.get("use_for_rag_filtering")
        or (
            row.get("status") == "accepted"
            and float(row.get("confidence") or 0.0) >= 0.80
        )
        for row in rag_metadata
    )

    return {
        "files": {
            name: _portable_path(path)
            for name, path in paths.items()
        },
        "prediction_results": {
            "status": "passed" if not result_errors else "stale_or_incomplete",
            "count": len(results),
            "status_counts": _status_counts(results),
            "document_external_ids": result_ids,
            "stale_or_null_source_id_count": stale_result_ids,
            "errors": result_errors,
        },
        "prediction_log_payloads": {
            "status": "passed" if not log_errors else "stale_or_incomplete",
            "count": len(log_payloads),
            "status_counts": _status_counts(log_payloads),
            "errors": log_errors,
        },
        "database_insert_proof": {
            "status": insert_status,
            "inserted_count": int(inserted_count or 0),
            "passed": db_insert_proof_passed,
            "note": (
                "A dry-run preview is contract evidence, not proof that rows were "
                "inserted and queried from PostgreSQL."
            ),
        },
        "rag_filter_metadata": {
            "count": len(rag_metadata),
            "hard_filter_count": rag_hard_filter_count,
            "safe_rule_passed": rag_rule_passed,
        },
        "ui_fixtures": {
            "single_count": 1 if isinstance(ui_single, dict) and ui_single else 0,
            "batch_count": len(ui_batch),
            "review_queue_count": len(ui_review),
            "status_counts": _status_counts(ui_batch),
            "contract_fields_passed": not ui_missing_fields,
            "real_duy_lineage_passed": not (
                ui_invalid_source_ids or ui_unknown_document_ids
            ),
            "invalid_source_ids": ui_invalid_source_ids,
            "unknown_document_external_ids": ui_unknown_document_ids,
            "missing_fields": ui_missing_fields,
            "note": "Contract-shaped sample fixtures are not real Duy lineage or DB proof.",
        },
        "output_contract_passed": bool(
            not result_errors
            and not log_errors
            and db_insert_proof_passed
            and rag_rule_passed
            and not ui_missing_fields
            and not ui_invalid_source_ids
            and not ui_unknown_document_ids
        ),
    }


def inspect_tuong_code(tuong_root: Path) -> dict[str, Any]:
    files = {
        relative: (tuong_root / relative).exists()
        for relative in TUONG_ACTIVE_FILES
    }
    config_text = _read_text(tuong_root / "ai/prediction/config.py")
    feature_text = _read_text(tuong_root / "ai/prediction/feature_builder.py")
    batch_text = _read_text(tuong_root / "ai/prediction/batch_inference.py")
    runner_text = _read_text(tuong_root / "scripts/run_real_payloads.py")
    smoke_text = _read_text(
        tuong_root / "scripts/week7_prediction_ci_smoke_test.py"
    )
    requirements = _read_text(tuong_root / "requirements.txt").lower()
    model_card = _read_json(
        tuong_root / "ai/prediction/models/model_card.json",
        {},
    )
    prediction_contract_text = _read_text(
        tuong_root / "docs/prediction_contract.md"
    )
    prediction_log_contract_text = _read_text(
        tuong_root / "docs/prediction_log_contract.md"
    )
    api_contract_text = _read_text(
        tuong_root / "docs/week7_prediction_api_contract.md"
    )

    findings: list[dict[str, str]] = []
    if not (tuong_root / ".gitignore").exists():
        findings.append(
            {
                "severity": "medium",
                "path": ".gitignore",
                "finding": "repository has Python cache directories but no root .gitignore",
                "fix": "add __pycache__/, *.py[cod], .pytest_cache/, .venv/ and .env",
            }
        )
    if (
        "STAGING_ACCEPTANCE_THRESHOLD = 0.80" in config_text
        and re.search(r"CONFIDENCE_THRESHOLD\s*=\s*0\.60", feature_text)
    ):
        findings.append(
            {
                "severity": "high",
                "path": "ai/prediction/feature_builder.py",
                "finding": "active codebase contains both 0.80 and legacy 0.60 acceptance thresholds",
                "fix": "make config.py the operational source of truth and rename any training-only threshold",
            }
        )
    if (
        '"source_id": payload.get("source_id")' not in batch_text
        or '"document_db_id": payload.get("document_db_id")' not in batch_text
    ):
        findings.append(
            {
                "severity": "high",
                "path": "ai/prediction/batch_inference.py",
                "finding": "batch responses do not preserve source_id and document_db_id",
                "fix": "copy all five lineage fields into every normalized batch result",
            }
        )
    if "print(f\"Warning: Payload missing" in runner_text:
        findings.append(
            {
                "severity": "high",
                "path": "scripts/run_real_payloads.py",
                "finding": "handoff validation only prints warnings and continues",
                "fix": "validate the 20-item contract, keep invalid test cases, and normalize each error into a failed result",
            }
        )
    if "build_prediction_log_payload" not in runner_text:
        findings.append(
            {
                "severity": "high",
                "path": "scripts/run_real_payloads.py",
                "finding": "the official Week 7 runner does not regenerate prediction log payloads",
                "fix": "write one DB payload per result to outputs/db_integration/week7_prediction_log_payloads.json",
            }
        )
    if (
        'result_invalid.get("error") == "validation_error"' in smoke_text
        and "build_rag_filter_metadata" not in smoke_text
    ):
        findings.append(
            {
                "severity": "medium",
                "path": "scripts/week7_prediction_ci_smoke_test.py",
                "finding": "CI smoke accepts a non-normalized error and mocks RAG/UI builders inline",
                "fix": "require status=failed and call the production log/RAG/UI builder paths",
            }
        )
    missing_requirements = [
        dependency
        for dependency in ("psycopg2-binary", "python-dotenv")
        if dependency not in requirements
    ]
    if missing_requirements:
        findings.append(
            {
                "severity": "high",
                "path": "requirements.txt",
                "finding": f"DB/runtime dependencies are missing: {missing_requirements}",
                "fix": "add the dependencies or document that the shared root requirements owns them",
            }
        )
    if model_card.get("confidence_threshold") == 0.60:
        findings.append(
            {
                "severity": "medium",
                "path": "ai/prediction/models/model_card.json",
                "finding": "model card still exposes 0.60 without the Week 7 staging threshold",
                "fix": "record both model-training metadata and staging_acceptance_threshold=0.80",
            }
        )
    if not model_card.get("training_environment"):
        findings.append(
            {
                "severity": "medium",
                "path": "ai/prediction/models/model_card.json",
                "finding": "model card does not record the claimed training environment/version",
                "fix": "add Python, scikit-learn, numpy, pandas and joblib versions",
            }
        )
    if (
        "`document_db_id` | `document_db_id`" in prediction_log_contract_text
        or "confidence >= 0.60" in prediction_log_contract_text
    ):
        findings.append(
            {
                "severity": "high",
                "path": "docs/prediction_log_contract.md",
                "finding": "contract uses the old DB column and old confidence policy",
                "fix": "map document_db_id to prediction_logs.document_id and document the 0.80 staging gate",
            }
        )
    if (
        "Safe for automatic RAG indexing and filtering" in prediction_contract_text
        or "currently `0.60`" in prediction_contract_text
    ):
        findings.append(
            {
                "severity": "high",
                "path": "docs/prediction_contract.md",
                "finding": "legacy contract permits unsafe automatic RAG filtering at 0.60",
                "fix": "use soft metadata by default and require accepted >=0.80 plus trust/manual review for hard filtering",
            }
        )
    if "Total payloads" in api_contract_text and "**8**" in api_contract_text:
        findings.append(
            {
                "severity": "medium",
                "path": "docs/week7_prediction_api_contract.md",
                "finding": "API contract still claims an 8-payload handoff",
                "fix": "reference Duy's current 20-payload batch and preserve platform IDs",
            }
        )

    return {
        "active_files": files,
        "active_files_complete": all(files.values()),
        "findings": findings,
        "cleanup_candidates": TUONG_CLEANUP_CANDIDATES,
    }


def _run_tuong_command(
    tuong_root: Path,
    command: list[str],
    display_command: str,
) -> dict[str, Any]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            command,
            cwd=tuong_root,
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
    combined = f"{completed.stdout}\n{completed.stderr}"
    error_summary = [
        line.strip()
        for line in combined.splitlines()
        if (
            "Error" in line
            or "ERROR" in line
            or "ModuleNotFoundError" in line
            or "failed" in line.lower()
        )
    ][-14:]
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "command": display_command,
        "error_summary": error_summary,
    }


def run_tuong_checks(tuong_root: Path) -> dict[str, Any]:
    return {
        "unit_tests": _run_tuong_command(
            tuong_root,
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ai_tests/",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            "python -m pytest tests/ai_tests/ -q -p no:cacheprovider",
        ),
        "ci_smoke": _run_tuong_command(
            tuong_root,
            [sys.executable, "scripts/week7_prediction_ci_smoke_test.py"],
            "python scripts/week7_prediction_ci_smoke_test.py",
        ),
    }


def build_mapping_summary(
    tuong_root: Path = DEFAULT_TUONG_ROOT,
) -> dict[str, Any]:
    duy_contract = inspect_duy_payloads()
    tuong_input = inspect_tuong_input_copy(tuong_root, duy_contract)
    tuong_outputs = inspect_tuong_outputs(tuong_root, duy_contract)
    code_audit = inspect_tuong_code(tuong_root)
    blocking_findings = [
        finding
        for finding in code_audit["findings"]
        if finding["severity"] in {"blocking", "high"}
    ]
    if tuong_input["status"] != "passed":
        blocking_findings.append(
            {
                "severity": "blocking",
                "path": TUONG_OUTPUT_FILES["input_copy"],
                "finding": "Tuong has not copied Duy's current 20-payload batch",
                "fix": "replace the input copy with the exact Duy batch without removing invalid test cases",
            }
        )
    if tuong_outputs["prediction_results"]["status"] != "passed":
        blocking_findings.append(
            {
                "severity": "blocking",
                "path": TUONG_OUTPUT_FILES["prediction_results"],
                "finding": "prediction result count/lineage is stale or incomplete",
                "fix": "rerun all 20 payloads and preserve one normalized result per input",
            }
        )
    if tuong_outputs["prediction_log_payloads"]["status"] != "passed":
        blocking_findings.append(
            {
                "severity": "blocking",
                "path": TUONG_OUTPUT_FILES["prediction_log_payloads"],
                "finding": "prediction log payload file does not cover the current batch",
                "fix": "regenerate one Phat-compatible log payload per prediction result",
            }
        )
    if not tuong_outputs["database_insert_proof"]["passed"]:
        blocking_findings.append(
            {
                "severity": "blocking",
                "path": TUONG_OUTPUT_FILES["prediction_log_insert_result"],
                "finding": "no real PostgreSQL insert/query-back result is present",
                "fix": "insert current logs into Phat's DB, query them back, and save the result JSON",
            }
        )
    if not tuong_outputs["ui_fixtures"]["real_duy_lineage_passed"]:
        blocking_findings.append(
            {
                "severity": "high",
                "path": "outputs/ui_fixtures/",
                "finding": "UI fixtures use synthetic source/document IDs instead of Duy/Phat lineage",
                "fix": "regenerate UI fixtures from the current Week 7 results and review queue",
            }
        )

    contract_passed = duy_contract["status"] == "passed"
    output_contract_passed = tuong_outputs["output_contract_passed"]
    status = (
        "passed"
        if contract_passed and output_contract_passed and not blocking_findings
        else "blocked_on_tuong_refresh"
    )
    return {
        "schema_version": "duy_tuong_week7_mapping_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "handoff_contract_passed": contract_passed,
        "tuong_output_contract_passed": output_contract_passed,
        "prediction_ci_proof_passed": False,
        "database_insert_proof_passed": tuong_outputs[
            "database_insert_proof"
        ]["passed"],
        "source_repositories": {
            "duy": _portable_path(PROJECT_ROOT),
            "tuong": _portable_path(tuong_root),
            "tuong_commit": _git_head(tuong_root),
        },
        "canonical_identity": {
            "source_id_map": EXPECTED_SOURCE_IDS,
            "document_external_id": DATAFLOW_EXTERNAL_ID,
            "document_db_id": EXPECTED_DOCUMENT_DB_ID,
            "ingestion_run_id": duy_contract["full_document_identity"].get(
                "ingestion_run_id"
            ),
            "rule": (
                "source_id is Phat sources.id; document_db_id maps to "
                "prediction_logs.document_id; ingestion_run_id is never source_id"
            ),
        },
        "duy_input_contract": duy_contract,
        "tuong_input_copy": tuong_input,
        "tuong_output_contract": tuong_outputs,
        "tuong_code_audit": code_audit,
        "tuong_execution": {
            "unit_tests": {
                "status": "not_run",
                "command": "python -m pytest tests/ai_tests/ -q -p no:cacheprovider",
            },
            "ci_smoke": {
                "status": "not_run",
                "command": "python scripts/week7_prediction_ci_smoke_test.py",
            },
        },
        "cleanup_candidates": TUONG_CLEANUP_CANDIDATES,
        "blocking_findings": blocking_findings,
        "required_tuong_actions": [
            "Copy Duy's exact 20-payload batch and keep the quality/invalid test cases.",
            "Return 20 normalized results with all lineage fields and all four statuses where expected.",
            "Make batch_inference preserve source_id and document_db_id.",
            "Regenerate 20 prediction-log payloads using document_db_id -> prediction_logs.document_id.",
            "Run a real PostgreSQL insert and save query-back evidence instead of only a one-row dry-run.",
            "Regenerate UI fixtures from Duy/Phat IDs; remove source_id=100-style sample lineage.",
            "Keep RAG metadata soft by default and test the production metadata builder.",
            "Unify the 0.80 staging policy across active docs/model metadata and add missing DB dependencies.",
        ],
        "commands_after_tuong_patch": {
            "copy_input": (
                "copy Duy outputs/prediction_payloads/"
                "tuong_week7_prediction_payloads.json to Tuong "
                "outputs/prediction_payloads/"
            ),
            "run_predictions": (
                "python scripts/run_real_payloads.py --input "
                "outputs/prediction_payloads/tuong_week7_prediction_payloads.json"
            ),
            "unit_tests": "python -m pytest tests/ai_tests/ -q",
            "ci_smoke": "python scripts/week7_prediction_ci_smoke_test.py",
            "db_dry_run": (
                "python scripts/insert_prediction_logs_to_postgres.py "
                "--input outputs/db_integration/week7_prediction_log_payloads.json "
                "--dry-run"
            ),
            "db_write": (
                "python scripts/insert_prediction_logs_to_postgres.py "
                "--input outputs/db_integration/week7_prediction_log_payloads.json"
            ),
        },
        "notes": [
            "Tuong's current 8-result file is useful evaluation history but does not cover Duy's current 20-payload batch.",
            "The four-state UI fixture is contract-shaped but uses synthetic IDs and is not real lineage evidence.",
            "Phat's separate Week 7 evidence reports 10 prediction_logs; it does not prove the current Duy 20-payload batch was inserted by Tuong.",
            "The Tuong-owned repository was audited read-only; cleanup and source fixes require a Tuong-owner commit.",
        ],
    }


def build_external_proof(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "duy_tuong_week7_external_mapping_audit",
        "status": summary["status"],
        "handoff_contract_passed": summary["handoff_contract_passed"],
        "tuong_output_contract_passed": summary["tuong_output_contract_passed"],
        "prediction_ci_proof_passed": summary["prediction_ci_proof_passed"],
        "database_insert_proof_passed": summary["database_insert_proof_passed"],
        "canonical_identity": summary["canonical_identity"],
        "tuong_commit": summary["source_repositories"].get("tuong_commit"),
        "tuong_outputs": summary["tuong_output_contract"].get("files", {}),
        "blocking_findings": summary["blocking_findings"],
        "required_tuong_actions": summary["required_tuong_actions"],
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
        description="Build an auditable Duy-to-Tuong Week 7 mapping summary"
    )
    parser.add_argument("--tuong-root", type=Path, default=DEFAULT_TUONG_ROOT)
    parser.add_argument(
        "--run-tuong-checks",
        action="store_true",
        help="Run Tuong pytest and CI smoke commands with caches disabled",
    )
    args = parser.parse_args()

    summary = build_mapping_summary(args.tuong_root)
    if args.run_tuong_checks:
        summary["tuong_execution"] = run_tuong_checks(args.tuong_root)
        summary["prediction_ci_proof_passed"] = all(
            result.get("status") == "passed"
            for result in summary["tuong_execution"].values()
        )
        if not summary["prediction_ci_proof_passed"]:
            summary["blocking_findings"].append(
                {
                    "severity": "blocking",
                    "path": "tests/ai_tests/ and scripts/week7_prediction_ci_smoke_test.py",
                    "finding": "Tuong checks failed in the audited environment",
                    "fix": "install the pinned requirements in a clean Python 3.11 environment and rerun both commands",
                }
            )
    if (
        summary["handoff_contract_passed"]
        and summary["tuong_output_contract_passed"]
        and summary["prediction_ci_proof_passed"]
        and summary["database_insert_proof_passed"]
        and not summary["blocking_findings"]
    ):
        summary["status"] = "passed"
    else:
        summary["status"] = "blocked_on_tuong_refresh"

    summary_path, proof_path = write_outputs(summary)
    print(f"Wrote Tuong mapping summary: {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"Wrote Tuong external proof: {proof_path.relative_to(PROJECT_ROOT)}")
    print(f"Handoff contract: {summary['handoff_contract_passed']}")
    print(f"Tuong output contract: {summary['tuong_output_contract_passed']}")
    print(f"Prediction CI proof: {summary['prediction_ci_proof_passed']}")
    print(f"Database insert proof: {summary['database_insert_proof_passed']}")
    print(f"Mapping status: {summary['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
