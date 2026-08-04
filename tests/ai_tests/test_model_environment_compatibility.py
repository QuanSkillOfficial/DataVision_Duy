import os
import sys
import json
import joblib

# Resolve project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

def test_model_environment_compatibility():
    model_path = os.path.join(_PROJECT_ROOT, "ai", "prediction", "models", "best_document_type_classifier.joblib")
    model_card_path = os.path.join(_PROJECT_ROOT, "ai", "prediction", "models", "model_card.json")

    # 1. model file exists
    assert os.path.exists(model_path), f"Model file not found at {model_path}"

    # 2. model_card exists
    assert os.path.exists(model_card_path), f"Model card not found at {model_card_path}"

    # 3. model loads
    pkg = joblib.load(model_path)
    assert pkg is not None
    assert "model" in pkg
    assert "label_encoder" in pkg

    # 4. model_version exists
    assert "model_version" in pkg
    assert pkg["model_version"] != "unknown"

    # 5. supported labels exist
    classes = pkg["label_encoder"].classes_
    assert len(classes) > 0
    assert "report" in classes or "contract" in classes # basic sanity check

    # 6. scikit-learn version is compatible
    import sklearn
    assert sklearn.__version__ == "1.7.2", f"Expected scikit-learn 1.7.2, got {sklearn.__version__}"

    with open(model_card_path, "r") as f:
        card = json.load(f)
    assert card is not None
