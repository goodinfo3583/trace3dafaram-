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

# 👉 步驟 2：變數都認識了，再一次性幫它們建立資料夾
for folder in [SCORE_HISTORY_DIR, MARKET_HISTORY_DIR, BLOCK_HISTORY_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)
# ==========置頂區塊測試區==================
# ==========================================
# ==========================================
# ==========================================
# 🧹 清道夫：強制刪除週末錯誤生成的假檔案 (05/28, 05/30, 05/31)
# ==========================================
# 確保所有資料夾在雲端都會被自動建立
for folder in [SCORE_HISTORY_DIR, MARKET_HISTORY_DIR, BLOCK_HISTORY_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

for bad_date in ["20260528", "20260530", "20260531"]:
    bad_file = os.path.join(SCORE_HISTORY_DIR, f"scores_{bad_date}.csv")
    if os.path.exists(bad_file):
        try: os.remove(bad_file)
        except: pass

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
# 🔍 個股籌碼快搜 "標題" (全區塊聯動掃描版 - 終極全景版)
# ==========================================
st.write("---")
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.subheader("🔍 個股籌碼快搜 (全方位診斷)")
# ==========================================
# 📈 繪製 K 線圖與技術分析引擎 (加入 KD、Y軸標籤、手機平移與極簡工具列)
# ==========================================
def render_technical_chart(stock_id, timeframe="日線", selected_mas=[], show_rsi=False, show_macd=False, show_kd=False):
    import yfinance as yf
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    import streamlit as st

    try:
        # 1. 智慧連線：下載歷史資料
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

        # ==========================================
        # 🧠 新增：技術型態雷達引擎 (動態掃描均線、爆量、收斂)
        # ==========================================
        def generate_technical_signals(df):
            signals = []
            if df.empty or len(df) < 20: return signals
            
            latest_close = df['Close'].iloc[-1]
            latest_vol = df['Volume'].iloc[-1]
            
            # 1. 🧨 爆近期大量提示 (今日成交量 > 20日均量 2.5倍)
            vol_20ma = df['Volume'].rolling(window=20).mean().iloc[-2] # 拿昨天的均量來比
            if pd.notna(vol_20ma) and vol_20ma > 0 and latest_vol > (vol_20ma * 2.5):
                signals.append(f"🧨 爆量出擊：今日成交量達 20 日均量的 {latest_vol/vol_20ma:.1f} 倍！")

            # 2. 🎯 均線回測與關鍵支撐 (差距 1.5% 內視為回測)
            mas = {'5MA': 5, '10MA': 10, '20MA': 20, '60MA': 60, '120MA': 120, '240MA': 240}
            for ma_name, period in mas.items():
                if len(df) >= period:
                    ma_val = df['Close'].rolling(window=period).mean().iloc[-1]
                    # 股價在均線上，且距離均線極近 (大於 0 但小於 1.5%)
                    if 0 < (latest_close - ma_val) / ma_val < 0.015:
                        signals.append(f"🎯 回測支撐：股價目前極度貼近 {ma_name} ({ma_val:.2f}) 關鍵支撐線。")

            # 3. 🌀 短中長均線糾結提示 (5, 10, 20MA 極度壓縮在 2% 空間內)
            if len(df) >= 20:
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma10 = df['Close'].rolling(10).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma_max, ma_min = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                if pd.notna(ma_max) and (ma_max - ma_min) / ma_min < 0.02:
                    signals.append("🌀 均線糾結：短天期 (5/10/20MA) 成本線高度重合壓縮，醞釀表態！")

            # 4. 📐 三角收斂 / 波動壓縮提示 (近20日高低落差，比前一個20日縮小40%以上)
            if len(df) >= 60:
                recent_high = df['High'].iloc[-20:].max()
                recent_low = df['Low'].iloc[-20:].min()
                prev_high = df['High'].iloc[-40:-20].max()
                prev_low = df['Low'].iloc[-40:-20].min()
                
                recent_volatility = recent_high - recent_low
                prev_volatility = prev_high - prev_low
                if prev_volatility > 0 and recent_volatility < (prev_volatility * 0.6):
                    signals.append("📐 型態壓縮：近一個月股價高低波幅急遽收斂，疑似三角收斂末端。")
            # 5. 🚀 股價創波段新高提示 (創 60 日新高)
            if len(df) >= 60:
                # 找出過去 60 天的最高價
                highest_60d = df['High'].iloc[-60:].max()
                # 如果今天的最高價，等於或突破過去 60 天的最高價
                if df['High'].iloc[-1] >= highest_60d:
                    signals.append("🚀 波段創高：今日股價突破 60 日 (約一季) 以來新高點，上攻動能極強！")

            # 6. 📈 均線多頭排列提示 (5MA > 10MA > 20MA > 60MA 且季線上揚)
            if len(df) >= 60:
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma10 = df['Close'].rolling(10).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma60 = df['Close'].rolling(60).mean().iloc[-1]
                ma60_prev = df['Close'].rolling(60).mean().iloc[-2] # 昨天的 60MA
                
                # 嚴格定義：收盤價站上所有均線，且均線照順序排列，外加 60MA 必須是向上的
                if pd.notna(ma60) and (latest_close > ma5 > ma10 > ma20 > ma60) and (ma60 > ma60_prev):
                    signals.append("📈 多頭排列：短中長期均線 (5/10/20/60MA) 呈現完美多頭發散，趨勢明確翻多！")

            return signals

        # 執行雷達掃描 (固定用日線資料來掃描最精確，避免切換週線時失真)
        tech_signals = generate_technical_signals(daily_df)

        # ==========================================
        # 🔥 顯示技術雷達面板
        # ==========================================
        if tech_signals:
            # 建立一個暗黑風格的雷達警告框
            signal_html = "<div style='background-color: rgba(0, 210, 255, 0.1); border-left: 4px solid #00D2FF; padding: 10px; border-radius: 5px; margin-bottom: 15px;'>"
            signal_html += "<h5 style='color: #00D2FF; margin-top:0px; margin-bottom: 10px;'>📡 AI 盤中技術型態雷達</h5>"
            for sig in tech_signals:
                signal_html += f"<p style='color: #E2E8F0; margin: 5px 0px; font-size: 15px;'>{sig}</p>"
            signal_html += "</div>"
            st.markdown(signal_html, unsafe_allow_html=True)

        # ==========================================
        # 轉換 K 線週期 (這裡有把括號寫完整了！)
        # ==========================================
        if timeframe == "週線":
            daily_df = daily_df.resample('W-FRI').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        elif timeframe == "月線":
            daily_df = daily_df.resample('ME').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()


        # 2. 計算均線
        ma_windows = [5, 10, 20, 60, 120, 240]
        for ma in ma_windows:
            daily_df[f'{ma}MA'] = daily_df['Close'].rolling(window=ma).mean()

        # 3. 內建量化指標計算 (RSI, MACD, KD)
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
            # KD (9, 3, 3) 台股標準平滑演算法
            low_9 = daily_df['Low'].rolling(window=9).min()
            high_9 = daily_df['High'].rolling(window=9).max()
            rsv = (close_series - low_9) / (high_9 - low_9).replace(0, 1e-9) * 100
            daily_df['K'] = rsv.ewm(com=2, adjust=False).mean() # com=2 相當於 1/3 平滑
            daily_df['D'] = daily_df['K'].ewm(com=2, adjust=False).mean()

        def get_latest_price(col):
            valid_data = daily_df[col].dropna()
            if not valid_data.empty:
                val = valid_data.iloc[-1]
                if isinstance(val, pd.Series): val = val.iloc[0]
                return f"{float(val):.2f}"
            return "-"

        # 4. 智慧動態調配畫布高度
        rows = 2
        row_heights = [0.5, 0.15]
        if show_rsi: rows += 1; row_heights.append(0.12)
        if show_macd: rows += 1; row_heights.append(0.14)
        if show_kd: rows += 1; row_heights.append(0.14)

        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.02, row_heights=row_heights)
                            
        #繪製K線選擇顏色
        up_color = 'rgb(240, 90, 90)'     
        down_color = 'rgb(80, 200, 120)'  

        # ==========================================
        # 5. 繪製主 K 線 (乾淨名稱 + 歷史高點標註)
        # ==========================================
        fig.add_trace(go.Candlestick(
            x=daily_df.index, open=daily_df['Open'].squeeze(), high=daily_df['High'].squeeze(), 
            low=daily_df['Low'].squeeze(), close=daily_df['Close'].squeeze(), 
            name='K線', 
            increasing=dict(line=dict(color=up_color, width=1.5), fillcolor=up_color),
            decreasing=dict(line=dict(color=down_color, width=1.5), fillcolor=down_color),
            hovertemplate="開：%{open:.2f}<br>高：%{high:.2f}<br>低：%{low:.2f}<br>收：%{close:.2f}<extra></extra>"
        ), row=1, col=1)
        
        # 🔥 升級 1：鎖死 Y 軸底線，徹底消滅負數股價 (-50)
        fig.update_yaxes(title_text="股價 (TWD)", row=1, col=1, title_font=dict(size=12, color="#E2E8F0"), rangemode="nonnegative")

        # 🔥 升級 2：自動抓取 5 年內歷史最高價，並繪製黃金天花板標示線
        if not daily_df.empty:
            max_price = daily_df['High'].max()
            max_date = daily_df['High'].idxmax()
            
            # 畫一條橫貫全圖的金色微透明虛線
            fig.add_hline(y=max_price, line_dash="dot", line_color="rgba(255, 215, 0, 0.4)", row=1, col=1)
            
            # 加上顯眼的價格標籤牌
            fig.add_annotation(
                x=max_date, y=max_price,
                text=f"<b>前高: {max_price:.2f}</b>",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor="#FFD700",
                ax=0, ay=-40, # 箭頭往上偏移，讓標籤浮在 K 線正上方不擋圖
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

        # ==========================================
        # 6. 繪製成交量 (🔥 同步防禦負數成交量)
        # ==========================================
        vol_colors = [up_color if c >= o else down_color for c, o in zip(daily_df['Close'].squeeze(), daily_df['Open'].squeeze())]
        fig.add_trace(go.Bar(
            x=daily_df.index, y=daily_df['Volume'].squeeze(), 
            name='成交量', 
            marker_color=vol_colors,
            showlegend=False, 
            hovertemplate="<b>成交量</b>： %{y}<extra></extra>"
        ), row=2, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1, title_font=dict(size=12, color="#E2E8F0"), rangemode="nonnegative")

        # 7. 動態追加技術指標畫布
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

        # ==========================================
        # 8. 版面美化與防重疊 (終極淨化版)
        # ==========================================
        fig.update_layout(
            # 🔥 升級 1：徹底移除上方標題，不再顯示「股票代號 日線與綜合技術指標」
            xaxis_rangeslider_visible=False,
            height=500 + (rows - 1) * 110, 
            template='plotly_dark',       
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',  
            # 🔥 升級 2：標題移除後，將上方留白(t)從 90 縮小至 30，讓圖表更緊湊
            margin=dict(l=10, r=65, t=30, b=10), 
            hovermode='x unified',
            hoverlabel=dict(bgcolor="#1A202C", font_size=15, font_color="#FFFFFF"),
            legend=dict(
                # 🔥 升級 3：移除「顯示：」字眼，只保留乾淨的按鈕
                orientation="h", 
                yanchor="bottom", 
                y=1.01, 
                xanchor="left", 
                x=0.01, 
                font=dict(color='#E2E8F0', size=16),
                itemsizing='constant'
            ),
            dragmode='pan' 
        )
        
        # 🔥 升級 4：十字游標變細 (0.5)、微黃色，並將背景分隔網格線 (gridcolor) 極度透明化 (0.05)
        fig.update_xaxes(
            showspikes=True, spikecolor="rgba(255, 235, 100, 0.5)", spikesnap="cursor", 
            spikemode="across", spikethickness=0.5, spikedash="dash",
            gridcolor="rgba(255, 255, 255, 0.05)"
        )
        fig.update_yaxes(
            showspikes=True, spikecolor="rgba(255, 235, 100, 0.5)", spikesnap="cursor", 
            spikemode="across", spikethickness=0.5, spikedash="dash", side="right",
            gridcolor="rgba(255, 255, 255, 0.05)"
        )
        
        for r in range(1, rows + 1):
            fig.update_xaxes(hoverformat="%Y-%m-%d", tickformat="%Y-%m-%d", row=r, col=1)
        
        if not daily_df.empty:
            latest_date = daily_df.index[-1] 
            start_date = latest_date - pd.Timedelta(days=140) 
            zoom_range = [start_date.strftime('%Y-%m-%d'), latest_date.strftime('%Y-%m-%d')]
            for r in range(1, rows + 1):
                fig.update_xaxes(range=zoom_range, row=r, col=1)
        
        # ==========================================
        # 🔥 升級 5：動態填補 K 線圖破洞 (精準剃除所有週末與國定假日)
        # ==========================================
        if timeframe == "日線":
            # 1. 產生從第一天到最後一天的「完整日曆天」
            all_days = pd.date_range(start=daily_df.index.min().normalize(), end=daily_df.index.max().normalize(), freq='D')
            
            # 2. 抓出這檔股票「實際有開盤交易的日子」
            actual_days = daily_df.index.normalize()
            
            # 3. 兩者相減，自動抓出所有「沒開盤的日子」(包含六日、國定假日、颱風假)
            missing_days = all_days.difference(actual_days).strftime('%Y-%m-%d').tolist()

            for r in range(1, rows + 1):
                # 將原本死板的 bounds，改成精準隱藏 missing_days
                fig.update_xaxes(rangebreaks=[dict(values=missing_days)], row=r, col=1)
        
        plotly_config = {
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': [
                'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 
                'select2d', 'lasso2d', 'hoverClosestCartesian', 
                'hoverCompareCartesian', 'toggleSpikelines'
            ]
        }
        
        st.plotly_chart(fig, use_container_width=True, key=f"kline_{stock_id}_{timeframe}_{len(selected_mas)}_{show_rsi}_{show_macd}_{show_kd}", config=plotly_config)
        
    except Exception as e:
        st.error(f"❌ 繪製 K 線圖時發生錯誤: {str(e)}")
