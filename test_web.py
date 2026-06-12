import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import re
import datetime
import requests  
import pytz  
# ==========================================
# 1. 網頁基本設定 & 目錄路徑初始化
# ==========================================
st.set_page_config(page_title="台股籌碼五大核心矩陣儀表板", layout="wide")
# 👇 新增啟動 Google Sheets 永久連線引擎紀錄爬蟲歷史成績
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TxHDahg8ul6lmUtDN-7X75cBXbkU0jaZ3M9zg6exBgU/edit?usp=sharing"
# 👉 步驟 1：先集中宣告所有的路徑變數
DATA_DIR = "./Goodinfo_Rankings"
SCORE_HISTORY_DIR = os.path.join(DATA_DIR, "ScoreHistory")
MARKET_HISTORY_DIR = os.path.join(DATA_DIR, "MarketHistory")
BLOCK_HISTORY_DIR = os.path.join(DATA_DIR, "BlockHistory")

# 👉 步驟 2：
# ==========================================
# 🛑 隱形急救引擎 (請置於程式最頂端，絕對不要刪除！)
# ==========================================
# 即使不顯示區塊 0 面板，這段程式碼也必須存在，
# 否則側邊欄導航會因為讀不到歷史檔案而顯示「查無資料」。
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(SCORE_HISTORY_DIR): os.makedirs(SCORE_HISTORY_DIR)
if not os.path.exists(MARKET_HISTORY_DIR): os.makedirs(MARKET_HISTORY_DIR)
if not os.path.exists(BLOCK_HISTORY_DIR): os.makedirs(BLOCK_HISTORY_DIR)

# 定義路徑
backup_df_path = os.path.join(DATA_DIR, "sidebar_twse_df_backup.csv")
backup_margin_path = os.path.join(DATA_DIR, "sidebar_margin_backup.csv")

# 1. 補法人備援
if not os.path.exists(backup_df_path):
    pd.DataFrame({
        '單位名稱': ['合計'],
        '買賣差額': ['102770738307']
    }).to_csv(backup_df_path, index=False, encoding='utf-8-sig')

# 2. 補融資備援
if not os.path.exists(backup_margin_path):
    pd.DataFrame([{"today_bal": 556359646.0, "prev_bal": 535025764.0}]).to_csv(backup_margin_path, index=False, encoding='utf-8-sig')
# ==========================================
# ==========================================
# ==========置頂區塊測試區==================
# ==========置頂區塊測試區==================
# ==========置頂區塊測試區==================
# ==========================================
# 🚨 區塊 00 測試區：
# ==========================================
# ==========置頂區塊測試區==================
# ==========置頂區塊測試區==================
# ==========置頂區塊測試區==================





#======測試爬蟲=====

#======測試爬蟲=====


# ==========================================
# 🧰 全站共用核心工具箱 (剛剛不小心消失的救命工具)
# ==========================================
def extract_date_from_name(filename):
    """從檔名中萃取出 8 碼日期，供全站各區塊排序使用"""
    match = re.search(r'\d{8}', os.path.basename(filename))
    return match.group(0) if match else "00000000"

def robust_read_csv(file_path):
    """強硬讀取法：解決各種中文編碼亂碼問題"""
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# ==========================================
# 🗂️ 台股代號與名稱產業類別 萬用字典引擎 (後台靜默運作版)
# ==========================================
@st.cache_data(ttl=3600)
def get_stock_dictionary():
    """讀取證交所 ISIN 檔案，在後台安靜地建立雙向對照表"""
    import re
    mapping = {}
    
    search_patterns = [
        os.path.join(DATA_DIR, "*辨識號碼*.txt"),
        os.path.join("./goodinfo_rankings", "*辨識號碼*.txt"),
        "./*辨識號碼*.txt"
    ]
    dict_files = []
    for pattern in search_patterns:
        dict_files.extend(glob.glob(pattern))
        
    if not dict_files:
        return mapping
        
    target_file = dict_files[0]
    raw_lines = []
    
    for encoding in ['utf-8-sig', 'utf-8', 'cp950', 'utf-16', 'big5']:
        try:
            with open(target_file, 'r', encoding=encoding) as f:
                raw_lines = f.readlines()
            if len(raw_lines) > 10:
                break
        except:
            continue
            
    for line in raw_lines:
        parts = line.split('\t') if '\t' in line else line.split(',')
        if len(parts) >= 5:
            name_part = parts[0].strip()
            industry = parts[4].strip()
            
            clean_name = re.sub(r'[\s　]+', ' ', name_part).strip()
            tokens = clean_name.split(' ')
            
            if len(tokens) >= 2:
                sid = tokens[0].strip()
                sname = tokens[1].strip()
                
                if sid.isdigit():
                    # 建立雙向字典 (輸入代號或名稱都能通)
                    mapping[sname] = {"id": sid, "name": sname, "industry": industry}
                    mapping[sid] = {"id": sid, "name": sname, "industry": industry}
                    
    return mapping

# 在系統啟動時，直接載入這本字典
STOCK_DICT = get_stock_dictionary()
# ==========================================
#以上原始區塊0
# ==========================================
# ==========================================
# 📡 證交所 API 直連：後台資料抓取引擎 (保留給側邊欄使用)
# ==========================================
import requests
import datetime
import pandas as pd
import streamlit as st

@st.cache_data(ttl=600)
def fetch_twse_institutional_data():
    """自動連線證交所抓取今日三大法人買賣超 (BFI82U)"""
    url = "https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        if data.get('stat') == 'OK':
            return data.get('title', '三大法人買賣金額統計表'), pd.DataFrame(data['data'], columns=data['fields'])
        return None, None
    except:
        return None, None

@st.cache_data(ttl=600)
def fetch_block_trades():
    """抓取證交所每日鉅額交易明細 (BFIAUU)"""
    url = "https://www.twse.com.tw/rwd/zh/block/BFIAUU?response=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        if data.get('stat') == 'OK':
            return pd.DataFrame(data['data'], columns=data['fields'])
        return pd.DataFrame()
    except:
        return pd.DataFrame()



# ==========================================
# 🌌 網頁格式顏色搭配注入極致黑看盤軟體專屬風格樣式 (全站深色化 + 表格與按鈕優化)
# ==========================================
st.markdown(
    """
    <style>
    /* 1. 變更全站主背景色 */
    .stApp { background-color: #0A0D14 !important; }
    
    /* 2. 強制標題與內文變成明亮的灰白 */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText { color: #E2E8F0 !important; }
    
    /* 3. 隱藏預設的通知背景 */
    [data-testid="stAlert"] { background-color: transparent !important; border: 1px solid #2D3748 !important; }
    
    /* 4. 側邊欄背景色與邊框 */
    [data-testid="stSidebar"] { background-color: #111622 !important; border-right: 1px solid #1E293B; }
    
    /* 5. 輸入框等元件 */
    .stTextInput>div>div>input { background-color: #1A202C !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }
    
    /* 6. 表格深色化修正 */
    div[data-testid="stDataFrame"] { background-color: #111622 !important; border: 1px solid #1E293B !important; border-radius: 6px; }

    /* 7. 超連結優化 */
    [data-testid="stSidebar"] a { color: #00D2FF !important; text-decoration: none !important; font-weight: 500 !important; letter-spacing: 0.5px; transition: all 0.3s ease; }
    [data-testid="stSidebar"] a:hover { color: #FFD700 !important; text-shadow: 0px 0px 8px rgba(255, 215, 0, 0.5); }
    
    /* 8. 🔴 全局按鈕與連結按鈕護眼暗黑化 (解決刺眼問題) */
    .stButton > button, .stLinkButton > a {
        background-color: #1E293B !important; /* 深石板灰 */
        color: #94A3B8 !important; /* 低調灰字 */
        border: 1px solid #334155 !important;
        transition: all 0.2s ease-in-out;
    }
    /* 滑鼠懸停時才亮起科技藍 */
    .stButton > button:hover, .stLinkButton > a:hover {
        border-color: #00D2FF !important;
        color: #00D2FF !important;
        box-shadow: 0 0 8px rgba(0, 210, 255, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ==========================================
# 🏆 預留置頂空間：頂級選股池容器
# ==========================================
top_pool_container = st.container()

# ==========================================
# 🧠 AI 量化評語生成引擎 (土洋對作/換手升級版)
# ==========================================
def generate_stock_commentary(row):
    """
    根據選股池的綜合數據，自動生成一段人話評語
    """
    score = row.get('總分', 0)
    warns = str(row.get('法人賣出警示', ''))
    b5_trend = str(row.get('大股東動向', ''))
    
    # 判斷是否帶有賣出警示與高分
    has_warning = "⚠️" in warns
    high_score = score >= 3
    
    # 1. 矛盾訊號判定：土洋對作 / 主力強勢吃籌碼
    if has_warning and high_score:
        return f"⚔️ 【土洋對作 / 激烈換手】系統偵測到法人分歧 ({warns})，但該股依然獲得 {score} 分的高評估！這代表『一方的倒貨正被另一方(或大戶)強勢吃下』。籌碼換手後若能維持強勢(如大漲/漲停)，代表承接方實力極強，可沿短均線偏多操作，但需嚴設停損。"
        
    # 2. 致命風險判定：真倒貨、無買盤
    if has_warning and not high_score:
        return f"🚨 【風險警示】目前法人主力正在進行倒貨調節 ({warns})，且無強大買盤承接，籌碼結構面臨鬆動。建議暫避風頭，嚴控資金水位。"
    
    if "大減" in b5_trend:
        return "⚠️ 【大戶撤退】400張以上大戶出現明顯減碼跡象，主力籌碼渙散，建議先行觀望，等待籌碼沉澱。"

    # 3. 綜合分數常規判定
    if score >= 6:
        base_comment = "🔥 【強勢噴發】籌碼面極度優異！內外資法人與大戶同步共振做多，具備強大的波段上攻潛力。"
        if "大增" in b5_trend:
            base_comment += "特別是大股東籌碼大幅集中，是不可多得的強勢防守標的，建議積極關注。"
        return base_comment
        
    elif score >= 3:
        return "📈 【偏多佈局】主力籌碼持續進駐，法人買盤給予一定支撐。具備穩健的波段潛力，可逢低尋找技術面切入點。"
        
    elif score >= 1:
        return "🔄 【中性觀望】籌碼表現較為平淡，雖有零星買盤但缺乏明確的連續性方向。建議多看少做，等待更強的表態訊號。"
        
    else:
        return "❄️ 【弱勢整理】籌碼處於流失或無主力認養狀態，資金效率低。若無特殊題材發酵，短期內建議暫不考量。"
# ==========================================
# 🔍 個股籌碼快搜 "標題" (保證生效：電競風科技橫幅版)
# ==========================================
st.write("---")
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)

# 🌟 使用 100% 絕對生效的 Inline HTML 設計超高質感橫幅
st.markdown("""
<div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
            border-top: 1px solid #38bdf8; 
            border-bottom: 1px solid #38bdf8; 
            padding: 20px 20px; 
            border-radius: 10px;
            text-align: center;
            box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2);
            margin-bottom: 25px;">
    <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
        🔍 個股籌碼快搜 (戰情診斷室)
    </h2>
    <p style="color: #94a3b8; margin-top: 8px; font-size: 14px; margin-bottom: 0;">
        輸入代號一鍵聯動：AI 型態掃描 ｜ 法人動向 ｜ 1000張大戶追蹤
    </p>
