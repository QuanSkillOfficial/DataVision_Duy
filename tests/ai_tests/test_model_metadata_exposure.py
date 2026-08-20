import os
import sys
import pytest

# Ensure project root is on sys.path
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import predict_document_type

VALID_PAYLOAD = {
    "file_name": "policy_doc.pdf",
    "file_type": "pdf",
    "file_size": 240000,
    "text_length": 4200,
    "num_pages": 4,
    "source_system": "manual_upload",
    "extracted_text": (
        "This policy explains the rules for access control, "
        "responsibilities, approval process, and compliance review."
    ),
}

def test_metadata_exposure_in_valid_prediction():
    """Verify metadata exposure for normal successful predictions."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result

    assert "model_version" in result
    assert "model_checksum" in result
    assert "training_data_version" in result
    assert "threshold_policy" in result

    assert isinstance(result["model_version"], str)
    assert isinstance(result["model_checksum"], str)
    assert len(result["model_checksum"]) == 32  # MD5 is 32 chars
    assert isinstance(result["training_data_version"], str)

    policy = result["threshold_policy"]
    assert isinstance(policy, dict)
    assert "staging_acceptance_threshold" in policy
    assert "review_threshold" in policy
    assert "min_extracted_text_length" in policy
    assert policy["staging_acceptance_threshold"] == 0.80
    assert policy["review_threshold"] == 0.50
    assert policy["min_extracted_text_length"] == 50

def test_metadata_exposure_in_short_text_prediction():
    """Verify metadata exposure even when quality gate triggers waiting_for_source."""
    short_payload = {**VALID_PAYLOAD, "extracted_text": "too short"}
    result = predict_document_type(short_payload)
    assert "error" not in result
    assert result["status"] == "waiting_for_source"

    assert "model_version" in result
    assert "model_checksum" in result
    assert "training_data_version" in result
    assert "threshold_policy" in result

    assert isinstance(result["model_version"], str)
    assert isinstance(result["model_checksum"], str)
    assert isinstance(result["training_data_version"], str)
    assert result["threshold_policy"]["staging_acceptance_threshold"] == 0.80
