"""
Rule-Based Scoring Engine
Modular, weight-configurable heuristic scorer.
Each rule returns a penalty (0-100) and a human-readable reason.
Final rule score = weighted sum, clamped to [0, 100].
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict


# ── Rule weight configuration ─────────────────────────────────────────────────
RULE_WEIGHTS: Dict[str, float] = {
    "following_exceeds_followers":  0.22,
    "very_new_account":             0.16,
    "new_account":                  0.10,
    "no_profile_picture":           0.12,
    "low_follower_count":           0.10,
    "spam_keywords_detected":       0.14,
    "random_username":              0.10,
    "zero_engagement":              0.12,
    "suspiciously_high_engagement": 0.08,
    "post_burst_new_account":       0.08,
    "empty_bio":                    0.06,
    "extreme_ff_ratio":             0.14,
}

# normalise weights so they sum to 1.0
_WEIGHT_SUM = sum(RULE_WEIGHTS.values())
RULE_WEIGHTS = {k: round(v / _WEIGHT_SUM, 4) for k, v in RULE_WEIGHTS.items()}


@dataclass
class RuleResult:
    rule_id:   str
    triggered: bool
    weight:    float
    penalty:   float        # 0-100 contribution before weighting
    reason:    str = ""


@dataclass
class RuleEngineOutput:
    rule_score:   float                  # 0-100 final weighted score
    rule_results: List[RuleResult] = field(default_factory=list)
    flags:        List[str]        = field(default_factory=list)
    flag_weights: Dict[str, float] = field(default_factory=dict)


# ── Individual rule functions ─────────────────────────────────────────────────

def _rule_following_exceeds_followers(f: dict) -> RuleResult:
    rid   = "following_exceeds_followers"
    ratio = f["ff_ratio"]
    if ratio >= 5.0:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          f"Following/Followers ratio is {ratio:.1f}x (extremely high)")
    if ratio >= 2.0:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 70,
                          f"Following/Followers ratio is {ratio:.1f}x (high)")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_very_new_account(f: dict) -> RuleResult:
    rid = "very_new_account"
    age = f["account_age_days"]
    if age < 14:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          f"Account only {age} days old (very new – high bot risk)")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_new_account(f: dict) -> RuleResult:
    rid = "new_account"
    age = f["account_age_days"]
    if 14 <= age < 60:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 60,
                          f"Account is {age} days old (relatively new)")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_no_profile_picture(f: dict) -> RuleResult:
    rid = "no_profile_picture"
    if not f["profile_picture"]:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          "No profile picture – common fake account trait")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_low_follower_count(f: dict) -> RuleResult:
    rid = "low_follower_count"
    fc  = f["followers_count"]
    if fc < 10:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          f"Only {fc} followers (very low)")
    if fc < 50:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 60,
                          f"Only {fc} followers (low)")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_spam_keywords(f: dict) -> RuleResult:
    rid   = "spam_keywords_detected"
    score = f["spam_keyword_score"]
    if score >= 0.6:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          f"Multiple spam keywords detected in bio/caption (score {score:.2f})")
    if score >= 0.2:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 50,
                          f"Spam keyword hint detected (score {score:.2f})")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_random_username(f: dict) -> RuleResult:
    rid   = "random_username"
    score = f["username_randomness"]
    if score >= 0.6:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          f"Username pattern matches bot/fake naming (score {score:.2f})")
    if score >= 0.3:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 50,
                          f"Username has mild randomness (score {score:.2f})")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_zero_engagement(f: dict) -> RuleResult:
    rid = "zero_engagement"
    if f["engagement_rate"] == 0 and f["followers_count"] > 100:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          "Zero engagement with 100+ followers – suspicious inactivity")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_suspiciously_high_engagement(f: dict) -> RuleResult:
    rid = "suspiciously_high_engagement"
    if f["engagement_rate"] > 60 and f["followers_count"] > 1000:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 80,
                          f"Engagement rate {f['engagement_rate']:.1f}% is unrealistically high")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_post_burst_new_account(f: dict) -> RuleResult:
    rid = "post_burst_new_account"
    ppw = f["posts_per_week"]
    age = f["account_age_days"]
    if age < 30 and ppw > 20:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 90,
                          f"{ppw:.1f} posts/week on a {age}-day-old account – burst posting")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_empty_bio(f: dict) -> RuleResult:
    rid = "empty_bio"
    if f["bio_length"] == 0:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 70,
                          "Empty bio – common fake/bot account pattern")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


def _rule_extreme_ff_ratio(f: dict) -> RuleResult:
    rid   = "extreme_ff_ratio"
    ratio = f["ff_ratio"]
    if ratio >= 10.0:
        return RuleResult(rid, True, RULE_WEIGHTS[rid], 100,
                          f"Extreme follower-following ratio: {ratio:.1f}x")
    return RuleResult(rid, False, RULE_WEIGHTS[rid], 0)


# ── Ordered rule pipeline ─────────────────────────────────────────────────────
_RULES = [
    _rule_following_exceeds_followers,
    _rule_very_new_account,
    _rule_new_account,
    _rule_no_profile_picture,
    _rule_low_follower_count,
    _rule_spam_keywords,
    _rule_random_username,
    _rule_zero_engagement,
    _rule_suspiciously_high_engagement,
    _rule_post_burst_new_account,
    _rule_empty_bio,
    _rule_extreme_ff_ratio,
]


# ── Main scorer ───────────────────────────────────────────────────────────────

def compute_rule_score(features: dict) -> RuleEngineOutput:
    """
    Runs all rules and returns a weighted composite score in [0, 100].
    """
    results: List[RuleResult] = []
    weighted_sum = 0.0

    for rule_fn in _RULES:
        result = rule_fn(features)
        results.append(result)
        if result.triggered:
            weighted_sum += result.weight * result.penalty

    # Normalise to 0-100
    max_possible = sum(r.weight * 100 for r in results)
    rule_score   = round((weighted_sum / max(max_possible, 1)) * 100, 2)
    rule_score   = min(rule_score, 100.0)

    flags        = [r.reason for r in results if r.triggered]
    flag_weights = {r.reason: round(r.weight * r.penalty, 2)
                    for r in results if r.triggered}

    return RuleEngineOutput(
        rule_score=rule_score,
        rule_results=results,
        flags=flags,
        flag_weights=flag_weights,
    )
