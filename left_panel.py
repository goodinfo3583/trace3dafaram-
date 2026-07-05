import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import os
# ==========================================
# 🌟 所有側邊欄專屬工具函數區 (🚨 必須放在 with st.sidebar 的最上方！)
# ==========================================

# --- 1. 快搜專屬工具 ---
def robust_search_engine(df, query):
    if df is None or df.empty: return pd.DataFrame()
    df = df.loc[:, ~df.columns.duplicated()].copy()
    query = str(query).strip()
    mask = pd.Series(False, index=df.index)
    if '股票代號' in df.columns:
        df['股票代號'] = df['股票代號'].astype(str).str.strip()
        mask = mask | (df['股票代號'] == query)
    if '股票名稱' in df.columns:
        df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
        mask = mask | df['股票名稱'].str.contains(query, na=False, case=False)
    return df[mask]

def scan_and_display(title, session_key, query):
    st.markdown(f"<h6 style='color: #E2E8F0; margin-bottom: 5px;'>{title}</h6>", unsafe_allow_html=True)
    if session_key not in st.session_state:
        st.write("⚪ 尚未載入資料表")
        return
    df = st.session_state[session_key]
    if df is None or df.empty:
        st.write("⚪ 該榜單無任何資料")
        return
    res = robust_search_engine(df, query)
    if not res.empty:
        pct_cols = [c for c in res.columns if '持股' in c or '佔' in c or '%' in c]
        if pct_cols:
            all_zero = True
            for c in pct_cols:
                val = res.iloc[0][c]
                if pd.isna(val): continue
                val_str = str(val).strip().replace('%', '')
                if val_str.lower() in ['', '-', 'nan', 'none', 'null']: continue
                try:
                    if abs(float(val_str)) > 0.0001:
                        all_zero = False
                        break
                except ValueError: continue
            if all_zero:
                st.write("⚪ 未進榜")
                return
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.write("⚪ 未進榜")

def generate_stock_commentary(row):
    score = row.get('總分', 0)
    warns = str(row.get('賣出警示', ''))
    b5_trend = str(row.get('大股東動向', ''))
    has_warning = "⚠️" in warns or "🚨" in warns
    high_score = score >= 3
    if has_warning and high_score:
        return f"⚔️ 【激烈換手】系統偵測到法人分歧 ({warns})，但該股依然獲得 {score} 分的高評估！這代表『一方的倒貨正被大戶強勢吃下』。若能維持強勢，代表承接方實力極強，需嚴設停損。"
    if has_warning and not high_score:
        return f"🚨 【風險警示】法人正在進行倒貨調節 ({warns})，且無強大買盤承接，籌碼結構面臨鬆動。建議暫避風頭。"
    if "大減" in b5_trend:
        return "⚠️ 【大戶撤退】400張以上大戶出現明顯減碼跡象，主力籌碼渙散，建議先行觀望。"
    if score >= 6:
        base_comment = "🔥 【強勢噴發】籌碼面極度優異！內外資法人與大戶同步共振做多，具備強大的波段上攻潛力。"
        if "大增" in b5_trend: base_comment += "大股東籌碼大幅集中，是不可多得的強勢防守標的。"
        return base_comment
    elif score >= 3: return "📈 【偏多佈局】主力籌碼持續進駐，法人買盤給予一定支撐。具備穩健的波段潛力。"
    elif score >= 1: return "🔄 【中性觀望】籌碼表現較為平淡，雖有零星買盤但缺乏明確連續性。建議多看少做。"
    else: return "❄️ 【弱勢整理】籌碼處於流失或無主力認養狀態。建議暫不考量。"
