import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

db_password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
if not db_password:
    raise RuntimeError(
        "❌ Database password declaration is mandatory! "
        "Please set POSTGRES_PASSWORD (or DB_PASSWORD) in the .env file or system environment."
    )

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB") or os.getenv("DB_NAME", "datavision_db"),
    "user": os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "datavision"),
    "password": db_password,
    "host": os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT", "5432")
}

VIEWS_TO_EXPORT = [
    "v_dashboard_overview",
    "v_latest_ingestion_runs",
    "v_data_quality_dashboard",
    "v_source_quality_summary",
    "v_source_quality_detail",
    "v_document_rag_readiness",
    "v_prediction_review_queue",
    "v_prediction_confidence_summary",
    "v_rag_daily_metrics",
    "v_recent_activity",
    "v_document_quality_summary",
    "v_ingestion_health"
]

OUTPUT_DIR = "week8/database/outputs/dashboard_view_samples"

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        print("Connected to database successfully.\n")

        for view in VIEWS_TO_EXPORT:
            print(f"Exporting data from {view}...")
            
            cur.execute(f"SELECT * FROM {view};")
            rows = cur.fetchall()
            
            
            output_file = os.path.join(OUTPUT_DIR, f"{view}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rows, f, cls=CustomJSONEncoder, indent=4, ensure_ascii=False)
            
            print(f"  -> Saved {len(rows)} rows to {output_file}")

        print("\nAll dashboard view samples exported successfully!")

    except Exception as e:
        print(f"Failed to export views: {e}")
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()