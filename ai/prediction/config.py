# ai/prediction/config.py
# Configuration for the Prediction Module, including Staging Safety Policies

# Week 7 Staging Safety Thresholds
STAGING_ACCEPTANCE_THRESHOLD = 0.80
REVIEW_THRESHOLD = 0.50
MIN_EXTRACTED_TEXT_LENGTH = 50

# Allowed statuses to pass the prediction release gate
RELEASE_GATE_ALLOWED_STATUSES = ["accepted", "needs_review"]

# Out-of-distribution confidence threshold
OOD_THRESHOLD = 0.30


