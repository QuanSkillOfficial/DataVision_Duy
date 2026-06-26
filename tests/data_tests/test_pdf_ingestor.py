from __future__ import annotations

from pathlib import Path

from data_engineering.ingestion.pdf_ingestor import run_pdf_ingestion
from data_engineering.pipelines.ingestion_engine import load_source_config


def test_pdf_ingestion_creates_document_pages_jsonl(tmp_path):
    config = load_source_config("data_engineering/configs/dataflow_pdf.json")
    config["raw_output_path"] = str(tmp_path / "raw.pdf")
    config["staging_text_output_path"] = str(tmp_path / "text.txt")
    config["staging_output_path"] = str(tmp_path / "pages_staging.csv")
    config["clean_output_path"] = str(tmp_path / "pages_clean.csv")
    config["document_pages_output_path"] = str(tmp_path / "document_pages.jsonl")
    config["metadata_output_path"] = str(tmp_path / "metadata.json")
    config["latest_log_path"] = str(tmp_path / "latest.json")
    config["run_log_dir"] = str(tmp_path / "runs")
    config["run_history_path"] = str(tmp_path / "history.jsonl")
    config["manifest_output_dir"] = str(tmp_path / "manifests")
    result = run_pdf_ingestion(config)

    document_pages_path = Path(result["document_pages_output_path"])
    assert result["status"] == "success"
    assert result["records_valid"] == 36
    assert document_pages_path.exists()
    assert document_pages_path.read_text(encoding="utf-8").strip()
