# views/sidebar.py
import streamlit as st
import pandas as pd
import requests
import re
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_utils import get_latest_csv, get_prev_csv

# ==========================================
# 🌟 "側邊雙視窗" 變數雷達與自動載入引擎 
# ==========================================
KEY_MAP = {
    'b1_final_df': ['b1_final_df', 'my_final_df'],
    'b2_1': ['b2_1', 'df_blk2_1'],
    'b2_2': ['b2_2', 'df_blk2_2'],
    'b2_3': ['b2_3', 'df_blk2_3'],
    'b2_4': ['b2_4', 'df_blk2_4'],
    'b3_main': ['b3_main', 'df_blk3_main'],
    'b4_margin_pct': ['b4_margin_pct', 'df_margin_pct'],
    'b4_short_pct': ['b4_short_pct', 'df_short_pct'],
    'b4_margin_plus_pct': ['b4_margin_plus_pct', 'df_margin_plus_pct'],
    'b4_margin_vol': ['b4_margin_vol', 'df_margin_vol'],
    'b4_short_vol': ['b4_short_vol', 'df_short_vol'],
    'b4_margin_plus_vol': ['b4_margin_plus_vol', 'df_margin_plus_vol'],
    'b5_400': ['b5_400', 'df_blk5'],
    'b5_1000': ['b5_1000', 'df_blk5_1000'],
    'b7_main': ['b7_main'],
    'b7_pledge': ['b7_pledge'],                 # 🟢 新增：董監最新質押比
    'b7_pledge_history': ['b7_pledge_history']  # 🟢 新增：董監質押歷史趨勢
    # 新增其他變數載入頁面，如'b7_main': ['b7_main'],--步驟2
}

def get_sidebar_df(primary_key):
    """🌟 側邊欄專用萬能變數雷達：支援新舊 Session State 鑰匙"""
    aliases = KEY_MAP.get(primary_key, [primary_key])
    for k in aliases:
        df = st.session_state.get(k)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return pd.DataFrame()

def ensure_b1_to_b5_loaded(DATA_DIR):
    """🚀 背景自動補載機制：當搜尋時發現數據缺失，自動觸發 B1~B5 後台同步引擎"""
    if not DATA_DIR or not os.path.exists(DATA_DIR):
        return
    # 放入所有擷入頁面--步驟3
    # B1 補載
    if get_sidebar_df('b1_final_df').empty:
        try:
            from views.b1_page import sync_b1_data
            sync_b1_data(DATA_DIR)
        except: pass

    # B2 補載
    if get_sidebar_df('b2_1').empty:
        try:
            from views.b2_page import sync_b2_data
            sync_b2_data(DATA_DIR)
        except: pass

    # B3 補載
    if get_sidebar_df('b3_main').empty:
        try:
            from views.b3_page import sync_b3_data
            sync_b3_data(DATA_DIR)
        except: pass

    # B4 補載
    if get_sidebar_df('b4_margin_pct').empty:
        try:
            from views.b4_page import sync_b4_data
            sync_b4_data(DATA_DIR)
        except: pass

    # B5 補載
    if get_sidebar_df('b5_1000').empty:
        try:
            from views.b5_page import sync_b5_data
            sync_b5_data(DATA_DIR)
        except: pass
    # B7 補載 (貼在 B5 補載邏輯的下方)
    if get_sidebar_df('b7_main').empty:
        try:
            from views.b7_page import sync_b7_data
            sync_b7_data(DATA_DIR)
        except: pass
    # 🟢 新增：B7 最新質押比 補載
    if get_sidebar_df('b7_pledge').empty:
        try:
            from views.b7_page import sync_pledge_data
            sync_pledge_data(DATA_DIR)
        except: pass

    # 🟢 新增：B7 質押歷史趨勢 補載
    if get_sidebar_df('b7_pledge_history').empty:
        try:
            from views.b7_page import sync_pledge_history_data
            sync_pledge_history_data(DATA_DIR)
        except: pass
