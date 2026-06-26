from __future__ import annotations

from data_engineering.pipelines.ingestion_engine import load_source_config, run_ingestion


def test_ingestion_engine_runs_config(tmp_path):
    config = load_source_config("data_engineering/configs/superstore_csv.json")
    config["raw_output_path"] = str(tmp_path / "raw.csv")
    config["staging_output_path"] = str(tmp_path / "staging.csv")
    config["clean_output_path"] = str(tmp_path / "clean.csv")
    config["latest_log_path"] = str(tmp_path / "latest.json")
    config["run_log_dir"] = str(tmp_path / "runs")
    config["run_history_path"] = str(tmp_path / "history.jsonl")
    config["manifest_output_dir"] = str(tmp_path / "manifests")
    result = run_ingestion(config)

    assert result["source_name"] == "superstore_sales_csv"
    assert result["status"] == "success"


def test_logs_use_project_relative_paths(tmp_path):
    config = load_source_config("data_engineering/configs/superstore_csv.json")
    config["raw_output_path"] = "week2/data/raw/csv/superstore_raw.csv"
    config["staging_output_path"] = "week2/data/staging/csv/superstore_staging.csv"
    config["clean_output_path"] = "week2/data/clean/csv/superstore_clean.csv"
    config["latest_log_path"] = str(tmp_path / "latest.json")
    config["run_log_dir"] = str(tmp_path / "runs")
    config["run_history_path"] = str(tmp_path / "history.jsonl")
    config["manifest_output_dir"] = str(tmp_path / "manifests")
    result = run_ingestion(config)

    for field in ("input_path_or_url", "raw_output_path", "staging_output_path", "clean_output_path"):
        value = result[field]
        assert value
        assert ":\\" not in value