</div>
""", unsafe_allow_html=True)

# 使用預設的帶邊框容器把圖表和表格包起來
with st.container(border=True):
    # ==========================================
    # 📈 繪製 K 線圖與技術分析引擎
    # ==========================================
    def render_technical_chart(stock_id, timeframe="日線", selected_mas=[], show_rsi=False, show_macd=False, show_kd=False):
        import yfinance as yf
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd

        try:
            ticker_tw = f"{stock_id}.TW"
            ticker_two = f"{stock_id}.TWO"
            
            df = yf.download(ticker_tw, period="5y", progress=False)
            if df is None or df.empty:
                df = yf.download(ticker_two, period="5y", progress=False)
                
            if df is None or df.empty:
                st.warning(f"⚠️ 無法從 Yahoo Finance 取得 {stock_id} 的即時報價。")
                return

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.loc[:, ~df.columns.duplicated()]

            if df.index.tz is not None:
                df.index = df.index.tz_convert('Asia/Taipei')
            else:
                df.index = df.index.tz_localize('UTC').tz_convert('Asia/Taipei')

            daily_df = df.copy()

            def generate_technical_signals(df):
                signals = []
                if df.empty or len(df) < 20: return signals
                
                latest_close = df['Close'].iloc[-1]
                latest_vol = df['Volume'].iloc[-1]
                
                vol_20ma = df['Volume'].rolling(window=20).mean().iloc[-2] 
                if pd.notna(vol_20ma) and vol_20ma > 0 and latest_vol > (vol_20ma * 2.5):
                    signals.append(f"🧨 爆量出擊：今日成交量達 20 日均量的 {latest_vol/vol_20ma:.1f} 倍！")

                mas = {'5MA': 5, '10MA': 10, '20MA': 20, '60MA': 60, '120MA': 120, '240MA': 240}
                for ma_name, period in mas.items():
                    if len(df) >= period:
                        ma_val = df['Close'].rolling(window=period).mean().iloc[-1]
                        if 0 < (latest_close - ma_val) / ma_val < 0.015:
                            signals.append(f"🎯 回測支撐：股價目前極度貼近 {ma_name} ({ma_val:.2f}) 關鍵支撐線。")

                if len(df) >= 20:
                    ma5 = df['Close'].rolling(5).mean().iloc[-1]
                    ma10 = df['Close'].rolling(10).mean().iloc[-1]
                    ma20 = df['Close'].rolling(20).mean().iloc[-1]
                    ma_max, ma_min = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                    if pd.notna(ma_max) and (ma_max - ma_min) / ma_min < 0.02:
                        signals.append("🌀 均線糾結：短天期 (5/10/20MA) 成本線高度重合壓縮，醞釀表態！")

                if len(df) >= 60:
                    recent_high = df['High'].iloc[-20:].max()
                    recent_low = df['Low'].iloc[-20:].min()
                    prev_high = df['High'].iloc[-40:-20].max()
                    prev_low = df['Low'].iloc[-40:-20].min()
                    
                    recent_volatility = recent_high - recent_low
                    prev_volatility = prev_high - prev_low
                    if prev_volatility > 0 and recent_volatility < (prev_volatility * 0.6):
                        signals.append("📐 型態壓縮：近一個月股價高低波幅急遽收斂，疑似三角收斂末端。")
                        
                if len(df) >= 60:
                    highest_60d = df['High'].iloc[-60:].max()
                    if df['High'].iloc[-1] >= highest_60d:
                        signals.append("🚀 波段創高：今日股價突破 60 日 (約一季) 以來新高點，上攻動能極強！")

                if len(df) >= 60:
                    ma5 = df['Close'].rolling(5).mean().iloc[-1]
                    ma10 = df['Close'].rolling(10).mean().iloc[-1]
                    ma20 = df['Close'].rolling(20).mean().iloc[-1]
                    ma60 = df['Close'].rolling(60).mean().iloc[-1]
                    ma60_prev = df['Close'].rolling(60).mean().iloc[-2] 
                    
                    if pd.notna(ma60) and (latest_close > ma5 > ma10 > ma20 > ma60) and (ma60 > ma60_prev):
                        signals.append("📈 多頭排列：短中長期均線 (5/10/20/60MA) 呈現完美多頭發散，趨勢明確翻多！")

                return signals

            tech_signals = generate_technical_signals(daily_df)

            if tech_signals:
                signal_html = "<div style='background-color: rgba(0, 210, 255, 0.1); border-left: 4px solid #00D2FF; padding: 10px; border-radius: 5px; margin-bottom: 15px;'>"
                signal_html += "<h5 style='color: #00D2FF; margin-top:0px; margin-bottom: 10px;'>📡 AI 盤中技術型態雷達</h5>"
                for sig in tech_signals:
                    signal_html += f"<p style='color: #E2E8F0; margin: 5px 0px; font-size: 15px;'>{sig}</p>"
                signal_html += "</div>"
                st.markdown(signal_html, unsafe_allow_html=True)

            if timeframe == "週線":
                daily_df = daily_df.resample('W-FRI').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
            elif timeframe == "月線":
                daily_df = daily_df.resample('ME').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()

            ma_windows = [5, 10, 20, 60, 120, 240]
            for ma in ma_windows:
                daily_df[f'{ma}MA'] = daily_df['Close'].rolling(window=ma).mean()

            close_series = daily_df['Close'].squeeze()
            
            if show_rsi:
                delta = close_series.diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                ema_gain = gain.ewm(com=13, adjust=False).mean()
                ema_loss = loss.ewm(com=13, adjust=False).mean()
                rs = ema_gain / ema_loss.replace(0, 1e-9)
                daily_df['RSI'] = 100 - (100 / (1 + rs))

            if show_macd:
                ema12 = close_series.ewm(span=12, adjust=False).mean()
                ema26 = close_series.ewm(span=26, adjust=False).mean()
                daily_df['DIF'] = ema12 - ema26
                daily_df['MACD_Sign'] = daily_df['DIF'].ewm(span=9, adjust=False).mean()
                daily_df['MACD_Hist'] = daily_df['DIF'] - daily_df['MACD_Sign']
                
            if show_kd:
                low_9 = daily_df['Low'].rolling(window=9).min()
                high_9 = daily_df['High'].rolling(window=9).max()
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
                x=daily_df.index, open=daily_df['Open'].squeeze(), high=daily_df['High'].squeeze(), 
                low=daily_df['Low'].squeeze(), close=daily_df['Close'].squeeze(), 
                name='K線', 
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
                    x=max_date, y=max_price,
                    text=f"<b>前高: {max_price:.2f}</b>",
                    showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor="#FFD700",
                    ax=0, ay=-40, 
                    font=dict(size=13, color="#FFD700"),
                    bgcolor="rgba(17, 22, 34, 0.85)", bordercolor="#FFD700", borderwidth=1, borderpad=4,
                    row=1, col=1
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
                        x=daily_df.index, y=daily_df[ma_name].squeeze(), mode='lines', 
                        name=f'{ma_name} ({latest_val})', 
                        line=dict(color=ma_config[ma_name]['color'], width=1.3),
                        hovertemplate=f"<b>{ma_name}</b>： %{{y:.2f}}<extra></extra>"
                    ), row=1, col=1)

            vol_colors = [up_color if c >= o else down_color for c, o in zip(daily_df['Close'].squeeze(), daily_df['Open'].squeeze())]
            fig.add_trace(go.Bar(
                x=daily_df.index, y=daily_df['Volume'].squeeze(), 
                name='成交量', 
                marker_color=vol_colors,
                showlegend=False, 
                hovertemplate="<b>成交量</b>： %{y}<extra></extra>"
            ), row=2, col=1)
            fig.update_yaxes(title_text="成交量", row=2, col=1, title_font=dict(size=12, color="#E2E8F0"), rangemode="nonnegative")

            current_row = 3
            if show_kd:
                fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['K'].squeeze(), mode='lines', name='K (9)', line=dict(color='#00CCFF', width=1.2), hovertemplate="<b>K</b>: %{y:.2f}<extra></extra>"), row=current_row, col=1)
                fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['D'].squeeze(), mode='lines', name='D (3)', line=dict(color='#FFCC00', width=1.2), hovertemplate="<b>D</b>: %{y:.2f}<extra></extra>"), row=current_row, col=1)
                fig.add_hline(y=80, line_dash="dash", line_color="rgba(240,90,90,0.4)", row=current_row, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="rgba(80,200,120,0.4)", row=current_row, col=1)
                fig.update_yaxes(title_text="KD(9,3,3)", row=current_row, col=1, title_font=dict(size=11, color="#E2E8F0"))
                current_row += 1
                
            if show_rsi:
                fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['RSI'].squeeze(), mode='lines', name='RSI (14)', line=dict(color='#E1BEE7', width=1.5), hovertemplate="<b>RSI</b>: %{y:.2f}<extra></extra>"), row=current_row, col=1)
                fig.add_hline(y=80, line_dash="dash", line_color="rgba(240,90,90,0.4)", row=current_row, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="rgba(80,200,120,0.4)", row=current_row, col=1)
                fig.update_yaxes(title_text="RSI(14)", row=current_row, col=1, title_font=dict(size=11, color="#E2E8F0"))
                current_row += 1

            if show_macd:
                fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['DIF'].squeeze(), mode='lines', name='DIF', line=dict(color='#FFF', width=1)), row=current_row, col=1)
                fig.add_trace(go.Scatter(x=daily_df.index, y=daily_df['MACD_Sign'].squeeze(), mode='lines', name='MACD', line=dict(color='#FFCC00', width=1)), row=current_row, col=1)
                hist_colors = [up_color if h >= 0 else down_color for h in daily_df['MACD_Hist'].squeeze()]
                fig.add_trace(go.Bar(x=daily_df.index, y=daily_df['MACD_Hist'].squeeze(), name='柱狀圖', marker_color=hist_colors), row=current_row, col=1)
                fig.update_yaxes(title_text="MACD", row=current_row, col=1, title_font=dict(size=11, color="#E2E8F0"))
                current_row += 1

            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=500 + (rows - 1) * 110, 
                template='plotly_dark',       
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',  
                margin=dict(l=10, r=65, t=30, b=10), 
                hovermode='x unified',
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
            
        except Exception as e:
            st.error(f"❌ 繪製 K 線圖時發生錯誤: {str(e)}")

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
        st.markdown(f"<h5 style='color: #E2E8F0;'>{title}</h5>", unsafe_allow_html=True)
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
                    import pandas as pd
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

    # ==========================================
    # 🎯 搜尋輸入框
    # ==========================================
    search_query = st.text_input("輸入代號或名稱 (例如: 3231 或 緯創 或 3231緯創)：", key="global_search_final")

    pure_stock_id = ""
    display_name = search_query

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

        st.markdown(f"### 🎯 綜合診斷標的：<span style='color: #00D2FF;'>{display_name}</span> <span style='font-size:16px; background-color:#1E293B; padding:4px 10px; border-radius:6px; color:#38BDF8; border: 1px solid #38BDF8; margin-left:10px;'>🏷️ {industry_label}</span>", unsafe_allow_html=True)

        pool_df = st.session_state.get('top_pool_df', pd.DataFrame())
        target_score = None
        current_stock_id = pure_stock_id 
        delta_val = 0.0

        if not pool_df.empty:
            match = robust_search_engine(pool_df, current_stock_id) if current_stock_id else robust_search_engine(pool_df, search_query)
            if not match.empty:
                target_score = match.iloc[0].get('總分', 0)
                delta_val = match.iloc[0].get('Delta (日變動)', 0.0) 

        if target_score is not None and current_stock_id != "":
            delta = delta_val 
            delta_color = "#FF4B4B" if delta > 0 else "#00CC66" if delta < 0 else "#94A3B8"
            delta_symbol = "🔥" if delta > 0 else "🚨" if delta < 0 else "🔄"
            delta_str = f"+{delta}" if delta > 0 else f"{delta}" 
            
            st.markdown(f"""
            #### 🏆 系統綜合評分：<span style='color:#FFD700; font-size:24px; text-shadow: 0 0 10px rgba(255,215,0,0.5);'>**{target_score}**</span> 分 
            <span style='color:{delta_color}; font-size:16px; margin-left:15px;'>{delta_symbol} Delta變化: **{delta_str}**</span>
            <span style='color:#94A3B8; font-size:14px; font-weight:normal; margin-left:10px;'>(評分數據僅供參考)</span>
            """, unsafe_allow_html=True)
        else:
            st.markdown("#### 🏆 系統綜合評分：<span style='color:#64748B; font-size:18px;'>未達綜合進榜標準 (0分)</span>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
        if 'show_kline' not in st.session_state: st.session_state.show_kline = False
        if 'kline_period' not in st.session_state: st.session_state.kline_period = "日線"

        button_label = "❌ 關閉技術 K 線圖" if st.session_state.show_kline else "📊 載入最新技術 K 線圖"
        if st.button(button_label, use_container_width=True):
            st.session_state.show_kline = not st.session_state.show_kline
            st.rerun()

        if st.session_state.show_kline:
            if 'pure_stock_id' in locals() and pure_stock_id != "":          
                st.markdown("##### ⚙️ 技術線圖與指標配置面板")
                tf_c1, tf_c2, tf_c3, _space = st.columns([1, 1, 1, 5])
                
                if tf_c1.button("日K", use_container_width=True, key="btn_p_day"):
                    st.session_state.kline_period = "日線"
                    st.rerun()
                if tf_c2.button("週K", use_container_width=True, key="btn_p_week"):
                    st.session_state.kline_period = "週線"
                    st.rerun()
                if tf_c3.button("月K", use_container_width=True, key="btn_p_month"):
                    st.session_state.kline_period = "月線"
                    st.rerun()
                
                ind_c1, ind_c2, ind_c3 = st.columns(3)
                chk_kd = ind_c1.checkbox("顯示 KD (9,3,3)", value=False, key="kd_chk")
                chk_macd = ind_c2.checkbox("顯示 MACD (12,26,9)", value=False, key="macd_chk")
                chk_rsi = ind_c3.checkbox("顯示 RSI (14)", value=False, key="rsi_chk")
                st.write("") 
                
                current_tf_name = {"日線": "日K", "週線": "週K", "月線": "月K"}.get(st.session_state.kline_period, "日K")
                with st.spinner(f"正在擷取 {pure_stock_id} 的最新 {current_tf_name} 及指標數據..."):
                    all_mas = ["5MA", "10MA", "20MA", "60MA", "120MA", "240MA"]
                    render_technical_chart(pure_stock_id, st.session_state.kline_period, all_mas, chk_rsi, chk_macd, chk_kd)
            else:
                st.warning("⚠️ 技術 K 線圖目前僅支援代號查詢。")

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

        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #FCD34D;'>🔄 區塊 4：券資有利排名</h4>", unsafe_allow_html=True)
        
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

        render_b4_panorama("5日幅度變動排名", [('📉 融資減少', 'df_margin_pct'), ('📉 借券減少', 'df_short_pct'), ('📈 融券增加', 'df_margin_plus_pct')], search_query)
        st.write("") 
        render_b4_panorama("5日張數變動排名", [('📉 融資減少', 'df_margin_vol'), ('📉 借券減少', 'df_short_vol'), ('📈 融券增加', 'df_margin_plus_vol')], search_query)

        st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #FCD34D;'>💰 區塊 5：大戶動向診斷</h4>", unsafe_allow_html=True)
        
        col_400, col_1000 = st.columns(2)
        with col_400: scan_and_display("💎 400張以上大戶動向", 'df_blk5', search_query)
        with col_1000: scan_and_display("🐳 1000張以上超級大戶動向", 'df_blk5_1000', search_query)
############################################    
# ==========================================
# 🧭 側邊欄導航與共用函數 (極速光速版：零爬蟲、零延遲、讀取本地 CSV)
# ==========================================
import os
import glob
import pandas as pd
import streamlit as st
import datetime
import yfinance as yf
import re

DATA_DIR = "./Goodinfo_Rankings"

# ==========================================
# 🌟 核心共用函數 (終極防呆：從此免疫 Excel 吃掉 0 的問題)
# ==========================================
def parse_json_history_csv(file_path, date_label):
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
        df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
        df = df.rename(columns={'法人持股': f"{date_label}持股%"})
        return df
    except: 
        return pd.DataFrame()

def agg_sections_func(x):
    valid_x = set()
    for val in x:
        if pd.notna(val) and str(val).strip() != "":
            for p in str(val).split(','):
                valid_x.add(p.strip())
    return ",".join([s for s in ['5日', '20日', '60日', '120日'] if s in valid_x])

# 🌟 全域資料夾讀取引擎：所有 CSV 一讀進來，代號全部強制補零！
@st.cache_data(ttl=60) 
def get_latest_csv(keyword):
    if not os.path.exists(DATA_DIR): return None, "未知"
    files = glob.glob(os.path.join(DATA_DIR, f"*{keyword}*csv"))
    if not files: return None, "未知"
    files.sort(reverse=True)
    try: 
        df = pd.read_csv(files[0])
        for col in ['股票代號', '代號', '證券代號']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df[col] = df[col].apply(lambda x: x.zfill(4) if x.isdigit() else x)
        return df, os.path.basename(files[0])[:8]
    except: return None, "未知"

@st.cache_data(ttl=60)
def get_prev_csv(keyword, current_date):
    if not os.path.exists(DATA_DIR): return None
    files = glob.glob(os.path.join(DATA_DIR, f"*{keyword}*csv"))
    past_files = [f for f in files if os.path.basename(f)[:8] < current_date]
    if not past_files: return None
    past_files.sort(reverse=True)
    try: 
        df = pd.read_csv(past_files[0])
        for col in ['股票代號', '代號', '證券代號']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df[col] = df[col].apply(lambda x: x.zfill(4) if x.isdigit() else x)
        return df
    except: return None

def get_diff_ui(today_val, prev_val):
    if prev_val is None or pd.isna(prev_val): return ""
    try:
        diff = int(today_val) - int(prev_val)
        if diff == 0: return ""
        sign = "+" if diff > 0 else ""
        color = "#FF4B4B" if diff > 0 else "#00E272" 
        return f"<br><span style='color:{color}; font-size:11px;'>({sign}{diff:,})</span>"
    except: return ""

tab1, tab2 = st.sidebar.tabs(["🔹 大盤與期權", "🔹 戰情導航"])


# ------------------------------------------
# 1. 大盤籌碼導航總覽 (終極精準融資 + 期貨變化量)
# ------------------------------------------
def render_sidebar_market_summary():
    st.markdown("<h2 style='margin-top: 0; margin-bottom: 5px;'>📊 大盤資金風向球</h2>", unsafe_allow_html=True)
    df_spot, date_spot = get_latest_csv("三大法人買賣超金額")
    df_fut, _ = get_latest_csv("三大法人期貨多空")
    df_fut_prev = get_prev_csv("三大法人期貨多空", date_spot)
    df_margin, margin_csv_name = get_latest_csv("融資融券餘額") # 💡 檔名對應
    
    if df_spot is None or df_fut is None:
        st.warning("尚無大盤數據，請確認資料夾中已有今日 CSV。")
        return "未知"

    # --- 1. 現貨 ---
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

    # --- 2. 期貨 (今日) ---
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

    # --- 3. 期貨 (前日，用來算變化量) ---
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

    # --- 4. 🚀 融資餘額 (絕對鎖定仟元與單位轉換) ---
    margin_diff_yi, margin_today_yi = 0.0, 0.0
    if df_margin is not None:
        for _, row in df_margin.iterrows():
            row_list = [str(x).replace(',', '').strip() for x in row.values]
            row_str = "".join(row_list)
            # 🎯 絕對鎖定「金額(仟元)」這一列
            if '融資金額' in row_str:
                try:
                    # 證交所標準欄位：最後兩格必定是 [前日餘額, 今日餘額]
                    margin_prev = float(row_list[-2]) 
                    margin_today = float(row_list[-1])
                    
                    # 將仟元轉換為億元 (除以 100,000)
                    margin_diff_yi = (margin_today - margin_prev) / 100000
                    margin_today_yi = margin_today / 100000
                    break
                except: pass

    # --- UI 渲染 ---
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

    # 1. 移除「本地極速版」字眼，只保留俐落的日期
    html = f"<div style='font-size: 13px; color: #00D2FF;'>📅 {date_spot} | 資金風向球</div>"
    html += "<table style='width: 100%; text-align: center; border-collapse: collapse; margin-top: 5px; font-size: 14px;'>"
    html += "<tr style='border-bottom: 1px solid #555; background-color: #262730;'>"
    html += "<th style='padding: 5px;'>法人</th><th style='padding: 5px;'>現貨(億)</th><th style='padding: 5px;'>TX未平倉</th></tr>"
    html += f"<tr><td style='padding: 4px;'>🌐 外資</td><td style='color: {f_c}; vertical-align: middle;'>{f_s}</td><td style='color: {fo_c}; vertical-align: middle; padding-bottom: 6px;'>{fo_s}{get_diff_ui(oi_foreign, oi_f_prev)}</td></tr>"
    html += f"<tr><td style='padding: 4px;'>🏦 投信</td><td style='color: {t_c}; vertical-align: middle;'>{t_s}</td><td style='color: {to_oc}; vertical-align: middle; padding-bottom: 6px;'>{to_os}{get_diff_ui(oi_trust, oi_t_prev)}</td></tr>"
    html += f"<tr><td style='padding: 4px;'>🏢 自營商</td><td style='color: {d_c}; vertical-align: middle;'>{d_s}</td><td style='color: {do_c}; vertical-align: middle; padding-bottom: 6px;'>{do_os}{get_diff_ui(oi_dealer, oi_d_prev)}</td></tr>"
    
    tot_prev = (oi_f_prev + oi_t_prev + oi_d_prev) if oi_f_prev is not None else None
    html += f"<tr style='border-top: 1px solid #555; font-weight: bold;'><td style='padding: 4px;'>🔥 合計</td><td style='color: {to_c}; vertical-align: middle;'>{to_s}</td><td style='color: {too_c}; vertical-align: middle; padding-bottom: 6px;'>{too_os}{get_diff_ui(total_oi, tot_prev)}</td></tr>"
    html += "</table>"
    
    if margin_today_yi != 0.0:
        # 2. 獲取融資檔案的專屬日期
        margin_date = margin_csv_name[:8] if margin_csv_name else "未知"
        
        html += "<div style='margin-top: 8px; padding: 6px; background-color: #1e1e24; border: 1px solid #555; border-radius: 5px; font-size: 13px;'>"
        # 3. 標題加上專屬日期標示
        html += f"<div style='font-weight: bold;'>📉 大盤融資餘額 <span style='font-size: 11px; color: #888; font-weight: normal; margin-left: 5px;'>({margin_date})</span></div>"
        html += f"<div style='color: #aaa; margin-top: 4px;'>今日增減(億) <span style='color: {m_c}; font-weight: bold; float: right;'>{m_s}</span></div>"
        html += f"<div style='color: #aaa; margin-top: 2px;'>餘額總計(億) <span style='float: right; color: #fff;'>{margin_today_yi:,.1f}</span></div>"
        html += "</div>"
        
    st.markdown(html, unsafe_allow_html=True)
    return date_spot

# ------------------------------------------
# 2. 選擇權關鍵兵力分布 (36000 智慧底線 + 變化量追蹤版)
# ------------------------------------------
def render_options_dashboard(target_date_str):
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top: 0; margin-bottom: 5px;'>🏰 選擇權兵力分布</h2>", unsafe_allow_html=True)
    
    df_opt, date_opt = get_latest_csv("臺指選擇權行情簡表")
    df_pcr, _ = get_latest_csv("臺指選擇權PC比")
    df_opt_prev = get_prev_csv("臺指選擇權行情簡表", date_opt)
    
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
        st.info("🔄 選擇權格式讀取失敗，請確認是否為 Report 格式。")
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

    # 🚀 解析昨日資料供比對
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

with tab1:
    actual_data_date = render_sidebar_market_summary()
    render_options_dashboard(actual_data_date)
    
with tab2:
    st.subheader("📊 大盤總體經濟指標")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1: st.link_button("📈 恐懼貪婪", "https://www.wantgoo.com/global/macroeconomics/fearandgreed", use_container_width=True)
    with c_btn2: st.link_button("⚠️ VIX 指數", "https://www.wantgoo.com/global/vix", use_container_width=True)
    st.markdown("---")
    st.subheader("📍 戰情室快速導航")
    st.markdown("[🏆 數據分析觀察名單](#section-top-pool)")
    st.markdown("[🔍 個股籌碼快搜 (診斷區)](#section-search)")
    st.markdown("[👑 區塊1：三大法人持股比追蹤](#section-1)")
    st.markdown("[🎯 區塊2系列：法人5日淨買佔比](#section-2-1)")
    st.markdown("[📅 區塊3：法人連續買超](#section-3)")
    st.markdown("[🔄 區塊4系列：融資券與軋空雷達](#section-4-1)")
    st.markdown("[💰 區塊5：大股東動向](#section-5)")
    st.markdown("[💸 區塊6：鉅額交易動向](#section-6)")

# ==========================================
# 🏠 核心五大區塊
# ==========================================
# ==========================================
# 🏠 區塊1：中長線 三大法人 持股比例 追蹤 (全本地同步極速版)
# ==========================================
st.write("---")
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)

header_placeholder = st.empty()

import re
import os
import glob
import pandas as pd
import requests
import datetime
from collections import defaultdict

# ------------------------------------------
# 🌐 全自動 GitHub JSON 抓取引擎 (僅供站長按鈕下載使用)
# ------------------------------------------
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

json_dfs, latest_all_df = fetch_github_json_all()


# ------------------------------------------
# 💾 站長專屬：JSON 200名快照存檔區
# ------------------------------------------
DATA_DIR = "./Goodinfo_Rankings"
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
    st.link_button("📊 DDong 台股法人籌碼數據儀表板", "https://goodinfo3583.github.io/DDong_tw-institutional-stocker/", use_container_width=True)

with c_btn2:
    try: exp_container = st.popover(f"🛠 站長快照 ({status_text})", use_container_width=True)
    except AttributeError: exp_container = st.expander(f"🛠 站長：下載 200名快照 ({status_text})", expanded=False)
        
    with exp_container:
        if is_updated_today: st.success(f"✅ **今日已更新！** 資料夾中最新快照為 `{local_latest_date}`。")
        else: st.warning(f"⚠️ **今日尚未更新！** 資料夾中最新快照停留在 `{local_latest_date}`，請記得下載！")
            
        admin_pw = st.text_input("請輸入站長密碼以解鎖功能", type="password", key="admin_pw_input")
        if admin_pw == "DDong888": 
            st.success("🔓 驗證成功！請執行快照封存。")
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
                    
                    st.success(f"✅ 成功生成 {len(snap_grouped)} 檔股票的歷史快照！")
                    st.download_button(
                        label="📥 點我下載快照 CSV 檔案", data=csv_data, file_name=f"{date_str}_JSON_History.csv",
                        mime="text/csv", type="primary", use_container_width=True
                    )
                else: st.error("❌ 尚未獲取到 GitHub 數據，封存失敗。")
        elif admin_pw != "": st.error("❌ 密碼錯誤，無法使用此功能。")

# ==========================================
# 🔄 歷史資料合併與邏輯運算 (底層大表重建)
# ==========================================
date_files = defaultdict(lambda: {'txt': [], 'csv': []})

def extract_date_from_filename(filename):
    m8 = re.search(r'(202\d{5})', filename)
    if m8: return m8.group(1)
    return None

all_csv_files = glob.glob(os.path.join(DATA_DIR, "*JSON*.csv"))
for f in all_csv_files:
    d_label = extract_date_from_filename(os.path.basename(f))
    if d_label: date_files[d_label]['csv'].append(f)

sorted_dates = sorted(date_files.keys(), reverse=True)
final_df = pd.DataFrame()

if sorted_dates:
    latest_d = sorted_dates[0]
    fmt_date = f"{latest_d[:4]}/{latest_d[4:6]}/{latest_d[6:]}"
    header_placeholder.markdown(
        f"<h2 style='margin-bottom: 0px;'>👑 區塊1：三大法人短中長線持股比追蹤 "
        f"<span style='color:#00D2FF; font-size:16px; font-weight:500; margin-left:12px;'>資料基準日：{fmt_date}</span></h2>", 
        unsafe_allow_html=True
    )
    
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
            
        if final_df is None or final_df.empty: final_df = df_day
        else: final_df = pd.merge(final_df, df_day, on=['股票代號', '股票名稱'], how='outer')
            
    if final_df is not None and not final_df.empty:
        date_cols = sorted([c for c in final_df.columns if '持股%' in c], reverse=True)
        for c in date_cols: final_df[c] = pd.to_numeric(final_df[c], errors='coerce').fillna(0)
            
        def generate_tags(sections):
            if pd.isna(sections) or not sections: return ""
            sec_list = str(sections).split(',')
            tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if key in sec_list]
            return " ".join(tags)
            
        latest_sect_col = f"{sorted_dates[0]}_區塊"
        if latest_sect_col not in final_df.columns: final_df[latest_sect_col] = ""
        
        final_df['今日上榜'] = final_df[latest_sect_col].apply(generate_tags)
        final_df['上榜數量'] = final_df['今日上榜'].apply(lambda x: str(x).count('日'))
            
        def evaluate_trend(row):
            if len(date_cols) < 2: return "⚪ 資料不足"
            dynamics, v0, v1 = [], row[date_cols[0]], row[date_cols[1]]
            diff1 = v0 - v1  
            if diff1 > 0:
                is_slowing = False
                if len(date_cols) >= 3:
                    v2 = row[date_cols[2]]
                    if v0 > v1 > v2 > 0: dynamics.append("🪜 階梯吸籌")
                    elif len(date_cols) >= 4 and v0 >= v1 >= v2 >= row[date_cols[3]] > 0 and v0 > row[date_cols[3]]: dynamics.append("🛡️ 穩健吸籌")
                    if v1 != 0 and v2 != 0 and diff1 < (v1 - v2): dynamics.append("⚠️ 趨緩"); is_slowing = True
                if not is_slowing: dynamics.append("📈 上升")
            elif diff1 < 0: dynamics.append("📉 下降")
            else: dynamics.append("🔄 持平")
                
            today_list = [s for s in str(row.get(f"{sorted_dates[0]}_區塊", "")).split(',') if s]
            yest_list = [s for s in str(row.get(f"{sorted_dates[1]}_區塊", "")).split(',') if s]
            
            if v0 > 0 and v1 == 0 and any(row[c] > 0 for c in date_cols[2:]): dynamics.append("🔄 洗盤回歸")
            if 1 <= len(yest_list) <= 3 and len(today_list) > len(yest_list):
                new_entries = [i for i in today_list if i not in yest_list]
                tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if any(key in item for item in new_entries)]
                if tags: dynamics.append(f"🚀 衝進{'、'.join(tags)}榜單")
            return " | ".join(dynamics)
                
        final_df['最新動態'] = final_df.apply(evaluate_trend, axis=1)
        final_df['法人持股'] = final_df[date_cols[0]]
        
        # 🔥 把單日精準變化補上去
        if not latest_all_df.empty and '股票代號' in latest_all_df.columns:
            final_df = pd.merge(final_df, latest_all_df, on='股票代號', how='left')
            final_df['△'] = final_df['精準單日△'].fillna(0.0)
        else:
            if len(date_cols) >= 2:
                final_df['△'] = final_df.apply(lambda row: row[date_cols[0]] - row[date_cols[1]] if row[date_cols[1]] > 0.001 else 0.0, axis=1)
            else: final_df['△'] = 0.0
            
        final_df['法人金額'] = 0.0 

        # 🔥 關鍵修復：把 GitHub JSON 的「期程專屬排名」與「專屬ΔChange」合併回大表
        for d in [5, 20, 60, 120]:
            if d in json_dfs and not json_dfs[d].empty:
                temp_json = json_dfs[d][['股票代號', f'{d}日ΔChange', f'{d}日排名']]
                final_df = pd.merge(final_df, temp_json, on='股票代號', how='left')

        color_ref = final_df.set_index('股票代號')['上榜數量'].to_dict()
        for col in date_cols: final_df[col] = final_df[col].apply(lambda x: "未進榜" if pd.isna(x) or abs(x) < 0.0001 else f"{x:.2f}")

        final_df['今日有上榜_排序'] = final_df['今日上榜'] != ""
        if date_cols:
            final_df = final_df.sort_values(by=['今日有上榜_排序', '上榜數量', date_cols[0]], ascending=[False, False, False])

else:
    header_placeholder.markdown("<h2 style='margin-bottom: 0px;'>👑 區塊1：三大法人短中長線持股比追蹤</h2>", unsafe_allow_html=True)

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
    # 篩選出有在這個期程上榜的股票
    df = final_df[final_df['今日上榜'].str.contains(f'{target_day_str}日', na=False)].copy()
    if df.empty: return df
    
    # 執行 ETF/債券/搜尋 過濾
    is_bond = df['股票代號'].str.endswith('B')
    is_etf = (df['股票代號'].str.len() >= 5) & (~is_bond)
    is_stock = df['股票代號'].str.len() == 4
    mask = is_stock
    if show_etf: mask |= is_etf
    if show_bond: mask |= is_bond
    if search_kw:
        mask &= (df['股票代號'].str.contains(search_kw, na=False)) | (df['股票名稱'].str.contains(search_kw, na=False))
    df = df[mask].copy()
    
    # 🔥 關鍵修復：依據該期程專屬的「排名」來重新排序！
    rank_col = f'{target_day_str}日排名'
    change_col = f'{target_day_str}日ΔChange'
    
    # 若有抓到專屬排名，就依據排名由小到大 (1~200) 排序；若只有 Change 就依 Change 降冪排序
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
st.info("💡 欄位說明：【△】為精準單日法人持股增減；【◯日ΔChange】為天期累積變化。")
st.session_state['my_final_df'] = final_df
# ==========================================
# 🎯 區塊2-1：外資 5 日買超 佔成交量比 追蹤 (穩定精確版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-1'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-1：外資 5 日 買超佔標的成交量")

import os
import glob
import pandas as pd

csv_pattern = os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")
all_csv_files = glob.glob(csv_pattern)

if not all_csv_files:
    st.warning("⚠️ 找不到任何包含『外資買超佔成交比』的 CSV 檔案。")
else:
    all_csv_files.sort(reverse=True)
    #串聯日數
    target_files = all_csv_files[:10]
    base_df = None
    latest_day_today_data = {}

    for idx, f in enumerate(target_files):
        try:
            # 強制讀取並清洗所有欄位名稱 (移除空格、換行、BOM)
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 確保代號/名稱存在
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '代號', name_col: '名稱'})
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 自動偵測欄位 (包含關鍵字即可)
            col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
            
            # 存當日數據
            if idx == 0 and col_today:
                latest_day_today_data = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            # 合併歷史 (修改為：成交比%)
            if col_5d:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}成交比%"})
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
        except Exception:
            continue

    if base_df is not None:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 強健排序：依據最新日期數值排序 (修改為：成交比%)
        latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}成交比%"
        if latest_col_name in csv_display.columns:
            csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
            
        # 動態判定邏輯 (將當日買佔比直接融合成文字)
        def evaluate_continuity(row):
            today = latest_day_today_data.get(row['股票代號'], 0)
            base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
            
            # 格式化顯示數值
            if pd.isna(today):
                val_str = "(無資料)"
            else:
                val_str = f"({today}%)"

            if pd.isna(today): return f"⚪ 觀望 {val_str}"
            if today > 0: 
                status = "🔥 強延續" if today > base else "⚠️ 趨緩"
                return f"{status} {val_str}"
            elif today < 0: 
                status = "🚨 劇烈倒貨" if abs(today) > abs(base) else "📉 調節洗盤"
                return f"{status} {val_str}"
            return f"🔄 持平 {val_str}"

        csv_display['今日短動態'] = csv_display.apply(evaluate_continuity, axis=1)
        
        # 動態說明對照表
        st.info("""
        **動態說明：** 🔥 強延續 (買盤加速) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (強烈賣出)
        """)
        
        # 1. UI 與過濾 (先處理好數據，才能顯示)
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="fo_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="fo_bond_v9")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 2. 調整欄位順序 (拿掉獨立的當日佔比，並抓取"成交比%")
        cols = ["股票代號", "股票名稱", "今日短動態"] + [c for c in csv_display.columns if "成交比%" in c]
        csv_display = csv_display[cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        # ==========================================
        # 🔥 顯示區塊 (調整順序：先表格，後說明)
        # ==========================================
        
        # 顯示表格
        st.dataframe(csv_display, use_container_width=True)

        # ==========================================================
        # 🔥 【重點新增】：將結果存入記憶體，供搜尋區塊讀取！
        # ==========================================================
        # 計算實際成功串聯的天數 (計算有幾個"成交比%"欄位)
        days_count = len([c for c in csv_display.columns if "成交比%" in c])
        st.success(f"串聯 {days_count} 個交易日追蹤共 {len(csv_display)} 檔")
        
        # 最後存入 Session State
        st.session_state['df_blk2_1'] = csv_display
        
    else:
        st.error("❌ 無法讀取外資買超數據，請檢查 CSV 欄位名稱是否包含『5日』與『成交』關鍵字。")


# ==========================================
# 🎯 區塊2-2：投信 5 日買超 佔成交量比 追蹤 (穩定修復版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-2'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-2：投信 5 日 買超佔標的成交量")

import os
import glob
import pandas as pd

csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if not all_files_sitc:
    st.warning("⚠️ 找不到任何包含『投信買超佔成交比』的 CSV 檔案。")
else:
    all_files_sitc.sort(reverse=True)
    #串聯日數
    target_files = all_files_sitc[:10]
    base_df = None
    latest_day_today_data_sitc = {}

    for idx, f in enumerate(target_files):
        try:
            # 1. 強制讀取並清洗欄位 (移除空格、換行、BOM)
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 2. 確保代號/名稱欄位存在並清理
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '代號', name_col: '名稱'})
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 3. 自動偵測關鍵欄位 (只要包含關鍵字即可)
            col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
            
            if idx == 0 and col_today:
                latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            # 合併歷史 (修改為：成交比%)
            if col_5d:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}成交比%"})
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
        except Exception:
            continue

    if base_df is not None:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 4. 強健排序 (修改為：成交比%)
        latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}成交比%"
        if latest_col_name in csv_display.columns:
            csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
            
        # 5. 動態判定邏輯 (將當日買佔比直接融合成文字)
        def evaluate_continuity(row):
            today = latest_day_today_data_sitc.get(row['股票代號'], 0)
            base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
            
            # 格式化顯示數值
            if pd.isna(today):
                val_str = "(無資料)"
            else:
                val_str = f"({today}%)"

            if pd.isna(today): return f"⚪ 觀望 {val_str}"
            if today > 0: 
                status = "🔥 強延續" if today > base else "⚠️ 趨緩"
                return f"{status} {val_str}"
            elif today < 0: 
                status = "🚨 劇烈倒貨" if abs(today) > abs(base) else "📉 調節洗盤"
                return f"{status} {val_str}"
            return f"🔄 持平 {val_str}"

        csv_display['今日短動態'] = csv_display.apply(evaluate_continuity, axis=1)
        
        # 動態說明 (目前註解掉，可隨時開啟)
        #st.info("""
        #**動態說明：** 🔥 強延續 (法人認養中) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (短線獲利了結)
        #""")
        
        # 篩選邏輯
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_v9")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 欄位順序調整 (拿掉獨立的當日佔比，並抓取"成交比%")
        cols = ["股票代號", "股票名稱", "今日短動態"] + [c for c in csv_display.columns if "成交比%" in c]
        csv_display = csv_display[cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.dataframe(csv_display, use_container_width=True)
        # 計算實際成功串聯的天數 (計算有幾個"成交比%"欄位)
        days_count = len([c for c in csv_display.columns if "成交比%" in c])
        st.success(f"串聯 {days_count} 個交易日追蹤共 {len(csv_display)} 檔")
        
        # 🔥 【連動儲存】：存入對應的快搜抽屜
        st.session_state['df_blk2_2'] = csv_display
    else:
        st.error("❌ 無法讀取投信買超數據，請確認 CSV 檔案內含有『5日』與『成交』欄位。")

# ==========================================
# 🎯 區塊2-3：外資 5 日買超佔發行張數 追蹤 (穩定精確版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-3'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-3：外資 5 日 買超佔公司發行張數")

import os
import glob
import pandas as pd

csv_pattern_fo = os.path.join(DATA_DIR, "*外資買超佔發行張數*.csv")
all_files_fo = glob.glob(csv_pattern_fo)

if not all_files_fo:
    st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
else:
    sorted_files = sorted(all_files_fo, key=extract_date_from_name, reverse=True)[:10]
    base_df = None
    date_labels = []
    latest_day_today_data_fo = {}

    for idx, f in enumerate(sorted_files):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
            
            if '代號' not in df.columns or '名稱' not in df.columns:
                continue
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            col_today = '當日買賣超佔發行張數'
            col_5d = '5日買賣超佔發行張數'
            
            if idx == 0 and col_today in df.columns:
                latest_day_today_data_fo = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d in df.columns:
                df_s = df[['代號', '名稱', col_5d]].copy()
                # 🔥 修改點 1：將欄位名稱精簡為 "發行數%"
                df_s = df_s.rename(columns={col_5d: f"{d_label}發行數%"})
                
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            
            date_labels.append(d_label)
        except Exception:
            continue

    if base_df is not None and len(date_labels) > 0:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 🔥 修改點 2：對齊新的精簡欄位名稱
        latest_5d_col = f"{date_labels[0]}發行數%"
        if latest_5d_col in csv_display.columns:
            csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
        
        def judge_today_alert_fo(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, 0)
            val_today = latest_day_today_data_fo.get(stock_id, 0)
            
            if val_5d == 0 or val_5d == "未進榜":
                return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
            
            if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
            elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
            return "🔄 今日量縮持平"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_fo, axis=1)
        
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="foreign_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="foreign_bond_final_v3")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 🔥 修改點 3：過濾並抓取新的精簡欄位名稱
        history_cols = [c for c in csv_display.columns if "發行數%" in c]
        csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        #表格
        st.dataframe(csv_display, use_container_width=True) 
        #說明
        st.success(f"串聯 {len(date_labels)} 個交易日追蹤共 {len(csv_display)} 檔")
        
        # 🔥 【連動儲存】
        st.session_state['df_blk2_3'] = csv_display
    else:
        st.error("❌ 無法讀取外資數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")

