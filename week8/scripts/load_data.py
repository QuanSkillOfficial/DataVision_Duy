import csv
import json
import os
import sys
from tkinter import ON
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import argparse
from dotenv import load_dotenv
load_dotenv()
# ------------------------------------------------------------------
# 1. CONFIGURATION — edit here or set via environment variables
# ------------------------------------------------------------------
DB_CONFIG = {
    "dbname":   os.environ.get("DB_NAME", "datavision_db"),    
    "user":     os.environ.get("DB_USER", "datavision"),      
    "password": os.environ["DB_PASSWORD"],  
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     os.environ.get("DB_PORT", "5432"),
}

# Directory containing Duy's 4 data files (defaults to the script's own directory)
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))

CSV_SOURCES = [
    # (csv file name, source name in the `sources` table)
    ("superstore_clean.csv",             "superstore_sales_csv"),
    ("product_sales_region_clean.csv",   "product_sales_region_excel"),
    ("dummyjson_products_clean.csv",     "dummyjson_products_api"),
]
JSONL_FILE = "document_pages.jsonl"

# ------------------------------------------------------------------
# 2. DATABASE CONNECTION
# ------------------------------------------------------------------
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False   # manage the transaction manually so we can roll back on error
    cur = conn.cursor()
except psycopg2.OperationalError as e:
    print(f"❌ Could not connect to the database: {e}")
    sys.exit(1)


