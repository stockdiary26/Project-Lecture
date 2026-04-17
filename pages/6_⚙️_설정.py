"""
pages/6_⚙️_설정.py — 카테고리(채점 영역) 관리 페이지
"""

import streamlit as st
from lib.auth import check_password
from lib import db

if not check_password():
    st.stop()

st.title("⚙️ 설정")
st.subheader("채점 영역 카테고리 관리")

# ---------------------------------------------------------------------------
# 현재 카테고리 목록
# ---------------------------------------------------------------------------

categories = db.get_categories()

if categories:
    st.write("**현재 카테고리 목록**")
    for cat in categories:
        col_name, col_order, col_save, col_del = st.columns([3, 1, 1, 1])

        with col_name:
            new_name = st.text_input(
                "카테고리명",
                value=cat["name"],
                key=f"name_{cat['id']}",
                label_visibility="collapsed",
            )
        with col_order:
            st.text(f"순서 {cat['sort_order']}")
        with col_save:
            if st.button("저장", key=f"save_{cat['id']}"):
                if new_name.strip():
                    db.update_category(cat["id"], name=new_name.strip())
                    st.success(f"'{new_name.strip()}' 으로 저장했습니다.")
                    st.rerun()
                else:
                    st.error("카테고리명을 입력하세요.")
        with col_del:
            if st.button("삭제", key=f"del_{cat['id']}"):
                db.delete_category(cat["id"])
                st.warning(f"'{cat['name']}' 카테고리가 삭제되었습니다.")
                st.rerun()
else:
    st.info("등록된 카테고리가 없습니다. 아래에서 추가하세요.")

st.divider()

# ---------------------------------------------------------------------------
# 새 카테고리 추가
# ---------------------------------------------------------------------------

st.write("**새 카테고리 추가**")
with st.form("add_category_form", clear_on_submit=True):
    col_new_name, col_new_order = st.columns([3, 1])
    with col_new_name:
        new_cat_name = st.text_input("카테고리명", placeholder="예: 문법, 독해, 문학")
    with col_new_order:
        next_order = max((c["sort_order"] for c in categories), default=0) + 1
        new_sort_order = st.number_input(
            "정렬 순서",
            min_value=1,
            value=next_order,
        )
    submitted = st.form_submit_button("추가")

if submitted:
    if new_cat_name.strip():
        db.create_category(new_cat_name.strip(), int(new_sort_order))
        st.success(f"'{new_cat_name.strip()}' 카테고리가 추가되었습니다.")
        st.rerun()
    else:
        st.error("카테고리명을 입력하세요.")
