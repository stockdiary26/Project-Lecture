import streamlit as st
from lib.auth import check_password
from lib import db

if not check_password():
    st.stop()

st.title("📋 메모")

classes = db.get_classes()
if not classes:
    st.warning("먼저 반과 학생을 등록해주세요.")
    st.stop()

selected_class = st.selectbox("반", classes, format_func=lambda c: c["name"])
students = db.get_students(selected_class["id"])

if not students:
    st.info("이 반에 학생이 없습니다.")
    st.stop()

selected_student = st.selectbox(
    "학생", students,
    format_func=lambda s: f"{s['name']} ({s.get('school_name') or ''})"
)

st.subheader("✏️ 새 메모")
with st.form("add_memo"):
    content = st.text_area(
        "내용",
        placeholder="상담 후 특이사항, 학부모 요청, 학생 상태 변화 등",
        height=100,
    )
    if st.form_submit_button("메모 저장"):
        if content.strip():
            db.create_memo(selected_student["id"], content.strip())
            st.rerun()
        else:
            st.error("내용을 입력해주세요.")

st.divider()
st.subheader("📜 메모 이력")

memos = db.get_memos_by_student(selected_student["id"])

if memos:
    editing_memo_id = st.session_state.get("editing_memo_id")

    for memo in memos:
        is_editing = editing_memo_id == memo["id"]

        if is_editing:
            st.markdown(f"**{memo['created_at'][:10]}** — 수정 중")
            new_content = st.text_area(
                "내용 수정",
                value=memo["content"],
                key=f"edit_memo_text_{memo['id']}",
                height=100,
                label_visibility="collapsed",
            )
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button(
                    "💾 저장",
                    type="primary",
                    key=f"save_memo_{memo['id']}",
                    use_container_width=True,
                ):
                    if new_content.strip():
                        db.update_memo(memo["id"], new_content.strip())
                        st.session_state["editing_memo_id"] = None
                        st.rerun()
                    else:
                        st.error("내용을 입력해주세요.")
            with col_cancel:
                if st.button(
                    "취소",
                    key=f"cancel_memo_{memo['id']}",
                    use_container_width=True,
                ):
                    st.session_state["editing_memo_id"] = None
                    st.rerun()
        else:
            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                st.markdown(f"**{memo['created_at'][:10]}**")
                st.write(memo["content"])
            with col2:
                if st.button("✏️", key=f"edit_memo_{memo['id']}", help="수정"):
                    st.session_state["editing_memo_id"] = memo["id"]
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_memo_{memo['id']}", help="삭제"):
                    db.delete_memo(memo["id"])
                    if editing_memo_id == memo["id"]:
                        st.session_state["editing_memo_id"] = None
                    st.rerun()
        st.divider()
else:
    st.info("이 학생에 대한 메모가 없습니다.")
