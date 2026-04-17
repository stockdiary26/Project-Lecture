import streamlit as st


def check_password() -> bool:
    """비밀번호 인증. 통과하면 True 반환."""
    if st.session_state.get("authenticated"):
        return True

    st.title("🔐 로그인")
    password = st.text_input("비밀번호를 입력하세요", type="password")

    if st.button("로그인"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

    return False
