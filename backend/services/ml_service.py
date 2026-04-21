"""
ML Inference Service
Loads trained models and provides probability predictions.
"""

import joblib
import numpy as np
from pathlib import Path

from backend.utils.feature_engineering import ML_FEATURE_NAMES

BASE_DIR  = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

# ── Lazy-loaded singletons ────────────────────────────────────────────────────
_scaler = None
_lr     = None
_rf     = None


def _load_models():
    global _scaler, _lr, _rf
    if _scaler is None:
        _scaler = joblib.load(MODEL_DIR / "scaler.pkl")
        _lr     = joblib.load(MODEL_DIR / "logistic_regression.pkl")
        _rf     = joblib.load(MODEL_DIR / "random_forest.pkl")


def predict(features: dict) -> dict:
    """
    Returns:
        {
            "rf_probability":  float 0-1,
            "lr_probability":  float 0-1,
            "primary_ml_prob": float 0-1   (RF is primary)
        }
    """
    _load_models()

    vec = np.array([[features[k] for k in ML_FEATURE_NAMES]], dtype=float)

    # RF – raw (unscaled)
    rf_prob = float(_rf.predict_proba(vec)[0][1])

    # LR – scaled
    vec_s   = _scaler.transform(vec)
    lr_prob = float(_lr.predict_proba(vec_s)[0][1])

    return {
        "rf_probability":  round(rf_prob, 4),
        "lr_probability":  round(lr_prob, 4),
        "primary_ml_prob": round(rf_prob, 4),
    }
