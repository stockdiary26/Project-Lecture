"""
pages/2_📝_성적입력.py — 학생별/시험별 성적 입력 (총점·등급·영역별 통합)
"""

import pandas as pd
import streamlit as st
from lib.auth import check_password
from lib import db

if not check_password():
    st.stop()

st.title("📝 성적 입력")

# ---------------------------------------------------------------------------
# 사전 조건
# ---------------------------------------------------------------------------

classes = db.get_classes()
if not classes:
    st.warning("등록된 반이 없습니다. 먼저 학생 관리 페이지에서 반을 추가하세요.")
    st.stop()

# ---------------------------------------------------------------------------
# 새 시험 생성 (Expander)
# ---------------------------------------------------------------------------

with st.expander("➕ 새 시험 생성"):
    with st.form("create_exam_form", clear_on_submit=True):
        new_exam_name = st.text_input(
            "시험 이름", placeholder="예: 2025 1학기 중간고사"
        )
        new_exam_type = st.selectbox("시험 유형", options=["중간", "기말", "모의고사"])
        new_exam_date = st.date_input("시험 날짜")
        if st.form_submit_button("시험 생성"):
            if new_exam_name.strip():
                db.create_exam(
                    new_exam_name.strip(),
                    new_exam_type,
                    str(new_exam_date),
                )
                st.success(f"'{new_exam_name.strip()}' 시험이 생성되었습니다.")
                st.rerun()
            else:
                st.error("시험 이름을 입력하세요.")

exams = db.get_exams()
categories = db.get_categories()

if not exams:
    st.info("시험을 먼저 생성해야 성적을 입력할 수 있습니다.")
    st.stop()

# ---------------------------------------------------------------------------
# 공용 헬퍼
# ---------------------------------------------------------------------------


def _is_blank(value) -> bool:
    return (
        value is None
        or (isinstance(value, float) and pd.isna(value))
        or value == ""
    )


def _save_row(
    student_id: int,
    exam_id: int,
    total_score,
    grade,
    category_values: dict,
    label: str,
) -> tuple[bool, str | None]:
    """Save a single row's scores. 총점이 비면 행 전체 스킵.

    총점 필수, 등급·영역별 선택. 영역별은 빈 셀이면 기존 DB 값을 유지한다.
    Returns (saved, error_message). (False, None) = silently skipped.
    """
    if _is_blank(total_score):
        return False, None
    try:
        total = int(total_score)
    except (ValueError, TypeError):
        return False, f"{label}: 총점 값이 올바르지 않습니다."
    if not (0 <= total <= 100):
        return False, f"{label}: 총점은 0–100 사이여야 합니다. (입력값: {total})"

    grade_val: int | None = None
    if not _is_blank(grade):
        try:
            grade_val = int(grade)
        except (ValueError, TypeError):
            return False, f"{label}: 등급 값이 올바르지 않습니다."
        if not (1 <= grade_val <= 9):
            return False, f"{label}: 등급은 1–9 사이여야 합니다. (입력값: {grade_val})"

    score_row = db.upsert_score(student_id, exam_id, total, grade_val)
    score_id = score_row["id"]

    for cat_id, cat_val in category_values.items():
        if _is_blank(cat_val):
            continue
        try:
            cv = int(cat_val)
        except (ValueError, TypeError):
            continue
        if cv < 0:
            continue
        db.upsert_category_score(score_id, cat_id, cv)

    return True, None


def _category_column_config(cats: list[dict]) -> dict:
    return {
        cat["name"]: st.column_config.NumberColumn(cat["name"], min_value=0)
        for cat in cats
    }


def _cat_map_by_score_id(rows: list[dict]) -> dict[int, dict[str, int]]:
    """Group category_scores rows by score_id → {category_name: score}."""
    result: dict[int, dict[str, int]] = {}
    for row in rows:
        name = (row.get("categories") or {}).get("name")
        if not name:
            continue
        result.setdefault(row["score_id"], {})[name] = row["score"]
    return result


# ---------------------------------------------------------------------------
# 탭
# ---------------------------------------------------------------------------

tab_by_student, tab_by_exam = st.tabs(["👤 학생별 입력", "📝 시험별 입력"])

# ── 탭 1: 학생별 입력 ──────────────────────────────────────────────────

