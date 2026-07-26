import streamlit as st


def show_login_page():

    st.title("🎉 股市派對")

    st.subheader("登入")

    username = st.text_input("帳號")

    password = st.text_input(
        "密碼",
        type="password"
    )

    if st.button("登入"):

        if username == "admin" and password == "123456":

            st.session_state.logged_in = True

            st.query_params["page"] = "b1"

            st.rerun()

        else:

            st.error("帳號或密碼錯誤")
