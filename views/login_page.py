# views/login_page.py
import streamlit as st
import time
import os

def show_login_page():
    st.title("🔐 VIP 驗證中心")

    # 狀態 1：已經登入 -> 顯示解鎖畫面與登出按鈕
    if st.session_state.get("logged_in", False):
        st.success(f"🎉 歡迎回來，{st.session_state['username']}！您已解鎖最高權限。")
        st.markdown("如果您想結束這次的探索，請點擊下方按鈕登出：")
        
        # 這裡就是你原本找不到的登出按鈕 (點擊導覽列的 VIP中心 就會看到)
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.query_params["page"] = "b1"
            st.rerun()
        return

    # 狀態 2：尚未登入 -> NPC 守衛登場！
    st.markdown("<br>", unsafe_allow_html=True) # 空一行讓畫面呼吸
    
    # 使用欄位排版：左邊 NPC 圖片 (佔比 1)，右邊對話框 (佔比 2)
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 讀取你的 NPC 圖片
        npc_path = "./static/npc_guard1.png"
        if os.path.exists(npc_path):
            st.image(npc_path, use_container_width=True)
        else:
            # 如果路徑錯誤或找不到圖片，會顯示這個提示，方便你除錯
            st.warning(f"找不到圖片: {npc_path}")
            
    with col2:
        # 使用 HTML 畫一個遊戲感的對話框 (加入 margin-bottom: 20px 增加與下方表單的間距)
        st.markdown("""
        <div style='background-color: rgba(17, 22, 34, 0.8); padding: 20px; border-radius: 10px; border: 1px solid #38BDF8; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); margin-bottom: 20px;'>
            <h3 style='color: #FFD700; margin-top: 0;'>🛡️ 親愛的冒險者：</h3>
            <p style='color: #E2E8F0; font-size: 18px; line-height: 1.6;'>
                「前方是VIP專屬領域，請先出示你的 <b>邀請函序號</b> ！」
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 👇 關鍵修改：將登入表單縮排，放在 col2 裡面，就會出現在對話框正下方
        with st.form("login_form"):
            username = st.text_input("👤 帳號 (Username)")
            password = st.text_input("🔑 密碼 (Password)", type="password")
            submit = st.form_submit_button("遞交邀請函", use_container_width=True)

            if submit:
                try:
                    valid_passwords = st.secrets["passwords"]
                    if username in valid_passwords and valid_passwords[username] == password:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.success("「驗證成功！大門已開啟，請進...」")
                        time.sleep(1.5)
                        
                        # 登入成功後跳轉至 B6
                        st.query_params["page"] = "b6"
                        st.rerun()
                    else:
                        st.error("❌ 守衛：「這張邀請函是假的！請重新確認！」")
                except KeyError:
                    st.error("⚠️ 系統尚未設定密碼保險箱 (secrets.toml)。請先完成設定。")
