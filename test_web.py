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
    # 👑 區塊 1：短中長線三大法人持股變化 (搜尋結果專屬顯示)
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
                # 🔥 終極淨化器：過濾掉系統運算用的「內部隱藏欄位」
                hide_keywords = ['_區塊', '排序', '上榜數量', '原始上榜', '精準單日']
                clean_cols = [c for c in res_b1.columns if not any(k in c for k in hide_keywords)]
                
                # 有真實數據，印出乾淨的表格 (只餵給它乾淨的欄位)
                st.dataframe(res_b1[clean_cols], use_container_width=True, hide_index=True)
                
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

############################################    
# ==========================================
# 🧭 側邊欄導航 (極速光速版：零爬蟲、零延遲、讀取本地 CSV)
# ==========================================
import os
import glob
import pandas as pd
import streamlit as st
import datetime
import yfinance as yf

DATA_DIR = "./Goodinfo_Rankings"

@st.cache_data(ttl=60) 
def get_latest_csv(keyword):
    if not os.path.exists(DATA_DIR): return None, "未知"
    files = glob.glob(os.path.join(DATA_DIR, f"*{keyword}*csv"))
    if not files: return None, "未知"
    files.sort(reverse=True)
    try: return pd.read_csv(files[0]), os.path.basename(files[0])[:8]
    except: return None, "未知"

@st.cache_data(ttl=60)
def get_prev_csv(keyword, current_date):
    if not os.path.exists(DATA_DIR): return None
    files = glob.glob(os.path.join(DATA_DIR, f"*{keyword}*csv"))
    past_files = [f for f in files if os.path.basename(f)[:8] < current_date]
    if not past_files: return None
    past_files.sort(reverse=True)
    try: return pd.read_csv(past_files[0])
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

tab1, tab2 = st.sidebar.tabs(["📊 大盤與期權", "🧭 戰情導航"])

# ------------------------------------------
# 1. 大盤籌碼導航總覽 (終極精準融資 + 期貨變化量)
# ------------------------------------------
def render_sidebar_market_summary():
    st.markdown("<h2 style='margin-top: 0; margin-bottom: 5px;'>📊 大盤資金風向球</h2>", unsafe_allow_html=True)
    df_spot, date_spot = get_latest_csv("三大法人買賣超金額")
    df_fut, _ = get_latest_csv("三大法人期貨多空")
    df_fut_prev = get_prev_csv("三大法人期貨多空", date_spot)
    df_margin, _ = get_latest_csv("融資融券餘額") # 💡 檔名對應
    
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

    html = f"<div style='font-size: 13px; color: #00E272;'>📅 {date_spot} | ⚡ 本地極速版</div>"
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
        html += "<div style='margin-top: 8px; padding: 6px; background-color: #1e1e24; border: 1px solid #555; border-radius: 5px; font-size: 13px;'>"
        html += f"<div style='font-weight: bold;'>📉 大盤融資餘額</div>"
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
# 🏠 區塊1：中長線 三大法人 持股比例 追蹤 (JSON 200名快照引擎版 + TXT修復)
# ==========================================
st.write("---")
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)

header_placeholder = st.empty()
c1, c2 = st.columns([3, 1])
with c1: st.link_button("📊 DDong 台股法人籌碼數據儀表板", "https://goodinfo3583.github.io/DDong_tw-institutional-stocker/")
st.write("")

import re
import os
import glob
import pandas as pd
import requests
import datetime
from collections import defaultdict

