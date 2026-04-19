"""
pages/1_👩‍🎓_학생관리.py — 반 관리 및 학생 등록/조회 페이지
"""

import io
import pandas as pd
import streamlit as st
from lib.auth import check_password
from lib import db

if not check_password():
    st.stop()

st.title("👩‍🎓 학생 관리")

# ---------------------------------------------------------------------------
# 반(Class) 관리
# ---------------------------------------------------------------------------

st.subheader("반 관리")

classes = db.get_classes()

with st.expander("반 목록 및 관리", expanded=True):
    if classes:
        for cls in classes:
            col_name, col_del = st.columns([5, 1])
            with col_name:
                st.write(cls["name"])
            with col_del:
                if st.button("삭제", key=f"del_class_{cls['id']}"):
                    db.delete_class(cls["id"])
                    st.warning(f"'{cls['name']}' 반이 삭제되었습니다.")
                    st.rerun()
    else:
        st.info("등록된 반이 없습니다.")

    st.write("**새 반 추가**")
    with st.form("add_class_form", clear_on_submit=True):
        new_class_name = st.text_input("반 이름", placeholder="예: 고2 수요반")
        class_submitted = st.form_submit_button("반 추가")

    if class_submitted:
        if new_class_name.strip():
            db.create_class(new_class_name.strip())
            st.success(f"'{new_class_name.strip()}' 반이 추가되었습니다.")
            st.rerun()
        else:
            st.error("반 이름을 입력하세요.")

st.divider()

# ---------------------------------------------------------------------------
# 학생 조회 (반별 / 학교별 토글)
# ---------------------------------------------------------------------------

st.subheader("학생 조회")
st.caption("학생 행을 클릭하면 해당 학생의 성적 분석 페이지로 이동합니다.")


def _navigate_to_analysis(student_id: int) -> None:
    """선택된 학생의 성적 분석 페이지로 이동한다.

    같은 학생이 재선택 상태로 남아 있는 경우 리다이렉트 루프를 피하기 위해
    마지막으로 이동시킨 학생 ID를 기억한다.
    """
    if st.session_state.get("last_nav_student_id") == student_id:
        return
    st.session_state["last_nav_student_id"] = student_id
    st.session_state["analysis_preselect_student_id"] = student_id
    st.switch_page("pages/3_📊_성적분석.py")


view_mode = st.radio(
    "보기 방식",
    options=["반별 보기", "학교별 보기"],
    horizontal=True,
)

if view_mode == "반별 보기":
    classes = db.get_classes()  # refresh after possible add/delete above
    if classes:
        class_options = {cls["name"]: cls["id"] for cls in classes}
        selected_class_name = st.selectbox("반 선택", options=list(class_options.keys()))
        selected_class_id = class_options[selected_class_name]

        students = db.get_students(class_id=selected_class_id)
        if students:
            df = pd.DataFrame(
                [
                    {
                        "이름": s["name"],
                        "학교명": s["school_name"],
                        "반": s["classes"]["name"] if s.get("classes") else "",
                    }
                    for s in students
                ]
            )
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="student_list_by_class",
            )
            if event.selection.rows:
                _navigate_to_analysis(students[event.selection.rows[0]]["id"])
        else:
            st.info("이 반에 등록된 학생이 없습니다.")
    else:
        st.info("먼저 반을 추가하세요.")

else:  # 학교별 보기
    all_students = db.get_students_by_school()
    if all_students:
        # school_name 기준으로 그루핑
        school_groups: dict[str, list] = {}
        for s in all_students:
            school = s.get("school_name") or "미지정"
            school_groups.setdefault(school, []).append(s)

        for school_name, stu_list in school_groups.items():
            st.write(f"**{school_name}** ({len(stu_list)}명)")
            df = pd.DataFrame(
                [
                    {
                        "이름": s["name"],
                        "반": s["classes"]["name"] if s.get("classes") else "",
                    }
                    for s in stu_list
                ]
            )
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key=f"student_list_school_{school_name}",
            )
            if event.selection.rows:
                _navigate_to_analysis(stu_list[event.selection.rows[0]]["id"])
    else:
        st.info("등록된 학생이 없습니다.")

st.divider()

# ---------------------------------------------------------------------------
# 학생 추가 (개별 입력 / CSV 업로드 탭)
# ---------------------------------------------------------------------------

st.subheader("학생 추가")

tab_single, tab_csv = st.tabs(["개별 입력", "CSV 일괄 업로드"])

