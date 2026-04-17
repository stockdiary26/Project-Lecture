"""
pages/4_💬_상담문생성.py — AI 상담문 생성 페이지

기능:
- 반 + 시험 선택
- 학생 선택
- 기존 상담문이 있으면: 편집 + 저장 / 재생성
- 없으면: 상담문 생성 버튼 → AI 생성 → DB 저장
- 상담문 히스토리 (expander)
"""

import streamlit as st
from lib.auth import check_password
from lib import db
from lib.ai import generate_consultation

if not check_password():
    st.stop()

st.title("💬 상담문 생성")

# ---------------------------------------------------------------------------
# 반 선택
# ---------------------------------------------------------------------------

classes = db.get_classes()
if not classes:
    st.warning("등록된 반이 없습니다. 먼저 학생 관리 페이지에서 반을 추가하세요.")
    st.stop()

class_options = {cls["name"]: cls["id"] for cls in classes}
selected_class_name = st.selectbox("반 선택", options=list(class_options.keys()))
selected_class_id = class_options[selected_class_name]

# ---------------------------------------------------------------------------
# 시험 선택
# ---------------------------------------------------------------------------

exams = db.get_exams()
if not exams:
    st.warning("등록된 시험이 없습니다. 먼저 성적 입력 페이지에서 시험을 생성하세요.")
    st.stop()

exam_options = {
    f"{e['name']} ({e['exam_type']}, {e['exam_date']})": e["id"] for e in exams
}
selected_exam_label = st.selectbox("시험 선택", options=list(exam_options.keys()))
selected_exam_id = exam_options[selected_exam_label]

# ---------------------------------------------------------------------------
# 학생 선택
# ---------------------------------------------------------------------------

students = db.get_students(class_id=selected_class_id)
if not students:
    st.info("이 반에 등록된 학생이 없습니다.")
    st.stop()

student_options = {
    f"{s['name']} ({s.get('school_name') or '학교 미지정'})": s["id"]
    for s in students
}
selected_label = st.selectbox("학생 선택", options=list(student_options.keys()))
selected_student_id = student_options[selected_label]

st.divider()

# ---------------------------------------------------------------------------
# 기존 상담문 확인
# ---------------------------------------------------------------------------

consultations = db.get_consultations_by_student(selected_student_id)
existing = next(
    (c for c in consultations if c["exam_id"] == selected_exam_id), None
)

if existing:
    st.subheader("상담문 편집")
    st.caption("이미 생성된 상담문이 있습니다. 내용을 수정하거나 저장할 수 있습니다.")

    edited_text = st.text_area(
        "상담문",
        value=existing.get("final_text") or existing.get("ai_draft") or "",
        height=300,
        key="edit_consultation_text",
    )

    col_save, col_regen = st.columns([1, 1])

    with col_save:
        if st.button("💾 저장", type="primary", use_container_width=True):
            db.update_consultation(existing["id"], edited_text)
            st.success("상담문이 저장되었습니다.")
            st.rerun()

    with col_regen:
        if st.button("🔄 재생성", use_container_width=True):
            with st.spinner("AI가 상담문을 생성하고 있습니다..."):
                try:
                    new_text = generate_consultation(selected_student_id, selected_exam_id)
                    db.update_consultation(existing["id"], new_text)
                    st.success("상담문이 재생성되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error("상담문 생성에 실패했습니다.")
                    st.warning(
                        "인터넷 연결 상태와 API 키 설정을 확인해 주세요.\n\n"
                        f"오류 내용: {e}"
                    )

else:
    st.subheader("상담문 생성")

    # 해당 시험 성적 존재 여부 확인
    exam_scores = db.get_scores_by_exam(selected_exam_id)
    student_score = next(
        (s for s in exam_scores if s["student_id"] == selected_student_id), None
    )

    if not student_score:
        st.warning(
            "이 학생의 해당 시험 성적이 없습니다. "
            "먼저 성적 입력 페이지에서 성적을 입력해 주세요."
        )
    else:
        if st.button("✨ 상담문 생성", type="primary"):
            with st.spinner("AI가 상담문을 생성하고 있습니다..."):
                try:
                    ai_text = generate_consultation(selected_student_id, selected_exam_id)
                    db.create_consultation(
                        student_id=selected_student_id,
                        exam_id=selected_exam_id,
                        ai_draft=ai_text,
                        final_text=ai_text,
                    )
                    st.success("상담문이 생성되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error("상담문 생성에 실패했습니다.")
                    st.warning(
                        "인터넷 연결 상태와 API 키 설정을 확인해 주세요.\n\n"
                        f"오류 내용: {e}"
                    )

# ---------------------------------------------------------------------------
# 상담문 히스토리
# ---------------------------------------------------------------------------

st.divider()
st.subheader("상담 히스토리")

if not consultations:
    st.info("이 학생의 상담 기록이 없습니다.")
else:
    for consultation in consultations:
        exam_info = consultation.get("exams") or {}
        exam_name = exam_info.get("name", "알 수 없음")
        exam_date = exam_info.get("exam_date", "")
        created_at = consultation.get("created_at", "")[:10]
        is_current = consultation["exam_id"] == selected_exam_id

        label = f"{'[현재] ' if is_current else ''}{exam_name} ({exam_date}) — 작성일: {created_at}"

        with st.expander(label, expanded=is_current):
            display_text = (
                consultation.get("final_text") or consultation.get("ai_draft") or ""
            )
            st.text_area(
                "상담문 내용",
                value=display_text,
                height=200,
                disabled=True,
                key=f"history_{consultation['id']}",
            )
