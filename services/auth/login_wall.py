import streamlit as st
from services.persistence.exercise_repository import get_or_create_user
def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True
    st.title("🏋🏻AI Real-time GYM COACH")
    st.markdown("### Welcome! Please enter your username to start")
    with st.form("login form",clear_on_submit=False):
        username = st.text_input("Name(unique)",placeholder="Unique name e.g. vruttipatel")
        submit_button= st.form_submit_button("Start Session ",width= "stretch")

    if submit_button:
        if not username:
            st.error("name cannot be empty")
            return False
        user = get_or_create_user(username)

        st.session_state["user_id"]=user["id"]
        st.session_state["username"]=user["username"]

        st.rerun()

    return False