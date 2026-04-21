"""
Evaluation API Routes
GET /api/evaluation/report    – full JSON evaluation report
GET /api/evaluation/summary   – concise metrics for UI display
"""

import json
from pathlib import Path
from fastapi  import APIRouter, HTTPException

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

REPORT_PATH = Path(__file__).resolve().parent.parent / "models" / "evaluation_report.json"


def _load_report() -> dict:
    if not REPORT_PATH.exists():
        raise HTTPException(status_code=503, detail="Evaluation report not found. Train models first.")
    with open(REPORT_PATH) as f:
        return json.load(f)


@router.get("/report")
def full_report():
    return _load_report()


@router.get("/summary")
def summary():
    report = _load_report()
    lr = report["logistic_regression"]
    rf = report["random_forest"]
    fi = report.get("feature_importances", {})

    return {
        "models": [
            {
                "name":      "Logistic Regression",
                "accuracy":  lr["accuracy"],
                "precision": lr["precision"],
                "recall":    lr["recall"],
                "f1_score":  lr["f1_score"],
                "roc_auc":   lr["roc_auc"],
                "confusion_matrix": lr["confusion_matrix"],
                "roc_curve": lr["roc_curve"],
            },
            {
                "name":      "Random Forest",
                "accuracy":  rf["accuracy"],
                "precision": rf["precision"],
                "recall":    rf["recall"],
                "f1_score":  rf["f1_score"],
                "roc_auc":   rf["roc_auc"],
                "confusion_matrix": rf["confusion_matrix"],
                "roc_curve": rf["roc_curve"],
            },
        ],
        "feature_importances": fi,
        "comparison_note": (
            "Random Forest is the primary ML component of the Hybrid model. "
            "Logistic Regression serves as a baseline comparator."
        )
    }
