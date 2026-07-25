import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import glob
import re
import datetime
import requests  
import pytz  
import math
import streamlit.components.v1 as components
import plotly.express as px
from components import style_manager
from components import nav_manager
# 定義修改路徑呼叫工具函式
from utils.data_utils import (
    STOCK_DICT, extract_date_from_name, robust_read_csv, get_latest_csv, get_prev_csv, get_diff_ui
)
# 頁面模組
from views.news_page import show_news_page
from views.contact_page import show_contact_page
from views.pool_page import show_pool_page

from views.b2_page import show_b2_page, sync_b2_data
from views.b3_page import show_b3_page, sync_b3_data
from views.b4_page import show_b4_page, sync_b4_data
from views.b5_page import show_b5_page, sync_b5_data
from views.b6_page import show_b6_page, sync_b6_data
# ==========================================
# 1. 網頁基本設定 & 目錄路徑初始化
# ==========================================
st.set_page_config(page_title="股市派對", layout="wide")
# 呼叫渲染視覺元件 components
style_manager.load_global_css()
style_manager.set_background("./image/派對盛宴邀請.png")
style_manager.render_fireflies()
style_manager.render_marquee()
# 注入客製化頂部導覽列
nav_manager.inject_custom_header()

# ==========================================
# 2. 啟動 Google Sheets 連線與目錄初始化
# ==========================================
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TxHDahg8ul6lmUtDN-7X75cBXbkU0jaZ3M9zg6exBgU"

# 集中所有路徑變數
DATA_DIR = "./data"

SCORE_HISTORY_DIR = os.path.join(DATA_DIR, "ScoreHistory")
MARKET_HISTORY_DIR = os.path.join(DATA_DIR, "MarketHistory")
BLOCK_HISTORY_DIR = os.path.join(DATA_DIR, "BlockHistory")
# 隱形急救引擎 (置於程式最頂端，不要刪除)
# 即使不顯示區塊 0 面板，這段程式碼也必須存在，否則側邊欄導航會因為讀不到歷史檔案而顯示「查無資料」。
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(SCORE_HISTORY_DIR): os.makedirs(SCORE_HISTORY_DIR)
if not os.path.exists(MARKET_HISTORY_DIR): os.makedirs(MARKET_HISTORY_DIR)
if not os.path.exists(BLOCK_HISTORY_DIR): os.makedirs(BLOCK_HISTORY_DIR)

# 定義路徑
backup_df_path = os.path.join(DATA_DIR, "sidebar_twse_df_backup.csv")
backup_margin_path = os.path.join(DATA_DIR, "sidebar_margin_backup.csv")

# 補法人備援
if not os.path.exists(backup_df_path):
    pd.DataFrame({
        '單位名稱': ['合計'], '買賣差額': ['102770738307']}).to_csv(backup_df_path, index=False, encoding='utf-8-sig')
# 補融資備援
if not os.path.exists(backup_margin_path):
    pd.DataFrame([{"today_bal": 556359646.0, "prev_bal": 535025764.0}]).to_csv(backup_margin_path, index=False, encoding='utf-8-sig')

# ==========================================
# 3. 網頁首頁路由控制中心 (極速切換引擎)-首頁設定
# ==========================================
current_page = st.query_params.get("page", "b1")

# 頁面渲染分流 (路由中心)
if current_page == "all":
    # 在觀察名單按下「全市場掃描」後觸發的背景引擎
    with st.spinner("🚀 背景全市場數據高速運算中..."):
        # b1_page.sync_b1_data(DATA_DIR) # 未來搬運 B1 後解除註解
        sync_b2_data(DATA_DIR)           # 在背景後台算好 b2
        sync_b3_data(DATA_DIR)
        sync_b4_data(DATA_DIR)
        sync_b5_data(DATA_DIR)
        sync_b6_data(DATA_DIR)
        # 算完後，把使用者自動傳送回觀察名單
        st.session_state.current_page = "pool"
        st.query_params["page"] = "pool"
        st.rerun()
# 頁面渲染分流
if current_page == "news":
    show_news_page()
elif current_page == "contact":
    show_contact_page(conn, SHEET_URL)
elif current_page == "pool":
    show_pool_page(conn, SHEET_URL, DATA_DIR, STOCK_DICT)
elif current_page == "b1":
    pass
elif current_page == "b2":
    show_b2_page(DATA_DIR)
elif current_page == "b3":
    show_b3_page(DATA_DIR)
elif current_page == "b4":
    show_b4_page(DATA_DIR)
elif current_page == "b5":
    show_b5_page(DATA_DIR, STOCK_DICT)
elif current_page == "b6":
    show_b6_page(DATA_DIR)

# ==========================================
# 🌟 所有"側邊雙視窗"專屬工具函數區 
# ==========================================
import streamlit as st
import pandas as pd
import requests
import re

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

# 🤖 [AI 籌碼訊號]新版判斷 (直接掃描全榜單)
def generate_stock_commentary(query):
    if not query: return ""
    
    score = 0
    warns = []
    b5_trend_400 = ""
    b5_trend_1000 = ""
    
    # 🎯 掃描 1: 法人買超診斷 (區塊2 - 共4個表)
    for key in ['df_blk2_1', 'df_blk2_2', 'df_blk2_3', 'df_blk2_4']:
        if key in st.session_state:
            res = robust_search_engine(st.session_state[key], query)
            if not res.empty:
                score += 1.5  # 出現在法人買超榜，每次加 1.5 分

    # 📅 掃描 2: 法人連買診斷 (區塊3)
    if 'df_blk3_main' in st.session_state:
        res = robust_search_engine(st.session_state['df_blk3_main'], query)
        if not res.empty:
            score += len(res) * 1.5  # 達成幾項連買條件就加幾次分

    # 🔄 掃描 3: 券資有利排名 (區塊4 - 共6個表)
    for key in ['df_margin_pct', 'df_short_pct', 'df_margin_plus_pct', 'df_margin_vol', 'df_short_vol', 'df_margin_plus_vol']:
        if key in st.session_state:
            res = robust_search_engine(st.session_state[key], query)
            if not res.empty:
                score += 0.5  # 券資籌碼權重較輕，每次加 0.5 分

    # 💰 掃描 4: 大戶動向診斷 (區塊5)
    def check_big_holder(key):
        if key in st.session_state:
            res = robust_search_engine(st.session_state[key], query)
            if not res.empty:
                # 模糊抓取動向欄位 (因為欄位名可能是'大股東動向'或'狀態動態')
                for col in res.columns:
                    if "動向" in col or "狀態" in col or "趨勢" in col or "動態" in col:
                        return str(res.iloc[0][col])
        return ""

    b5_trend_400 = check_big_holder('b5_400')
    if "增" in b5_trend_400: score += 2
    elif "減" in b5_trend_400: 
        score -= 2
        warns.append("400張大戶減碼")

    b5_trend_1000 = check_big_holder('b5_1000')
    if "增" in b5_trend_1000: score += 2
    elif "減" in b5_trend_1000: 
        score -= 2
        warns.append("千張超級大戶減碼")

    # 💡 綜合判定邏輯
    has_warning = len(warns) > 0
    warn_str = "、".join(warns)
    high_score = score >= 4
    
    if has_warning and high_score:
        return f"⚔️ 【激烈換手】系統偵測到法人與大戶分歧 ({warn_str})，但籌碼動能依然獲 {score} 分的高評估！代表『倒貨正被強勢吃下』。若能維持強勢，承接方實力極強，需嚴設停損。"
    if has_warning and not high_score:
        return f"🚨 【風險警示】大戶正在進行倒貨調節 ({warn_str})，且無強大買盤承接，籌碼結構面臨鬆動。建議暫避風頭。"
    if "大減" in b5_trend_400 or "大減" in b5_trend_1000:
        return "⚠️ 【大戶撤退】大戶出現明顯『大減』跡象，主力籌碼渙散，建議先行觀望。"
    if score >= 6:
        base_comment = f"🔥 【強勢噴發】籌碼面極度優異 (積分: {score})！多個法人與大戶榜單同步共振做多，具備強大的波段上攻潛力。"
        if "大增" in b5_trend_400 or "大增" in b5_trend_1000: base_comment += " 大股東籌碼大幅集中，是極佳的防守標的。"
        return base_comment
    elif score >= 3: 
        return f"📈 【偏多佈局】主力籌碼持續進駐 (積分: {score})，法人與券資數據給予支撐。具備穩健的波段潛力。"
    elif score >= 1: 
        return f"🔄 【中性觀望】籌碼表現較為平淡 (積分: {score})，雖有零星榜單出現，但缺乏明確連續性。建議多看少做。"
    else: 
        return "❄️ 【弱勢整理】目前未進入任何核心法人與大戶買超榜單，籌碼處於流失或無主力認養狀態。建議暫不考量。"

# 🤖  [ AI 技術型態訊號]判斷 (從 K 線抽離出來)
def generate_technical_signals(df_sig):
    signals = []
    if df_sig is None or df_sig.empty or len(df_sig) < 20: return signals
    latest_close = df_sig['Close'].iloc[-1]
    latest_vol = df_sig['Volume'].iloc[-1]
    
    vol_20ma = df_sig['Volume'].rolling(window=20).mean().iloc[-2] 
    if pd.notna(vol_20ma) and vol_20ma > 0 and latest_vol > (vol_20ma * 2.5):
        signals.append(f"🧨 爆量出擊：今日成交量達 20 日均量的 {latest_vol/vol_20ma:.1f} 倍！")

    mas = {'5MA': 5, '10MA': 10, '20MA': 20, '60MA': 60, '120MA': 120, '240MA': 240}
    for ma_name, period in mas.items():
        if len(df_sig) >= period:
            ma_val = df_sig['Close'].rolling(window=period).mean().iloc[-1]
            if 0 < (latest_close - ma_val) / ma_val < 0.015:
                signals.append(f"🎯 回測支撐：股價目前極度貼近 {ma_name} ({ma_val:.2f}) 關鍵支撐線。")

    if len(df_sig) >= 60:
        highest_60d = df_sig['High'].iloc[-60:].max()
        if df_sig['High'].iloc[-1] >= highest_60d:
            signals.append("🚀 波段創高：今日股價突破 60 日 (約一季) 以來新高點，上攻動能極強！")
    return signals
    
def render_b4_panorama(view_title, keys_and_labels, query):
    display_list = []
    display_id, display_name = query, "-"
    for label, key in keys_and_labels:
        if key in st.session_state:
            res = robust_search_engine(st.session_state[key], query)
            if not res.empty:
                display_id = res.iloc[0].get('股票代號', query)
                display_name = res.iloc[0].get('股票名稱', '-')
                break
                
    for label, key in keys_and_labels:
        if key in st.session_state:
            res = robust_search_engine(st.session_state[key], query)
            if not res.empty:
                row_data = res.iloc[0].to_dict()
                new_row = {'榜單類型': label}; new_row.update(row_data); display_list.append(new_row)
            else: display_list.append({'榜單類型': label, '股票代號': display_id, '股票名稱': display_name, '進榜狀態': '⚪ 未進榜'})
        else: display_list.append({'榜單類型': label, '股票代號': display_id, '股票名稱': display_name, '進榜狀態': '⚠️ 尚未載入'})
            
    df_panorama = pd.DataFrame(display_list).fillna('-')
    front_cols = ['榜單類型', '股票代號', '股票名稱', '進榜狀態']
    data_cols = [c for c in df_panorama.columns if c not in front_cols]
    final_cols = [c for c in front_cols if c in df_panorama.columns] + data_cols
    for c in final_cols: df_panorama[c] = df_panorama[c].apply(lambda x: str(x)[:-2] if str(x).endswith('.0') else x)
    
    st.markdown(f"<h5 style='color: #E2E8F0;'>{view_title}</h5>", unsafe_allow_html=True)
    st.dataframe(df_panorama[final_cols], use_container_width=True, hide_index=True)
  #以上核對完畢
    
