"""
Feature Engineering Module
Computes all profile features used by both rule-based and ML models.
"""

import re
import math


# ── Spam keyword lexicon ──────────────────────────────────────────────────────
SPAM_KEYWORDS = [
    "follow back", "followback", "follow for follow", "f4f", "l4l", "like4like",
    "gain followers", "free followers", "dm for promo", "click link", "buy now",
    "win free", "limited offer", "get rich", "make money fast", "work from home",
    "100% real", "no spam", "only fans", "onlyfans", "check bio", "link in bio promo",
    "instant followers", "legit", "verify me", "investment return", "bitcoin profit",
    "crypto giveaway", "double your money",
]

# Common random-name patterns used by bots
BOT_NAME_PATTERNS = [
    r"^[a-z]{3,6}\d{4,}$",          # letters + 4+ digits  e.g. "john1234"
    r"^[a-z]+_[a-z]+\d{3,}$",       # word_word + 3+ digits
    r"^\w{1,3}\d{6,}$",              # very short prefix + long number
    r"^[a-zA-Z]{2}\d{8,}$",         # 2 letters + 8+ digits
    r"^user\d+$",                    # user12345
    r"^[a-z]{5,12}\.[a-z]{5,12}\d{2,}$",  # firstname.lastname123
]


def compute_username_randomness(username: str) -> float:
    """
    Returns a score 0-1 indicating how 'random' / bot-like a username looks.
    Higher = more suspicious.
    """
    if not username:
        return 0.5

    u = username.lower().strip()
    score = 0.0

    # Pattern matching
    for pattern in BOT_NAME_PATTERNS:
        if re.match(pattern, u):
            score += 0.4
            break

    # High digit ratio
    digits = sum(c.isdigit() for c in u)
    if len(u) > 0:
        digit_ratio = digits / len(u)
        if digit_ratio > 0.4:
            score += 0.2

    # Very long username
    if len(u) > 20:
        score += 0.15

    # Consecutive repeated chars
    if re.search(r"(.)\1{3,}", u):
        score += 0.15

    # Underscore spam
    if u.count("_") >= 3:
        score += 0.1

    return min(round(score, 3), 1.0)


def compute_spam_keyword_score(bio: str, caption: str = "") -> float:
    """
    Returns 0-1 score for spam keyword density in bio + caption.
    """
    text = f"{bio} {caption}".lower()
    if not text.strip():
        return 0.0

    hits = sum(1 for kw in SPAM_KEYWORDS if kw in text)
    score = min(hits / 5.0, 1.0)   # cap at 5 hits = 1.0
    return round(score, 3)


def compute_engagement_rate(followers: int, avg_likes: int, avg_comments: int) -> float:
    """
    Engagement rate = (avg_likes + avg_comments) / followers * 100
    Returns percentage, capped at 100.
    """
    if followers <= 0:
        return 0.0
    rate = ((avg_likes + avg_comments) / followers) * 100
    return round(min(rate, 100.0), 3)


def compute_posts_per_week(total_posts: int, account_age_days: int) -> float:
    if account_age_days <= 0:
        return 0.0
    weeks = account_age_days / 7
    return round(total_posts / weeks, 3)


def build_feature_vector(profile: dict) -> dict:
    """
    Takes raw profile dict and returns enriched feature dict.

    Required keys:
        username, bio, followers_count, following_count,
        account_age_days, total_posts, avg_likes, avg_comments,
        has_profile_picture, caption (optional)
    """
    followers   = max(int(profile.get("followers_count", 0)), 0)
    following   = max(int(profile.get("following_count", 0)), 0)
    age_days    = max(int(profile.get("account_age_days", 0)), 0)
    total_posts = max(int(profile.get("total_posts", 0)), 0)
    avg_likes   = max(int(profile.get("avg_likes", 0)), 0)
    avg_comments= max(int(profile.get("avg_comments", 0)), 0)
    bio         = str(profile.get("bio", ""))
    username    = str(profile.get("username", ""))
    caption     = str(profile.get("caption", ""))
    has_pic     = int(bool(profile.get("has_profile_picture", False)))

    engagement  = compute_engagement_rate(followers, avg_likes, avg_comments)
    ppw         = compute_posts_per_week(total_posts, age_days)
    username_rs = compute_username_randomness(username)
    spam_score  = compute_spam_keyword_score(bio, caption)
    bio_length  = len(bio.strip())
    ff_ratio    = round(following / max(followers, 1), 4)

    return {
        "followers_count":     followers,
        "following_count":     following,
        "engagement_rate":     engagement,
        "account_age_days":    age_days,
        "posts_per_week":      ppw,
        "bio_length":          bio_length,
        "profile_picture":     has_pic,
        "username_randomness": username_rs,
        "spam_keyword_score":  spam_score,
        "ff_ratio":            ff_ratio,
        # raw carry-throughs
        "total_posts":         total_posts,
        "avg_likes":           avg_likes,
        "avg_comments":        avg_comments,
        "username":            username,
        "bio":                 bio,
    }


# ── Feature names for ML model (must match training order) ────────────────────
ML_FEATURE_NAMES = [
    "followers_count",
    "following_count",
    "engagement_rate",
    "account_age_days",
    "posts_per_week",
    "bio_length",
    "profile_picture",
    "username_randomness",
    "spam_keyword_score",
    "ff_ratio",
]
