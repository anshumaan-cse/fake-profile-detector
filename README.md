# FakeProfileDetector — Hybrid AI System v2.0

> **Production-grade + Research-ready** fake social media profile detection powered by a hybrid engine combining rule-based heuristics and machine learning.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-teal)
![ML](https://img.shields.io/badge/ML-RandomForest%20%2B%20LogisticRegression-orange)
![UI](https://img.shields.io/badge/UI-Glassmorphism%20Dark%20SaaS-purple)

---

## 📋 Problem Statement

Fake and bot accounts are a growing threat on social platforms — enabling spam, misinformation, and fraud. Traditional rule-based systems have low precision; pure ML models lack explainability. This system solves both problems via a **hybrid approach** that combines interpretable heuristic rules with ML probability scores.

---

## 🏗️ System Architecture

```
Profile Input
      ↓
Feature Engineering (10 computed features)
      ↓
    ┌─────────────────────┬──────────────────────┐
    │   Rule Engine        │    ML Models          │
    │   12 heuristic rules │    Logistic Regression│
    │   Weighted scoring   │    Random Forest ✓    │
    └─────────────────────┴──────────────────────┘
              ↓                       ↓
         Rule Score              ML Probability
              └──────────┬──────────┘
                         ↓
              Hybrid Scorer
         (0.6 × Rule) + (0.4 × RF × 100)
                         ↓
     Risk Score + Status Badge + AI Explanation
```

---

## 🔬 Hybrid Model

The final risk score combines both engines with empirically chosen weights:

```
Final Risk Score = (0.6 × Rule Score) + (0.4 × ML Probability × 100)
```

| Component | Weight | Model |
|-----------|--------|-------|
| Rule Engine | 60% | 12 modular heuristic rules |
| ML (Random Forest) | 40% | 200-tree ensemble, primary model |
| ML (Logistic Regression) | — | Baseline comparator only |

**Status thresholds:**
| Score | Status |
|-------|--------|
| 0–34 | ✅ REAL |
| 35–64 | ⚠️ SUSPICIOUS |
| 65–100 | 🚨 HIGH RISK |

---

## 🧠 Feature Engineering

All features are computed automatically from raw profile inputs:

| Feature | Description |
|---------|-------------|
| `followers_count` | Raw follower count |
| `following_count` | Raw following count |
| `engagement_rate` | `(avg_likes + avg_comments) / followers × 100` |
| `account_age_days` | Days since account creation |
| `posts_per_week` | `total_posts / (age_days / 7)` |
| `bio_length` | Character count of bio |
| `profile_picture` | Binary: has pic or not |
| `username_randomness` | Pattern-based score 0–1 |
| `spam_keyword_score` | NLP keyword density 0–1 |
| `ff_ratio` | `following / followers` |

---

## 🔧 Rule Engine (12 Rules)

Rules are modular, independently configurable with weights:

1. `following_exceeds_followers` — F/F ratio ≥ 2.0
2. `very_new_account` — Age < 14 days
3. `new_account` — Age 14–60 days
4. `no_profile_picture` — Missing profile pic
5. `low_follower_count` — Under 50 followers
6. `spam_keywords_detected` — Bio/caption keyword hits
7. `random_username` — Bot-pattern username
8. `zero_engagement` — 0% engagement with 100+ followers
9. `suspiciously_high_engagement` — >60% with 1000+ followers
10. `post_burst_new_account` — >20 posts/week on new account
11. `empty_bio` — No bio text
12. `extreme_ff_ratio` — F/F ratio ≥ 10.0

---

## 📊 Model Results (Synthetic Dataset, 2,100 samples)

| Model | Accuracy | Precision | Recall | F1 | AUC |
|-------|----------|-----------|--------|----|-----|
| Logistic Regression | ~97% | ~97% | ~97% | ~97% | ~0.99 |
| Random Forest | ~99% | ~99% | ~99% | ~99% | ~1.00 |

> Note: Results are on a controlled synthetic dataset. Real-world performance will vary.

---

## 🖥️ Tech Stack

### Backend
- **FastAPI** — REST API with auto-generated OpenAPI docs
- **scikit-learn** — ML training (LogisticRegression + RandomForest)
- **joblib** — Model persistence
- **pandas / numpy** — Data processing

### Frontend
- **Vanilla JS** — No framework dependencies
- **Chart.js** — Interactive visualisations
- **CSS Glassmorphism** — Dark SaaS dashboard UI
- **Inter font** — Modern typography

---

## 📂 Project Structure

```
fake-profile-detector/
│
├── main.py                          # FastAPI app entry point
│
├── backend/
│   ├── routes/
│   │   ├── analysis.py              # POST /api/analyze
│   │   └── evaluation.py           # GET /api/evaluation/*
│   ├── services/
│   │   ├── rule_engine.py          # 12-rule heuristic scorer
│   │   ├── ml_service.py           # ML inference wrapper
│   │   └── hybrid_engine.py        # Hybrid pipeline + explanations
│   ├── models/
│   │   ├── trainer.py              # Dataset generation + model training
│   │   ├── random_forest.pkl       # Trained RF model
│   │   ├── logistic_regression.pkl # Trained LR model
│   │   ├── scaler.pkl              # Feature scaler
│   │   └── evaluation_report.json  # Metrics + ROC + confusion matrix
│   ├── utils/
│   │   └── feature_engineering.py  # Feature computation
│   └── data/
│       └── synthetic_profiles.csv  # 2100-sample training dataset
│
└── frontend/
    ├── index.html                   # Profile input page
    ├── dashboard.html               # Analysis results dashboard
    ├── research.html                # Evaluation / research module
    ├── css/main.css                 # Full glassmorphism UI stylesheet
    └── js/
        ├── analyzer.js              # Input form controller
        ├── dashboard.js             # Dashboard renderer + charts
        └── research.js              # Research page charts
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install fastapi uvicorn scikit-learn numpy pandas joblib python-multipart
```

### 2. Train models (auto-runs on startup if models missing)
```bash
python -m backend.models.trainer
```

### 3. Start server
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open browser
- **Analyzer**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **Research**: http://localhost:8000/research
- **API Docs**: http://localhost:8000/docs

---

## 🔌 API Reference

### `POST /api/analyze`
```json
{
  "username":            "john_doe123",
  "bio":                 "Follow me back! DM for promo",
  "followers_count":     45,
  "following_count":     2300,
  "account_age_days":    12,
  "total_posts":         8,
  "avg_likes":           2,
  "avg_comments":        0,
  "has_profile_picture": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "hybrid_score":  78.4,
    "rule_score":    82.1,
    "ml_rf_probability": 71.2,
    "status":        "HIGH RISK",
    "flags":         ["Following/Followers ratio is 51.1x", "..."],
    "anomalies":     ["Follow-unfollow pattern suspected..."],
    "explanation":   "⚠ This profile is classified as HIGH RISK...",
    "features":      { ... },
    "model_comparison": { ... }
  }
}
```

### `GET /api/evaluation/summary`
Returns full model evaluation metrics, confusion matrices, ROC curves, and feature importances.

---

## 👨‍💻 Author

**Anshumaan Singh** — Computer Science Undergraduate  
Upgraded to production-grade hybrid AI system v2.0.

---

## 📜 License

MIT License — free for academic and research use.