# ==========================================
# 🎯 區塊2-4：投信 5 日買超佔發行張數 追蹤 (最終穩定版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-4'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-4：投信 5 日 買超佔公司發行張數")

import os
import glob
import pandas as pd

csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if not all_files_sitc:
    st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
else:
    sorted_files = sorted(all_files_sitc, key=extract_date_from_name, reverse=True)[:10]
    base_df = None
    date_labels = []
    latest_day_today_data_sitc = {}

    for idx, f in enumerate(sorted_files):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
            
            if '代號' not in df.columns or '名稱' not in df.columns:
                continue
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            col_today = '當日買賣超佔發行張數'
            col_5d = '5日買賣超佔發行張數'
            
            if idx == 0 and col_today in df.columns:
                latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d in df.columns:
                df_s = df[['代號', '名稱', col_5d]].copy()
                # 🔥 修改點 1：將欄位名稱精簡為 "發行數%"
                df_s = df_s.rename(columns={col_5d: f"{d_label}發行數%"})
                
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            
            date_labels.append(d_label)
        except Exception:
            continue

    if base_df is not None and len(date_labels) > 0:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 🔥 修改點 2：對齊新的精簡欄位名稱
        latest_5d_col = f"{date_labels[0]}發行數%"
        if latest_5d_col in csv_display.columns:
            csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
        
        def judge_today_alert_sitc(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, 0)
            val_today = latest_day_today_data_sitc.get(stock_id, 0)
            
            if val_5d == 0 or val_5d == "未進榜":
                return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
            
            if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
            elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
            return "🔄 今日量縮持平"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_sitc, axis=1)
        
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_final_v3")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 🔥 修改點 3：過濾並抓取新的精簡欄位名稱
        history_cols = [c for c in csv_display.columns if "發行數%" in c]
        csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        
        st.dataframe(csv_display, use_container_width=True)
        # 🔥 修改點 4：統一成功訊息的標點符號格式
        st.success(f"串聯 {len(date_labels)} 個交易日追蹤共 {len(csv_display)} 檔")
        
        # 🔥 【連動儲存】
        st.session_state['df_blk2_4'] = csv_display
    else:
        st.error("❌ 無法讀取投信數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")