# ==========================================
# 📈 側邊雙視窗 K 線圖與技術分析引擎 (整合版)
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
            
    # --- 週期處理與指標計算 ---
    if timeframe == "週線":
        daily_df = daily_df.resample('W-FRI').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()
    elif timeframe == "月線":
        daily_df = daily_df.resample('ME').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

    for ma in [5, 10, 20, 60, 120, 240]:
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

    def get_latest_price(col):
        valid_data = daily_df[col].dropna()
        if not valid_data.empty:
            val = valid_data.iloc[-1]
            if isinstance(val, pd.Series): val = val.iloc[0]
            return f"{float(val):.2f}"
        return "-"
   # --- Plotly 繪圖區 (⚠️ 全部移除 squeeze 確保型別正確) ---
    rows = 2
    row_heights = [0.5, 0.15]
    if show_rsi: rows += 1; row_heights.append(0.12)
    if show_macd: rows += 1; row_heights.append(0.14)
    if show_kd: rows += 1; row_heights.append(0.14)

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=row_heights)
                                        
    up_color = 'rgb(240, 90, 90)'     
    down_color = 'rgb(80, 200, 120)'  

    fig.add_trace(go.Candlestick(
        x=daily_df.index, open=daily_df['Open'], high=daily_df['High'], 
        low=daily_df['Low'], close=daily_df['Close'], name='K線', 
        increasing=dict(line=dict(color=up_color, width=1.5), fillcolor=up_color),
        decreasing=dict(line=dict(color=down_color, width=1.5), fillcolor=down_color),
        hovertemplate="開：%{open:.2f}<br>高：%{high:.2f}<br>低：%{low:.2f}<br>收：%{close:.2f}<extra></extra>"
    ), row=1, col=1)
    
    fig.update_yaxes(title_text="股價 (TWD)", row=1, col=1, title_font=dict(size=12, color="#E2E8F0"), rangemode="nonnegative")

    if not daily_df.empty:
        max_price = daily_df['High'].max()
        max_date = daily_df['High'].idxmax()
        fig.add_hline(y=max_price, line_dash="dot", line_color="rgba(255, 215, 0, 0.4)", row=1, col=1)
        fig.add_annotation(
            x=max_date, y=max_price, text=f"<b>前高: {max_price:.2f}</b>",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor="#FFD700", ax=0, ay=-40, 
            font=dict(size=13, color="#FFD700"), bgcolor="rgba(17, 22, 34, 0.85)", bordercolor="#FFD700", borderwidth=1, borderpad=4, row=1, col=1
        )

    ma_config = {
        '5MA': {'color': '#FFFF37'}, '10MA': {'color': '#00FFFF'},
        '20MA': {'color': '#921AFF'}, '60MA': {'color': '#D0D0D0'},
        '120MA': {'color': '#D200D2'}, '240MA': {'color': '#BB3D00'}
    }
    for ma_name in selected_mas:
        if ma_name in daily_df.columns:
            latest_val = get_latest_price(ma_name)
            fig.add_trace(go.Scatter(
                x=daily_df.index, y=daily_df[ma_name], mode='lines', 
                name=f'{ma_name} ({latest_val})', line=dict(color=ma_config[ma_name]['color'], width=1.3),
                hovertemplate=f"<b>{ma_name}</b>： %{{y:.2f}}<extra></extra>"
            ), row=1, col=1)

    vol_colors = [up_color if c >= o else down_color for c, o in zip(daily_df['Close'], daily_df['Open'])]
    fig.add_trace(go.Bar(
        x=daily_df.index, y=daily_df['Volume'], name='成交量', 
        marker_color=vol_colors, showlegend=False, hovertemplate="<b>成交量</b>： %{y}<extra></extra>"
    ), row=2, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1, title_font=dict(size=12, color="#E2E8F0"), rangemode="nonnegative")

    current_row = 3
    if show_kd:
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['K'], mode='lines', name='K (9)', line=dict(color='#00CCFF', width=1.2), hovertemplate="<b>K</b>: %{y:.2f}<extra></extra>"), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['D'], mode='lines', name='D (3)', line=dict(color='#FFCC00', width=1.2), hovertemplate="<b>D</b>: %{y:.2f}<extra></extra>"), row=current_row, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="rgba(240,90,90,0.4)", row=current_row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="rgba(80,200,120,0.4)", row=current_row, col=1)
        fig.update_yaxes(title_text="KD(9,3,3)", row=current_row, col=1, title_font=dict(size=11, color="#E2E8F0"))
        current_row += 1
        
    if show_rsi:
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['RSI'], mode='lines', name='RSI (14)', line=dict(color='#E1BEE7', width=1.5), hovertemplate="<b>RSI</b>: %{y:.2f}<extra></extra>"), row=current_row, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="rgba(240,90,90,0.4)", row=current_row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="rgba(80,200,120,0.4)", row=current_row, col=1)
        fig.update_yaxes(title_text="RSI(14)", row=current_row, col=1, title_font=dict(size=11, color="#E2E8F0"))
        current_row += 1

    if show_macd:
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['DIF'], mode='lines', name='DIF', line=dict(color='#FFF', width=1)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['MACD_Sign'], mode='lines', name='MACD', line=dict(color='#FFCC00', width=1)), row=current_row, col=1)
        hist_colors = [up_color if h >= 0 else down_color for h in daily_df['MACD_Hist']]
        fig.add_trace(go.Bar(x=daily_df.index, y=daily_df['MACD_Hist'], name='柱狀圖', marker_color=hist_colors), row=current_row, col=1)
        fig.update_yaxes(title_text="MACD", row=current_row, col=1, title_font=dict(size=11, color="#E2E8F0"))
        current_row += 1

    fig.update_layout(
        xaxis_rangeslider_visible=False, height=500 + (rows - 1) * 110, 
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',  
        margin=dict(l=10, r=65, t=30, b=10), hovermode='x unified',
        hoverlabel=dict(bgcolor="#1A202C", font_size=15, font_color="#FFFFFF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.01, font=dict(color='#E2E8F0', size=16), itemsizing='constant'),
        dragmode='pan' 
    )
    
    fig.update_xaxes(showspikes=True, spikecolor="rgba(255, 235, 100, 0.5)", spikesnap="cursor", spikemode="across", spikethickness=0.5, spikedash="dash", gridcolor="rgba(255, 255, 255, 0.05)")
    fig.update_yaxes(showspikes=True, spikecolor="rgba(255, 235, 100, 0.5)", spikesnap="cursor", spikemode="across", spikethickness=0.5, spikedash="dash", side="right", gridcolor="rgba(255, 255, 255, 0.05)")
    
    for r in range(1, rows + 1): fig.update_xaxes(hoverformat="%Y-%m-%d", tickformat="%Y-%m-%d", row=r, col=1)
    
    if not daily_df.empty:
        latest_date = daily_df.index[-1] 
        start_date = latest_date - pd.Timedelta(days=140) 
        zoom_range = [start_date.strftime('%Y-%m-%d'), latest_date.strftime('%Y-%m-%d')]
        for r in range(1, rows + 1): fig.update_xaxes(range=zoom_range, row=r, col=1)
    
    if timeframe == "日線":
        all_days = pd.date_range(start=daily_df.index.min().normalize(), end=daily_df.index.max().normalize(), freq='D')
        actual_days = daily_df.index.normalize()
        missing_days = all_days.difference(actual_days).strftime('%Y-%m-%d').tolist()
        for r in range(1, rows + 1): fig.update_xaxes(rangebreaks=[dict(values=missing_days)], row=r, col=1)
    
    plotly_config = {'scrollZoom': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'select2d', 'lasso2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines']}
    st.plotly_chart(fig, use_container_width=True, key=f"kline_{stock_id}_{timeframe}_{len(selected_mas)}_{show_rsi}_{show_macd}_{show_kd}", config=plotly_config)

#======================================================
#分頁功能渲染區:🔹 大盤籌碼🔹 選擇權🔹 總經導航(以下核對完畢)
#======================================================
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
#分頁3
# ======================================================
# 分頁3 - 總經導航 (🚀 終極正則表達式 - 網頁暴力拆解版)
# ======================================================



