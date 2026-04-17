"""
lib/analysis.py — Pure analysis functions for score data.
No Streamlit or DB dependencies; all inputs are plain Python dicts.
"""

from __future__ import annotations


def calc_score_change(scores: list[dict]) -> dict:
    """Sort scores by exam_date and return change between the two most recent exams.

    Returns:
        {
            "current": int,
            "previous": int | None,
            "change": int,
            "direction": "up" | "down" | "same",
        }
    """
    if not scores:
        return {"current": 0, "previous": None, "change": 0, "direction": "same"}

    sorted_scores = sorted(scores, key=lambda s: s["exams"]["exam_date"])
    current_score = sorted_scores[-1]["total_score"]

    if len(sorted_scores) == 1:
        return {
            "current": current_score,
            "previous": None,
            "change": 0,
            "direction": "same",
        }

    previous_score = sorted_scores[-2]["total_score"]
    change = current_score - previous_score

    if change > 0:
        direction = "up"
    elif change < 0:
        direction = "down"
    else:
        direction = "same"

    return {
        "current": current_score,
        "previous": previous_score,
        "change": change,
        "direction": direction,
    }


def calc_class_average(scores: list[dict]) -> float:
    """Return the class average total_score rounded to one decimal place."""
    if not scores:
        return 0.0
    total = sum(s["total_score"] for s in scores)
    return round(total / len(scores), 1)


def rank_in_group(student_id: int, scores: list[dict]) -> dict:
    """Return the rank of a student among the provided scores.

    Ranking is 1-based with the highest score ranked 1.

    Returns:
        {"rank": int, "total": int}
    """
    sorted_scores = sorted(scores, key=lambda s: s["total_score"], reverse=True)
    total = len(sorted_scores)

    for i, s in enumerate(sorted_scores, start=1):
        if s["student_id"] == student_id:
            return {"rank": i, "total": total}

    return {"rank": total, "total": total}


def calc_category_changes(current: list[dict], previous: list[dict]) -> dict:
    """Compute per-category score changes between two exam results.

    Each item in `current` and `previous` must have:
        - "category_name": str
        - "score": int

    Returns a dict keyed by category_name:
        {
            category_name: {
                "current": int,
                "previous": int | None,
                "change": int,
            }
        }
    """
    previous_map = {item["category_name"]: item["score"] for item in previous}

    result: dict[str, dict] = {}
    for item in current:
        name = item["category_name"]
        curr_score = item["score"]
        prev_score = previous_map.get(name)

        result[name] = {
            "current": curr_score,
            "previous": prev_score,
            "change": (curr_score - prev_score) if prev_score is not None else 0,
        }

    return result


def find_strengths_weaknesses(categories: list[dict]) -> dict:
    """Identify the strongest and weakest categories based on score.

    A category is a "strength" if its score is above the mean,
    and a "weakness" if its score is below the mean.

    Each item must have:
        - "category_name": str
        - "score": int | float

    Returns:
        {"strengths": [str, ...], "weaknesses": [str, ...]}
    """
    if not categories:
        return {"strengths": [], "weaknesses": []}

    avg = sum(c["score"] for c in categories) / len(categories)

    strengths = [c["category_name"] for c in categories if c["score"] > avg]
    weaknesses = [c["category_name"] for c in categories if c["score"] < avg]

    return {"strengths": strengths, "weaknesses": weaknesses}
