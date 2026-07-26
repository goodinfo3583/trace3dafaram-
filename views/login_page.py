# views/login_page.py
import streamlit as st
import time

def show_login_page():
    st.title("🔐 VIP 驗證中心")

    if st.session_state.get("logged_in", False):
        st.success(f"🎉 歡迎回來，{st.session_state['username']}！您已解鎖最高權限。")
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.query_params["page"] = "b1"
            st.rerun()
        return

    st.markdown("### 請輸入您的邀請函憑證")
    with st.form("login_form"):
        username = st.text_input("👤 帳號 (Username)")
        password = st.text_input("🔑 密碼 (Password)", type="password")
        submit = st.form_submit_button("進入包廂", use_container_width=True)

        if submit:
            try:
                valid_passwords = st.secrets["passwords"]
                if username in valid_passwords and valid_passwords[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.success("驗證成功！正在為您開啟專屬通道...")
                    time.sleep(1)
                    # 登入成功後，直接帶回剛剛被擋下的 B6 頁面
                    st.query_params["page"] = "b6"
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，請重新確認！")
            except KeyError:
                st.error("⚠️ 系統尚未設定密碼保險箱 (secrets.toml)。")
