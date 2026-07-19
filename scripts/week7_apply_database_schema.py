from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.storage.db_connection import get_connection


DEFAULT_SCHEMA = (
    PROJECT_ROOT / "deployment/database/init/10_phat_schema_v4_fixed.sql"
)


def resolve_schema_path(value: str | Path | None = None) -> Path:
    configured = value or os.getenv("PHAT_SCHEMA_PATH") or DEFAULT_SCHEMA
    path = Path(configured)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Phat schema contract not found: {path}")
    return path


def apply_schema(
    schema_path: str | Path | None = None,
    *,
    db_config: str | Path | None = None,
) -> Path:
    path = resolve_schema_path(schema_path)
    sql = path.read_text(encoding="utf-8")
    conn = get_connection(db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the pinned Phat schema_v4 contract to PostgreSQL"
    )
    parser.add_argument("--schema", help="Schema SQL path")
    parser.add_argument("--db-config", help="Database config JSON path")
    args = parser.parse_args()
    try:
        applied = apply_schema(args.schema, db_config=args.db_config)
    except Exception as exc:
        print(f"Schema setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Applied schema: {applied.relative_to(PROJECT_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