@st.cache_data(ttl=300) 
def fetch_macro_indicators():
    import requests
    import re
    
    data = {
        "vix": {"value": None, "pct": None},
        "vixtwn": {"value": None, "pct": None},
        "fng": {"score": None, "rating": "無法取得"}
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }

    # --- 1. 🇺🇸 美股 VIX (^VIX) - Yahoo 原生 API ---
    try:
        yf_url = "https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d"
        res_us = requests.get(yf_url, headers=headers, timeout=5)
        if res_us.status_code == 200:
            us_json = res_us.json()
            closes = us_json['chart']['result'][0]['indicators']['quote'][0]['close']
            valid_closes = [c for c in closes if c is not None]
            if len(valid_closes) >= 2:
                latest = float(valid_closes[-1])
                prev = float(valid_closes[-2])
                data["vix"]["value"] = latest
                data["vix"]["pct"] = (latest - prev) / prev * 100
    except: pass

    # --- 2. 🇹🇼 台股 VIX (VIXTWN) - 暴力拆解官方網頁 ---
    prev_vix = None
    
    # 🌟 策略 A: 先拆解「每日 VIX」網頁，目的是為了拿到昨天的收盤價來算漲跌幅
    try:
        res_daily = requests.get("https://www.taifex.com.tw/cht/3/vixInfo", headers=headers, timeout=5)
        if res_daily.status_code == 200:
            # 正規表達式：尋找「日期 (如 113/07/21)」+「中間任意字元」+「數值 (如 35.54)」
            matches_d = re.findall(r'(\d{3,4}/\d{2}/\d{2})[\s\S]{1,100}?([1-9]\d{1,2}\.\d{2,4})', res_daily.text)
            if matches_d:
                data["vixtwn"]["value"] = float(matches_d[-1][1])
                if len(matches_d) >= 2:
                    prev_vix = float(matches_d[-2][1])
                    data["vixtwn"]["pct"] = (data["vixtwn"]["value"] - prev_vix) / prev_vix * 100
    except: pass

    # 🌟 策略 B: 再拆解「盤中每分鐘 VIX」網頁，取得當下最新報價直接覆蓋
    try:
        res_min = requests.get("https://www.taifex.com.tw/cht/7/vixMinNew", headers=headers, timeout=5)
        if res_min.status_code == 200:
            # 正規表達式：尋找「時間 (如 13:45:00)」+「中間任意字元」+「數值 (如 35.54)」
            matches_m = re.findall(r'(\d{2}:\d{2}:\d{2})[\s\S]{1,100}?([1-9]\d{1,2}\.\d{2,4})', res_min.text)
            if matches_m:
                latest_vix = float(matches_m[-1][1])
                data["vixtwn"]["value"] = latest_vix
                # 結合策略 A 拿到的昨收，算出精準的即時漲跌幅
                if prev_vix:
                    data["vixtwn"]["pct"] = (latest_vix - prev_vix) / prev_vix * 100
    except: pass

    # 🌟 策略 C: HiStock 備援 (若期交所網頁維修時自動啟動)
    if data["vixtwn"]["value"] is None:
        try:
            res_hi = requests.get("https://histock.tw/stock/tcharti.aspx?no=VIXTWN", headers=headers, timeout=5)
            if res_hi.status_code == 200:
                match = re.search(r'CPHB1_lblPrice[^>]*>\s*([\d\.]+)\s*<', res_hi.text)
                if match:
                    data["vixtwn"]["value"] = float(match.group(1))
                    data["vixtwn"]["pct"] = 0.0
        except: pass


    # --- 3. CNN 恐懼貪婪指數 ---
    try:
        headers_cnn = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
            "Referer": "https://edition.cnn.com/"
        }
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        res = requests.get(url, headers=headers_cnn, timeout=5)
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
# =======================================================
# 🚀 終極局部渲染魔法：將整個側邊視窗獨立為「不閃爍區塊」(以下核對完畢)
# =======================================================
@st.fragment
def render_sidebar_war_room():
    st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)

    # 🌟 使用 100% 絕對生效的 Inline HTML 設計超高質感橫幅
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 20px 20px; 
                border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 25px;">
        <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
            🔍 個股籌碼快搜
        </h2>
        <p style="color: #94a3b8; margin-top: 8px; font-size: 14px; margin-bottom: 0;">一起看看K線吧</p>
    </div>
    """, unsafe_allow_html=True)

# 使用預設的帶邊框容器把圖表和表格包起來
    with st.container(border=True):
        
        # =================
        # 🎯 搜尋輸入框
        # =================
        def clear_search():
            st.session_state['global_search_final'] = ""

        st.markdown("<div style='font-size: 14px; color: #E2E8F0; margin-bottom: 5px; font-weight: bold;'>輸入 代號 或 名稱 或 代號+名稱 ：</div>", unsafe_allow_html=True)
        
        c_search, c_btn_go, c_btn_clear = st.columns([6, 1.5, 1.5])
        
        with c_search:
            search_query = st.text_input(
                "搜尋標的", 
                key="global_search_final", 
                label_visibility="collapsed", 
                placeholder="點此輸入..."
            )
        
        with c_btn_go:
            # 🚀 加入按鈕：拔除底色與邊框
            st.button("→", key="btn_go", type="tertiary", use_container_width=True, help="送出搜尋")
            
        with c_btn_clear:
            # 🚀 修正按鈕：加入 type="tertiary" 拔除底色與邊框
            st.button("×", key="btn_clear", type="tertiary", on_click=clear_search, use_container_width=True, help="清空欄位")

        pure_stock_id = ""
        display_name = search_query
        
        # 以下保留你原本的 pure_stock_id 解析邏輯與排版
        if search_query:
            query_clean = search_query.strip()
            industry_label = "未分類"
            
            if 'STOCK_DICT' in locals() or 'STOCK_DICT' in globals():
                if query_clean in STOCK_DICT:
                    pure_stock_id = STOCK_DICT[query_clean]["id"]
                    display_name = f"{STOCK_DICT[query_clean]['id']} {STOCK_DICT[query_clean]['name']}"
                    industry_label = STOCK_DICT[query_clean]["industry"]
                else:
                    for k, v in STOCK_DICT.items():
                        if query_clean in k:
                            pure_stock_id = v["id"]
                            display_name = f"{v['id']} {v['name']}"
                            industry_label = v["industry"]
                            break
            
            if pure_stock_id == "":
                import re
                match_num = re.search(r'\d+', query_clean)
                if match_num: pure_stock_id = match_num.group(0)
#這裡原本有系統綜合假評分
            st.markdown(f"### 🎯 綜合診斷標的：<span style='color: #00D2FF;'>{display_name}</span> <span style='font-size:16px; background-color:#1E293B; padding:4px 10px; border-radius:6px; color:#38BDF8; border: 1px solid #38BDF8; margin-left:10px;'>🏷️ {industry_label}</span>", unsafe_allow_html=True)

            # ==========================================
            # 🚀 融合 AI 訊號區 (拔除對評分的依賴，直接搜尋即可顯示)
            # ==========================================
            # 1. 綜合掃描各區塊資料庫，動態計算籌碼 AI 訊號 (修改為generate_stock commentary)
            target_query = pure_stock_id if pure_stock_id else search_query
            old_ai_msg = generate_stock_commentary(target_query)

            # 2. 自動抓取最新 K 線計算技術訊號
            new_ai_msgs = []
            if pure_stock_id:
                with st.spinner("🧠 AI 雷達掃描中..."):
                    df_tech = fetch_yfinance_data(f"{pure_stock_id}.TW", period="1y")
                    if df_tech is None or df_tech.empty:
                        df_tech = fetch_yfinance_data(f"{pure_stock_id}.TWO", period="1y")
                    
                    if df_tech is not None and not df_tech.empty:
                        if isinstance(df_tech.columns, pd.MultiIndex):
                            df_tech.columns = df_tech.columns.get_level_values(0)
                        df_tech = df_tech.loc[:, ~df_tech.columns.duplicated()]
                        new_ai_msgs = generate_technical_signals(df_tech)

            # 3. 完美組合並顯示兩版 AI 訊號
            if old_ai_msg or new_ai_msgs:
                signal_html = "<div style='background-color: rgba(0, 210, 255, 0.05); border-left: 4px solid #00D2FF; padding: 12px; border-radius: 5px; margin: 10px 0px;'>"
                signal_html += "<h5 style='color: #00D2FF; margin-top:0px; margin-bottom: 10px;'>📡 AI 綜合籌碼與技術雷達</h5>"
                
                if old_ai_msg:
                    signal_html += f"<p style='color: #FCD34D; margin: 5px 0px; font-size: 15px; font-weight: bold;'>{old_ai_msg}</p>"
                
                if old_ai_msg and new_ai_msgs:
                    signal_html += "<hr style='border-color: rgba(0, 210, 255, 0.15); margin: 8px 0px;'>"
                    
                if new_ai_msgs:
                    for sig in new_ai_msgs:
                        signal_html += f"<p style='color: #E2E8F0; margin: 5px 0px; font-size: 14.5px;'>{sig}</p>"
                    
                signal_html += "</div>"
                st.markdown(signal_html, unsafe_allow_html=True)
            elif pure_stock_id:
                st.info("📡 AI 雷達：目前尚無強烈技術或籌碼訊號。")

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
#這裡原本有系統綜合假評分
            # ==========================================
            # 📊 K 線控制台 (利用 Fragment 特性，無須 rerun)
            # ==========================================
            show_kline = st.toggle("📊 展開技術 K 線圖 (雙擊縮放)", value=st.session_state.get('show_kline', False), key="toggle_kline")
            st.session_state.show_kline = show_kline

            if show_kline:
                if 'pure_stock_id' in locals() and pure_stock_id != "":          
                    st.markdown("##### 技術線圖與指標配置面板")
                    
                    kline_period = st.radio("選擇週期", ["日線", "週線", "月線"], horizontal=True, label_visibility="collapsed", key="kline_radio_period")
                    
                    ind_c1, ind_c2, ind_c3 = st.columns(3)
                    chk_kd = ind_c1.checkbox("顯示 KD (9,3,3)", value=False, key="kd_chk")
                    chk_macd = ind_c2.checkbox("顯示 MACD (12,26,9)", value=False, key="macd_chk")
                    chk_rsi = ind_c3.checkbox("顯示 RSI (14)", value=False, key="rsi_chk")
                    st.write("") 
                    
                    with st.spinner(f"正在擷取 {pure_stock_id} 的最新數據..."):
                        all_mas = ["5MA", "10MA", "20MA", "60MA", "120MA", "240MA"]
                        render_technical_chart(pure_stock_id, kline_period, all_mas, chk_rsi, chk_macd, chk_kd)
                else:
                    st.warning("⚠️ 技術 K 線圖目前僅支援代號查詢。")
            #顯示在側欄搜尋股票或標的的各區塊資訊-法人動向
            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>👑 區塊 1：短中長線三大法人持股變化</h4>", unsafe_allow_html=True)
            
            if 'my_final_df' in st.session_state:
                df_b1 = st.session_state['my_final_df']
                res_b1 = robust_search_engine(df_b1, search_query)
                
                if not res_b1.empty:
                    date_cols = [c for c in res_b1.columns if '持股%' in c or c.isdigit()]
                    is_all_unranked = True
                    for c in date_cols:
                        val = str(res_b1.iloc[0][c]).strip()
                        if val != "未進榜" and val not in ['0', '0.0', 'nan', '-']:
                            is_all_unranked = False
                            break
                            
                    if is_all_unranked:
                        st.write("⚪ 未進榜")
                    else:
                        hide_keywords = ['_區塊', '排序', '上榜數量', '原始上榜', '精準單日']
                        clean_cols = [c for c in res_b1.columns if not any(k in c for k in hide_keywords)]
                        st.dataframe(res_b1[clean_cols], use_container_width=True, hide_index=True)
                        
                        row = res_b1.iloc[0]
                        stock_name = row.get('股票名稱', search_query)
                        raw_x_vals = date_cols[::-1]
                        clean_x_labels = [c.replace('持股%', '')[-4:] for c in raw_x_vals]
                        
                        y_vals = []
                        for c in raw_x_vals:
                            val = row[c]
                            if str(val) == "未進榜" or pd.isna(val): y_vals.append(0.0)
                            else:
                                try: y_vals.append(float(val))
                                except: y_vals.append(0.0)
                                    
                        import plotly.graph_objects as go
                        fig_b1 = go.Figure()
                        fig_b1.add_trace(go.Bar(
                            x=clean_x_labels, y=y_vals,  
                            marker_color=['#FF4B4B' if i == len(y_vals)-1 else '#4B8BFF' for i in range(len(y_vals))],
                            text=[f"{v}%" if v > 0 else "" for v in y_vals], textposition='outside'
                        ))
                        fig_b1.update_layout(
                            title=dict(text=f"📈 持股波段真實軌跡 ({stock_name})", font=dict(color="#E2E8F0")),
                            height=300, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(l=20, r=20, t=40, b=20),
                            yaxis=dict(title="持股比例 (%)", showgrid=True, gridcolor='#334155'), xaxis=dict(tickangle=45), dragmode='pan'
                        )
                        st.plotly_chart(fig_b1, use_container_width=True, config={'displayModeBar': False})
                else: st.write("⚪ 未進榜")
            else: st.info("⚪ 尚未載入資料表")
            #顯示在側欄搜尋股票或標的的各區塊資訊-法人掃貨
            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>🎯 區塊 2：法人買超診斷</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: scan_and_display("🌐 外資 5 日淨買佔成交量", 'df_blk2_1', search_query)
            with c2: scan_and_display("🏦 投信 5 日淨買佔成交量", 'df_blk2_2', search_query)
            c3, c4 = st.columns(2)
            with c3: scan_and_display("🌐 外資 5 日淨買佔發行量", 'df_blk2_3', search_query)
            with c4: scan_and_display("🏦 投信 5 日淨買佔發行量", 'df_blk2_4', search_query)

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>📅 區塊 3：法人連買診斷 (日/週)</h4>", unsafe_allow_html=True)
            if 'df_blk3_main' in st.session_state:
                df_b3 = st.session_state['df_blk3_main']
                res_b3 = robust_search_engine(df_b3, search_query)
                display_id = res_b3.iloc[0]['股票代號'] if not res_b3.empty else search_query
                display_name = res_b3.iloc[0]['股票名稱'] if not res_b3.empty else "-"
                
                base_types = ['🌐 外資日連買', '🌐 外資週連買', '🏦 投信日連買', '🏦 投信週連買']
                display_list = []
                for b_type in base_types:
                    match = res_b3[res_b3['連買類型'] == b_type] if not res_b3.empty else pd.DataFrame()
                    if not match.empty: display_list.append(match.iloc[0].to_dict())
                    else: display_list.append({'連買類型': b_type, '股票代號': display_id, '股票名稱': display_name, '狀態動態': '⚪ 未進榜', '連買週期數': '-'})
                st.dataframe(pd.DataFrame(display_list), use_container_width=True, hide_index=True)
            else: st.info("⚪ 區塊 3：尚未載入資料表")
            #顯示在側欄搜尋股票或標的的各區塊資訊-券資動向
            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>🔄 區塊 4：券資有利排名</h4>", unsafe_allow_html=True)
            
            render_b4_panorama("5日幅度變動排名", [('📉 融資減少', 'df_margin_pct'), ('📉 借券減少', 'df_short_pct'), ('📈 融券增加', 'df_margin_plus_pct')], search_query)
            st.write("") 
            render_b4_panorama("5日張數變動排名", [('📉 融資減少', 'df_margin_vol'), ('📉 借券減少', 'df_short_vol'), ('📈 融券增加', 'df_margin_plus_vol')], search_query)
            #顯示在側欄搜尋股票或標的的各區塊資訊-大腿動向
            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>💰 區塊 5：大腿動向</h4>", unsafe_allow_html=True)
            
            col_400, col_1000 = st.columns(2)
            with col_400: scan_and_display("💎 400張以上大戶動向", 'b5_400', search_query)
            with col_1000: scan_and_display("🐳 1000張以上超級大戶動向", 'b5_1000', search_query)

    # 💡 當搜尋列「沒有內容」時，顯示大盤總經 (隱藏下方 Tabs)
    if not search_query:
        st.write("---") # 側邊欄快搜與三大導航 Tab 的分隔線
        tab1, tab2, tab3 = st.tabs(["🔹 大盤籌碼", "🔹 選擇權", "🔹 總經導航🛠️"])
        
        with tab1:
            actual_data_date = render_sidebar_market_summary()
            
        with tab2:
            render_options_dashboard()
            
        with tab3:
            macro_data = fetch_macro_indicators()
            
            vix_val = macro_data["vix"]["value"]
            vix_color = "#a1a1aa" 
            if vix_val is not None:
                if vix_val < 20: vix_color = "#10b981" 
                elif vix_val < 28.7: vix_color = "#3b82f6" 
                elif vix_val < 33.5: vix_color = "#f59e0b" 
                else: vix_color = "#ef4444" 
            vix_tooltip = f"VIX 市場恐慌指標\n目前 VIX： {vix_val if vix_val else '無'}\n綠色：市場平穩。\n藍色：報酬較差。\n橘色：報酬達 15%。\n紅色：報酬達 25%。"

            vixtwn_val = macro_data["vixtwn"]["value"]
            vixtwn_color = "#a1a1aa"
            if vixtwn_val is not None:
                if vixtwn_val < 20: vixtwn_color = "#3b82f6" 
                elif vixtwn_val < 30: vixtwn_color = "#10b981" 
                elif vixtwn_val < 40: vixtwn_color = "#f59e0b" 
                else: vixtwn_color = "#ef4444" 
            vixtwn_tooltip = f"VIXTWN 台灣恐慌指標\n目前： {vixtwn_val if vixtwn_val else '無'}\n藍：多頭常態。\n綠：波動加劇。\n橘：恐慌殺盤布局。\n紅：極度恐慌買點。"

            fng_val = macro_data["fng"]["score"]
            fng_color = "#a1a1aa"
            if fng_val is not None:
                if fng_val < 25: fng_color = "#ef4444" 
                elif fng_val > 75: fng_color = "#10b981" 
                else: fng_color = "#f59e0b" 
            fng_tooltip = f"FNG 恐懼貪婪指數\n目前： {fng_val if fng_val else '無'}\n<25 積極買點\n<15 分批加碼\n>75 分批減碼\n>85 獲利了結\n>90 提高現金"

            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                v1_str = f"{vix_val:.2f}" if vix_val else "無資料"
                p1_str = f"{'+' if macro_data['vix']['pct'] and macro_data['vix']['pct'] > 0 else ''}{macro_data['vix']['pct']:.2f}%" if macro_data['vix']['pct'] is not None else "-"
                st.markdown(f"""
                <div title="{vix_tooltip}" style="background-color: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); text-align: center; cursor: help; margin-bottom: 10px;">
                    <div style="font-size: 13px; color: #a1a1aa; margin-bottom: 4px;">🇺🇸 美股 VIX</div>
                    <div style="font-size: 22px; font-weight: 700; color: {vix_color}; margin-bottom: 2px;">{v1_str}</div>
                    <div style="font-size: 12px; color: #71717a;">{p1_str}</div>
                </div>
                """, unsafe_allow_html=True)
                
                v2_str = f"{vixtwn_val:.2f}" if vixtwn_val else "無資料"
                p2_str = "最新數值" if vixtwn_val else "-"
                st.markdown(f"""
                <div title="{vixtwn_tooltip}" style="background-color: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); text-align: center; cursor: help;">
                    <div style="font-size: 13px; color: #a1a1aa; margin-bottom: 4px;">🇹🇼 台股 VIX</div>
                    <div style="font-size: 22px; font-weight: 700; color: {vixtwn_color}; margin-bottom: 2px;">{v2_str}</div>
                    <div style="font-size: 12px; color: #71717a;">{p2_str}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_right:
                f_str = str(fng_val) if fng_val else "無資料"
                f_rating = macro_data["fng"]["rating"]
                st.markdown(f"""
                <div title="{fng_tooltip}" style="background-color: rgba(255,255,255,0.03); padding: 12px; height: calc(100% - 24px); display: flex; flex-direction: column; justify-content: center; align-items: center; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); text-align: center; cursor: help;">
                    <div style="font-size: 15px; color: #a1a1aa; margin-bottom: 15px;">恐懼與貪婪</div>
                    <div style="font-size: 36px; font-weight: 700; color: {fng_color}; margin-bottom: 10px;">{f_str}</div>
                    <div style="font-size: 14px; font-weight: 600; color: {fng_color};">{f_rating}</div>
                </div>
                """, unsafe_allow_html=True)

