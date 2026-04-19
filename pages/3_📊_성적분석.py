"""
pages/3_📊_성적분석.py — 학생별 성적 분석 페이지

기능:
- 반별/학교별 토글로 학생 선택
- 성적 추이 차트 (Plotly, 등급 보조 Y축)
- 최신 시험 분석: 총점 변화, 등급, 반 평균
- 반 내 순위
- 영역별 점수 변화 및 강점/약점
"""

import streamlit as st
import plotly.graph_objects as go
from lib.auth import check_password
from lib import db
from lib.analysis import (
    calc_score_change,
    calc_class_average,
    rank_in_group,
    calc_category_changes,
    find_strengths_weaknesses,
)

if not check_password():
    st.stop()

st.title("📊 성적 분석")

# ---------------------------------------------------------------------------
# 학생 선택 (반별 / 학교별 토글)
# ---------------------------------------------------------------------------

# 다른 페이지에서 학생을 클릭해 넘어온 경우, 전체 학생 목록이 보이는
# '학교별' 뷰로 전환해 preselect 학생을 확실히 찾아낼 수 있게 한다.
preselect_student_id = st.session_state.pop("analysis_preselect_student_id", None)
if preselect_student_id is not None:
    st.session_state["analysis_view_mode"] = "학교별"

view_mode = st.radio(
    "학생 선택 방식",
    options=["반별", "학교별"],
    horizontal=True,
    key="analysis_view_mode",
)

if view_mode == "반별":
    classes = db.get_classes()
    if not classes:
        st.warning("등록된 반이 없습니다. 먼저 학생 관리 페이지에서 반을 추가하세요.")
        st.stop()

    class_options = {cls["name"]: cls["id"] for cls in classes}
    selected_class_name = st.selectbox("반 선택", options=list(class_options.keys()))
    selected_class_id = class_options[selected_class_name]
    students = db.get_students(class_id=selected_class_id)
else:
    students = db.get_students_by_school()

if not students:
    st.info("선택한 조건에 해당하는 학생이 없습니다.")
    st.stop()

student_options = {
    f"{s['name']} ({s.get('school_name') or '학교 미지정'})": s["id"]
    for s in students
}

# preselect가 현재 옵션 안에 존재하면 selectbox의 기본값을 그쪽으로 맞춘다.
if preselect_student_id is not None:
    preselect_label = next(
        (lbl for lbl, sid in student_options.items() if sid == preselect_student_id),
        None,
    )
    if preselect_label:
        st.session_state["analysis_student_select"] = preselect_label

selected_label = st.selectbox(
    "학생 선택",
    options=list(student_options.keys()),
    key="analysis_student_select",
)
selected_student_id = student_options[selected_label]

st.divider()

# ---------------------------------------------------------------------------
# 성적 데이터 로드
# ---------------------------------------------------------------------------

all_scores = db.get_scores_by_student(selected_student_id)

if not all_scores:
    st.info("이 학생의 성적 데이터가 없습니다.")
    st.stop()

# exam_date 기준으로 정렬 (오름차순)
sorted_scores = sorted(all_scores, key=lambda s: s["exams"]["exam_date"])

# ---------------------------------------------------------------------------
# 성적 추이 차트
# ---------------------------------------------------------------------------

st.subheader("성적 추이")

exam_dates = [s["exams"]["exam_date"] for s in sorted_scores]
exam_names = [s["exams"]["name"] for s in sorted_scores]
total_scores = [s["total_score"] for s in sorted_scores]
grades = [s.get("grade") for s in sorted_scores]

has_grades = any(g is not None for g in grades)

fig = go.Figure()

# 총점 라인
fig.add_trace(
    go.Scatter(
        x=exam_dates,
        y=total_scores,
        mode="lines+markers+text",
        name="총점",
        text=[str(sc) for sc in total_scores],
        textposition="top center",
        line=dict(color="#4C72B0", width=2),
        marker=dict(size=8),
        hovertemplate="%{x}<br>총점: %{y}<extra></extra>",
    )
)

