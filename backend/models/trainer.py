"""
Synthetic Dataset Generator + ML Model Trainer
Creates 2000+ labeled samples, trains Logistic Regression and Random Forest,
evaluates both models, and persists artifacts.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.linear_model    import LogisticRegression
from sklearn.ensemble        import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing   import StandardScaler
from sklearn.metrics         import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_curve, auc
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
DATA_DIR  = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

FEATURE_NAMES = [
    "followers_count", "following_count", "engagement_rate",
    "account_age_days", "posts_per_week", "bio_length",
    "profile_picture", "username_randomness", "spam_keyword_score", "ff_ratio",
]

# ── Synthetic data generation ─────────────────────────────────────────────────
np.random.seed(42)

def _generate_real_profiles(n: int) -> pd.DataFrame:
    followers    = np.random.randint(200, 50_000, n)
    following    = np.random.randint(50, 3_000, n)
    engagement   = np.random.uniform(1.5, 15.0, n)
    age_days     = np.random.randint(180, 2000, n)
    ppw          = np.random.uniform(0.5, 5.0, n)
    bio_length   = np.random.randint(20, 200, n)
    has_pic      = np.ones(n, dtype=int)
    username_rs  = np.random.uniform(0.0, 0.25, n)
    spam_score   = np.random.uniform(0.0, 0.1, n)
    ff_ratio     = following / np.maximum(followers, 1)
    label        = np.zeros(n, dtype=int)
    return pd.DataFrame({
        "followers_count": followers, "following_count": following,
        "engagement_rate": engagement, "account_age_days": age_days,
        "posts_per_week": ppw, "bio_length": bio_length,
        "profile_picture": has_pic, "username_randomness": username_rs,
        "spam_keyword_score": spam_score, "ff_ratio": ff_ratio,
        "label": label
    })

def _generate_fake_profiles(n: int) -> pd.DataFrame:
    followers    = np.random.randint(0, 500, n)
    following    = np.random.randint(500, 8_000, n)
    engagement   = np.random.uniform(0.0, 1.5, n)
    age_days     = np.random.randint(1, 90, n)
    ppw          = np.random.uniform(0.0, 30.0, n)
    bio_length   = np.random.randint(0, 30, n)
    has_pic      = np.random.choice([0, 1], n, p=[0.6, 0.4])
    username_rs  = np.random.uniform(0.3, 1.0, n)
    spam_score   = np.random.uniform(0.2, 1.0, n)
    ff_ratio     = following / np.maximum(followers, 1)
    label        = np.ones(n, dtype=int)
    return pd.DataFrame({
        "followers_count": followers, "following_count": following,
        "engagement_rate": engagement, "account_age_days": age_days,
        "posts_per_week": ppw, "bio_length": bio_length,
        "profile_picture": has_pic, "username_randomness": username_rs,
        "spam_keyword_score": spam_score, "ff_ratio": ff_ratio,
        "label": label
    })

def _generate_suspicious_profiles(n: int) -> pd.DataFrame:
    """Mid-ground profiles – harder cases for the model."""
    followers    = np.random.randint(10, 2_000, n)
    following    = np.random.randint(200, 5_000, n)
    engagement   = np.random.uniform(0.0, 5.0, n)
    age_days     = np.random.randint(30, 300, n)
    ppw          = np.random.uniform(1.0, 15.0, n)
    bio_length   = np.random.randint(0, 60, n)
    has_pic      = np.random.choice([0, 1], n, p=[0.4, 0.6])
    username_rs  = np.random.uniform(0.2, 0.7, n)
    spam_score   = np.random.uniform(0.1, 0.5, n)
    ff_ratio     = following / np.maximum(followers, 1)
    label        = np.ones(n, dtype=int)  # treat as fake
    return pd.DataFrame({
        "followers_count": followers, "following_count": following,
        "engagement_rate": engagement, "account_age_days": age_days,
        "posts_per_week": ppw, "bio_length": bio_length,
        "profile_picture": has_pic, "username_randomness": username_rs,
        "spam_keyword_score": spam_score, "ff_ratio": ff_ratio,
        "label": label
    })


def generate_dataset() -> pd.DataFrame:
    real        = _generate_real_profiles(900)
    fake        = _generate_fake_profiles(900)
    suspicious  = _generate_suspicious_profiles(300)
    df          = pd.concat([real, fake, suspicious], ignore_index=True)
    df          = df.sample(frac=1, random_state=42).reset_index(drop=True)
    df.to_csv(DATA_DIR / "synthetic_profiles.csv", index=False)
    print(f"[Dataset] Generated {len(df)} samples  (real={len(real)}, fake={len(fake)+len(suspicious)})")
    return df


# ── Model evaluation helpers ──────────────────────────────────────────────────

def _evaluate(model, X_test, y_test, name: str) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc     = auc(fpr, tpr)
    cm          = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model":     name,
        "accuracy":  round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score":  round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc, 4),
        "confusion_matrix": cm,
        "roc_curve": {
            "fpr": [round(v, 4) for v in fpr.tolist()],
            "tpr": [round(v, 4) for v in tpr.tolist()],
        },
    }
    print(f"[{name}] Acc={metrics['accuracy']}  P={metrics['precision']}  "
          f"R={metrics['recall']}  F1={metrics['f1_score']}  AUC={metrics['roc_auc']}")
    return metrics


# ── Main train function ───────────────────────────────────────────────────────

def train_models():
    df = generate_dataset()

    X = df[FEATURE_NAMES].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # ── Scale ────────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # ── Logistic Regression ───────────────────────────────────────────────────
    lr = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
    lr.fit(X_train_s, y_train)
    lr_metrics = _evaluate(lr, X_test_s, y_test, "Logistic Regression")

    # ── Random Forest ─────────────────────────────────────────────────────────
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=12,
        random_state=42, class_weight="balanced", n_jobs=-1
    )
    rf.fit(X_train, y_train)          # RF doesn't need scaling
    rf_metrics = _evaluate(rf, X_test, y_test, "Random Forest")

    # ── Persist ───────────────────────────────────────────────────────────────
    joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
    joblib.dump(lr,     MODEL_DIR / "logistic_regression.pkl")
    joblib.dump(rf,     MODEL_DIR / "random_forest.pkl")

    # Feature importances
    importances = dict(zip(FEATURE_NAMES, rf.feature_importances_.tolist()))

    eval_report = {
        "logistic_regression": lr_metrics,
        "random_forest":       rf_metrics,
        "feature_importances": importances,
    }
    with open(MODEL_DIR / "evaluation_report.json", "w") as f:
        json.dump(eval_report, f, indent=2)

    print("[Trainer] All models saved successfully.")
    return eval_report


if __name__ == "__main__":
    train_models()