#大盤總體經濟
def render_sidebar_market_summary():
    df_spot, date_spot = get_latest_csv("三大法人買賣超金額")
    df_fut, _ = get_latest_csv("三大法人期貨多空")
    df_fut_prev = get_prev_csv("三大法人期貨多空", date_spot)
    df_margin, margin_csv_name = get_latest_csv("融資融券餘額")
    
    # 📥 新增：讀取上市與上櫃成交量資料
    df_twse, _ = get_latest_csv("大盤上市成交量")
    df_tpex, _ = get_latest_csv("大盤上櫃成交量")
    
    if df_spot is None or df_fut is None:
        st.warning("尚無大盤數據，請確認資料夾中已有今日 CSV。")
        return "未知"

    net_foreign, net_trust, net_dealer, net_total = 0.0, 0.0, 0.0, 0.0
    for _, row in df_spot.iterrows():
        name = str(row.get('單位名稱', ''))
        try: val = float(str(row.get('買賣差額', '0')).replace(',', '')) / 100000000
        except: val = 0.0
        if '外資' in name and '不含' in name: net_foreign += val
        elif '外資自營商' in name: net_foreign += val
        elif '投信' in name: net_trust += val
        elif '自營商' in name: net_dealer += val
        elif '合計' in name: net_total = val

    oi_foreign, oi_trust, oi_dealer = 0, 0, 0
    if df_fut is not None:
        target_oi_col = next((c for c in df_fut.columns if '未平倉' in c and '多空淨額' in c), None)
        if target_oi_col:
            for _, row in df_fut.iterrows():
                row_vals = " ".join([str(x) for x in row.values])
                if '臺股期貨' in row_vals:
                    iden = str(row.values[2]) 
                    try: val = int(str(row[target_oi_col]).replace(',', ''))
                    except: val = 0
                    if '外資' in iden: oi_foreign = val
                    elif '投信' in iden: oi_trust = val
                    elif '自營商' in iden: oi_dealer = val
    total_oi = oi_foreign + oi_trust + oi_dealer

    oi_f_prev, oi_t_prev, oi_d_prev = None, None, None
    if df_fut_prev is not None:
        t_col_prev = next((c for c in df_fut_prev.columns if '未平倉' in c and '多空淨額' in c), None)
        if t_col_prev:
            for _, row in df_fut_prev.iterrows():
                r_vals = " ".join([str(x) for x in row.values])
                if '臺股期貨' in r_vals:
                    iden = str(row.values[2]) 
                    try: val = int(str(row[t_col_prev]).replace(',', ''))
                    except: val = 0
                    if '外資' in iden: oi_f_prev = val
                    elif '投信' in iden: oi_t_prev = val
                    elif '自營商' in iden: oi_d_prev = val

    margin_diff_yi, margin_today_yi = 0.0, 0.0
    if df_margin is not None:
        for _, row in df_margin.iterrows():
            row_list = [str(x).replace(',', '').strip() for x in row.values]
            row_str = "".join(row_list)
            if '融資金額' in row_str:
                try:
                    margin_prev = float(row_list[-2]) 
                    margin_today = float(row_list[-1])
                    margin_diff_yi = (margin_today - margin_prev) / 100000
                    margin_today_yi = margin_today / 100000
                    break
                except: pass

    # 📊 新增：計算成交量 (單位轉為億)
    twse_vol_today, twse_diff = 0.0, 0.0
    if df_twse is not None and len(df_twse) >= 2:
        try:
            # 上市單位是「元」，除以 100,000,000 變成億
            v_today = float(str(df_twse.iloc[-1]['成交金額']).replace(',', '')) / 100000000
            v_yest = float(str(df_twse.iloc[-2]['成交金額']).replace(',', '')) / 100000000
            twse_vol_today = v_today
            twse_diff = v_today - v_yest
        except: pass

    tpex_vol_today, tpex_diff = 0.0, 0.0
    if df_tpex is not None and len(df_tpex) >= 2:
        try:
            # 上櫃單位是「千元」，只要除以 100,000 就變成億
            v_today = float(str(df_tpex.iloc[-1]['成交金額(千元)']).replace(',', '')) / 100000
            v_yest = float(str(df_tpex.iloc[-2]['成交金額(千元)']).replace(',', '')) / 100000
            tpex_vol_today = v_today
            tpex_diff = v_today - v_yest
        except: pass

    total_vol_today = twse_vol_today + tpex_vol_today
    total_diff = twse_diff + tpex_diff

    def get_color(val, is_float=True):
        if val > 0: return "#ff4b4b", f"+{val:,.1f}" if is_float else f"+{val:,}"
        elif val < 0: return "#00e676", f"{val:,.1f}" if is_float else f"{val:,}"
        return "#e0e0e0", "0.0" if is_float else "0"

    f_c, f_s = get_color(net_foreign)
    t_c, t_s = get_color(net_trust)
    d_c, d_s = get_color(net_dealer)
    to_c, to_s = get_color(net_total)
    fo_c, fo_s = get_color(oi_foreign, False)
    to_oc, to_os = get_color(oi_trust, False)
    do_c, do_os = get_color(oi_dealer, False)
    too_c, too_os = get_color(total_oi, False)
    m_c, m_s = get_color(margin_diff_yi)
    
    # 成交量增減顏色
    tw_c, tw_s = get_color(twse_diff)
    tp_c, tp_s = get_color(tpex_diff)
    tot_c, tot_s = get_color(total_diff)

    # === 開始組裝 HTML ===
    html = f"<div style='font-size: 13px; color: #00D2FF;'>基準日：{date_spot}</div>"
    
    # 區塊 1: 法人現貨與未平倉
    html += "<table style='width: 100%; text-align: center; border-collapse: collapse; margin-top: 5px; font-size: 14px;'>"
    html += "<tr style='border-bottom: 1px solid #555; background-color: #262730;'>"
    html += "<th style='padding: 5px;'>法人</th><th style='padding: 5px;'>現貨(億)</th><th style='padding: 5px;'>TX未平倉</th></tr>"
    html += f"<tr><td style='padding: 4px;'>🌐 外資</td><td style='color: {f_c}; vertical-align: middle;'>{f_s}</td><td style='color: {fo_c}; vertical-align: middle; padding-bottom: 6px;'>{fo_s}{get_diff_ui(oi_foreign, oi_f_prev)}</td></tr>"
    html += f"<tr><td style='padding: 4px;'>🏦 投信</td><td style='color: {t_c}; vertical-align: middle;'>{t_s}</td><td style='color: {to_oc}; vertical-align: middle; padding-bottom: 6px;'>{to_os}{get_diff_ui(oi_trust, oi_t_prev)}</td></tr>"
    html += f"<tr><td style='padding: 4px;'>🏢 自營商</td><td style='color: {d_c}; vertical-align: middle;'>{d_s}</td><td style='color: {do_c}; vertical-align: middle; padding-bottom: 6px;'>{do_os}{get_diff_ui(oi_dealer, oi_d_prev)}</td></tr>"
    
    tot_prev = (oi_f_prev + oi_t_prev + oi_d_prev) if oi_f_prev is not None else None
    html += f"<tr style='border-top: 1px solid #555; font-weight: bold;'><td style='padding: 4px;'> 合計</td><td style='color: {to_c}; vertical-align: middle;'>{to_s}</td><td style='color: {too_c}; vertical-align: middle; padding-bottom: 6px;'>{too_os}{get_diff_ui(total_oi, tot_prev)}</td></tr>"
    html += "</table>"
    
    # 🌟 區塊 2 (新增): 市場成交量 (完美安插在中間)
    if total_vol_today > 0:
        html += "<div style='margin-top: 8px; padding: 6px; background-color: #1e1e24; border: 1px solid #555; border-radius: 5px; font-size: 13px;'>"
        html += "<div style='font-weight: bold; margin-bottom: 4px;'>市場成交量 (億)</div>"
        html += f"<div style='color: #aaa; margin-top: 2px;'> 上市 <span style='float: right; color: #fff;'>{twse_vol_today:,.1f} <span style='color: {tw_c}; font-size: 11px; margin-left: 2px;'>({tw_s})</span></span></div>"
        html += f"<div style='color: #aaa; margin-top: 2px;'> 上櫃 <span style='float: right; color: #fff;'>{tpex_vol_today:,.1f} <span style='color: {tp_c}; font-size: 11px; margin-left: 2px;'>({tp_s})</span></span></div>"
        html += "<div style='border-top: 1px dashed #555; margin: 4px 0;'></div>"
        html += f"<div style='color: #fbbf24; font-weight: bold; margin-top: 2px;'> 總量 <span style='float: right;'>{total_vol_today:,.1f} <span style='color: {tot_c}; font-size: 11px; margin-left: 2px;'>({tot_s})</span></span></div>"
        html += "</div>"
    
    # 區塊 3: 融資餘額
    if margin_today_yi != 0.0:
        margin_date = margin_csv_name[:8] if margin_csv_name else "未知"
        html += "<div style='margin-top: 8px; padding: 6px; background-color: #1e1e24; border: 1px solid #555; border-radius: 5px; font-size: 13px;'>"
        html += f"<div style='font-weight: bold;'>大盤融資餘額 <span style='font-size: 13px; color: #00D2FF; font-weight: normal; margin-left: 5px;'>({margin_date})</span></div>"
        html += f"<div style='color: #aaa; margin-top: 4px;'>今日增減(億) <span style='color: {m_c}; font-weight: bold; float: right;'>{m_s}</span></div>"
        html += f"<div style='color: #aaa; margin-top: 2px;'>餘額總計(億) <span style='float: right; color: #fff;'>{margin_today_yi:,.1f}</span></div>"
        html += "</div>"
        
    st.markdown(html, unsafe_allow_html=True)
    return date_spot