# ==========================================
# 🌟 快搜各頁面與顯示工具函數區 
# ==========================================
def robust_search_engine(df, query):
    """
    強化版搜尋引擎：先精準比對 (Exact Match)，找不到才模糊比對 (Partial Match)
    解決權證 (如 054430) 攔截真實代號 (5443) 的問題
    """
    if df is None or df.empty: return pd.DataFrame()
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    query = str(query).strip()
    if not query: return pd.DataFrame()

    # 1. 找出正確的欄位名稱
    col_id = '股票代號' if '股票代號' in df.columns else ('代號' if '代號' in df.columns else None)
    col_name = '股票名稱' if '股票名稱' in df.columns else ('名稱' if '名稱' in df.columns else None)

    # 確保欄位都是乾淨的字串，並強制剃除 Pandas 產生的 .0
    if col_id:
        df[col_id] = df[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    if col_name:
        df[col_name] = df[col_name].astype(str).str.strip()

    # ==========================================
    # 🌟 第一階段：【嚴格精準比對】
    # ==========================================
    exact_mask = pd.Series(False, index=df.index)
    if col_id:
        exact_mask = exact_mask | (df[col_id] == query)
    if col_name:
        exact_mask = exact_mask | (df[col_name].str.lower() == query.lower())

    # 如果有找到「完全一模一樣」的，就直接回傳，不再往下找！
    exact_result = df[exact_mask]
    if not exact_result.empty:
        return exact_result

    # ==========================================
    # 🌟 第二階段：【模糊包含比對】 (只有精準找不到時才啟動)
    # ==========================================
    partial_mask = pd.Series(False, index=df.index)
    if col_id:
        partial_mask = partial_mask | df[col_id].str.contains(query, na=False)
    if col_name:
        partial_mask = partial_mask | df[col_name].str.contains(query, na=False, case=False)

    return df[partial_mask]

# ==========================================
def scan_and_display(title, session_key, query):
    st.markdown(f"<h6 style='color: #E2E8F0; margin-bottom: 5px;'>{title}</h6>", unsafe_allow_html=True)
    df = get_sidebar_df(session_key)
    if df.empty:
        st.write("⚪ 尚未載入資料表")
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

# 🤖 [AI 籌碼訊號] 診斷
def generate_stock_commentary(query):
    if not query: return ""
    
    score = 0
    warns = []
    
    # 🎯 掃描 1: 法人買超診斷 (區塊2 - 共4個表)
    for key in ['b2_1', 'b2_2', 'b2_3', 'b2_4']:
        df = get_sidebar_df(key)
        if not df.empty:
            res = robust_search_engine(df, query)
            if not res.empty:
                score += 1.5

    # 📅 掃描 2: 法人連買診斷 (區塊3)
    df_b3 = get_sidebar_df('b3_main')
    if not df_b3.empty:
        res = robust_search_engine(df_b3, query)
        if not res.empty:
            score += len(res) * 1.5

    # 🔄 掃描 3: 券資有利排名 (區塊4 - 共6個表)
    for key in ['b4_margin_pct', 'b4_short_pct', 'b4_margin_plus_pct', 'b4_margin_vol', 'b4_short_vol', 'b4_margin_plus_vol']:
        df = get_sidebar_df(key)
        if not df.empty:
            res = robust_search_engine(df, query)
            if not res.empty:
                score += 0.5

    # 💰 掃描 4: 大戶動向診斷 (區塊5)
    def check_big_holder(key):
        df = get_sidebar_df(key)
        if not df.empty:
            res = robust_search_engine(df, query)
            if not res.empty:
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

# 🤖 [AI 技術型態訊號] 判斷
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
        df = get_sidebar_df(key)
        if not df.empty:
            res = robust_search_engine(df, query)
            if not res.empty:
                display_id = res.iloc[0].get('股票代號', query)
                display_name = res.iloc[0].get('股票名稱', '-')
                break
                
    for label, key in keys_and_labels:
        df = get_sidebar_df(key)
        if not df.empty:
            res = robust_search_engine(df, query)
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

# ==========================================
# 📈 側邊雙視窗 K 線圖與技術分析引擎
# ==========================================
@st.cache_data(ttl=900)
def fetch_yfinance_data(ticker, period="3y"):
    import yfinance as yf
    try:
        df = yf.download(ticker, period=period, progress=False)
        return df
    except:
        return pd.DataFrame()

def render_technical_chart(stock_id, timeframe="日線", selected_mas=[], show_rsi=False, show_macd=False, show_kd=False):
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

# ======================================================
# 分頁功能渲染區: 🔹 大盤籌碼 🔹 選擇權 🔹 總經導航
# ======================================================
def get_diff_ui(current, prev):
    if prev is None or pd.isna(prev): return ""
    diff = current - prev
    if diff > 0: return f" <span style='color: #ff4b4b; font-size: 11px;'>(+{int(diff):,})</span>"
    elif diff < 0: return f" <span style='color: #00e676; font-size: 11px;'>({int(diff):,})</span>"
    return ""

def render_sidebar_market_summary():
    df_spot, date_spot = get_latest_csv("三大法人買賣超金額")
    df_fut, _ = get_latest_csv("三大法人期貨多空")
    df_fut_prev = get_prev_csv("三大法人期貨多空", date_spot)
    df_margin, margin_csv_name = get_latest_csv("融資融券餘額")
    
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

    twse_vol_today, twse_diff = 0.0, 0.0
    if df_twse is not None and len(df_twse) >= 2:
        try:
            v_today = float(str(df_twse.iloc[-1]['成交金額']).replace(',', '')) / 100000000
            v_yest = float(str(df_twse.iloc[-2]['成交金額']).replace(',', '')) / 100000000
            twse_vol_today = v_today
            twse_diff = v_today - v_yest
        except: pass

    tpex_vol_today, tpex_diff = 0.0, 0.0
    if df_tpex is not None and len(df_tpex) >= 2:
        try:
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
    
    tw_c, tw_s = get_color(twse_diff)
    tp_c, tp_s = get_color(tpex_diff)
    tot_c, tot_s = get_color(total_diff)

    html = f"<div style='font-size: 13px; color: #00D2FF;'>基準日：{date_spot}</div>"
    
    html += "<table style='width: 100%; text-align: center; border-collapse: collapse; margin-top: 5px; font-size: 14px;'>"
    html += "<tr style='border-bottom: 1px solid #555; background-color: #262730;'>"
    html += "<th style='padding: 5px;'>法人</th><th style='padding: 5px;'>現貨(億)</th><th style='padding: 5px;'>TX未平倉</th></tr>"
    html += f"<tr><td style='padding: 4px;'>🌐 外資</td><td style='color: {f_c}; vertical-align: middle;'>{f_s}</td><td style='color: {fo_c}; vertical-align: middle; padding-bottom: 6px;'>{fo_s}{get_diff_ui(oi_foreign, oi_f_prev)}</td></tr>"
    html += f"<tr><td style='padding: 4px;'>🏦 投信</td><td style='color: {t_c}; vertical-align: middle;'>{t_s}</td><td style='color: {to_oc}; vertical-align: middle; padding-bottom: 6px;'>{to_os}{get_diff_ui(oi_trust, oi_t_prev)}</td></tr>"
    html += f"<tr><td style='padding: 4px;'>🏢 自營商</td><td style='color: {d_c}; vertical-align: middle;'>{d_s}</td><td style='color: {do_c}; vertical-align: middle; padding-bottom: 6px;'>{do_os}{get_diff_ui(oi_dealer, oi_d_prev)}</td></tr>"
    
    tot_prev = (oi_f_prev + oi_t_prev + oi_d_prev) if oi_f_prev is not None else None
    html += f"<tr style='border-top: 1px solid #555; font-weight: bold;'><td style='padding: 4px;'> 合計</td><td style='color: {to_c}; vertical-align: middle;'>{to_s}</td><td style='color: {too_c}; vertical-align: middle; padding-bottom: 6px;'>{too_os}{get_diff_ui(total_oi, tot_prev)}</td></tr>"
    html += "</table>"
    
    if total_vol_today > 0:
        html += "<div style='margin-top: 8px; padding: 6px; background-color: #1e1e24; border: 1px solid #555; border-radius: 5px; font-size: 13px;'>"
        html += "<div style='font-weight: bold; margin-bottom: 4px;'>市場成交量 (億)</div>"
        html += f"<div style='color: #aaa; margin-top: 2px;'> 上市 <span style='float: right; color: #fff;'>{twse_vol_today:,.1f} <span style='color: {tw_c}; font-size: 11px; margin-left: 2px;'>({tw_s})</span></span></div>"
        html += f"<div style='color: #aaa; margin-top: 2px;'> 上櫃 <span style='float: right; color: #fff;'>{tpex_vol_today:,.1f} <span style='color: {tp_c}; font-size: 11px; margin-left: 2px;'>({tp_s})</span></span></div>"
        html += "<div style='border-top: 1px dashed #555; margin: 4px 0;'></div>"
        html += f"<div style='color: #fbbf24; font-weight: bold; margin-top: 2px;'> 總量 <span style='float: right;'>{total_vol_today:,.1f} <span style='color: {tot_c}; font-size: 11px; margin-left: 2px;'>({tot_s})</span></span></div>"
        html += "</div>"
    
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

@st.cache_data(ttl=300) 
def fetch_macro_indicators():
    data = {
        "vix": {"value": None, "pct": None},
        "vixtwn": {"value": None, "pct": None},
        "fng": {"score": None, "rating": "無法取得"}
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }

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

    prev_vix = None
    try:
        res_daily = requests.get("https://www.taifex.com.tw/cht/3/vixInfo", headers=headers, timeout=5)
        if res_daily.status_code == 200:
            matches_d = re.findall(r'(\d{3,4}/\d{2}/\d{2})[\s\S]{1,100}?([1-9]\d{1,2}\.\d{2,4})', res_daily.text)
            if matches_d:
                data["vixtwn"]["value"] = float(matches_d[-1][1])
                if len(matches_d) >= 2:
                    prev_vix = float(matches_d[-2][1])
                    data["vixtwn"]["pct"] = (data["vixtwn"]["value"] - prev_vix) / prev_vix * 100
    except: pass

    try:
        res_min = requests.get("https://www.taifex.com.tw/cht/7/vixMinNew", headers=headers, timeout=5)
        if res_min.status_code == 200:
            matches_m = re.findall(r'(\d{2}:\d{2}:\d{2})[\s\S]{1,100}?([1-9]\d{1,2}\.\d{2,4})', res_min.text)
            if matches_m:
                latest_vix = float(matches_m[-1][1])
                data["vixtwn"]["value"] = latest_vix
                if prev_vix:
                    data["vixtwn"]["pct"] = (latest_vix - prev_vix) / prev_vix * 100
    except: pass

    if data["vixtwn"]["value"] is None:
        try:
            res_hi = requests.get("https://histock.tw/stock/tcharti.aspx?no=VIXTWN", headers=headers, timeout=5)
            if res_hi.status_code == 200:
                match = re.search(r'CPHB1_lblPrice[^>]*>\s*([\d\.]+)\s*<', res_hi.text)
                if match:
                    data["vixtwn"]["value"] = float(match.group(1))
                    data["vixtwn"]["pct"] = 0.0
        except: pass

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
# 🚀 終極局部渲染魔法：將整個側邊視窗獨立為「不閃爍區塊」
# =======================================================
@st.fragment
def render_sidebar_war_room(STOCK_DICT, DATA_DIR="data"):
    st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
    # ==========================================
    # 🌟 新增：追蹤名單聯動顯示區塊 (放在最頂端)
    # ==========================================
    if st.session_state.get("logged_in", False):
        selected_stock = st.session_state.get("selected_watch_stock", None)
        
        if selected_stock:
            st.markdown(f"### 🎯 焦點標的：{selected_stock}")
            
            # 萃取出純數字代號
            stock_code_match = re.search(r'\d+', selected_stock)
            if stock_code_match:
                stock_code = stock_code_match.group()
                
                # 建立各大財經網站的快速連結 (使用 columns 橫排，節省空間)
                col_l1, col_l2, col_l3 = st.columns(3)
                with col_l1: 
                    st.markdown(f"[🔗Goodinfo](https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={stock_code})")
                with col_l2: 
                    st.markdown(f"[🔗Yahoo](https://tw.stock.yahoo.com/quote/{stock_code})")
                with col_l3: 
                    st.markdown(f"[🔗Fugle](https://www.fugle.tw/ai/{stock_code})")
            else:
                st.info("無法解析股票代碼，請確認追蹤名稱中包含數字代號。")
            
            # 關閉焦點標的的按鈕 (加上 key 避免與其他按鈕衝突)
            st.write("") # 空一行
            if st.button("❌ 關閉焦點", use_container_width=True, key="close_focus_btn"):
                st.session_state["selected_watch_stock"] = None

                # 關閉焦點時，同步清空下方的搜尋框(watchlist自訂義用)
                st.session_state["global_search_final"] = ""

                st.rerun()
                
            st.markdown("<hr style='border-color: #38BDF8; margin: 15px 0px;'>", unsafe_allow_html=True)
    # ==========================================

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

    with st.container(border=True):
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
            st.button("→", key="btn_go", type="tertiary", use_container_width=True, help="送出搜尋")
            
        with c_btn_clear:
            st.button("×", key="btn_clear", type="tertiary", on_click=clear_search, use_container_width=True, help="清空欄位")

        pure_stock_id = ""
        display_name = search_query
        
        if search_query:
            query_clean = search_query.strip()
            
            # 搜尋當下即時觸發 B1~B5 背景補載機制
            ensure_b1_to_b5_loaded(DATA_DIR)
            
            industry_label = "未分類"
            
            # ==========================================
            # 🚀 修復：兩段式字典解析 (解決權證攔截問題)
            # ==========================================
            if STOCK_DICT:
                exact_match = False
                    
                # 🌟 第一階段：優先精準比對 (代號完全相等 或 名稱完全相等)
                for k, v in STOCK_DICT.items():
                    stock_id = str(v.get("id", ""))
                    stock_name = str(v.get("name", ""))
                    if query_clean == stock_id or query_clean == stock_name:
                        pure_stock_id = stock_id
                        display_name = f"{stock_id} {stock_name}"
                        industry_label = v.get("industry", "未分類")
                        exact_match = True
                        break
                        
                # 🌟 第二階段：如果精準比對找不到，才啟動模糊包含比對
                if not exact_match:
                    for k, v in STOCK_DICT.items():
                        if query_clean in k or query_clean in str(v.get("name", "")):
                            pure_stock_id = str(v.get("id", ""))
                            display_name = f"{v.get('id', '')} {v.get('name', '')}"
                            industry_label = v.get("industry", "未分類")
                            break
                                    
        if pure_stock_id == "":
            match_num = re.search(r'\d+', query_clean)
            if match_num: pure_stock_id = match_num.group(0)

            st.markdown(f"### 🎯 綜合診斷標的：<span style='color: #00D2FF;'>{display_name}</span> <span style='font-size:16px; background-color:#1E293B; padding:4px 10px; border-radius:6px; color:#38BDF8; border: 1px solid #38BDF8; margin-left:10px;'>🏷️ {industry_label}</span>", unsafe_allow_html=True)

            # ==========================================
            # 🚀 融合 AI 訊號區
            # ==========================================
            target_query = pure_stock_id if pure_stock_id else search_query
            old_ai_msg = generate_stock_commentary(target_query)

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

            # ==========================================
            # 📊 K 線控制台
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

            # ==========================================
            # 👑 區塊 1 ~ 5：數據庫展演 (對接萬能變數雷達)
            # ==========================================
            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>👑 區塊 1：短中長線三大法人持股變化</h4>", unsafe_allow_html=True)
            
            df_b1 = get_sidebar_df('b1_final_df')
            if not df_b1.empty:
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

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>🎯 區塊 2：法人買超診斷</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: scan_and_display("🌐 外資 5 日淨買佔成交量", 'b2_1', search_query)
            with c2: scan_and_display("🏦 投信 5 日淨買佔成交量", 'b2_2', search_query)
            c3, c4 = st.columns(2)
            with c3: scan_and_display("🌐 外資 5 日淨買佔發行量", 'b2_3', search_query)
            with c4: scan_and_display("🏦 投信 5 日淨買佔發行量", 'b2_4', search_query)

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>📅 區塊 3：法人連買診斷 (日/週)</h4>", unsafe_allow_html=True)
            df_b3 = get_sidebar_df('b3_main')
            if not df_b3.empty:
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

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>🔄 區塊 4：券資有利排名</h4>", unsafe_allow_html=True)
            
            render_b4_panorama("5日幅度變動排名", [('📉 融資減少', 'b4_margin_pct'), ('📉 借券減少', 'b4_short_pct'), ('📈 融券增加', 'b4_margin_plus_pct')], search_query)
            st.write("") 
            render_b4_panorama("5日張數變動排名", [('📉 融資減少', 'b4_margin_vol'), ('📉 借券減少', 'b4_short_vol'), ('📈 融券增加', 'b4_margin_plus_vol')], search_query)

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>💰 區塊 5：大腿動向</h4>", unsafe_allow_html=True)
            
            col_400, col_1000 = st.columns(2)
            with col_400: scan_and_display("💎 400張以上大戶動向", 'b5_400', search_query)
            with col_1000: scan_and_display("🐳 1000張以上超級大戶動向", 'b5_1000', search_query)
            # 👇 
            #區塊 7 新增--步驟4
            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>👔 區塊 7：董監動向</h4>", unsafe_allow_html=True)
            # 🟢 依序將三個表單渲染至側邊搜尋視窗中
            scan_and_display("🔹 董監最新質押比", 'b7_pledge', search_query)
            scan_and_display("🔹 董監質押歷史趨勢", 'b7_pledge_history', search_query)
            scan_and_display("🔹 董監持股比增減", 'b7_main', search_query)
            
    # 💡 當搜尋列「沒有內容」時，顯示大盤總經
    if not search_query:
        st.write("---") 
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