# ------------------------------------------
# 🌐 全自動 GitHub JSON 抓取引擎
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
                df = df.rename(columns={'code': '股票代號', 'name': '股票名稱', 'three_inst_ratio': '法人持股', 'change': f'{d}日ΔChange'})
                df[f'{d}日排名'] = (df.index + 1).astype(int) 
                json_dfs[d] = df
            else: json_dfs[d] = pd.DataFrame()
        except Exception: json_dfs[d] = pd.DataFrame()
        
    latest_all_df = pd.DataFrame()
    try:
        url_all = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/stock_three_inst_latest.json"
        res_all = requests.get(url_all, timeout=5)
        if res_all.status_code == 200:
            temp_df = pd.DataFrame(res_all.json())
            if not temp_df.empty and 'code' in temp_df.columns and 'change' in temp_df.columns:
                latest_all_df = temp_df[['code', 'change']].rename(columns={'code': '股票代號', 'change': '精準單日△'})
    except Exception: pass
    return json_dfs, latest_all_df

json_dfs, latest_all_df = fetch_github_json_all()

# ------------------------------------------
# 💾 站長專屬：JSON 200名快照存檔區 (含密碼防護與下載功能)
# ------------------------------------------
with st.expander("🛠點我沒反應", expanded=False):
    st.info("💡 站長專用：將今日 GitHub 最新資料封存為歷史 CSV。")
    
    # 1. 密碼防護機制
    admin_pw = st.text_input("請輸入站長密碼以解鎖功能", type="password", key="admin_pw_input")
    
    # 請將 "DDong888" 換成你自己想要的密碼
    if admin_pw == "DDong888": 
        st.success("🔓 驗證成功！請執行快照封存。")
        
        col_d, col_btn = st.columns([1, 2])
        with col_d:
            snap_date = st.date_input("選擇這份資料的實際基準日")
        with col_btn:
            st.write("") 
            if st.button("💾 將今日 GitHub 200名數據封存為 CSV"):
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
                        '法人持股': 'max',
                        '上榜區塊': lambda x: ",".join(set(x))
                    }).reset_index()
                    
                    # 轉成 CSV 格式的字串，準備供下載
                    csv_data = snap_grouped.to_csv(index=False).encode('utf-8-sig')
                    
                    # 依然在伺服器暫存一份，讓當下的畫面可以立刻重算
                    snap_grouped.to_csv(save_path, index=False, encoding='utf-8-sig')
                    
                    st.success(f"✅ 成功生成 {len(snap_grouped)} 檔股票的歷史快照！")
                    
                    # 2. 顯示下載按鈕，讓站長可以直接下載到本機
                    st.download_button(
                        label="📥 點我下載快照 CSV 檔案",
                        data=csv_data,
                        file_name=f"{date_str}_JSON_History.csv",
                        mime="text/csv",
                        type="primary"
                    )
                    st.warning("⚠️ 提醒：請務必點擊上方下載按鈕，將檔案放入本機的 Goodinfo_Rankings 資料夾並 Push 到 GitHub，否則雲端重啟後資料會遺失！")
                else:
                    st.error("❌ 尚未獲取到 GitHub 數據，封存失敗。")
    elif admin_pw != "":
        st.error("❌ 密碼錯誤，無法使用此功能。")
# ------------------------------------------
# 📜 混合歷史解析引擎 (💡 修復版：完美讀取舊 TXT 與新 CSV)
# ------------------------------------------
def parse_special_txt(file_path, date_label):
    parsed_data, target_col, current_section = [], f"{date_label}持股%", None
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith("---") or line_str.startswith("==="):
                    current_section = None; continue
                # 🔥 這裡修復了上一版的 Bug，重新找回精準的標籤定位
                if "三大法人持股變化排名" in line_str or ("排名" in line_str and "日)" in line_str):
                    if "120日" in line_str: current_section = "120日"
                    elif "20日" in line_str: current_section = "20日"
                    elif "5日" in line_str: current_section = "5日"
                    elif "60日" in line_str: current_section = "60日"
                    continue
                parts = line_str.split('\t')
                if current_section and len(parts) >= 4 and parts[0].isdigit():
                    try: holding_pct = float(parts[-2])
                    except ValueError: continue
                    stock_str = parts[1].strip()  
                    m = re.match(r'^(\d+)(.*)', stock_str)
                    parsed_data.append({'股票代號': m.group(1) if m else stock_str, '股票名稱': m.group(2).strip() if m else stock_str, target_col: holding_pct, '上榜區塊': current_section})
    except Exception: pass
    return pd.DataFrame(parsed_data)