#===================================
#以上技術線圖
#===================================       

# 🛠️ 定義強韌的搜尋函式
def robust_search_engine(df, query):
    if df is None or df.empty:
        return pd.DataFrame()
        
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

# ==========================================
# 🎯 建立通用掃描與顯示工具 (浮點數級別終極攔截 0% 假象)
# ==========================================
def scan_and_display(title, session_key, query):
    # 先不管有沒有資料，標題一律用 subheader 頂固，確保左右 columns 完全對齊
    st.subheader(title)
    
    if session_key not in st.session_state:
        st.write("⚪ 尚未載入資料表")
        return
        
    df = st.session_state[session_key]
    if df is None or df.empty:
        st.write("⚪ 該榜單無任何資料")
        return
        
    res = robust_search_engine(df, query)
    
    if not res.empty:
        # 🔥 終極攔截器：直接轉成數學小數點來驗證，消滅所有格式變形的「0」
        # 找出所有可能是持股比例或佔比的欄位名稱
        pct_cols = [c for c in res.columns if '持股' in c or '佔' in c or '%' in c]
        
        if pct_cols:
            all_zero = True
            for c in pct_cols:
                val = res.iloc[0][c]
                
                # 1. 如果是 pandas 內建的空值 (NaN)，直接當作 0
                import pandas as pd
                if pd.isna(val):
                    continue
                    
                # 2. 將數值轉為字串，並移除 % 符號與隱藏的空白
                val_str = str(val).strip().replace('%', '')
                
                # 3. 如果是這些特殊無效符號，也當作 0
                if val_str.lower() in ['', '-', 'nan', 'none', 'null']:
                    continue
                    
                # 4. 強制轉換為數學浮點數進行驗證
                try:
                    # 只要數字的絕對值大於 0.0001，就代表這是「真實有持股」的標的
                    if abs(float(val_str)) > 0.0001:
                        all_zero = False
                        break
                except ValueError:
                    # 如果轉不成數字 (例如遇到奇怪的文字)，直接當作無效值跳過
                    continue
            
            # 如果所有持股比例欄位檢查完都被判定為 0 (或空值)，則強制攔截，改顯示未進榜
            if all_zero:
                st.write("⚪ 未進榜")
                return
                
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.write("⚪ 未進榜")

# ==========================================
# 🎯 搜尋輸入框 (導入產業別與全域代號翻譯)
# ==========================================
search_query = st.text_input("請輸入想觀測的股票代號或名稱 (例如: 3231 或 緯創，未顯示任何資料代表持股比未追蹤)：", key="global_search_final")

# 預先準備好全域變數，供下方所有區塊(AI、K線)使用
pure_stock_id = ""
display_name = search_query

