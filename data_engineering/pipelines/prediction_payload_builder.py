from __future__ import annotations

import json
import re
import csv
from itertools import islice
from pathlib import Path
from typing import Any

from data_engineering.utils.path_utils import resolve_project_path
from data_engineering.pipelines.handoff_context import (
    identity_for_document,
    identity_for_source,
    load_database_identity_map,
)


def _read_json(path: str | Path) -> dict[str, Any]:
    resolved = resolve_project_path(path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def _safe_document_id(file_name: str) -> str:
    stem = Path(file_name).stem.lower()
    safe_stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"doc_{safe_stem or 'unknown'}"


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = resolve_project_path(path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")
    records: list[dict[str, Any]] = []
    with resolved.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _read_csv_preview(
    path: str | Path,
    max_rows: int = 5,
    start_row: int = 0,
) -> list[dict[str, Any]]:
    resolved = resolve_project_path(path)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with resolved.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(islice(reader, start_row, start_row + max_rows))


def _latest_run_by_source(source_name: str, run_log_dir: str | Path = "logs/runs") -> dict[str, Any]:
    resolved = resolve_project_path(run_log_dir)
    if resolved is None or not resolved.exists():
        raise FileNotFoundError(f"Run log directory not found: {run_log_dir}")
    matches = []
    for path in resolved.glob("*.json"):
        run = json.loads(path.read_text(encoding="utf-8"))
        if run.get("source_name") == source_name and run.get("status") in {"success", "partial_success"}:
            matches.append(run)
    if not matches:
        raise FileNotFoundError(f"No successful run log found for source: {source_name}")
    return max(matches, key=lambda item: item.get("end_time") or "")


def _payload_base(
    *,
    document_external_id: str,
    source_name: str,
    ingestion_run_id: str,
    file_name: str,
    file_type: str,
    file_size: int | None,
    text: str,
    source_system: str,
    parsing_status: str = "ready",
    source_id: int | None = None,
    document_db_id: int | None = None,
    num_pages: int = 0,
    raw_output_path: str | None = None,
    staging_output_path: str | None = None,
    clean_output_path: str | None = None,
    records_read: int = 0,
    records_valid: int = 0,
    records_invalid: int = 0,
    test_case: str = "normal",
    expected_status_hint: str | None = None,
    page_range: str | None = None,
    data_quality_score: float | None = None,
    file_hash_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "document_id": document_external_id,
        "document_external_id": document_external_id,
        "document_db_id": document_db_id,
        "source_id": source_id,
        "source_name": source_name,
        "ingestion_run_id": ingestion_run_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "text_length": len(text),
        "num_pages": num_pages,
        "page_range": page_range,
        "source_system": source_system,
        "extracted_text": text,
        "parsing_status": parsing_status,
        "raw_output_path": raw_output_path,
        "staging_output_path": staging_output_path,
        "clean_output_path": clean_output_path,
        "records_read": records_read,
        "records_valid": records_valid,
        "records_invalid": records_invalid,
        "test_case": test_case,
        "expected_status_hint": expected_status_hint,
        "data_quality_score": data_quality_score,
        "file_hash_sha256": file_hash_sha256,
    }


def _structured_text_from_rows(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [title, "Extracted tabular preview:"]
    for index, row in enumerate(rows, start=1):
        compact = ", ".join(f"{key}: {value}" for key, value in row.items() if value not in {None, ""})
        lines.append(f"Row {index}: {compact}")
    return "\n".join(lines)


def build_pdf_prediction_payload(
    *,
    ingestion_log_path: str | Path = "week2/logs/pdf_ingestion_log.json",
    metadata_path: str | Path = "week2/logs/pdf_metadata.json",
    source_system: str = "manual_upload",
    source_id: int | None = None,
    document_db_id: int | None = None,
) -> dict[str, Any]:
    ingestion_log = _read_json(ingestion_log_path)
    metadata = _read_json(metadata_path)
    input_relative = ingestion_log["input_path_or_url"]
    input_path = resolve_project_path(input_relative)
    text_relative_path = (
        metadata.get("staging_text_output_path")
        or metadata.get("staging_output_path")
        or ingestion_log.get("staging_text_output_path")
        or ingestion_log["staging_output_path"]
    )
    staging_path = resolve_project_path(text_relative_path)
    extracted_text = staging_path.read_text(encoding="utf-8") if staging_path and staging_path.exists() else ""
    file_name = input_path.name if input_path else metadata.get("file_name", "unknown.pdf")

    parsing_status = "ready" if ingestion_log.get("status") == "success" else ingestion_log.get("status")
    if not extracted_text.strip() and parsing_status == "ready":
        parsing_status = "partial_success"

    document_external_id = metadata.get("document_id") or ingestion_log.get("document_id") or _safe_document_id(file_name)
    source_name = metadata.get("source_name") or ingestion_log.get("source_name")
    ingestion_run_id = ingestion_log["run_id"]

    return {
        # Backward-compatible alias for earlier Tuong contracts.
        "document_id": document_external_id,
        "document_external_id": document_external_id,
        "document_db_id": document_db_id,
        "source_id": source_id,
        "source_name": source_name,
        "file_name": file_name,
        "file_type": Path(file_name).suffix.lower().lstrip("."),
        "file_size": input_path.stat().st_size if input_path and input_path.exists() else metadata.get("file_size_bytes"),
        "text_length": metadata.get("total_characters") or len(extracted_text),
        "num_pages": metadata.get("page_count") or metadata.get("total_pages", 0),
        "page_range": f"1-{metadata.get('page_count') or metadata.get('total_pages', 0)}",
        "source_system": source_system,
        "extracted_text": extracted_text,
        "ingestion_run_id": ingestion_run_id,
        "raw_output_path": ingestion_log.get("raw_output_path"),
        "staging_output_path": text_relative_path,
        "staging_csv_output_path": metadata.get("staging_csv_output_path"),
        "document_pages_output_path": metadata.get("document_pages_output_path"),
        "clean_output_path": ingestion_log.get("clean_output_path"),
        "records_read": ingestion_log.get("records_read", 0),
        "records_valid": ingestion_log.get("records_valid", 0),
        "records_invalid": ingestion_log.get("records_invalid", 0),
        "empty_pages": metadata.get("empty_pages", []),
        "empty_page_count": metadata.get("empty_page_count", 0),
        "parsing_status": parsing_status,
        "data_quality_score": ingestion_log.get("data_quality_score"),
        "file_hash_sha256": (ingestion_log.get("file_manifest") or {}).get("file_hash_sha256"),
    }


def build_tuong_prediction_test_payloads(
    db_identity_map: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build 10 Duy-style payloads for Tuong prediction and safety tests.

    The list intentionally includes normal, low-text, empty-text, and invalid
    cases so Tuong can test accepted / needs_review / waiting_for_source /
    failed handling in batch inference.
    """
    db_identity_map = db_identity_map or load_database_identity_map()
    pdf_source_id = identity_for_source(db_identity_map, "dataflow_technical_report_pdf")
    pdf_document_id = identity_for_document(db_identity_map, "doc_dataflow_technical_report")
    pdf_payload = build_pdf_prediction_payload(
        source_id=pdf_source_id,
        document_db_id=pdf_document_id,
    )
    pages = _read_jsonl("outputs/rag_handoff/document_pages.jsonl")
    pages_by_number = {page["page_number"]: page for page in pages}
    pdf_run = _latest_run_by_source("dataflow_technical_report_pdf")
    csv_run = _latest_run_by_source("superstore_sales_csv")
    excel_run = _latest_run_by_source("product_sales_region_excel")
    api_run = _latest_run_by_source("dummyjson_products_api")

    def page_text(*page_numbers: int) -> str:
        return "\n\n".join(pages_by_number[number]["text"] for number in page_numbers if number in pages_by_number)

    csv_text = _structured_text_from_rows(
        "Superstore sales CSV with orders, customers, products, sales, profit, and discount fields.",
        _read_csv_preview("week2/data/clean/csv/superstore_clean.csv"),
    )
    excel_text = _structured_text_from_rows(
        "Product sales region Excel with product, region, salesperson, shipping, payment, and return fields.",
        _read_csv_preview("week2/data/clean/excel/product_sales_region_clean.csv"),
    )
    api_text = _structured_text_from_rows(
        "DummyJSON products API response with product catalog, price, stock, rating, dimensions, and shipping fields.",
        _read_csv_preview("week2/data/clean/api/dummyjson_products_clean.csv"),
    )

    payloads: list[dict[str, Any]] = []
    payloads.append({**pdf_payload, "test_case": "full_pdf_document", "expected_status_hint": "accepted_or_needs_review"})
    payloads.append(
        _payload_base(
            document_external_id="doc_dataflow_technical_report_intro_pages",
            source_name=pdf_run["source_name"],
            ingestion_run_id=pdf_run["run_id"],
            file_name="DataFlow_Technical_Report_intro_pages.pdf",
            file_type="pdf",
            file_size=pdf_payload.get("file_size"),
            text=page_text(4, 5),
            source_system="manual_upload",
            num_pages=2,
            raw_output_path=pdf_run.get("raw_output_path"),
            staging_output_path=pdf_run.get("staging_text_output_path"),
            clean_output_path=pdf_run.get("clean_output_path"),
            records_read=2,
            records_valid=2,
            test_case="pdf_intro_section",
            expected_status_hint="accepted_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_dataflow_technical_report_architecture_page",
            source_name=pdf_run["source_name"],
            ingestion_run_id=pdf_run["run_id"],
            file_name="DataFlow_Technical_Report_architecture_page.pdf",
            file_type="pdf",
            file_size=pdf_payload.get("file_size"),
            text=page_text(8),
            source_system="manual_upload",
            num_pages=1,
            raw_output_path=pdf_run.get("raw_output_path"),
            staging_output_path=pdf_run.get("staging_text_output_path"),
            clean_output_path=pdf_run.get("clean_output_path"),
            records_read=1,
            records_valid=1,
            test_case="pdf_architecture_page",
            expected_status_hint="accepted_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_dataflow_technical_report_related_work",
            source_name=pdf_run["source_name"],
            ingestion_run_id=pdf_run["run_id"],
            file_name="DataFlow_Technical_Report_related_work.pdf",
            file_type="pdf",
            file_size=pdf_payload.get("file_size"),
            text=page_text(6, 7),
            source_system="manual_upload",
            num_pages=2,
            raw_output_path=pdf_run.get("raw_output_path"),
            staging_output_path=pdf_run.get("staging_text_output_path"),
            clean_output_path=pdf_run.get("clean_output_path"),
            records_read=2,
            records_valid=2,
            test_case="pdf_related_work_section",
            expected_status_hint="accepted_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_superstore_sales_csv_summary",
            source_name=csv_run["source_name"],
            ingestion_run_id=csv_run["run_id"],
            file_name="superstore_clean.csv",
            file_type="csv",
            file_size=(csv_run.get("file_manifest") or {}).get("file_size_bytes"),
            text=csv_text,
            source_system="csv_upload",
            raw_output_path=csv_run.get("raw_output_path"),
            staging_output_path=csv_run.get("staging_output_path"),
            clean_output_path=csv_run.get("clean_output_path"),
            records_read=csv_run.get("records_read", 0),
            records_valid=csv_run.get("records_valid", 0),
            records_invalid=csv_run.get("records_invalid", 0),
            test_case="csv_structured_summary",
            expected_status_hint="accepted_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_product_sales_region_excel_summary",
            source_name=excel_run["source_name"],
            ingestion_run_id=excel_run["run_id"],
            file_name="product_sales_region_clean.csv",
            file_type="xlsx",
            file_size=(excel_run.get("file_manifest") or {}).get("file_size_bytes"),
            text=excel_text,
            source_system="excel_upload",
            raw_output_path=excel_run.get("raw_output_path"),
            staging_output_path=excel_run.get("staging_output_path"),
            clean_output_path=excel_run.get("clean_output_path"),
            records_read=excel_run.get("records_read", 0),
            records_valid=excel_run.get("records_valid", 0),
            records_invalid=excel_run.get("records_invalid", 0),
            test_case="excel_structured_summary",
            expected_status_hint="accepted_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_dummyjson_products_api_summary",
            source_name=api_run["source_name"],
            ingestion_run_id=api_run["run_id"],
            file_name="dummyjson_products_clean.csv",
            file_type="json",
            file_size=(api_run.get("file_manifest") or {}).get("file_size_bytes"),
            text=api_text,
            source_system="api",
            raw_output_path=api_run.get("raw_output_path"),
            staging_output_path=api_run.get("staging_output_path"),
            clean_output_path=api_run.get("clean_output_path"),
            records_read=api_run.get("records_read", 0),
            records_valid=api_run.get("records_valid", 0),
            records_invalid=api_run.get("records_invalid", 0),
            test_case="api_structured_summary",
            expected_status_hint="accepted_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_short_text_quality_gate",
            source_name=pdf_run["source_name"],
            ingestion_run_id=pdf_run["run_id"],
            file_name="short_text_sample.pdf",
            file_type="pdf",
            file_size=128,
            text="Short text.",
            source_system="manual_upload",
            num_pages=1,
            parsing_status="partial_success",
            test_case="short_extracted_text_quality_gate",
            expected_status_hint="waiting_for_source_or_needs_review",
        )
    )
    payloads.append(
        _payload_base(
            document_external_id="doc_empty_text_quality_gate",
            source_name=pdf_run["source_name"],
            ingestion_run_id=pdf_run["run_id"],
            file_name="empty_text_sample.pdf",
            file_type="pdf",
            file_size=0,
            text="",
            source_system="manual_upload",
            num_pages=1,
            parsing_status="failed",
            records_read=1,
            records_valid=0,
            records_invalid=1,
            test_case="empty_extracted_text_quality_gate",
            expected_status_hint="waiting_for_source",
        )
    )

    invalid_payload = _payload_base(
        document_external_id="doc_missing_file_name_validation",
        source_name=pdf_run["source_name"],
        ingestion_run_id=pdf_run["run_id"],
        file_name="missing_file_name.pdf",
        file_type="pdf",
        file_size=256,
        text="This payload intentionally omits file_name so Tuong can test normalized validation errors.",
        source_system="manual_upload",
        num_pages=1,
        parsing_status="ready",
        test_case="missing_required_file_name",
        expected_status_hint="failed",
    )
    invalid_payload.pop("file_name")
    payloads.append(invalid_payload)

    runs_by_source = {
        run["source_name"]: run
        for run in (pdf_run, csv_run, excel_run, api_run)
    }
    page_ranges = {
        "full_pdf_document": "1-36",
        "pdf_intro_section": "4-5",
        "pdf_architecture_page": "8",
        "pdf_related_work_section": "6-7",
        "short_extracted_text_quality_gate": "1",
        "empty_extracted_text_quality_gate": "1",
        "missing_required_file_name": "1",
    }
    for payload in payloads:
        run = runs_by_source.get(payload.get("source_name"), {})
        manifest = run.get("file_manifest") or {}
        payload["source_id"] = identity_for_source(db_identity_map, payload.get("source_name", ""))
        payload["document_db_id"] = (
            pdf_document_id
            if payload.get("document_external_id") == "doc_dataflow_technical_report"
            else None
        )
        payload["page_range"] = page_ranges.get(payload.get("test_case"))
        payload["data_quality_score"] = run.get("data_quality_score")
        payload["file_hash_sha256"] = manifest.get("file_hash_sha256")
        if payload.get("test_case") in {
            "short_extracted_text_quality_gate",
            "empty_extracted_text_quality_gate",
            "missing_required_file_name",
        }:
            payload["data_quality_score"] = None
            payload["file_hash_sha256"] = None
        payload["database_identity_status"] = db_identity_map.get("status")
    return payloads


def build_tuong_additional_prediction_test_payloads(
    db_identity_map: dict[str, Any] | None = None,
    base_payloads: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build Week 7 cases 11-20 without changing the original 10-case batch.

    The additional cases cover new real PDF sections, non-overlapping
    structured-data samples, an unknown file type, missing platform lineage,
    and invalid numeric metadata.
    """
    db_identity_map = db_identity_map or load_database_identity_map()
    base_payloads = base_payloads or build_tuong_prediction_test_payloads(db_identity_map)
    by_case = {payload["test_case"]: payload for payload in base_payloads}

    pdf_payload = by_case["full_pdf_document"]
    csv_payload = by_case["csv_structured_summary"]
    excel_payload = by_case["excel_structured_summary"]
    api_payload = by_case["api_structured_summary"]
    pages = _read_jsonl("outputs/rag_handoff/document_pages.jsonl")
    pages_by_number = {page["page_number"]: page for page in pages}

    def page_text(*page_numbers: int) -> str:
        return "\n\n".join(
            pages_by_number[number]["text"]
            for number in page_numbers
            if number in pages_by_number
        )

    def derived_pdf_payload(
        *,
        document_external_id: str,
        file_name: str,
        page_numbers: tuple[int, ...],
        test_case: str,
    ) -> dict[str, Any]:
        is_contiguous = all(
            current + 1 == following
            for current, following in zip(page_numbers, page_numbers[1:])
        )
        if len(page_numbers) == 1:
            page_range = str(page_numbers[0])
        elif is_contiguous:
            page_range = f"{page_numbers[0]}-{page_numbers[-1]}"
        else:
            page_range = ",".join(str(number) for number in page_numbers)
        return _payload_base(
            document_external_id=document_external_id,
            source_name=pdf_payload["source_name"],
            ingestion_run_id=pdf_payload["ingestion_run_id"],
            file_name=file_name,
            file_type="pdf",
            file_size=pdf_payload.get("file_size"),
            text=page_text(*page_numbers),
            source_system=pdf_payload.get("source_system") or "manual_upload",
            source_id=pdf_payload.get("source_id"),
            document_db_id=None,
            num_pages=len(page_numbers),
            page_range=page_range,
            raw_output_path=pdf_payload.get("raw_output_path"),
            staging_output_path=pdf_payload.get("staging_output_path"),
            clean_output_path=pdf_payload.get("clean_output_path"),
            records_read=len(page_numbers),
            records_valid=len(page_numbers),
            test_case=test_case,
            expected_status_hint="accepted_or_needs_review",
            data_quality_score=pdf_payload.get("data_quality_score"),
            file_hash_sha256=pdf_payload.get("file_hash_sha256"),
        )

    csv_rows = _read_csv_preview(
        "week2/data/clean/csv/superstore_clean.csv",
        max_rows=6,
        start_row=120,
    )
    excel_rows = _read_csv_preview(
        "week2/data/clean/excel/product_sales_region_clean.csv",
        max_rows=6,
        start_row=300,
    )
    api_rows = _read_csv_preview(
        "week2/data/clean/api/dummyjson_products_clean.csv",
        max_rows=6,
        start_row=10,
    )

    payloads = [
        derived_pdf_payload(
            document_external_id="doc_dataflow_system_operators_pages",
            file_name="DataFlow_Technical_Report_system_operators_pages.pdf",
            page_numbers=(9, 10),
            test_case="pdf_system_operators_section",
        ),
        derived_pdf_payload(
            document_external_id="doc_dataflow_pipeline_api_pages",
            file_name="DataFlow_Technical_Report_pipeline_api_pages.pdf",
            page_numbers=(11, 12),
            test_case="pdf_pipeline_api_section",
        ),
        derived_pdf_payload(
            document_external_id="doc_dataflow_agent_workflow_pages",
            file_name="DataFlow_Technical_Report_agent_workflow_pages.pdf",
            page_numbers=(14, 15),
            test_case="pdf_agent_workflow_section",
        ),
        derived_pdf_payload(
            document_external_id="doc_dataflow_agentic_rag_evaluation_pages",
            file_name="DataFlow_Technical_Report_agentic_rag_evaluation.pdf",
            page_numbers=(25, 29),
            test_case="pdf_agentic_rag_evaluation_section",
        ),
        _payload_base(
            document_external_id="doc_superstore_order_profitability_sample",
            source_name=csv_payload["source_name"],
            ingestion_run_id=csv_payload["ingestion_run_id"],
            file_name="superstore_order_profitability_sample.csv",
            file_type="csv",
            file_size=csv_payload.get("file_size"),
            text=_structured_text_from_rows(
                "Superstore order sample for customer, product, discount, sales, and profit classification.",
                csv_rows,
            ),
            source_system=csv_payload.get("source_system") or "csv_upload",
            source_id=csv_payload.get("source_id"),
            raw_output_path=csv_payload.get("raw_output_path"),
            staging_output_path=csv_payload.get("staging_output_path"),
            clean_output_path=csv_payload.get("clean_output_path"),
            records_read=len(csv_rows),
            records_valid=len(csv_rows),
            test_case="csv_order_profitability_sample",
            expected_status_hint="accepted_or_needs_review",
            data_quality_score=csv_payload.get("data_quality_score"),
            file_hash_sha256=csv_payload.get("file_hash_sha256"),
        ),
        _payload_base(
            document_external_id="doc_product_sales_region_sample",
            source_name=excel_payload["source_name"],
            ingestion_run_id=excel_payload["ingestion_run_id"],
            file_name="product_sales_region_sample.xlsx",
            file_type="xlsx",
            file_size=excel_payload.get("file_size"),
            text=_structured_text_from_rows(
                "Product sales regional sample for salesperson, shipment, payment, and return analysis.",
                excel_rows,
            ),
            source_system=excel_payload.get("source_system") or "excel_upload",
            source_id=excel_payload.get("source_id"),
            raw_output_path=excel_payload.get("raw_output_path"),
            staging_output_path=excel_payload.get("staging_output_path"),
            clean_output_path=excel_payload.get("clean_output_path"),
            records_read=len(excel_rows),
            records_valid=len(excel_rows),
            test_case="excel_regional_sales_sample",
            expected_status_hint="accepted_or_needs_review",
            data_quality_score=excel_payload.get("data_quality_score"),
            file_hash_sha256=excel_payload.get("file_hash_sha256"),
        ),
        _payload_base(
            document_external_id="doc_dummyjson_inventory_sample",
            source_name=api_payload["source_name"],
            ingestion_run_id=api_payload["ingestion_run_id"],
            file_name="dummyjson_inventory_sample.json",
            file_type="json",
            file_size=api_payload.get("file_size"),
            text=_structured_text_from_rows(
                "DummyJSON inventory sample for catalog, stock, rating, dimensions, and shipping analysis.",
                api_rows,
            ),
            source_system=api_payload.get("source_system") or "api",
            source_id=api_payload.get("source_id"),
            raw_output_path=api_payload.get("raw_output_path"),
            staging_output_path=api_payload.get("staging_output_path"),
            clean_output_path=api_payload.get("clean_output_path"),
            records_read=len(api_rows),
            records_valid=len(api_rows),
            test_case="api_inventory_sample",
            expected_status_hint="accepted_or_needs_review",
            data_quality_score=api_payload.get("data_quality_score"),
            file_hash_sha256=api_payload.get("file_hash_sha256"),
        ),
        _payload_base(
            document_external_id="doc_dataflow_technical_notes_markdown",
            source_name=pdf_payload["source_name"],
            ingestion_run_id=pdf_payload["ingestion_run_id"],
            file_name="DataFlow_technical_notes.md",
            file_type="md",
            file_size=len(page_text(5).encode("utf-8")),
            text=page_text(5),
            source_system="local_directory",
            source_id=pdf_payload.get("source_id"),
            num_pages=1,
            page_range="5",
            records_read=1,
            records_valid=1,
            test_case="unknown_file_type_markdown",
            expected_status_hint="accepted_or_needs_review_unknown_file_type",
            data_quality_score=pdf_payload.get("data_quality_score"),
            file_hash_sha256=None,
        ),
    ]

    missing_document_external_id = _payload_base(
        document_external_id="doc_missing_document_external_id_validation",
        source_name=pdf_payload["source_name"],
        ingestion_run_id=pdf_payload["ingestion_run_id"],
        file_name="missing_document_external_id.pdf",
        file_type="pdf",
        file_size=1024,
        text=page_text(4),
        source_system="manual_upload",
        source_id=pdf_payload.get("source_id"),
        num_pages=1,
        page_range="4",
        test_case="missing_document_external_id",
        expected_status_hint="failed_contract_validation",
    )
    missing_document_external_id.pop("document_id")
    missing_document_external_id.pop("document_external_id")
    payloads.append(missing_document_external_id)

    invalid_file_size = _payload_base(
        document_external_id="doc_invalid_file_size_validation",
        source_name=pdf_payload["source_name"],
        ingestion_run_id=pdf_payload["ingestion_run_id"],
        file_name="invalid_file_size.pdf",
        file_type="pdf",
        file_size=None,
        text=page_text(8),
        source_system="manual_upload",
        source_id=pdf_payload.get("source_id"),
        num_pages=1,
        page_range="8",
        test_case="invalid_file_size_type",
        expected_status_hint="failed",
    )
    invalid_file_size["file_size"] = "not-a-number"
    payloads.append(invalid_file_size)

    for payload in payloads:
        payload["database_identity_status"] = db_identity_map.get("status")
    return payloads


def build_tuong_extended_prediction_test_payloads(
    db_identity_map: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build the original 10 cases plus Week 7 cases 11-20."""
    db_identity_map = db_identity_map or load_database_identity_map()
    base_payloads = build_tuong_prediction_test_payloads(db_identity_map)
    additional_payloads = build_tuong_additional_prediction_test_payloads(
        db_identity_map,
        base_payloads,
    )
    return base_payloads + additional_payloads
