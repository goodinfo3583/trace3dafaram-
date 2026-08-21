# views/watchlist_page.py
import streamlit as st
import json
import re
import time
import pandas as pd

# ==========================================
# 💾 資料庫存取 (Google Sheets 正式連線版)
# ==========================================
def get_user_watchlist(username, conn, SHEET_URL):
    if not conn or not SHEET_URL: return {}
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="會員名冊", ttl=0)
        if df.empty or '帳號' not in df.columns or 'Watchlist' not in df.columns:
            return {}
            
        clean_accounts = df['帳號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
        target_user = str(username).strip().lower()
        match = df[clean_accounts == target_user]
        
        if not match.empty:
            gs_watchlist_str = match.iloc[0]['Watchlist']
            if pd.notna(gs_watchlist_str) and str(gs_watchlist_str).strip() != "":
                data = json.loads(str(gs_watchlist_str))
                if isinstance(data, list): return {stock: "" for stock in data}
                return data
    except Exception as e: pass
    return {}

def save_user_watchlist(username, watchlist, conn, SHEET_URL):
    if not conn or not SHEET_URL:
        st.error("⚠️ 無法連線至資料庫，無法存檔。")
        return
    try:
        watchlist_str = json.dumps(watchlist, ensure_ascii=False)
        df = conn.read(spreadsheet=SHEET_URL, worksheet="會員名冊", ttl=0)
        if df.empty or '帳號' not in df.columns: return
            
        if 'Watchlist' not in df.columns: df['Watchlist'] = ""
        df['Watchlist'] = df['Watchlist'].astype(object)
            
        clean_accounts = df['帳號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.lower()
        target_user = str(username).strip().lower()
        idx = df[clean_accounts == target_user].index
        
        if len(idx) > 0:
            df.at[idx[0], 'Watchlist'] = watchlist_str
            conn.update(spreadsheet=SHEET_URL, worksheet="會員名冊", data=df)
    except Exception as e:
        st.error(f"❌ 存檔失敗: {e}")

# ==========================================
# 🚀 高效能批次報價引擎
# ==========================================
@st.cache_data(ttl=300)
def get_watchlist_quotes(stock_codes):
    import yfinance as yf
    if not stock_codes: return {}
    
    tickers = [f"{c}.TW" for c in stock_codes] + [f"{c}.TWO" for c in stock_codes]
    try: df = yf.download(tickers, period="5d", progress=False)
    except: return {}
        
    quotes = {}
    if df.empty: return quotes
    
    if isinstance(df.columns, pd.MultiIndex):
        close_df = df['Close'] if 'Close' in df.columns else pd.DataFrame()
        vol_df = df['Volume'] if 'Volume' in df.columns else pd.DataFrame()
    else:
        close_df = pd.DataFrame({tickers[0]: df['Close']}) if 'Close' in df.columns else pd.DataFrame()
        vol_df = pd.DataFrame({tickers[0]: df['Volume']}) if 'Volume' in df.columns else pd.DataFrame()

    for c in stock_codes:
        tw, two = f"{c}.TW", f"{c}.TWO"
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
            quotes[c] = {"price": c_today, "price_pct": p_pct, "vol": int(v_today / 1000), "vol_pct": v_pct, "date": closes.index[-1].strftime("%Y/%m/%d")}
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
    wl_cache_key = f"wl_cache_{username}"

    if wl_cache_key not in st.session_state:
        with st.spinner("載入您的專屬名單中..."):
            st.session_state[wl_cache_key] = get_user_watchlist(username, conn, SHEET_URL)
            
    watchlist = st.session_state[wl_cache_key]
    MAX_STOCKS = 60 

    # 確保每個筆記欄位的值都在 session_state 中，避免元件衝突
    for stock in list(watchlist.keys()):
        nk = f"note_{stock}"
        if nk not in st.session_state:
            st.session_state[nk] = watchlist[stock]

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
                        st.session_state[f"note_{final_stock_name}"] = ""
                        st.success(f"已暫存「{final_stock_name}」，請記得點擊左上方「💾 存檔」！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info(f"「{final_stock_name}」已在名單中囉！")

    st.markdown("<hr style='border-color: #334155; margin: 10px 0;'>", unsafe_allow_html=True)
    
    # 準備報價資料
    stock_codes = []
    for stock in watchlist.keys():
        m = re.search(r'\d+', stock)
        if m: stock_codes.append(m.group())

    market_data = {}
    market_date = "今日"
    if stock_codes:
        with st.spinner("📡 正在同步即時報價與成交量..."):
            market_data = get_watchlist_quotes(stock_codes)
            if market_data:
                # 抓取第一筆資料的日期作為基準日
                market_date = list(market_data.values())[0]["date"]

    # ==========================================
    # 💾 左上角存檔與日期區塊 
    # ==========================================
    col_save, col_date, col_space = st.columns([1.5, 3.0, 5.5])
    with col_save:
        if st.button("💾 存檔", use_container_width=True, type="primary", help="將目前的變更同步至雲端"):
            with st.spinner("正在上傳至雲端..."):
                for stock in list(watchlist.keys()):
                    nk = f"note_{stock}"
                    if nk in st.session_state:
                        watchlist[stock] = st.session_state[nk]
                save_user_watchlist(username, watchlist, conn, SHEET_URL)
            st.success("✅ 存檔成功！")
            time.sleep(1)
            st.rerun()
    with col_date:
        if watchlist and market_data:
            st.markdown(f"<div style='padding-top:8px; color:#38BDF8; font-size:15px; font-weight:bold;'>📅 行情基準日：{market_date}</div>", unsafe_allow_html=True)

    st.write("") 
    
    if not watchlist:
        st.info("目前還沒有追蹤任何標的，趕快新增一個吧！")
    else:
        # 📋 分割為 8 個區域 (騰出一個專屬給「帶入」按鈕)
        col_ratios = [1.1, 0.9, 1.1, 1.1, 3.8, 0.8, 0.6, 0.6]
        
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(col_ratios)
        h1.markdown("<span style='color:#94a3b8; font-size:14px;'>標的名稱</span>", unsafe_allow_html=True)
        h2.markdown("<span style='color:#94a3b8; font-size:14px;'>產業別</span>", unsafe_allow_html=True)
        h3.markdown("<span style='color:#94a3b8; font-size:14px;'>最新價</span>", unsafe_allow_html=True)
        h4.markdown("<span style='color:#94a3b8; font-size:14px;'>成交量 (張)</span>", unsafe_allow_html=True)
        h5.markdown("<span style='color:#94a3b8; font-size:14px;'>專屬筆記 (編輯後點擊左上方存檔)</span>", unsafe_allow_html=True)
        h6.markdown("")
        h7.markdown("")
        h8.markdown("")

        def fmt_color(val, is_pct=False, is_vol=False):
            color = "#FF4B4B" if val > 0 else ("#00E272" if val < 0 else "#94A3B8")
            sign = "+" if val > 0 else ""
            tail = "%" if is_pct else ""
            if is_vol: return f"<span style='color:{color}; font-size:12px;'>({sign}{val:.1f}%)</span>"
            return f"<span style='color:{color}; font-weight:bold;'>{sign}{val:.2f}{tail}</span>"

        for stock in list(watchlist.keys()):
            nk = f"note_{stock}"
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
                # 完全依賴 session_state 綁定，避免重複覆寫
                st.text_area(
                    "筆記", 
                    key=nk, 
                    label_visibility="collapsed", 
                    placeholder="點此輸入筆記...", 
                    height=68 
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with c6:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                # 📥 智慧帶入按鈕
                if st.button(f"📥 帶入", key=f"import_{stock}", use_container_width=True, help="將今日行情寫入筆記 (不覆蓋)"):
                    if pure_code and pure_code in market_data:
                        d = market_data[pure_code]
                        # 準備要帶入的字串格式
                        append_str = f"[{d['date'][5:]}] 收:{d['price']:.2f} 量:{d['vol']:,}張"
                        
                        # 如果原本有筆記，就自動換行加上去
                        current_text = st.session_state[nk].strip()
                        if current_text:
                            st.session_state[nk] = current_text + f"\n{append_str}"
                        else:
                            st.session_state[nk] = append_str
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c7:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button(f"🔍", key=f"view_{stock}", use_container_width=True, help="顯示籌碼診斷"):
                    st.session_state["selected_watch_stock"] = stock
                    st.session_state["global_search_final"] = pure_code if pure_code else stock
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c8:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button(f"🗑️", key=f"remove_{stock}", use_container_width=True, help="移除此標的"):
                    del watchlist[stock]
                    if nk in st.session_state:
                        del st.session_state[nk]
                    if st.session_state.get("selected_watch_stock") == stock:
                        st.session_state["selected_watch_stock"] = None
                        st.session_state["global_search_final"] = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #1E293B; margin: 5px 0;'>", unsafe_allow_html=True)
