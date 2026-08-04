"""
feature_builder.py — Centralized preprocessing for document type classification.

This module is the single source of truth for all feature preprocessing.
Both train_model.py and inference.py use this module to ensure
train/serve parity (no skew between training and inference).

Key design:
- Text cleaning, categorical cleaning, and numeric coercion are done
  on the raw DataFrame before feeding into the sklearn pipeline.
- log1p transformation is embedded inside the sklearn pipeline via
  FunctionTransformer, so the saved .joblib model handles it automatically.
"""

import re

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    StandardScaler,
)

# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "file_name",
    "file_type",
    "file_size",
    "text_length",
    "num_pages",
    "source_system",
    "extracted_text",
]

TEXT_COLS = ["file_name", "extracted_text"]
CAT_COLS = ["file_type", "source_system"]
NUM_COLS = ["file_size", "text_length", "num_pages"]

FEATURE_COLS = [
    "file_name",
    "file_type",
    "file_size",
    "text_length",
    "num_pages",
    "source_system",
    "extracted_text",
]

TARGET_COL = "document_type"

# Confidence threshold – predictions below this are marked "needs_review"
CONFIDENCE_THRESHOLD = 0.60

# Minimum extracted text length for reliable prediction
MIN_EXTRACTED_TEXT_LENGTH = 50

# Model metadata
MODEL_VERSION = "document_classifier_v1"
MODEL_NAME = "document_classifier"

# Final status values (aligned across all services)
STATUS_ACCEPTED = "accepted"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_WAITING_FOR_SOURCE = "waiting_for_source"
STATUS_FAILED = "failed"

VALID_STATUSES = [STATUS_ACCEPTED, STATUS_NEEDS_REVIEW, STATUS_WAITING_FOR_SOURCE, STATUS_FAILED]


# ---------------------------------------------------------------------------
# Text / categorical / numeric helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip."""
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def clean_dataframe(df: pd.DataFrame, *, fit_mode: bool = True) -> pd.DataFrame:
    """
    Apply deterministic cleaning that must happen *before* the sklearn
    pipeline (because TfidfVectorizer expects plain strings, not raw NaN).

    Parameters
    ----------
    df : pd.DataFrame
        Raw feature dataframe.
    fit_mode : bool
        If True (training), numeric NaN values are filled with column median.
        If False (inference on a single row), numeric NaN are filled with 0.

    Returns
    -------
    pd.DataFrame
        Cleaned copy.
    """
    df = df.copy()

    # --- text columns ---
    for col in TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].fillna("").apply(clean_text)

    # --- categorical columns ---
    for col in CAT_COLS:
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("unknown")
                .astype(str)
                .str.lower()
                .str.strip()
            )

    # --- numeric columns ---
    for col in NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if fit_mode:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(0)

    return df


# ---------------------------------------------------------------------------
# sklearn preprocessor builder
# ---------------------------------------------------------------------------

def _log1p_transform(X):
    """Apply log1p; works on dense arrays."""
    return np.log1p(np.abs(X))


def build_preprocessor() -> ColumnTransformer:
    """
    Return a ColumnTransformer that handles:
      - categorical → OneHotEncoder
      - numeric    → log1p (via FunctionTransformer) + StandardScaler
      - file_name  → TF-IDF (max 2000 features, unigrams + bigrams)
      - extracted_text → TF-IDF (max 5000 features, unigrams + bigrams)

    log1p is inside the pipeline so the saved model handles it
    automatically during inference.
    """

    numeric_pipeline = Pipeline([
        ("log1p", FunctionTransformer(_log1p_transform, validate=False)),
        ("scaler", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
            ("num", numeric_pipeline, NUM_COLS),
            (
                "file_name_tfidf",
                TfidfVectorizer(max_features=2000, ngram_range=(1, 2)),
                "file_name",
            ),
            (
                "text_tfidf",
                TfidfVectorizer(max_features=5000, ngram_range=(1, 2)),
                "extracted_text",
            ),
        ]
    )

    return preprocessor


# ---------------------------------------------------------------------------
# Input validation (for inference)
# ---------------------------------------------------------------------------

def validate_input(payload: dict) -> list[str]:
    """
    Validate that all required fields are present in *payload*.

    Returns a list of error messages (empty list means valid).
    """
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: '{field}'")

    # Type checks for numeric fields
    for field in NUM_COLS:
        if field in payload:
            val = payload[field]
            if not isinstance(val, (int, float)):
                try:
                    float(val)
                except (TypeError, ValueError):
                    errors.append(
                        f"Field '{field}' must be a number, got {type(val).__name__}"
                    )

    # Non-empty checks for string fields
    for field in ["file_name", "file_type", "source_system"]:
        if field in payload and not str(payload[field]).strip():
            errors.append(f"Field '{field}' must not be empty")

    return errors


def payload_to_dataframe(payload: dict) -> pd.DataFrame:
    """
    Convert a single API payload dict into a cleaned DataFrame
    ready for the sklearn pipeline.
    """
    row = {col: payload.get(col, None) for col in FEATURE_COLS}
    df = pd.DataFrame([row])
    df = clean_dataframe(df, fit_mode=False)
    return df