def render_options_dashboard():
    df_opt, date_opt = get_latest_csv("臺指選擇權行情簡表")
    df_pcr, _ = get_latest_csv("臺指選擇權PC比")
    df_opt_prev = get_prev_csv("臺指選擇權行情簡表", date_opt)
    
    if date_opt and date_opt != "未知":
        st.markdown(f"<div style='font-size: 13px; color: #00D2FF; margin-bottom: 12px;'>基準日：{date_opt}</div>", unsafe_allow_html=True)
    
    if df_opt is None:
        st.warning("尚無選擇權資料。")
        return

    pcr_val = 0.0
    if df_pcr is not None:
        pcr_col = next((c for c in df_pcr.columns if '買賣權未平倉量比率' in c), None)
        if pcr_col:
            try: pcr_val = float(str(df_pcr[pcr_col].dropna().iloc[-1]).replace('%', ''))
            except: pass
    pcr_color = "#FF4B4B" if pcr_val > 100 else "#00E272"
    st.markdown(f"**PCR:** <span style='color:{pcr_color}; font-size: 16px;'>{pcr_val}%</span>", unsafe_allow_html=True)

    col_strike = next((c for c in df_opt.columns if '履約價' in c), None)
    col_type = next((c for c in df_opt.columns if '買賣權' in c), None)
    col_oi = next((c for c in df_opt.columns if '未沖銷' in c or '未平倉' in c), None)
    col_month = next((c for c in df_opt.columns if '到期' in c or '月份' in c), None)
    
    if not all([col_strike, col_type, col_oi, col_month]):
        st.info("🔄 選擇權格式讀取失敗。")
        return

    valid_months = [m for m in df_opt[col_month].dropna().unique() if str(m).startswith('20')]
    if not valid_months: return
    front_month = sorted(valid_months)[0]
    df_opt = df_opt[df_opt[col_month] == front_month].copy()

    df_opt[col_strike] = pd.to_numeric(df_opt[col_strike], errors='coerce')
    df_opt[col_oi] = pd.to_numeric(df_opt[col_oi].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    df_call = df_opt[df_opt[col_type].str.contains('Call|買權', case=False, na=False)].copy()
    df_put = df_opt[df_opt[col_type].str.contains('Put|賣權', case=False, na=False)].copy()
    
    top_calls = df_call.nlargest(2, col_oi).reset_index(drop=True)
    top_puts = df_put.nlargest(2, col_oi).reset_index(drop=True)
    max_pressure = int(top_calls.loc[0, col_strike]) if not top_calls.empty else 0
    max_support = int(top_puts.loc[0, col_strike]) if not top_puts.empty else 0

    prev_oi_dict = {}
    if df_opt_prev is not None and col_strike in df_opt_prev.columns:
        valid_months_p = [m for m in df_opt_prev[col_month].dropna().unique() if str(m).startswith('20')]
        if valid_months_p:
            f_month_p = sorted(valid_months_p)[0]
            df_opt_prev = df_opt_prev[df_opt_prev[col_month] == f_month_p]
            df_opt_prev[col_strike] = pd.to_numeric(df_opt_prev[col_strike], errors='coerce')
            df_opt_prev[col_oi] = pd.to_numeric(df_opt_prev[col_oi].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            for _, row in df_opt_prev.iterrows():
                strike_val = row[col_strike]
                if pd.isna(strike_val): continue
                strike_val = int(strike_val)
                type_val = str(row[col_type])
                oi_val = int(row[col_oi])
                
                if strike_val not in prev_oi_dict: prev_oi_dict[strike_val] = {'c': 0, 'p': 0}
                if 'Call' in type_val or '買權' in type_val: prev_oi_dict[strike_val]['c'] += oi_val
                if 'Put' in type_val or '賣權' in type_val: prev_oi_dict[strike_val]['p'] += oi_val

    start_strike = int(max_pressure) + 2000
    end_strike = int(max_support) - 3000
    if start_strike >= 36000 and end_strike < 36000: end_strike = 36000
        
    display_strikes = list(range(start_strike, end_strike - 1, -1000))
    
    html_opt = "<table style='width: 100%; text-align: center; border-collapse: collapse; margin-top: 5px; font-size: 13px;'>"
    html_opt += "<tr style='border-bottom: 1px solid #555; background-color: #262730;'>"
    html_opt += "<th style='padding: 5px;'>點位</th><th style='padding: 5px;'>⚔️ Call (口)</th><th style='padding: 5px;'>🛡️ Put (口)</th></tr>"
    
    for strike in display_strikes:
        c_val = df_call[df_call[col_strike] == strike][col_oi].sum()
        p_val = df_put[df_put[col_strike] == strike][col_oi].sum()
        if c_val == 0 and p_val == 0: continue
            
        strike_label = str(strike)
        if strike == max_pressure: strike_label += "<br><span style='color:#FF4B4B; font-size:10px;'>(最壓)</span>"
        elif strike == max_support: strike_label += "<br><span style='color:#00E272; font-size:10px;'>(最撐)</span>"

        prev_c = prev_oi_dict.get(strike, {}).get('c', None)
        prev_p = prev_oi_dict.get(strike, {}).get('p', None)

        html_opt += f"<tr style='border-bottom: 1px solid #333;'>"
        html_opt += f"<td style='padding: 6px; font-weight: bold; vertical-align: middle;'>{strike_label}</td>"
        html_opt += f"<td style='padding: 6px; color: #FF4B4B; vertical-align: middle;'>{int(c_val):,}{get_diff_ui(c_val, prev_c)}</td>"
        html_opt += f"<td style='padding: 6px; color: #00E272; vertical-align: middle;'>{int(p_val):,}{get_diff_ui(p_val, prev_p)}</td>"
        html_opt += f"</tr>"
        
    html_opt += "</table>"
    st.markdown(html_opt, unsafe_allow_html=True)

@st.cache_data(ttl=2400) 
def fetch_macro_indicators():
    import yfinance as yf
    data = {
        "vix": {"value": None, "pct": None},
        "vixtwn": {"value": None, "pct": None},
        "fng": {"score": None, "rating": "無法取得"}
    }
    
    # 1. 抓取美股 VIX (^VIX)
    try:
        hist_vix = yf.Ticker("^VIX").history(period="2d")
        if len(hist_vix) >= 2:
            latest = hist_vix['Close'].iloc[-1]
            prev = hist_vix['Close'].iloc[-2]
            data["vix"]["value"] = latest
            data["vix"]["pct"] = (latest - prev) / prev * 100
    except: pass

    # 2. 抓取台股 VIX (玩股網 / 期交所雙重備援)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url_wantgoo = "https://www.wantgoo.com/global/vixtwn"
        res = requests.get(url_wantgoo, headers=headers, timeout=5)
        if res.status_code == 200:
            import re
            match = re.search(r'"price":\s*([\d\.]+)', res.text)
            if not match: match = re.search(r'臺指VIX.*?(\d+\.\d{2})', res.text)
            if match:
                data["vixtwn"]["value"] = float(match.group(1))
                data["vixtwn"]["pct"] = 0.0 
        if data["vixtwn"]["value"] is None:
            url_taifex = "https://www.taifex.com.tw/cht/index"
            res_t = requests.get(url_taifex, headers=headers, timeout=5)
            match_t = re.search(r'VIX.*?(\d+\.\d{2})', res_t.text, re.IGNORECASE)
            if match_t:
                data["vixtwn"]["value"] = float(match_t.group(1))
                data["vixtwn"]["pct"] = 0.0 
    except: pass

    # 3. 抓取 CNN 恐懼貪婪指數
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            fg_data = res.json()
            score = int(fg_data['fear_and_greed']['score'])
            if score < 15: rating_tw = "🉐 分批加碼"
            elif score < 25: rating_tw = "🈵 積極買點"
            elif score > 90: rating_tw = "🈲 提高現金"
            elif score > 85: rating_tw = "🈹 獲利了結"
            elif score > 75: rating_tw = "🈴 分批減碼"
            else: rating_tw = "⚖️ 中立平穩"
            data["fng"]["score"] = score
            data["fng"]["rating"] = rating_tw
    except: pass

    return data

# ==========================================
# 📈 繪製 K 線圖與技術分析引擎 (加入快取與側邊欄窄版優化)
# ==========================================
@st.cache_data(ttl=900)
def fetch_yfinance_data(ticker, period="3y"):
    import yfinance as yf
    import pandas as pd
    try:
        df = yf.download(ticker, period=period, progress=False)
        return df
    except:
        return pd.DataFrame()

def render_technical_chart(stock_id, timeframe="日線", selected_mas=[], show_rsi=False, show_macd=False, show_kd=False):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd

    ticker_tw = f"{stock_id}.TW"
    ticker_two = f"{stock_id}.TWO"
    
    df = fetch_yfinance_data(ticker_tw)
    if df is None or df.empty:
        df = fetch_yfinance_data(ticker_two)
        
    if df is None or df.empty:
        st.warning(f"⚠️ 無法取得 {stock_id} 的即時報價。")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()]

    if df.index.tz is not None: df.index = df.index.tz_convert('Asia/Taipei')
    else: df.index = df.index.tz_localize('UTC').tz_convert('Asia/Taipei')

    daily_df = df.copy()

    if timeframe == "週線":
        daily_df = daily_df.resample('W-FRI').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
    elif timeframe == "月線":
        daily_df = daily_df.resample('ME').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

    for ma in [5, 10, 20, 60]:
        daily_df[f'{ma}MA'] = daily_df['Close'].rolling(window=ma).mean()

    close_series = daily_df['Close'].squeeze()
    
    if show_rsi:
        delta = close_series.diff()
        gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
        ema_gain = gain.ewm(com=13, adjust=False).mean(); ema_loss = loss.ewm(com=13, adjust=False).mean()
        rs = ema_gain / ema_loss.replace(0, 1e-9)
        daily_df['RSI'] = 100 - (100 / (1 + rs))

    if show_macd:
        ema12 = close_series.ewm(span=12, adjust=False).mean(); ema26 = close_series.ewm(span=26, adjust=False).mean()
        daily_df['DIF'] = ema12 - ema26
        daily_df['MACD_Sign'] = daily_df['DIF'].ewm(span=9, adjust=False).mean()
        daily_df['MACD_Hist'] = daily_df['DIF'] - daily_df['MACD_Sign']
        
    if show_kd:
        low_9 = daily_df['Low'].rolling(window=9).min(); high_9 = daily_df['High'].rolling(window=9).max()
        rsv = (close_series - low_9) / (high_9 - low_9).replace(0, 1e-9) * 100
        daily_df['K'] = rsv.ewm(com=2, adjust=False).mean()
        daily_df['D'] = daily_df['K'].ewm(com=2, adjust=False).mean()

    rows = 2
    row_heights = [0.5, 0.15]
    if show_rsi: rows += 1; row_heights.append(0.15)
    if show_macd: rows += 1; row_heights.append(0.15)
    if show_kd: rows += 1; row_heights.append(0.15)

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)
    up_color = 'rgb(240, 90, 90)'; down_color = 'rgb(80, 200, 120)'

    # 💡 修復點：加入 hovertemplate 強制使用中文顯示 開/高/低/收
    fig.add_trace(go.Candlestick(
        x=daily_df.index, open=daily_df['Open'].squeeze(), high=daily_df['High'].squeeze(), 
        low=daily_df['Low'].squeeze(), close=daily_df['Close'].squeeze(), name='K線', 
        increasing=dict(line=dict(color=up_color, width=1), fillcolor=up_color),
        decreasing=dict(line=dict(color=down_color, width=1), fillcolor=down_color),
        hovertemplate="<b>日期</b>: %{x|%Y-%m-%d}<br><b>開</b>: %{open:.2f}<br><b>高</b>: %{high:.2f}<br><b>低</b>: %{low:.2f}<br><b>收</b>: %{close:.2f}<extra></extra>"
    ), row=1, col=1)

    ma_colors = {'5MA': '#FFFF37', '10MA': '#00FFFF', '20MA': '#921AFF', '60MA': '#D0D0D0'}
    for ma in selected_mas:
        if ma in daily_df.columns:
            fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df[ma].squeeze(), mode='lines', name=ma, line=dict(color=ma_colors[ma], width=1)), row=1, col=1)

    vol_colors = [up_color if c >= o else down_color for c, o in zip(daily_df['Close'].squeeze(), daily_df['Open'].squeeze())]
    fig.add_trace(go.Bar(x=daily_df.index, y=daily_df['Volume'].squeeze(), name='成交量', marker_color=vol_colors), row=2, col=1)

    current_row = 3
    if show_kd:
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['K'].squeeze(), mode='lines', name='K', line=dict(color='#00CCFF', width=1)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['D'].squeeze(), mode='lines', name='D', line=dict(color='#FFCC00', width=1)), row=current_row, col=1)
        current_row += 1
    if show_rsi:
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['RSI'].squeeze(), mode='lines', name='RSI', line=dict(color='#E1BEE7', width=1)), row=current_row, col=1)
        current_row += 1
    if show_macd:
        # 💡 修復點：將 go.Scatter(type='bar') 正確改寫為 go.Bar 以解決 ValueError
        fig.add_trace(go.Bar(
            x=daily_df.index, y=daily_df['MACD_Hist'].squeeze(), name='MACD', 
            marker_color=[up_color if h >= 0 else down_color for h in daily_df['MACD_Hist'].squeeze()]
        ), row=current_row, col=1)

    fig.update_layout(
        xaxis_rangeslider_visible=False, height=400 + (rows - 2) * 100, 
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=5, r=40, t=20, b=5), showlegend=False, hovermode='x unified'
    )
    
    if timeframe == "日線":
        all_days = pd.date_range(start=daily_df.index.min().normalize(), end=daily_df.index.max().normalize(), freq='D')
        missing_days = all_days.difference(daily_df.index.normalize()).strftime('%Y-%m-%d').tolist()
        fig.update_xaxes(rangebreaks=[dict(values=missing_days)])

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
# ==========================================
# 🌀 局部渲染魔法：K線圖控制台 (主畫面不會閃爍！)
# ==========================================
@st.fragment
def render_kline_fragment(pure_stock_id):
    # 改用優雅的切換按鈕，取代需要 rerun 的 button
    show_kline = st.toggle("📊 展開技術 K 線圖", value=False)
    
    if show_kline and pure_stock_id != "":
        # 改用 radio button 切換週期，自然連動無須 rerun
        kline_period = st.radio("選擇週期", ["日線", "週線", "月線"], horizontal=True, label_visibility="collapsed")
        
        ind_c1, ind_c2, ind_c3 = st.columns(3)
        chk_kd = ind_c1.checkbox("KD", value=False)
        chk_macd = ind_c2.checkbox("MACD", value=False)
        chk_rsi = ind_c3.checkbox("RSI", value=False)
        
        with st.spinner("載入線圖中..."):
            all_mas = ["5MA", "10MA", "20MA", "60MA"]
            render_technical_chart(pure_stock_id, kline_period, all_mas, chk_rsi, chk_macd, chk_kd)

