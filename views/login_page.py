# views/login_page.py
import streamlit as st
import time
import os
import pandas as pd
import datetime

def show_login_page(conn=None, SHEET_URL=None):
    # ==========================================
    # 狀態 1：已經登入 -> 顯示解鎖畫面與登出按鈕
    # ==========================================
    if st.session_state.get("logged_in", False):
        # 如果有紀錄性別，可以在這裡加點巧思，但先預設顯示名字
        st.success(f"歡迎回來，{st.session_state['username']}！您已解鎖最高權限。")
        st.markdown("如果您想結束這次的探索，請點擊下方按鈕登出：")
        
        if st.button("登出系統", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.query_params["page"] = "b1"
            st.rerun()
        return

    # ==========================================
    # 狀態 2：尚未登入 -> NPC 守衛登場！
    # ==========================================
    st.markdown("<br>", unsafe_allow_html=True) 
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        npc_path = "./static/npc_guard1.png"
        if os.path.exists(npc_path):
            st.image(npc_path, use_container_width=True)
        else:
            st.warning(f"找不到圖片: {npc_path}")
            
    with col2:
        # 提示文字加入 /M 與 /F
        st.markdown("""
        <div style='background-color: rgba(17, 22, 34, 0.8); padding: 20px; border-radius: 10px; border: 1px solid #38BDF8; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); margin-bottom: 20px;'>
            <h3 style='color: #FFD700; margin-top: 0;'>親愛的冒險者：</h3>
            <p style='color: #E2E8F0; font-size: 18px; line-height: 1.6;'>
                「請出示你的 <b>邀請函序號</b> ！」<br>
                <span style='font-size: 14px; color: #A0AEC0;'>*(守衛悄悄說：如果是新來的，在名字後面加上 <b>/M (男)</b> 或 <b>/F (女)</b> 並輸入密碼，我就會幫你自動造冊...)*</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            raw_username = st.text_input("帳號 (Username)")
            raw_password = st.text_input("密碼 (Password)", type="password")
            submit = st.form_submit_button("遞交邀請函", use_container_width=True)

            if submit:
                clean_user = raw_username.strip()
                clean_pass = raw_password.strip()
                
                if not clean_user or not clean_pass:
                    st.error("守衛：「名字跟密碼都要寫啊，不然我怎麼認人！」")
                else:
                    # 把輸入的帳號轉小寫來判斷後綴，讓玩家打 /M, /m, /F, /f 都會通
                    lower_user = clean_user.lower()
                    
                    # ==========================================
                    # 🌟 邏輯分流 A：RO 私服式註冊模式 (/M 或 /F)
                    # ==========================================
                    if lower_user.endswith("/m") or lower_user.endswith("/f"):
                        
                        # 擷取最後一個字母轉大寫，當作性別 (M 或 F)
                        gender_code = clean_user[-1].upper() 
                        
                        # 把 "/m" 或 "/f" 切掉，取得真正的帳號名稱
                        real_user = clean_user[:-2].strip()
                        
                        if not real_user:
                            st.error(f"守衛：「別鬧了，/{gender_code} 前面要寫上你的名字啊！」")
                        elif not conn or not SHEET_URL:
                            st.error("⚠️ 系統尚未連線至資料庫，無法造冊。")
                        else:
                            with st.spinner("守衛正在翻閱會員名冊..."):
                                try:
                                    # 1. 檢查是否冒充站長
                                    valid_passwords = st.secrets.get("passwords", {})
                                    if real_user in valid_passwords:
                                        st.error("守衛：「大膽！這可是站長的名號，不准冒用！」")
                                        st.stop()
                                        
                                    # 2. 讀取 Google Sheets 檢查是否重複註冊
                                    try:
                                        current_users = conn.read(spreadsheet=SHEET_URL, worksheet="會員名冊", ttl=0)
                                        is_exist = False
                                        if not current_users.empty and '帳號' in current_users.columns:
                                            if real_user in current_users['帳號'].astype(str).values:
                                                is_exist = True
                                    except:
                                        current_users = pd.DataFrame()
                                        is_exist = False
                                    
                                    if is_exist:
                                        st.error(f"守衛：「『{real_user}』這個名字已經有人用了，換一個吧！」")
                                    else:
                                        # 3. 寫入新帳號，加入「性別」欄位
                                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        new_data = pd.DataFrame([{
                                            "帳號": real_user,
                                            "密碼": clean_pass,
                                            "性別": gender_code,  # 🌟 新增性別紀錄
                                            "註冊時間": now_str
                                        }])
                                        
                                        if current_users.empty:
                                            final_users = new_data
                                        else:
                                            final_users = pd.concat([current_users, new_data], ignore_index=True)
                                            
                                        conn.update(spreadsheet=SHEET_URL, worksheet="會員名冊", data=final_users)
                                        
                                        gender_title = "男冒險者" if gender_code == "M" else "女冒險者"
                                        st.success(f"🎉 註冊成功！守衛已經將 {gender_title}『{real_user}』記錄下來。請刪除帳號後面的 /{gender_code} 重新登入！")
                                except Exception as e:
                                    st.error(f"❌ 造冊失敗，發生了未知的魔法干擾：{e}")

                    # ==========================================
                    # 🌟 邏輯分流 B：正常登入模式
                    # ==========================================
                    else:
                        login_success = False
                        
                        # 1. 先查 Secrets 保險箱
                        try:
                            valid_passwords = st.secrets.get("passwords", {})
                            if clean_user in valid_passwords and str(valid_passwords[clean_user]) == clean_pass:
                                login_success = True
                        except:
                            pass
                            
                        # 2. 去 Google Sheets 查「會員名冊」
                        if not login_success and conn and SHEET_URL:
                            try:
                                user_df = conn.read(spreadsheet=SHEET_URL, worksheet="會員名冊", ttl=0)
                                if not user_df.empty and '帳號' in user_df.columns and '密碼' in user_df.columns:
                                    match = user_df[(user_df['帳號'].astype(str) == clean_user) & 
                                                    (user_df['密碼'].astype(str) == clean_pass)]
                                    if not match.empty:
                                        login_success = True
                            except Exception as e:
                                st.warning(f"⚠️ 無法連線至會員資料庫：{e}")

                        # 處理登入結果
                        if login_success:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = clean_user
                            st.success("「驗證成功！大門已開啟，請進...」")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("守衛：「這張邀請函是假的，或者密碼錯誤！請重新確認！」")
