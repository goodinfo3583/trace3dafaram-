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

    for stock in list(watchlist.keys()):
        nk = f"note_{stock}"
        if nk not in st.session_state:
            st.session_state[nk] = watchlist[stock]

    st.subheader(f"新增追蹤標的 (目前 {len(watchlist)}/{MAX_STOCKS} 檔)")
    col1, col2 = st.columns([3, 1])
    
    # 🚀 升級：自動產生下拉選單，並使用 set {...} 剃除重複的雙胞胎！
    stock_options = []
    if STOCK_DICT:
        unique_options = {f"{v['id']} {v['name']}" for v in STOCK_DICT.values() if len(str(v['id'])) <= 4}
        stock_options = sorted(list(unique_options))

    with col1:
        new_stock = st.selectbox(
            "請選擇股票", 
            options=[""] + stock_options,
            key="new_stock_input",
            label_visibility="collapsed"
        )
        
    with col2:
        if st.button("加入追蹤", use_container_width=True):
            if new_stock:
                if len(watchlist) >= MAX_STOCKS:
                    st.error(f"⚠️ 追蹤名單已達 {MAX_STOCKS} 檔上限！")
                else:
                    # 💡 因為選單出來的值已經是完美的 "2330 台積電" 格式，我們不需要再做任何文字處理！
                    if new_stock not in watchlist:
                        watchlist[new_stock] = "" 
                        st.session_state[f"note_{new_stock}"] = ""
                        st.success(f"已暫存「{new_stock}」，請記得點擊左上方「存檔」！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info(f"「{new_stock}」已在名單中囉！")

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
                market_date = list(market_data.values())[0]["date"]

    # ==========================================
    # 💾 左上角存檔、匯出與日期區塊 
    # ==========================================
    col_save, col_export, col_date, col_space = st.columns([1.5, 1.5, 3.0, 4.0])
    with col_save:
        if st.button("存檔", icon=":material/save:", use_container_width=True, type="primary", help="將目前的變更同步至雲端"):
            with st.spinner("正在上傳至雲端..."):
                for stock in list(watchlist.keys()):
                    nk = f"note_{stock}"
                    if nk in st.session_state:
                        watchlist[stock] = st.session_state[nk]
                save_user_watchlist(username, watchlist, conn, SHEET_URL)
            st.success("✅ 存檔成功！")
            time.sleep(1)
            st.rerun()
            
    with col_export:
        # 製作匯出專用的 DataFrame
        if watchlist:
            export_data = []
            for stock, note in watchlist.items():
                current_note = st.session_state.get(f"note_{stock}", note)
                pure_code = None
                stock_code_match = re.search(r'\d+', stock)
                if stock_code_match: pure_code = stock_code_match.group()
                
                # 若有抓到即時報價也一併附上
                price, vol = "", ""
                if pure_code and pure_code in market_data:
                    price = market_data[pure_code]["price"]
                    vol = market_data[pure_code]["vol"]
                    
                export_data.append({"標的名稱": stock, "最新價": price, "成交量(張)": vol, "專屬筆記": current_note})
                
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            
            # 使用 Streamlit 內建的下載按鈕
            st.download_button(
                label="匯出",
                icon=":material/download:",
                data=csv,
                file_name=f"watchlist_{username}.csv",
                mime="text/csv",
                use_container_width=True,
                help="下載為 CSV 檔"
            )
        else:
            st.button("匯出", icon=":material/download:", use_container_width=True, disabled=True)

    with col_date:
        if watchlist and market_data:
            st.markdown(f"<div style='padding-top:8px; color:#38BDF8; font-size:15px; font-weight:bold;'>📅 行情基準日：{market_date}</div>", unsafe_allow_html=True)

    st.write("") 
    
    if not watchlist:
        st.info("目前還沒有追蹤任何標的，趕快新增一個吧！")
    else:
        # 📋 分割為 8 個區域 (將按鈕欄位縮小，因為只剩 Icon)
        col_ratios = [1.1, 0.9, 1.1, 1.1, 4.4, 0.5, 0.5, 0.5]
        
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

        def append_quote_to_note(stock_name, p_code):
            if p_code and p_code in market_data:
                d = market_data[p_code]
                append_str = f"[{d['date'][5:]}] 收:{d['price']:.2f} 量:{d['vol']:,}張"
                nk = f"note_{stock_name}"
                current_text = st.session_state.get(nk, "").strip()
                
                if current_text:
                    st.session_state[nk] = current_text + f"\n{append_str}"
                else:
                    st.session_state[nk] = append_str
                watchlist[stock_name] = st.session_state[nk]

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
                st.button(
                    "", 
                    icon=":material/input:", # 帶入
                    key=f"import_{stock}", 
                    use_container_width=True, 
                    help="將今日行情寫入筆記 (不覆蓋)",
                    on_click=append_quote_to_note,
                    args=(stock, pure_code)
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with c7:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button("", icon=":material/monitoring:", key=f"view_{stock}", use_container_width=True, help="顯示籌碼診斷"):
                    # 🚀 強制轉為標準格式，才能與下拉選單的選項完美吻合！
                    standard_format = stock
                    if pure_code and STOCK_DICT and pure_code in STOCK_DICT:
                        v = STOCK_DICT[pure_code]
                        standard_format = f"{v['id']} {v['name']}"
                        
                    st.session_state["selected_watch_stock"] = standard_format
                    st.session_state["global_search_final"] = standard_format
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with c8:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button("", icon=":material/delete:", key=f"remove_{stock}", use_container_width=True, help="移除此標的"):
                    del watchlist[stock]
                    if nk in st.session_state:
                        del st.session_state[nk]
                    if st.session_state.get("selected_watch_stock") == stock:
                        st.session_state["selected_watch_stock"] = None
                        st.session_state["global_search_final"] = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #1E293B; margin: 5px 0;'>", unsafe_allow_html=True)
