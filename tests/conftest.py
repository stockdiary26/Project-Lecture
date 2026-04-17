import pytest


@pytest.fixture
def sample_scores():
    """테스트용 점수 데이터."""
    return [
        {"student_id": 1, "exam_id": 1, "total_score": 85, "grade": 3},
        {"student_id": 1, "exam_id": 2, "total_score": 92, "grade": 2},
        {"student_id": 2, "exam_id": 1, "total_score": 70, "grade": 5},
        {"student_id": 2, "exam_id": 2, "total_score": 78, "grade": 4},
    ]


@pytest.fixture
def sample_category_scores():
    """테스트용 영역별 점수 데이터."""
    return [
        {"score_id": 1, "category_id": 1, "category_name": "문법", "score": 28},
        {"score_id": 1, "category_id": 2, "category_name": "독해", "score": 30},
        {"score_id": 1, "category_id": 3, "category_name": "문학", "score": 27},
        {"score_id": 2, "category_id": 1, "category_name": "문법", "score": 32},
        {"score_id": 2, "category_id": 2, "category_name": "독해", "score": 35},
        {"score_id": 2, "category_id": 3, "category_name": "문학", "score": 25},
    ]


@pytest.fixture
def sample_students():
    """테스트용 학생 데이터."""
    return [
        {"id": 1, "name": "김철수", "school_name": "OO고", "class_id": 1},
        {"id": 2, "name": "이영희", "school_name": "△△고", "class_id": 1},
        {"id": 3, "name": "박지민", "school_name": "OO고", "class_id": 1},
    ]