def parse_json_history_csv(file_path, date_label):
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df['股票代號'] = df['股票代號'].astype(str)
        df = df.rename(columns={'法人持股': f"{date_label}持股%"})
        return df
    except: return pd.DataFrame()

def agg_sections_func(x):
    valid_x = set()
    for val in x:
        if pd.notna(val) and str(val).strip() != "":
            # 🔥 關鍵修復：針對 CSV 已經合併過的格式 (例如 "5日,20日") 進行拆解，確保每一顆勳章都能獨立辨識
            for p in str(val).split(','):
                valid_x.add(p.strip())
    return ",".join([s for s in ['5日', '20日', '60日', '120日'] if s in valid_x])

# ==========================================
# 🔄 歷史資料合併與邏輯運算 (底層大表重建)
# ==========================================
all_txt_files = glob.glob(os.path.join(DATA_DIR, "*持股排名變化*.txt"))
all_csv_files = glob.glob(os.path.join(DATA_DIR, "*_JSON_History.csv"))

date_files = defaultdict(lambda: {'txt': [], 'csv': []})
for f in all_txt_files:
    date_label = os.path.basename(f)[:8]
    if date_label.isdigit(): date_files[date_label]['txt'].append(f)
for f in all_csv_files:
    date_label = os.path.basename(f)[:8]
    if date_label.isdigit(): date_files[date_label]['csv'].append(f)

sorted_dates = sorted(date_files.keys(), reverse=True)
final_df = pd.DataFrame()

if sorted_dates:
    latest_d = sorted_dates[0]
    fmt_date = f"{latest_d[:4]}/{latest_d[4:6]}/{latest_d[6:]}"
    header_placeholder.markdown(
        f"<h2 style='margin-bottom: 0px;'>👑 區塊1：三大法人短中長線持股比追蹤 "
        f"<span style='color:#00D2FF; font-size:16px; font-weight:500; margin-left:12px;'>歷史基準日：{fmt_date}</span></h2>", 
        unsafe_allow_html=True
    )
    
    final_df = None
    for i, date_label in enumerate(sorted_dates[:30]): 
        day_dfs = []
        if date_files[date_label]['csv']:
            day_dfs.append(parse_json_history_csv(date_files[date_label]['csv'][0], date_label))
        elif date_files[date_label]['txt']:
            for f in date_files[date_label]['txt']: day_dfs.append(parse_special_txt(f, date_label))
            
        day_dfs = [df for df in day_dfs if not df.empty]
        if not day_dfs: continue
            
        df_day_raw = pd.concat(day_dfs, ignore_index=True)
        agg_dict = {f"{date_label}持股%": 'max', '上榜區塊': agg_sections_func}
        df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg(agg_dict).reset_index().rename(columns={'上榜區塊': f"{date_label}_區塊"})
            
        if final_df is None: final_df = df_day
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
        final_df['原始上榜區塊'] = final_df[latest_sect_col] 
            
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
        
        if not latest_all_df.empty and '股票代號' in latest_all_df.columns:
            final_df = pd.merge(final_df, latest_all_df, on='股票代號', how='left')
            final_df['△'] = final_df['精準單日△'].fillna(0.0)
        else:
            if len(date_cols) >= 2:
                final_df['△'] = final_df.apply(
                    lambda row: row[date_cols[0]] - row[date_cols[1]] if row[date_cols[1]] > 0.001 else 0.0, 
                    axis=1
                )
            else:
                final_df['△'] = 0.0
            
        final_df['法人金額'] = 0.0 

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
# 🔧 UI 數據渲染 (精緻過濾與格式化)
# ==========================================
c1, c2 = st.columns(2)
show_etf = c1.checkbox("顯示 ETF", value=True, key="blk1_etf_sync")
show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="blk1_bond_sync")

