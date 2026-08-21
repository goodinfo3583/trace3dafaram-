# views/watchlist_page.py
import streamlit as st
import json
import re
import time
import pandas as pd
import os
# 定義儲存使用者資料的路徑
USER_DATA_DIR = "./data/users"
os.makedirs(USER_DATA_DIR, exist_ok=True)
# ==========================================
# 💾 資料庫存取 (Google Sheets 正式連線版)
# ==========================================
def get_user_watchlist(username, conn, SHEET_URL):
    """從 GS 讀取使用者的追蹤名單與筆記"""
    if not conn or not SHEET_URL:
        return {}
        
    try:
        # 1. 讀取整張「會員名冊」
        df = conn.read(spreadsheet=SHEET_URL, worksheet="會員名冊", ttl=0)
        
        if df.empty or '帳號' not in df.columns or 'Watchlist' not in df.columns:
            return {}
            
        # 2. 清理帳號格式 (轉字串、去小數點、去空白、轉小寫) 確保能精準比對
        clean_accounts = df['帳號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
        target_user = str(username).strip().lower()
        
        # 3. 找出該名冒險者的資料列
        match = df[clean_accounts == target_user]
        
        if not match.empty:
            gs_watchlist_str = match.iloc[0]['Watchlist']
            # 如果欄位有內容且不是空值 (NaN)
            if pd.notna(gs_watchlist_str) and str(gs_watchlist_str).strip() != "":
                data = json.loads(str(gs_watchlist_str))
                # 相容舊版陣列轉換
                if isinstance(data, list): 
                    return {stock: "" for stock in data}
                return data
                
    except Exception as e:
        pass
        
    return {}

def save_user_watchlist(username, watchlist, conn, SHEET_URL):
    """將使用者的追蹤名單與筆記存回 GS"""
    if not conn or not SHEET_URL:
        st.error("⚠️ 無法連線至資料庫，無法存檔。")
        return
        
    try:
        # 1. 將字典轉為純文字 JSON 字串
        watchlist_str = json.dumps(watchlist, ensure_ascii=False)
        
        # 2. 讀取目前的「會員名冊」
        df = conn.read(spreadsheet=SHEET_URL, worksheet="會員名冊", ttl=0)
        
        if df.empty or '帳號' not in df.columns:
            return
            
        # 確保有 Watchlist 欄位 (防呆機制)
        if 'Watchlist' not in df.columns:
            df['Watchlist'] = ""
            
        # 🌟 關鍵修復：強制將欄位轉為 object 型態，這樣就能允許寫入字串！
        df['Watchlist'] = df['Watchlist'].astype(object)
            
        # 3. 尋找對應的帳號列
        clean_accounts = df['帳號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
        target_user = str(username).strip().lower()
        
        idx = df[clean_accounts == target_user].index
        
        if len(idx) > 0:
            # 4. 覆寫該列的 Watchlist 欄位
            df.at[idx[0], 'Watchlist'] = watchlist_str
            # 5. 上傳更新回 Google Sheets
            conn.update(spreadsheet=SHEET_URL, worksheet="會員名冊", data=df)
            
    except Exception as e:
        st.error(f"❌ 同步至雲端失敗: {e}")

# ==========================================
# 🚀 高效能批次報價引擎
# ==========================================
@st.cache_data(ttl=300)
def get_watchlist_quotes(stock_codes):
    """批次向 Yahoo Finance 請求報價，並濾除盤中空值雜訊"""
    import yfinance as yf
    if not stock_codes: return {}
    
    tickers = [f"{c}.TW" for c in stock_codes] + [f"{c}.TWO" for c in stock_codes]
    try:
        df = yf.download(tickers, period="5d", progress=False)
    except:
        return {}
        
    quotes = {}
    if df.empty: return quotes
    
    if isinstance(df.columns, pd.MultiIndex):
        close_df = df['Close'] if 'Close' in df.columns else pd.DataFrame()
        vol_df = df['Volume'] if 'Volume' in df.columns else pd.DataFrame()
    else:
        close_df = pd.DataFrame({tickers[0]: df['Close']}) if 'Close' in df.columns else pd.DataFrame()
        vol_df = pd.DataFrame({tickers[0]: df['Volume']}) if 'Volume' in df.columns else pd.DataFrame()

    for c in stock_codes:
        tw = f"{c}.TW"
        two = f"{c}.TWO"
        
        closes = close_df[tw].dropna() if tw in close_df.columns else pd.Series(dtype=float)
        vols = vol_df[tw].dropna() if tw in vol_df.columns else pd.Series(dtype=float)
        
        if closes.empty:
            closes = close_df[two].dropna() if two in close_df.columns else pd.Series(dtype=float)
            vols = vol_df[two].dropna() if two in vol_df.columns else pd.Series(dtype=float)
            
        if len(closes) >= 2 and len(vols) >= 2:
            c_today, c_yest = float(closes.iloc[-1]), float(closes.iloc[-2])
            v_today, v_yest = float(vols.iloc[-1]), float(vols.iloc[-2])
            
            p_pct = (c_today - c_yest) / c_yest * 100 if c_yest > 0 else 0
            v_pct = (v_today - v_yest) / v_yest * 100 if v_yest > 0 else 0
            
            quotes[c] = {
                "price": c_today, "price_pct": p_pct,
                "vol": int(v_today / 1000), "vol_pct": v_pct,
                "date": closes.index[-1].strftime("%m/%d")
            }
    return quotes

# ==========================================
# 🎨 畫面渲染主程式
# ==========================================
def show_watchlist_page(STOCK_DICT=None, conn=None, SHEET_URL=None):
    st.title("冒險者專屬追蹤名單")

    if not st.session_state.get("logged_in", False):
        st.warning("⚠️ 守衛：「這區是 VIP 專屬！請先前往『登入頁面』出示邀請函。」")
        if st.button("前往登入", key="go_login_from_watchlist"):
            st.query_params["page"] = "login"
            st.rerun()
        return

    username = st.session_state.get("username", "guest")
    # 🌟 傳入連線物件
    watchlist = get_user_watchlist(username, conn, SHEET_URL)
    MAX_STOCKS = 60 

    st.subheader(f"新增追蹤標的 (目前 {len(watchlist)}/{MAX_STOCKS} 檔)")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_stock = st.text_input("請輸入股票代號或名稱", key="new_stock_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("加入追蹤", use_container_width=True):
            if new_stock:
                if len(watchlist) >= MAX_STOCKS:
                    st.error(f"⚠️ 追蹤名單已達 {MAX_STOCKS} 檔上限！")
                else:
                    query_clean = new_stock.strip()
                    final_stock_name = query_clean
                    
                    if STOCK_DICT:
                        if query_clean in STOCK_DICT:
                            final_stock_name = f"{STOCK_DICT[query_clean]['id']} {STOCK_DICT[query_clean]['name']}"
                        else:
                            for k, v in STOCK_DICT.items():
                                if query_clean in k or query_clean == v["id"] or query_clean == v["name"]:
                                    final_stock_name = f"{v['id']} {v['name']}"
                                    break

                    if final_stock_name not in watchlist:
                        watchlist[final_stock_name] = "" 
                        # 🌟 寫入時傳入連線物件
                        save_user_watchlist(username, watchlist, conn, SHEET_URL)
                        st.success(f"已加入「{final_stock_name}」！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info(f"「{final_stock_name}」已在名單中囉！")

    st.markdown("<hr style='border-color: #334155; margin: 10px 0;'>", unsafe_allow_html=True)
    
    if not watchlist:
        st.info("目前還沒有追蹤任何標的，趕快新增一個吧！")
    else:
        stock_codes = []
        for stock in watchlist.keys():
            m = re.search(r'\d+', stock)
            if m: stock_codes.append(m.group())

        with st.spinner("📡 正在同步即時報價與成交量..."):
            market_data = get_watchlist_quotes(stock_codes)

        col_space, col_batch_del = st.columns([8.5, 1.5])
        with col_batch_del:
            if st.button("🗑️ 刪除勾選", use_container_width=True, type="primary"):
                to_delete = [s for s in watchlist.keys() if st.session_state.get(f"chk_{s}", False)]
                if to_delete:
                    for s in to_delete: del watchlist[s]
                    save_user_watchlist(username, watchlist, conn, SHEET_URL)
                    st.success(f"已移除 {len(to_delete)} 檔！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("請先勾選後方選取框。")

        col_ratios = [0.9, 0.7, 1.2, 1.2, 3.2, 0.7, 0.6, 0.5]
        
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(col_ratios)
        h1.markdown("<span style='color:#94a3b8; font-size:14px;'>標的名稱</span>", unsafe_allow_html=True)
        h2.markdown("<span style='color:#94a3b8; font-size:14px;'>產業別</span>", unsafe_allow_html=True)
        h3.markdown("<span style='color:#94a3b8; font-size:14px;'>最新價</span>", unsafe_allow_html=True)
        h4.markdown("<span style='color:#94a3b8; font-size:14px;'>成交量 (張)</span>", unsafe_allow_html=True)
        h5.markdown("<span style='color:#94a3b8; font-size:14px;'>專屬筆記 (Enter換行/點擊空白處存檔)</span>", unsafe_allow_html=True)
        h8.markdown("<span style='color:#94a3b8; font-size:13px;'>批次</span>", unsafe_allow_html=True)

        def save_note_callback(stock_key):
            watchlist[stock_key] = st.session_state[f"note_{stock_key}"]
            save_user_watchlist(username, watchlist, conn, SHEET_URL)

        def fmt_color(val, is_pct=False, is_vol=False):
            color = "#FF4B4B" if val > 0 else ("#00E272" if val < 0 else "#94A3B8")
            sign = "+" if val > 0 else ""
            tail = "%" if is_pct else ""
            if is_vol: return f"<span style='color:{color}; font-size:12px;'>({sign}{val:.1f}%)</span>"
            return f"<span style='color:{color}; font-weight:bold;'>{sign}{val:.2f}{tail}</span>"

        for stock, note in list(watchlist.items()):
            pure_code = None
            stock_code_match = re.search(r'\d+', stock)
            if stock_code_match: pure_code = stock_code_match.group()

            industry_label = "未知"
            if pure_code and STOCK_DICT and pure_code in STOCK_DICT:
                industry_label = STOCK_DICT[pure_code].get("industry", "未知")

            p_str, v_str = "<span style='color:#555;'>-</span>", "<span style='color:#555;'>-</span>"
            if pure_code and pure_code in market_data:
                d = market_data[pure_code]
                p_str = f"<span style='font-size:16px;'>{d['price']:.2f}</span><br>{fmt_color(d['price_pct'], True)}"
                v_str = f"<span style='font-size:15px;'>{d['vol']:,}</span><br>{fmt_color(d['vol_pct'], False, True)}"

            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(col_ratios)
            
            with c1:
                st.markdown(f"<div style='padding-top:8px; font-weight:bold; font-size:15px;'>{stock}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='padding-top:10px; font-size:12px; color:#38BDF8;'><span style='background-color:#1E293B; padding:2px 5px; border-radius:4px; border: 1px solid #0369a1;'>{industry_label}</span></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='padding-top:4px;'>{p_str}</div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='padding-top:4px;'>{v_str}</div>", unsafe_allow_html=True)
            with c5:
                st.markdown("<div style='padding-top:2px;'>", unsafe_allow_html=True)
                st.text_area(
                    "筆記", 
                    value=note, 
                    key=f"note_{stock}", 
                    label_visibility="collapsed", 
                    placeholder="點此輸入筆記...", 
                    on_change=save_note_callback, 
                    args=(stock,),
                    height=68 
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with c6:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button(f"籌碼", key=f"view_{stock}", use_container_width=True):
                    st.session_state["selected_watch_stock"] = stock
                    st.session_state["global_search_final"] = pure_code if pure_code else stock
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c7:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button(f"移除", key=f"remove_{stock}", use_container_width=True):
                    del watchlist[stock]
                    save_user_watchlist(username, watchlist, conn, SHEET_URL)
                    if st.session_state.get("selected_watch_stock") == stock:
                        st.session_state["selected_watch_stock"] = None
                        st.session_state["global_search_final"] = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c8:
                st.markdown("<div style='padding-top:22px; padding-left:5px;'>", unsafe_allow_html=True)
                st.checkbox("選取", key=f"chk_{stock}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #1E293B; margin: 5px 0;'>", unsafe_allow_html=True)
