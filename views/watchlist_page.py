# views/watchlist_page.py
import streamlit as st
import os
import json
import re

# 定義儲存使用者資料的路徑
USER_DATA_DIR = "./data/users"
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

def get_user_watchlist(username):
    """讀取使用者的追蹤名單"""
    path = os.path.join(USER_DATA_DIR, f"{username}_watchlist.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_user_watchlist(username, watchlist):
    """儲存使用者的追蹤名單"""
    path = os.path.join(USER_DATA_DIR, f"{username}_watchlist.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False)

def show_watchlist_page(STOCK_DICT=None):
    st.title("🌟 冒險者專屬追蹤名單")

    # 1. 權限檢查：必須登入才能使用
    if not st.session_state.get("logged_in", False):
        st.warning("⚠️ 守衛：「這區是 VIP 專屬！請先前往『登入頁面』出示邀請函。」")
        if st.button("前往登入", key="go_login_from_watchlist"):
            st.query_params["page"] = "login"
            st.rerun()
        return

    username = st.session_state.get("username", "guest")
    watchlist = get_user_watchlist(username)

    # 2. 新增標的區塊
    st.subheader("➕ 新增追蹤標的")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_stock = st.text_input("請輸入股票代號 (例如: 2330 或 2330台積電)", key="new_stock_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("加入追蹤", use_container_width=True):
            if new_stock:
                if new_stock not in watchlist:
                    watchlist.append(new_stock)
                    save_user_watchlist(username, watchlist)
                    st.success(f"已將「{new_stock}」加入追蹤名單！")
                    time.sleep(1) # 給點時間顯示成功訊息
                    st.rerun()
                else:
                    st.info("該標的已經在你的追蹤名單中囉！")

    st.divider()

    # 3. 顯示追蹤名單與操作按鈕
    st.subheader("📋 目前追蹤名單")
    if not watchlist:
        st.info("目前還沒有追蹤任何標的，趕快新增一個吧！")
    else:
        for stock in watchlist:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"#### {stock}")
            with c2:
                # 點擊後，將選中的標的寫入 session_state 給側邊欄讀取
                if st.button(f"🔍 顯示資料", key=f"view_{stock}"):
                    st.session_state["selected_watch_stock"] = stock
                    st.rerun()
            with c3:
                # 刪除功能
                if st.button(f"🗑️ 移除", key=f"remove_{stock}"):
                    watchlist.remove(stock)
                    save_user_watchlist(username, watchlist)
                    # 如果刪除的剛好是正在查看的，則清空側邊欄狀態
                    if st.session_state.get("selected_watch_stock") == stock:
                        st.session_state["selected_watch_stock"] = None
                    st.rerun()