if search_query:
    query_clean = search_query.strip()
    industry_label = "未分類"
    
    # 🌟 透過搜尋後台股票代號名稱字典，自動翻譯出正確代號與產業類別
    if query_clean in STOCK_DICT:
        pure_stock_id = STOCK_DICT[query_clean]["id"]
        display_name = f"{STOCK_DICT[query_clean]['id']} {STOCK_DICT[query_clean]['name']}"
        industry_label = STOCK_DICT[query_clean]["industry"]
    else:
        # 模糊搜尋備用 (如果只輸入"台積"，也能找到)
        for k, v in STOCK_DICT.items():
            if query_clean in k:
                pure_stock_id = v["id"]
                display_name = f"{v['id']} {v['name']}"
                industry_label = v["industry"]
                break
    
    # 如果字典真的查不到，最後手段：看看是不是輸入純數字
    if pure_stock_id == "":
        match_num = re.search(r'\d+', query_clean)
        if match_num:
            pure_stock_id = match_num.group(0)

    # 🔥 顯示帶有科技感「產業別」標籤的標題
    st.markdown(f"### 🎯 綜合診斷標的：{display_name} <span style='font-size:16px; background-color:#1E293B; padding:4px 10px; border-radius:6px; color:#00D2FF; margin-left:10px;'>🏷️ {industry_label}</span>", unsafe_allow_html=True)

    # 🔥 動態顯示該標的總分
    pool_df = st.session_state.get('top_pool_df', pd.DataFrame())
    target_score = None
    current_stock_id = pure_stock_id # 將正確代號交給後續系統
    delta_val = 0.0

    if not pool_df.empty:
        # 用正確的代號去總表精準搜尋
        match = robust_search_engine(pool_df, current_stock_id) if current_stock_id else robust_search_engine(pool_df, search_query)
        if not match.empty:
            target_score = match.iloc[0].get('總分', 0)
            delta_val = match.iloc[0].get('Delta (日變動)', 0.0) 

    # 🔥 顯示 Delta 分數
    if target_score is not None and current_stock_id != "":
        delta = delta_val 
        delta_color = "#FF4B4B" if delta > 0 else "#00CC66" if delta < 0 else "#E2E8F0"
        delta_symbol = "🔥" if delta > 0 else "🚨" if delta < 0 else "🔄"
        delta_str = f"+{delta}" if delta > 0 else f"{delta}" 
        
        st.markdown(f"""
        #### 🏆 系統綜合評分：<span style='color:#FFD700; font-size:24px;'>**{target_score}**</span> 分 
        <span style='color:{delta_color}; font-size:16px; margin-left:15px;'>{delta_symbol} Delta變化: **{delta_str}**</span>
        <span style='color:#FFFFFF; font-size:14px; font-weight:normal; margin-left:10px;'>(評分數據僅供參考)</span>
        """, unsafe_allow_html=True)
    else:
        st.markdown("#### 🏆 系統綜合評分：<span style='color:#718096; font-size:18px;'>未達綜合進榜標準 (0分)</span> <span style='color:#FFFFFF; font-size:14px; font-weight:normal;'>(評分數據僅供參考)</span>", unsafe_allow_html=True)


    # ==========================================
    # 📈 K 線圖按鈕、週期切換與技術指標面板
    # ==========================================
    st.write("---")
    if 'show_kline' not in st.session_state:
        st.session_state.show_kline = False
        
    if 'kline_period' not in st.session_state:
        st.session_state.kline_period = "日線"

    button_label = "❌ 關閉技術 K 線圖" if st.session_state.show_kline else "📊 載入最新技術 K 線圖"
    if st.button(button_label, use_container_width=True):
        st.session_state.show_kline = not st.session_state.show_kline
        st.rerun()

    if st.session_state.show_kline:
        # 🔥 剛剛在搜尋區塊頂端已經翻譯好 pure_stock_id 了，這裡直接無腦取用！
        if 'pure_stock_id' in locals() and pure_stock_id != "":          
            st.markdown("##### ⚙️ 技術線圖與指標配置面板")
            
            # 🔥 縮小按鈕魔法：將版面切成 4 塊，前面 3 塊極小，後面留白
            tf_c1, tf_c2, tf_c3, _space = st.columns([1, 1, 1, 5])
            
            # ... (下面 p_day, p_week 的按鈕代碼維持不變，繼續留著) ...
                      
            p_day = "日K" if st.session_state.kline_period == "日線" else "日K"
            p_week = "週K" if st.session_state.kline_period == "週線" else "週K"
            p_month = "月K" if st.session_state.kline_period == "月線" else "月K"
            
            if tf_c1.button(p_day, use_container_width=True, key="btn_p_day"):
                st.session_state.kline_period = "日線"
                st.rerun()
            if tf_c2.button(p_week, use_container_width=True, key="btn_p_week"):
                st.session_state.kline_period = "週線"
                st.rerun()
            if tf_c3.button(p_month, use_container_width=True, key="btn_p_month"):
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
                render_technical_chart(
                    stock_id=pure_stock_id, 
                    timeframe=st.session_state.kline_period, 
                    selected_mas=all_mas, 
                    show_rsi=chk_rsi, 
                    show_macd=chk_macd,
                    show_kd=chk_kd
                )
        else:
            st.warning("⚠️ 技術 K 線圖目前僅支援代號查詢。請在上方輸入框加入股票代號。")

    # ==========================================
    # ==========================================
    # 👑 區塊 1：短中長線三大法人持股變化 (搜尋結果專屬顯示)
    # ==========================================
    # ==========================================
    st.write("---")
    st.subheader("👑 區塊 1：短中長線三大法人持股變化")
    
    if 'my_final_df' in st.session_state:
        df_b1 = st.session_state['my_final_df']
        res_b1 = robust_search_engine(df_b1, search_query)
        
        if not res_b1.empty:
            date_cols = [c for c in res_b1.columns if '持股%' in c or c.isdigit()]
            
            # 🔥 判斷是否整排全部都是 "未進榜"
            is_all_unranked = True
            for c in date_cols:
                val = str(res_b1.iloc[0][c]).strip()
                if val != "未進榜" and val not in ['0', '0.0', 'nan', '-']:
                    is_all_unranked = False
                    break
                    
            if is_all_unranked:
                # 只要全部都是未進榜，就連圖表都不畫了，乾淨俐落！
                st.write("未進榜")
            else:
                # 有真實數據，印出乾淨的表格
                st.dataframe(res_b1, use_container_width=True, hide_index=True)
                
                # 📊 繪製持股波段軌跡圖
                row = res_b1.iloc[0]
                stock_name = row.get('股票名稱', search_query)
                
                raw_x_vals = date_cols[::-1]
                
                # 🔥 【修正】：把 '20260522持股%' 去除文字並只取最後 4 碼 (0522)
                clean_x_labels = [c.replace('持股%', '')[-4:] for c in raw_x_vals]
                
                y_vals = []
                for c in raw_x_vals:
                    val = row[c]
                    if str(val) == "未進榜" or pd.isna(val):
                        y_vals.append(0.0)
                    else:
                        try:
                            y_vals.append(float(val))
                        except:
                            y_vals.append(0.0)
                            
                import plotly.graph_objects as go
                fig_b1 = go.Figure()
                fig_b1.add_trace(go.Bar(
                    x=clean_x_labels, y=y_vals,  # 👈 這裡換成乾淨的 X 軸標籤
                    marker_color=['#FF4B4B' if i == len(y_vals)-1 else '#4B8BFF' for i in range(len(y_vals))],
                    text=[f"{v}%" if v > 0 else "" for v in y_vals], # 只有大於0的柱子才顯示數字
                    textposition='outside'
                ))
                fig_b1.update_layout(
                    title=f"📈 持股波段真實軌跡 ({stock_name})",
                    height=300,
                    template='plotly_dark',
                    margin=dict(l=20, r=20, t=40, b=20),
                    yaxis=dict(title="持股比例 (%)", showgrid=True, gridcolor='#2D3748'),
                    xaxis=dict(tickangle=45),
                    dragmode='pan'
                )
                st.plotly_chart(fig_b1, use_container_width=True, config={'displayModeBar': False})
        else:
            st.write("未進榜")
    else:
        st.info("⚪ 尚未載入資料表")

    # ==========================================
    # 📊 區塊 2：動能與外資診斷
    # ==========================================
    st.write("---")
    st.write("#### 🎯 區塊 2：法人買超診斷")
    c1, c2 = st.columns(2)
    with c1: scan_and_display("🌐區塊 2-1:外資5日淨買佔標的成交量", 'df_blk2_1', search_query)
    with c2: scan_and_display("🌐區塊 2-2:投信5日淨買佔標的成交量", 'df_blk2_2', search_query)
    c3, c4 = st.columns(2)
    with c3: scan_and_display("🌐區塊 2-3:外資5日淨買佔公司發行量", 'df_blk2_3', search_query)
    with c4: scan_and_display("🏦區塊 2-4:投信5日淨買佔公司發行量", 'df_blk2_4', search_query)

    # ==========================================
    # 📊 區塊 3： (4 榜全景)
    # ==========================================
    st.write("---")
    st.subheader("📅 區塊 3：法人連買診斷(日、週)")
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
                
        final_b3_display = pd.DataFrame(display_list)
        st.dataframe(final_b3_display, use_container_width=True, hide_index=True)
    else:
        st.info("⚪ 區塊 3：尚未載入資料表 (請確認上半部區塊已執行)")


    # ==========================================
    # 📊 區塊 4：籌碼變動排名診斷 (三榜全景 + 強制去小數點)
    # ==========================================
    st.write("---")
    st.write("#### 🔄 區塊 4：券資有利排名")
    
    def render_b4_panorama(view_title, keys_and_labels, query):
        display_list = []
        display_id = query
        display_name = "-"
        
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
                    new_row = {'榜單類型': label}
                    new_row.update(row_data)
                    display_list.append(new_row)
                else:
                    display_list.append({'榜單類型': label, '股票代號': display_id, '股票名稱': display_name, '進榜狀態': '⚪ 未進榜'})
            else:
                display_list.append({'榜單類型': label, '股票代號': display_id, '股票名稱': display_name, '進榜狀態': '⚠️ 尚未載入'})
                
        df_panorama = pd.DataFrame(display_list).fillna('-')
        
        front_cols = ['榜單類型', '股票代號', '股票名稱', '進榜狀態']
        data_cols = [c for c in df_panorama.columns if c not in front_cols]
        final_cols = [c for c in front_cols if c in df_panorama.columns] + data_cols
        
        # 🔥 【神級修正】：強制將以 '.0' 結尾的數值轉為整數字串 (消除 190.0 的現象)
        for c in final_cols:
            df_panorama[c] = df_panorama[c].apply(lambda x: str(x)[:-2] if str(x).endswith('.0') else x)
        
        st.markdown(f"##### {view_title}")
        st.dataframe(df_panorama[final_cols], use_container_width=True, hide_index=True)

    render_b4_panorama("5日幅度變動排名", [('📉 融資減少', 'df_margin_pct'), ('📉 借券減少', 'df_short_pct'), ('📈 融券增加', 'df_margin_plus_pct')], search_query)
    st.write("") 
    render_b4_panorama("5日張數變動排名", [('📉 融資減少', 'df_margin_vol'), ('📉 借券減少', 'df_short_vol'), ('📈 融券增加', 'df_margin_plus_vol')], search_query)

    # ==========================================
    # 💎 區塊 5：大戶動向
    # ==========================================
    st.write("---")
    st.subheader("💰 區塊 5：大戶動向診斷") # 👈 將原本的 st.write("#### ...") 統一改為 st.subheader
    scan_and_display("400張以上大戶動向", 'df_blk5', search_query)

    