# =======================================================
# 實際呼叫 按鈕 "呼叫側邊欄" 雙視窗指令
# =======================================================
with st.sidebar:
    render_sidebar_war_room()

# ==========================================
# 🏠 核心五大區塊
# ==========================================
# ==========================================
# 🌟 "區塊 1 法人動向"專屬工具函數與背景預載引擎
# ==========================================
from collections import defaultdict

@st.cache_data(ttl=3600)
def load_foreign_ratio_data(data_dir="./data"):
    """
    掃描資料夾中所有外資持股比例的 CSV 檔案。
    會自動將同一天(如1-300, 301-600)的檔案先垂直合併，再將不同日期的數據水平合併。
    """
    foreign_csvs = glob.glob(os.path.join(data_dir, "*外資持股比例*.csv"))
    
    if not foreign_csvs:
        return pd.DataFrame()
        
    # 1. 根據日期將檔案分組 (例如 '20260627': [檔案1, 檔案2...])
    files_by_date = defaultdict(list)
    for f in foreign_csvs:
        date_match = re.search(r'(202\d{5})', os.path.basename(f))
        if date_match:
            files_by_date[date_match.group(1)].append(f)
            
    daily_dfs = []
    
    # 2. 將同一天的所有排名檔案「上下垂直合併」(Concat)
    for date_str, files in files_by_date.items():
        chunks = []
        for f in files:
            try:
                temp_df = pd.read_csv(f)
                temp_df.columns = temp_df.columns.str.replace(r'\s+', '', regex=True)
                cols_to_keep = ['代號', '名稱', '外資持股(%)']
                temp_df = temp_df[[c for c in cols_to_keep if c in temp_df.columns]]
                chunks.append(temp_df)
            except Exception as e:
                pass # 忽略毀損檔案
                
        if chunks:
            # 垂直合併拼成一天的完整表
            day_df = pd.concat(chunks, ignore_index=True)
            day_df['代號'] = day_df['代號'].astype(str).str.strip()
            # 移除可能重複爬取的股票代號
            day_df = day_df.drop_duplicates(subset=['代號'])
            
            day_df = day_df.rename(columns={
                '代號': '股票代號',
                '名稱': '股票名稱',
                '外資持股(%)': f'外資持股_{date_str}'
            })
            # 丟棄股票名稱，以免後續左右合併時產生大量重複的 名稱_x, 名稱_y
            day_df = day_df.drop(columns=['股票名稱'], errors='ignore')
            daily_dfs.append(day_df)

    if not daily_dfs:
        return pd.DataFrame()

    # 3. 將不同日期的完整日表「左右水平合併」(Merge)
    final_foreign_df = daily_dfs[0]
    for i in range(1, len(daily_dfs)):
        final_foreign_df = pd.merge(final_foreign_df, daily_dfs[i], on='股票代號', how='outer')
        
    # 將遺失的數值填為 0
    final_foreign_df = final_foreign_df.fillna(0.0)
    
    return final_foreign_df

    # ======== 以上外資持股 ========



@st.cache_data(ttl=600)
def fetch_github_json_all():
    days_list = [5, 20, 60, 120]
    json_dfs = {}
    account, repo, branch = "goodinfo3583", "DDong_tw-institutional-stocker", "main"
    
    for d in days_list:
        url = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/top_three_inst_change_{d}_up.json"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                df['股票代號'] = df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                df['股票名稱'] = df['name'].astype(str).str.strip()
                df = df.rename(columns={'three_inst_ratio': '法人持股', 'change': f'{d}日ΔChange'})
                df[f'{d}日排名'] = (df.index + 1).astype(int) 
                json_dfs[d] = df[['股票代號', '股票名稱', '法人持股', f'{d}日ΔChange', f'{d}日排名']]
            else: json_dfs[d] = pd.DataFrame()
        except Exception: json_dfs[d] = pd.DataFrame()
        
    latest_all_df = pd.DataFrame()
    try:
        url_all = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/stock_three_inst_latest.json"
        res_all = requests.get(url_all, timeout=5)
        if res_all.status_code == 200:
            temp_df = pd.DataFrame(res_all.json())
            if not temp_df.empty and 'code' in temp_df.columns and 'change' in temp_df.columns:
                temp_df['股票代號'] = temp_df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                temp_df['股票代號'] = temp_df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                latest_all_df = temp_df[['股票代號', 'change']].rename(columns={'change': '精準單日△'})
    except Exception: pass
    return json_dfs, latest_all_df

def extract_date_from_filename(filename):
    m8 = re.search(r'(202\d{5})', filename)
    if m8: return m8.group(1)
    return None

@st.cache_data(ttl=300)
def build_block1_master_df():
    DATA_DIR = "./data"
    date_files = defaultdict(lambda: {'txt': [], 'csv': []})
    all_csv_files = glob.glob(os.path.join(DATA_DIR, "*JSON*.csv"))
    
    for f in all_csv_files:
        d_label = extract_date_from_filename(os.path.basename(f))
        if d_label: date_files[d_label]['csv'].append(f)

    sorted_dates = sorted(date_files.keys(), reverse=True)
    f_df = pd.DataFrame()
    
    j_dfs, l_all_df = fetch_github_json_all()

    if sorted_dates:
        for i, date_label in enumerate(sorted_dates[:30]): 
            day_dfs = []
            if date_files[date_label]['csv']:
                df = pd.read_csv(date_files[date_label]['csv'][0], encoding='utf-8-sig')
                if '股票代號' in df.columns:
                    df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                    df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
                    df = df.rename(columns={'法人持股': f"{date_label}持股%"})
                    day_dfs.append(df)
                
            day_dfs = [df for df in day_dfs if not df.empty]
            if not day_dfs: continue
                
            df_day_raw = pd.concat(day_dfs, ignore_index=True)
            def agg_sections_func(x):
                valid_x = set()
                for val in x:
                    if pd.notna(val) and str(val).strip() != "":
                        for p in str(val).split(','): valid_x.add(p.strip())
                return ",".join([s for s in ['5日', '20日', '60日', '120日'] if s in valid_x])
                
            agg_dict = {f"{date_label}持股%": 'max', '上榜區塊': agg_sections_func}
            df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg(agg_dict).reset_index().rename(columns={'上榜區塊': f"{date_label}_區塊"})
                
            if f_df is None or f_df.empty: f_df = df_day
            else: f_df = pd.merge(f_df, df_day, on=['股票代號', '股票名稱'], how='outer')
                
        if f_df is not None and not f_df.empty:
            d_cols = sorted([c for c in f_df.columns if '持股%' in c], reverse=True)
            for c in d_cols: f_df[c] = pd.to_numeric(f_df[c], errors='coerce').fillna(0)
                
            def generate_tags(sections):
                if pd.isna(sections) or not sections: return ""
                sec_list = str(sections).split(',')
                tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if key in sec_list]
                return " ".join(tags)
                
            latest_sect_col = f"{sorted_dates[0]}_區塊"
            if latest_sect_col not in f_df.columns: f_df[latest_sect_col] = ""
            
            f_df['今日上榜'] = f_df[latest_sect_col].apply(generate_tags)
            f_df['上榜數量'] = f_df['今日上榜'].apply(lambda x: str(x).count('日'))
                
            def evaluate_trend(row):
                if len(d_cols) < 2: return "⚪ 資料不足"
                dynamics, v0, v1 = [], row[d_cols[0]], row[d_cols[1]]
                diff1 = v0 - v1  
                if diff1 > 0:
                    is_slowing = False
                    if len(d_cols) >= 3:
                        v2 = row[d_cols[2]]
                        if v0 > v1 > v2 > 0: dynamics.append("🪜 階梯吸籌")
                        elif len(d_cols) >= 4 and v0 >= v1 >= v2 >= row[d_cols[3]] > 0 and v0 > row[d_cols[3]]: dynamics.append("🛡️ 穩健吸籌")
                        if v1 != 0 and v2 != 0 and diff1 < (v1 - v2): dynamics.append("⚠️ 趨緩"); is_slowing = True
                    if not is_slowing: dynamics.append("📈 上升")
                elif diff1 < 0: dynamics.append("📉 下降")
                else: dynamics.append("🔄 持平")
                    
                today_list = [s for s in str(row.get(f"{sorted_dates[0]}_區塊", "")).split(',') if s]
                yest_list = [s for s in str(row.get(f"{sorted_dates[1]}_區塊", "")).split(',') if s]
                
                if v0 > 0 and v1 == 0 and any(row[c] > 0 for c in d_cols[2:]): dynamics.append("🔄 洗盤回歸")
                if 1 <= len(yest_list) <= 3 and len(today_list) > len(yest_list):
                    new_entries = [i for i in today_list if i not in yest_list]
                    tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if any(key in item for item in new_entries)]
                    if tags: dynamics.append(f"🚀 衝進{'、'.join(tags)}榜單")
                return " | ".join(dynamics)
                    
            f_df['最新動態'] = f_df.apply(evaluate_trend, axis=1)
            f_df['法人持股'] = f_df[d_cols[0]]
            
            if not l_all_df.empty and '股票代號' in l_all_df.columns:
                f_df = pd.merge(f_df, l_all_df, on='股票代號', how='left')
                f_df['△'] = f_df['精準單日△'].fillna(0.0)
            else:
                if len(d_cols) >= 2:
                    f_df['△'] = f_df.apply(lambda row: row[d_cols[0]] - row[d_cols[1]] if row[d_cols[1]] > 0.001 else 0.0, axis=1)
                else: f_df['△'] = 0.0
                
            f_df['法人金額'] = 0.0 

            for d in [5, 20, 60, 120]:
                if d in j_dfs and not j_dfs[d].empty:
                    temp_json = j_dfs[d][['股票代號', f'{d}日ΔChange', f'{d}日排名']]
                    f_df = pd.merge(f_df, temp_json, on='股票代號', how='left')

            col_ref = f_df.set_index('股票代號')['上榜數量'].to_dict()
            for col in d_cols: f_df[col] = f_df[col].apply(lambda x: "未進榜" if pd.isna(x) or abs(x) < 0.0001 else f"{x:.2f}")

            f_df['今日有上榜_排序'] = f_df['今日上榜'] != ""
            if d_cols:
                f_df = f_df.sort_values(by=['今日有上榜_排序', '上榜數量', d_cols[0]], ascending=[False, False, False])
            
            return f_df, sorted_dates, d_cols, col_ref
    
    return pd.DataFrame(), [], [], {}