tab5, tab20, tab60, tab120, tab_all = st.tabs([
    "🔴 5日排行 Top 200", "🟡 20日排行 Top 200", "🟢 60日排行 Top 200", "🔵 120日排行 Top 200", "📊 歷史軌跡全能池"
])

def format_delta(x):
    try:
        val = float(x)
        if abs(val) < 0.005: return "0.00"
        return f"+{val:.2f}" if val > 0 else f"{val:.2f}"
    except: return "0.00"

def process_json_tab(df, target_day):
    if df.empty: return df
    
    if not final_df.empty:
        merge_cols = ['股票代號', '最新動態', '今日上榜', '△']
        available_cols = [c for c in merge_cols if c in final_df.columns]
        df = pd.merge(df, final_df[available_cols], on='股票代號', how='left')
        
    if '△' not in df.columns: df['△'] = 0.0
        
    is_bond = df['股票代號'].str.endswith('B')
    is_etf = (df['股票代號'].str.len() >= 5) & (~is_bond)
    is_stock = df['股票代號'].str.len() == 4
    mask = is_stock
    if show_etf: mask |= is_etf
    if show_bond: mask |= is_bond
    df = df[mask].copy()

    df['法人持股'] = df['法人持股'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
    
    if f'{target_day}日ΔChange' in df.columns: df[f'{target_day}日ΔChange'] = df[f'{target_day}日ΔChange'].apply(format_delta)
    if '△' in df.columns: df['△'] = df['△'].apply(format_delta)
    
    df['法人金額'] = "0.00"
    if '最新動態' in df.columns: df['最新動態'] = df['最新動態'].fillna("⚪ 尚無比對紀錄")
    if '今日上榜' in df.columns: df['今日上榜'] = df['今日上榜'].fillna("")
    return df

with tab5:
    df_5 = process_json_tab(json_dfs.get(5, pd.DataFrame()), 5)
    display_cols = ['5日排名', '股票代號', '股票名稱', '法人持股', '△', '5日ΔChange', '法人金額', '最新動態', '今日上榜']
    if not df_5.empty: st.dataframe(df_5[[c for c in display_cols if c in df_5.columns]], use_container_width=True, hide_index=True)
    else: st.info("💡 正在從 Github 獲取數據...")

with tab20:
    df_20 = process_json_tab(json_dfs.get(20, pd.DataFrame()), 20)
    display_cols = ['20日排名', '股票代號', '股票名稱', '法人持股', '△', '20日ΔChange', '法人金額', '最新動態', '今日上榜']
    if not df_20.empty: st.dataframe(df_20[[c for c in display_cols if c in df_20.columns]], use_container_width=True, hide_index=True)

with tab60:
    df_60 = process_json_tab(json_dfs.get(60, pd.DataFrame()), 60)
    display_cols = ['60日排名', '股票代號', '股票名稱', '法人持股', '△', '60日ΔChange', '法人金額', '最新動態', '今日上榜']
    if not df_60.empty: st.dataframe(df_60[[c for c in display_cols if c in df_60.columns]], use_container_width=True, hide_index=True)

with tab120:
    df_120 = process_json_tab(json_dfs.get(120, pd.DataFrame()), 120)
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
            
        all_display_cols = ['股票代號', '股票名稱', '今日上榜', '最新動態'] + date_cols
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
# 💰 區塊 5：大股東動向 (八碼完整日期顯示版)
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
            
            # 【核心修復 1】：取消去西元截斷，全面保留 8 碼 (例如 20260530)
            standardized_cols = []
            for c in df.columns:
                if re.match(r'^202\d{5}$', c):  # 如果是完整的 8 碼格式
                    standardized_cols.append(c)
                elif re.match(r'^\d{4}$', c):   # 防呆機制：如果是舊的 4 碼檔案，幫它補回年份
                    standardized_cols.append(f"2026{c}")
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
                
            # 抓取已被標準化為 8 碼的日期欄位
            date_cols = [c for c in df.columns if re.match(r'^202\d{5}$', c)]
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
        
        # 2. 排序日期欄位 (已轉為8碼，可直接降冪排序，越新越前面)
        sorted_dates = sorted(list(all_date_cols), reverse=True)
        
        # 🔥 抓出最新日期，並印出帶有樣式的標題
        latest_date = sorted_dates[0] if sorted_dates else "無資料"
        # 標題美化：將 20260530 變成 2026/05/30
        fmt_latest_date = f"{latest_date[:4]}/{latest_date[4:6]}/{latest_date[6:]}" if len(latest_date) == 8 else latest_date
        
        st.write("---")
        st.markdown("<div id='section-5'></div>", unsafe_allow_html=True)
        st.markdown(f"## 💰 區塊 5：大股東動向 <span style='font-size: 0.5em; color: #00D2FF;'>({fmt_latest_date})</span>", unsafe_allow_html=True)
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
        
        # 🔥 表格輸出前，把最新日期的欄位名稱加上 ▼ (維持 8 碼)
        if sorted_dates:
            latest_col = sorted_dates[0]
            final_df = final_df.rename(columns={latest_col: f"▼{latest_col}"})
        
        st.dataframe(final_df, use_container_width=True, hide_index=True)
        
        # 將最終結果同步存入記憶體，供搜尋區塊聯動掃描
        st.session_state['df_blk5'] = final_df
    else:
        st.error("無法合併資料。")
# ==========================================
# 💸 區塊 6：盤後鉅額交易總表 (發光懸浮 + 歷史矩陣強效相容版)
# ==========================================
def clean_number_for_display(val):
    try:
        if pd.isna(val) or str(val).strip() == '-': return '-'
        f = float(str(val).replace(',', ''))
        return str(int(f)) if f.is_integer() else str(f).rstrip('0').rstrip('.')
    except: return str(val)

@st.cache_data(ttl=60)
def build_historical_block_matrix():
    """搜尋資料夾中所有的鉅額交易紀錄，自動組成歷史矩陣 (最強寬容版)"""
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
            col_name = f"▼{short_date}"
            if col_name not in date_cols: date_cols.append(col_name)
            
            df = pd.read_csv(f)
            # 🎯 極致寬容的欄位鎖定：只要包含關鍵字就能抓！
            c_code = next((c for c in df.columns if '代號' in c or '證券代號' in c), None)
            c_name = next((c for c in df.columns if '名稱' in c or '證券名稱' in c), None)
            c_price = next((c for c in df.columns if '價' in c), None) # 只要有「價」就抓
            
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
        valid_date_cols.sort(reverse=True)
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

tab_today, tab_hist = st.tabs(["🆕 今日最新鉅額交易", "📅 歷史防守價追蹤表"])

# ==================== Tab 1: 今日鉅額交易 ====================
with tab_today:
    if df_block is not None and not df_block.empty:
        col_code = next((c for c in df_block.columns if '代號' in c), None)
        col_name = next((c for c in df_block.columns if '名稱' in c), None)
        col_price = next((c for c in df_block.columns if '單價' in c or '成交價' in c), None)
        col_vol = next((c for c in df_block.columns if '股數' in c or '張數' in c or '成交量' in c), None)
        col_amt = next((c for c in df_block.columns if '金額' in c or '總額' in c), None)

        if all([col_code, col_name, col_price, col_vol, col_amt]):
            df_block['代號'] = df_block[col_code].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
            df_block['股票名稱'] = df_block[col_name]
            df_block['成交價'] = pd.to_numeric(df_block[col_price].astype(str).replace(',', '', regex=True), errors='coerce')
            df_block['成交股數'] = pd.to_numeric(df_block[col_vol].astype(str).replace(',', '', regex=True), errors='coerce')
            df_block['成交金額'] = pd.to_numeric(df_block[col_amt].astype(str).replace(',', '', regex=True), errors='coerce')
            df_block = df_block[(df_block['代號'] != '0') & (df_block['代號'] != '') & (df_block['代號'] != 'nan')]

            grouped_block = df_block.groupby(['代號', '股票名稱']).agg({
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
            display_df = grouped_block[['代號', '股票名稱', '成交價', '▼收盤價', '成交張數', '總額(億)']].copy()
            display_df = display_df.rename(columns={'成交價': dynamic_price_col})

            def style_block_table(df):
                styler = df.style.hide(axis='index') if hasattr(df.style, 'hide') else df.style.hide_index()
                def highlight_row(row):
                    styles = []
                    target_col = [c for c in row.index if '成交價' in c][0]
                    for col in row.index:
                        if col == target_col:
                            try:
                                prices = [float(p) for p in str(row[target_col]).split(' / ')]
                                avg_p = sum(prices) / len(prices)
                                c_p = float(str(row['▼收盤價']).replace(',',''))
                                color = '#FF4B4B' if c_p > avg_p else '#FFA500' if c_p == avg_p else '#00E272'
                                styles.append(f"color: {color}; font-weight: bold;")
                            except: styles.append(f"color: #e0e0e0;")
                        else:
                            styles.append('color: #e0e0e0;')
                    return styles
                
                styler = styler.apply(highlight_row, axis=1)
                border_css = '1px solid #808495'
                
                styler = styler.set_table_styles([
                    {'selector': 'table', 'props': [('width', '100%'), ('border-collapse', 'collapse'), ('font-family', 'sans-serif'), ('font-size', '13px')]},
                    {'selector': 'th.col2', 'props': [('width', '90px'), ('text-align', 'left !important')]},
                    {'selector': 'td.col2', 'props': [('text-align', 'left !important')]},
                    {'selector': 'th', 'props': [
                        ('background-color', '#1e1e24'), ('color', '#ffffff'), ('font-weight', 'normal'),
                        ('border', border_css), ('padding', '6px 4px'), ('text-align', 'center'),
                        ('position', 'sticky'), ('top', '0'), ('z-index', '1')
                    ]},
                    {'selector': 'td', 'props': [
                        ('border', border_css), ('padding', '6px'), ('text-align', 'center'), ('transition', 'all 0.2s ease-in-out')
                    ]},
                    {'selector': 'tbody tr:hover td', 'props': [
                        ('background-color', 'rgba(4, 8, 20, 0.85) !important'), 
                        ('text-shadow', '0 0 8px rgba(255, 255, 255, 0.5) !important')
                    ]}
                ])
                return styler.to_html()

            html_table = style_block_table(display_df)
            scrollable_div = f"""
            <div style="max-height: 350px; overflow-y: auto; border: 1px solid #808495; border-radius: 5px;">
            {html_table}
            </div>
            """
            st.markdown(scrollable_div, unsafe_allow_html=True)
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
# 🏆 頂級選股池核心引擎 (動態日期捕捉 + 暗盤連動)
# ==========================================
with top_pool_container:
    st.write("---")
    st.markdown("<div id='section-top-pool'></div>", unsafe_allow_html=True)
    
    import os
    import glob
    import re
    import json
    import pandas as pd

    # 1. 自動掃描最新資料日期 (🔥 終極升級：四大區塊獨立日期追蹤引擎)
    all_files = glob.glob(os.path.join(DATA_DIR, "*"))
    anchor_date_str = "00000000" # 供存檔用的全局最大日期
    
    # 🔥 完整建立各區塊專屬的日期追蹤器
    d_b1_inst = "00000000"  # 區塊1：法人持股排名
    d_b23_chip = "00000000" # 區塊2&3：買賣佔比、連買
    d_b4_margin = "00000000"# 區塊4：融資券、借券
    d_b5_share = "00000000" # 區塊5：大股東、神秘金字塔
    
    for f in all_files:
        filename = os.path.basename(f)
        # 尋找檔名中 8 位數的日期 (例如 20260604)
        match = re.search(r'(202\d{5})', filename)
        if match:
            file_date = match.group(1)
            
            # 紀錄全局最大日期 (存檔用)
            if file_date > anchor_date_str:
                anchor_date_str = file_date
                
            # 🔥 完整分類掃描各區塊的最新日期
            if "持股排名變化" in filename or "JSON_History" in filename:
                if file_date > d_b1_inst: d_b1_inst = file_date
                
            elif "佔成交比" in filename or "連買" in filename or "買賣超" in filename:
                if file_date > d_b23_chip: d_b23_chip = file_date
                
            elif "融資" in filename or "融券" in filename or "借券" in filename or "資券" in filename:
                if file_date > d_b4_margin: d_b4_margin = file_date
                
            elif "大股東" in filename or "集保" in filename or "神秘金字塔" in filename:
                if file_date > d_b5_share: d_b5_share = file_date

    # 日期格式化小工具 (只顯示 月/日)
    def fmt_d(d_str):
        return f"{d_str[4:6]}/{d_str[6:]}" if d_str != "00000000" else "--/--"

    # 🔥 恢復四大區塊獨立日期顯示，掌握所有籌碼的開牌進度！
    st.markdown(
        f"## 🏆 數據分析觀察名單 <br>"
        f"<span style='font-size:14px; color:#00D2FF; font-weight:500; display:inline-block; margin-top:5px; background-color:rgba(0, 210, 255, 0.1); padding:5px 10px; border-radius:5px;'>"
        f"📊 資料基準日 ➔ 📍區塊1(法人): {fmt_d(d_b1_inst)} ｜ 📍區塊2&3(佔比/連買): {fmt_d(d_b23_chip)} ｜ 📍區塊4(資券): {fmt_d(d_b4_margin)} ｜ 📍區塊5(大股東): {fmt_d(d_b5_share)}"
        f"</span>", 
        unsafe_allow_html=True
    )
    
    st.info("💡 **評分方式**：區塊一之法人持股上榜搭配其他數據分析積分。(請搜尋參考今日短動態追蹤法人行為,評分數據僅供參考)")

    # (接下來保留原本的 if 'my_final_df' not in st.session_state... 以下都不用動)

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
                
                if sid in block_sids: b1_dyn = f"{b1_dyn} | 💸 鉅額交易"
                    
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
                
                # 區塊四核心升級 (幅+1, 量+0.5)
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
            hist_combined = pd.DataFrame() 
            
            try:
                gs_history = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史", ttl=600)
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
            except Exception as e:
                pass 

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
                else:
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
            
            # 💾 歷史紀錄存檔機制 (嚴格依據動態日期 anchor_date_str 寫入)
            if res_df is not None and not res_df.empty:
                try:
                    if anchor_date_str != "00000000":
                        save_df = res_df.copy()
                        save_df.insert(0, '紀錄日期', anchor_date_str)
                        
                        try:
                            old_df = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史", ttl=600)
                            old_df = old_df.dropna(how="all")
                            if '紀錄日期' in old_df.columns:
                                old_df['紀錄日期'] = old_df['紀錄日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8)
                                # 🔥 關鍵防護：只刪除「相同總最新日期」的舊資料，絕對不刪除前一天的紀錄！
                                old_df = old_df[old_df['紀錄日期'] != anchor_date_str]
                            final_save_df = pd.concat([old_df, save_df], ignore_index=True)
                        except:
                            final_save_df = save_df

                        conn.update(spreadsheet=SHEET_URL, worksheet="選股歷史", data=final_save_df)
                except Exception as e: 
                    pass # 隱藏報錯，保持版面乾淨

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
                    else: 
                        st.warning("尚無足夠的歷史分數紀錄。")
                except Exception as e: 
                    pass

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