# ==========================================
# 📅 區塊三：外資與投信連續買超 (日/週全景戰情室)
# ==========================================
st.write("---")
st.markdown("<div id='section-3'></div>", unsafe_allow_html=True)
st.header("📅 區塊3：法人連續買超")

def read_live_ln_report(file_keyword, strict_type, exact_field_name, prefix_keyword, col_label):
    if strict_type == "日":
        search_pattern1 = os.path.join(DATA_DIR, f"*{file_keyword}*(日)*.csv")
        search_pattern2 = os.path.join(DATA_DIR, f"*{file_keyword}*日*.csv")
        target_files = glob.glob(search_pattern1) + glob.glob(search_pattern2)
        target_files = [f for f in target_files if "週" not in os.path.basename(f) and "周" not in os.path.basename(f) and "wk" not in os.path.basename(f).lower()]
    else:
        search_pattern1 = os.path.join(DATA_DIR, f"*{file_keyword}*(週)*.csv")
        search_pattern2 = os.path.join(DATA_DIR, f"*{file_keyword}*週*.csv")
        target_files = glob.glob(search_pattern1) + glob.glob(search_pattern2)
        
    target_files = list(set(target_files))
    if not target_files: return pd.DataFrame(), None
        
    latest_file = sorted(target_files, key=extract_date_from_name, reverse=True)[0]
    date_str = extract_date_from_name(latest_file) 
    
    try:
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        df.columns = df.columns.astype(str).str.replace('\n', '').str.replace(' ', '').str.replace('\ufeff', '').str.strip()
        
        col_id = next((c for c in df.columns if '代號' in c), df.columns[0])
        col_name = next((c for c in df.columns if '名稱' in c), df.columns[1])
        
        target_key = exact_field_name.replace(' ', '')
        if target_key in df.columns:
            target_data_col = target_key
        else:
            matched_cols = [c for c in df.columns if '買賣' in c and strict_type in c]
            target_data_col = matched_cols[0] if matched_cols else df.columns[2]
            
        df[target_data_col] = pd.to_numeric(df[target_data_col], errors='coerce').fillna(0)
        df_sorted = df[df[target_data_col] > 0].sort_values(by=target_data_col, ascending=False)
        
        if df_sorted.empty: return pd.DataFrame(), date_str
            
        output_df = pd.DataFrame()
        output_df["股票代號"] = df_sorted[col_id].astype(str).str.strip()
        output_df["股票名稱"] = df_sorted[col_name].astype(str).str.strip()
        
        def get_status_tag(val):
            if strict_type == "日":
                if val >= 10: return "🔥 波段認養"
                elif val >= 5: return "⚡ 買盤點火"
                else: return "🆕 試單觀察"
            else:
                if val >= 10: return "👑 長線主控"
                elif val >= 5: return "🚀 趨勢加溫"
                else: return "🌱 週線發動"
                
        output_df["狀態動態"] = df_sorted[target_data_col].apply(get_status_tag)
        output_df[col_label] = df_sorted[target_data_col].astype(int)
        
        real_pct_trade = [c for c in df_sorted.columns if prefix_keyword in c and "佔成交" in c]
        real_pct_issue = [c for c in df_sorted.columns if prefix_keyword in c and "佔發行量" in c]
        
        if real_pct_trade: output_df["佔成交(%)"] = pd.to_numeric(df_sorted[real_pct_trade[0]], errors='coerce').fillna(0.0)
        else: output_df["佔成交(%)"] = 0.0
            
        if real_pct_issue: output_df["佔發行量(%)"] = pd.to_numeric(df_sorted[real_pct_issue[0]], errors='coerce').fillna(0.0)
        else: output_df["佔發行量(%)"] = 0.0
            
        output_df.index = range(1, len(output_df) + 1)
        return output_df, date_str
    except Exception as e:
        return pd.DataFrame(), f"解讀失敗: {str(e)}"

