# views/watchlist_page.py
import streamlit as st
import os
import json
import re
import time

# 定義儲存使用者資料的路徑
USER_DATA_DIR = "./data/users"
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

def get_user_watchlist(username):
    """讀取使用者的追蹤名單與筆記"""
    path = os.path.join(USER_DATA_DIR, f"{username}_watchlist.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 🔄 舊版相容機制：如果讀到舊的 List 格式，自動轉換成含有筆記空字串的 Dict
            if isinstance(data, list):
                return {stock: "" for stock in data}
            return data
    return {} # 現在回傳 Dict 格式

def save_user_watchlist(username, watchlist):
    """儲存使用者的追蹤名單與筆記"""
    path = os.path.join(USER_DATA_DIR, f"{username}_watchlist.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False)

def show_watchlist_page(STOCK_DICT=None):
    st.title("冒險者專屬追蹤名單")

    # 1. 權限檢查：必須登入才能使用
    if not st.session_state.get("logged_in", False):
        st.warning("⚠️ 守衛：「這區是 VIP 專屬！請先前往『登入頁面』出示邀請函。」")
        if st.button("前往登入", key="go_login_from_watchlist"):
            st.query_params["page"] = "login"
            st.rerun()
        return

    username = st.session_state.get("username", "guest")
    watchlist = get_user_watchlist(username)
    MAX_STOCKS = 60 # 🛡️ 設定最大追蹤數量

    # 2. 新增標的區塊
    st.subheader(f"新增追蹤標的 (目前 {len(watchlist)}/{MAX_STOCKS} 檔)")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_stock = st.text_input("請輸入股票代號或名稱 (例如: 2330 或 台積電)", key="new_stock_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("加入追蹤", use_container_width=True):
            if new_stock:
                if len(watchlist) >= MAX_STOCKS:
                    st.error(f"⚠️ 追蹤名單已達 {MAX_STOCKS} 檔上限！為確保系統效能，請先移除部分標的。")
                else:
                    query_clean = new_stock.strip()
                    final_stock_name = query_clean
                    
                    # 透過 STOCK_DICT 尋找完整名稱
                    if STOCK_DICT:
                        if query_clean in STOCK_DICT:
                            final_stock_name = f"{STOCK_DICT[query_clean]['id']} {STOCK_DICT[query_clean]['name']}"
                        else:
                            for k, v in STOCK_DICT.items():
                                if query_clean in k or query_clean == v["id"] or query_clean == v["name"]:
                                    final_stock_name = f"{v['id']} {v['name']}"
                                    break

                    # 檢查是否已經在追蹤名單內
                    if final_stock_name not in watchlist:
                        watchlist[final_stock_name] = "" # 預設筆記為空字串
                        save_user_watchlist(username, watchlist)
                        st.success(f"已將「{final_stock_name}」加入追蹤名單！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info(f"「{final_stock_name}」已經在你的追蹤名單中囉！")

    # 3. 顯示追蹤名單與操作按鈕
    st.markdown("<hr style='border-color: #334155; margin: 10px 0;'>", unsafe_allow_html=True)
    
    if not watchlist:
        st.info("目前還沒有追蹤任何標的，趕快新增一個吧！")
    else:
        # 🗑️ 批次刪除按鈕
        col_space, col_batch_del = st.columns([8, 2])
        with col_batch_del:
            if st.button("🗑️ 刪除已勾選標的", use_container_width=True, type="primary"):
                # 收集被勾選的標的
                to_delete = [s for s in watchlist.keys() if st.session_state.get(f"chk_{s}", False)]
                if to_delete:
                    for s in to_delete:
                        del watchlist[s]
                    save_user_watchlist(username, watchlist)
                    st.success(f"已成功移除 {len(to_delete)} 檔標的！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("請先勾選後方的選取框。")

        # 📋 標題列 (調整比例來填補空白)
        h1, h2, h3, h4, h5 = st.columns([1.5, 4, 1.2, 1, 0.8])
        h1.markdown("<span style='color:#94a3b8;'>標的名稱</span>", unsafe_allow_html=True)
        h2.markdown("<span style='color:#94a3b8;'>專屬筆記</span>", unsafe_allow_html=True)
        h3.markdown("")
        h4.markdown("")
        h5.markdown("<span style='color:#94a3b8; font-size:14px;'>批次選取</span>", unsafe_allow_html=True)

        # 定義儲存筆記的 Callback 函數 (打字按 Enter 即自動存檔)
        def save_note_callback(stock_key):
            watchlist[stock_key] = st.session_state[f"note_{stock_key}"]
            save_user_watchlist(username, watchlist)

        # 🔄 迴圈渲染清單
        for stock, note in list(watchlist.items()):
            # 調整比例：標的(1.5) | 筆記(4) | 顯示資料(1.2) | 單一移除(1) | 勾選框(0.8)
            c1, c2, c3, c4, c5 = st.columns([1.5, 4, 1.2, 1, 0.8])
            
            with c1:
                st.markdown(f"<div style='padding-top:6px; font-weight:bold; font-size:16px;'>{stock}</div>", unsafe_allow_html=True)
            
            with c2:
                # 📝 自訂筆記輸入框
                st.text_input(
                    "筆記", 
                    value=note, 
                    key=f"note_{stock}", 
                    label_visibility="collapsed", 
                    placeholder="點此輸入筆記...",
                    on_change=save_note_callback,
                    args=(stock,) # 傳遞當前標的名稱給 Callback
                )
                
            with c3:
                # 🔍 顯示資料 (結合先前實作的側邊欄連動)
                if st.button(f"🔍 顯示", key=f"view_{stock}", use_container_width=True):
                    st.session_state["selected_watch_stock"] = stock
                    stock_code_match = re.search(r'\d+', stock)
                    if stock_code_match:
                        st.session_state["global_search_final"] = stock_code_match.group()
                    else:
                        st.session_state["global_search_final"] = stock
                    st.rerun()
                    
            with c4:
                # 🗑️ 單一移除
                if st.button(f"移除", key=f"remove_{stock}", use_container_width=True):
                    del watchlist[stock]
                    save_user_watchlist(username, watchlist)
                    # 如果刪除的剛好是正在查看的，清空狀態
                    if st.session_state.get("selected_watch_stock") == stock:
                        st.session_state["selected_watch_stock"] = None
                        st.session_state["global_search_final"] = ""
                    st.rerun()
                    
            with c5:
                # ☑️ 批次選取勾選框
                st.markdown("<div style='padding-top:6px; padding-left:15px;'>", unsafe_allow_html=True)
                st.checkbox("選取", key=f"chk_{stock}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