# ==========================================
# 區塊1背景預載引擎 (強制維持記憶體熱度，解決歸零與 KeyError 問題)
# ==========================================
def preload_all_csv_data():
    import os, glob
    import pandas as pd
    DATA_DIR = "./data"
    
    # 智慧檔案尋找器 (加入終極欄位清洗，解決 KeyError)
    def safe_load(key, kw1, kw2=""):
        if key in st.session_state and not st.session_state[key].empty: return
        files = glob.glob(os.path.join(DATA_DIR, f"*{kw1}*.csv"))
        if kw2: files = [f for f in files if kw2 in f]
        if files:
            for enc in ['cp950', 'utf-8-sig', 'utf-8']:
                try:
                    df = pd.read_csv(sorted(files, reverse=True)[0], encoding=enc)
                    if not df.empty:
                        # 💡 終極防呆：清洗所有欄位名稱，把亂七八糟的代號統整為「股票代號」
                        df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
                        id_col = next((c for c in df.columns if '代號' in c or 'code' in c.lower()), None)
                        nm_col = next((c for c in df.columns if '名稱' in c or 'name' in c.lower()), None)
                        
                        rename_dict = {}
                        if id_col and id_col != '股票代號': rename_dict[id_col] = '股票代號'
                        if nm_col and nm_col != '股票名稱': rename_dict[nm_col] = '股票名稱'
                        if rename_dict: df = df.rename(columns=rename_dict)
                        
                        # 確保股票代號是乾淨的字串
                        if '股票代號' in df.columns:
                            df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                            
                        st.session_state[key] = df
                        return
                except: continue
        st.session_state[key] = pd.DataFrame()

    # 強制將所有區塊的 CSV 預先載入記憶體
    safe_load('df_blk2_1', '外資買', '成交')
    safe_load('df_blk2_2', '投信買', '成交')
    safe_load('df_blk2_3', '外資買', '發行')
    safe_load('df_blk2_4', '投信買', '發行')
    safe_load('df_blk3_main', '連買')
    safe_load('df_margin_pct', '融資減少幅度')
    safe_load('df_margin_vol', '融資減少張數')
    safe_load('df_short_pct', '借券賣出減少幅度')
    safe_load('df_short_vol', '借券賣出減少張數')
    safe_load('df_margin_plus_pct', '融券增加幅度')
    safe_load('df_margin_plus_vol', '融券增加張數')
    safe_load('df_blk5', '400張')
    if st.session_state.get('df_blk5', pd.DataFrame()).empty: safe_load('df_blk5', '大股東')
    safe_load('df_blk5_1000', '1000張')
    if st.session_state.get('df_blk5_1000', pd.DataFrame()).empty: safe_load('df_blk5_1000', '大股東')

# 👇 確保下方有呼叫它
if 'my_final_df' not in st.session_state or st.session_state['my_final_df'].empty or st.session_state.get('force_reload', False):
    with st.spinner("⚡ 背景引擎啟動中，正在載入全市場籌碼數據... (僅需數秒)"):
        json_dfs, latest_all_df = fetch_github_json_all()
        final_df, sorted_dates, date_cols, color_ref = build_block1_master_df()
        st.session_state['my_final_df'] = final_df
        preload_all_csv_data()  # 💡 啟動預載雷達
        st.session_state['force_reload'] = False

# ==========================================
# 🌟 區塊 1 專屬工具函數區 (必須放在 if 鎖外面，供應全站數據)
# ==========================================

from collections import defaultdict

@st.cache_data(ttl=3600)
def fetch_github_json_all():
    days_list = [5, 20, 60, 120]
    json_dfs = {}
    account, repo, branch = "goodinfo3583", "DDong_tw-institutional-stocker", "main"
    
    for d in days_list:
        url = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/top_three_inst_change_{d}_up.json"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                df['股票代號'] = df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                df['股票名稱'] = df['name'].astype(str).str.strip()
                df = df.rename(columns={'three_inst_ratio': '法人持股', 'change': f'{d}日ΔChange'})
                df[f'{d}日排名'] = (df.index + 1).astype(int) 
                json_dfs[d] = df[['股票代號', '股票名稱', '法人持股', f'{d}日ΔChange', f'{d}日排名']]
            else: json_dfs[d] = pd.DataFrame()
        except Exception: json_dfs[d] = pd.DataFrame()
        
    latest_all_df = pd.DataFrame()
    try:
        url_all = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/stock_three_inst_latest.json"
        res_all = requests.get(url_all, timeout=5)
        if res_all.status_code == 200:
            temp_df = pd.DataFrame(res_all.json())
            if not temp_df.empty and 'code' in temp_df.columns and 'change' in temp_df.columns:
                temp_df['股票代號'] = temp_df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                temp_df['股票代號'] = temp_df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                latest_all_df = temp_df[['股票代號', 'change']].rename(columns={'change': '精準單日△'})
    except Exception: pass
    return json_dfs, latest_all_df

def extract_date_from_filename(filename):
    m8 = re.search(r'(202\d{5})', filename)
    if m8: return m8.group(1)
    return None

# 🛠️ 核心巨集：合併所有歷史快照與 GitHub 即時數據，產生全域母表
@st.cache_data(ttl=300)
def build_block1_master_df():
    DATA_DIR = "./data"
    date_files = defaultdict(lambda: {'txt': [], 'csv': []})
    all_csv_files = glob.glob(os.path.join(DATA_DIR, "*JSON*.csv"))
    
    for f in all_csv_files:
        d_label = extract_date_from_filename(os.path.basename(f))
        if d_label: date_files[d_label]['csv'].append(f)

    sorted_dates = sorted(date_files.keys(), reverse=True)
    f_df = pd.DataFrame()
    
    j_dfs, l_all_df = fetch_github_json_all()

    if sorted_dates:
        for i, date_label in enumerate(sorted_dates[:30]): 
            day_dfs = []
            if date_files[date_label]['csv']:
                df = pd.read_csv(date_files[date_label]['csv'][0], encoding='utf-8-sig')
                if '股票代號' in df.columns:
                    df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                    df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
                    df = df.rename(columns={'法人持股': f"{date_label}持股%"})
                    day_dfs.append(df)
                
            day_dfs = [df for df in day_dfs if not df.empty]
            if not day_dfs: continue
                
            df_day_raw = pd.concat(day_dfs, ignore_index=True)
            def agg_sections_func(x):
                valid_x = set()
                for val in x:
                    if pd.notna(val) and str(val).strip() != "":
                        for p in str(val).split(','): valid_x.add(p.strip())
                return ",".join([s for s in ['5日', '20日', '60日', '120日'] if s in valid_x])
                
            agg_dict = {f"{date_label}持股%": 'max', '上榜區塊': agg_sections_func}
            df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg(agg_dict).reset_index().rename(columns={'上榜區塊': f"{date_label}_區塊"})
                
            if f_df is None or f_df.empty: f_df = df_day
            else: f_df = pd.merge(f_df, df_day, on=['股票代號', '股票名稱'], how='outer')
                
        if f_df is not None and not f_df.empty:
            d_cols = sorted([c for c in f_df.columns if '持股%' in c], reverse=True)
            for c in d_cols: f_df[c] = pd.to_numeric(f_df[c], errors='coerce').fillna(0)
                
            def generate_tags(sections):
                if pd.isna(sections) or not sections: return ""
                sec_list = str(sections).split(',')
                tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if key in sec_list]
                return " ".join(tags)
                
            latest_sect_col = f"{sorted_dates[0]}_區塊"
            if latest_sect_col not in f_df.columns: f_df[latest_sect_col] = ""
            
            f_df['今日上榜'] = f_df[latest_sect_col].apply(generate_tags)
            f_df['上榜數量'] = f_df['今日上榜'].apply(lambda x: str(x).count('日'))
                
            def evaluate_trend(row):
                if len(d_cols) < 2: return "⚪ 資料不足"
                dynamics, v0, v1 = [], row[d_cols[0]], row[d_cols[1]]
                diff1 = v0 - v1  
                if diff1 > 0:
                    is_slowing = False
                    if len(d_cols) >= 3:
                        v2 = row[d_cols[2]]
                        if v0 > v1 > v2 > 0: dynamics.append("🪜 階梯吸籌")
                        elif len(d_cols) >= 4 and v0 >= v1 >= v2 >= row[d_cols[3]] > 0 and v0 > row[d_cols[3]]: dynamics.append("🛡️ 穩健吸籌")
                        if v1 != 0 and v2 != 0 and diff1 < (v1 - v2): dynamics.append("⚠️ 趨緩"); is_slowing = True
                    if not is_slowing: dynamics.append("📈 上升")
                elif diff1 < 0: dynamics.append("📉 下降")
                else: dynamics.append("🔄 持平")
                    
                today_list = [s for s in str(row.get(f"{sorted_dates[0]}_區塊", "")).split(',') if s]
                yest_list = [s for s in str(row.get(f"{sorted_dates[1]}_區塊", "")).split(',') if s]
                
                if v0 > 0 and v1 == 0 and any(row[c] > 0 for c in d_cols[2:]): dynamics.append("🔄 洗盤回歸")
                if 1 <= len(yest_list) <= 3 and len(today_list) > len(yest_list):
                    new_entries = [i for i in today_list if i not in yest_list]
                    tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if any(key in item for item in new_entries)]
                    if tags: dynamics.append(f"🚀 衝進{'、'.join(tags)}榜單")
                return " | ".join(dynamics)
                    
            f_df['最新動態'] = f_df.apply(evaluate_trend, axis=1)
            f_df['法人持股'] = f_df[d_cols[0]]
            
            if not l_all_df.empty and '股票代號' in l_all_df.columns:
                f_df = pd.merge(f_df, l_all_df, on='股票代號', how='left')
                f_df['△'] = f_df['精準單日△'].fillna(0.0)
            else:
                if len(d_cols) >= 2:
                    f_df['△'] = f_df.apply(lambda row: row[d_cols[0]] - row[d_cols[1]] if row[d_cols[1]] > 0.001 else 0.0, axis=1)
                else: f_df['△'] = 0.0
                
            f_df['法人金額'] = 0.0 

            for d in [5, 20, 60, 120]:
                if d in j_dfs and not j_dfs[d].empty:
                    temp_json = j_dfs[d][['股票代號', f'{d}日ΔChange', f'{d}日排名']]
                    f_df = pd.merge(f_df, temp_json, on='股票代號', how='left')

            col_ref = f_df.set_index('股票代號')['上榜數量'].to_dict()
            for col in d_cols: f_df[col] = f_df[col].apply(lambda x: "未進榜" if pd.isna(x) or abs(x) < 0.0001 else f"{x:.2f}")

            f_df['今日有上榜_排序'] = f_df['今日上榜'] != ""
            if d_cols:
                f_df = f_df.sort_values(by=['今日有上榜_排序', '上榜數量', d_cols[0]], ascending=[False, False, False])
            
            return f_df, sorted_dates, d_cols, col_ref
    
    return pd.DataFrame(), [], [], {}

