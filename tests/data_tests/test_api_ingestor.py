from __future__ import annotations

import shutil

from data_engineering.ingestion.api_ingestor import run_api_ingestion
from data_engineering.pipelines.ingestion_engine import load_source_config
from data_engineering.utils.path_utils import resolve_project_path


def test_api_ingestion_returns_success_with_cached_response(tmp_path):
    config = load_source_config("data_engineering/configs/dummyjson_products_api.json")
    cached_raw = tmp_path / "cached_raw.json"
    shutil.copy2(resolve_project_path(config["raw_output_path"]), cached_raw)
    config["use_cached_response"] = True
    config["raw_output_path"] = str(cached_raw)
    config["staging_output_path"] = str(tmp_path / "staging.csv")
    config["clean_output_path"] = str(tmp_path / "clean.csv")
    config["latest_log_path"] = str(tmp_path / "latest.json")
    config["run_log_dir"] = str(tmp_path / "runs")
    config["run_history_path"] = str(tmp_path / "history.jsonl")
    config["manifest_output_dir"] = str(tmp_path / "manifests")
    result = run_api_ingestion(config)

    assert result["status"] == "success"
    assert result["records_valid"] == 30
    assert result["api_fallback_error"] == "used cached API response"