# ==========================================
# 🛠 必備函數：強硬讀取法
# ==========================================
def robust_read_csv(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# ========================================================
# 🚀 執行排程與備份邏輯
# ========================================================
live_fo_day, date_fo_day = read_live_ln_report("外資連續買超", "日", "外資連續買賣日數", "外資", "最新連買天數")
if live_fo_day.empty and date_fo_day is None: 
    live_fo_day, date_fo_day = read_live_ln_report("外資連買", "日", "外資連續買賣日數", "外資", "最新連買天數")

live_it_day, date_it_day = read_live_ln_report("投信連續買超", "日", "投信連續買賣日數", "投信", "最新連買天數")
if live_it_day.empty and date_it_day is None:
    live_it_day, date_it_day = read_live_ln_report("投信連買", "日", "投信連續買賣日數", "投信", "最新連買天數")
if live_it_day.empty:
    live_it_day, date_it_day = read_live_ln_report("外資連續買超", "日", "投信連續買賣日數", "投信", "最新連買天數")
    if live_it_day.empty:
        live_it_day, date_it_day = read_live_ln_report("外資連買", "日", "投信連續買賣日數", "投信", "最新連買天數")

live_fo_wk, date_fo_wk = read_live_ln_report("外資連續買超", "週", "外資連續買賣週數", "外資", "最新連買週數")
if live_fo_wk.empty and date_fo_wk is None:
    live_fo_wk, date_fo_wk = read_live_ln_report("外資連買", "週", "外資連續買賣週數", "外資", "最新連買週數")

live_it_wk, date_it_wk = read_live_ln_report("投信連續買超", "週", "投信連續買賣週數", "投信", "最新連買週數")
if live_it_wk.empty and date_it_wk is None:
    live_it_wk, date_it_wk = read_live_ln_report("投信連買", "週", "投信連續買賣週數", "投信", "最新連買週數")
if live_it_wk.empty:
    live_it_wk, date_it_wk = read_live_ln_report("外資連續買超", "週", "投信連續買賣週數", "投信", "最新連買週數")
    if live_it_wk.empty:
        live_it_wk, date_it_wk = read_live_ln_report("外資連買", "週", "投信連續買賣週數", "投信", "最新連買週數")

# ========================================================
# 🔍 新增：全域 ETF 與 債券 篩選器
# ========================================================
c_f1, c_f2 = st.columns(2)
show_etf_b3 = c_f1.checkbox("顯示 ETF", value=True, key="b3_etf_filter")
show_bond_b3 = c_f2.checkbox("顯示 債券/債券ETF", value=True, key="b3_bond_filter")

def apply_b3_filter(df):
    if df is None or df.empty:
        return df
    mask = (df['股票代號'].str.len() == 4)
    if show_etf_b3: mask |= ((df['股票代號'].str.len() >= 5) & (~df['股票代號'].str.endswith('B')))
    if show_bond_b3: mask |= df['股票代號'].str.endswith('B')
    res_df = df[mask].copy()
    res_df.index = range(1, len(res_df) + 1)
    return res_df

# 套用篩選器
live_fo_day = apply_b3_filter(live_fo_day)
live_it_day = apply_b3_filter(live_it_day)
live_fo_wk = apply_b3_filter(live_fo_wk)
live_it_wk = apply_b3_filter(live_it_wk)

# ========================================================
# 🖼️ 視覺介面渲染 (最新單日區塊)
# ========================================================
# 1. 第一層：左右子標題 (只留標題，拿掉日期)
h_day1, h_day2 = st.columns(2)
with h_day1:
    st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🌐 外資最新日連買</h3>", unsafe_allow_html=True)

with h_day2:
    st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🏦 投信最新日連買</h3>", unsafe_allow_html=True)

# 2. 第二層：動態說明
st.markdown("<div style='color: white; margin-top: 5px; margin-bottom: 18px; font-size: 16px;'>💡 <b>日動態說明：</b> 🔥 波段認養 (連買10天以上)  ⚡ 買盤點火 (連買5~9天)  🆕 試單觀察 (連買1~4天)</div>", unsafe_allow_html=True)

# 3. 第三層：左右資料表 + 表底日期
c_day1, c_day2 = st.columns(2)
with c_day1:
    if not live_fo_day.empty:
        st.dataframe(live_fo_day, use_container_width=True)
    else:
        st.write("無資料")
    # 將日期移到表格正下方
    date_val = date_fo_day if date_fo_day else '無資料'
    st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>最新數據: {date_val}</div>", unsafe_allow_html=True)

with c_day2:
    if not live_it_day.empty:
        st.dataframe(live_it_day, use_container_width=True)
    else:
        st.write("無資料")
    # 將日期移到表格正下方
    date_val = date_it_day if date_it_day else '無資料'
    st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>最新數據: {date_val}</div>", unsafe_allow_html=True)

st.write("---") # 加上分隔線，讓日與週的區塊更分明

# ========================================================
# 🖼️ 視覺介面渲染 (最新單週區塊)
# ========================================================
# 1. 第一層：左右子標題 (只留標題，拿掉日期)
h_wk1, h_wk2 = st.columns(2)
with h_wk1:
    st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🌐 外資最新週連買</h3>", unsafe_allow_html=True)

with h_wk2:
    st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🏦 投信最新週連買</h3>", unsafe_allow_html=True)

# 2. 第二層：動態說明
st.markdown("<div style='color: white; margin-top: 5px; margin-bottom: 18px; font-size: 16px;'>💡 <b>週動態說明：</b> 👑 長線主控 (連買10週以上)  🚀 趨勢加溫 (連買5~9週)  🌱 週線發動 (連買1~4週)</div>", unsafe_allow_html=True)

# 3. 第三層：左右資料表 + 表底日期
c_wk1, c_wk2 = st.columns(2)
with c_wk1:
    if not live_fo_wk.empty:
        st.dataframe(live_fo_wk, use_container_width=True)
    else:
        st.write("無資料")
    # 將日期移到表格正下方
    date_val = date_fo_wk if date_fo_wk else '無資料'
    st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>最新數據: {date_val}</div>", unsafe_allow_html=True)

with c_wk2:
    if not live_it_wk.empty:
        st.dataframe(live_it_wk, use_container_width=True)
    else:
        st.write("無資料")
    # 將日期移到表格正下方
    date_val = date_it_wk if date_it_wk else '無資料'
    st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>最新數據: {date_val}</div>", unsafe_allow_html=True)

# ========================================================
# 🖼️ 記憶體整合連動區塊 (供快搜功能使用)
# ========================================================
b3_combined_list = []

if 'live_fo_day' in locals() and not live_fo_day.empty:
    df_tmp = live_fo_day.copy()
    df_tmp['連買類型'] = '🌐 外資日連買'
    df_tmp = df_tmp.rename(columns={'最新連買天數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if 'live_it_day' in locals() and not live_it_day.empty:
    df_tmp = live_it_day.copy()
    df_tmp['連買類型'] = '🏦 投信日連買'
    df_tmp = df_tmp.rename(columns={'最新連買天數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if 'live_fo_wk' in locals() and not live_fo_wk.empty:
    df_tmp = live_fo_wk.copy()
    df_tmp['連買類型'] = '🌐 外資週連買'
    df_tmp = df_tmp.rename(columns={'最新連買週數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if 'live_it_wk' in locals() and not live_it_wk.empty:
    df_tmp = live_it_wk.copy()
    df_tmp['連買類型'] = '🏦 投信週連買'
    df_tmp = df_tmp.rename(columns={'最新連買週數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if b3_combined_list:
    df_b3 = pd.concat(b3_combined_list, ignore_index=True)
    df_b3 = df_b3[['連買類型', '股票代號', '股票名稱', '狀態動態', '連買週期數']]
    st.session_state['df_blk3_main'] = df_b3
else:
    st.session_state['df_blk3_main'] = pd.DataFrame(columns=['連買類型', '股票代號', '股票名稱', '狀態動態', '連買週期數'])


# ==========================================
# 📅 區塊 4 綜合區：融資與借券動向 (5日累計)
# ==========================================

# 🛠️ 【不可省略】讀取函數
def get_specific_margin_data(keyword):
    import os, pandas as pd
    found_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        if '.git' in root or 'venv' in root: continue
        for file in files:
            if file.lower().endswith(".csv") and keyword in file:
                found_files.append(os.path.join(root, file))
    
    if not found_files:
        return pd.DataFrame(), f"找不到包含『{keyword}』的檔案"
    
    latest_file = sorted(found_files, key=lambda x: os.path.basename(x), reverse=True)[0]
    file_name = os.path.basename(latest_file)
    
    try:
        df = robust_read_csv(latest_file)
        if df.empty:
            return pd.DataFrame(), f"讀取成功但內容為空: {file_name}"
        
        df.columns = df.columns.astype(str).str.replace('\ufeff', '').str.strip()
        
        for col in df.columns:
            if "幅度" in col or "張數" in col or "%" in col or "％" in col or "漲跌" in col:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.replace('%', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df, file_name
    except Exception as e:
        return pd.DataFrame(), f"讀取崩潰 ({file_name}): {str(e)}"
#==============區塊四表格欄位設計============
# 🛠️ 【不可省略】欄位清理與過濾函數
#==============區塊四表格欄位設計============
def process_margin_df(df, type_name, flag_etf, flag_bond):
    if df.empty: return df
    df = df.copy()
    
    cols_to_drop = [c for c in df.columns if "更新" in str(c) and "日期" in str(c)]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        
    target_idx = -1
    if type_name == "幅度":
        for i, col in enumerate(df.columns):
            if "3個月" in str(col) and ("%" in str(col) or "％" in str(col)):
                target_idx = i
                break
    else: 
        for i, col in enumerate(df.columns):
            if "3個月" in str(col) and "張數" in str(col):
                target_idx = i
                break
                
    if target_idx != -1:
        df = df.iloc[:, :target_idx+1]
        
    col_name = next((c for c in df.columns if '名稱' in c), None)
    col_id = next((c for c in df.columns if '代號' in c), None)
    
    if col_name and col_id:
        df = df.rename(columns={col_id: '股票代號', col_name: '股票名稱'})
        df['股票代號'] = df['股票代號'].astype(str).str.strip()
        df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
        
        mask_bond = df['股票名稱'].str.contains('債', na=False) | df['股票代號'].str.endswith('B', na=False)
        mask_etf = df['股票代號'].str.startswith('00', na=False)
        
        if not flag_bond: df = df[~mask_bond]
        if not flag_etf: df = df[~(mask_etf & ~mask_bond)] 

    # 🚀 顯示優化：自動改名為「漲跌幅%」並進行上漲優先排序
    sort_col = next((c for c in df.columns if '漲跌' in str(c) or '漲幅' in str(c)), None)
    if sort_col:
        df = df.rename(columns={sort_col: '漲跌幅%'}) # 強制改名，畫面更直觀
        df['漲跌幅%'] = pd.to_numeric(df['漲跌幅%'], errors='coerce').fillna(0)
        df = df.sort_values(by='漲跌幅%', ascending=False)

    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

# 🎨 核心渲染引擎：移除多餘零尾隨、改採護眼紅渲染
def render_styled_margin_table(clean_df):
    if clean_df.empty:
        st.warning("⚠️ 無相符資料")
        return
        
    display_df = clean_df.copy()
    change_col = next((c for c in display_df.columns if '漲跌' in str(c) or '漲幅' in str(c)), None)
    
    # 💡 終極去零法：在不破壞數據類型的前提下，將所有數值列收縮格式
    for col in display_df.columns:
        if col not in ['股票代號', '股票名稱']:
            try:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:.1f}".rstrip('0').rstrip('.') if pd.notna(x) and isinstance(x, (int, float)) else x
                )
            except: pass

    # 🎨 護眼深紅渲染
    def style_row_by_price(row):
        styles = [''] * len(row)
        if change_col:
            try:
                # 讀取原始 clean_df 的數值做精確多空判斷
                orig_val = clean_df.loc[row.name, change_col]
                if float(orig_val) > 0:
                    return ['color: #db7093; font-weight: bold;'] * len(row) # 🎯 升級護眼暗紅
            except: pass
        return styles

    styled_df = display_df.style.apply(style_row_by_price, axis=1)
    
    # 📐 欄位寬度最佳化配置：縮小股票名稱與代號寬度，強迫右側當日數據完美浮現
    col_config = {
        "股票代號": st.column_config.TextColumn("股票代號", width=65),
        "股票名稱": st.column_config.TextColumn("股票名稱", width=80)
    }
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True, column_config=col_config)

# 🕒 輔助函數：解析真實日期
def peek_data_date(keyword):
    import re
    _, msg = get_specific_margin_data(keyword)
    return re.search(r'\d{8}', msg).group(0) if re.search(r'\d{8}', msg) else "未知"

# ==========================================
# 📅 區塊 4-1：融資減少動向
# ==========================================
st.write("---")
st.markdown("<div id='section-4-1'></div>", unsafe_allow_html=True)

date_41 = peek_data_date("融資減少幅度")
# 使用 Markdown 語法，並透過 span 標籤嵌入 style
st.markdown(f"""### 🔄 區塊 4-1：融資減少動向 <span style="font-size: 0.6em; color: #00D2FF;">({date_41})</span>
""", unsafe_allow_html=True)

f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1: show_etf_41 = st.checkbox("顯示 ETF", value=True, key="margin_show_etf")
with f_col2: show_bond_41 = st.checkbox("顯示債券/債券ETF", value=True, key="margin_show_bond")
st.write("") 

c1, c2 = st.columns(2)
with c1:
    st.markdown("<h3 style='margin-top: 0; margin-bottom: 10px;'>📉 融資減少比例排名</h3>", unsafe_allow_html=True)
    df_pct, _ = get_specific_margin_data("融資減少幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度", show_etf_41, show_bond_41)
    render_styled_margin_table(df_pct_clean)
with c2:
    st.markdown("<h3 style='margin-top: 0; margin-bottom: 10px;'>📉 融資減少張數排名</h3>", unsafe_allow_html=True)
    df_vol, _ = get_specific_margin_data("融資減少張數")
    df_vol_clean = process_margin_df(df_vol, "張數", show_etf_41, show_bond_41)
    render_styled_margin_table(df_vol_clean)

st.session_state['df_margin_pct'] = df_pct_clean
st.session_state['df_margin_vol'] = df_vol_clean

# ==========================================
# 📅 區塊 4-2：借券賣出減少動向
# ==========================================
st.write("---")
st.markdown("<div id='section-4-2'></div>", unsafe_allow_html=True)

date_42 = peek_data_date("借券賣出減少幅度")
# 使用 Markdown 語法，並透過 span 標籤嵌入 style
st.markdown(f"""### 🔄 區塊 4-2：借券賣出減少動向 <span style="font-size: 0.6em; color: #00D2FF;">({date_42})</span>
""", unsafe_allow_html=True)

f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1: show_etf_42 = st.checkbox("顯示 ETF", value=True, key="stock_show_etf_42")
with f_col2: show_bond_42 = st.checkbox("顯示債券/債券ETF", value=True, key="stock_show_bond_42")
st.write("") 

c1, c2 = st.columns(2)
with c1:
    st.markdown("<h3 style='margin-top: 0; margin-bottom: 10px;'>📉 借券賣出減少比例排名</h3>", unsafe_allow_html=True)
    df_pct, _ = get_specific_margin_data("借券賣出減少幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度", show_etf_42, show_bond_42)
    render_styled_margin_table(df_pct_clean)
with c2:
    st.markdown("<h3 style='margin-top: 0; margin-bottom: 10px;'>📉 借券賣出減少張數排名</h3>", unsafe_allow_html=True)
    df_vol, _ = get_specific_margin_data("借券賣出減少張數")
    df_vol_clean = process_margin_df(df_vol, "張數", show_etf_42, show_bond_42)
    render_styled_margin_table(df_vol_clean)

st.session_state['df_short_pct'] = df_pct_clean
st.session_state['df_short_vol'] = df_vol_clean

# ==========================================
# 📅 區塊 4-3：融券增加動向
# ==========================================
st.write("---")
st.markdown("<div id='section-4-3'></div>", unsafe_allow_html=True)

date_43 = peek_data_date("融券增加幅度")
st.markdown(f"""### 🔄 區塊 4-3：融券增加動向 <span style="font-size: 0.6em; color: #00D2FF;">({date_43})</span>
""", unsafe_allow_html=True)

f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1: show_etf_43 = st.checkbox("顯示 ETF", value=True, key="stock_show_etf_43")
with f_col2: show_bond_43 = st.checkbox("顯示債券/債券ETF", value=True, key="stock_show_bond_43")
st.write("") 

c1, c2 = st.columns(2)
with c1:
    st.markdown("<h3 style='margin-top: 0; margin-bottom: 10px;'>📈 融券增加比例排名</h3>", unsafe_allow_html=True)
    df_pct, _ = get_specific_margin_data("融券增加幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度", show_etf_43, show_bond_43)
    render_styled_margin_table(df_pct_clean)
with c2:
    st.markdown("<h3 style='margin-top: 0; margin-bottom: 10px;'>📈 融券增加張數排名</h3>", unsafe_allow_html=True)
    df_vol, _ = get_specific_margin_data("融券增加張數")
    df_vol_clean = process_margin_df(df_vol, "張數", show_etf_43, show_bond_43)
    render_styled_margin_table(df_vol_clean)

st.session_state['df_margin_plus_pct'] = df_pct_clean
st.session_state['df_margin_plus_vol'] = df_vol_clean
# ==========================================
# 🚀 區塊 4-4：短線軋空雷達 (法人點火 + 空軍認錯 + 散戶放空)
# ==========================================
import streamlit as st
import pandas as pd
import os
import glob
import re

st.markdown("<div id='section-4-4'></div>", unsafe_allow_html=True)

def robust_read_csv_local(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

def build_squeeze_radar():
    # 🎯 抓取軋空所需的 4 個關鍵檔案
    buy_pattern = os.path.join(DATA_DIR, "*三大法人買超佔成交比*.csv")
    margin_dec_pattern = os.path.join(DATA_DIR, "*融資減少幅度*.csv")       # 散戶下車
    sbl_dec_pattern = os.path.join(DATA_DIR, "*借券賣出減少幅度*.csv")   # 空軍回補
    short_inc_pattern = os.path.join(DATA_DIR, "*融券增加幅度*.csv")       # 散戶逆勢放空
    
    buy_files = sorted(glob.glob(buy_pattern), reverse=True)
    margin_dec_files = sorted(glob.glob(margin_dec_pattern), reverse=True)
    sbl_dec_files = sorted(glob.glob(sbl_dec_pattern), reverse=True)
    short_inc_files = sorted(glob.glob(short_inc_pattern), reverse=True)
    
    if not buy_files:
        return pd.DataFrame(), "找不到三大法人買超檔案", "", False

    # ⏳ 解析檔名日期功能
    def get_date(filepath):
        match = re.search(r'(\d{8})', os.path.basename(filepath))
        return match.group(1) if match else ""
    
    dates = [
        get_date(buy_files[0]) if buy_files else "",
        get_date(margin_dec_files[0]) if margin_dec_files else "",
        get_date(sbl_dec_files[0]) if sbl_dec_files else "",
        get_date(short_inc_files[0]) if short_inc_files else ""
    ]
    
    # 過濾掉空字串後檢查日期是否全部一致
    valid_dates = [d for d in dates if d]
    is_sync = len(set(valid_dates)) == 1 if valid_dates else False
    display_date = f"{dates[0][:4]}/{dates[0][4:6]}/{dates[0][6:]}" if len(dates[0]) == 8 else dates[0]

    try:
        # 1. 處理母表 (三大法人買超)
        df_buy = robust_read_csv_local(buy_files[0])
        df_buy.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df_buy.columns]
        
        id_col = next((c for c in df_buy.columns if '代號' in c), df_buy.columns[1])
        name_col = next((c for c in df_buy.columns if '名稱' in c), df_buy.columns[2])
        df_buy = df_buy.rename(columns={id_col: '代號', name_col: '名稱'})
        df_buy['代號'] = df_buy['代號'].astype(str).str.strip()
        
        # 📝 指定保留的欄位
        keep_cols = ['代號', '名稱', '成交', '漲跌價', '漲跌幅']
        for keyword in ['當日', '2日', '3日', '5日']:
            matched_cols = [c for c in df_buy.columns if keyword in c and '買賣超佔成交' in c]
            if matched_cols:
                keep_cols.append(matched_cols[0])
                
        # 過濾出我們需要的欄位
        keep_cols = list(dict.fromkeys(keep_cols)) # 保持順序且去重
        # 如果有些欄位檔案裡沒有，就只拿存在的
        keep_cols = [c for c in keep_cols if c in df_buy.columns]
        df_squeeze = df_buy[keep_cols].copy()
#===
        #rename_mapping = {}
        #for col in df_risk.columns:
            #if '買賣超佔成交' in col:
                #new_name = col.replace('買賣超佔成交', '賣佔成交')
                #if '當日' in new_name:
                    #new_name = new_name.replace('當日', '▼當日')
                #rename_mapping[col] = new_name
        #df_risk = df_risk.rename(columns=rename_mapping)
#===    
        # 📝 更改欄位名稱 (買賣超佔成交 -> 買佔成交)
        
        rename_mapping = {}      
        for col in df_squeeze.columns:
            if '買賣超佔成交' in col:
                new_name = col.replace('買賣超佔成交', '買佔成交')
                if '當日' in new_name:
                    new_name = new_name.replace('當日', '▼當日')
                rename_mapping[col] = new_name                
        df_squeeze = df_squeeze.rename(columns=rename_mapping)
        
        # 數值轉型
        for col in df_squeeze.columns:
            if col not in ['代號', '名稱']:
                df_squeeze[col] = pd.to_numeric(df_squeeze[col].astype(str).str.replace('%', '', regex=False), errors='coerce')
                if pd.api.types.is_float_dtype(df_squeeze[col]):
                    df_squeeze[col] = df_squeeze[col].round(2)
        
        # 💡 軋空邏輯：只保留「漲跌幅 >= 0」的上漲/持平股票
        df_squeeze = df_squeeze[df_squeeze['漲跌幅'] >= 0]
        
    except Exception as e:
        return pd.DataFrame(), f"讀取買超母表失敗: {str(e)}", "", False

    # 2. 處理交集名單
    def get_danger_ids(files):
        danger_ids = set()
        if files:
            try:
                df_temp = robust_read_csv_local(files[0])
                t_id_col = next((c for c in df_temp.columns if '代號' in c), None)
                if t_id_col:
                    danger_ids = set(df_temp[t_id_col].astype(str).str.replace(r'\D', '', regex=True))
            except: pass
        return danger_ids

    margin_dec_ids = get_danger_ids(margin_dec_files)
    sbl_dec_ids = get_danger_ids(sbl_dec_files)
    short_inc_ids = get_danger_ids(short_inc_files)

    # 3. 標記與算分
    df_squeeze['📉融資減'] = df_squeeze['代號'].apply(lambda x: "✔️" if x in margin_dec_ids else "")
    df_squeeze['📉借券減'] = df_squeeze['代號'].apply(lambda x: "✔️" if x in sbl_dec_ids else "")
    df_squeeze['📈融券增'] = df_squeeze['代號'].apply(lambda x: "✔️" if x in short_inc_ids else "")
    
    # 計算軋空指數 (最高 4 分)
    df_squeeze['軋空指數'] = 1 + (df_squeeze['📉融資減'] == "✔️").astype(int) + (df_squeeze['📉借券減'] == "✔️").astype(int) + (df_squeeze['📈融券增'] == "✔️").astype(int)
    
    # 排序：指數越高的排前面，同分則看漲幅誰大
    df_squeeze = df_squeeze.sort_values(by=['軋空指數', '漲跌幅'], ascending=[False, False]).reset_index(drop=True)
    
    # 📝 動態標籤
    def get_squeeze_tag(score):
        if score == 4: return "💥 終極"
        elif score == 3: return "🚀 強軋"
        elif score == 2: return "🔥 點火"
        return "🔼 進駐"
        
    df_squeeze.insert(2, '軋空評估', df_squeeze['軋空指數'].apply(get_squeeze_tag))
    df_squeeze = df_squeeze.drop(columns=['軋空指數'])
    
    return df_squeeze, "Success", display_date, is_sync

# ==========================================
# 執行與渲染
# ==========================================
with st.spinner("⏳ 正在掃描全市場軋空名單..."):
    df_squeeze_radar, msg, radar_date, is_radar_sync = build_squeeze_radar()

header_html = "🚀 區塊 4-4：可能軋空雷達 "
if radar_date:
    if is_radar_sync:
        header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span>"
    else:
        header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span> <span style='color: #ffa500; font-size: 0.5em;'>⏳籌碼待更新</span>"

st.markdown(f"<h2>{header_html}</h2>", unsafe_allow_html=True)
st.write("💡 三大法人買超，伴隨融資退場、借券回補或融券逆勢增加的潛在軋空標的。")

if not df_squeeze_radar.empty:
    show_all = st.checkbox("顯示榜內被法人買超的上漲標的，但籌碼未見軋空特徵", value=False)
    
    if not show_all:
        # 只顯示 2 分以上的標的 (有任何一個軋空特徵)
        df_squeeze_radar = df_squeeze_radar[df_squeeze_radar['軋空評估'].str.contains("💥|🚀|🔥", regex=True)]

    if df_squeeze_radar.empty:
        st.success("🎉 目前沒有同時出現法人買超與軋空特徵的強勢名單！")
    else:
        # 重設索引
        df_squeeze_radar = df_squeeze_radar.reset_index(drop=True)
        df_squeeze_radar.insert(0, '索引', range(1, len(df_squeeze_radar) + 1))
        
        def style_table(df):
            try:
                styler = df.style.hide(axis='index')
            except:
                styler = df.style.hide_index()
            
            def highlight_squeeze(row):
                styles = []
                for col_name in row.index:
                    base_style = 'background-color: #262730;'
                    
                    # 🔴 數值三雄改成台股的「上漲紅」
                    if col_name in ['成交', '漲跌價', '漲跌幅']:
                        styles.append(base_style + ' color: #ff4b4b;')
                    else:
                        styles.append(base_style + ' color: #e0e0e0;')
                return styles
            
            styler = styler.apply(highlight_squeeze, axis=1)
            
            border_css = '1px solid #808495'
            styler = styler.set_table_styles([
                {'selector': 'table', 'props': [('width', '100%'), ('border-collapse', 'collapse'), ('font-family', 'sans-serif'), ('font-size', '13px')]},
                {'selector': 'th', 'props': [
                    ('background-color', '#1e1e24'), 
                    ('color', '#ffffff'), 
                    ('font-weight', 'normal'),
                    ('border', border_css),
                    ('padding', '6px 4px'), 
                    ('text-align', 'center'),
                    ('position', 'sticky'),  
                    ('top', '0'),            
                    ('z-index', '1')         
                ]},
                {'selector': 'td', 'props': [
                    ('border', border_css),
                    ('padding', '4px'), 
                    ('text-align', 'center'),
                    ('transition', 'all 0.2s ease-in-out') 
                ]},
                # 🌟 滑鼠 Hover 動態光暈效果 
                {'selector': 'tbody tr:hover td', 'props': [
                    ('background-color', 'rgba(4, 8, 20, 0.85) !important'), 
                    ('text-shadow', '0 0 8px rgba(255, 255, 255, 0.5) !important') 
                ]}
            ])
            
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            if '索引' in num_cols:
                num_cols.remove('索引')
                
            styler = styler.format({col: "{:.2f}" for col in num_cols})
            
            return styler.to_html()

        html_table = style_table(df_squeeze_radar)
        
        # 📏 高度控制 (顯示約 10~12 筆)
        scrollable_div = f"""
<div style="max-height: 420px; overflow-y: auto; border: 1px solid #808495; border-radius: 5px;">
{html_table}
</div>
"""
        st.markdown(scrollable_div, unsafe_allow_html=True)
else:
    st.warning(f"軋空雷達載入失敗：{msg}")

# ==========================================
# 🚨 區塊 4-5：短線避險雷達 (法人倒貨 + 融資套牢 + 空軍狙擊)
# ==========================================
import streamlit as st
import pandas as pd
import os
import glob
import re

st.markdown("<div id='section-4-5'></div>", unsafe_allow_html=True)

def robust_read_csv_local(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

def build_risk_radar():
    sell_pattern = os.path.join(DATA_DIR, "*三大法人賣超佔成交比*.csv")
    margin_pattern = os.path.join(DATA_DIR, "*融資增加幅度*.csv")
    short_pattern = os.path.join(DATA_DIR, "*借券賣出增加幅度*.csv")
    
    sell_files = sorted(glob.glob(sell_pattern), reverse=True)
    margin_files = sorted(glob.glob(margin_pattern), reverse=True)
    short_files = sorted(glob.glob(short_pattern), reverse=True)
    
    if not sell_files:
        return pd.DataFrame(), "找不到三大法人賣超檔案", "", False

    def get_date(filepath):
        match = re.search(r'(\d{8})', os.path.basename(filepath))
        return match.group(1) if match else ""
    
    sell_date = get_date(sell_files[0]) if sell_files else ""
    margin_date = get_date(margin_files[0]) if margin_files else ""
    short_date = get_date(short_files[0]) if short_files else ""
    
    is_sync = (sell_date == margin_date == short_date)
    display_date = f"{sell_date[:4]}/{sell_date[4:6]}/{sell_date[6:]}" if len(sell_date) == 8 else sell_date

    try:
        df_sell = robust_read_csv_local(sell_files[0])
        df_sell.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df_sell.columns]
        
        id_col = next((c for c in df_sell.columns if '代號' in c), df_sell.columns[1])
        name_col = next((c for c in df_sell.columns if '名稱' in c), df_sell.columns[2])
        df_sell = df_sell.rename(columns={id_col: '代號', name_col: '名稱'})
        df_sell['代號'] = df_sell['代號'].astype(str).str.strip()
        
        keep_cols = ['代號', '名稱']
        for keyword in ['成交', '漲跌價', '漲跌幅', '當日', '2日', '3日', '5日']:
            matched_cols = [c for c in df_sell.columns if keyword in c and '月' not in c and '年' not in c]
            if matched_cols:
                keep_cols.append(matched_cols[0])
                
        keep_cols = list(dict.fromkeys(keep_cols))
        df_risk = df_sell[keep_cols].copy()
        
        rename_mapping = {}
        for col in df_risk.columns:
            if '買賣超佔成交' in col:
                new_name = col.replace('買賣超佔成交', '賣佔成交')
                if '當日' in new_name:
                    new_name = new_name.replace('當日', '▼當日')
                rename_mapping[col] = new_name
        df_risk = df_risk.rename(columns=rename_mapping)
        
        for col in df_risk.columns:
            if col not in ['代號', '名稱']:
                df_risk[col] = pd.to_numeric(df_risk[col].astype(str).str.replace('%', '', regex=False), errors='coerce')
                if pd.api.types.is_float_dtype(df_risk[col]):
                    df_risk[col] = df_risk[col].round(2)
        
        df_risk = df_risk[df_risk['漲跌幅'] <= 0]
        
    except Exception as e:
        return pd.DataFrame(), f"讀取賣超母表失敗: {str(e)}", "", False

    margin_danger_ids = set()
    if margin_files:
        try:
            df_margin = robust_read_csv_local(margin_files[0])
            m_id_col = next((c for c in df_margin.columns if '代號' in c), None)
            if m_id_col:
                margin_danger_ids = set(df_margin[m_id_col].astype(str).str.replace(r'\D', '', regex=True))
        except: pass
        
    short_danger_ids = set()
    if short_files:
        try:
            df_short = robust_read_csv_local(short_files[0])
            s_id_col = next((c for c in df_short.columns if '代號' in c), None)
            if s_id_col:
                short_danger_ids = set(df_short[s_id_col].astype(str).str.replace(r'\D', '', regex=True))
        except: pass

    df_risk['🚨融資套牢'] = df_risk['代號'].apply(lambda x: "✔️" if x in margin_danger_ids else "")
    df_risk['📉借券大增'] = df_risk['代號'].apply(lambda x: "✔️" if x in short_danger_ids else "")
    
    df_risk['危險指數'] = 1 + (df_risk['🚨融資套牢'] == "✔️").astype(int) + (df_risk['📉借券大增'] == "✔️").astype(int)
    df_risk = df_risk.sort_values(by=['危險指數', '漲跌幅'], ascending=[False, True]).reset_index(drop=True)
    
    def get_risk_tag(score):
        if score == 3: return "☠️ 極危"
        elif score == 2: return "🚨 高危"
        return "⚠️ 初危"
        
    df_risk.insert(2, '套牢評估', df_risk['危險指數'].apply(get_risk_tag))
    df_risk = df_risk.drop(columns=['危險指數'])
    
    return df_risk, "Success", display_date, is_sync

# 執行與渲染
with st.spinner("⏳ 正在掃描全市場避險名單..."):
    df_risk_radar, msg, radar_date, is_radar_sync = build_risk_radar()

header_html = "🚨 區塊 4-5：短線套牢名單 "
if radar_date:
    if is_radar_sync:
        header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span>"
    else:
        header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span> <span style='color: #ffa500; font-size: 0.5em;'>⏳融券資待更新</span>"

st.markdown(f"<h2>{header_html}</h2>", unsafe_allow_html=True)
st.write("💡 三大法人賣超,融資套牢或借券增加的籌碼惡化標的,若當日成交轉正有望回溫。")

if not df_risk_radar.empty:
    show_all = st.checkbox("顯示榜內被法人賣超的下跌/持平標的但融資借券未上榜", value=False)
    
    if not show_all:
        df_risk_radar = df_risk_radar[df_risk_radar['套牢評估'].str.contains("☠️|🚨", regex=True)]

    if df_risk_radar.empty:
        st.success("🎉 目前沒有同時出現法人賣超與籌碼惡化的危險名單！")
    else:
        df_risk_radar = df_risk_radar.reset_index(drop=True)
        df_risk_radar.insert(0, '索引', range(1, len(df_risk_radar) + 1))
        
        def style_table(df):
            try:
                styler = df.style.hide(axis='index')
            except:
                styler = df.style.hide_index()
            
            def highlight_risk(row):
                styles = []
                for col_name in row.index:
                    base_style = 'background-color: #262730;'
                    
                    if col_name in ['成交', '漲跌價', '漲跌幅']:
                        styles.append(base_style + ' color: #00e676;')
                    elif col_name == '▼當日賣佔成交' and pd.to_numeric(row[col_name], errors='coerce') > 0:
                        styles.append(base_style + ' color: #ff4b4b;')
                    else:
                        styles.append(base_style + ' color: #e0e0e0;')
                return styles
            
            styler = styler.apply(highlight_risk, axis=1)
            
            border_css = '1px solid #808495'
            styler = styler.set_table_styles([
                {'selector': 'table', 'props': [('width', '100%'), ('border-collapse', 'collapse'), ('font-family', 'sans-serif'), ('font-size', '13px')]},
                {'selector': 'th', 'props': [
                    ('background-color', '#1e1e24'), 
                    ('color', '#ffffff'), 
                    ('font-weight', 'normal'),
                    ('border', border_css),
                    ('padding', '6px 4px'), 
                    ('text-align', 'center'),
                    ('position', 'sticky'),  
                    ('top', '0'),            
                    ('z-index', '1')         
                ]},
                {'selector': 'td', 'props': [
                    ('border', border_css),
                    ('padding', '4px'), 
                    ('text-align', 'center'),
                    ('transition', 'all 0.2s ease-in-out') 
                ]},
                {'selector': 'tbody tr:hover td', 'props': [
                    ('background-color', 'rgba(4, 8, 20, 0.85) !important'), 
                    ('text-shadow', '0 0 8px rgba(255, 255, 255, 0.5) !important') 
                ]}
            ])
            
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            if '索引' in num_cols:
                num_cols.remove('索引')
                
            styler = styler.format({col: "{:.2f}" for col in num_cols})
            
            return styler.to_html()

        html_table = style_table(df_risk_radar)
        
        # 📏 【修改點】：將 max-height 調整為 420px，大約顯示 10~12 筆
        scrollable_div = f"""
<div style="max-height: 420px; overflow-y: auto; border: 1px solid #808495; border-radius: 5px;">
{html_table}
</div>
"""
        st.markdown(scrollable_div, unsafe_allow_html=True)
else:
    st.warning(f"避險雷達載入失敗：{msg}")
    
# ==========================================
# 💰 區塊 5：大股東動向 (四層級對稱系統 + 4碼日期完美排版)
# ==========================================
import re
import os
import glob
import pandas as pd
import streamlit as st

# ------------------------------------------
# 0. 預先掃描最新檔案日期以供標題基準日顯示
# ------------------------------------------
global_latest_date = "0605"
all_b5_raw_files = glob.glob(os.path.join(DATA_DIR, "*神秘金字塔*")) + glob.glob(os.path.join(DATA_DIR, "*大股東*"))
for f in all_b5_raw_files:
    match = re.search(r'(\d{8})', os.path.basename(f))
    if match and match.group(1).startswith("202"):
        if match.group(1)[4:] > global_latest_date:
            global_latest_date = match.group(1)[4:]

st.write("---")
st.markdown("<div id='section-5'></div>", unsafe_allow_html=True)

# 科技風漸層橫幅標題
st.markdown(f"""
<div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
            border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; 
            border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
    <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
        💰 區塊 5：大股東動向
    </h2>
    <div style='font-size:13px; color:#00D2FF; font-weight:500; margin-top:8px;'>
        📊 基準日 : {global_latest_date[:2]}/{global_latest_date[2:]} 
    </div>
</div>
""", unsafe_allow_html=True)

st.write("💡 千張與四百張長線千金大戶股權動態週持有張數更新軌跡。")

# 篩選器
filter_c1, filter_c2, _ = st.columns([2, 3, 5])
show_etf = filter_c1.checkbox("顯示 ETF", value=True, key="b5_global_etf")
show_bond = filter_c2.checkbox("顯示 債券 / 債券 ETF", value=True, key="b5_global_bond")

def apply_b5_market_filters(df, show_etf, show_bond):
    if df is None or df.empty: return df
    is_etf = df['股票代號'].astype(str).str.startswith('00')
    is_bond = df['股票代號'].astype(str).str.endswith('B') | df['股票名稱'].astype(str).str.contains('債')
    mask = pd.Series(True, index=df.index)
    if not show_etf: mask = mask & ~(is_etf & ~is_bond)
    if not show_bond: mask = mask & ~is_bond
    return df[mask]

# 擴充為 5 個 Tab
tab_1000, tab_800, tab_600, tab_400, tab_sync = st.tabs([
    "🔹 1000張大戶", "🔹 800張大戶", "🔹 600張大戶", "🔹 400張大戶", "🔹 雙引擎共振"
])

filtered_1000_df, filtered_800_df, filtered_600_df, filtered_400_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ================= 通用大戶資料產生器 =================
# 因為 1000, 800, 600 張大戶的資料結構都在同一個 CSV 中，我們用一個通用函數處理
def process_major_shareholders(target_level):
    """
    target_level: '1千', '800', '600'
    """
    # 這裡的 pattern 可以抓到您命名的 1000張 或 800張等檔案
    files = glob.glob(os.path.join(DATA_DIR, "*大股東*數週增加*.csv"))
    if not files: return pd.DataFrame()
    
    groups = {}
    for f in files:
        m = re.search(r'(\d{8})', os.path.basename(f))
        key = m.group(1) if m else "UNKNOWN"
        groups.setdefault(key, []).append(f)
    
    merged, all_dates_4 = [], []
    col_abs_name = f'持股超過{target_level}張(%)'
    col_delta_name = f'超過{target_level}張增減'

    for prefix, fs in sorted(groups.items(), reverse=True):
        chunks = []
        detected_date = None
        for f in fs:
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).strip() for c in df.columns]
                
                c_code = next((c for c in df.columns if '代號' in c), None)
                c_name = next((c for c in df.columns if '名稱' in c), None)
                c_abs = next((c for c in df.columns if col_abs_name in c), None)
                c_delta = next((c for c in df.columns if col_delta_name in c), None)
                c_date = next((c for c in df.columns if '更新 日期' in c or '更新日期' in c), None)
                
                if not all([c_code, c_name, c_abs, c_delta]): continue
                
                df['股票代號'] = df[c_code].astype(str).str.extract(r'(\d+)')
                df['股票名稱'] = df[c_name].astype(str).str.strip()
                df['持股%'] = pd.to_numeric(df[c_abs].astype(str).str.replace('%', ''), errors='coerce')
                df['增減%'] = pd.to_numeric(df[c_delta].astype(str).str.replace('+', '').str.replace('%', ''), errors='coerce')
                
                if detected_date is None and c_date and not df[c_date].dropna().empty:
                    raw_date = str(df[c_date].dropna().iloc[0]).replace('/', '').strip()
                    detected_date = raw_date[-4:] if len(raw_date) in [4, 8] else prefix[-4:]

                chunks.append(df[['股票代號', '股票名稱', '持股%', '增減%']].dropna(subset=['股票代號']))
            except: continue
        
        if chunks:
            comb = pd.concat(chunks).groupby(['股票代號', '股票名稱']).max().reset_index()
            date_4 = detected_date if detected_date else prefix[-4:]
            if date_4 not in all_dates_4: all_dates_4.append(date_4)
            # 建立暫時名稱，以便後續依照最新/歷史決定是否加 ▼
            comb = comb.rename(columns={'持股%': f"{date_4}持有%", '增減%': f"DELTA_{date_4}"})
            merged.append(comb)
            
    if merged:
        master = merged[0]
        for m in merged[1:]: master = pd.merge(master, m, on=['股票代號', '股票名稱'], how='outer')
        sorted_dates_4 = sorted(all_dates_4, reverse=True)
        latest_date_4 = sorted_dates_4[0]
        
        def get_trend(val):
            if pd.isna(val): return "無"
            if val >= 1.5: return "🔥 大增"
            if val >= 0.5: return "📈 增"
            if val > 0: return "↗️ 微增"
            if val == 0: return "🔄 持平"
            if val > -0.5: return "↘️ 微減"
            return "🚨 減/大減"
            
        master['週動態'] = master[f"DELTA_{latest_date_4}"].apply(get_trend)
        
        # 計算 6 週增減
        delta_cols = [f"DELTA_{d}" for d in sorted_dates_4 if f"DELTA_{d}" in master.columns]
        master['▼6周增減'] = master[delta_cols[:6]].sum(axis=1, min_count=1)
        
        # 欄位重新命名與排序邏輯 (只給最新日期加 ▼)
        rename_dict = {}
        cols_order = ['股票代號', '股票名稱', '週動態', '▼6周增減']
        
        # 最新持有%
        if f"{latest_date_4}持有%" in master.columns:
            cols_order.append(f"{latest_date_4}持有%")
            
        for i, d in enumerate(sorted_dates_4):
            original_delta_col = f"DELTA_{d}"
            if original_delta_col in master.columns:
                if i == 0:
                    # 最新增減加上 ▼
                    new_delta_name = f"▼{d}"
                else:
                    # 歷史增減不加 ▼
                    new_delta_name = f"{d}"
                rename_dict[original_delta_col] = new_delta_name
                cols_order.append(new_delta_name)
                
        master = master.rename(columns=rename_dict)
        final_df = master[[c for c in cols_order if c in master.columns]]
        final_df = final_df.sort_values(by=f"▼{latest_date_4}", ascending=False)
        return final_df
    return pd.DataFrame()

# ================= TAB 1, 2, 3: 高階大戶系統 =================
with tab_1000:
    df_1000 = process_major_shareholders('1千')
    if not df_1000.empty:
        filtered_1000_df = apply_b5_market_filters(df_1000, show_etf, show_bond)
        st.dataframe(filtered_1000_df, use_container_width=True, hide_index=True)
        st.session_state['df_blk5_1000'] = filtered_1000_df
    else: st.info("⚪ 暫無 1000張大戶資料。")

with tab_800:
    df_800 = process_major_shareholders('800')
    if not df_800.empty:
        filtered_800_df = apply_b5_market_filters(df_800, show_etf, show_bond)
        st.dataframe(filtered_800_df, use_container_width=True, hide_index=True)
        st.session_state['df_blk5_800'] = filtered_800_df
    else: st.info("⚪ 暫無 800張大戶資料。")

with tab_600:
    df_600 = process_major_shareholders('600')
    if not df_600.empty:
        filtered_600_df = apply_b5_market_filters(df_600, show_etf, show_bond)
        st.dataframe(filtered_600_df, use_container_width=True, hide_index=True)
        st.session_state['df_blk5_600'] = filtered_600_df
    else: st.info("⚪ 暫無 600張大戶資料。")

# ================= TAB 4: 400張大戶 =================
with tab_400:
    files = glob.glob(os.path.join(DATA_DIR, "*神秘金字塔*.csv"))
    if files:
        files = sorted(files, key=os.path.basename, reverse=True)
        master = None
        all_dates = set()
        for f in files:
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).strip() for c in df.columns]
                
                # 自動將 8 碼轉 4 碼
                new_cols = []
                for c in df.columns:
                    if re.match(r'202\d{5}', c): new_cols.append(c[-4:])
                    elif re.match(r'\d{4}', c): new_cols.append(c)
                    else: new_cols.append(c)
                df.columns = new_cols
                
                if '股票代號/名稱' in df.columns:
                    df['股票代號'] = df['股票代號/名稱'].astype(str).str.extract(r'(\d+)')
                    df['股票名稱'] = df['股票代號/名稱'].astype(str).str.replace(r'^\d+', '', regex=True)
                
                df = df.set_index(['股票代號', '股票名稱'])
                date_cols = [c for c in df.columns if re.match(r'^\d{4}$', c)]
                all_dates.update(date_cols)
                
                master = df.combine_first(master) if master is not None else df
            except: continue
        
        if master is not None:
            master = master.reset_index()
            sorted_dates = sorted(list(all_dates), reverse=True)
            if sorted_dates:
                newest = sorted_dates[0]
                prev = sorted_dates[1] if len(sorted_dates) >= 2 else newest
                master[newest] = pd.to_numeric(master[newest], errors='coerce')
                master[prev] = pd.to_numeric(master[prev], errors='coerce')
                
                def get_trend_400(row):
                    v1, v2 = row.get(newest), row.get(prev)
                    if pd.isna(v1) or pd.isna(v2): return "無資料"
                    diff = v1 - v2
                    if diff >= 1.5: return "🔥 大增"
                    if diff >= 0.5: return "📈 增"
                    if diff > 0: return "↗️ 微增"
                    if diff == 0: return "🔄 持平"
                    if diff > -0.5: return "↘️ 微減"
                    return "🚨 減/大減"
                master['週動態'] = master.apply(get_trend_400, axis=1) if len(sorted_dates) >= 2 else "持平"
                
                # 重新命名：只給最新增減加 ▼
                rename_dict = {newest: f"▼{newest}"}
                if '上週持有%' in master.columns: rename_dict['上週持有%'] = f"{newest}持有%"
                if '總增減' in master.columns: rename_dict['總增減'] = "▼6周增減"
                master = master.rename(columns=rename_dict)
                
                # 排序邏輯
                cols_order = ['股票代號', '股票名稱', '週動態']
                if '▼6周增減' in master.columns: cols_order.append('▼6周增減')
                if f"{newest}持有%" in master.columns: cols_order.append(f"{newest}持有%")
                cols_order.append(f"▼{newest}")
                for d in sorted_dates[1:]:
                    if d in master.columns: cols_order.append(d)
                
                final_df = master[[c for c in cols_order if c in master.columns]]
                final_df = final_df.sort_values(by=f"▼{newest}", ascending=False)
                
                filtered_400_df = apply_b5_market_filters(final_df, show_etf, show_bond)
                st.dataframe(filtered_400_df, use_container_width=True, hide_index=True)
                st.session_state['df_blk5'] = filtered_400_df

# ================= TAB 5: 雙引擎共振 =================
with tab_sync:
    if not filtered_1000_df.empty and not filtered_400_df.empty:
        # 1. 篩選兩邊大戶都呈現「增」的標的
        df1_inc = filtered_1000_df[filtered_1000_df['週動態'].astype(str).str.contains('增', na=False)].copy()
        df2_inc = filtered_400_df[filtered_400_df['週動態'].astype(str).str.contains('增', na=False)].copy()

        # 2. 標記千張與四百張後綴
        df1 = df1_inc.add_suffix(' (千張)').rename(columns={'股票代號 (千張)': '股票代號', '股票名稱 (千張)': '股票名稱'})
        df2 = df2_inc.add_suffix(' (四百)').rename(columns={'股票代號 (四百)': '股票代號', '股票名稱 (四百)': '股票名稱'})

        sync = pd.merge(df1, df2, on=['股票代號', '股票名稱'], how='inner')

        if not sync.empty:
            # 3. 提取所有的 4 碼日期 (例如: 0605, 0529)
            date_bases = set()
            for c in sync.columns:
                match = re.search(r'(?:▼)?(\d{4})', c)
                if match:
                    date_bases.add(match.group(1))

            # 日期由新到舊排序
            sorted_dates = sorted(list(date_bases), reverse=True)

            # 4. 智慧欄位穿插排序
            cols_order = ['股票代號', '股票名稱']

            # - 動態指標放一起
            if '週動態 (千張)' in sync.columns: cols_order.append('週動態 (千張)')
            if '週動態 (四百)' in sync.columns: cols_order.append('週動態 (四百)')

            # - 6周總增減放一起
            if '▼6周增減 (千張)' in sync.columns: cols_order.append('▼6周增減 (千張)')
            if '▼6周增減 (四百)' in sync.columns: cols_order.append('▼6周增減 (四百)')

            # - 依日期降冪，同一日期千張與四百張完美成對排列
            for d in sorted_dates:
                # 先放持有比例 (如果有)
                c_hold_1000 = f"{d}持有% (千張)"
                c_hold_400 = f"{d}持有% (四百)"
                if c_hold_1000 in sync.columns: cols_order.append(c_hold_1000)
                if c_hold_400 in sync.columns: cols_order.append(c_hold_400)

                # 再放增減張數/比例 (自動判斷最新日期是否有 ▼)
                c_v_1000 = f"▼{d} (千張)"
                c_v_400 = f"▼{d} (四百)"
                c_n_1000 = f"{d} (千張)"
                c_n_400 = f"{d} (四百)"

                if c_v_1000 in sync.columns: cols_order.append(c_v_1000)
                elif c_n_1000 in sync.columns: cols_order.append(c_n_1000)

                if c_v_400 in sync.columns: cols_order.append(c_v_400)
                elif c_n_400 in sync.columns: cols_order.append(c_n_400)

            # 保底防呆：把剩下的欄位加進來
            for c in sync.columns:
                if c not in cols_order:
                    cols_order.append(c)

            sync = sync[cols_order]

            # 5. 排序：以千張的最新增減值降冪排列
            sort_col = next((c for c in sync.columns if '▼' in c and '千張' in c and '持有' not in c and '6周' not in c), None)
            if sort_col:
                sync = sync.sort_values(by=sort_col, ascending=False)

            st.success(f"🔥 強烈訊號！共有 **{len(sync)}** 檔標的出現大戶雙引擎共振 (千張與四百張同增)！")
            st.dataframe(sync, use_container_width=True, hide_index=True)
        else:
            st.info("⚪ 最新一週目前沒有「千張與四百張」同時增加的共振標的。")
    else:
        st.warning("⚠️ 請確保 1000 張與 400 張資料皆有成功載入，才能啟動共振掃描引擎。")
# ==========================================
# 💸 區塊 6：盤後鉅額交易總表 (原生 Dataframe 升級版 + 交易別顯示)
# ==========================================
def clean_number_for_display(val):
    try:
        if pd.isna(val) or str(val).strip() == '-': return '-'
        f = float(str(val).replace(',', ''))
        return str(int(f)) if f.is_integer() else str(f).rstrip('0').rstrip('.')
    except: return str(val)

@st.cache_data(ttl=60)
def build_historical_block_matrix():
    """搜尋資料夾中所有的鉅額交易紀錄，自動組成歷史矩陣 (最強寬容版 + 智慧箭頭標示)"""
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

st.write("---")
st.markdown("<div id='section-6'></div>", unsafe_allow_html=True)

df_block, block_date = get_latest_csv("鉅額交易")
formatted_date = f"{block_date[:4]}/{block_date[4:6]}/{block_date[6:8]}" if block_date != "未知" else "未知"
status_icon = "🟢" if df_block is not None else "🌕"

st.markdown(f"### 💸 區塊 6：鉅額交易動向 <span style='font-size: 0.6em; color: #00D2FF;'>({formatted_date} {status_icon})</span>", unsafe_allow_html=True)
st.write("💡 鉅額交易常為大戶私下換手籌碼，成交價可視為「支撐/壓力」防守線；短線跌破建議嚴設停損。")

tab_today, tab_hist = st.tabs(["🔹 今日最新鉅額交易", "🔹 歷史防守價追蹤表"])

# ==================== Tab 1: 今日鉅額交易 ====================
with tab_today:
    if df_block is not None and not df_block.empty:
        col_code = next((c for c in df_block.columns if '代號' in c), None)
        col_name = next((c for c in df_block.columns if '名稱' in c), None)
        col_price = next((c for c in df_block.columns if '單價' in c or '成交價' in c), None)
        col_vol = next((c for c in df_block.columns if '股數' in c or '張數' in c or '成交量' in c), None)
        col_amt = next((c for c in df_block.columns if '金額' in c or '總額' in c), None)
        # 🔥 新增：動態抓取交易別 (證交所通常寫「交易別」或「類別」)
        col_type = next((c for c in df_block.columns if '交易別' in c or '類別' in c), None)

        if all([col_code, col_name, col_price, col_vol, col_amt]):
            df_block['代號'] = df_block[col_code].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
            df_block['股票名稱'] = df_block[col_name]
            df_block['成交價'] = pd.to_numeric(df_block[col_price].astype(str).replace(',', '', regex=True), errors='coerce')
            df_block['成交股數'] = pd.to_numeric(df_block[col_vol].astype(str).replace(',', '', regex=True), errors='coerce')
            df_block['成交金額'] = pd.to_numeric(df_block[col_amt].astype(str).replace(',', '', regex=True), errors='coerce')
            # 🔥 處理交易別，若找不到該欄位則預設填入 '-'
            df_block['交易別'] = df_block[col_type].fillna('-') if col_type else '-'
            
            df_block = df_block[(df_block['代號'] != '0') & (df_block['代號'] != '') & (df_block['代號'] != 'nan')]

            grouped_block = df_block.groupby(['代號', '股票名稱']).agg({
                # 🔥 將同檔股票的不同交易別合併顯示 (例如: 逐筆交易、配對交易)
                '交易別': lambda x: '、'.join(sorted(set([str(i) for i in x.dropna() if str(i).strip() != '-']))),
                '成交價': lambda x: ' / '.join(sorted(set([clean_number_for_display(i) for i in x.dropna()]))),
                '成交股數': 'sum',
                '成交金額': 'sum'
            }).reset_index()

            grouped_block['成交張數'] = (grouped_block['成交股數'] / 1000).astype(int).apply(lambda x: f"{x:,}")
            grouped_block['總額(億)'] = (grouped_block['成交金額'] / 100000000).apply(lambda x: f"{x:.2f}".rstrip('0').rstrip('.'))

            unique_ids = grouped_block['代號'].unique()
            close_price_dict = {}
            if len(unique_ids) > 0:
                yf_tickers = " ".join([f"{sid}.TW" for sid in unique_ids])
                try:
                    df_yf = yf.download(yf_tickers, period="5d", progress=False)
                    if not df_yf.empty and 'Close' in df_yf:
                        close_data = df_yf['Close']
                        if len(unique_ids) == 1: close_price_dict[unique_ids[0]] = str(int(round(close_data.dropna().iloc[-1])))
                        else:
                            for sid in unique_ids:
                                tkr = f"{sid}.TW"
                                if tkr in close_data.columns and not close_data[tkr].dropna().empty: 
                                    close_price_dict[sid] = str(int(round(close_data[tkr].dropna().iloc[-1])))
                except: pass

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
            # 🔥 將交易別加入最終顯示清單
            display_df = grouped_block[['代號', '股票名稱', '交易別', '成交價', '▼收盤價', '成交張數', '總額(億)']].copy()
            display_df = display_df.rename(columns={'成交價': dynamic_price_col})

            # 🔥 保留原本貼心的紅綠字體提示，但改用 Pandas 內建的 Style 傳給 st.dataframe
            def highlight_price(row):
                styles = [''] * len(row)
                try:
                    target_idx = row.index.get_loc(dynamic_price_col)
                    prices = [float(p) for p in str(row[dynamic_price_col]).split(' / ')]
                    avg_p = sum(prices) / len(prices)
                    c_p = float(str(row['▼收盤價']).replace(',', ''))
                    
                    if c_p > avg_p:
                        styles[target_idx] = 'color: #FF4B4B; font-weight: bold;'
                    elif c_p == avg_p:
                        styles[target_idx] = 'color: #FFA500; font-weight: bold;'
                    else:
                        styles[target_idx] = 'color: #00E272; font-weight: bold;'
                except: pass
                return styles

            # 🔥 使用原生且穩定的 st.dataframe 渲染
            st.dataframe(display_df.style.apply(highlight_price, axis=1), use_container_width=True, hide_index=True)
            
        else:
            st.error("⚠️ 欄位名稱無法匹配，請確認爬蟲格式。")
    else:
        st.info("🕒 目前查無今日鉅額交易資料，請確認資料夾中是否有對應的 CSV 檔案。")


# ==================== Tab 2: 歷史防守價追蹤表 ====================
with tab_hist:
    hist_matrix, detected_files = build_historical_block_matrix()
    
    # 💡 新增：檔案偵測雷達 (協助你確認程式抓到了哪些檔案)
    if detected_files:
        st.caption(f"📡 已自動讀取 {len(detected_files)} 天的歷史檔案，組合中...")
        
    if hist_matrix is not None and not hist_matrix.empty:
        st.dataframe(hist_matrix, use_container_width=True, hide_index=True)
    else:
        st.info("📂 資料夾內尚無足夠的歷史交易紀錄，請確認檔名包含「鉅額」字樣。")
        
# ==========================================以上網頁核心區塊
# ==========================================
# 🏆 頂級選股池核心引擎 (科技藍發光卡片版 + 千張/四百張雙軌雷達)
# ==========================================
with top_pool_container:
    st.write("---")
    st.markdown("<div id='section-top-pool'></div>", unsafe_allow_html=True)
    
    import os
    import glob
    import re
    import json
    import pandas as pd
    import datetime

    def get_df_safe(key): return st.session_state.get(key, pd.DataFrame())
    
    df_b5_1000 = get_df_safe('df_blk5_1000')
    df_b5_400 = get_df_safe('df_blk5')
    
    # 1. 自動掃描最新資料日期
    all_files = glob.glob(os.path.join(DATA_DIR, "*"))
    anchor_date_str = "00000000"
    
    d_b1_inst, d_b23_chip, d_b4_margin, d_b5_share = "00000000", "00000000", "00000000", "00000000"
    
    for f in all_files:
        filename = os.path.basename(f)
        match = re.search(r'(202\d{5})', filename)
        if match:
            file_date = match.group(1)
            if file_date > anchor_date_str: anchor_date_str = file_date
                
            if "持股排名變化" in filename or "JSON_History" in filename:
                if file_date > d_b1_inst: d_b1_inst = file_date
            elif "佔成交比" in filename or "連買" in filename or "買賣超" in filename:
                if file_date > d_b23_chip: d_b23_chip = file_date
            elif "融資" in filename or "融券" in filename or "借券" in filename or "資券" in filename:
                if file_date > d_b4_margin: d_b4_margin = file_date

    # 🔥 大戶檔案掃描 (找出真實 0605 日期)
    b5_files = (
        glob.glob(os.path.join(DATA_DIR, "*大股東*")) + 
        glob.glob(os.path.join(DATA_DIR, "*神秘金字塔*")) + 
        glob.glob(os.path.join(DATA_DIR, "*集保*"))
    )
    if b5_files:
        latest_b5_file = sorted(b5_files, reverse=True)[0]
        try:
            with open(latest_b5_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
                head_content = f.read(4000)
                
                d_match = re.search(r'(\d{4})週動態', head_content)
                if d_match:
                    d_b5_share = f"2026{d_match.group(1)}"
                else:
                    d_match2 = re.search(r'更新\s*日期[^\d]*(\d{4})', head_content)
                    if d_match2:
                        d_b5_share = f"2026{d_match2.group(1)}"
                    else:
                        f_match = re.search(r'(202\d{5})', os.path.basename(latest_b5_file))
                        if f_match: d_b5_share = f_match.group(1)
        except: pass

    def fmt_d(d_str): return f"{d_str[4:6]}/{d_str[6:]}" if d_str != "00000000" else "--/--"

    # 🌟 科技風漸層橫幅標題
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #38bdf8; 
                border-bottom: 1px solid #38bdf8; 
                padding: 15px 20px; 
                border-radius: 10px;
                text-align: center;
                box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2);
                margin-bottom: 20px;">
        <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
            🏆 數據分析觀察名單
        </h2>
        <div style='font-size:13px; color:#00D2FF; font-weight:500; margin-top:8px;'>
             資料基準日 : 📍區塊1(法人): {fmt_d(d_b1_inst)} ｜ 📍區塊2&3(籌碼): {fmt_d(d_b23_chip)} ｜ 📍區塊4(資券): {fmt_d(d_b4_margin)} ｜ 📍區塊5(大戶): {fmt_d(d_b5_share)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.info("💡 **評分方式**：法人籌碼上榜為底，搭配「千張大戶權重加乘」與其他數據積分。(請參考▼明細)")

        if 'my_final_df' not in st.session_state or st.session_state['my_final_df'].empty:
            st.warning("⚠️ 尚未載入區塊 1 資料，無法進行選股池評比。")
        else:
            df_b1 = st.session_state['my_final_df'].copy()
            dyn_col = next((c for c in df_b1.columns if '動態' in c or '動能' in c), None)
            rank_col = next((c for c in df_b1.columns if '今日上榜' in c or '上榜' in c), None)
            
            if dyn_col:
                mask = df_b1[dyn_col].astype(str).str.contains('趨緩|上升|升|吸籌|衝進|回歸', na=False)
                pool_df = df_b1[mask].copy()
            else:
                pool_df = df_b1.copy()
                
            if pool_df.empty:
                st.warning("⚪ 目前區塊 1 中沒有符合動能的標的。")
            else:
                fo_sell_ids, it_sell_ids = set(), set()
                try:
                    fo_sell_files = glob.glob(os.path.join(DATA_DIR, "*外資賣出佔成交比*3日*.csv"))
                    if not fo_sell_files: fo_sell_files = glob.glob(os.path.join(DATA_DIR, "*外資賣出佔成交比*.csv"))
                    if fo_sell_files:
                        df_fs = robust_read_csv(sorted(fo_sell_files, reverse=True)[0])
                        id_c = next((c for c in df_fs.columns if '代號' in c), None)
                        if id_c: fo_sell_ids = set(df_fs[id_c].astype(str).str.replace(r'\D', '', regex=True))
                    
                    it_sell_files = glob.glob(os.path.join(DATA_DIR, "*投信賣出佔成交比*5日*.csv"))
                    if not it_sell_files: it_sell_files = glob.glob(os.path.join(DATA_DIR, "*投信賣出佔成交比*.csv"))
                    if it_sell_files:
                        df_is = robust_read_csv(sorted(it_sell_files, reverse=True)[0])
                        id_c = next((c for c in df_is.columns if '代號' in c), None)
                        if id_c: it_sell_ids = set(df_is[id_c].astype(str).str.replace(r'\D', '', regex=True))
                except: pass

                df_b2_1, df_b2_2 = get_df_safe('df_blk2_1'), get_df_safe('df_blk2_2')
                df_b2_3, df_b2_4 = get_df_safe('df_blk2_3'), get_df_safe('df_blk2_4')
                df_b3 = get_df_safe('df_blk3_main')
                
                df_b4_mar_pct, df_b4_mar_vol = get_df_safe('df_margin_pct'), get_df_safe('df_margin_vol')
                df_b4_sho_pct, df_b4_sho_vol = get_df_safe('df_short_pct'), get_df_safe('df_short_vol')
                df_b4_mp_pct, df_b4_mp_vol = get_df_safe('df_margin_plus_pct'), get_df_safe('df_margin_plus_vol')
                
                s_b4_mar_pct, s_b4_mar_vol = set(df_b4_mar_pct.get('股票代號', [])), set(df_b4_mar_vol.get('股票代號', []))
                s_b4_sho_pct, s_b4_sho_vol = set(df_b4_sho_pct.get('股票代號', [])), set(df_b4_sho_vol.get('股票代號', []))
                s_b4_mp_pct, s_b4_mp_vol = set(df_b4_mp_pct.get('股票代號', [])), set(df_b4_mp_vol.get('股票代號', []))

                def check_b2_strict(df, sid, bad_keywords):
                    if df.empty or sid not in df['股票代號'].values: return False
                    dyn = str(df[df['股票代號'] == sid].iloc[0].get('今日短動態', ''))
                    if any(bad in dyn for bad in bad_keywords): return False
                    return True

                bad_b2_vol = ['持平', '調節洗盤', '劇烈倒貨', '觀望']
                bad_b2_iss = ['轉賣反轉', '籌碼沉澱中', '今日量縮持平']

                def get_b3_score(df, sid, type_keyword):
                    if df.empty: return 0, ""
                    match = df[(df['股票代號'] == sid) & (df['連買類型'].str.contains(type_keyword))]
                    if match.empty: return 0, ""
                    days = pd.to_numeric(match.iloc[0].get('連買週期數', 0), errors='coerce')
                    if pd.isna(days) or days == 0: return 0, ""
                    if '日' in type_keyword:
                        if days >= 10: return 1.0, f"✔️({days}日)"
                        elif days >= 5: return 0.8, f"✔️({days}日)"
                        else: return 0.5, f"✔️({days}日)"
                    else:
                        if days >= 10: return 2.0, f"✔️({days}週)"
                        elif days >= 5: return 1.5, f"✔️({days}週)"
                        else: return 1.0, f"✔️({days}週)"

                def get_today_ratio(df, stock_id, col_name):
                    if df is not None and not df.empty and stock_id in df['股票代號'].values:
                        try: return float(df.loc[df['股票代號'] == stock_id, col_name].iloc[0])
                        except: return 0.0
                    return 0.0

                block_sids = set()
                try:
                    temp_block = fetch_block_trades()
                    if not temp_block.empty:
                        block_sids = set(temp_block['證券代號'].astype(str).str.replace(r'\D', '', regex=True))
                except: pass

                results = []
                for _, row in pool_df.iterrows():
                    sid = str(row['股票代號']).strip()
                    sname = str(row.get('股票名稱', '')).strip()
                    b1_dyn = str(row.get(dyn_col, '')) if dyn_col else '-'
                    
                    try:
                        delta_val = float(row.get('△', 0.0))
                        if abs(delta_val) < 0.005: b1_delta = "0.00"
                        else: b1_delta = f"+{delta_val:.2f}" if delta_val > 0 else f"{delta_val:.2f}"
                    except:
                        b1_delta = "0.00"
                    
                    if sid in block_sids: b1_dyn = f"{b1_dyn} | 💸 鉅額交易"
                        
                    b1_rank = str(row.get(rank_col, '-')) if rank_col else '-'
                    score = 0.0
                    details = [] 
                    
                    if check_b2_strict(df_b2_1, sid, bad_b2_vol): score += 1; details.append("外買佔: +1"); r_b2_1 = "✔️"
                    else: r_b2_1 = ""
                    if check_b2_strict(df_b2_2, sid, bad_b2_vol): score += 1; details.append("投買佔: +1"); r_b2_2 = "✔️"
                    else: r_b2_2 = ""
                    if check_b2_strict(df_b2_3, sid, bad_b2_iss): score += 1; details.append("外佔發行: +1"); r_b2_3 = "✔️"
                    else: r_b2_3 = ""
                    if check_b2_strict(df_b2_4, sid, bad_b2_iss): score += 1; details.append("投佔發行: +1"); r_b2_4 = "✔️"
                    else: r_b2_4 = ""
                    
                    if get_today_ratio(df_b2_1, sid, '當日買佔比%') <= -10: score -= 0.5; details.append("外買佔(<-10%): -0.5")
                    if get_today_ratio(df_b2_2, sid, '當日買佔比%') <= -10: score -= 0.5; details.append("投買佔(<-10%): -0.5")
                    if get_today_ratio(df_b2_3, sid, '當日買發比%') <= -10: score -= 0.5; details.append("外佔發(<-10%): -0.5")
                    if get_today_ratio(df_b2_4, sid, '當日買發比%') <= -10: score -= 0.5; details.append("投佔發(<-10%): -0.5")
                    
                    s_fd, r_b3_fd = get_b3_score(df_b3, sid, '外資日'); score += s_fd; 
                    if s_fd > 0: details.append(f"外資日連: +{s_fd}")
                    s_fw, r_b3_fw = get_b3_score(df_b3, sid, '外資週'); score += s_fw; 
                    if s_fw > 0: details.append(f"外資週連: +{s_fw}")
                    s_id, r_b3_id = get_b3_score(df_b3, sid, '投信日'); score += s_id; 
                    if s_id > 0: details.append(f"投信日連: +{s_id}")
                    s_iw, r_b3_iw = get_b3_score(df_b3, sid, '投信週'); score += s_iw; 
                    if s_iw > 0: details.append(f"投信週連: +{s_iw}")
                    
                    r_b4_mar = ""
                    b4_list_count = 0
                    if sid in s_b4_mar_pct: r_b4_mar += "✔️(幅)"; score += 1.0; details.append("資減(幅): +1.0"); b4_list_count += 1
                    if sid in s_b4_mar_vol: r_b4_mar += "✔️(量)"; score += 0.5; details.append("資減(量): +0.5"); b4_list_count += 1
                    
                    r_b4_sho = ""
                    if sid in s_b4_sho_pct: r_b4_sho += "✔️(幅)"; score += 1.0; details.append("借減(幅): +1.0"); b4_list_count += 1
                    if sid in s_b4_sho_vol: r_b4_sho += "✔️(量)"; score += 0.5; details.append("借減(量): +0.5"); b4_list_count += 1
                    
                    r_b4_mp = ""
                    if sid in s_b4_mp_pct: r_b4_mp += "✔️(幅)"; score += 1.0; details.append("券增(幅): +1.0"); b4_list_count += 1
                    if sid in s_b4_mp_vol: r_b4_mp += "✔️(量)"; score += 0.5; details.append("券增(量): +0.5"); b4_list_count += 1
                    
                    if b4_list_count > 0:
                        change_val = 0.0
                        b4_tables = [df_b4_mar_pct, df_b4_mar_vol, df_b4_sho_pct, df_b4_sho_vol, df_b4_mp_pct, df_b4_mp_vol]
                        for b4_df in b4_tables:
                            if not b4_df.empty and sid in b4_df['股票代號'].values and '漲跌幅%' in b4_df.columns:
                                try: 
                                    change_val = float(str(b4_df.loc[b4_df['股票代號'] == sid, '漲跌幅%'].iloc[0]).replace('%', ''))
                                    break 
                                except: pass
                        
                        if change_val > 0:
                            score += 0.7; details.append("榜上+當日上漲: +0.7")
                            if change_val > 3:
                                score += 0.7; details.append("榜上+漲幅>3%: +0.7")
                                
                        # 🔥 已修復 && 為 and
                        short_decrease_val = 0.0
                        if not df_b4_sho_pct.empty and sid in df_b4_sho_pct['股票代號'].values:
                            s_col = next((c for c in df_b4_sho_pct.columns if '當日' in str(c) and ('%' in str(c) or '增減' in str(c))), None)
                            if s_col:
                                try: short_decrease_val = float(str(df_b4_sho_pct.loc[df_b4_sho_pct['股票代號'] == sid, s_col].iloc[0]).replace('%', ''))
                                except: pass
                        if abs(short_decrease_val) >= 1:
                            score += 1.2; details.append("空頭認輸(借券減>1%): +1.2")

                    r_b5_1000, r_b5_400 = "-", "-"
                    trend_1000_val, trend_400_val = "", ""
                    
                    if not df_b5_1000.empty and sid in df_b5_1000['股票代號'].values:
                        trend_1000_val = str(df_b5_1000[df_b5_1000['股票代號'] == sid].iloc[0].get('週動態', ''))
                        if '大增' in trend_1000_val: score += 2.0; r_b5_1000 = "🔥千張大增(+2)"; details.append("千張大增: +2")
                        elif '增' in trend_1000_val and '微' not in trend_1000_val: score += 1.0; r_b5_1000 = "📈千張增(+1)"; details.append("千張增: +1")
                        elif '微增' in trend_1000_val: score += 0.5; r_b5_1000 = "↗️千微增(+0.5)"; details.append("千張微增: +0.5")
                        elif '大減' in trend_1000_val: score -= 0.5; r_b5_1000 = "🚨千大減(-0.5)"; details.append("千張大減: -0.5")
                        elif '減' in trend_1000_val: score -= 0.5; r_b5_1000 = "📉千減(-0.5)"; details.append("千張減: -0.5")
                        else: r_b5_1000 = f"千{trend_1000_val}"

                    if not df_b5_400.empty and sid in df_b5_400['股票代號'].values:
                        trend_400_val = str(df_b5_400[df_b5_400['股票代號'] == sid].iloc[0].get('週動態', ''))
                        if '大增' in trend_400_val: score += 1.0; r_b5_400 = "🔥四百大增(+1)"; details.append("四百大增: +1")
                        elif '增' in trend_400_val and '微' not in trend_400_val: score += 0.5; r_b5_400 = "📈四百增(+0.5)"; details.append("四百增: +0.5")
                        elif '微增' in trend_400_val: score += 0.0; r_b5_400 = "↗️四百微增(0)"
                        elif '大減' in trend_400_val: score -= 0.0; r_b5_400 = "🚨四百大減(0)" 
                        elif '減' in trend_400_val: score -= 0.0; r_b5_400 = "📉四百減(0)"
                        else: r_b5_400 = f"四百{trend_400_val}"

                    if ('增' in trend_1000_val and '減' in trend_400_val):
                        score += 1.0
                        details.append("🌟籌碼極集中: +1")
                        r_b5_1000 = f"{r_b5_1000}🌟"

                    if r_b5_1000 != "-" or r_b5_400 != "-": r_b5 = f"{r_b5_1000} | {r_b5_400}"
                    else: r_b5 = "-"
                    
                    is_fo_sell = sid in fo_sell_ids; is_it_sell = sid in it_sell_ids
                    if is_fo_sell and is_it_sell: r_warn = "🚨外投雙倒"; score -= 2.0; details.append("外投雙倒: -2")
                    elif is_fo_sell: r_warn = "⚠️外資倒"
                    elif is_it_sell: r_warn = "⚠️投信倒"
                    else: r_warn = "-"

                    score_breakdown = " \n".join(details) if details else "無加扣分"

                    results.append({
                        '總分': score, '代號': sid, '名稱': sname, '▼明細': score_breakdown, '△': b1_delta,
                        '最新動態': b1_dyn, '今日上榜': b1_rank, '賣出警示': r_warn,
                        '外買佔比': r_b2_1, '投買佔比': r_b2_2, '外佔發行': r_b2_3, '投佔發行': r_b2_4,
                        '外日連': r_b3_fd, '外週連': r_b3_fw, '投日連': r_b3_id, '投週連': r_b3_iw,
                        '資減': r_b4_mar, '借減': r_b4_sho, '券增': r_b4_mp,
                        '大股東動向': r_b5
                    })
                    
                res_df = pd.DataFrame(results).sort_values(by='總分', ascending=False).drop_duplicates(subset=['代號']).reset_index(drop=True)
                
                # ==========================================
                # 🔥 Delta (▼變量) 計算引擎
                # ==========================================
                prev_scores_dict = {}
                hist_combined = pd.DataFrame() 
                
                try:
                    gs_history = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史", ttl=10)
                    gs_history = gs_history.dropna(how="all")
                    if not gs_history.empty and '紀錄日期' in gs_history.columns:
                        gs_history['紀錄日期'] = gs_history['紀錄日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8)
                        hist_combined = gs_history.copy()
                        available_dates = sorted(gs_history['紀錄日期'].unique(), reverse=True)
                        if len(available_dates) >= 2:
                            prev_date = available_dates[1]
                            prev_df = gs_history[gs_history['紀錄日期'] == prev_date]
                            id_col = '代號' if '代號' in prev_df.columns else '股票代號' if '股票代號' in prev_df.columns else None
                            if id_col:
                                clean_ids = prev_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
                                prev_scores_dict = dict(zip(clean_ids, prev_df['總分']))
                except: pass 

                def calc_table_delta(row):
                    sid = str(row['代號']).strip()
                    try: curr_score = float(row.get('總分', 0))
                    except: curr_score = 0.0
                    if sid in prev_scores_dict:
                        try: prev_score = float(prev_scores_dict[sid])
                        except: prev_score = 0.0
                        delta = curr_score - prev_score
                        if delta > 0.01: return f"+{delta:.1f}"
                        elif delta < -0.01: return f"{delta:.1f}"
                        else: return "0.0"
                    else: return f"🆕 +{curr_score:.1f}"

                if not res_df.empty and '總分' in res_df.columns:
                    res_df['▼變量'] = res_df.apply(calc_table_delta, axis=1)

                cols = [c for c in res_df.columns if c not in ['▼變量', '▼明細', '△', '賣出警示']]
                score_idx = cols.index('總分')
                cols.insert(score_idx + 1, '▼變量')
                name_idx = cols.index('名稱')
                cols.insert(name_idx + 1, '▼明細')
                detail_idx = cols.index('▼明細')
                cols.insert(detail_idx + 1, '△')
                rank_idx = cols.index('今日上榜')
                cols.insert(rank_idx + 1, '賣出警示')
                res_df = res_df[cols]

                st.session_state['top_pool_df'] = res_df
                
                # 💾 歷史紀錄存檔機制
                if res_df is not None and not res_df.empty:
                    try:
                        if anchor_date_str != "00000000":
                            save_df = res_df.copy()
                            save_df.insert(0, '紀錄日期', anchor_date_str)
                            try:
                                old_df = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史", ttl=0)
                                old_df = old_df.dropna(how="all")
                                if '紀錄日期' in old_df.columns:
                                    old_df['紀錄日期'] = old_df['紀錄日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8)
                                    old_df = old_df[old_df['紀錄日期'] != anchor_date_str]
                                final_save_df = pd.concat([old_df, save_df], ignore_index=True)
                            except: final_save_df = save_df
                            conn.update(spreadsheet=SHEET_URL, worksheet="選股歷史", data=final_save_df)
                    except: pass 

                tab1, tab2, tab3 = st.tabs(["🔹 今日最新排行", "🔹 歷史分數追蹤表", "🔹 模型驗證：每週 Top 5 追蹤"])
                
                with tab1:
                    st.dataframe(
                        res_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "▼明細": st.column_config.TextColumn("▼明細", help="滑鼠游標停留在這裡，查看完整明細", width="small", max_chars=4)
                        }
                    )
                    st.success(f"選股池掃描完成！今日共過濾出 {len(res_df)} 檔潛力標的。")
                    
                with tab2:
                    try:
                        if not hist_combined.empty:
                            recent_dates = sorted(hist_combined['紀錄日期'].unique(), reverse=True)[:20]
                            df_h = hist_combined[hist_combined['紀錄日期'].isin(recent_dates)].copy()
                            id_col = '代號' if '代號' in df_h.columns else '股票代號' if '股票代號' in df_h.columns else None
                            
                            if id_col and '總分' in df_h.columns:
                                df_h['日期'] = df_h['紀錄日期'].apply(lambda x: f"{x[4:6]}/{x[6:]}" if len(x)==8 else x)
                                df_h['代號'] = df_h[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
                                df_h = df_h[['代號', '總分', '日期']]
                                
                                hist_pivot = df_h.pivot_table(index='代號', columns='日期', values='總分', aggfunc='first').reset_index()
                                date_columns = [col for col in hist_pivot.columns if col not in ['代號', '名稱']]
                                sorted_date_columns = sorted(date_columns, reverse=True)
                                hist_pivot = hist_pivot[['代號'] + sorted_date_columns]
                                
                                name_mapping = dict(zip(res_df['代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True), res_df['名稱']))
                                hist_pivot.insert(1, '名稱', hist_pivot['代號'].map(name_mapping).fillna('-'))
                                
                                latest_day = sorted_date_columns[0]
                                hist_pivot = hist_pivot[hist_pivot['名稱'] != '-']
                                if not hist_pivot.empty and latest_day in hist_pivot.columns:
                                    hist_pivot = hist_pivot.sort_values(by=latest_day, ascending=False).reset_index(drop=True)
                                st.dataframe(hist_pivot, use_container_width=True, hide_index=True)
                                st.info("💡 二篩進榜標的在選股池中的總分變化，觀察籌碼動能的延續性與驗證 ▼變量！")
                        else: st.warning("尚無足夠的歷史分數紀錄。")
                    except: pass

                with tab3:
                    st.markdown("### 🏆 AI 嚴選：今日最強 5 檔")
                    st.info("💡 **篩選邏輯**：排除任何帶有「外/投倒貨」警示的標的，並依據「總分」與「當日△」選出前 5 名。")
                    
                    if not res_df.empty:
                        safe_df = res_df[res_df['賣出警示'] == "-"].copy()
                        if not safe_df.empty:
                            safe_df['數值△'] = safe_df['△'].astype(str).str.replace('+', '').str.replace('%', '')
                            safe_df['數值△'] = pd.to_numeric(safe_df['數值△'], errors='coerce').fillna(0)
                            
                            top5_df = safe_df.sort_values(by=['總分', '數值△'], ascending=[False, False]).head(5)
                            top5_df = top5_df.drop(columns=['數值△'])
                            
                            cols = st.columns(5)
                            for idx, (i, row) in enumerate(top5_df.iterrows()):
                                with cols[idx]:
                                    delta_str = str(row['△'])
                                    delta_color = "#FF4B4B" if "+" in delta_str else ("#00E272" if "-" in delta_str else "#E2E8F0")
                                    
                                    st.markdown(
                                        f"""
                                        <div style="background-color:rgba(0, 210, 255, 0.05); border-top: 3px solid #00D2FF; padding: 10px; border-radius: 5px;">
                                            <h4 style="margin:0; color:#E2E8F0;">{row['名稱']}</h4>
                                            <p style="margin:0; font-size:12px; color:#A0AEC0;">{row['代號']}</p>
                                            <h2 style="margin:10px 0; color:#00D2FF;">{row['總分']:.1f} 分</h2>
                                            <p style="margin:0; font-size:14px;"><strong>當日△:</strong> <span style="color:{delta_color}; font-weight:bold;">{delta_str}</span></p>
                                            <p style="margin:5px 0 0 0; font-size:12px; line-height:1.2;">{row['大股東動向']}</p>
                                        </div>
                                        """, unsafe_allow_html=True
                                    )
                            
                            st.write("")
                            st.dataframe(top5_df[['代號', '名稱', '總分', '▼變量', '△', '最新動態', '▼明細']], use_container_width=True, hide_index=True)
                            
                            st.write("---")
                            with st.expander("🛠 站長專用：鎖定本週追蹤名單", expanded=False):
                                c_pw, c_btn = st.columns([1, 2])
                                with c_pw:
                                    track_pw = st.text_input("請輸入密碼解鎖", type="password", key="track_pw")
                                with c_btn:
                                    st.write("")
                                    if track_pw == "DDong888":
                                        if st.button("💾 將以上 5 檔儲存為『本週驗證名單』", type="primary", use_container_width=True):
                                            track_date = datetime.datetime.now().strftime("%Y-%m-%d")
                                            top5_df['鎖定日期'] = track_date
                                            track_path = os.path.join(DATA_DIR, "Weekly_Top5_Tracking.csv")
                                            
                                            if os.path.exists(track_path):
                                                try: old_track = pd.read_csv(track_path, encoding='utf-8-sig')
                                                except: old_track = pd.DataFrame()
                                                new_track = pd.concat([old_track, top5_df], ignore_index=True)
                                            else: new_track = top5_df
                                                
                                            new_track.to_csv(track_path, index=False, encoding='utf-8-sig')
                                            st.success(f"✅ 已成功將 {track_date} 的 Top 5 寫入追蹤資料庫！")
                                    elif track_pw != "": st.error("密碼錯誤")
                                        
                    st.markdown("### 📊 歷史名單回測觀察")
                    track_file = os.path.join(DATA_DIR, "Weekly_Top5_Tracking.csv")
                    if os.path.exists(track_file):
                        try:
                            history_track_df = pd.read_csv(track_file, encoding='utf-8-sig')
                            if not history_track_df.empty:
                                available_weeks = sorted(history_track_df['鎖定日期'].unique(), reverse=True)
                                selected_week = st.selectbox("📅 選擇要回顧的鎖定日期", available_weeks)
                                week_df = history_track_df[history_track_df['鎖定日期'] == selected_week].copy()
                                
                                if not res_df.empty:
                                    today_scores = dict(zip(res_df['代號'].astype(str), res_df['總分']))
                                    today_deltas = dict(zip(res_df['代號'].astype(str), res_df['△']))
                                    week_df['今日分數'] = week_df['代號'].astype(str).map(today_scores).fillna(0)
                                    week_df['今日△'] = week_df['代號'].astype(str).map(today_deltas).fillna("未進榜")
                                    
                                    def score_diff(row):
                                        diff = float(row['今日分數']) - float(row['總分']) 
                                        if diff > 0: return f"📈 +{diff:.1f}"
                                        elif diff < 0: return f"📉 {diff:.1f}"
                                        else: return "-"
                                    week_df['模型分數變化'] = week_df.apply(score_diff, axis=1)
                                
                                show_cols = ['鎖定日期', '代號', '名稱', '總分', '今日分數', '模型分數變化', '今日△', '大股東動向']
                                st.dataframe(week_df[[c for c in show_cols if c in week_df.columns]], use_container_width=True, hide_index=True)
                                st.info("💡 **驗證方法**：觀察這些鎖定的股票在未來一週的『模型分數變化』是否持續上升？如果分數持續上升且股價也上漲，代表我們的【大股東+集中度】指標非常精準！")
                        except: st.warning("讀取追蹤檔案失敗。")
                    else: st.write("⚪ 尚無歷史追蹤紀錄，請點擊上方按鈕建立第一筆！")
# ==========================================
# 🧪 測試區：Google Sheets 連線測試
# ==========================================
# ==========================================
# 🧪 測試區：Google Sheets 連線測試
# ==========================================


# ==========================================
# 📊 【蜂蜜計數器】本站累計觀測人次統計
# ==========================================
st.write("---")

# 🌟 新增防護罩：如果伺服器上沒有這個資料夾，就自動建立一個，避免當機
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

counter_file = os.path.join(DATA_DIR, "counter.txt")
if not os.path.exists(counter_file):
    with open(counter_file, "w") as f: f.write("1")
    count = 1
else:
    with open(counter_file, "r") as f:
        try: count = int(f.read().strip()) + 1
        except: count = 1
    with open(counter_file, "w") as f: f.write(str(count))

st.markdown(f"<p style='text-align: center; font-size: 16px; color: #DDA400; font-weight: bold;'>🐝 🍯 迷途不回家的小蜜蜂： {count} 隻 ｜ 祝阿東甜美收尾，順利通關畢業！ 🍯 🐝</p>", unsafe_allow_html=True)
