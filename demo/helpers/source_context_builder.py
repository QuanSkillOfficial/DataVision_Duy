import io
import uuid
from html import escape
from datetime import datetime, timezone
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

from domain_config import (
    DEFAULT_DOMAIN_KEY,
)


IMAGE_FILE_TYPES = {"png", "jpg", "jpeg", "webp"}


def parse_links(raw_links: str) -> List[str]:
    return [line.strip() for line in (raw_links or "").splitlines() if line.strip()]


def read_tabular_data(content: bytes, file_name: str) -> pd.DataFrame | None:
    """Parse raw file bytes into a Pandas DataFrame based on file extension."""
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if lower_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    if lower_name.endswith(".json"):
        try:
            return pd.read_json(io.BytesIO(content))
        except ValueError:
            return pd.read_json(io.BytesIO(content), lines=True)
    if lower_name.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(content))
    return None


def read_tabular_file(uploaded_file) -> pd.DataFrame | None:
    """Read a tabular uploaded file object into a DataFrame."""
    return read_tabular_data(uploaded_file.getvalue(), uploaded_file.name)



def preview_file(uploaded_file):
    try:
        df = read_tabular_file(uploaded_file)
        if df is None:
            st.caption("Preview not available for this file type.")
            return
    except Exception as exc:
        st.warning(f"Preview not available: {exc}")
        return

    st.dataframe(df.head(5), use_container_width=True)
    st.caption(f"Rows: {len(df)} | Columns: {len(df.columns)}")


def source_type_from_name(file_name: str) -> str:
    suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "file"
    return suffix


def preview_text_for_file(uploaded_file) -> str:
    file_name = uploaded_file.name.lower()
    try:
        df = read_tabular_file(uploaded_file)
        if df is not None:
            columns = ", ".join(str(column) for column in df.columns[:8])
            return f"Data preview: {len(df)} rows, {len(df.columns)} columns. Columns: {columns}"
        if source_type_from_name(file_name) in IMAGE_FILE_TYPES:
            return "Image uploaded for visual data extraction. Analysis is mocked in this demo."
    except Exception as exc:
        return f"Preview unavailable: {exc}"
    return "Preview not available for this file type."


def infer_domain_from_columns(columns: List[str]) -> tuple[str, float, str]:
    normalized = {str(column).lower().replace("_", " ") for column in columns}
    ecommerce_terms = {"order", "product", "customer", "revenue", "sales", "price", "quantity", "sku"}
    finance_terms = {"amount", "balance", "transaction", "account", "payment", "profit", "cost"}
    research_terms = {"response", "score", "experiment", "sample", "group", "survey", "result"}

    joined = " ".join(normalized)
    if any(term in joined for term in ecommerce_terms):
        return "E-commerce", 0.82, "Sales, customer, and product performance"
    if any(term in joined for term in finance_terms):
        return "Finance", 0.76, "Financial activity, amounts, and risk signals"
    if any(term in joined for term in research_terms):
        return "Research", 0.71, "Experimental results, survey responses, or sample groups"
    return "General Data", 0.58, "Core metrics, distributions, and quality signals"


def analyze_sources(uploaded_files: List[Any], links: List[str] | None) -> Dict[str, Any]:
    links = links or []
    total_rows = 0
    total_columns = 0
    detected_columns = []
    previewable = 0
    image_count = 0
    file_summaries = []

    for uploaded_file in uploaded_files:
        source_type = source_type_from_name(uploaded_file.name)
        summary = {
            "name": uploaded_file.name,
            "type": source_type.upper(),
            "size": uploaded_file.size,
            "rows": None,
            "columns": None,
            "status": "Ready",
        }

        if source_type in IMAGE_FILE_TYPES:
            image_count += 1
            summary["status"] = "Image ready for visual extraction"
            file_summaries.append(summary)
            continue

        try:
            df = read_tabular_file(uploaded_file)
            if df is None:
                summary["status"] = "Metadata captured"
            else:
                previewable += 1
                total_rows += len(df)
                total_columns += len(df.columns)
                detected_columns.extend(str(column) for column in df.columns)
                summary["rows"] = len(df)
                summary["columns"] = len(df.columns)
                summary["status"] = "Analyzed"
        except Exception as exc:
            summary["status"] = f"Metadata captured; preview unavailable ({exc})"

        file_summaries.append(summary)

    domain, confidence, suggested_focus = infer_domain_from_columns(detected_columns)
    if image_count and not detected_columns:
        domain, confidence, suggested_focus = "Image Data", 0.64, "Visual extraction, labels, and image-level metrics"
    if links and not detected_columns and not image_count:
        domain, confidence, suggested_focus = "Linked Source", 0.52, "Source metadata, accessibility, and extraction readiness"

    key_columns = list(dict.fromkeys(detected_columns))[:8]
    if not key_columns and image_count:
        key_columns = ["image_name", "image_type", "visual_features"]
    if not key_columns and links:
        key_columns = ["source_url", "source_type", "extraction_status"]

    for link in links:
        file_summaries.append(
            {
                "name": link,
                "type": "LINK",
                "size": None,
                "rows": None,
                "columns": None,
                "status": "Link captured for extraction",
            }
        )

    return {
        "detected_domain": domain,
        "confidence": confidence,
        "row_count": total_rows,
        "column_count": total_columns,
        "key_columns": key_columns,
        "suggested_focus": suggested_focus,
        "file_summaries": file_summaries,
        "previewable_sources": previewable,
    }


def build_source_entries(uploaded_files: List[Any], links: List[str]) -> List[Dict[str, Any]]:
    uploaded_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "domain_context": st.session_state.get("selected_domain_context", DEFAULT_DOMAIN_KEY),
        "data_category": st.session_state.get("data_category"),
        "source_system": st.session_state.get("source_system"),
        "processing_options": list(st.session_state.get("process_options", [])),
        "skip_empty_rows": st.session_state.get("skip_empty_rows", True),
        "auto_mapping": st.session_state.get("auto_mapping", True),
    }

    entries: List[Dict[str, Any]] = []
    for uploaded_file in uploaded_files:
        source_type = source_type_from_name(uploaded_file.name)
        preview_text = preview_text_for_file(uploaded_file)
        entries.append(
            {
                "id": uuid.uuid4().hex,
                "type": "file",
                "source_type": source_type,
                "name": uploaded_file.name,
                "filename": uploaded_file.name,
                "size": uploaded_file.size,
                "content": uploaded_file.getvalue(),
                "uploaded_at": uploaded_at,
                "preview_text": preview_text,
                **metadata,
            }
        )

    for link in links:
        entries.append(
            {
                "id": uuid.uuid4().hex,
                "type": "link",
                "source_type": "link",
                "value": link,
                "uploaded_at": uploaded_at,
                "preview_text": f"Source link captured for demo processing: {link}",
                **metadata,
            }
        )

    return entries