# ==========================================
# 🧭 側邊欄導航 (無感互動+休市備援版)
# ==========================================
# ------------------------------------------
# 1. 大盤籌碼導航總覽引擎 (Google Sheets 看門狗極速版)
# ------------------------------------------
def render_sidebar_market_summary():
    """自動連線證交所，搭載看門狗機制，已存雲端的資料絕不重複爬取，達成 0.1 秒極速載入"""
    import datetime
    import pandas as pd
    import streamlit as st
    import re
    import requests
    from bs4 import BeautifulSoup
    
    global conn, SHEET_URL
    st.sidebar.markdown("<h2 style='margin-top: 0; margin-bottom: 5px;'>📊 大盤資金風向球</h2>", unsafe_allow_html=True)

    # 🐶 =========================================
    # 🐶 看門狗機制 (Database-First 偵測)
    # 🐶 =========================================
    now = datetime.datetime.now()
    today_str = now.strftime("%Y%m%d")
    need_crawl = True # 預設要爬蟲
    gs_backup = pd.DataFrame()
    
    try:
        gs_backup = conn.read(spreadsheet=SHEET_URL, worksheet="大盤風向球").dropna(how="all")
        if not gs_backup.empty and '日期' in gs_backup.columns:
            gs_latest_date = str(gs_backup['日期'].iloc[-1]).replace('.0', '')
            
            if now.weekday() >= 5: 
                need_crawl = False # 週末：不爬蟲
            elif now.time() < datetime.time(14, 50):
                need_crawl = False # 平日15:00前(抓14:50緩衝)：今日資料未出，不爬蟲
            elif gs_latest_date == today_str:
                need_crawl = False # 平日15:00後：檢查雲端，如果今天已經抓過，不爬蟲！
    except Exception as e:
        pass # 若雲端連線異常，強制放行爬蟲去抓資料

    # ------------------------------------------
    # A. 數據採集 (看門狗放行才會執行)
    # ------------------------------------------
    twse_title, twse_df = None, None
    margin_today, margin_prev = None, None
    date_key = None
    oi_data = {"外資": 0, "投信": 0, "自營商": 0}
    
    if need_crawl:
        twse_title, twse_df = fetch_twse_institutional_data()
        if twse_df is not None and not twse_df.empty:
            date_match = re.search(r'(\d+)年(\d+)月(\d+)日', str(twse_title))
            if date_match:
                date_key = f"{int(date_match.group(1))+1911}{int(date_match.group(2)):02d}{int(date_match.group(3)):02d}"
                
            try: # 融資爬蟲
                res_margin = requests.get("https://www.twse.com.tw/rwd/zh/margin/MI_MARGN?response=json&selectType=MS", timeout=5)
                if res_margin.status_code == 200:
                    m_data = res_margin.json().get("data", []) if "data" in res_margin.json() else res_margin.json().get("tables", [{}])[0].get("data", [])
                    for row in m_data:
                        if row and len(row) >= 6 and "融資" in str(row[0]):
                            margin_prev = float(str(row[4]).replace(',', '').strip())
                            margin_today = float(str(row[5]).replace(',', '').strip())
                            break
            except: pass

            try: # 選擇權/期貨未平倉爬蟲
                query_date = f"{int(date_key[:4])}/{date_key[4:6]}/{date_key[6:8]}" if date_key else now.strftime("%Y/%m/%d")
                res_oi = requests.post("https://www.taifex.com.tw/cht/3/futContractsDate", data={'queryDate': query_date}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                if res_oi.status_code == 200:
                    for row in BeautifulSoup(res_oi.text, 'html.parser').find_all('tr'):
                        texts = [td.get_text(strip=True) for td in row.find_all('td')]
                        if not texts or len(texts) < 10: continue
                        if "臺股期貨" in texts:
                            identity = "外資" if "外資" in texts else "投信" if "投信" in texts else "自營商" if "自營商" in texts else None
                            if identity: oi_data[identity] = int(texts[-2].replace(',', ''))
            except: pass

    # ------------------------------------------
    # B. 資料彙整與呈現
    # ------------------------------------------
    net_buy_foreign = 0.0; net_buy_trust = 0.0; net_buy_dealer = 0.0; net_buy_total = 0.0
    total_oi = 0; margin_diff_yi = 0.0; margin_today_yi = 0.0
    date_str = "未知日期"
    is_weekend_mode = False

    if twse_df is not None and not twse_df.empty:
        # ✅ 看門狗放行且抓到新資料，進行運算並寫入雲端
        for _, row in twse_df.iterrows():
            unit_name = str(row['單位名稱']).strip()
            try: net_val = float(str(row['買賣差額']).replace(',', '')) / 100000000
            except: net_val = 0.0
            
            if unit_name in ['外資及陸資(不含外資自營商)', '外資自營商']: net_buy_foreign += net_val
            elif unit_name == '投信': net_buy_trust += net_val
            elif unit_name in ['自營商(自行買賣)', '自營商(避險)']: net_buy_dealer += net_val
            elif unit_name == '合計': net_buy_total = net_val
            
        total_oi = sum(oi_data.values())
        if margin_today and margin_prev:
            margin_today_yi = margin_today / 100000
            margin_diff_yi = margin_today_yi - (margin_prev / 100000)

        date_str = date_key if date_key else today_str
        
        # 寫入雲端
        today_record = {
            "日期": str(date_str), "外資現貨": round(net_buy_foreign, 2), "投信現貨": round(net_buy_trust, 2),
            "自營商現貨": round(net_buy_dealer, 2), "合計現貨": round(net_buy_total, 2),
            "外資OI": oi_data.get('外資', 0), "投信OI": oi_data.get('投信', 0),
            "自營商OI": oi_data.get('自營商', 0), "合計OI": total_oi,
            "融資增減": round(margin_diff_yi, 2), "融資餘額": round(margin_today_yi, 2)
        }
        try:
            today_df = pd.DataFrame([today_record])
            if not gs_backup.empty and '日期' in gs_backup.columns:
                gs_backup = gs_backup[gs_backup['日期'].astype(str) != str(date_str)]
            conn.update(spreadsheet=SHEET_URL, worksheet="大盤風向球", data=pd.concat([gs_backup, today_df], ignore_index=True) if not gs_backup.empty else today_df)
        except: pass

    else:
        # ⚡ 極速讀取模式 (看門狗攔截爬蟲，直接載入雲端)
        is_weekend_mode = True
        if not gs_backup.empty:
            last_record = gs_backup.iloc[-1]
            date_str = str(last_record.get('日期', '未知日期')).replace('.0', '')
            net_buy_foreign = float(last_record.get('外資現貨', 0))
            net_buy_trust = float(last_record.get('投信現貨', 0))
            net_buy_dealer = float(last_record.get('自營商現貨', 0))
            net_buy_total = float(last_record.get('合計現貨', 0))
            oi_data['外資'] = int(last_record.get('外資OI', 0))
            oi_data['投信'] = int(last_record.get('投信OI', 0))
            oi_data['自營商'] = int(last_record.get('自營商OI', 0))
            total_oi = int(last_record.get('合計OI', 0))
            margin_diff_yi = float(last_record.get('融資增減', 0))
            margin_today_yi = float(last_record.get('融資餘額', 0))

    # ------------------------------------------
    # C. UI 排版視覺化渲染
    # ------------------------------------------
    if date_str != "未知日期":
        if is_weekend_mode and need_crawl == False and now.time() >= datetime.time(14, 50):
            status_badge = "⚡ <span style='color:#00E272;'>雲端極速載入</span>"
        else:
            status_badge = "🌕 <span style='color:#00D2FF;'>雲端同步版</span>" if is_weekend_mode else "🌕 <span style='color:#00E272;'>即時更新版</span>"

        def get_cls(val): return '#FF4B4B' if val > 0 else '#00CC66' if val < 0 else 'white'
        def get_sign(val): return f"+{val:.1f}" if val > 0 else f"{val:.1f}"
        def get_oi_str(val): return "0" if val == 0 else f"+{val:,}" if val > 0 else f"{val:,}"

        html_lines = [
            f"<div style='background-color: #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 10px;'>",
            f"<div style='font-size: 13px; color: #00D2FF; margin-bottom: 8px;'>📅 {date_str} | {status_badge}</div>",
            f"<table style='width:100%; border-collapse: collapse; table-layout: fixed; font-size: 14px; color: white;'>",
            f"<tr style='border-bottom: 1px solid #334155; font-weight: bold;'><td style='padding: 4px 0; width: 28%;'>法人</td><td style='padding: 4px 0; text-align: right; width: 36%;'>現貨(億)</td><td style='padding: 4px 0; text-align: right; width: 36%;'>TX未平倉</td></tr>",
            f"<tr><td style='padding: 6px 0;'>🌐 外資</td><td style='text-align: right; color: {get_cls(net_buy_foreign)}; font-weight: bold;'>{get_sign(net_buy_foreign)}</td><td style='text-align: right; color: {get_cls(oi_data.get('外資',0))}; font-weight: bold;'>{get_oi_str(oi_data.get('外資',0))}</td></tr>",
            f"<tr><td style='padding: 6px 0;'>🏦 投信</td><td style='text-align: right; color: {get_cls(net_buy_trust)}; font-weight: bold;'>{get_sign(net_buy_trust)}</td><td style='text-align: right; color: {get_cls(oi_data.get('投信',0))}; font-weight: bold;'>{get_oi_str(oi_data.get('投信',0))}</td></tr>",
            f"<tr><td style='padding: 6px 0;'>🏢 自營商</td><td style='text-align: right; color: {get_cls(net_buy_dealer)}; font-weight: bold;'>{get_sign(net_buy_dealer)}</td><td style='text-align: right; color: {get_cls(oi_data.get('自營商',0))}; font-weight: bold;'>{get_oi_str(oi_data.get('自營商',0))}</td></tr>",
            f"<tr style='border-top: 1px solid #334155;'><td style='padding: 6px 0; color: #FFD700; font-weight: bold;'>🔥 合計</td><td style='text-align: right; color: {get_cls(net_buy_total)}; font-weight: bold;'>{get_sign(net_buy_total)}</td><td style='text-align: right; color: {get_cls(total_oi)}; font-weight: bold;'>{get_oi_str(total_oi)}</td></tr>"
        ]

        if margin_diff_yi != 0 or margin_today_yi != 0:
            html_lines.append(f"<tr style='border-top: 1px dashed #334155;'><td style='padding: 8px 0 2px 0; color: white; font-weight: bold;' colspan='2'>📊 融資餘額增減(億)</td><td style='padding: 8px 0 2px 0; text-align: right; color: {get_cls(margin_diff_yi)}; font-weight: bold;'>{get_sign(margin_diff_yi)}</td></tr>")
            html_lines.append(f"<tr><td style='padding: 1px 0 4px 0; font-size: 12px; color: #94A3B8; font-weight: normal;' colspan='2'>└ 今日融資總餘額</td><td style='padding: 1px 0 4px 0; text-align: right; color: #94A3B8; font-size: 12px; font-weight: normal;'>{margin_today_yi:.1f}</td></tr>")

        html_lines.append("</table></div>")
        st.sidebar.markdown("".join(html_lines), unsafe_allow_html=True)
    else:
        st.sidebar.info("🕒 目前查無今日三大法人買賣資料。")



# 執行渲染側邊欄大盤卡片
render_sidebar_market_summary()

# ------------------------------------------
# 2. 大盤總體經濟指標
# ------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📊 大盤總體經濟指標")

c_btn1, c_btn2 = st.sidebar.columns(2)
with c_btn1:
    st.link_button("📈 恐懼貪婪", "https://www.wantgoo.com/global/macroeconomics/fearandgreed", use_container_width=True)
with c_btn2:
    st.link_button("⚠️ VIX 指數", "https://www.wantgoo.com/global/vix", use_container_width=True)

# ------------------------------------------
# 3. 戰情室快速導航
# ------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📍 戰情室快速導航")
st.sidebar.markdown("[🏆 數據分析觀察名單](#section-top-pool)")
st.sidebar.markdown("[🔍 個股籌碼快搜 (診斷區)](#section-search)")
st.sidebar.markdown("[👑 區塊1：三大法人持股比追蹤](#section-1)")
st.sidebar.markdown("[🎯 區塊2-1：外資5日淨買佔成交量](#section-2-1)")
st.sidebar.markdown("[🎯 區塊2-2：投信5日淨買佔成交量](#section-2-2)")
st.sidebar.markdown("[🎯 區塊2-3：外資5日淨買佔發行量](#section-2-3)")
st.sidebar.markdown("[🎯 區塊2-4：投信5日淨買佔發行量](#section-2-4)")
st.sidebar.markdown("[📅 區塊3：法人連續買超](#section-3)")
st.sidebar.markdown("[🔄 區塊4-1：融資減少動向](#section-4-1)")
st.sidebar.markdown("[🔄 區塊4-2：借券賣出減少動向](#section-4-2)")
st.sidebar.markdown("[🔄 區塊4-3：融券增加動向](#section-4-3)")
st.sidebar.markdown("[💰 區塊5：大股東動向](#section-5)")
st.sidebar.markdown("[💸 區塊6：鉅額交易動向](#section-6)")
# ==========================================
# 🏠 核心五大區塊
# ==========================================

# ==========================================
# 🏠 區塊1：中長線 三大法人 持股比例 追蹤 (量化動態升級+暗黑專業版)
# ==========================================
st.write("---")
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)
st.header("👑 區塊1：三大法人短中長線持股比追蹤")

import re
import os
import glob
import pandas as pd
from collections import defaultdict