with tab_by_student:
    st.caption("학생 한 명의 모든 시험 성적을 한 표에서 편집합니다.")

    class_options_s = {c["name"]: c["id"] for c in classes}
    sel_class_name_s = st.selectbox(
        "반", options=list(class_options_s.keys()), key="byS_class"
    )
    students_s = db.get_students(class_id=class_options_s[sel_class_name_s])

    if not students_s:
        st.info("이 반에 학생이 없습니다.")
    else:
        student_options_s = {
            f"{s['name']} ({s.get('school_name') or '-'})": s["id"]
            for s in students_s
        }
        sel_stu_label_s = st.selectbox(
            "학생", options=list(student_options_s.keys()), key="byS_student"
        )
        sel_stu_id = student_options_s[sel_stu_label_s]

        student_scores = db.get_scores_by_student(sel_stu_id)
        score_by_exam_s = {s["exam_id"]: s for s in student_scores}
        cat_map_s = _cat_map_by_score_id(
            db.get_category_scores_for_score_ids(
                [s["id"] for s in student_scores]
            )
        )

        rows_s = []
        for exam in exams:
            existing_score = score_by_exam_s.get(exam["id"])
            cat_values = (
                cat_map_s.get(existing_score["id"], {}) if existing_score else {}
            )
            row = {
                "exam_id": exam["id"],
                "시험명": exam["name"],
                "유형": exam["exam_type"],
                "날짜": str(exam["exam_date"]),
                "총점": existing_score["total_score"] if existing_score else None,
                "등급": existing_score.get("grade") if existing_score else None,
            }
            for cat in categories:
                row[cat["name"]] = cat_values.get(cat["name"])
            rows_s.append(row)

        df_s = pd.DataFrame(rows_s)

        col_config_s = {
            "exam_id": None,
            "시험명": st.column_config.TextColumn("시험명", disabled=True),
            "유형": st.column_config.TextColumn("유형", disabled=True),
            "날짜": st.column_config.TextColumn("날짜", disabled=True),
            "총점": st.column_config.NumberColumn(
                "총점", min_value=0, max_value=100
            ),
            "등급": st.column_config.NumberColumn("등급", min_value=1, max_value=9),
            **_category_column_config(categories),
        }

        edited_s = st.data_editor(
            df_s,
            use_container_width=True,
            hide_index=True,
            column_config=col_config_s,
            key=f"editor_by_student_{sel_stu_id}",
        )

        if st.button("💾 저장", type="primary", key="save_by_student"):
            saved = 0
            errors: list[str] = []
            for _, row in edited_s.iterrows():
                cat_vals = {c["id"]: row.get(c["name"]) for c in categories}
                ok, err = _save_row(
                    student_id=sel_stu_id,
                    exam_id=int(row["exam_id"]),
                    total_score=row["총점"],
                    grade=row["등급"],
                    category_values=cat_vals,
                    label=str(row["시험명"]),
                )
                if ok:
                    saved += 1
                if err:
                    errors.append(err)

            for e in errors:
                st.error(e)
            if saved > 0:
                st.success(f"{saved}개 시험 성적이 저장되었습니다.")


# ── 탭 2: 시험별 입력 ──────────────────────────────────────────────────

with tab_by_exam:
    st.caption("시험 1개를 선택해 반 학생들의 성적을 한 표에서 일괄 편집합니다.")

    class_options_e = {c["name"]: c["id"] for c in classes}
    exam_options_e = {
        f"{e['name']} ({e['exam_type']}, {e['exam_date']})": e["id"] for e in exams
    }

    col_a, col_b = st.columns(2)
    with col_a:
        sel_class_name_e = st.selectbox(
            "반", options=list(class_options_e.keys()), key="byE_class"
        )
    with col_b:
        sel_exam_label_e = st.selectbox(
            "시험", options=list(exam_options_e.keys()), key="byE_exam"
        )
    sel_class_id_e = class_options_e[sel_class_name_e]
    sel_exam_id = exam_options_e[sel_exam_label_e]

    sort_by_school = st.checkbox("학교별 정렬", key="byE_sort")

    students_e = db.get_students(class_id=sel_class_id_e)
    if not students_e:
        st.info("이 반에 학생이 없습니다.")
    else:
        if sort_by_school:
            students_e = sorted(
                students_e,
                key=lambda s: (s.get("school_name") or "", s["name"]),
            )

        exam_scores = db.get_scores_by_exam(sel_exam_id)
        score_by_student_e = {s["student_id"]: s for s in exam_scores}
        cat_map_e = _cat_map_by_score_id(
            db.get_category_scores_for_score_ids(
                [s["id"] for s in exam_scores]
            )
        )

        rows_e = []
        for s in students_e:
            existing_score = score_by_student_e.get(s["id"])
            cat_values = (
                cat_map_e.get(existing_score["id"], {}) if existing_score else {}
            )
            row = {
                "student_id": s["id"],
                "이름": s["name"],
                "학교명": s.get("school_name") or "",
                "총점": existing_score["total_score"] if existing_score else None,
                "등급": existing_score.get("grade") if existing_score else None,
            }
            for cat in categories:
                row[cat["name"]] = cat_values.get(cat["name"])
            rows_e.append(row)

        df_e = pd.DataFrame(rows_e)

        col_config_e = {
            "student_id": None,
            "이름": st.column_config.TextColumn("이름", disabled=True),
            "학교명": st.column_config.TextColumn("학교명", disabled=True),
            "총점": st.column_config.NumberColumn(
                "총점", min_value=0, max_value=100
            ),
            "등급": st.column_config.NumberColumn("등급", min_value=1, max_value=9),
            **_category_column_config(categories),
        }

        edited_e = st.data_editor(
            df_e,
            use_container_width=True,
            hide_index=True,
            column_config=col_config_e,
            key=f"editor_by_exam_{sel_exam_id}_{sel_class_id_e}",
        )

        if st.button("💾 저장", type="primary", key="save_by_exam"):
            saved = 0
            errors: list[str] = []
            for _, row in edited_e.iterrows():
                cat_vals = {c["id"]: row.get(c["name"]) for c in categories}
                ok, err = _save_row(
                    student_id=int(row["student_id"]),
                    exam_id=sel_exam_id,
                    total_score=row["총점"],
                    grade=row["등급"],
                    category_values=cat_vals,
                    label=str(row["이름"]),
                )
                if ok:
                    saved += 1
                if err:
                    errors.append(err)

            for e in errors:
                st.error(e)
            if saved > 0:
                st.success(f"{saved}명의 성적이 저장되었습니다.")
