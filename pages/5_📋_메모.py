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
    format_func=lambda s: f"{s['name']} ({s['school_name']})"
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
    for memo in memos:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{memo['created_at'][:10]}**")
            st.write(memo["content"])
        with col2:
            if st.button("🗑️", key=f"del_memo_{memo['id']}"):
                db.delete_memo(memo["id"])
                st.rerun()
        st.divider()
else:
    st.info("이 학생에 대한 메모가 없습니다.")
