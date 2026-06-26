from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from data_engineering.ingestion.api_ingestor import run_api_ingestion
from data_engineering.ingestion.csv_ingestor import run_csv_ingestion
from data_engineering.ingestion.excel_ingestor import run_excel_ingestion
from data_engineering.ingestion.pdf_ingestor import run_pdf_ingestion
from data_engineering.utils.path_utils import resolve_project_path


INGESTORS = {
    "csv": run_csv_ingestion,
    "excel": run_excel_ingestion,
    "api": run_api_ingestion,
    "pdf": run_pdf_ingestion,
}


def load_source_config(config_path: str | Path) -> dict[str, Any]:
    path = resolve_project_path(config_path)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_ingestion(source_config: dict[str, Any]) -> dict[str, Any]:
    source_type = source_config["source_type"]
    if source_type not in INGESTORS:
        raise ValueError(f"Unsupported source_type: {source_type}")
    return INGESTORS[source_type](source_config)


def run_configs(config_paths: list[str]) -> list[dict[str, Any]]:
    return [run_ingestion(load_source_config(config_path)) for config_path in config_paths]


def default_config_paths() -> list[str]:
    return [
        "data_engineering/configs/superstore_csv.json",
        "data_engineering/configs/product_sales_excel.json",
        "data_engineering/configs/dummyjson_products_api.json",
        "data_engineering/configs/dataflow_pdf.json",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DataVision ingestion pipeline")
    parser.add_argument("--config", action="append", help="Path to a source config JSON file")
    parser.add_argument("--all", action="store_true", help="Run all default source configs")
    args = parser.parse_args()

    config_paths = default_config_paths() if args.all or not args.config else args.config
    results = run_configs(config_paths)
    for result in results:
        print(f"{result['source_type']}: {result['status']} - {result['records_valid']} valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

