"""
pages/2_📝_성적입력.py — 시험 생성 및 성적 입력 페이지
"""

import pandas as pd
import streamlit as st
from lib.auth import check_password
from lib import db

if not check_password():
    st.stop()

st.title("📝 성적 입력")

# ---------------------------------------------------------------------------
# 반(Class) 확인
# ---------------------------------------------------------------------------

classes = db.get_classes()
if not classes:
    st.warning("등록된 반이 없습니다. 먼저 학생 관리 페이지에서 반을 추가하세요.")
    st.stop()

# ---------------------------------------------------------------------------
# 시험 선택 / 생성
# ---------------------------------------------------------------------------

st.subheader("시험 선택")

tab_existing, tab_new = st.tabs(["기존 시험 선택", "새 시험 생성"])

with tab_existing:
    exams = db.get_exams()
    if exams:
        exam_options = {
            f"{e['name']} ({e['exam_type']}, {e['exam_date']})": e["id"]
            for e in exams
        }
        selected_exam_label = st.selectbox(
            "시험 선택", options=list(exam_options.keys()), key="exam_select"
        )
        selected_exam_id = exam_options[selected_exam_label]
    else:
        st.info("등록된 시험이 없습니다. '새 시험 생성' 탭에서 시험을 추가하세요.")

with tab_new:
    with st.form("create_exam_form", clear_on_submit=True):
        exam_name = st.text_input("시험 이름", placeholder="예: 2025 1학기 중간고사")
        exam_type = st.selectbox("시험 유형", options=["중간", "기말", "모의고사"])
        exam_date = st.date_input("시험 날짜")
        exam_submitted = st.form_submit_button("시험 생성")

    if exam_submitted:
        if exam_name.strip():
            db.create_exam(exam_name.strip(), exam_type, str(exam_date))
            st.success(f"'{exam_name.strip()}' 시험이 생성되었습니다.")
            st.rerun()
        else:
            st.error("시험 이름을 입력하세요.")

# ---------------------------------------------------------------------------
# 시험 존재 확인 (탭 이후)
# ---------------------------------------------------------------------------

exams = db.get_exams()
if not exams:
    st.info("시험을 먼저 생성해야 성적을 입력할 수 있습니다.")
    st.stop()

# 현재 선택된 시험 ID 결정
if "exam_select" in st.session_state:
    exam_options_current = {
        f"{e['name']} ({e['exam_type']}, {e['exam_date']})": e["id"]
        for e in exams
    }
    current_exam_label = st.session_state.get("exam_select")
    if current_exam_label and current_exam_label in exam_options_current:
        selected_exam_id = exam_options_current[current_exam_label]
    else:
        selected_exam_id = exams[0]["id"]
else:
    selected_exam_id = exams[0]["id"]

st.divider()

# ---------------------------------------------------------------------------
# 성적 입력
# ---------------------------------------------------------------------------

st.subheader("성적 입력")

# 반 선택
class_options = {cls["name"]: cls["id"] for cls in classes}
selected_class_name = st.selectbox(
    "반 선택", options=list(class_options.keys()), key="score_class_select"
)
selected_class_id = class_options[selected_class_name]

# 학교별 정렬 토글
sort_by_school = st.checkbox("학교별 정렬")

# 학생 목록 조회
students = db.get_students(selected_class_id)

if not students:
    st.info("이 반에 등록된 학생이 없습니다.")
    st.stop()

# 학교별 정렬 적용
if sort_by_school:
    students = sorted(
        students,
        key=lambda s: (s.get("school_name") or "", s.get("name") or ""),
    )

# 기존 성적 조회 — student_id → score 매핑
existing_scores = db.get_scores_by_exam(selected_exam_id)
score_map = {s["student_id"]: s for s in existing_scores}

# DataFrame 구성
rows = []
for s in students:
    existing = score_map.get(s["id"])
    rows.append(
        {
            "student_id": s["id"],
            "이름": s["name"],
            "학교명": s.get("school_name") or "",
            "총점": existing["total_score"] if existing else None,
            "등급": existing["grade"] if existing else None,
        }
    )