if has_grades:
    grade_values = [g if g is not None else None for g in grades]
    fig.add_trace(
        go.Scatter(
            x=exam_dates,
            y=grade_values,
            mode="lines+markers+text",
            name="등급",
            text=[str(g) if g is not None else "" for g in grade_values],
            textposition="bottom center",
            line=dict(color="#DD8452", width=2, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
            yaxis="y2",
            hovertemplate="%{x}<br>등급: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis2=dict(
            title="등급",
            overlaying="y",
            side="right",
            autorange="reversed",
            tickvals=list(range(1, 10)),
            range=[9.5, 0.5],
            showgrid=False,
        )
    )

fig.update_layout(
    xaxis_title="시험 날짜",
    yaxis=dict(title="총점", range=[0, 105]),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400,
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 최신 시험 분석
# ---------------------------------------------------------------------------

st.subheader("최신 시험 분석")

score_change = calc_score_change(all_scores)
latest_score = sorted_scores[-1]
latest_exam = latest_score["exams"]
latest_exam_id = latest_score["exam_id"]

# 반 평균 계산을 위해 같은 시험의 전체 성적 가져오기
class_scores = db.get_scores_by_exam(latest_exam_id)
class_avg = calc_class_average(class_scores)

col1, col2, col3, col4 = st.columns(4)

with col1:
    change_val = score_change["change"]
    delta_str = f"{change_val:+d}" if score_change["previous"] is not None else None
    st.metric(
        label="총점",
        value=score_change["current"],
        delta=delta_str,
    )

with col2:
    grade_display = latest_score.get("grade")
    st.metric(
        label="등급",
        value=f"{grade_display}등급" if grade_display else "미입력",
    )

with col3:
    st.metric(
        label="반 평균",
        value=f"{class_avg:.1f}",
        delta=f"{score_change['current'] - class_avg:+.1f} (평균 대비)",
    )

with col4:
    rank_info = rank_in_group(selected_student_id, class_scores)
    st.metric(
        label="반 순위",
        value=f"{rank_info['rank']} / {rank_info['total']}",
    )

st.caption(
    f"시험: **{latest_exam['name']}** ({latest_exam.get('exam_type', '')}, {latest_exam['exam_date']})"
)

st.divider()

# ---------------------------------------------------------------------------
# 영역별 분석
# ---------------------------------------------------------------------------

st.subheader("영역별 분석")

# 최신 성적의 score_id로 카테고리 점수 조회
latest_score_id = latest_score["id"]
current_cats = db.get_category_scores(latest_score_id)

# 카테고리 이름 정규화 (categories 조인 결과 처리)
def _normalize_cat(raw: list[dict]) -> list[dict]:
    """categories 조인 결과에서 category_name 필드를 표준화한다."""
    normalized = []
    for item in raw:
        name = item.get("category_name") or (
            item["categories"]["name"] if item.get("categories") else "알 수 없음"
        )
        normalized.append({**item, "category_name": name})
    return normalized

current_cats = _normalize_cat(current_cats)

if not current_cats:
    st.info("이 시험의 영역별 점수 데이터가 없습니다.")
else:
    # 이전 시험 카테고리 점수 조회 (있을 경우)
    previous_cats: list[dict] = []
    if len(sorted_scores) >= 2:
        prev_score_id = sorted_scores[-2]["id"]
        previous_cats = _normalize_cat(db.get_category_scores(prev_score_id))

    category_changes = calc_category_changes(current_cats, previous_cats)
    sw = find_strengths_weaknesses(current_cats)

    # 영역별 메트릭 표시
    cat_cols = st.columns(min(len(category_changes), 4))
    for idx, (cat_name, info) in enumerate(category_changes.items()):
        col = cat_cols[idx % len(cat_cols)]
        with col:
            delta_val = None
            if info["previous"] is not None:
                delta_val = f"{info['change']:+d}"
            st.metric(
                label=cat_name,
                value=info["current"],
                delta=delta_val,
            )

    st.divider()

    # 강점 / 약점
    col_str, col_weak = st.columns(2)

    with col_str:
        st.write("**강점 영역**")
        if sw["strengths"]:
            for name in sw["strengths"]:
                st.success(f"✓ {name}")
        else:
            st.info("강점 영역 없음")

    with col_weak:
        st.write("**보완 필요 영역**")
        if sw["weaknesses"]:
            for name in sw["weaknesses"]:
                st.warning(f"△ {name}")
        else:
            st.info("보완 필요 영역 없음")