# 👇👇👇 致命錯誤修復：執行引擎必須放在上面兩個 def 函數「定義完成」的下面！ 👇👇👇
json_dfs, latest_all_df = fetch_github_json_all()
final_df, sorted_dates, date_cols, color_ref = build_block1_master_df()
st.session_state['my_final_df'] = final_df
# 👆👆👆 ======================================================================👆👆👆

# ==========================================
# 🔒 區塊 1 專屬包廂鎖 (畫面渲染與站長工具包進這裡)
# ==========================================
if current_page in ["all", "b1"]:
    
    st.write("---")
    st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)

    if sorted_dates:
        latest_d = sorted_dates[0]
        fmt_date = f"{latest_d[:4]}/{latest_d[4:6]}/{latest_d[6:]}"
        st.markdown(
            f"<h2 style='margin-bottom: 0px;'>法人動向：三大法人短中長線持股比追蹤 "
            f"<span style='color:#00D2FF; font-size:16px; font-weight:500; margin-left:12px;'>基準日：{fmt_date}</span></h2>", 
            unsafe_allow_html=True
        )
    else:
        st.markdown("<h2 style='margin-bottom: 0px;'>👑 區塊1：三大法人短中長線持股比追蹤</h2>", unsafe_allow_html=True)

    # ------------------------------------------
    # 💾 站長專屬：JSON 200名快照存檔區
    # ------------------------------------------
    DATA_DIR = "./data"
    all_json_csvs = glob.glob(os.path.join(DATA_DIR, "*JSON_History.csv"))
    local_latest_date = "無紀錄"
    if all_json_csvs:
        dates = [m.group(1) for f in all_json_csvs if (m := re.search(r'(202\d{5})', os.path.basename(f)))]
        if dates: local_latest_date = max(dates)

    today_str = datetime.datetime.now().strftime("%Y%m%d")
    is_updated_today = (local_latest_date == today_str)
    status_icon = "✅" if is_updated_today else "⚠️"
    status_text = f"{status_icon} 本地最新: {local_latest_date}"

    st.write("") 
    c_btn1, c_btn2 = st.columns(2)

    with c_btn1: 
        st.link_button("📊 台股法人籌碼追蹤 (50名)", "https://goodinfo3583.github.io/DDong_tw-institutional-stocker/", use_container_width=True)

    with c_btn2:
        try: exp_container = st.popover(f"🛠 站長快照 ({status_text})", use_container_width=True)
        except AttributeError: exp_container = st.expander(f"🛠 站長：下載 200名快照 ({status_text})", expanded=False)
            
        with exp_container:
            if is_updated_today: st.success(f"✅ **今日已更新！** 資料夾中最新快照為 `{local_latest_date}`。")
            else: st.warning(f"⚠️ **今日尚未更新！** 資料夾中最新快照停留在 `{local_latest_date}`，請記得下載！")
                
            admin_pw = st.text_input("請輸入站長密碼以解鎖功能", type="password", key="admin_pw_input")
            if admin_pw == "DDong888": 
                st.success("🔓 驗證成功！請執行快照封存。")
                
                if st.button("🔄 站長專屬：強制抓取 GitHub 最新數據", use_container_width=True):
                    fetch_github_json_all.clear() 
                    st.rerun()                     
                
                snap_date = st.date_input("選擇這份資料的實際基準日")
                st.write("")
                if st.button("💾 將 GitHub 200名數據封存為 CSV", use_container_width=True):
                    date_str = snap_date.strftime("%Y%m%d")
                    save_path = os.path.join(DATA_DIR, f"{date_str}_JSON_History.csv")
                    all_snap_data = []
                    for d in [5, 20, 60, 120]:
                        if d in json_dfs and not json_dfs[d].empty:
                            temp = json_dfs[d][['股票代號', '股票名稱', '法人持股']].copy()
                            temp['上榜區塊'] = f"{d}日"
                            all_snap_data.append(temp)
                    
                    if all_snap_data:
                        snap_df = pd.concat(all_snap_data, ignore_index=True)
                        snap_grouped = snap_df.groupby(['股票代號', '股票名稱']).agg({
                            '法人持股': 'max', '上榜區塊': lambda x: ",".join(set(x))
                        }).reset_index()
                        csv_data = snap_grouped.to_csv(index=False).encode('utf-8-sig')
                        snap_grouped.to_csv(save_path, index=False, encoding='utf-8-sig')
                        
                        build_block1_master_df.clear() # 🌟 清空母表快取，讓下次系統讀取包含最新資料
                        st.success(f"✅ 成功生成 {len(snap_grouped)} 檔股票的歷史快照！")
                        st.download_button(
                            label="📥 點我下載快照 CSV 檔案", data=csv_data, file_name=f"{date_str}_JSON_History.csv",
                            mime="text/csv", type="primary", use_container_width=True
                        )
                    else: st.error("❌ 尚未獲取到 GitHub 數據，封存失敗。")
            elif admin_pw != "": st.error("❌ 密碼錯誤，無法使用此功能。")


    # ==========================================
    # 🔧 UI 數據渲染 (四大榜單完美還原期程排序)
    # ==========================================
    c1, c2, c3 = st.columns([1, 1, 2])
    show_etf = c1.checkbox("顯示 ETF", value=True, key="blk1_etf_sync")
    show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="blk1_bond_sync")
    search_kw = c3.text_input("🔍 快速尋找標的 (輸入代號或名稱)", placeholder="例如: 2890 或 永豐金")

    tab5, tab20, tab60, tab120, tab_all = st.tabs([
        "🔴 5日排行", "🟡 20日排行", "🟢 60日排行", "🔵 120日排行", "📊 歷史軌跡全能池"
    ])

    def format_delta(x):
        try:
            val = float(x)
            if abs(val) < 0.005: return "0.00"
            return f"+{val:.2f}" if val > 0 else f"{val:.2f}"
        except: return "0.00"

    def get_local_tab_df(target_day_str):
        if final_df is None or final_df.empty: return pd.DataFrame()
        df = final_df[final_df['今日上榜'].str.contains(f'{target_day_str}日', na=False)].copy()
        if df.empty: return df
        
        is_bond = df['股票代號'].str.endswith('B')
        is_etf = (df['股票代號'].str.len() >= 5) & (~is_bond)
        is_stock = df['股票代號'].str.len() == 4
        mask = is_stock
        if show_etf: mask |= is_etf
        if show_bond: mask |= is_bond
        if search_kw:
            mask &= (df['股票代號'].str.contains(search_kw, na=False)) | (df['股票名稱'].str.contains(search_kw, na=False))
        df = df[mask].copy()
        
        rank_col = f'{target_day_str}日排名'
        change_col = f'{target_day_str}日ΔChange'
        
        if rank_col in df.columns:
            df = df.sort_values(by=rank_col, ascending=True)
        elif change_col in df.columns:
            df[change_col] = pd.to_numeric(df[change_col], errors='coerce').fillna(0)
            df = df.sort_values(by=change_col, ascending=False)
            df[f'{target_day_str}日排名'] = range(1, len(df) + 1)
            
        df['法人持股'] = df['法人持股'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
        df['△'] = df['△'].apply(format_delta)
        if change_col in df.columns: 
            df[change_col] = df[change_col].apply(format_delta)
            
        df['法人金額'] = "0.00"
        df['最新動態'] = df['最新動態'].fillna("⚪ 尚無比對紀錄")
        return df

    with tab5:
        df_5 = get_local_tab_df(5)
        display_cols = ['5日排名', '股票代號', '股票名稱', '法人持股', '△', '5日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_5.empty: st.dataframe(df_5[[c for c in display_cols if c in df_5.columns]], use_container_width=True, hide_index=True)
        else: st.info("⚪ 尚無 5日進榜數據。")

    with tab20:
        df_20 = get_local_tab_df(20)
        display_cols = ['20日排名', '股票代號', '股票名稱', '法人持股', '△', '20日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_20.empty: st.dataframe(df_20[[c for c in display_cols if c in df_20.columns]], use_container_width=True, hide_index=True)

    with tab60:
        df_60 = get_local_tab_df(60)
        display_cols = ['60日排名', '股票代號', '股票名稱', '法人持股', '△', '60日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_60.empty: st.dataframe(df_60[[c for c in display_cols if c in df_60.columns]], use_container_width=True, hide_index=True)

    with tab120:
        df_120 = get_local_tab_df(120)
        display_cols = ['120日排名', '股票代號', '股票名稱', '法人持股', '△', '120日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_120.empty: st.dataframe(df_120[[c for c in display_cols if c in df_120.columns]], use_container_width=True, hide_index=True)
            
    with tab_all:
        if final_df is not None and not final_df.empty:
            is_bond = final_df['股票代號'].str.endswith('B')
            is_etf = (final_df['股票代號'].str.len() >= 5) & (~is_bond)
            is_stock = final_df['股票代號'].str.len() == 4
            mask = is_stock
            if show_etf: mask |= is_etf
            if show_bond: mask |= is_bond
            
            if search_kw:
                mask &= (final_df['股票代號'].str.contains(search_kw, na=False)) | (final_df['股票名稱'].str.contains(search_kw, na=False))
                
            filtered_df = final_df[mask].copy()
            filtered_df['法人持股'] = filtered_df['法人持股'].apply(lambda x: f"{x:.2f}%")
            filtered_df['△'] = filtered_df['△'].apply(format_delta)
            
            def highlight_row(row):
                cnt = color_ref.get(row['股票代號'], 0)
                if cnt == 4: bg = 'background-color: rgba(240, 90, 90, 0.25)'     
                elif cnt == 3: bg = 'background-color: rgba(255, 165, 0, 0.25)'    
                elif cnt == 2: bg = 'background-color: rgba(80, 200, 120, 0.25)'    
                elif cnt == 1: bg = 'background-color: rgba(0, 127, 255, 0.25)'    
                else: bg = 'background-color: #111622; color: #E2E8F0'                                                                                                                                                                                                                                                                                                                                                                                                  
                return [bg] * len(row)
                
            all_display_cols = ['股票代號', '股票名稱', '今日上榜', '最新動態', '△'] + date_cols
            st.dataframe(filtered_df[all_display_cols].style.apply(highlight_row, axis=1), use_container_width=True)

    st.write("")
    st.info("💡 △是單日的法人持股增減(如果最新基準日未進前200榜，△會直接以歸0計算)；5/20/60/120日ΔChange為5/20/60/120期間的累積變化，我們可以試著短線與長線一起觀察。")

    # ==========================================
    # 📊 繪製區塊 ：產業聚落與資金輪動板塊 (Treemap - 動態分頁熱力圖版)
    # ==========================================
    st.write("---")
    
    st.markdown("### 🧩 資金聚落板塊：三大法人進榜產業分佈")
    st.caption("透過區塊面積大小，觀察法人資金集中攻擊哪些產業。")
    st.info("💡 △ 是單日的法人持股增減 (如果最新基準日未進前200榜，△會直接以歸0計算)；滑鼠懸停可觀察短長線的持股波段軌跡。底色越紅買超越強，△代表單日法人持股增減，但也要小心大買大賣的名單。")

    # 1. 取得主資料表與股票字典
    df_b1_master = st.session_state.get('my_final_df', pd.DataFrame())
    
    if not df_b1_master.empty and 'STOCK_DICT' in globals() and STOCK_DICT:
        
        # 🚀 修正 2：搜尋框與觀測範圍往下放，排在標題與表格之間 (雙欄並排更美觀)
        st.write("") # 增加一點呼吸空間
        c_opt, c_search = st.columns([2.5, 1.5])
        with c_opt:
            top_n_option = st.radio("設定觀測範圍：", ["顯示前 50 名", "顯示前 200 名"], horizontal=True)
            top_n = 50 if "50" in top_n_option else 200
            
        with c_search:
            treemap_search = st.text_input("🔍 板塊內標的搜尋", placeholder="輸入代號/名稱以聚焦...", label_visibility="visible")

        # 3. 建立五個分頁
        tab_5, tab_20, tab_60, tab_120, tab_all = st.tabs(["🔴 5日排行", "🟡 20日排行", "🟢 60日排行", "🔵 120日排行", "🌟 綜合熱力池"])

        # 💡 定義專屬的繪圖引擎函數
        def render_period_treemap(period_days):
            if period_days == "all":
                has_tag = df_b1_master['今日上榜'].astype(str).str.strip() != ""
                period_df = df_b1_master[has_tag].copy()
                
                if period_df.empty:
                    st.info("⚪ 今日尚無任何標的上榜。")
                    return
                
                period_df['熱力數值'] = pd.to_numeric(
                    period_df['△'].astype(str).str.replace('+', '').str.replace('%', ''), 
                    errors='coerce'
                ).fillna(0.0)
                
                period_df = period_df.nlargest(top_n, '熱力數值').copy()
                period_df['綜合△排名'] = period_df['熱力數值'].rank(ascending=False, method='min')
                rank_col = '綜合△排名'
                title_name = "🌟 綜合上榜熱力池"
                
            else:
                rank_col = f"{period_days}日排名"
                if rank_col not in df_b1_master.columns:
                    st.info(f"⚪ 尚無 {period_days} 日排行資料。")
                    return

                period_df = df_b1_master[df_b1_master[rank_col] > 0].nsmallest(top_n, rank_col).copy()

                if period_df.empty:
                    st.info(f"⚪ {period_days} 日排行無符合資料。")
                    return
                
                period_df['熱力數值'] = pd.to_numeric(
                    period_df['△'].astype(str).str.replace('+', '').str.replace('%', ''), 
                    errors='coerce'
                ).fillna(0.0)
                title_name = f"🏆 {period_days}日資金聚落"

            # 配對產業別 (剔除 ETF / 債券)
            period_df['產業別'] = period_df['股票代號'].astype(str).apply(
                lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他")
            )
            period_df['產業別'] = period_df['產業別'].replace('', 'ETF / 債券 / 其他')
            period_df = period_df[period_df['產業別'] != 'ETF / 債券 / 其他']

            if period_df.empty:
                st.info("⚪ 剔除 ETF/債券 後無一般產業資料。")
                return

            # 如果有輸入搜尋關鍵字，啟動精準聚焦過濾！
            if treemap_search:
                query = treemap_search.strip()
                period_df = period_df[
                    period_df['股票代號'].astype(str).str.contains(query, case=False, na=False) | 
                    period_df['股票名稱'].astype(str).str.contains(query, case=False, na=False)
                ]
                if period_df.empty:
                    st.warning(f"此週期榜單中，找不到符合「{query}」的標的。")
                    return

            period_df['計數'] = 1 
            period_df['單日△_格式化'] = period_df['熱力數值'].apply(lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}")

            def format_block_label(row):
                name = str(row.get('股票名稱', ''))
                delta_str = row.get('單日△_格式化', '0.00')
                rank_val = row.get(rank_col, '-')
                try: rank_str = str(int(float(rank_val)))
                except: rank_str = str(rank_val)
                
                rank_display = f"△排行: {rank_str}" if period_days == "all" else f"排名: {rank_str}"
                return f"<b>{name}</b><br><span style='font-size: 11px; color: #E5E7EB;'>△ {delta_str}<br>{rank_display}</span>"
            
            period_df['顯示名稱'] = period_df.apply(format_block_label, axis=1)

            date_cols = sorted([c for c in period_df.columns if '持股%' in c], reverse=True)[:7]
            hover_columns = ['股票代號', '今日上榜', '最新動態', '單日△_格式化', rank_col] + date_cols

            custom_continuous_scale = [
                [0.0, "rgba(0, 230, 118, 0.85)"],  
                [0.5, "rgba(30, 41, 59, 0.95)"],   
                [1.0, "rgba(255, 75, 75, 0.85)"]   
            ]

            import plotly.express as px
            fig = px.treemap(
                period_df,
                path=[px.Constant(title_name), '產業別', '顯示名稱'],
                values='計數',                      
                color='熱力數值',                   
                color_continuous_scale=custom_continuous_scale, 
                color_continuous_midpoint=0,        
                hover_data=hover_columns
            )
            fig.update_coloraxes(showscale=False)

            rank_hover_label = "綜合△排行" if period_days == "all" else f"{period_days}日排行"
            hover_template = (
                '<b>%{label}</b><br>'
                '股票代號: %{customdata[0]}<br>'
                '今日上榜: %{customdata[1]}<br>'
                '最新動態: %{customdata[2]}<br>'
                '單日△: <b>%{customdata[3]}</b><br>'
                f'{rank_hover_label}: <b>第 %{{customdata[4]}} 名</b><br>' 
                '----------------<br>'
            )
            for i, col in enumerate(date_cols):
                clean_date = col.replace("持股%", "") 
                hover_template += f'{clean_date} 持股比: %{{customdata[{5+i}]}}%<br>'
            hover_template += '<extra></extra>'

            fig.update_traces(
                textinfo="label", 
                textfont=dict(color="white", size=14),
                marker=dict(line=dict(color='#0B0F19', width=2), pad=dict(t=35, l=10, r=10, b=10)),
                hovertemplate=hover_template
            )
            
            fig.update_layout(margin=dict(t=30, l=0, r=0, b=0), height=650, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="sans-serif"))
            st.plotly_chart(fig, use_container_width=True)

        with tab_5: render_period_treemap(5)
        with tab_20: render_period_treemap(20)
        with tab_60: render_period_treemap(60)
        with tab_120: render_period_treemap(120)
        with tab_all: render_period_treemap("all")

        # ==========================================
        # 🗑️ 進階版 ETF 與債券懸停與變色模塊 (單行 HTML 防破圖版)
        # ==========================================
        is_etf = df_b1_master['股票代號'].astype(str).apply(
            lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他") in ["ETF / 債券 / 其他", ""]
        )
        on_list = df_b1_master['今日上榜'].astype(str).str.strip() != ""
        excluded_etfs = df_b1_master[is_etf & on_list].sort_values(by='股票代號')
        
        if not excluded_etfs.empty:
            st.write("")
            st.markdown("##### 🗑️ 本次已剔除的非一般產業 (ETF / 債券 / 指數)")
            st.caption("這些標的雖有強大法人資金進駐上榜，但已從上方產業聚落中剔除。**游標懸停於標籤可查看詳細 7 日明細。**")
            
            tags_html = ""
            import html # 引入字串跳脫模組
            
            date_cols_master = sorted([c for c in df_b1_master.columns if '持股%' in c], reverse=True)[:7]
            
            for _, r in excluded_etfs.iterrows():
                name = str(r.get('股票名稱', ''))
                sid = str(r.get('股票代號', ''))
                tag = str(r.get('今日上榜', '無'))
                dyn = str(r.get('最新動態', '-'))
                delta = r.get('△', 0.0)
                
                safe_name = html.escape(name, quote=True)
                safe_sid = html.escape(sid, quote=True)
                safe_tag = html.escape(tag, quote=True)
                safe_dyn = html.escape(dyn, quote=True)
                
                try: d_val = float(str(delta).replace('+', '').replace('%', ''))
                except: d_val = 0.0
                    
                if d_val > 0:
                    bg_color = "rgba(255, 75, 75, 0.15)"   
                    border_color = "rgba(255, 75, 75, 0.4)" 
                    text_color = "#FF4B4B"                  
                    d_str = f"+{d_val:.2f}"
                elif d_val < 0:
                    bg_color = "rgba(0, 230, 118, 0.15)"   
                    border_color = "rgba(0, 230, 118, 0.4)" 
                    text_color = "#00E676"                  
                    d_str = f"{d_val:.2f}"
                else:
                    bg_color = "rgba(30, 41, 59, 0.6)"     
                    border_color = "#334155"
                    text_color = "#94A3B8"
                    d_str = "0.00"
                    
                tooltip_text = (
                    f"【{safe_name}】&#10;"
                    f"股票代號: {safe_sid}&#10;"
                    f"今日上榜: {safe_tag}&#10;"
                    f"最新動態: {safe_dyn}&#10;"
                    f"單日△: {d_str}&#10;"
                    f"----------------&#10;"
                )
                
                for col in date_cols_master:
                    clean_date = col.replace("持股%", "") 
                    val = r.get(col, "0.00")
                    tooltip_text += f"{clean_date} 持股比: {val}%&#10;"
                
                # 🚀 核心修復：強制把 HTML 寫在「單行」內，不留任何換行與縮排，避免觸發 Markdown 程式碼區塊地雷！
                tags_html += f"<div title=\"{tooltip_text}\" style=\"background-color: {bg_color}; color: #E2E8F0; border: 1px solid {border_color}; padding: 6px 14px; border-radius: 20px; margin: 5px; display: inline-flex; align-items: center; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); cursor: help; transition: transform 0.2s;\">{safe_name} ({safe_sid}) <span style='color: {text_color}; font-weight: bold; margin-left: 8px;'>△ {d_str}</span></div>"
            
            st.markdown(f"<div style='margin-top: 5px; line-height: 2.4;'>{tags_html}</div>", unsafe_allow_html=True)

    else:
        st.info("⚪ 尚無全市場大數據或找不到產業字典，請確認背景掃描引擎已啟動。")
# ========# ========
# 讀取外資數據庫下面
# ========# ========
# ==========================================
    # 🕵️‍♂️ [壓軸尋寶] 實驗性功能：雙引擎籌碼歷史軌跡 (內資推估 vs 外資大腿)
    # ==========================================
    st.write("---")
    
    # 1. 呼叫外資資料庫讀取引擎
    df_foreign = load_foreign_ratio_data(DATA_DIR)
    
    # 2. 如果外資資料和總表都存在，就啟動雙引擎分析系統
    if not df_foreign.empty and final_df is not None and not final_df.empty:
        with st.expander("🕵️‍♂️ [深潛實驗室] 籌碼 20 日歷史軌跡透視鏡 (內資推估 vs 外資)", expanded=False):
            st.caption("透過 20 日的持股比例變化，精準透視法人是在「短線洗盤」還是「長線階梯式建倉」。")
            
            # 💡 抓取所有日期：找出主表與外資表共有的日期
            foreign_dates = {c.replace('外資持股_', '') for c in df_foreign.columns if '外資持股_' in c}
            total_dates = {c.replace('持股%', '') for c in final_df.columns if '持股%' in c}
            
            # 取交集並由新到舊排序，最多取近 20 天
            common_dates = sorted(list(foreign_dates & total_dates), reverse=True)[:20]
            
            if common_dates:
                # 將外資表需要的欄位拿出來 (代號 + 所有共有的日期欄位)
                f_need_cols = ['股票代號'] + [f'外資持股_{d}' for d in common_dates]
                
                # 進行合併
                df_calc = pd.merge(final_df, df_foreign[f_need_cols], on='股票代號', how='inner')
                
                # 清洗百分比字串的函數
                def clean_pct(val):
                    try: return float(str(val).replace('%', '').replace(',', ''))
                    except: return 0.0
                
                # 準備存放顯示欄位名稱的清單
                dom_display_cols = []
                for_display_cols = []
                
                # 💡 利用單一迴圈，同時計算「內資」與格式化「外資」的 20 天數據
                for d in common_dates:
                    tot_col = f'{d}持股%'
                    for_col = f'外資持股_{d}'
                    
                    dom_col = f'內資_{d[-4:]}' 
                    for_out_col = f'外資_{d[-4:]}'
                    
                    # 取出數值
                    tot_val = df_calc[tot_col].apply(clean_pct)
                    for_val = df_calc[for_col].apply(clean_pct)
                    
                    # 【內資計算】：總法人 - 外資
                    df_calc[f'{dom_col}_raw'] = (tot_val - for_val).clip(lower=0)
                    df_calc[dom_col] = df_calc[f'{dom_col}_raw'].apply(lambda x: f"{x:.2f}%")
                    dom_display_cols.append(dom_col)
                    
                    # 【外資格式化】：直接取用外資數值
                    df_calc[f'{for_out_col}_raw'] = for_val
                    df_calc[for_out_col] = df_calc[f'{for_out_col}_raw'].apply(lambda x: f"{x:.2f}%")
                    for_display_cols.append(for_out_col)
                
                # 基礎篩選：只看今天有上榜的有動能股票
                df_calc = df_calc[df_calc['今日上榜'].astype(str).str.strip() != ""]
                
                # 🌟 建立兩個分頁
                tab_dom, tab_for = st.tabs(["🕵️‍♂️ 內資 (投信+自營) 20日軌跡", "🌎 外資大腿 20日軌跡"])
                
                # 共通的基礎欄位
                base_cols = ['股票代號', '股票名稱', '今日上榜', '△']
                
                with tab_dom:
                    st.markdown("##### 🔍 尋找「投信/自營商」連續鎖碼股")
                    st.caption("內資常專注於中小型爆發股，若連續多日比例上升，代表投信作帳行情啟動。")
                    # 以最新一天的內資持股排序
                    latest_dom_col = f'內資_{common_dates[0][-4:]}_raw'
                    df_dom_sorted = df_calc.sort_values(by=latest_dom_col, ascending=False).head(40)
                    st.dataframe(df_dom_sorted[base_cols + dom_display_cols], use_container_width=True, hide_index=True)
                    
                with tab_for:
                    st.markdown("##### 🔍 尋找「外資大腿」長線階梯建倉股")
                    st.caption("外資資金龐大，若發現持股比例連續 1~2 週穩步增長，代表真正的長線資金進駐。")
                    # 以最新一天的外資持股排序
                    latest_for_col = f'外資_{common_dates[0][-4:]}_raw'
                    df_for_sorted = df_calc.sort_values(by=latest_for_col, ascending=False).head(40)
                    st.dataframe(df_for_sorted[base_cols + for_display_cols], use_container_width=True, hide_index=True)
                
            else:
                st.warning("⚠️ 找不到主表與外資表的共通日期，請確認資料是否已同步。")
# ==========================================
# 區塊 2 專屬包廂鎖
# ==========================================

# ==========================================
# 區塊 3 專屬包廂鎖
# ==========================================

# ==========================================
# 區塊 4 專屬包廂鎖
# ==========================================

# ==========================================
# 區塊 5 專屬包廂鎖
# ==========================================
          
# ==========================================
# 💸 區塊 6：盤後鉅額交易總表 (原生 Dataframe 升級版 + 交易別顯示)
# ==========================================

# 💡 修正點 1：將函數定義放在 if 鎖的「外面」，確保 Streamlit 的快取正常運作
def clean_number_for_display(val):
    try:
        if pd.isna(val) or str(val).strip() == '-': return '-'
        f = float(str(val).replace(',', ''))
        return str(int(f)) if f.is_integer() else str(f).rstrip('0').rstrip('.')
    except: return str(val)

@st.cache_data(ttl=60)
def build_historical_block_matrix():
    """搜尋資料夾中所有的鉅額交易紀錄，自動組成歷史矩陣 (最強寬容版 + 智慧箭頭標示)"""
    import os, glob
    import pandas as pd
    if not os.path.exists(DATA_DIR): return None, []
    files = glob.glob(os.path.join(DATA_DIR, "*鉅額*.csv"))
    if not files: return None, []
    
    files.sort(reverse=True)
    target_files = files[:10]
    master_df = None
    date_cols = []
    
    for f in target_files:
        try:
            d_str = os.path.basename(f).replace('-', '').replace('_', '')[:8]
            short_date = d_str[-4:]
            col_name = short_date  # 🔥 修改點 1：先使用乾淨的純日期作為欄位名稱
            if col_name not in date_cols: date_cols.append(col_name)
            
            df = pd.read_csv(f)
            c_code = next((c for c in df.columns if '代號' in c or '證券代號' in c), None)
            c_name = next((c for c in df.columns if '名稱' in c or '證券名稱' in c), None)
            c_price = next((c for c in df.columns if '價' in c), None) 
            
            if not all([c_code, c_name, c_price]): continue
            
            df['代號'] = df[c_code].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
            df = df[(df['代號'] != '0') & (df['代號'] != '') & (df['代號'] != 'nan')]
            
            day_df = df.groupby(['代號', c_name]).agg({
                c_price: lambda x: ' / '.join(sorted(set([clean_number_for_display(i) for i in x.dropna()])))
            }).reset_index()
            day_df = day_df.rename(columns={c_name: '股票名稱', c_price: col_name})
            
            if master_df is None: master_df = day_df
            else: master_df = pd.merge(master_df, day_df, on=['代號', '股票名稱'], how='outer')
        except: pass
        
    if master_df is not None and not master_df.empty:
        master_df = master_df.fillna('-')
        master_df = master_df.loc[:, ~master_df.columns.duplicated()]
        valid_date_cols = [c for c in date_cols if c in master_df.columns]
        valid_date_cols.sort(reverse=True) # 排序日期，例如 ['0606', '0605', '0604']
        
        # 🔥 修改點 2：只為「最新」的那一天加上 ▼ 標記，其餘保持純數字
        if valid_date_cols:
            latest_col = valid_date_cols[0]
            new_latest_col = f"▼{latest_col}"
            master_df = master_df.rename(columns={latest_col: new_latest_col})
            valid_date_cols[0] = new_latest_col # 更新列表中的名稱
            
        master_df = master_df[['代號', '股票名稱'] + valid_date_cols]
        if valid_date_cols:
            master_df = master_df.sort_values(by=valid_date_cols[0], ascending=False)
            
    return master_df, [os.path.basename(f) for f in target_files]

# ----------------------------------------------------
# 🔒 區塊 6 專屬包廂鎖 (這以下才是 UI 渲染，包進 if 裡面)
# ----------------------------------------------------
if current_page in ["all", "b6"]:
    st.write("---")
    st.markdown("<div id='section-6'></div>", unsafe_allow_html=True)

    df_block, block_date = get_latest_csv("鉅額交易")
    
    st.markdown("### 區塊 6：鉅額交易動向", unsafe_allow_html=True)
    st.write("💡 鉅額交易有時為大戶私下換手籌碼，成交價可作為「支撐/壓力」的防守線；如果短線跌破建議嚴設停損。")

    tab_today, tab_hist = st.tabs(["🔹 今日最新鉅額交易", "🔹 歷史防守價追蹤表"])

    # ==================== Tab 1: 今日鉅額交易 ====================
    with tab_today:
        if df_block is not None and not df_block.empty:
            col_code = next((c for c in df_block.columns if '代號' in c), None)
            col_name = next((c for c in df_block.columns if '名稱' in c), None)
            col_price = next((c for c in df_block.columns if '單價' in c or '成交價' in c), None)
            col_vol = next((c for c in df_block.columns if '股數' in c or '張數' in c or '成交量' in c), None)
            col_amt = next((c for c in df_block.columns if '金額' in c or '總額' in c), None)
            col_type = next((c for c in df_block.columns if '交易別' in c or '類別' in c), None)

            if all([col_code, col_name, col_price, col_vol, col_amt]):
                df_block['代號'] = df_block[col_code].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
                df_block['股票名稱'] = df_block[col_name]
                df_block['成交價'] = pd.to_numeric(df_block[col_price].astype(str).replace(',', '', regex=True), errors='coerce')
                df_block['成交股數'] = pd.to_numeric(df_block[col_vol].astype(str).replace(',', '', regex=True), errors='coerce')
                df_block['成交金額'] = pd.to_numeric(df_block[col_amt].astype(str).replace(',', '', regex=True), errors='coerce')
                df_block['交易別'] = df_block[col_type].fillna('-') if col_type else '-'
                
                df_block = df_block[(df_block['代號'] != '0') & (df_block['代號'] != '') & (df_block['代號'] != 'nan')]

                grouped_block = df_block.groupby(['代號', '股票名稱']).agg({
                    '交易別': lambda x: '、'.join(sorted(set([str(i) for i in x.dropna() if str(i).strip() != '-']))),
                    
                    # 🔥 修正重點：移除 clean_number_for_display，改用內建的 f-string 格式化來去除多餘的 0 與小數點
                    '成交價': lambda x: ' / '.join(sorted(set([f"{float(i):.2f}".rstrip('0').rstrip('.') for i in x.dropna()]))),
                    
                    '成交股數': 'sum',
                    '成交金額': 'sum'
                }).reset_index()

                grouped_block['成交張數'] = (grouped_block['成交股數'] / 1000).astype(int).apply(lambda x: f"{x:,}")
                grouped_block['總額(億)'] = (grouped_block['成交金額'] / 100000000).apply(lambda x: f"{x:.2f}".rstrip('0').rstrip('.'))

                unique_ids = grouped_block['代號'].unique()
                close_price_dict = {}
                
                # ========================================================
                # 🚀 修正與強化 YFinance 抓取邏輯 (解決 NaN 與報錯問題)
                # ========================================================
                if len(unique_ids) > 0:
                    # 同時準備 .TW(上市) 與 .TWO(上櫃) 的查詢字串，確保不漏接
                    tw_tickers = [f"{sid}.TW" for sid in unique_ids]
                    two_tickers = [f"{sid}.TWO" for sid in unique_ids]
                    all_tickers = " ".join(tw_tickers + two_tickers)
                    
                    try:
                        import yfinance as yf
                        # 批次下載
                        df_yf = yf.download(all_tickers, period="5d", progress=False)
                        
                        if not df_yf.empty and 'Close' in df_yf:
                            close_data = df_yf['Close']
                            
                            # 💡 關鍵：若只成功抓到一檔，強制轉為 DataFrame 以防 .columns 報錯
                            if isinstance(close_data, pd.Series):
                                if hasattr(close_data, 'name') and close_data.name:
                                    close_data = close_data.to_frame(name=close_data.name)
                                else:
                                    close_data = close_data.to_frame()

                            # 進行配對寫入
                            for sid in unique_ids:
                                tkr_tw = f"{sid}.TW"
                                tkr_two = f"{sid}.TWO"
                                
                                target_tkr = None
                                if tkr_tw in close_data.columns and not close_data[tkr_tw].dropna().empty:
                                    target_tkr = tkr_tw
                                elif tkr_two in close_data.columns and not close_data[tkr_two].dropna().empty:
                                    target_tkr = tkr_two
                                    
                                if target_tkr:
                                    # 取得最後一筆收盤價，四捨五入至小數點後兩位 (保留浮點數精準度)
                                    last_price = close_data[target_tkr].dropna().iloc[-1]
                                    close_price_dict[sid] = str(round(last_price, 2))
                    except Exception as e:
                        pass
                # ========================================================

                grouped_block['▼收盤價'] = grouped_block['代號'].map(close_price_dict).fillna('-')

                def sort_logic(row):
                    try:
                        prices = [float(p) for p in str(row['成交價']).split(' / ')]
                        avg_p = sum(prices) / len(prices)
                        close_p = float(str(row['▼收盤價']).replace(',', ''))
                        return 1 if close_p > avg_p else 2 if close_p == avg_p else 3
                    except: return 4
                
                grouped_block['__rank'] = grouped_block.apply(sort_logic, axis=1)
                grouped_block = grouped_block.sort_values(by=['__rank', '代號'], ascending=[True, True])
                
                dynamic_price_col = f"▼{block_date[-4:]} 成交價"
                display_df = grouped_block[['代號', '股票名稱', '交易別', '成交價', '▼收盤價', '成交張數', '總額(億)']].copy()
                display_df = display_df.rename(columns={'成交價': dynamic_price_col})

                def highlight_price(row):
                    styles = [''] * len(row)
                    try:
                        target_idx = row.index.get_loc(dynamic_price_col)
                        prices = [float(p) for p in str(row[dynamic_price_col]).split(' / ')]
                        avg_p = sum(prices) / len(prices)
                        c_p = float(str(row['▼收盤價']).replace(',', ''))
                        
                        # 收盤價 > 均價 顯示紅字，相等顯橘字，低於顯綠字
                        if c_p > avg_p:
                            styles[target_idx] = 'color: #FF4B4B; font-weight: bold;'
                        elif c_p == avg_p:
                            styles[target_idx] = 'color: #FFA500; font-weight: bold;'
                        else:
                            styles[target_idx] = 'color: #00E272; font-weight: bold;'
                    except: pass
                    return styles

                # 使用 pandas 內建 Style 渲染至 st.dataframe
                st.dataframe(display_df.style.apply(highlight_price, axis=1), use_container_width=True, hide_index=True)
                
            else:
                st.error("⚠️ 欄位名稱無法匹配，請確認爬蟲格式。")
        else:
            st.info("🕒 目前查無今日鉅額交易資料，請確認資料夾中是否有對應的 CSV 檔案。")


    # ==================== Tab 2: 歷史防守價追蹤表 ====================
    with tab_hist:
        hist_matrix, detected_files = build_historical_block_matrix()
        
        if detected_files:
            st.caption(f"📡 已自動讀取 {len(detected_files)} 天的歷史檔案，組合中...")
            
        if hist_matrix is not None and not hist_matrix.empty:
            st.dataframe(hist_matrix, use_container_width=True, hide_index=True)
        else:
            st.info("📂 資料夾內尚無足夠的歷史交易紀錄，請確認檔名包含「鉅額」字樣。")

  
# ==========================================以上網頁核心區塊↑↑↑↑↑
# ==========================================
# 🎭 幕後無縫換頁引擎 (放在最後)
# ==========================================
# 如果程式順利走到這裡(沒有被上面的 st.stop 攔截)，就渲染按鈕
nav_manager.render_proxy_buttons()
