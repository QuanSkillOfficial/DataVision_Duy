from __future__ import annotations

import json
from pathlib import Path

import fitz
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "tests/fixtures/data"


def build_shared_test_fixtures() -> dict[str, int]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_source = PROJECT_ROOT / "week2/data/sample_inputs/Superstore.csv"
    csv_output = OUTPUT_DIR / "sample_superstore_small.csv"
    csv_rows = pd.read_csv(csv_source, encoding="latin1").head(8)
    csv_rows.to_csv(csv_output, index=False)

    excel_source = PROJECT_ROOT / "week2/data/sample_inputs/Product-Sales-Region.xlsx"
    excel_output = OUTPUT_DIR / "sample_product_sales_small.xlsx"
    excel_rows = pd.read_excel(excel_source).head(8)
    excel_rows.to_excel(excel_output, index=False)

    api_source = PROJECT_ROOT / "data/sample_inputs/api/dummyjson_products_sample.json"
    api_output = OUTPUT_DIR / "sample_api_products.json"
    api_payload = json.loads(api_source.read_text(encoding="utf-8"))
    api_sample = dict(api_payload)
    api_sample["products"] = api_payload.get("products", [])[:5]
    api_sample["total"] = len(api_sample["products"])
    api_sample["limit"] = len(api_sample["products"])
    api_output.write_text(json.dumps(api_sample, indent=2, ensure_ascii=False), encoding="utf-8")

    pages_source = PROJECT_ROOT / "outputs/rag_handoff/document_pages.jsonl"
    pages_output = OUTPUT_DIR / "sample_dataflow_pages_small.jsonl"
    page_lines = [line for line in pages_source.read_text(encoding="utf-8").splitlines() if line.strip()][:2]
    pages_output.write_text("\n".join(page_lines) + "\n", encoding="utf-8")

    pdf_source = fitz.open(PROJECT_ROOT / "week2/data/sample_inputs/DataFlow_Technical_Report.pdf")
    pdf_sample = fitz.open()
    try:
        pdf_sample.insert_pdf(pdf_source, from_page=0, to_page=min(1, pdf_source.page_count - 1))
        (OUTPUT_DIR / "sample_dataflow_small.pdf").write_bytes(pdf_sample.tobytes())
    finally:
        pdf_sample.close()
        pdf_source.close()

    return {
        "csv_rows": len(csv_rows),
        "excel_rows": len(excel_rows),
        "api_rows": len(api_sample["products"]),
        "pdf_pages": len(page_lines),
    }


def main() -> int:
    result = build_shared_test_fixtures()
    print(json.dumps({"status": "passed", "fixtures": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