# 1. 解析引擎 (嚴格依賴分隔線)
def parse_special_txt(file_path, date_label):
    parsed_data = []
    target_col = f"{date_label}持股%"
    current_section = None
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line_str = line.strip()
                
                # 🛑 【絕對斷路器】：只要遇到分隔線，立刻清空狀態
                if line_str.startswith("---") or line_str.startswith("==="):
                    current_section = None
                    continue
                
                # 💡 【區塊開關】：讀到對應標題才開啟
                if "三大法人持股變化排名" in line_str or ("排名" in line_str and "日)" in line_str):
                    if "120日" in line_str: current_section = "120日"
                    elif "20日" in line_str: current_section = "20日"
                    elif "5日" in line_str: current_section = "5日"
                    elif "60日" in line_str: current_section = "60日"
                    continue
                
                # 抓取資料
                parts = line_str.split('\t')
                if current_section and len(parts) >= 5 and parts[0].isdigit():
                    try: holding_pct = float(parts[-2])
                    except ValueError: continue
                    
                    stock_str = parts[1].strip()  
                    m = re.match(r'^(\d+)(.*)', stock_str)
                    stock_id = m.group(1) if m else stock_str
                    stock_name = m.group(2).strip() if m else stock_str
                    
                    parsed_data.append({
                        '股票代號': stock_id,
                        '股票名稱': stock_name,
                        target_col: holding_pct,
                        '上榜區塊': current_section
                    })
    except Exception:
        pass
    return pd.DataFrame(parsed_data)

# 聚合相同標的的不同榜單標籤
def agg_sections_func(x):
    valid_x = set([s for s in x if pd.notna(s) and s != ""])
    order = ['5日', '20日', '60日', '120日']
    return ",".join([s for s in order if s in valid_x])

# ==========================================
# 🔄 多日歷史資料合併與邏輯運算
# ==========================================
txt_pattern = os.path.join(DATA_DIR, "*持股排名變化*.txt")
all_txt_files = glob.glob(txt_pattern)

date_files = defaultdict(list)
for f in all_txt_files:
    date_label = os.path.basename(f)[:8]
    if date_label.isdigit():
        date_files[date_label].append(f)

sorted_dates = sorted(date_files.keys(), reverse=True)

if sorted_dates:
    # 👇 新增：自動抓取最新日期並格式化 (例如 20260526 變成 2026/05/26)
    latest_d = sorted_dates[0]
    fmt_date = f"{latest_d[:4]}/{latest_d[4:6]}/{latest_d[6:]}"
    st.markdown(f"<span style='color:#00D2FF; font-size:14px; font-weight:500;'>最新數據：{fmt_date}</span>", unsafe_allow_html=True)
    
    final_df = None  # (這行是原本就有的，保留在下面)
    final_df = None
    
    for i, date_label in enumerate(sorted_dates[:30]):
        is_latest = (i == 0)
        day_dfs = []
        
        for file_path in date_files[date_label]:
            df_part = parse_special_txt(file_path, date_label)
            if not df_part.empty:
                day_dfs.append(df_part)
                
        if not day_dfs: continue
            
        df_day_raw = pd.concat(day_dfs, ignore_index=True)
        target_col = f"{date_label}持股%"
        
        # 🔥 【邏輯重構】：歷史每一天的上榜榜單全部予以保留，以便比對「洗盤回歸」與「衝進榜單」
        df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg({
            target_col: 'max',  
            '上榜區塊': agg_sections_func
        }).reset_index()
        
        # 將上榜區塊重新命名以區分日期
        df_day = df_day.rename(columns={'上榜區塊': f"{date_label}_區塊"})
            
        if final_df is None: 
            final_df = df_day
        else: 
            final_df = pd.merge(final_df, df_day, on=['股票代號', '股票名稱'], how='outer')
            
    if final_df is not None and not final_df.empty:
        date_cols = sorted([c for c in final_df.columns if '持股%' in c], reverse=True)
        for c in date_cols:
            final_df[c] = pd.to_numeric(final_df[c], errors='coerce').fillna(0)
            
        # 今日上榜欄位標籤化
        def generate_tags(sections):
            if pd.isna(sections) or not sections: return ""
            sec_list = str(sections).split(',')
            tags = []
            if '5日' in sec_list: tags.append('🔴5日')
            if '20日' in sec_list: tags.append('🟡20日')
            if '60日' in sec_list: tags.append('🟢60日')
            if '120日' in sec_list: tags.append('🔵120日')
            return " ".join(tags)
            
        latest_sect_col = f"{sorted_dates[0]}_區塊"
        if latest_sect_col not in final_df.columns:
            final_df[latest_sect_col] = ""
            
        final_df['今日上榜'] = final_df[latest_sect_col].apply(generate_tags)
        final_df['上榜數量'] = final_df['今日上榜'].apply(lambda x: str(x).count('日'))
            
        # 🧠 量化動態判定邏輯核心 (多重訊號疊加 + 高級吸籌型態)
        def evaluate_trend(row):
            if len(date_cols) < 2: return "⚪ 資料不足"
            
            dynamics = []
            v0, v1 = row[date_cols[0]], row[date_cols[1]]
            
            # --- 1. 基礎趨勢與高級吸籌型態判定 ---
            diff1 = v0 - v1  
            if diff1 > 0:
                is_slowing = False
                if len(date_cols) >= 3:
                    v2 = row[date_cols[2]]
                    
                    # 【階梯吸籌】：連三日嚴格遞增 (v0 > v1 > v2)
                    if v0 > v1 > v2 > 0:
                        dynamics.append("🪜 階梯吸籌")
                    else:
                        # 【穩健吸籌】：連四日不減碼，且整體有增加
                        if len(date_cols) >= 4:
                            v3 = row[date_cols[3]]
                            if v0 >= v1 >= v2 >= v3 > 0 and v0 > v3:
                                dynamics.append("🛡️ 穩健吸籌")
                                
                    # 趨緩判定
                    if v1 != 0 and v2 != 0:
                        diff2 = v1 - v2
                        if diff2 > 0 and diff1 < diff2:
                            dynamics.append("⚠️ 趨緩")
                            is_slowing = True
                            
                # 若沒有被判定為趨緩，則加上基礎上升標籤
                if not is_slowing:
                    dynamics.append("📈 上升")
                    
            elif diff1 < 0: 
                dynamics.append("📉 下降")
            else: 
                dynamics.append("🔄 持平")
                
            # --- 2. 特殊籌碼事件判定 (洗盤與衝進) ---
            today_sec_str = str(row.get(f"{sorted_dates[0]}_區塊", ""))
            yesterday_sec_str = str(row.get(f"{sorted_dates[1]}_區塊", ""))
            
            today_list = [s for s in today_sec_str.split(',') if s]
            yesterday_list = [s for s in yesterday_sec_str.split(',') if s]
            
            # 🔍 【洗盤回歸】
            if v0 > 0 and v1 == 0:
                has_past_record = False
                for c in date_cols[2:]:
                    if row[c] > 0:
                        has_past_record = True
                        break
                if has_past_record:
                    dynamics.append("🔄 洗盤回歸")
            
            # 🚀 【衝進新榜單】
            if 1 <= len(yesterday_list) <= 3 and len(today_list) > len(yesterday_list):
                new_entries = [item for item in today_list if item not in yesterday_list]
                if new_entries:
                    mapped_labels = []
                    for item in new_entries:
                        if '5日' in item: mapped_labels.append('🔴5日')
                        elif '20日' in item: mapped_labels.append('🟡20日')
                        elif '60日' in item: mapped_labels.append('🟢60日')
                        elif '120日' in item: mapped_labels.append('🔵120日')
                    if mapped_labels:
                        dynamics.append(f"🚀 衝進{'、'.join(mapped_labels)}榜單")
            
            return " | ".join(dynamics)
            
            # 3. 常規趨勢判定
            diff1 = v0 - v1  
            if diff1 > 0:
                if len(date_cols) >= 3:
                    v2 = row[date_cols[2]]
                    if v1 != 0 and v2 != 0:
                        diff2 = v1 - v2
                        if diff2 > 0 and diff1 < diff2: return "⚠️ 趨緩"
                return "📈 上升"
            elif diff1 < 0: 
                return "📉 下降"
            else: 
                return "🔄 持平"
                
        final_df['最新動態'] = final_df.apply(evaluate_trend, axis=1)
        
        if date_cols:
            final_df = final_df.sort_values(by=['上榜數量', date_cols[0]], ascending=[False, False])
            
        color_ref = final_df.set_index('股票代號')['上榜數量'].to_dict()
        cols = ['股票代號', '股票名稱', '今日上榜', '最新動態'] + date_cols
        final_df = final_df[cols]
        
        # ==========================================
        # 🧹 源頭數據清洗：強制鎖死小數點兩位，並將 0 替換為 "未進榜"
        # ==========================================
        if not final_df.empty:
            import pandas as pd
            # 抓出所有可能是歷史持股%的欄位
            clean_cols = [c for c in final_df.columns if '持股%' in c or c.isdigit()]
            
            for col in clean_cols:
                # 1. 確保全部轉為數字，無法轉換的會變成空值 NaN
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
                
                # 🔥 2. 核心清洗：鎖死小數點後 2 位，徹底阻絕系統自動亂加 0
                final_df[col] = final_df[col].apply(
                    lambda x: "未進榜" if pd.isna(x) or abs(x) < 0.0001 else f"{x:.2f}"
                )

        # ==========================================
        # 🔧 UI 顯示與過濾 (保留勾選框，隱藏文字)
        # ==========================================
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="blk1_etf_sync")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="blk1_bond_sync")
        
        is_bond = final_df['股票代號'].str.endswith('B')
        is_etf = (final_df['股票代號'].str.len() >= 5) & (~is_bond)
        is_stock = final_df['股票代號'].str.len() == 4
        
        mask = is_stock
        if show_etf: mask |= is_etf
        if show_bond: mask |= is_bond
            
        filtered_df = final_df[mask].copy()
        
        # 🎨 暗黑專業版高亮色系設定
        def highlight_row(row):
            cnt = color_ref.get(row['股票代號'], 0)
            if cnt == 4: bg = 'background-color: rgba(240, 90, 90, 0.25)'     
            elif cnt == 3: bg = 'background-color: rgba(255, 165, 0, 0.25)'    
            elif cnt == 2: bg = 'background-color: rgba(80, 200, 120, 0.25)'    
            elif cnt == 1: bg = 'background-color: rgba(0, 127, 255, 0.25)'    
            else: bg = 'background-color: #111622; color: #E2E8F0'                                                                         
            return [bg] * len(row)

        styled_df = filtered_df.style.apply(highlight_row, axis=1)
        
        # 1. 先顯示表格 (資料優先)
        st.dataframe(styled_df, use_container_width=True)
        
        # 2. 下方再顯示補充說明與狀態訊息
        st.info("今日上榜：代表法人持股變化數據分析後於5/20/60/120日前段班，多榜單共振籌碼集中度高，長線具備底氣。")
        st.success(f"已成功串聯歷史的持股數據 (今日上榜共振數量排序優先)")
        
        # 將資料存入 session
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

