from __future__ import annotations

from data_engineering.ingestion.excel_ingestor import run_excel_ingestion
from data_engineering.pipelines.ingestion_engine import load_source_config


def test_excel_ingestion_returns_success(tmp_path):
    config = load_source_config("data_engineering/configs/product_sales_excel.json")
    config["raw_output_path"] = str(tmp_path / "raw.xlsx")
    config["staging_output_path"] = str(tmp_path / "staging.csv")
    config["clean_output_path"] = str(tmp_path / "clean.csv")
    config["latest_log_path"] = str(tmp_path / "latest.json")
    config["run_log_dir"] = str(tmp_path / "runs")
    config["run_history_path"] = str(tmp_path / "history.jsonl")
    config["manifest_output_dir"] = str(tmp_path / "manifests")
    result = run_excel_ingestion(config)

    assert result["status"] == "success"
    assert result["records_valid"] == 1500
    assert result["selected_sheet"] == "Sheet1"