# --- 개별 입력 ---
with tab_single:
    classes = db.get_classes()
    if not classes:
        st.warning("먼저 반을 추가하세요.")
    else:
        with st.form("add_student_form", clear_on_submit=True):
            class_options_single = {cls["name"]: cls["id"] for cls in classes}
            selected_for_add = st.selectbox(
                "반 선택", options=list(class_options_single.keys())
            )
            student_name = st.text_input("학생 이름")
            student_school = st.text_input("학교명")
            student_submitted = st.form_submit_button("학생 추가")

        if student_submitted:
            if student_name.strip() and student_school.strip():
                db.create_student(
                    class_id=class_options_single[selected_for_add],
                    name=student_name.strip(),
                    school_name=student_school.strip(),
                )
                st.success(f"'{student_name.strip()}' 학생이 추가되었습니다.")
                st.rerun()
            else:
                st.error("이름과 학교명을 모두 입력하세요.")

# --- CSV 일괄 업로드 ---
with tab_csv:
    st.write("CSV 파일 형식: **이름,학교명** (헤더 포함)")
    st.caption("예시:\n```\n이름,학교명\n홍길동,서울중학교\n김영희,부산고등학교\n```")

    classes = db.get_classes()
    if not classes:
        st.warning("먼저 반을 추가하세요.")
    else:
        class_options_csv = {cls["name"]: cls["id"] for cls in classes}
        csv_target_class = st.selectbox(
            "업로드 대상 반",
            options=list(class_options_csv.keys()),
            key="csv_class_select",
        )

        uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"])

        if uploaded_file is not None:
            try:
                df_csv = pd.read_csv(uploaded_file)

                # 컬럼명 정규화
                df_csv.columns = df_csv.columns.str.strip()

                if "이름" not in df_csv.columns or "학교명" not in df_csv.columns:
                    st.error("CSV 파일에 '이름' 과 '학교명' 컬럼이 필요합니다.")
                else:
                    df_preview = df_csv[["이름", "학교명"]].dropna()
                    st.write(f"미리보기 ({len(df_preview)}명)")
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)

                    if st.button("일괄 등록"):
                        target_class_id = class_options_csv[csv_target_class]
                        rows = [
                            {
                                "class_id": target_class_id,
                                "name": str(row["이름"]).strip(),
                                "school_name": str(row["학교명"]).strip(),
                            }
                            for _, row in df_preview.iterrows()
                            if str(row["이름"]).strip()
                        ]
                        if rows:
                            db.bulk_create_students(rows)
                            st.success(f"{len(rows)}명의 학생이 등록되었습니다.")
                            st.rerun()
                        else:
                            st.error("등록할 유효한 학생 데이터가 없습니다.")
            except Exception as e:
                st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")

st.divider()

# ---------------------------------------------------------------------------
# 학생 삭제
# ---------------------------------------------------------------------------

st.subheader("🗑️ 학생 삭제")
st.caption(
    "학생을 삭제하면 해당 학생의 성적·영역별 점수·상담문·메모도 함께 삭제됩니다. "
    "되돌릴 수 없으니 신중히 진행하세요."
)

classes = db.get_classes()
if not classes:
    st.info("먼저 반을 추가하세요.")
else:
    class_options_del = {cls["name"]: cls["id"] for cls in classes}
    del_class_name = st.selectbox(
        "반 선택",
        options=list(class_options_del.keys()),
        key="del_class_select",
    )
    students_del = db.get_students(class_id=class_options_del[del_class_name])

    if not students_del:
        st.info("이 반에 등록된 학생이 없습니다.")
    else:
        student_options_del = {
            f"{s['name']} ({s.get('school_name') or '-'})": s["id"]
            for s in students_del
        }
        del_student_label = st.selectbox(
            "삭제할 학생",
            options=list(student_options_del.keys()),
            key="del_student_select",
        )
        del_student_id = student_options_del[del_student_label]

        confirm_for = st.session_state.get("delete_student_confirm_for")

        if confirm_for == del_student_id:
            st.warning(
                f"**'{del_student_label}'** 학생과 관련 데이터가 모두 삭제됩니다. "
                "정말 삭제하시겠습니까?"
            )
            col_yes, col_no = st.columns([1, 1])
            with col_yes:
                if st.button("✅ 정말 삭제", type="primary", key="confirm_del_student"):
                    db.delete_student(del_student_id)
                    st.session_state["delete_student_confirm_for"] = None
                    st.success(f"'{del_student_label}' 학생이 삭제되었습니다.")
                    st.rerun()
            with col_no:
                if st.button("취소", key="cancel_del_student"):
                    st.session_state["delete_student_confirm_for"] = None
                    st.rerun()
        else:
            if st.button("🗑️ 학생 삭제", key="request_del_student"):
                st.session_state["delete_student_confirm_for"] = del_student_id
                st.rerun()