# 🛠️ 【不可省略】欄位清理與過濾函數
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

    # 📊 核心機制：自動尋找「漲跌」相關欄位，進行優化排序
    sort_col = next((c for c in df.columns if '漲跌' in str(c)), None)
    if sort_col:
        df[sort_col] = pd.to_numeric(df[sort_col], errors='coerce').fillna(0)
        # 排序：漲幅/漲跌價大的（正值）絕對優先排在前面
        df = df.sort_values(by=sort_col, ascending=False)

    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

# 🎨 核心渲染引擎：實現上漲整欄改紅，平盤下跌維持原樣
def render_styled_margin_table(clean_df):
    if clean_df.empty:
        st.warning("⚠️ 無相符資料")
        return

    # 尋找關鍵的漲跌欄位
    change_col = next((c for c in clean_df.columns if '漲跌' in str(c)), None)
    
    def style_row_by_price(row):
        styles = [''] * len(row)
        if change_col:
            try:
                val = float(str(row[change_col]).replace(',', ''))
                if val > 0:
                    # 🚀 強勢軋空股：整列文字改為顯目紅色，並加粗體
                    return ['color: #FF4B4B; font-weight: bold;'] * len(row)
            except:
                pass
        return styles

    styled_df = clean_df.style.apply(style_row_by_price, axis=1)
    
    # 📐 欄位寬度最佳化配置：強行鎖定股票名稱寬度，完美讓右側當日數據浮現
    col_config = {
        "股票代號": st.column_config.TextColumn("股票代號", width=70),
        "股票名稱": st.column_config.TextColumn("股票名稱", width=95)
    }
    
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True,
        column_config=col_config
    )

# 🕒 輔助函數：提早解析日期供大表頭使用
def peek_data_date(keyword):
    import re
    _, msg = get_specific_margin_data(keyword)
    return re.search(r'\d{8}', msg).group(0) if re.search(r'\d{8}', msg) else "未知"

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
# 💰 區塊 5：大股東動向 (日期去重與去西元修復版)
# ==========================================
import re
import os
import glob
import pandas as pd

csv_pattern_b5 = os.path.join(DATA_DIR, "*神秘金字塔 - 股權類股排行(5日之400張以上股東排行)*.csv")
all_files_b5 = glob.glob(csv_pattern_b5)

if not all_files_b5:
    # 找不到檔案時，維持顯示基本標題
    st.write("---")
    st.markdown("<div id='section-5'></div>", unsafe_allow_html=True)
    st.markdown("## 💰 區塊 5：大股東動向", unsafe_allow_html=True)
    st.write("💡 400張以上大股東週更新資訊。")
    st.warning("⚠️ 找不到相關 CSV 檔案。")
else:
    # 依照檔名排序，確保最新的檔案在最前面
    all_files_b5 = sorted(all_files_b5, key=os.path.basename, reverse=True)
    
    master_df = None
    all_date_cols = set()

    # 1. 遍歷所有檔案並合併
    for idx, file in enumerate(all_files_b5):
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            df.columns = [str(c).strip() for c in df.columns]
            
            # 【核心修復 1】：即時偵測並刪除欄位名稱開頭的 "2026"
            standardized_cols = []
            for c in df.columns:
                if re.match(r'^2026\d{4}$', c):  # 如果是 2026XXXX 格式
                    standardized_cols.append(c[-4:])  # 只取後方 4 碼 XXXX
                else:
                    standardized_cols.append(c)
            df.columns = standardized_cols
            
            # 【核心修復 2】：刪除單檔內部可能重複的相同日期欄位
            df = df.loc[:, ~df.columns.duplicated()]
            
            # 分離代號與名稱
            if '股票代號/名稱' in df.columns:
                df['股票代號'] = df['股票代號/名稱'].astype(str).str.extract(r'(\d+)')
                df['股票名稱'] = df['股票代號/名稱'].astype(str).str.replace(r'^\d+', '', regex=True)
            
            if '股票代號' not in df.columns:
                continue
                
            # 抓取已被標準化為 4 碼的日期欄位
            date_cols = [c for c in df.columns if re.match(r'^\d{4}$', c)]
            all_date_cols.update(date_cols)
            
            # 決定保留的欄位
            cols_to_keep = ['股票代號', '股票名稱'] + date_cols
            
            # 只有在讀取最新檔案 (idx == 0) 時，才把「上週持有%」抓進來
            if idx == 0 and '上週持有%' in df.columns:
                cols_to_keep.append('上週持有%')
            
            cols_to_keep = [c for c in cols_to_keep if c in df.columns]
            temp_df = df[cols_to_keep].copy()
            
            # 設定索引進行智慧拼接
            temp_df = temp_df.set_index(['股票代號', '股票名稱'])
            
            if master_df is None:
                master_df = temp_df
            else:
                # 智慧拼接歷史資料
                master_df = master_df.combine_first(temp_df)
        except Exception:
            continue

    if master_df is not None:
        master_df = master_df.reset_index()
        
        # 2. 排序日期欄位 (皆已轉為4碼，可直接降冪排序，越新越前面)
        sorted_dates = sorted(list(all_date_cols), reverse=True)
        
        # 🔥 【修改點 1】：在這裡抓出最新日期，並印出帶有樣式的標題
        latest_date = sorted_dates[0] if sorted_dates else "無資料"
        
        st.write("---")
        st.markdown("<div id='section-5'></div>", unsafe_allow_html=True)
        st.markdown(f"## 💰 區塊 5：大股東動向 <span style='font-size: 0.5em; color: #00D2FF;'>({latest_date})</span>", unsafe_allow_html=True)
        st.write("💡 400張以上大股東週更新資訊。")
        
        # 3. 計算週動態
        if len(sorted_dates) >= 2:
            newest, prev = sorted_dates[0], sorted_dates[1]
            master_df[newest] = pd.to_numeric(master_df[newest], errors='coerce')
            master_df[prev] = pd.to_numeric(master_df[prev], errors='coerce')
            
            def get_trend(row):
                v1, v2 = row.get(newest), row.get(prev)
                if pd.isna(v1) or pd.isna(v2): return "無資料"
                diff = v1 - v2
                if diff >= 1.5: return "🔥 大增"
                if diff >= 0.5: return "📈 增"
                if diff > 0: return "↗️ 微增"
                if diff == 0: return "🔄 持平"
                if diff > -0.5: return "↘️ 微減"
                if diff > -1.5: return "📉 減"
                return "🚨 大減"
            
            master_df['週動態'] = master_df.apply(get_trend, axis=1)
        else:
            master_df['週動態'] = "無資料"

        # 4. 整理最終欄位順序：代號、名稱、週動態、上週持有%、所有日期(新到舊)
        final_cols = ['股票代號', '股票名稱', '週動態']
        if '上週持有%' in master_df.columns:
            final_cols.append('上週持有%')
        final_cols.extend(sorted_dates)
        
        final_df = master_df[[c for c in final_cols if c in master_df.columns]].copy()
        
        # 5. 排序表單：以最新日期做為置頂降冪排序依據
        if sorted_dates:
            final_df = final_df.sort_values(by=sorted_dates[0], ascending=False)
        
        # 6. 清理小數點與空值 (安全去除 .0 尾數)
        def clean_decimals(val):
            if pd.isna(val): return "無資料"
            s = str(val).strip()
            if s.endswith('.0'): return s[:-2]
            return s
            
        for col in sorted_dates:
            final_df[col] = final_df[col].apply(clean_decimals)
        if '上週持有%' in final_df.columns:
            final_df['上週持有%'] = final_df['上週持有%'].apply(clean_decimals)
            
        final_df = final_df.fillna("無資料")
        
        # 🔥 【修改點 2】：表格輸出前，把最新日期的欄位名稱加上 ▼
        if sorted_dates:
            latest_col = sorted_dates[0]
            final_df = final_df.rename(columns={latest_col: f"▼{latest_col}"})
        
        st.dataframe(final_df, use_container_width=True, hide_index=True)
        
        # 將最終結果同步存入記憶體，供搜尋區塊聯動掃描
        st.session_state['df_blk5'] = final_df
    else:
        st.error("無法合併資料。")
# ==========================================
# 💸 區塊 6：盤後鉅額交易總表 (Google Sheets 雲端矩陣版)
# ==========================================
import os, re, datetime
import pandas as pd
import yfinance as yf

