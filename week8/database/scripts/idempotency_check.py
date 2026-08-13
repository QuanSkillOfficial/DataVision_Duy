#!/usr/bin/env python3
import os, json, sys, datetime
import psycopg2
from dotenv import load_dotenv
load_dotenv()
TABLES = ["sources", "documents", "document_pages", "document_chunks",
          "structured_records", "ingestion_logs", "prediction_logs"]

def get_conn():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError("DB_PASSWORD environment variable is required")
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "datavision_db"),
        user=os.environ.get("DB_USER", "datavision"),
        password=password,
    )

def snapshot(label):
    conn = get_conn()
    cur = conn.cursor()
    counts = {}
    for t in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        counts[t] = cur.fetchone()[0]
    conn.close()
    return {"label": label, "timestamp": datetime.datetime.utcnow().isoformat(),
            "counts": counts}

if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    result = snapshot(label)
    out_dir = "week8/database/outputs/db_validation"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/idempotency_{label}.json", "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))