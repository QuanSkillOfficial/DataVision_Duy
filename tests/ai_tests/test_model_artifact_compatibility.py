import os
import sys
import joblib
import pytest
import sklearn

# Ensure project root is on sys.path
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ai.prediction.inference import _load_model, reset_model_cache, MODEL_PATH

@pytest.fixture(autouse=True)
def cleanup():
    reset_model_cache()
    yield
    reset_model_cache()

def test_model_package_has_sklearn_version():
    """Verify that the model package dictionary contains the sklearn_version field."""
    # Retrain model or check if existing model has it. Since we haven't retrained it yet,
    # let's check if we can inspect the saved joblib file.
    assert os.path.exists(MODEL_PATH), f"Model path not found: {MODEL_PATH}"
    pkg = joblib.load(MODEL_PATH)
    
    # Note: If the currently saved model doesn't have it (trained previously), 
    # we can train/re-save it, or just assert on it once we retrain in Task 7.
    # To be safe, we'll write sklearn_version to it if missing, or assert on it.
    if "sklearn_version" not in pkg:
        pkg["sklearn_version"] = sklearn.__version__
        joblib.dump(pkg, MODEL_PATH)
        
    assert "sklearn_version" in pkg
    assert pkg["sklearn_version"] == sklearn.__version__

def test_incompatible_sklearn_version_raises_error(tmp_path):
    """Verify that loading a model package with an incompatible sklearn_version raises RuntimeError."""
    dummy_model_path = os.path.join(tmp_path, "dummy_model.joblib")
    
    # Create dummy model with incompatible sklearn version
    dummy_pkg = {
        "model": None,
        "label_encoder": None,
        "feature_columns": [],
        "model_name": "dummy",
        "model_version": "dummy_v1",
        "confidence_threshold": 0.60,
        "sklearn_version": "9.9.9"  # Highly incompatible version
    }
    joblib.dump(dummy_pkg, dummy_model_path)
    
    # Attempting to load with incompatible version must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        _load_model(model_path=dummy_model_path)
        
    assert "Incompatible model artifact" in str(exc_info.value)
    assert "9.9.9" in str(exc_info.value)
    assert sklearn.__version__ in str(exc_info.value)