df = pd.DataFrame(rows)

# data_editor로 인라인 편집
edited_df = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "student_id": None,  # 숨김
        "이름": st.column_config.TextColumn("이름", disabled=True),
        "학교명": st.column_config.TextColumn("학교명", disabled=True),
        "총점": st.column_config.NumberColumn("총점", min_value=0, max_value=100),
        "등급": st.column_config.NumberColumn("등급", min_value=1, max_value=9),
    },
    key="score_editor",
)

# ---------------------------------------------------------------------------
# 저장 버튼
# ---------------------------------------------------------------------------

if st.button("성적 저장", type="primary"):
    success_count = 0
    errors = []

    for _, row in edited_df.iterrows():
        student_id = int(row["student_id"])
        total_score = row["총점"]
        grade = row["등급"]

        # 총점이 없으면 스킵
        if total_score is None or (isinstance(total_score, float) and pd.isna(total_score)):
            continue

        # 총점 범위 검증 (0–100)
        try:
            total_score = int(total_score)
        except (ValueError, TypeError):
            errors.append(f"{row['이름']}: 총점이 올바르지 않습니다.")
            continue

        if not (0 <= total_score <= 100):
            errors.append(f"{row['이름']}: 총점은 0–100 사이여야 합니다. (입력값: {total_score})")
            continue

        # 등급 검증 (1–9, None은 허용)
        grade_value = None
        if grade is not None and not (isinstance(grade, float) and pd.isna(grade)):
            try:
                grade_value = int(grade)
            except (ValueError, TypeError):
                errors.append(f"{row['이름']}: 등급이 올바르지 않습니다.")
                continue

            if not (1 <= grade_value <= 9):
                errors.append(f"{row['이름']}: 등급은 1–9 사이여야 합니다. (입력값: {grade_value})")
                continue

        db.upsert_score(student_id, selected_exam_id, total_score, grade_value)
        success_count += 1

    if errors:
        for err in errors:
            st.error(err)

    if success_count > 0:
        st.success(f"{success_count}명의 성적이 저장되었습니다.")

# ── 영역별 점수 입력 ─────────────────────────
st.divider()
st.subheader("📊 영역별 점수 입력 (선택)")
st.caption("영역별 점수는 선택사항입니다. 입력하면 영역별 분석이 가능해집니다.")

selected_exam = next((e for e in exams if e["id"] == selected_exam_id), None)

categories = db.get_categories()
if categories and selected_exam:
    cat_student = st.selectbox(
        "학생 선택 (영역별 점수)", students,
        format_func=lambda s: f"{s['name']} ({s.get('school_name') or ''})",
        key="cat_student_select"
    )

    # Get existing score for this student+exam
    existing = db.get_scores_by_exam(selected_exam["id"])
    student_score = next((s for s in existing if s["student_id"] == cat_student["id"]), None)

    if student_score:
        existing_cat_scores = db.get_category_scores(student_score["id"])
        cat_score_map = {}
        for cs in existing_cat_scores:
            cat_name = cs.get("categories", {}).get("name", "")
            cat_score_map[cat_name] = cs["score"]

        with st.form("category_scores_form"):
            cat_values = {}
            cols = st.columns(len(categories))
            for i, cat in enumerate(categories):
                with cols[i]:
                    cat_values[cat["id"]] = st.number_input(
                        cat["name"],
                        min_value=0,
                        value=cat_score_map.get(cat["name"], 0),
                        key=f"cat_{cat['id']}"
                    )

            if st.form_submit_button("영역별 점수 저장"):
                for cat_id, score in cat_values.items():
                    if score > 0:
                        db.upsert_category_score(student_score["id"], cat_id, score)
                st.success("영역별 점수 저장 완료!")
                st.rerun()
    else:
        st.info("이 학생의 총점을 먼저 입력해주세요.")
