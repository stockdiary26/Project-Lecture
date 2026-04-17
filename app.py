import streamlit as st
from lib.auth import check_password
from lib import db

st.set_page_config(
    page_title="국어 성적 관리",
    page_icon="📚",
    layout="wide",
)

if not check_password():
    st.stop()

st.title("🏠 대시보드")

col1, col2, col3 = st.columns(3)

classes = db.get_classes()
students = db.get_students()
exams = db.get_exams()

with col1:
    st.metric("반", f"{len(classes)}개")
with col2:
    st.metric("학생", f"{len(students)}명")
with col3:
    st.metric("시험", f"{len(exams)}회")

if exams:
    latest_exam = exams[0]
    st.subheader(f"📝 최근 시험: {latest_exam['name']}")
    st.write(f"유형: {latest_exam['exam_type']} | 날짜: {latest_exam['exam_date']}")

    scores = db.get_scores_by_exam(latest_exam["id"])
    if scores:
        avg = sum(s["total_score"] for s in scores) / len(scores)
        st.metric("평균 점수", f"{avg:.1f}점")

        consultations = []
        for s in scores:
            cons = db.get_consultations_by_student(s["student_id"])
            exam_cons = [c for c in cons if c.get("exam_id") == latest_exam["id"]]
            if exam_cons:
                consultations.append(s["student_id"])

        remaining = len(scores) - len(consultations)
        if remaining > 0:
            st.warning(f"💬 상담문 미작성 학생: {remaining}명")
        else:
            st.success("✅ 모든 학생 상담문 작성 완료")
    else:
        st.info("아직 점수가 입력되지 않았습니다.")
else:
    st.info("👋 시작하려면 사이드바에서 **학생 관리** → **성적 입력** 순으로 진행하세요.")
    st.markdown("""
    ### 시작 가이드
    1. **⚙️ 설정** — 영역 카테고리를 확인하세요 (기본: 문법, 독해, 문학)
    2. **👩‍🎓 학생 관리** — 반을 만들고 학생을 등록하세요
    3. **📝 성적 입력** — 시험을 생성하고 점수를 입력하세요
    """)
