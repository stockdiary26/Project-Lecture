from lib.analysis import (
    calc_score_change, calc_class_average, calc_category_changes,
    rank_in_group, find_strengths_weaknesses,
)

def test_calc_score_change():
    scores = [
        {"total_score": 85, "exams": {"exam_date": "2026-03-15"}},
        {"total_score": 92, "exams": {"exam_date": "2026-04-15"}},
    ]
    result = calc_score_change(scores)
    assert result["current"] == 92
    assert result["previous"] == 85
    assert result["change"] == 7
    assert result["direction"] == "up"

def test_calc_score_change_single():
    scores = [{"total_score": 85, "exams": {"exam_date": "2026-03-15"}}]
    result = calc_score_change(scores)
    assert result["current"] == 85
    assert result["previous"] is None
    assert result["change"] == 0

def test_calc_class_average():
    assert calc_class_average([{"total_score": 85}, {"total_score": 90}, {"total_score": 75}]) == 83.3

def test_calc_class_average_empty():
    assert calc_class_average([]) == 0.0

def test_rank_in_group():
    scores = [{"student_id": 1, "total_score": 90}, {"student_id": 2, "total_score": 85}, {"student_id": 3, "total_score": 95}]
    assert rank_in_group(2, scores) == {"rank": 3, "total": 3}

def test_calc_category_changes():
    current = [{"category_name": "문법", "score": 32}, {"category_name": "독해", "score": 35}]
    previous = [{"category_name": "문법", "score": 28}, {"category_name": "독해", "score": 30}]
    result = calc_category_changes(current, previous)
    assert result["문법"]["change"] == 4
    assert result["독해"]["change"] == 5

def test_calc_category_changes_no_previous():
    result = calc_category_changes([{"category_name": "문법", "score": 32}], [])
    assert result["문법"]["previous"] is None

def test_find_strengths_weaknesses():
    cats = [{"category_name": "문법", "score": 32}, {"category_name": "독해", "score": 35}, {"category_name": "문학", "score": 20}]
    result = find_strengths_weaknesses(cats)
    assert "독해" in result["strengths"]
    assert "문학" in result["weaknesses"]
