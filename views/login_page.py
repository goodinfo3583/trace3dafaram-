import streamlit as st
import time

def show_login_page():
    # 呈現不同的標題 (可依照你的派對風格設計)
    st.title("🔐 VIP 驗證中心")

    # 狀態 1：已經登入 -> 顯示登出畫面
    if st.session_state["logged_in"]:
        st.success(f"🎉 歡迎回來，{st.session_state['username']}！您已擁有最高存取權限。")
        
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.success("已成功登出系統，正在為您引導至大廳...")
            time.sleep(1)
            st.query_params["page"] = "b1"  # 登出後導回首頁 b1
            st.rerun()
        return  # 提前結束函式，不顯示下方的登入表單

    # 狀態 2：尚未登入 -> 顯示登入表單
    st.markdown("### 請輸入您的邀請函憑證")
    with st.form("login_form"):
        username = st.text_input("👤 帳號 (Username)")
        password = st.text_input("🔑 密碼 (Password)", type="password") # 隱藏密碼輸入
        submit = st.form_submit_button("進入包廂", use_container_width=True)

        if submit:
            # 讀取 secrets.toml 中的密碼進行比對
            try:
                valid_passwords = st.secrets["passwords"]
                # 驗證帳號是否存在，且密碼是否正確
                if username in valid_passwords and valid_passwords[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.success("驗證成功！正在開啟專屬通道...")
                    time.sleep(1)
                    
                    # 登入成功後，把使用者帶往想去的包廂 (例如觀察名單 pool)
                    st.query_params["page"] = "pool"
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，請重新確認！")
            except KeyError:
                st.error("⚠️ 系統尚未設定密碼保險箱 (secrets.toml)，請聯絡管理員。")