def get_source_id(name: str) -> int:
    cur.execute("SELECT id FROM sources WHERE name = %s", (name,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(
            f"Source '{name}' not found in the sources table. "
            f"Please insert it into the sources table before running this script."
        )
    return row[0]


def get_document_id(ext_id: str) -> int:
    cur.execute("SELECT id FROM documents WHERE document_external_id = %s", (ext_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(
            f"Document '{ext_id}' not found in the documents table. "
            f"Please insert it into the documents table before running this script."
        )
    return row[0]

# ------------------------------------------------------------------
# NEW: LOAD METADATA (Sources, Pipeline Runs, Ingestion Logs, Documents)
# ------------------------------------------------------------------
def load_metadata_from_files():
    """
    Reads Duy's actual JSON/JSONL files (ingestion_runs.jsonl and pdf_metadata.json)
    to populate the prerequisite tables before loading CSVs and JSONLs.
    """
    ingestion_runs_path = os.path.join(DATA_DIR, "ingestion_runs.jsonl")
    pdf_metadata_path = os.path.join(DATA_DIR, "pdf_metadata.json")

    # 1. Load Sources, Pipeline Runs, and Ingestion Logs
    
    if os.path.exists(ingestion_runs_path):
        with open(ingestion_runs_path, "r", encoding="utf-8-sig") as f:
            seen_sources = set()
            for line in f:
                line = line.strip()
                if not line:
                    continue
                run_data = json.loads(line)
                source_name = run_data.get("source_name")
                if source_name in seen_sources:
                    continue
                seen_sources.add(source_name)

                source_name = run_data.get("source_name")
                run_id = run_data.get("run_id", "unknown_run_id")
                status = run_data.get("status", "success")

                # Infer source_type from source_name (based on Duy's naming convention)
                source_type = "unknown"
                if "csv" in source_name: source_type = "csv"
                elif "pdf" in source_name: source_type = "pdf"
                elif "api" in source_name: source_type = "api"
                elif "excel" in source_name: source_type = "excel"

                # Insert Source (Ignore if it already exists to avoid unique constraint errors)
                cur.execute("""
                    INSERT INTO sources (name, source_type, status)
                    VALUES (%s, %s, 'active')
                    ON CONFLICT (name) DO NOTHING
                """, (source_name, source_type))
                source_id = get_source_id(source_name)

                # Insert Pipeline Run (run_name format mapped from Handoff document)
                run_name = f"{source_name}_{run_id}"
                start_time = run_data.get("start_time", run_data.get("started_at", datetime.now()))
                end_time = run_data.get("end_time", run_data.get("ended_at", datetime.now()))

                cur.execute("""
                    INSERT INTO pipeline_runs (run_name, start_time, end_time, status)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (run_name) DO UPDATE SET
                        status = EXCLUDED.status, end_time = EXCLUDED.end_time
                    RETURNING id
                """, (run_name, start_time, end_time, status))
                pipeline_run_id = cur.fetchone()[0]

                # Insert Ingestion Log (mapping exact fields required by schema)
                cur.execute("""
                    INSERT INTO ingestion_logs (
                        run_id, source_id, pipeline_run_id, status,
                        records_read, records_valid, records_invalid, data_quality_score,
                        raw_output_path, staging_output_path, clean_output_path
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_id, run_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        records_read = EXCLUDED.records_read,
                        records_valid = EXCLUDED.records_valid,
                        records_invalid = EXCLUDED.records_invalid
                """, (
                    run_id, source_id, pipeline_run_id, status,
                    run_data.get("records_read", 0),
                    run_data.get("records_valid", 0),
                    run_data.get("records_invalid", 0),
                    run_data.get("data_quality_score", 100.0),
                    run_data.get("raw_output_path", ""),
                    run_data.get("staging_output_path", ""),
                    run_data.get("clean_output_path", "")
                ))
        print("✅ Loaded: sources, pipeline_runs, ingestion_logs (from ingestion_runs.jsonl)")
    else:
        print(f"⚠️ Missing {ingestion_runs_path}. Skipping logs.")

    # 2. Load Documents metadata
    if os.path.exists(pdf_metadata_path):
        with open(pdf_metadata_path, "r", encoding="utf-8-sig") as f:
            pdf_meta = json.load(f)

        # Get source_id for the PDF (inserted during step 1)
        source_name = pdf_meta.get("source_name", "dataflow_technical_report_pdf")
        source_id = get_source_id(source_name)
        doc_ext_id = pdf_meta.get("document_external_id", "doc_dataflow_technical_report")

        # Insert Document (Ignore if exists)
        cur.execute("""
            INSERT INTO documents (
                source_id, file_name, processing_status, document_external_id,
                file_hash_sha256, page_count, character_count
            ) VALUES (%s, %s, 'processed', %s, %s, %s, %s)
            ON CONFLICT (document_external_id) DO NOTHING
        """, (
            source_id,
            pdf_meta.get("file_name", "DataFlow_Technical_Report.pdf"),
            doc_ext_id,
            pdf_meta.get("file_hash_sha256", ""),
            pdf_meta.get("page_count", 36),
            pdf_meta.get("total_characters", 129028)
        ))
        print("✅ Loaded: documents (from pdf_metadata.json)")
    else:
        print(f"⚠️ Missing {pdf_metadata_path}. Skipping document metadata.")


# ------------------------------------------------------------------
# 3. LOAD structured_records FROM CSV
# ------------------------------------------------------------------
def load_structured_records(csv_path: str, source_name: str, limit: int = None, status: str = "clean") -> int:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    source_id = get_source_id(source_name)
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        import hashlib
        for row in csv.DictReader(f):
            if limit is not None and len(rows) >= limit:
                break
            record_str = json.dumps(row, ensure_ascii=False)
            record_hash = hashlib.md5(record_str.encode('utf-8')).hexdigest()
            rows.append((source_id, record_str, status, record_hash))

    if not rows:
        print(f"⚠️  {source_name}: file is empty, skipping.")
        return 0

    execute_values(
        cur,
        """INSERT INTO structured_records (source_id, record_data, status, record_hash)
           VALUES %s
           ON CONFLICT (source_id, record_hash) DO NOTHING""",
        rows,
        template="(%s, %s::jsonb, %s, %s)",
        page_size=1000,
    )
    print(f"✅ {source_name}: loaded {len(rows)} rows into structured_records")
    return len(rows)


# ------------------------------------------------------------------
# 4. LOAD document_pages FROM JSONL
# ------------------------------------------------------------------
def load_document_pages(jsonl_path: str, limit: int = None) -> int:
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"File not found: {jsonl_path}")

    rows = []
    doc_id_cache = {}  # cache to avoid repeated queries for lines sharing the same document_id
    with open(jsonl_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if limit is not None and len(rows) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ext_id = rec["document_id"]
            if ext_id not in doc_id_cache:
                doc_id_cache[ext_id] = get_document_id(ext_id)
            doc_id = doc_id_cache[ext_id]
            rows.append((
                doc_id,
                rec["page_number"],
                rec["text"],
                rec["character_count"],
                rec["is_empty"],
            ))

    if not rows:
        print("⚠️  document_pages.jsonl is empty, skipping.")
        return 0

    execute_values(
        cur,
        """INSERT INTO document_pages (document_id, page_number, page_text, character_count, is_empty)
            VALUES %s
            ON CONFLICT (document_id, page_number) DO NOTHING""",
        rows,
        page_size=100,
    )
    print(f"✅ document_pages: loaded {len(rows)} rows")
    return len(rows)


# ------------------------------------------------------------------
# 5. RUN EVERYTHING IN A SINGLE TRANSACTION
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Load data with Smoke mode support")
    parser.add_argument("--smoke", action="store_true", help="Enable smoke mode")
    parser.add_argument("--limit-structured-records", type=int, default=100, help="Limit records for smoke mode")
    args = parser.parse_args()

    str_limit = args.limit_structured_records if args.smoke else None
    page_limit = 36 if args.smoke else None

    total_structured = 0
    try:
        load_metadata_from_files()
        for csv_name, source_name in CSV_SOURCES:
            csv_path = os.path.join(DATA_DIR, csv_name)
            total_structured += load_structured_records(csv_path, source_name, limit=str_limit)

        jsonl_path = os.path.join(DATA_DIR, JSONL_FILE)
        total_pages = load_document_pages(jsonl_path, limit=page_limit)

        cur.execute("SELECT COUNT(*) FROM sources;")
        total_sources = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pipeline_runs;")
        total_pipeline_runs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ingestion_logs;")
        total_ingestion_logs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM documents;")
        total_documents = cur.fetchone()[0]

        # If everything ran without errors -> commit once at the end
        conn.commit()
        print("\n🎉 Done. Changes have been committed to the database.")
        print(f"   - sources:            {total_sources} rows")
        print(f"   - pipeline_runs:      {total_pipeline_runs} rows")
        print(f"   - ingestion_logs:     {total_ingestion_logs} rows")
        print(f"   - documents:          {total_documents} rows")
        print(f"   - document_pages:     {total_pages} rows")
        print(f"   - structured_records: {total_structured} rows")

        output_dir = os.path.join("week8", "database", "outputs", "db_validation")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "duy_data_load_counts.json")
        
        output_data = {
            "sources": total_sources,
            "pipeline_runs": total_pipeline_runs,
            "ingestion_logs": total_ingestion_logs,
            "documents": total_documents,
            "document_pages": total_pages,
            "structured_records": total_structured
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4)
            
        print(f"   - Đã lưu file kết quả tại: {output_file}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ An error occurred, ROLLED BACK everything (no rows were saved): {e}")
        sys.exit(1)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()