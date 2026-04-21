"""
Hybrid Scoring Engine
Final Risk Score = (0.6 × Rule Score) + (0.4 × ML Probability × 100)
Also generates AI explanation summary and behavioral anomaly flags.
"""

import re
from typing import List, Tuple

from backend.services.rule_engine  import compute_rule_score, RuleEngineOutput
from backend.services.ml_service   import predict as ml_predict
from backend.utils.feature_engineering import build_feature_vector

# ── Hybrid weights ────────────────────────────────────────────────────────────
RULE_WEIGHT = 0.6
ML_WEIGHT   = 0.4


def _status_badge(score: float) -> str:
    if score < 35:
        return "REAL"
    if score < 65:
        return "SUSPICIOUS"
    return "HIGH RISK"


def _status_color(status: str) -> str:
    return {"REAL": "green", "SUSPICIOUS": "yellow", "HIGH RISK": "red"}[status]


# ── Behavioral anomaly detection ──────────────────────────────────────────────

def _behavioral_anomalies(features: dict) -> List[str]:
    anomalies = []

    # Ghost follower pattern
    if features["followers_count"] > 5000 and features["engagement_rate"] < 0.3:
        anomalies.append("Ghost followers detected: High follower count with near-zero engagement")

    # Follow-unfollow pattern proxy
    if features["ff_ratio"] > 3 and features["following_count"] > 1000:
        anomalies.append("Follow-unfollow pattern suspected: Aggressively following many accounts")

    # Burst posting on new account
    if features["posts_per_week"] > 15 and features["account_age_days"] < 60:
        anomalies.append("Abnormal posting frequency for account age – possible automation")

    # Zero-bio with high following
    if features["bio_length"] == 0 and features["following_count"] > 200:
        anomalies.append("No bio + high following count – typical bot profile structure")

    # Username randomness + spam combo
    if features["username_randomness"] > 0.5 and features["spam_keyword_score"] > 0.3:
        anomalies.append("Username pattern + spam keywords combo – high bot probability")

    return anomalies


# ── AI Explanation Summary generator ─────────────────────────────────────────

def _generate_explanation(
    status: str,
    hybrid_score: float,
    rule_score: float,
    ml_prob: float,
    flags: List[str],
    anomalies: List[str],
    features: dict
) -> str:
    score_pct  = round(hybrid_score, 1)
    rule_pct   = round(rule_score, 1)
    ml_pct     = round(ml_prob * 100, 1)
    n_flags    = len(flags)
    n_anomalies = len(anomalies)

    if status == "REAL":
        return (
            f"This profile shows a low risk score of {score_pct}%. "
            f"The rule engine flagged {n_flags} minor concern(s) and "
            f"the ML model assigned a fake probability of {ml_pct}%. "
            f"Overall, the account exhibits typical legitimate behaviour: "
            f"reasonable engagement, adequate account age, and consistent "
            f"follower-to-following ratio."
        )

    if status == "SUSPICIOUS":
        top_flags = " ".join(f'"{f}"' for f in flags[:2]) if flags else "none"
        return (
            f"This profile received a medium risk score of {score_pct}%. "
            f"The rule-based engine contributed {rule_pct}/100 "
            f"and the ML model estimated {ml_pct}% fake probability. "
            f"Key concerns include: {top_flags}. "
            f"{n_anomalies} behavioral anomal{'y' if n_anomalies==1 else 'ies'} detected. "
            f"Manual review is recommended before trusting this profile."
        )

    # HIGH RISK
    top_flags = ", ".join(f'"{f}"' for f in flags[:3]) if flags else "multiple violations"
    return (
        f"⚠ This profile is classified as HIGH RISK with a score of {score_pct}%. "
        f"The rule engine raised {n_flags} red flag(s) contributing {rule_pct}/100. "
        f"The ML model (Random Forest) independently predicted {ml_pct}% fake probability. "
        f"Critical signals: {top_flags}. "
        f"{n_anomalies} behavioral anomal{'y' if n_anomalies==1 else 'ies'} reinforce this verdict. "
        f"This account strongly matches known fake/bot profile patterns."
    )


# ── Main hybrid analyzer ──────────────────────────────────────────────────────

def analyze_profile(raw_profile: dict) -> dict:
    """
    Full pipeline:
      1. Feature engineering
      2. Rule engine
      3. ML inference
      4. Hybrid score
      5. Behavioral anomalies
      6. AI explanation

    Returns a comprehensive result dict consumed by the API.
    """
    # 1. Features
    features = build_feature_vector(raw_profile)

    # 2. Rule engine
    rule_output: RuleEngineOutput = compute_rule_score(features)

    # 3. ML
    ml_output  = ml_predict(features)
    ml_prob    = ml_output["primary_ml_prob"]
    lr_prob    = ml_output["lr_probability"]
    rf_prob    = ml_output["rf_probability"]

    # 4. Hybrid
    hybrid_score = round(
        RULE_WEIGHT * rule_output.rule_score + ML_WEIGHT * ml_prob * 100, 2
    )
    hybrid_score = min(hybrid_score, 100.0)

    # 5. Anomalies
    anomalies    = _behavioral_anomalies(features)

    # 6. Status
    status       = _status_badge(hybrid_score)
    status_color = _status_color(status)

    # 7. Explanation
    explanation  = _generate_explanation(
        status, hybrid_score,
        rule_output.rule_score, ml_prob,
        rule_output.flags, anomalies, features
    )

    # Rule contribution breakdown for chart
    flag_weights = rule_output.flag_weights

    return {
        # ── Scores ──────────────────────────────────────────────────────────
        "hybrid_score":      hybrid_score,
        "rule_score":        round(rule_output.rule_score, 2),
        "ml_rf_probability": round(rf_prob * 100, 2),
        "ml_lr_probability": round(lr_prob * 100, 2),

        # ── Classification ───────────────────────────────────────────────────
        "status":       status,
        "status_color": status_color,

        # ── Explainability ───────────────────────────────────────────────────
        "flags":           rule_output.flags,
        "flag_weights":    flag_weights,
        "anomalies":       anomalies,
        "explanation":     explanation,

        # ── Features ─────────────────────────────────────────────────────────
        "features":        {k: v for k, v in features.items()
                            if k not in ("username", "bio")},

        # ── Rule details ─────────────────────────────────────────────────────
        "rule_details": [
            {
                "rule_id":   r.rule_id,
                "triggered": r.triggered,
                "weight":    r.weight,
                "penalty":   r.penalty,
                "reason":    r.reason,
            }
            for r in rule_output.rule_results
        ],

        # ── Model comparison (for research charts) ───────────────────────────
        "model_comparison": {
            "rule_based": round(rule_output.rule_score, 2),
            "ml_rf":      round(rf_prob * 100, 2),
            "ml_lr":      round(lr_prob * 100, 2),
            "hybrid":     hybrid_score,
        },
    }