# 使用 Streamlit 快取確保效能，避免重複抓取 (記憶 10 分鐘)
@st.cache_data(ttl=600)
def get_historical_block_matrix_from_gs():
    """從 Google Sheets 抓取扁平化歷史資料，並自動重組成帶有顏色的跨日矩陣"""
    try:
        hist_df = conn.read(spreadsheet=SHEET_URL, worksheet="鉅額交易")
        hist_df = hist_df.dropna(how="all")
        if hist_df.empty or '日期' not in hist_df.columns:
            return None, []
            
        # 🎯 修復 29.0 的關鍵：強制去尾數，並補足 8 位數
        hist_df['日期'] = hist_df['日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8)
        hist_df['代號'] = hist_df['代號'].astype(str).str.replace(r'\D', '', regex=True)
        
        date_list = sorted(hist_df['日期'].unique(), reverse=True)
        master_hist_df = None
        date_cols_list = []
        
        for d in date_list:
            short_date = d[-4:] # 現在這裡絕對會是乾淨的 0529 了！
            block_col = f"▼{short_date}成交價"
            close_col = f"{short_date}收盤價"
            date_cols_list.append(block_col)
            
            day_df = hist_df[hist_df['日期'] == d][['代號', '股票名稱', '成交價', '收盤價']].copy()
            day_df = day_df.rename(columns={'成交價': block_col, '收盤價': close_col})
            
            # 若同一天有多筆成交價，將成交價以 / 隔開
            day_df = day_df.groupby(['代號', '股票名稱']).agg({
                block_col: lambda x: ' / '.join(sorted(set(x.astype(str)))),
                close_col: 'first'
            }).reset_index()
            
            if master_hist_df is None:
                master_hist_df = day_df
            else:
                master_hist_df = pd.merge(master_hist_df, day_df, on=['代號', '股票名稱'], how='outer')
                
        master_hist_df = master_hist_df.fillna('-')
        
        # 🔥【自動刪除週末非交易日拷貝】
        cols_to_drop = []
        for i in range(len(date_cols_list) - 1):
            new_col = date_cols_list[i]
            old_col = date_cols_list[i+1]
            if master_hist_df[new_col].equals(master_hist_df[old_col]):
                cols_to_drop.append(new_col)
                cols_to_drop.append(new_col.replace('▼', '').replace('成交價', '收盤價'))
        
        master_hist_df = master_hist_df.drop(columns=[c for c in cols_to_drop if c in master_hist_df.columns])
        date_cols_list = [c for c in date_cols_list if c not in cols_to_drop]
        
        if date_cols_list:
            master_hist_df = master_hist_df.sort_values(by=date_cols_list[0], ascending=False)
            
        return master_hist_df, date_cols_list
    except Exception as e:
        return None, []

# 🎯 雲端對齊：直接抓取大盤日期作為基準
def get_cloud_synced_date():
    try:
        df_market = conn.read(spreadsheet=SHEET_URL, worksheet="大盤風向球")
        if not df_market.empty and '日期' in df_market.columns:
            # 強制轉字串，並把尾數 .0 刪掉
            return str(df_market['日期'].iloc[-1]).replace('.0', '')
    except: pass
    return datetime.datetime.now().strftime("%Y%m%d")

real_trade_date = get_cloud_synced_date() 
date_mmdd = real_trade_date[-4:]         
dynamic_price_col = f"▼{date_mmdd}成交價" 

# 幫日期穿上 2026/05/29 的格式化衣服
if len(real_trade_date) == 8:
    formatted_date = f"{real_trade_date[:4]}/{real_trade_date[4:6]}/{real_trade_date[6:8]}"
else:
    formatted_date = real_trade_date

st.write("---")
st.markdown("<div id='section-6'></div>", unsafe_allow_html=True)
st.markdown(f"### 💸 區塊 6：鉅額交易動向 <span style='font-size: 0.6em; color: #00D2FF;'>({formatted_date})</span>", unsafe_allow_html=True)
st.write("💡 鉅額交易常為大戶私下換手籌碼，成交價可視為「支撐/壓力」防守線；短線跌破建議嚴設停損。")

tab1, tab2 = st.tabs(["🆕 今日最新鉅額交易", "📅 歷史防守價追蹤表"])

# ==========================================
# 資料處理核心：寫入 Google Sheets
# ==========================================
raw_block_df = fetch_block_trades() 
display_df = None
is_weekend = False

if raw_block_df is not None and not raw_block_df.empty:
    try:
        price_col = next((c for c in ['成交價', '成交價格', '成交單價'] if c in raw_block_df.columns), None)
        if price_col:
            raw_block_df['成交股數_數值'] = pd.to_numeric(raw_block_df['成交股數'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            raw_block_df['成交金額_數值'] = pd.to_numeric(raw_block_df['成交金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            raw_block_df[dynamic_price_col] = pd.to_numeric(raw_block_df[price_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).round(0).astype(int)
            raw_block_df = raw_block_df[raw_block_df['成交股數_數值'] > 0].copy()
            raw_block_df['成交張數'] = (raw_block_df['成交股數_數值'] / 1000).astype(int)
            raw_block_df['成交總額(億)'] = (raw_block_df['成交金額_數值'] / 100000000).apply(lambda x: f"{x:.2f}".rstrip('0').rstrip('.'))
            raw_block_df['乾淨代號'] = raw_block_df['證券代號'].astype(str).str.replace(r'\D', '', regex=True)
            
            # --- 抓取收盤價 ---
            close_price_dict = {}
            unique_ids = raw_block_df['乾淨代號'].dropna().unique()
            if len(unique_ids) > 0:
                yf_tickers = " ".join([f"{sid}.TW" for sid in unique_ids])
                try:
                    df_yf = yf.download(yf_tickers, period="5d", progress=False)
                    if not df_yf.empty and 'Close' in df_yf:
                        close_data = df_yf['Close']
                        if len(unique_ids) == 1:
                            price = close_data.dropna().iloc[-1]
                            close_price_dict[unique_ids[0]] = str(int(round(price)))
                        else:
                            for sid in unique_ids:
                                tkr = f"{sid}.TW"
                                if tkr in close_data.columns:
                                    valid_prices = close_data[tkr].dropna()
                                    if not valid_prices.empty: close_price_dict[sid] = str(int(round(valid_prices.iloc[-1])))
                except: pass 
            
            raw_block_df['▼收盤價'] = raw_block_df['乾淨代號'].map(close_price_dict).fillna('-')
            
            def get_color_rank(close_val, block_val):
                try:
                    c = float(str(close_val).replace(',', ''))
                    b = float(str(block_val).replace(',', ''))
                    return 1 if c > b else 2 if c == b else 3       
                except: return 4 
            raw_block_df['__color_rank'] = raw_block_df.apply(lambda r: get_color_rank(r['▼收盤價'], r[dynamic_price_col]), axis=1)
            raw_block_df = raw_block_df.sort_values(by=['__color_rank', '乾淨代號'], ascending=[True, True])
            
            display_df = raw_block_df[['乾淨代號', '證券名稱', dynamic_price_col, '▼收盤價', '成交張數', '成交總額(億)']].copy()
            display_df = display_df.rename(columns={'乾淨代號': '代號', '證券名稱': '股票名稱'})
            
            # 🚀 同步至 Google Sheets
            save_df = display_df.copy()
            save_df.columns = ['代號', '股票名稱', '成交價', '收盤價', '成交張數', '成交總額(億)']
            save_df.insert(0, '日期', real_trade_date)
            
            try:
                old_gs = conn.read(spreadsheet=SHEET_URL, worksheet="鉅額交易")
                old_gs = old_gs.dropna(how="all")
                if '日期' in old_gs.columns:
                    old_gs = old_gs[old_gs['日期'].astype(str) != str(real_trade_date)]
                final_gs = pd.concat([old_gs, save_df], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="鉅額交易", data=final_gs)
            except Exception as e:
                try: conn.update(spreadsheet=SHEET_URL, worksheet="鉅額交易", data=save_df)
                except: pass

    except Exception as e: st.warning(f"⚠️ 資料解析錯誤: {str(e)}")
else:
    is_weekend = True
    try:
        gs_backup = conn.read(spreadsheet=SHEET_URL, worksheet="鉅額交易").dropna(how="all")
        if not gs_backup.empty and '日期' in gs_backup.columns:
            # 🎯 裝上防護罩：把雲端讀下來的 529.0 強制轉字串、去尾數、補足 8 位數
            gs_backup['日期'] = gs_backup['日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8)
            
            latest_date = gs_backup['日期'].max()
            backup_df = gs_backup[gs_backup['日期'] == latest_date].copy()
            short_date = latest_date[-4:] # 這裡就會是乾淨的 0529 了！
            
            backup_df = backup_df.rename(columns={'成交價': f"▼{short_date}成交價", '收盤價': '▼收盤價'})
            display_df = backup_df.drop(columns=['日期'])
    except: pass

# ==========================================
# 渲染 UI
# ==========================================
with tab1:
    if display_df is not None and not display_df.empty:
        # 🎯 已經將「休市期間...」的提示文字刪除
        def highlight_block_row(row):
            styles = [''] * len(row)
            try:
                close_p = float(str(row['▼收盤價']).replace(',', ''))
                target_col = [c for c in row.index if '成交價' in c][0] 
                block_p = float(str(row[target_col]).replace(',', ''))
                color = '#FF4B4B' if close_p > block_p else '#FFA500' if close_p == block_p else '#00E272'
                idx = row.index.get_loc(target_col)
                styles[idx] = f'color: {color}; font-weight: bold;'
            except: pass 
            return styles
            
        styled_df = display_df.style.apply(highlight_block_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else: 
        st.info("🕒 目前查無今日鉅額交易資料，且雲端尚無備份。")

with tab2:
    master_hist_df, date_cols_list = get_historical_block_matrix_from_gs()
    if master_hist_df is not None and not master_hist_df.empty:
        def highlight_history(row):
            styles = [''] * len(row)
            for idx, col in enumerate(row.index):
                if '成交價' in col:
                    date_str = col.replace('▼', '').replace('成交價', '')
                    close_col = f"{date_str}收盤價"
                    if close_col in row.index:
                        block_val, close_val = str(row[col]), str(row[close_col])
                        if block_val != '-' and close_val != '-':
                            try:
                                first_block = float(block_val.split('/')[0].strip())
                                close_p = float(close_val)
                                color = '#FF4B4B' if close_p > first_block else '#FFA500' if close_p == first_block else '#00E272'
                                styles[idx] = f'color: {color}; font-weight: bold;'
                            except: pass
            return styles
            
        styled_hist = master_hist_df.style.apply(highlight_history, axis=1)
        hide_cols = [c for c in master_hist_df.columns if '收盤價' in c]
        styled_hist = styled_hist.hide(subset=hide_cols, axis="columns")
        st.dataframe(styled_hist, use_container_width=True, hide_index=True)
    else: 
        st.info("📂 目前 Google Sheets 尚未累積歷史交易檔案。")

# ==========================================以上網頁核心區塊
# ==========================================
# 🏆 頂級選股池核心引擎 (精確量化權重 + 暗盤連動 + 歷史追蹤分頁)
# ==========================================
with top_pool_container:
    st.write("---")
    st.markdown("<div id='section-top-pool'></div>", unsafe_allow_html=True)
    
    import os
    import glob
    import re
    import json
    import pandas as pd

    # 1. 自動掃描最新資料日期
    txt_pattern = os.path.join(DATA_DIR, "*持股排名變化*.txt") 
    all_txt_files = glob.glob(txt_pattern)
    latest_date_str = "未知日期"

    if all_txt_files:
        latest_file = max(all_txt_files, key=os.path.basename)
        date_label = os.path.basename(latest_file)[:8]
        if date_label.isdigit():
            latest_date_str = f"{date_label[:4]}/{date_label[4:6]}/{date_label[6:]}"

    st.markdown(f"## 🏆 數據分析觀察名單 <span style='font-size:18px; color:#00D2FF; font-weight:500;'>(最新數據: {latest_date_str})</span>", unsafe_allow_html=True)
    st.info("💡 **權重評分**：法人持股上榜搭配其他數據分析積分,請參考短動態。(評分數據僅供參考)")

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

            def get_df_safe(key): return st.session_state.get(key, pd.DataFrame())

            df_b2_1, df_b2_2 = get_df_safe('df_blk2_1'), get_df_safe('df_blk2_2')
            df_b2_3, df_b2_4 = get_df_safe('df_blk2_3'), get_df_safe('df_blk2_4')
            df_b3 = get_df_safe('df_blk3_main')
            
            df_b4_mar_pct, df_b4_mar_vol = get_df_safe('df_margin_pct'), get_df_safe('df_margin_vol')
            df_b4_sho_pct, df_b4_sho_vol = get_df_safe('df_short_pct'), get_df_safe('df_short_vol')
            df_b4_mp_pct, df_b4_mp_vol = get_df_safe('df_margin_plus_pct'), get_df_safe('df_margin_plus_vol')
            
            s_b4_mar_pct, s_b4_mar_vol = set(df_b4_mar_pct.get('股票代號', [])), set(df_b4_mar_vol.get('股票代號', []))
            s_b4_sho_pct, s_b4_sho_vol = set(df_b4_sho_pct.get('股票代號', [])), set(df_b4_sho_vol.get('股票代號', []))
            s_b4_mp_pct, s_b4_mp_vol = set(df_b4_mp_pct.get('股票代號', [])), set(df_b4_mp_vol.get('股票代號', []))
            df_b5 = get_df_safe('df_blk5')

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
                
                if sid in block_sids: b1_dyn = f"{b1_dyn} | 🎯鉅額交易"
                    
                b1_rank = str(row.get(rank_col, '-')) if rank_col else '-'
                score = 0.0
                details = [] 
                
                # 區塊二評分
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
                
                # 區塊三評分
                s_fd, r_b3_fd = get_b3_score(df_b3, sid, '外資日'); score += s_fd; 
                if s_fd > 0: details.append(f"外資日連: +{s_fd}")
                s_fw, r_b3_fw = get_b3_score(df_b3, sid, '外資週'); score += s_fw; 
                if s_fw > 0: details.append(f"外資週連: +{s_fw}")
                s_id, r_b3_id = get_b3_score(df_b3, sid, '投信日'); score += s_id; 
                if s_id > 0: details.append(f"投信日連: +{s_id}")
                s_iw, r_b3_iw = get_b3_score(df_b3, sid, '投信週'); score += s_iw; 
                if s_iw > 0: details.append(f"投信週連: +{s_iw}")
                
                # 🔥 區塊四核心升級 (幅+1, 量+0.5)
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
                            
                    short_decrease_val = 0.0
                    if not df_b4_sho_pct.empty and sid in df_b4_sho_pct['股票代號'].values:
                        s_col = next((c for c in df_b4_sho_pct.columns if '當日' in str(c) and ('%' in str(c) or '增減' in str(c))), None)
                        if s_col:
                            try: short_decrease_val = float(str(df_b4_sho_pct.loc[df_b4_sho_pct['股票代號'] == sid, s_col].iloc[0]).replace('%', ''))
                            except: pass
                    if abs(short_decrease_val) >= 1:
                        score += 1.2; details.append("空頭認輸(借券減>1%): +1.2")

                # 區塊五評分
                r_b5 = ""
                if not df_b5.empty and sid in df_b5['股票代號'].values:
                    trend = str(df_b5[df_b5['股票代號'] == sid].iloc[0].get('週動態', ''))
                    if '大增' in trend or ('增' in trend and '微' not in trend): score += 2; r_b5 = "🔥大增(+2)"; details.append("大股東大增: +2")
                    elif '微增' in trend: score += 1; r_b5 = "↗️微增(+1)"; details.append("大股東微增: +1")
                    elif '大減' in trend: score -= 1; r_b5 = "🚨大減(-1)"; details.append("大股東大減: -1")
                    elif '減' in trend and '微' in trend: score -= 0.5; r_b5 = "↘️微減(-0.5)"; details.append("大股東微減: -0.5")
                    elif '減' in trend: score -= 0.5; r_b5 = "📉減(-0.5)"; details.append("大股東減: -0.5")
                    else: r_b5 = trend
                
                is_fo_sell = sid in fo_sell_ids; is_it_sell = sid in it_sell_ids
                if is_fo_sell and is_it_sell: r_warn = "🚨外投雙倒"; score -= 2.0; details.append("外投雙倒: -2")
                elif is_fo_sell: r_warn = "⚠️外資倒(換手?)"
                elif is_it_sell: r_warn = "⚠️投信倒(換手?)"
                else: r_warn = "-"

                score_breakdown = " \n".join(details) if details else "無加扣分"

                results.append({
                    '總分': score, '代號': sid, '名稱': sname, '▼明細': score_breakdown, 
                    '最新動態': b1_dyn, '今日上榜': b1_rank, '賣出警示': r_warn,
                    '外買佔比': r_b2_1, '投買佔比': r_b2_2, '外佔發行': r_b2_3, '投佔發行': r_b2_4,
                    '外日連': r_b3_fd, '外週連': r_b3_fw, '投日連': r_b3_id, '投週連': r_b3_iw,
                    '資減': r_b4_mar, '借減': r_b4_sho, '券增': r_b4_mp,
                    '大股東動向': r_b5
                })
                
            res_df = pd.DataFrame(results).sort_values(by='總分', ascending=False).drop_duplicates(subset=['代號']).reset_index(drop=True)
            
            # ==========================================
            # 🔥 Delta (▼變量) 計算引擎 (升級為 Google Sheets 讀取版)
            # ==========================================
            prev_scores_dict = {}
            hist_combined = pd.DataFrame() # 預備給 Tab 2 使用
            
            try:
                # 1. 讀取 Google Sheets 中的歷史資料
                gs_history = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史")
                gs_history = gs_history.dropna(how="all")
                
                if not gs_history.empty and '紀錄日期' in gs_history.columns:
                    hist_combined = gs_history.copy()
                    # 取得所有不重複的日期，並由新到舊排序
                    available_dates = sorted(gs_history['紀錄日期'].astype(str).unique(), reverse=True)
                    
                    # 只要有兩天以上的紀錄，就抓「上一天」(索引 1) 的資料來比對 Delta
                    if len(available_dates) >= 2:
                        prev_date = available_dates[1]
                        prev_df = gs_history[gs_history['紀錄日期'].astype(str) == prev_date]
                        
                        id_col = '代號' if '代號' in prev_df.columns else '股票代號' if '股票代號' in prev_df.columns else None
                        if id_col:
                            prev_scores_dict = dict(zip(prev_df[id_col].astype(str).str.replace(r'\D', '', regex=True), prev_df['總分']))
            except Exception as e:
                pass # 第一次可能還沒有資料表，忽略錯誤

            def calc_table_delta(row):
                sid = str(row['代號']).replace(r'\D', '')
                
                # 確保分數是乾淨的浮點數數字，避免文字型態干擾
                try:
                    curr_score = float(row.get('總分', 0))
                except:
                    curr_score = 0.0
                
                # 判斷是否為昨日榜單上的老面孔
                if sid in prev_scores_dict:
                    try:
                        prev_score = float(prev_scores_dict[sid])
                    except:
                        prev_score = 0.0
                        
                    delta = curr_score - prev_score
                    
                    # 使用 :.1f 強制鎖定文字輸出只顯示 1 位小數，徹底封殺浮點數尾數
                    if delta > 0.01: 
                        return f"+{delta:.1f}"
                    elif delta < -0.01: 
                        return f"{delta:.1f}"
                    else: 
                        return "0.0"
                else:
                    # 🆕 全新進榜：同樣鎖定 1 位小數
                    return f"🆕 +{curr_score:.1f}"

            if not res_df.empty and '總分' in res_df.columns:
                res_df['▼變量'] = res_df.apply(calc_table_delta, axis=1)

            cols = [c for c in res_df.columns if c not in ['▼變量', '▼明細', '賣出警示']]
            
            score_idx = cols.index('總分')
            cols.insert(score_idx + 1, '▼變量')
            
            name_idx = cols.index('名稱')
            cols.insert(name_idx + 1, '▼明細')
            
            rank_idx = cols.index('今日上榜')
            cols.insert(rank_idx + 1, '賣出警示')
            
            res_df = res_df[cols]

            st.session_state['top_pool_df'] = res_df
            
            # 💾 歷史紀錄存檔機制 (升級為 Google Sheets 永久雲端版)
            if res_df is not None and not res_df.empty:
                try:
                    anchor_date_str = "00000000" 
                    if all_txt_files:
                        latest_file = max(all_txt_files, key=os.path.basename)
                        date_label = os.path.basename(latest_file)[:8]
                        if date_label.isdigit(): anchor_date_str = date_label
                    
                    if anchor_date_str != "00000000":
                        save_df = res_df.copy()
                        save_df.insert(0, '紀錄日期', anchor_date_str)
                        
                        try:
                            old_df = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史")
                            old_df = old_df.dropna(how="all")
                            if '紀錄日期' in old_df.columns:
                                old_df = old_df[old_df['紀錄日期'].astype(str) != anchor_date_str]
                            final_save_df = pd.concat([old_df, save_df], ignore_index=True)
                        except:
                            final_save_df = save_df

                        conn.update(spreadsheet=SHEET_URL, worksheet="選股歷史", data=final_save_df)
                except Exception as e: 
                    st.error(f"寫入 Google Sheets 發生錯誤: {e}")

            # 🌟 Streamlit 頁籤渲染
            tab1, tab2 = st.tabs(["🔥 今日最新排行", "📈 歷史分數追蹤表"])
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
                        recent_dates = sorted(hist_combined['紀錄日期'].astype(str).unique(), reverse=True)[:20]
                        df_h = hist_combined[hist_combined['紀錄日期'].astype(str).isin(recent_dates)].copy()
                        
                        id_col = '代號' if '代號' in df_h.columns else '股票代號' if '股票代號' in df_h.columns else None
                        
                        if id_col and '總分' in df_h.columns:
                            df_h['日期'] = df_h['紀錄日期'].astype(str).apply(lambda x: f"{x[4:6]}/{x[6:]}" if len(x)==8 else x)
                            df_h['代號'] = df_h[id_col].astype(str).str.replace(r'\D', '', regex=True)
                            df_h = df_h[['代號', '總分', '日期']]
                            
                            hist_pivot = df_h.pivot_table(index='代號', columns='日期', values='總分', aggfunc='first').reset_index()
                            name_mapping = dict(zip(res_df['代號'].astype(str).str.replace(r'\D', '', regex=True), res_df['名稱']))
                            hist_pivot.insert(1, '名稱', hist_pivot['代號'].map(name_mapping).fillna('-'))
                            latest_day = hist_pivot.columns[-1]
                            hist_pivot = hist_pivot[hist_pivot['名稱'] != '-']
                            hist_pivot = hist_pivot.sort_values(by=latest_day, ascending=False).reset_index(drop=True)
                            st.dataframe(hist_pivot, use_container_width=True, hide_index=True)
                            st.info("💡 這裡統整了標的在過去20日選股池中的【總分變化】，可藉此觀察籌碼動能的延續性與驗證 ▼變量！")
                    else: 
                        st.warning("尚無足夠的歷史分數紀錄。")
                except Exception as e: 
                    st.error(f"歷史分數讀取發生錯誤: {e}")


# ==========================================
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
