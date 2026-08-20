import os
import sys
import pytest
import numpy as np

# Ensure project root is on sys.path
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import predict_document_type, reset_model_cache
from ai.prediction.reviewer_corrections import build_correction_payload

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

@pytest.fixture(autouse=True)
def cleanup():
    reset_model_cache()
    yield
    reset_model_cache()

def test_clear_input_does_not_trigger_ood():
    """Clear high-confidence input should have is_out_of_distribution = False."""
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result
    assert result["is_out_of_distribution"] is False

def test_vague_input_triggers_ood_and_correct_routing(monkeypatch):
    """An ambiguous input with top confidence below OOD_THRESHOLD (0.30) must trigger OOD flag and needs_review status."""
    # To reliably trigger OOD, we mock the model's predict_proba to return flat probabilities (e.g. ~14% each for 7 classes)
    from ai.prediction.inference import _load_model
    pkg = _load_model()
    model = pkg["model"]
    
    # Mock predict_proba to return flat probabilities where max probability is 0.20
    flat_probs = np.array([[0.20, 0.15, 0.15, 0.15, 0.15, 0.10, 0.10]])
    monkeypatch.setattr(model, "predict_proba", lambda X: flat_probs)
    # Mock predict to return class index 0
    monkeypatch.setattr(model, "predict", lambda X: np.array([0]))
    
    result = predict_document_type(VALID_PAYLOAD)
    assert "error" not in result
    assert result["is_out_of_distribution"] is True
    assert result["status"] == "needs_review"
    assert result["review_reason"] == "Out-of-distribution input detected"

def test_correction_payload_builder_valid():
    """Verify that build_correction_payload produces a valid DB dictionary."""
    payload = build_correction_payload(
        prediction_log_id=12,
        original_prediction="report",
        corrected_document_type="contract",
        corrected_by="admin_user",
        correction_reason="Verified by team lead",
        document_id=5,
        document_external_id="doc_005"
    )
    
    assert payload["prediction_log_id"] == 12
    assert payload["original_prediction"] == "report"
    assert payload["corrected_document_type"] == "contract"
    assert payload["corrected_by"] == "admin_user"
    assert payload["correction_reason"] == "Verified by team lead"
    assert payload["document_id"] == 5
    assert payload["document_external_id"] == "doc_005"
    assert "created_at" in payload

def test_correction_payload_builder_invalid_inputs():
    """Verify type and value errors are raised for invalid builder inputs."""
    with pytest.raises(TypeError):
        build_correction_payload(
            prediction_log_id="not-an-int",
            original_prediction="report",
            corrected_document_type="contract",
            corrected_by="user"
        )
        
    with pytest.raises(ValueError):
        build_correction_payload(
            prediction_log_id=1,
            original_prediction="",
            corrected_document_type="contract",
            corrected_by="user"
        )
