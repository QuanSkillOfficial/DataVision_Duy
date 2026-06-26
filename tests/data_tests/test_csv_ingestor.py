from __future__ import annotations

import json

import pandas as pd

from data_engineering.ingestion.csv_ingestor import run_csv_ingestion
from data_engineering.pipelines.ingestion_engine import load_source_config


def _with_tmp_outputs(config, tmp_path):
    config = dict(config)
    config["raw_output_path"] = str(tmp_path / "raw.csv")
    config["staging_output_path"] = str(tmp_path / "staging.csv")
    config["clean_output_path"] = str(tmp_path / "clean.csv")
    config["latest_log_path"] = str(tmp_path / "latest.json")
    config["run_log_dir"] = str(tmp_path / "runs")
    config["run_history_path"] = str(tmp_path / "history.jsonl")
    config["manifest_output_dir"] = str(tmp_path / "manifests")
    return config


def test_csv_ingestion_returns_success(tmp_path):
    config = load_source_config("data_engineering/configs/superstore_csv.json")
    config = _with_tmp_outputs(config, tmp_path)
    result = run_csv_ingestion(config)

    assert result["status"] == "success"
    assert result["records_valid"] == 9994
    assert result["data_quality_score"] > 0


def test_missing_required_fields_increases_records_invalid(tmp_path):
    input_path = tmp_path / "bad.csv"
    pd.DataFrame(
        [
            {"row_id": 1, "order_id": None, "sales": 10},
            {"row_id": 2, "order_id": "CA-001", "sales": 20},
        ]
    ).to_csv(input_path, index=False)

    config = {
        "source_name": "bad_csv",
        "source_type": "csv",
        "input_path": str(input_path),
        "raw_output_path": str(tmp_path / "raw.csv"),
        "staging_output_path": str(tmp_path / "staging.csv"),
        "clean_output_path": str(tmp_path / "clean.csv"),
        "latest_log_path": str(tmp_path / "latest.json"),
        "run_log_dir": str(tmp_path / "runs"),
        "run_history_path": str(tmp_path / "history.jsonl"),
        "manifest_output_dir": str(tmp_path / "manifests"),
        "required_fields": ["row_id", "order_id", "sales"],
        "optional_fields": [],
        "owner": "Nguyen Minh Duy",
    }

    result = run_csv_ingestion(config)

    assert result["status"] == "partial_success"
    assert result["records_invalid"] == 1
    assert json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))["run_id"]


def test_invalid_file_path_returns_failed_status(tmp_path):
    config = {
        "source_name": "missing_csv",
        "source_type": "csv",
        "input_path": str(tmp_path / "missing.csv"),
        "raw_output_path": str(tmp_path / "raw.csv"),
        "staging_output_path": str(tmp_path / "staging.csv"),
        "clean_output_path": str(tmp_path / "clean.csv"),
        "latest_log_path": str(tmp_path / "latest.json"),
        "run_log_dir": str(tmp_path / "runs"),
        "run_history_path": str(tmp_path / "history.jsonl"),
        "manifest_output_dir": str(tmp_path / "manifests"),
        "required_fields": ["id"],
        "optional_fields": [],
        "owner": "Nguyen Minh Duy",
    }

    result = run_csv_ingestion(config)

    assert result["status"] == "failed"
    assert "Input file not found" in result["error_message"]
