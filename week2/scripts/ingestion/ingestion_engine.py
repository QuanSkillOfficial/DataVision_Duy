from __future__ import annotations

try:
    from .api_ingestor import run_api_ingestion
    from .csv_ingestor import run_csv_ingestion
    from .excel_ingestor import run_excel_ingestion
    from .pdf_ingestor import run_pdf_ingestion
except ImportError:
    from api_ingestor import run_api_ingestion
    from csv_ingestor import run_csv_ingestion
    from excel_ingestor import run_excel_ingestion
    from pdf_ingestor import run_pdf_ingestion


def run_all_ingestion() -> dict:
    return {
        "csv": run_csv_ingestion(),
        "excel": run_excel_ingestion(),
        "api": run_api_ingestion(),
        "pdf": run_pdf_ingestion(),
    }


if __name__ == "__main__":
    results = run_all_ingestion()
    for source_type, log in results.items():
        print(f"{source_type}: {log['status']} - {log['records_valid']} valid")
