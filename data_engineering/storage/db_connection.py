from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from data_engineering.utils.path_utils import resolve_project_path


DEFAULT_CONFIG_PATH = "data_engineering/configs/db_config.example.json"


def load_db_config(config_path: str | Path | None = None) -> dict[str, Any]:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        # Environment variables and JSON config still work without python-dotenv.
        pass

    path = resolve_project_path(config_path or os.getenv("DATAVISION_DB_CONFIG") or DEFAULT_CONFIG_PATH)
    config: dict[str, Any] = {}
    if path is not None and path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))

    env_mapping = {
        "host": ("DB_HOST", "DATAVISION_DB_HOST"),
        "port": ("DB_PORT", "DATAVISION_DB_PORT"),
        "database": ("DB_NAME", "DATAVISION_DB_NAME"),
        "user": ("DB_USER", "DATAVISION_DB_USER"),
        "password": ("DB_PASSWORD", "DATAVISION_DB_PASSWORD"),
    }
    for key, env_names in env_mapping.items():
        value = next((os.getenv(env_name) for env_name in env_names if os.getenv(env_name)), None)
        if value:
            config[key] = int(value) if key == "port" else value
    return config


def build_connection_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    required = ["host", "port", "database", "user", "password"]
    missing = [field for field in required if not config.get(field)]
    if missing:
        raise ValueError(f"Missing database config fields: {missing}")
    return {field: config[field] for field in required}


def get_connection(config_path: str | Path | None = None):
    try:
        import psycopg2
    except ImportError as exc:
        raise ImportError("Install psycopg2-binary to enable PostgreSQL loading") from exc

    config = load_db_config(config_path)
    return psycopg2.connect(**build_connection_kwargs(config))
