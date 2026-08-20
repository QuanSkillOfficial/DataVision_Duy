#!/usr/bin/env python3
import os
import json
import sys
import datetime
sys.path.insert(0, "week8/database/scripts")
from db_connection import get_db_connection  # noqa: E402
from db_schema_constants import CORE_TABLES  # noqa: E402


def snapshot(label):
    conn = get_db_connection()
    cur = conn.cursor()
    counts = {}
    for t in CORE_TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        counts[t] = cur.fetchone()[0]
    conn.close()
    return {
        "label": label,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "counts": counts,
    }


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    result = snapshot(label)
    out_dir = "week8/database/outputs/db_validation"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/idempotency_{label}.json", "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
