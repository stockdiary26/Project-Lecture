"""
lib/ai.py — AI consultation generation using Claude API.

Provides:
- build_student_context: gathers all relevant data into a text string
- generate_consultation: calls Claude API to produce a Korean parent consultation letter
"""

import streamlit as st
import anthropic
from lib import db
from lib.analysis import (
    calc_score_change,
    calc_class_average,
    calc_category_changes,
    find_strengths_weaknesses,
    rank_in_group,
)


def _normalize_cat(raw: list[dict]) -> list[dict]:
    """categories 조인 결과에서 category_name 필드를 표준화한다."""
    normalized = []
    for item in raw:
        name = item.get("category_name") or (
            item["categories"]["name"] if item.get("categories") else "알 수 없음"
        )
        normalized.append({**item, "category_name": name})
    return normalized


def build_student_context(student_id: int, exam_id: int) -> str:
    """Gather all data needed for AI consultation and return as formatted text.

    Collects student info, scores, class average, rank, category scores,
    strengths/weaknesses, consultation history, and memos.
    """
    # --- Student info ---
    all_students = db.get_students()
    student = next((s for s in all_students if s["id"] == student_id), None)
    student_name = student["name"] if student else "알 수 없음"
    school_name = (student.get("school_name") or "학교 미지정") if student else "알 수 없음"

    # --- All scores for this student ---
    scores = db.get_scores_by_student(student_id)

    # --- Score change (current vs previous) ---
    score_change = calc_score_change(scores)

    # --- Class average and rank for the selected exam ---
    exam_scores = db.get_scores_by_exam(exam_id)
    class_avg = calc_class_average(exam_scores)
    rank_info = rank_in_group(student_id, exam_scores)

    # --- Latest score record for the selected exam ---
    latest_score = next((s for s in scores if s["exam_id"] == exam_id), None)

    # --- Category scores for the selected exam ---
    current_cats: list[dict] = []
    previous_cats: list[dict] = []
    category_changes: dict = {}
    sw: dict = {"strengths": [], "weaknesses": []}

    if latest_score:
        current_cats = _normalize_cat(db.get_category_scores(latest_score["id"]))

        # Find the previous exam score (by date, before selected exam)
        sorted_scores = sorted(scores, key=lambda s: s["exams"]["exam_date"])
        exam_index = next(
            (i for i, s in enumerate(sorted_scores) if s["exam_id"] == exam_id),
            None,
        )
        if exam_index is not None and exam_index > 0:
            prev_score = sorted_scores[exam_index - 1]
            previous_cats = _normalize_cat(db.get_category_scores(prev_score["id"]))

        if current_cats:
            category_changes = calc_category_changes(current_cats, previous_cats)
            sw = find_strengths_weaknesses(current_cats)

    # --- Previous consultations ---
    consultations = db.get_consultations_by_student(student_id)
    latest_consultation_text = ""
    if consultations:
        latest = consultations[0]
        final_text = latest.get("final_text") or latest.get("ai_draft") or ""
        latest_consultation_text = final_text[:500]

    # --- Memos ---
    memos = db.get_memos_by_student(student_id)
    recent_memos = memos[:3]

    # --- Build context text ---
    lines = [
        "=== 학생 정보 ===",
        f"이름: {student_name}",
        f"학교: {school_name}",
        "",
        "=== 성적 변화 ===",
        f"현재 점수: {score_change['current']}점",
    ]

    if score_change["previous"] is not None:
        direction_label = {"up": "상승", "down": "하락", "same": "유지"}[
            score_change["direction"]
        ]
        lines.append(f"이전 점수: {score_change['previous']}점")
        lines.append(
            f"변화: {score_change['change']:+d}점 ({direction_label})"
        )
    else:
        lines.append("이전 점수: 없음 (첫 시험)")

    lines += [
        "",
        "=== 반 비교 ===",
        f"반 평균: {class_avg:.1f}점",
        f"반 순위: {rank_info['rank']}위 / {rank_info['total']}명",
        f"평균 대비: {score_change['current'] - class_avg:+.1f}점",
    ]

    if category_changes:
        lines += ["", "=== 영역별 점수 ==="]
        for cat_name, info in category_changes.items():
            prev_str = (
                f" (이전: {info['previous']}점, 변화: {info['change']:+d}점)"
                if info["previous"] is not None
                else ""
            )
            lines.append(f"  {cat_name}: {info['current']}점{prev_str}")

    if sw["strengths"] or sw["weaknesses"]:
        lines += ["", "=== 강점 / 약점 ==="]
        if sw["strengths"]:
            lines.append(f"강점 영역: {', '.join(sw['strengths'])}")
        if sw["weaknesses"]:
            lines.append(f"약점 영역: {', '.join(sw['weaknesses'])}")

    if latest_consultation_text:
        lines += [
            "",
            "=== 이전 상담문 (최신, 최대 500자) ===",
            latest_consultation_text,
        ]

    if recent_memos:
        lines += ["", "=== 최근 메모 (최대 3건) ==="]
        for memo in recent_memos:
            created = memo.get("created_at", "")[:10]
            lines.append(f"[{created}] {memo.get('content', '')}")

    return "\n".join(lines)


def generate_consultation(student_id: int, exam_id: int) -> str:
    """Call Claude API to generate a Korean parent consultation letter.

    Uses the student context from build_student_context() as user message.
    Returns the generated text.
    """
    context = build_student_context(student_id, exam_id)

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    system_prompt = (
        "당신은 한국 학원의 담임 강사입니다. 학부모님께 보내는 상담문을 작성합니다.\n"
        "\n"
        "작성 규칙:\n"
        "1. 존댓말을 사용합니다 (합니다/습니다체).\n"
        "2. 따뜻하면서도 전문적인 어조를 유지합니다.\n"
        "3. 다음 구조로 작성합니다: 성적 변화 요약 → 강점 언급 → 보완 필요 사항 → 학습 제안.\n"
        "4. 구체적인 숫자(점수, 순위, 변화량 등)를 포함하여 신뢰감을 줍니다.\n"
        "5. 전체 글자 수는 300~500자 내외로 작성합니다.\n"
        "6. 인사말로 시작하고 마무리 인사로 끝냅니다.\n"
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "아래 학생 데이터를 바탕으로 학부모 상담문을 작성해 주세요.\n\n"
                    + context
                ),
            }
        ],
    )

    return message.content[0].text
