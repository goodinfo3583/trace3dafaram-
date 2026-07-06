import streamlit as st
import pandas as pd
import numpy as np
import os
import glob       
import re         
import datetime
import requests  
import pytz  
import math
import streamlit.components.v1 as components
import plotly.express as px

# ==========================================
# 1. 網頁基本設定 (⚠️ 注意：這行必須是整個檔案的第一個 st 指令)
# ==========================================
st.set_page_config(page_title="股市派對", layout="wide")

# ==========================================
# ✨ 2. 一鍵召喚 UI 視覺特效法術書！
# ==========================================
import ui
ui.setup_all_effects()

# =======================================================
## 👇2.01-在這裡加入這兩行，啟動data_engine引擎！
# =======================================================
import data_engine
data_engine.init_all_data()

# 👇 告訴主程式，我們有一個側邊欄工具箱可以使用
import left_panel
# ==========================================
# 3. 資料庫連線與路徑初始化
# ==========================================
# 👇 啟動 Google Sheets 永久連線引擎
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TxHDahg8ul6lmUtDN-7X75cBXbkU0jaZ3M9zg6exBgU"

# 👉 宣告路徑變數
DATA_DIR = "./Goodinfo_Rankings"
SCORE_HISTORY_DIR = os.path.join(DATA_DIR, "ScoreHistory")
MARKET_HISTORY_DIR = os.path.join(DATA_DIR, "MarketHistory")
BLOCK_HISTORY_DIR = os.path.join(DATA_DIR, "BlockHistory")

# ==========================================
# 🛑 4. 隱形急救引擎 (確保護航資料夾與備援檔存在)
# ==========================================
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(SCORE_HISTORY_DIR): os.makedirs(SCORE_HISTORY_DIR)
if not os.path.exists(MARKET_HISTORY_DIR): os.makedirs(MARKET_HISTORY_DIR)
if not os.path.exists(BLOCK_HISTORY_DIR): os.makedirs(BLOCK_HISTORY_DIR)

backup_df_path = os.path.join(DATA_DIR, "sidebar_twse_df_backup.csv")
backup_margin_path = os.path.join(DATA_DIR, "sidebar_margin_backup.csv")

if not os.path.exists(backup_df_path):
    pd.DataFrame({
        '單位名稱': ['合計'],
        '買賣差額': ['102770738307']
    }).to_csv(backup_df_path, index=False, encoding='utf-8-sig')

if not os.path.exists(backup_margin_path):
    pd.DataFrame([{"today_bal": 556359646.0, "prev_bal": 535025764.0}]).to_csv(backup_margin_path, index=False, encoding='utf-8-sig')

# ---------------- (原本 293 行之後的程式碼繼續接在這裡) ----------------

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

# ===================================================================
# 🗂 核心共用工具-台股代號與名稱產業類別 萬用字典引擎 (後台靜默運作)
# ===================================================================
@st.cache_data(ttl=3600)
def get_stock_dictionary():
    """讀取證交所 ISIN 檔案，在後台安靜地建立雙向對照表"""
    import re
    import glob
    import os
    mapping = {}
    
    # 假設 DATA_DIR 已經在全域宣告，若無請確保替換為實際字串
    search_patterns = [
        "./Goodinfo_Rankings/*辨識號碼*.txt",
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
            
            clean_name = re.sub(r'[\s ]+', ' ', name_part).strip()
            tokens = clean_name.split(' ')
            
            if len(tokens) >= 2:
                sid = tokens[0].strip()
                sname = tokens[1].strip()
                
                # 💡 修改處：用 isalnum 容許 ETF 代號 (如 00983A)
                if sid.isalnum(): 
                    mapping[sname] = {"id": sid, "name": sname, "industry": industry}
                    mapping[sid] = {"id": sid, "name": sname, "industry": industry}
                    
    return mapping

# 啟動時載入字典
STOCK_DICT = get_stock_dictionary()


# ================
# 🌌 網頁風格設計
# ================
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
# 🚦 網頁路由控制中心 (極速切換引擎)
# ==========================================
# 【首頁顯示預設】：把預設值改成 "news"，這樣一進網站就會是最新消息！(現在首頁改成區塊1)
current_page = st.query_params.get("page", "b1")
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 📍 頂部按鈕 (終極無縫切換版 + 懸浮提示收闔浮標 + 修復死鍵Bug)
# ==========================================
inject_js = """
<script>
const parentDoc = window.parent.document;

if (!parentDoc.getElementById('custom-sticky-header')) {
    
    const style = parentDoc.createElement('style');
    style.innerHTML = `
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="collapsedControl"] { top: 70px !important; z-index: 1000000 !important; background-color: rgba(10, 13, 20, 0.8) !important; border-radius: 50%; }

        #custom-sticky-header { position: fixed; top: 0; left: 0; width: 100%; z-index: 999999; background: transparent !important; pointer-events: none; }
        .disclaimer-bar, .nav-btn-container { pointer-events: auto; }
        .disclaimer-bar { display: flex; align-items: center; background: transparent !important; padding: 0px 15px; border: none !important; }
        .disclaimer-item { position: relative; padding: 6px 15px; cursor: help; background: transparent !important; }
        .disclaimer-title { color: #64748B; font-size: 13px; font-weight: 500; text-decoration: none; text-shadow: 1px 1px 4px rgba(0,0,0,1), -1px -1px 4px rgba(0,0,0,1); }
        .disclaimer-item:hover .disclaimer-title { color: #FFD700; text-shadow: 0 0 8px rgba(255, 215, 0, 0.8); }
        
        /* 閃亮亮的登入按鈕*/
        .vip-login-btn { color: #FFD700 !important; font-weight: bold; text-shadow: 0 0 5px rgba(255, 215, 0, 0.5); transition: all 0.3s; }
        .vip-login-btn:hover { text-shadow: 0 0 12px rgba(255, 215, 0, 1); transform: scale(1.05); }

        .disclaimer-content { position: absolute; top: 100%; left: 0; width: 350px; max-width: 90vw; background-color: rgba(17, 22, 34, 0.95); border: 1px solid #1E293B; border-top: none; border-radius: 0 0 8px 8px; padding: 0px 15px; max-height: 0; opacity: 0; overflow: hidden; transition: all 0.3s; font-size: 12px; color: #94A3B8; line-height: 1.6; box-shadow: 0px 8px 20px rgba(0,0,0,0.8); }
        .disclaimer-item:hover .disclaimer-content { max-height: 400px; opacity: 1; padding: 12px 15px; }
        
        .nav-btn-container { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; padding: 8px 15px; background: transparent !important; gap: 6px; border: none !important; transition: all 0.3s ease-in-out; }
        .nav-text-link { text-decoration: none !important; color: #94A3B8 !important; font-size: 16px; font-weight: 600; padding: 4px 6px; transition: all 0.2s ease-in-out; text-shadow: 1px 1px 4px rgba(0,0,0,1), -1px -1px 4px rgba(0,0,0,1); cursor: pointer; display: flex; align-items: center; }
        .nav-text-link:hover { color: #FFD700 !important; text-shadow: 0 0 12px rgba(255, 215, 0, 0.8); transform: scale(1.08); }
        .nav-divider { color: #334155; font-size: 16px; user-select: none; }
        #custom-sidebar-toggle { color: #38BDF8 !important; }

        /* 🎨 自訂圖片圖示的 CSS 樣式 */
        .nav-icon { 
            width: 22px; 
            height: 22px; 
            margin-right: 5px; 
            border-radius: 4px; 
            object-fit: cover;
            position: relative; 
            top: -2px;          
            left: 0px;          
            transition: all 0.3s ease-in-out;
        }
        .nav-text-link:hover .nav-icon {
            filter: drop-shadow(0px 0px 6px rgba(255, 215, 0, 0.9)) brightness(1.15);
        }
        
        @media (max-width: 768px) { .nav-btn-container { padding: 5px 10px; } .nav-divider { display: none; } .nav-text-link { font-size: 14px; margin: 2px; } }
        .stApp { margin-top: 50px !important; }
    `;
    parentDoc.head.appendChild(style);

    const headerDiv = parentDoc.createElement('div');
    headerDiv.id = 'custom-sticky-header';
    headerDiv.innerHTML = `
        <div class="disclaimer-bar">
            <div class="disclaimer-item"><span class="disclaimer-title">使用聲明</span><div class="disclaimer-content">本平台僅供教育研究與籌碼觀察，絕不構成任何實質投資建議、勸誘或要約。所有資料源自公開數據，受限於網路技術，可能有延遲或錯誤。<br><br>投資必有風險，依本平台資訊所做之任何決策與損益，均須由使用者自行負責，本平台不負擔任何法律賠償責任。</div></div>
            <div class="disclaimer-item"><span class="disclaimer-title">隱私權政策</span><div class="disclaimer-content"><b>1. 蒐集目的與範圍：</b><br>本平台依個資法蒐集您的識別資料僅供維持系統安全與優化服務使用。<br><b>2. 資料利用：</b><br>您的資料絕不向第三方洩露。<br><b>3. 資料刪除：</b><br>您可透過「聯絡我們」請求刪除資料。<br><b>4. 政策修訂：</b><br>本站保留修改政策之權利，繼續使用即視為同意。</div></div>
            <div class="disclaimer-item"><a href="#" data-target="NavToContact" class="disclaimer-title internal-nav" style="cursor: pointer;">聯絡我們</a></div>
            
            <div class="disclaimer-item">
                <a href="#" data-target="登入專區" class="disclaimer-title internal-nav vip-login-btn" style="cursor: pointer; display: flex; align-items: center;">
                    <span style="font-size: 13px; margin-right: 3px;"></span> 登入🛠️
                </a>
            </div>
           
            <div style="flex-grow: 1;"></div>
            <div class="disclaimer-item" id="mobile-nav-toggle" title="收起選單" style="cursor: pointer; padding-right: 5px;">
                <span id="nav-toggle-icon" style="font-size: 18px; color: #38BDF8;">📜</span>
            </div>
        </div>
        <div class="nav-btn-container" id="nav-btn-container">
            <a href="#" id="custom-sidebar-toggle" class="nav-text-link"><img src="app/static/iconarrow1.png" class="nav-icon" alt="icon">呼叫側邊欄</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToNews" class="nav-text-link internal-nav"><img src="app/static/magicbook2.png" class="nav-icon" alt="icon">市場消息</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToPool" class="nav-text-link internal-nav"><img src="app/static/magicbookfire2.png" class="nav-icon" alt="icon">觀察名單</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB1" class="nav-text-link internal-nav"><img src="app/static/magicbookleaf.png" class="nav-icon" alt="icon">法人動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB2" class="nav-text-link internal-nav"><img src="app/static/magicbookwind.png" class="nav-icon" alt="icon">法人掃貨</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB3" class="nav-text-link internal-nav"><img src="app/static/magicbookwater.png" class="nav-icon" alt="icon">法人連買</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB4" class="nav-text-link internal-nav"><img src="app/static/magicbookground.png" class="nav-icon" alt="icon">資券動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB5" class="nav-text-link internal-nav"><img src="app/static/wirtleg.png" class="nav-icon" alt="icon">大腿動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB6" class="nav-text-link internal-nav"><img src="app/static/magicbookfire.png" class="nav-icon" alt="icon">鉅額交易</a>
        </div>
    `;
    parentDoc.body.insertBefore(headerDiv, parentDoc.body.firstChild);

    setTimeout(() => {
        // 🚀 主按鈕切換邏輯
        const navLinks = parentDoc.querySelectorAll('.internal-nav');
        navLinks.forEach(link => {
            link.onclick = (e) => {
                e.preventDefault(); 
                const targetName = link.getAttribute('data-target');
                const btns = Array.from(parentDoc.querySelectorAll('button'));
                
                // 💡 終極殺招：使用 textContent 取代 innerText，保證隱藏按鈕也能被找到！
                const targetBtn = btns.find(b => b.textContent.includes(targetName));
                if (targetBtn) targetBtn.click();
            };
        });

        // 🚀 收闔邏輯：只改變 title 與 icon 內容
        const menuToggle = parentDoc.getElementById('mobile-nav-toggle');
        const navContainer = parentDoc.getElementById('nav-btn-container');
        const iconSpan = parentDoc.getElementById('nav-toggle-icon');
        
        if (menuToggle && navContainer && iconSpan) {
            menuToggle.onclick = (e) => {
                e.preventDefault();
                if (navContainer.style.display === 'none') {
                    navContainer.style.display = 'flex';
                    menuToggle.title = "收起選單";
                    iconSpan.innerText = '📜';
                    iconSpan.style.color = '#38BDF8';
                } else {
                    navContainer.style.display = 'none';
                    menuToggle.title = "展開選單";
                    iconSpan.innerText = '📙';
                    iconSpan.style.color = '#FFD700';
                }
            };
        }

        // 側邊欄開關邏輯
        const toggleBtn = parentDoc.getElementById('custom-sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.onclick = (e) => {
                e.preventDefault();
                const expandBtn = parentDoc.querySelector('[data-testid="collapsedControl"]');
                if (expandBtn) expandBtn.click();
                else {
                    const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
                    if (sidebar) {
                        const closeBtn = sidebar.querySelector('button');
                        if (closeBtn) closeBtn.click();
                    }
                }
            };
        }
        
        // 🛡️ 隱藏守護員：可以安心使用 display: none 了
        setInterval(() => {
            const allBtns = Array.from(parentDoc.querySelectorAll('button'));
            allBtns.forEach(b => {
                if(b.textContent.includes('NavTo')) { // 這裡也要用 textContent
                    const wrapper = b.closest('div[data-testid="stElementContainer"]');
                    if (wrapper) wrapper.style.display = 'none';
                }
            });
        }, 100);
    }, 500);
}
</script>
"""

# 透過隱藏的頂部按鈕導航 iframe 執行上述的 JavaScript 注入
components.html(inject_js, height=0, width=0)

# ==========================================
# 🔗 市場消息隱形傳送門：讓頂部 JS 按鈕可以切換實體分頁
# ==========================================
if st.button("NavToNews", key="nav_news"):
    try:
        # 直接指定沒有 Emoji 的純淨檔名！
        st.switch_page("pages/1_市場消息.py")
    except Exception as e:
        st.error(f"⚠️ 傳送失敗，系統回報的錯誤細節：{e}")

# ==========================================
# 🌟 觀察名單專屬工具函數區 (補回遺失的計分工具)
# ==========================================
def get_df_safe(key): 
    return st.session_state.get(key, pd.DataFrame())

def fmt_d(d_str): 
    return f"{d_str[4:6]}/{d_str[6:]}" if d_str != "00000000" else "--/--"

# 💡 防呆升級版：即使讀到了壞掉的表，也絕對不會當機！
def check_b2_strict(df, sid, bad_keywords):
    if df.empty or '股票代號' not in df.columns or sid not in df['股票代號'].values: return False
    dyn = str(df[df['股票代號'] == sid].iloc[0].get('今日短動態', ''))
    if any(bad in dyn for bad in bad_keywords): return False
    return True

# 💡 防呆升級版：支援欄位模糊比對，找不到欄位也絕對不准當機！
def get_b3_score(df, sid, type_keyword):
    if df is None or df.empty or '股票代號' not in df.columns: 
        return 0, ""
    
    # 模糊比對尋找「類型」與「天數」欄位
    type_col = next((c for c in df.columns if '類型' in str(c) or '連買' in str(c)), None)
    days_col = next((c for c in df.columns if '週期' in str(c) or '天數' in str(c) or '日' in str(c)), None)
    
    # 如果真的找不到對應欄位，直接回傳 0 分，跳過計算
    if not type_col or not days_col or type_col not in df.columns:
        return 0, ""

    match = df[(df['股票代號'] == sid) & (df[type_col].astype(str).str.contains(type_keyword, na=False))]
    if match.empty: return 0, ""
    
    days = pd.to_numeric(match.iloc[0].get(days_col, 0), errors='coerce')
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
    if df is not None and not df.empty and '股票代號' in df.columns and stock_id in df['股票代號'].values:
        try: return float(df.loc[df['股票代號'] == stock_id, col_name].iloc[0])
        except: 
            # 模糊比對欄位，避免 CSV 欄位名稱有些微差異
            fuzzy_col = next((c for c in df.columns if '當日' in str(c) and ('買' in str(c) or '比' in str(c))), None)
            if fuzzy_col:
                try: return float(df.loc[df['股票代號'] == stock_id, fuzzy_col].iloc[0])
                except: pass
    return 0.0

def robust_read_csv_pool(file_path):
    import pandas as pd
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): continue
            return df
        except: continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# 🛑 test_web.py 目前到這裡結束！ 🛑*****

# =======================================================
# 🚀 終極局部渲染魔法：將整個側邊欄獨立為「不閃爍區塊」
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
# 使用預設的帶邊框容器把圖表和表格包起來
    with st.container(border=True):
        
        # ==========================================
        # 🎯 搜尋輸入框 (🚀 升級版：透明幽靈按鈕)
        # ==========================================
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
            # 🚀 關鍵修正：加入 type="tertiary" 拔除底色與邊框
            st.button("→", key="btn_go", type="tertiary", use_container_width=True, help="送出搜尋")
            
        with c_btn_clear:
            # 🚀 關鍵修正：加入 type="tertiary" 拔除底色與邊框
            st.button("×", key="btn_clear", type="tertiary", on_click=clear_search, use_container_width=True, help="清空欄位")

        pure_stock_id = ""
        display_name = search_query
        
        # ... (以下保留你原本的 pure_stock_id 解析邏輯與排版) ...

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
                match = left_panel.robust_search_engine(pool_df, current_stock_id) if current_stock_id else left_panel.robust_search_engine(pool_df, search_query)
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
            
            # ==========================================
            # 📊 優化：K 線控制台 (利用 Fragment 特性，無須 rerun)
            # ==========================================
            show_kline = st.toggle("📊 展開技術 K 線圖", value=st.session_state.get('show_kline', False), key="toggle_kline")
            st.session_state.show_kline = show_kline

            if show_kline:
                if 'pure_stock_id' in locals() and pure_stock_id != "":          
                    st.markdown("##### ⚙️ 技術線圖與指標配置面板")
                    
                    kline_period = st.radio("選擇週期", ["日線", "週線", "月線"], horizontal=True, label_visibility="collapsed", key="kline_radio_period")
                    
                    ind_c1, ind_c2, ind_c3 = st.columns(3)
                    chk_kd = ind_c1.checkbox("顯示 KD (9,3,3)", value=False, key="kd_chk")
                    chk_macd = ind_c2.checkbox("顯示 MACD (12,26,9)", value=False, key="macd_chk")
                    chk_rsi = ind_c3.checkbox("顯示 RSI (14)", value=False, key="rsi_chk")
                    st.write("") 
                    
                    with st.spinner(f"正在擷取 {pure_stock_id} 的最新數據..."):
                        all_mas = ["5MA", "10MA", "20MA", "60MA", "120MA", "240MA"]
                        left_panel.render_technical_chart(pure_stock_id, kline_period, all_mas, chk_rsi, chk_macd, chk_kd)
                else:
                    st.warning("⚠️ 技術 K 線圖目前僅支援代號查詢。")

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>👑 區塊 1：短中長線三大法人持股變化</h4>", unsafe_allow_html=True)
            
            if 'my_final_df' in st.session_state:
                df_b1 = st.session_state['my_final_df']
                res_b1 = left_panel.robust_search_engine(df_b1, search_query)
                
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
            with c1: left_panel.scan_and_display("🌐 外資 5 日淨買佔成交量", 'df_blk2_1', search_query)
            with c2: left_panel.scan_and_display("🏦 投信 5 日淨買佔成交量", 'df_blk2_2', search_query)
            c3, c4 = st.columns(2)
            with c3: left_panel.scan_and_display("🌐 外資 5 日淨買佔發行量", 'df_blk2_3', search_query)
            with c4: left_panel.scan_and_display("🏦 投信 5 日淨買佔發行量", 'df_blk2_4', search_query)

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>📅 區塊 3：法人連買診斷 (日/週)</h4>", unsafe_allow_html=True)
            if 'df_blk3_main' in st.session_state:
                df_b3 = st.session_state['df_blk3_main']
                res_b3 = left_panel.robust_search_engine(df_b3, search_query)
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
            
            left_panel.render_b4_panorama("5日幅度變動排名", [('📉 融資減少', 'df_margin_pct'), ('📉 借券減少', 'df_short_pct'), ('📈 融券增加', 'df_margin_plus_pct')], search_query)
            st.write("") 
            left_panel.render_b4_panorama("5日張數變動排名", [('📉 融資減少', 'df_margin_vol'), ('📉 借券減少', 'df_short_vol'), ('📈 融券增加', 'df_margin_plus_vol')], search_query)

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #FCD34D;'>💰 區塊 5：大戶動向診斷</h4>", unsafe_allow_html=True)
            
            col_400, col_1000 = st.columns(2)
            with col_400: left_panel.scan_and_display("💎 400張以上大戶動向", 'df_blk5', search_query)
            with col_1000: left_panel.scan_and_display("🐳 1000張以上超級大戶動向", 'df_blk5_1000', search_query)

    # 💡 當搜尋列「沒有內容」時，顯示大盤總經 (隱藏下方 Tabs)
    if not search_query:
        st.write("---") # 側邊欄快搜與三大導航 Tab 的分隔線
        tab1, tab2, tab3 = st.tabs(["🔹 大盤籌碼", "🔹 選擇權", "🔹 總經導航🛠️"])
        
        with tab1:
            actual_data_date = left_panel.render_sidebar_market_summary()
            
        with tab2:
            left_panel.render_options_dashboard()
            
        with tab3:
            macro_data = left_panel.fetch_macro_indicators()
            
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
# 側邊欄：實際呼叫魔法渲染區塊 (放在這裡即可)
# =======================================================
with st.sidebar:
    render_sidebar_war_room()

# ==========================================
# 📍 預留給底層「觀察名單」傳送上來的隱形卡位槽
# ==========================================
top_pool_slot = st.empty()
# ==========================================
# 🏠 核心五大區塊
# ==========================================
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
    DATA_DIR = "./Goodinfo_Rankings"
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
import streamlit as st
import pandas as pd
import ui  # 👈 沒錯，換回您精心打造的 ui.py！
import left_panel
import data_engine
import page_b1  # 引入我們剛剛做的分頁模組

st.set_page_config(page_title="台股籌碼戰情室", page_icon="👑", layout="wide")

# ==========================================
# 1. 啟動 UI 與全域字典 (真正的高級螢火蟲與跑馬燈回來了！)
# ==========================================
ui.setup_all_effects()  # 👈 呼叫您原本的一鍵召喚視覺魔法
STOCK_DICT = data_engine.load_stock_dict()

# ==========================================
# 2. 側邊欄與 SPA 無縫導航選單 (不閃爍的核心)
# ==========================================
with st.sidebar:
    st.markdown("### 🧭 系統導航")
    current_page = st.radio(
        "選擇功能區塊", 
        ["市場總經與消息", "法人動向 (五大區塊)"], 
        label_visibility="collapsed"
    )
    
    st.markdown("<hr style='border-color: #334155; margin: 10px 0;'>", unsafe_allow_html=True)
    
    # 無論切換到哪個畫面，側邊戰情室永遠存在、永遠可用！
    left_panel.render_sidebar_war_room()

# ==========================================
# 3. 根據選單，動態載入畫面 (無縫切換，不再重整閃爍！)
# ==========================================
if current_page == "法人動向 (五大區塊)":
    # 呼叫 page_b1 的渲染函數，並把字典傳進去
    page_b1.render_page(STOCK_DICT)

elif current_page == "市場總經與消息":
    st.title("📰 市場消息與總經看板")
    st.write("（這裡未來可以呼叫您另一個 page_news.py）")
    
# ==========================================
# 🔒 區塊 2 專屬包廂鎖 (2-1 到 2-4 所有畫面渲染包進這裡)
# ==========================================
if current_page in ["all", "b2"]:
    import os
    import glob
    import pandas as pd

    # ==========================================
    # 🎯 區塊 2-1：外資 5 日買超 佔成交量比 追蹤 (穩定精確版)
    # ==========================================
    st.write("---")
    st.markdown("<div id='section-2-1'></div>", unsafe_allow_html=True)
    st.header("🎯 法人掃貨：外資 5 日 買超佔標的成交量")

    csv_pattern = os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")
    all_csv_files = glob.glob(csv_pattern)

    if not all_csv_files:
        st.warning("⚠️ 找不到任何包含『外資買超佔成交比』的 CSV 檔案。")
    else:
        all_csv_files.sort(reverse=True)
        target_files = all_csv_files[:10]
        base_df = None
        latest_day_today_data = {}

        for idx, f in enumerate(target_files):
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
                
                id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
                name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
                df = df.rename(columns={id_col: '代號', name_col: '名稱'})
                df['代號'] = df['代號'].astype(str).str.strip()
                df['名稱'] = df['名稱'].astype(str).str.strip()
                
                d_label = extract_date_from_name(f)[-4:]
                
                col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
                col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
                
                if idx == 0 and col_today:
                    latest_day_today_data = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
                
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
            
            latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}成交比%"
            if latest_col_name in csv_display.columns:
                csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
                
            def evaluate_continuity(row):
                today = latest_day_today_data.get(row['股票代號'], 0)
                base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
                
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
            
            st.info("動態 🔥 強延續 (買盤加速) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (強烈賣出)")
            
            c1, c2 = st.columns(2)
            show_etf = c1.checkbox("顯示 ETF", value=True, key="fo_etf_v9")
            show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="fo_bond_v9")
            
            mask = (csv_display['股票代號'].str.len() == 4)
            if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
            if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
            csv_display = csv_display[mask]
            
            cols = ["股票代號", "股票名稱", "今日短動態"] + [c for c in csv_display.columns if "成交比%" in c]
            csv_display = csv_display[cols]
            csv_display.index = range(1, len(csv_display) + 1)
            
            st.dataframe(csv_display, use_container_width=True)
            
            st.session_state['df_blk2_1'] = csv_display
            
        else:
            st.error("❌ 無法讀取外資買超數據，請檢查 CSV 欄位名稱是否包含『5日』與『成交』關鍵字。")


    # ==========================================
    # 🎯 區塊 2-2：投信 5 日買超 佔成交量比 追蹤 (穩定修復版)
    # ==========================================
    st.write("---")
    st.markdown("<div id='section-2-2'></div>", unsafe_allow_html=True)
    st.header("🎯 法人掃貨：投信 5 日 買超佔標的成交量")

    csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")
    all_files_sitc = glob.glob(csv_pattern_sitc)

    if not all_files_sitc:
        st.warning("⚠️ 找不到任何包含『投信買超佔成交比』的 CSV 檔案。")
    else:
        all_files_sitc.sort(reverse=True)
        target_files = all_files_sitc[:10]
        base_df = None
        latest_day_today_data_sitc = {}

        for idx, f in enumerate(target_files):
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
                
                id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
                name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
                df = df.rename(columns={id_col: '代號', name_col: '名稱'})
                df['代號'] = df['代號'].astype(str).str.strip()
                df['名稱'] = df['名稱'].astype(str).str.strip()
                
                d_label = extract_date_from_name(f)[-4:]
                
                col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
                col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
                
                if idx == 0 and col_today:
                    latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
                
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
            
            latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}成交比%"
            if latest_col_name in csv_display.columns:
                csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
                
            def evaluate_continuity_sitc(row):
                today = latest_day_today_data_sitc.get(row['股票代號'], 0)
                base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
                
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

            csv_display['今日短動態'] = csv_display.apply(evaluate_continuity_sitc, axis=1)
            
            c1, c2 = st.columns(2)
            show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_v9")
            show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_v9")
            
            mask = (csv_display['股票代號'].str.len() == 4)
            if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
            if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
            csv_display = csv_display[mask]
            
            cols = ["股票代號", "股票名稱", "今日短動態"] + [c for c in csv_display.columns if "成交比%" in c]
            csv_display = csv_display[cols]
            csv_display.index = range(1, len(csv_display) + 1)
            
            st.dataframe(csv_display, use_container_width=True)
            
            st.session_state['df_blk2_2'] = csv_display
        else:
            st.error("❌ 無法讀取投信買超數據，請確認 CSV 檔案內含有『5日』與『成交』欄位。")


    # ==========================================
    # 🎯 區塊 2-3：外資 5 日買超佔發行張數 追蹤 (穩定精確版)
    # ==========================================
    st.write("---")
    st.markdown("<div id='section-2-3'></div>", unsafe_allow_html=True)
    st.header("🎯 法人掃貨：外資 5 日 買超佔公司發行張數")

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
            
            history_cols = [c for c in csv_display.columns if "發行數%" in c]
            csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
            csv_display.index = range(1, len(csv_display) + 1)
            
            st.dataframe(csv_display, use_container_width=True) 
            st.session_state['df_blk2_3'] = csv_display
        else:
            st.error("❌ 無法讀取外資數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")


    # ==========================================
    # 🎯 區塊 2-4：投信 5 日買超佔發行張數 追蹤 (最終穩定版)
    # ==========================================
    st.write("---")
    st.markdown("<div id='section-2-4'></div>", unsafe_allow_html=True)
    st.header("🎯 法人掃貨：投信 5 日 買超佔公司發行張數")

    csv_pattern_sitc2 = os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")
    all_files_sitc2 = glob.glob(csv_pattern_sitc2)

    if not all_files_sitc2:
        st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
    else:
        sorted_files = sorted(all_files_sitc2, key=extract_date_from_name, reverse=True)[:10]
        base_df = None
        date_labels = []
        latest_day_today_data_sitc2 = {}

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
                    latest_day_today_data_sitc2 = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
                
                if col_5d in df.columns:
                    df_s = df[['代號', '名稱', col_5d]].copy()
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
            
            latest_5d_col = f"{date_labels[0]}發行數%"
            if latest_5d_col in csv_display.columns:
                csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
            
            def judge_today_alert_sitc2(row):
                stock_id = row['股票代號']
                val_5d = row.get(latest_5d_col, 0)
                val_today = latest_day_today_data_sitc2.get(stock_id, 0)
                
                if val_5d == 0 or val_5d == "未進榜":
                    return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
                
                if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
                elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
                return "🔄 今日量縮持平"

            csv_display['今日短動態'] = csv_display.apply(judge_today_alert_sitc2, axis=1)
            
            c1, c2 = st.columns(2)
            show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_final_v3")
            show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_final_v3")
            
            mask = (csv_display['股票代號'].str.len() == 4)
            if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
            if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
            csv_display = csv_display[mask]
            
            history_cols = [c for c in csv_display.columns if "發行數%" in c]
            csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
            csv_display.index = range(1, len(csv_display) + 1)
            
            st.dataframe(csv_display, use_container_width=True)
            
            st.session_state['df_blk2_4'] = csv_display
        else:
            st.error("❌ 無法讀取投信數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")
# ==========================================
# 🌟 區塊 3 專屬工具函數區 (必須放在 if 鎖外面)
# ==========================================
# 🛠️ 輔助函數：從檔名提取 8 碼日期
def extract_date_from_name(filename):
    match = re.search(r'(\d{8})', os.path.basename(filename))
    return match.group(1) if match else "00000000"

# 🛠️ 必備函數：強硬讀取法
def robust_read_csv_b3(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# 🛠️ 核心函數：讀取法人連續買超報告
@st.cache_data(ttl=60)
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
        df = robust_read_csv_b3(latest_file)
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
# 🔒 區塊 3 專屬包廂鎖 (畫面渲染包進這裡)
# ==========================================
# 🚨 修正點：將原本錯寫的 b1 改為 b3
if current_page in ["all", "b3"]:
    st.write("---")
    st.markdown("<div id='section-3'></div>", unsafe_allow_html=True)
    st.header("📅 法人連續買超")

    # ========================================================
    # 🚀 執行排程與備份邏輯
    # ========================================================
    with st.spinner("⏳ 載入連續買超數據中..."):
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
    h_day1, h_day2 = st.columns(2)
    with h_day1:
        st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🌐 外資最新 日連買</h3>", unsafe_allow_html=True)
    with h_day2:
        st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🏦 投信最新 日連買</h3>", unsafe_allow_html=True)

    st.markdown("<div style='color: white; margin-top: 5px; margin-bottom: 18px; font-size: 16px;'>💡 <b>日動態說明：</b> 🔥 波段認養 (連買10天以上)  ⚡ 買盤點火 (連買5~9天)  🆕 試單觀察 (連買1~4天)</div>", unsafe_allow_html=True)

    c_day1, c_day2 = st.columns(2)
    with c_day1:
        if not live_fo_day.empty:
            st.dataframe(live_fo_day, use_container_width=True)
        else:
            st.write("無資料")
        date_val = date_fo_day if date_fo_day else '無資料'
        st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>基準日: {date_val}</div>", unsafe_allow_html=True)

    with c_day2:
        if not live_it_day.empty:
            st.dataframe(live_it_day, use_container_width=True)
        else:
            st.write("無資料")
        date_val = date_it_day if date_it_day else '無資料'
        st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>基準日: {date_val}</div>", unsafe_allow_html=True)

    st.write("---") 

    # ========================================================
    # 🖼️ 視覺介面渲染 (最新單週區塊)
    # ========================================================
    h_wk1, h_wk2 = st.columns(2)
    with h_wk1:
        st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🌐 外資最新 週連買</h3>", unsafe_allow_html=True)
    with h_wk2:
        st.markdown(f"<h3 style='margin-top: 0; margin-bottom: 0;'>🏦 投信最新 週連買</h3>", unsafe_allow_html=True)

    st.markdown("<div style='color: white; margin-top: 5px; margin-bottom: 18px; font-size: 16px;'>💡 <b>週動態說明：</b> 👑 長線主控 (連買10週以上)  🚀 趨勢加溫 (連買5~9週)  🌱 週線發動 (連買1~4週)</div>", unsafe_allow_html=True)

    c_wk1, c_wk2 = st.columns(2)
    with c_wk1:
        if not live_fo_wk.empty:
            st.dataframe(live_fo_wk, use_container_width=True)
        else:
            st.write("無資料")
        date_val = date_fo_wk if date_fo_wk else '無資料'
        st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>基準日: {date_val}</div>", unsafe_allow_html=True)

    with c_wk2:
        if not live_it_wk.empty:
            st.dataframe(live_it_wk, use_container_width=True)
        else:
            st.write("無資料")
        date_val = date_it_wk if date_it_wk else '無資料'
        st.markdown(f"<div style='color: #00D2FF; font-size: 16px; margin-top: 1px;'>基準日: {date_val}</div>", unsafe_allow_html=True)

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
# 🌟 區塊 4 專屬工具函數區 (必須放在 if 鎖外面，確保全域可用)
# ==========================================
# 🛠️ 1. 強化版 CSV 讀取 (合併去重)
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

# 🛠️ 2. 特定籌碼數據讀取
def get_specific_margin_data(keyword):
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
        df = robust_read_csv_local(latest_file) # 修正為統一呼叫 _local 版本
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

# 🛠️ 3. 欄位清理與過濾
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

    sort_col = next((c for c in df.columns if '漲跌' in str(c) or '漲幅' in str(c)), None)
    if sort_col:
        df = df.rename(columns={sort_col: '漲跌幅%'}) 
        df['漲跌幅%'] = pd.to_numeric(df['漲跌幅%'], errors='coerce').fillna(0)
        df = df.sort_values(by='漲跌幅%', ascending=False)

    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

# 🛠️ 4. 表格渲染引擎
def render_styled_margin_table(clean_df):
    if clean_df.empty:
        st.warning("⚠️ 無相符資料")
        return
        
    display_df = clean_df.copy()
    change_col = next((c for c in display_df.columns if '漲跌' in str(c) or '漲幅' in str(c)), None)
    
    for col in display_df.columns:
        if col not in ['股票代號', '股票名稱']:
            try:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:.1f}".rstrip('0').rstrip('.') if pd.notna(x) and isinstance(x, (int, float)) else x
                )
            except: pass

    def style_row_by_price(row):
        styles = [''] * len(row)
        if change_col:
            try:
                orig_val = clean_df.loc[row.name, change_col]
                if float(orig_val) > 0:
                    return ['color: #db7093; font-weight: bold;'] * len(row)
            except: pass
        return styles

    styled_df = display_df.style.apply(style_row_by_price, axis=1)
    
    col_config = {
        "股票代號": st.column_config.TextColumn("股票代號", width=65),
        "股票名稱": st.column_config.TextColumn("股票名稱", width=80)
    }
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True, column_config=col_config)

# 🛠️ 5. 輔助函數：解析真實日期
def peek_data_date(keyword):
    _, msg = get_specific_margin_data(keyword)
    return re.search(r'\d{8}', msg).group(0) if re.search(r'\d{8}', msg) else "未知"

# 🛠️ 6. 軋空雷達運算引擎
def build_squeeze_radar():
    buy_pattern = os.path.join(DATA_DIR, "*三大法人買超佔成交比*.csv")
    margin_dec_pattern = os.path.join(DATA_DIR, "*融資減少幅度*.csv")       
    sbl_dec_pattern = os.path.join(DATA_DIR, "*借券賣出減少幅度*.csv")   
    short_inc_pattern = os.path.join(DATA_DIR, "*融券增加幅度*.csv")       
    
    buy_files = sorted(glob.glob(buy_pattern), reverse=True)
    margin_dec_files = sorted(glob.glob(margin_dec_pattern), reverse=True)
    sbl_dec_files = sorted(glob.glob(sbl_dec_pattern), reverse=True)
    short_inc_files = sorted(glob.glob(short_inc_pattern), reverse=True)
    
    if not buy_files:
        return pd.DataFrame(), "找不到三大法人買超檔案", "", False

    def get_date(filepath):
        match = re.search(r'(\d{8})', os.path.basename(filepath))
        return match.group(1) if match else ""
    
    dates = [
        get_date(buy_files[0]) if buy_files else "",
        get_date(margin_dec_files[0]) if margin_dec_files else "",
        get_date(sbl_dec_files[0]) if sbl_dec_files else "",
        get_date(short_inc_files[0]) if short_inc_files else ""
    ]
    
    valid_dates = [d for d in dates if d]
    is_sync = len(set(valid_dates)) == 1 if valid_dates else False
    display_date = f"{dates[0][:4]}/{dates[0][4:6]}/{dates[0][6:]}" if len(dates[0]) == 8 else dates[0]

    try:
        df_buy = robust_read_csv_local(buy_files[0])
        df_buy.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df_buy.columns]
        
        id_col = next((c for c in df_buy.columns if '代號' in c), df_buy.columns[1])
        name_col = next((c for c in df_buy.columns if '名稱' in c), df_buy.columns[2])
        df_buy = df_buy.rename(columns={id_col: '代號', name_col: '名稱'})
        df_buy['代號'] = df_buy['代號'].astype(str).str.strip()
        
        keep_cols = ['代號', '名稱', '成交', '漲跌價', '漲跌幅']
        for keyword in ['當日', '2日', '3日', '5日']:
            matched_cols = [c for c in df_buy.columns if keyword in c and '買賣超佔成交' in c]
            if matched_cols:
                keep_cols.append(matched_cols[0])
                
        keep_cols = list(dict.fromkeys(keep_cols)) 
        keep_cols = [c for c in keep_cols if c in df_buy.columns]
        df_squeeze = df_buy[keep_cols].copy()
        
        rename_mapping = {}      
        for col in df_squeeze.columns:
            if '買賣超佔成交' in col:
                new_name = col.replace('買賣超佔成交', '買佔成交')
                if '當日' in new_name:
                    new_name = new_name.replace('當日', '▼當日')
                rename_mapping[col] = new_name                
        df_squeeze = df_squeeze.rename(columns=rename_mapping)
        
        for col in df_squeeze.columns:
            if col not in ['代號', '名稱']:
                df_squeeze[col] = pd.to_numeric(df_squeeze[col].astype(str).str.replace('%', '', regex=False), errors='coerce')
                if pd.api.types.is_float_dtype(df_squeeze[col]):
                    df_squeeze[col] = df_squeeze[col].round(2)
        
        df_squeeze = df_squeeze[df_squeeze['漲跌幅'] >= 0]
        
    except Exception as e:
        return pd.DataFrame(), f"讀取買超母表失敗: {str(e)}", "", False

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

    df_squeeze['📉融資減'] = df_squeeze['代號'].apply(lambda x: "✔️" if x in margin_dec_ids else "")
    df_squeeze['📉借券減'] = df_squeeze['代號'].apply(lambda x: "✔️" if x in sbl_dec_ids else "")
    df_squeeze['📈融券增'] = df_squeeze['代號'].apply(lambda x: "✔️" if x in short_inc_ids else "")
    
    df_squeeze['軋空指數'] = 1 + (df_squeeze['📉融資減'] == "✔️").astype(int) + (df_squeeze['📉借券減'] == "✔️").astype(int) + (df_squeeze['📈融券增'] == "✔️").astype(int)
    df_squeeze = df_squeeze.sort_values(by=['軋空指數', '漲跌幅'], ascending=[False, False]).reset_index(drop=True)
    
    def get_squeeze_tag(score):
        if score == 4: return "💥 終極"
        elif score == 3: return "🚀 強軋"
        elif score == 2: return "🔥 點火"
        return "🔼 進駐"
        
    df_squeeze.insert(2, '軋空評估', df_squeeze['軋空指數'].apply(get_squeeze_tag))
    df_squeeze = df_squeeze.drop(columns=['軋空指數'])
    
    return df_squeeze, "Success", display_date, is_sync

# 🛠️ 7. 避險雷達運算引擎
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

# ==========================================
# 🔒 區塊 4 專屬包廂鎖 (4-1 到 4-5 所有畫面渲染包進這裡)
# ==========================================
if current_page in ["all", "b4"]:

    # ==================== 4-1 ====================
    st.write("---")
    st.markdown("<div id='section-4-1'></div>", unsafe_allow_html=True)
    date_41 = peek_data_date("融資減少幅度")
    st.markdown(f"### 🔄 區塊 4-1：融資減少動向 <span style='font-size: 0.6em; color: #00D2FF;'>({date_41})</span>", unsafe_allow_html=True)

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

    # ==================== 4-2 ====================
    st.write("---")
    st.markdown("<div id='section-4-2'></div>", unsafe_allow_html=True)
    date_42 = peek_data_date("借券賣出減少幅度")
    st.markdown(f"### 🔄 區塊 4-2：借券賣出減少動向 <span style='font-size: 0.6em; color: #00D2FF;'>({date_42})</span>", unsafe_allow_html=True)

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

    # ==================== 4-3 ====================
    st.write("---")
    st.markdown("<div id='section-4-3'></div>", unsafe_allow_html=True)
    date_43 = peek_data_date("融券增加幅度")
    st.markdown(f"### 🔄 區塊 4-3：融券增加動向 <span style='font-size: 0.6em; color: #00D2FF;'>({date_43})</span>", unsafe_allow_html=True)

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

    # ==================== 4-4 ====================
    st.write("---")
    st.markdown("<div id='section-4-4'></div>", unsafe_allow_html=True)

    with st.spinner("⏳ 正在掃描全市場軋空名單..."):
        df_squeeze_radar, msg, radar_date, is_radar_sync = build_squeeze_radar()

    header_html = "🚀 區塊 4-4：可能軋空雷達 "
    if radar_date:
        if is_radar_sync:
            header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span>"
        else:
            header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span> <span style='color: #ffa500; font-size: 0.5em;'>⏳籌碼待更新</span>"

    st.markdown(f"<h2>{header_html}</h2>", unsafe_allow_html=True)
    st.write("💡 觀察法人們買超，且伴隨融資退場、借券回補或融券逆勢增加的潛在軋空標的。")

    if not df_squeeze_radar.empty:
        show_all = st.checkbox("顯示榜內被法人買超的上漲標的，但籌碼未見軋空特徵", value=False)
        
        if not show_all:
            df_squeeze_radar = df_squeeze_radar[df_squeeze_radar['軋空評估'].str.contains("💥|🚀|🔥", regex=True)]

        if df_squeeze_radar.empty:
            st.success("🎉 目前沒有同時出現法人買超與軋空特徵的強勢名單！")
        else:
            df_squeeze_radar = df_squeeze_radar.reset_index(drop=True)
            df_squeeze_radar.insert(0, '索引', range(1, len(df_squeeze_radar) + 1))
            
            def style_table(df):
                try: styler = df.style.hide(axis='index')
                except: styler = df.style.hide_index()
                
                def highlight_squeeze(row):
                    styles = []
                    for col_name in row.index:
                        base_style = 'background-color: #262730;'
                        if col_name in ['成交', '漲跌價', '漲跌幅']:
                            styles.append(base_style + ' color: #ff4b4b;')
                        else:
                            styles.append(base_style + ' color: #e0e0e0;')
                    return styles
                
                styler = styler.apply(highlight_squeeze, axis=1)
                
                border_css = '1px solid #808495'
                styler = styler.set_table_styles([
                    {'selector': 'table', 'props': [('width', '100%'), ('border-collapse', 'collapse'), ('font-family', 'sans-serif'), ('font-size', '13px')]},
                    {'selector': 'th', 'props': [('background-color', '#1e1e24'), ('color', '#ffffff'), ('font-weight', 'normal'), ('border', border_css), ('padding', '6px 4px'), ('text-align', 'center'), ('position', 'sticky'), ('top', '0'), ('z-index', '1')]},
                    {'selector': 'td', 'props': [('border', border_css), ('padding', '4px'), ('text-align', 'center'), ('transition', 'all 0.2s ease-in-out')]},
                    {'selector': 'tbody tr:hover td', 'props': [('background-color', 'rgba(4, 8, 20, 0.85) !important'), ('text-shadow', '0 0 8px rgba(255, 255, 255, 0.5) !important')]}
                ])
                
                num_cols = df.select_dtypes(include=['number']).columns.tolist()
                if '索引' in num_cols: num_cols.remove('索引')
                styler = styler.format({col: "{:.2f}" for col in num_cols})
                return styler.to_html()

            html_table = style_table(df_squeeze_radar)
            
            scrollable_div = f"""<div style="max-height: 420px; overflow-y: auto; border: 1px solid #808495; border-radius: 5px;">{html_table}</div>"""
            st.markdown(scrollable_div, unsafe_allow_html=True)
    else:
        st.warning(f"軋空雷達載入失敗：{msg}")

# ==================== 4-5 ====================
    st.write("---")
    st.markdown("<div id='section-4-5'></div>", unsafe_allow_html=True)

    with st.spinner("⏳ 正在掃描全市場避險名單..."):
        df_risk_radar, msg, radar_date, is_radar_sync = build_risk_radar()

    header_html = "🚨 區塊 4-5：短線套牢名單 "
    if radar_date:
        if is_radar_sync:
            header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span>"
        else:
            header_html += f"<span style='color: #00D2FF; font-size: 0.7em;'>({radar_date})</span> <span style='color: #ffa500; font-size: 0.5em;'>⏳融券資待更新</span>"

    st.markdown(f"<h2>{header_html}</h2>", unsafe_allow_html=True)
    st.write("💡 法人們賣超，且股價下跌融資套牢或借券增加的籌碼惡化標的，不過我們似乎觀察倒若當日成交轉正有望回溫或是反彈...")

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
                try: styler = df.style.hide(axis='index')
                except: styler = df.style.hide_index()
                
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
                    return styles  # 🌟 致命 Bug 修復：將這行往左退一格，確保檢查完所有欄位才回傳！
                
                styler = styler.apply(highlight_risk, axis=1)
                
                border_css = '1px solid #808495'
                styler = styler.set_table_styles([
                    {'selector': 'table', 'props': [('width', '100%'), ('border-collapse', 'collapse'), ('font-family', 'sans-serif'), ('font-size', '13px')]},
                    {'selector': 'th', 'props': [('background-color', '#1e1e24'), ('color', '#ffffff'), ('font-weight', 'normal'), ('border', border_css), ('padding', '6px 4px'), ('text-align', 'center'), ('position', 'sticky'), ('top', '0'), ('z-index', '1')]},
                    {'selector': 'td', 'props': [('border', border_css), ('padding', '4px'), ('text-align', 'center'), ('transition', 'all 0.2s ease-in-out')]},
                    {'selector': 'tbody tr:hover td', 'props': [('background-color', 'rgba(4, 8, 20, 0.85) !important'), ('text-shadow', '0 0 8px rgba(255, 255, 255, 0.5) !important')]}
                ])
                
                num_cols = df.select_dtypes(include=['number']).columns.tolist()
                if '索引' in num_cols: num_cols.remove('索引')
                styler = styler.format({col: "{:.2f}" for col in num_cols})
                return styler.to_html()

            html_table = style_table(df_risk_radar)
            
            scrollable_div = f"""<div style="max-height: 420px; overflow-y: auto; border: 1px solid #808495; border-radius: 5px;">{html_table}</div>"""
            st.markdown(scrollable_div, unsafe_allow_html=True)
    else:
        st.warning(f"避險雷達載入失敗：{msg}")
# ==========================================
# 💰 區塊 5：大股東動向 (四層級對稱系統 + 4碼日期完美排版)
# ==========================================

def apply_b5_market_filters(df, show_etf, show_bond):
    if df is None or df.empty: return df
    is_etf = df['股票代號'].astype(str).str.startswith('00')
    is_bond = df['股票代號'].astype(str).str.endswith('B') | df['股票名稱'].astype(str).str.contains('債')
    mask = pd.Series(True, index=df.index)
    if not show_etf: mask = mask & ~(is_etf & ~is_bond)
    if not show_bond: mask = mask & ~is_bond
    return df[mask]

def process_major_shareholders(target_level):
    """
    通用大戶資料產生器 (終極容錯防呆版 - 支援多種編碼與動態欄位對接)
    """
    import os, glob, re
    import pandas as pd
    
    # 1. 不分大小寫抓取所有 CSV (避免附檔名變成 .CSV 抓不到)
    files = []
    for ext in ('*.csv', '*.CSV'):
        files.extend(glob.glob(os.path.join(DATA_DIR, f"*大股東{ext}")))
    if not files: return pd.DataFrame()
    
    groups = {}
    for f in files:
        m = re.search(r'(\d{8})', os.path.basename(f))
        key = m.group(1) if m else "UNKNOWN"
        groups.setdefault(key, []).append(f)
    
    merged, all_dates_4 = [], []
    # 建立彈性數字 (例如傳入 '1千'，就會同時尋找 '1千' 或 '1000')
    target_num = target_level.replace('1千', '1000').replace('千', '000')

    for prefix, fs in sorted(groups.items(), reverse=True):
        chunks = []
        detected_date = None
        
        for f in fs:
            df = None
            # 2. 自動嘗試多種編碼，解決 Excel 另存新檔造成的亂碼報錯 (無聲崩潰的主因)
            for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
                try:
                    df = pd.read_csv(f, encoding=enc)
                    break # 成功讀取就跳出編碼嘗試
                except: pass
            
            if df is None or df.empty: continue
            
            # 3. 終極清洗：拔除所有隱形空白、換行符號與 BOM
            df.columns = [re.sub(r'\s+', '', str(c)).replace('\ufeff', '') for c in df.columns]
            
            c_code = next((c for c in df.columns if '代號' in c or '代碼' in c), None)
            c_name = next((c for c in df.columns if '名稱' in c), None)
            
            # 4. 高容錯比對 (容許 '1千' 或 '1000', 容許 '%' 或 '比例')
            c_abs = next((c for c in df.columns if (target_level in c or target_num in c) and ('%' in c or '比例' in c) and '增減' not in c and '差' not in c), None)
            c_delta = next((c for c in df.columns if (target_level in c or target_num in c) and ('增減' in c or '差' in c)), None)
            c_date = next((c for c in df.columns if '日期' in c), None)
            
            if not all([c_code, c_name, c_abs, c_delta]): continue
            
            try:
                df['股票代號'] = df[c_code].astype(str).str.extract(r'(\d+)', expand=False)
                df['股票名稱'] = df[c_name].astype(str).str.strip()
                df['持股%'] = pd.to_numeric(df[c_abs].astype(str).str.replace('%', ''), errors='coerce')
                df['增減%'] = pd.to_numeric(df[c_delta].astype(str).str.replace('+', '').str.replace('%', ''), errors='coerce')
                
                if detected_date is None and c_date and not df[c_date].dropna().empty:
                    raw_date = str(df[c_date].dropna().iloc[0]).replace('/', '').replace('-', '').strip()
                    detected_date = raw_date[-4:] if len(raw_date) >= 4 else prefix[-4:]
                
                chunks.append(df[['股票代號', '股票名稱', '持股%', '增減%']].dropna(subset=['股票代號']))
            except: continue
        
        if chunks:
            # 合併同日期的分批資料 (1-300, 301-600...)
            comb = pd.concat(chunks, ignore_index=True).groupby(['股票代號', '股票名稱']).max().reset_index()
            date_4 = detected_date if detected_date else prefix[-4:]
            if date_4 not in all_dates_4: all_dates_4.append(date_4)
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
        
        delta_cols = [f"DELTA_{d}" for d in sorted_dates_4 if f"DELTA_{d}" in master.columns]
        master['▼6周增減'] = master[delta_cols[:6]].sum(axis=1, min_count=1)
        
        rename_dict = {}
        cols_order = ['股票代號', '股票名稱', '週動態', '▼6周增減']
        
        if f"{latest_date_4}持有%" in master.columns: cols_order.append(f"{latest_date_4}持有%")
            
        for i, d in enumerate(sorted_dates_4):
            original_delta_col = f"DELTA_{d}"
            if original_delta_col in master.columns:
                new_delta_name = f"▼{d}" if i == 0 else f"{d}"
                rename_dict[original_delta_col] = new_delta_name
                cols_order.append(new_delta_name)
                
        master = master.rename(columns=rename_dict)
        final_df = master[[c for c in cols_order if c in master.columns]]
        final_df = final_df.sort_values(by=f"▼{latest_date_4}", ascending=False)
        return final_df
        
    return pd.DataFrame()


# ----------------------------------------------------
# 🔒 區塊 5 專屬包廂鎖
# ----------------------------------------------------
if current_page in ["all", "b5"]:
    st.write("---")


    st.markdown("<div id='section-5'></div>", unsafe_allow_html=True)
    
    # ...(以下保留你原本區塊5的 UI 渲染與 Tab 分頁邏輯)...
    
    # 0. 預先掃描最新檔案日期以供標題基準日顯示
    import glob, os, re
    global_latest_date = "0605"
    all_b5_raw_files = glob.glob(os.path.join(DATA_DIR, "*神秘金字塔*")) + glob.glob(os.path.join(DATA_DIR, "*大股東*"))
    for f in all_b5_raw_files:
        match = re.search(r'(\d{8})', os.path.basename(f))
        if match and match.group(1).startswith("202"):
            if match.group(1)[4:] > global_latest_date:
                global_latest_date = match.group(1)[4:]

    # 科技風漸層橫幅標題
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; 
                border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
        <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
            💰 區塊 5：大股東動向
        </h2>
        <div style='font-size:13px; color:#00D2FF; font-weight:500; margin-top:8px;'>
            基準日 : {global_latest_date[:2]}/{global_latest_date[2:]} 
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 篩選器
    filter_c1, filter_c2, _ = st.columns([2, 3, 5])
    show_etf = filter_c1.checkbox("顯示 ETF", value=True, key="b5_global_etf")
    show_bond = filter_c2.checkbox("顯示 債券 / 債券 ETF", value=True, key="b5_global_bond")

    # 擴充為 5 個 Tab
    #tab_1000, tab_800, tab_600, tab_400, tab_sync = st.tabs([
        #"🔹 1000張大戶", "🔹 800張大戶", "🔹 600張大戶", "🔹 400張大戶", "🔹 雙引擎共振"
    #])
    # 🔥 擴充後方分頁，加入「長短線共振」
    tab_1000, tab_800, tab_600, tab_400, tab_resonance, tab_long_short = st.tabs([
        "🔹 1000張大戶", 
        "🔹 800張大戶", 
        "🔹 600張大戶", 
        "🔹 400張大戶", 
        "🔹 雙引擎共振",
        "🔹 長短線共振"  # 👈 全新新增
    ])



    filtered_1000_df, filtered_800_df, filtered_600_df, filtered_400_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
                        df['股票代號'] = df['股票代號/名稱'].astype(str).str.extract(r'(\d+)', expand=False)# ✅ 修正觀察名單讀取不到
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
    with tab_resonance:
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

                st.success(f"這是強烈的大腿訊號！共有 **{len(sync)}** 檔標的出現大腿雷達共振 (千張與四百張同時增加)，值得好好研究！")
                st.dataframe(sync, use_container_width=True, hide_index=True)
            else:
                st.info("⚪ 最新一週目前沒有「千張與四百張」同時增加的共振標的。")
        else:
            st.warning("⚠️ 請確保 1000 張與 400 張資料皆有成功載入，才能啟動共振掃描引擎。")

    # ==================== Tab 6: 🔹 長短線共振 ====================
    with tab_long_short:
        st.markdown("#### 長短線大戶籌碼雙向共振榜")
        st.caption("💡 核心邏輯：1000張大戶波段吸籌（6周增）且本週加碼（最新週增），同時聯手 400張短線大戶波段與本週皆同步加碼的強勢共振標的。")
        
        # 直接使用前方已計算好的 DataFrame (無需再讀取 CSV)
        if not filtered_1000_df.empty and not filtered_400_df.empty:
            df_1k = filtered_1000_df.copy()
            df_400 = filtered_400_df.copy()
            
            # 1. 動態尋找「最新一週」的欄位名稱 (找尋包含 '▼' 且不是 '▼6周' 的直行，例如 '▼0618')
            latest_col_1k = next((c for c in df_1k.columns if c.startswith('▼') and '6周' not in c), None)
            latest_col_400 = next((c for c in df_400.columns if c.startswith('▼') and '6周' not in c), None)
            
            if latest_col_1k and latest_col_400 and '▼6周增減' in df_1k.columns and '▼6周增減' in df_400.columns:
                
                # 2. 執行 1000 張大戶過濾：▼6周增減 > 0 且 最新週 > 0
                cond_1k = (pd.to_numeric(df_1k['▼6周增減'], errors='coerce').fillna(0) > 0) & \
                          (pd.to_numeric(df_1k[latest_col_1k], errors='coerce').fillna(0) > 0)
                
                base_df = df_1k[cond_1k][['股票代號', '股票名稱', '▼6周增減', latest_col_1k]].copy()
                base_df = base_df.rename(columns={'▼6周增減': '6周增減(一千)', latest_col_1k: f"{latest_col_1k}(一千)"})
                
                # 3. 執行 400 張中實戶過濾：▼6周增減 > 0 且 最新週 > 0
                cond_400 = (pd.to_numeric(df_400['▼6周增減'], errors='coerce').fillna(0) > 0) & \
                           (pd.to_numeric(df_400[latest_col_400], errors='coerce').fillna(0) > 0)
                
                df_400_filtered = df_400[cond_400][['股票代號', '▼6周增減', latest_col_400]].copy()
                df_400_filtered = df_400_filtered.rename(columns={'▼6周增減': '6周增減(四百)', latest_col_400: f"{latest_col_400}(四百)"})
                
                # 4. 🚀 核心靈魂：Inner Join 交集 (只保留兩邊都過關的資優生)
                resonance_df = pd.merge(base_df, df_400_filtered, on='股票代號', how='inner')
                
                if not resonance_df.empty:
                    # 5. 順手把 600 張與 800 張的數據拉進來當作觀察輔助 (用 Left Join，不強制大於0)
                    if not filtered_600_df.empty:
                        df_600 = filtered_600_df.copy()
                        latest_col_600 = next((c for c in df_600.columns if c.startswith('▼') and '6周' not in c), None)
                        if latest_col_600 and '▼6周增減' in df_600.columns:
                            sub_600 = df_600[['股票代號', '▼6周增減', latest_col_600]].copy()
                            sub_600 = sub_600.rename(columns={'▼6周增減': '6周增減(六百)', latest_col_600: f"{latest_col_600}(六百)"})
                            resonance_df = pd.merge(resonance_df, sub_600, on='股票代號', how='left')
                            
                    if not filtered_800_df.empty:
                        df_800 = filtered_800_df.copy()
                        latest_col_800 = next((c for c in df_800.columns if c.startswith('▼') and '6周' not in c), None)
                        if latest_col_800 and '▼6周增減' in df_800.columns:
                            sub_800 = df_800[['股票代號', '▼6周增減', latest_col_800]].copy()
                            sub_800 = sub_800.rename(columns={'▼6周增減': '6周增減(八百)', latest_col_800: f"{latest_col_800}(八百)"})
                            resonance_df = pd.merge(resonance_df, sub_800, on='股票代號', how='left')

                    # 把沒有資料的欄位優雅地補上 None
                    resonance_df = resonance_df.fillna('None')
                    
                    # 🧹 終極去重機制：避免金融股/特別股因代號重複，在 Merge 時引發的交錯相乘繁殖
                    if '股票名稱' in resonance_df.columns:
                        resonance_df = resonance_df.drop_duplicates(subset=['股票代號', '股票名稱'], keep='first')
                    else:
                        resonance_df = resonance_df.drop_duplicates(subset=['股票代號'], keep='first')
                    
                    st.success(f"🔥 極度嚴苛過濾！找到了 **{len(resonance_df)}** 檔 1000張與400張「長線(6周)與短線(最新週)」同步雙向做多的超級共振標的！")
                    st.dataframe(resonance_df, use_container_width=True, hide_index=True)

                    # ==========================================
                    # 🧩 區塊擴充：長短線大戶雙向共振榜 - 產業資金聚落 (Treemap)
                    # ==========================================
                    st.write("---")
                    st.markdown("### 🧩 大股東共振資金聚落板塊")
                    st.caption("這是過濾出長短線大戶籌碼雙向共名單(1000張與400張大戶波段吸籌且本週持續加碼)轉換為產業面積，一眼看出大戶同步做多的核心產業 (我們排除 ETF/債券)。如果能找出法人持股也在同步增加作多的標的，勝率應該能高出許多呢！")
                    
                    if 'STOCK_DICT' in globals() and STOCK_DICT:
                        
                        # 動態取得最新週次的欄位名稱 (例如：'▼0618(一千)')
                        target_color_col = f"{latest_col_1k}(一千)"
                        
                        # ==========================================
                        # 🚀 雙層連動控制 UI (排序依據 + 顯示數量)
                        # ==========================================
                        st.write("")
                        c_opt, c_topn = st.columns([3, 1.5])
                        
                        with c_opt:
                            b5_filter = st.radio(
                                "設定排序依據：", 
                                ["全部顯示 (預設)", "依 6周增減(一千) 排序", f"依 {target_color_col} 排序"], 
                                horizontal=True, 
                                key="b5_treemap_filter"
                            )
                        with c_topn:
                            top_n = st.selectbox(
                                "顯示檔數：", 
                                [10, 30, 50, 100], 
                                index=2, 
                                key="b5_top_n",
                                help="當選擇「全部顯示」時，此數量設定不會生效。"
                            )

                        # 複製一份繪圖用 DataFrame
                        tm_b5_df = resonance_df.copy()
                        
                        # ==========================================
                        # 💡 執行資料過濾與排序邏輯
                        # ==========================================
                        # 1. 確保所有核心數值欄位皆清洗為純數字，供排序與二次格式化使用
                        tm_b5_df['數值_6周'] = pd.to_numeric(tm_b5_df['6周增減(一千)'].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0.0)
                        tm_b5_df['數值_最新週'] = pd.to_numeric(tm_b5_df[target_color_col].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0.0)
                        tm_b5_df['數值_400_最新'] = pd.to_numeric(tm_b5_df[f"{latest_col_400}(四百)"].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0.0)
                        tm_b5_df['數值_400_6周'] = pd.to_numeric(tm_b5_df['6周增減(四百)'].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0.0)

                        # 2. 根據讀者選擇的選項進行過濾
                        if "6周增減" in b5_filter:
                            tm_b5_df = tm_b5_df.nlargest(top_n, '數值_6周')
                        elif "依 ▼" in b5_filter or "依 最新" in b5_filter or target_color_col in b5_filter:
                            tm_b5_df = tm_b5_df.nlargest(top_n, '數值_最新週')
                        
                        # ==========================================
                        # 🎨 產業配對與 Treemap 繪製
                        # ==========================================
                        # 配對產業別 (剔除 ETF / 債券)
                        tm_b5_df['產業別'] = tm_b5_df['股票代號'].astype(str).apply(
                            lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他")
                        )
                        tm_b5_df['產業別'] = tm_b5_df['產業別'].replace('', 'ETF / 債券 / 其他')
                        
                        # 擷取即將被剔除的 ETF / 債券清單
                        b5_excluded_etfs = tm_b5_df[tm_b5_df['產業別'] == 'ETF / 債券 / 其他'].sort_values(by='股票代號').copy()
                        
                        # 剔除 ETF，保留一般產業畫圖
                        tm_b5_df = tm_b5_df[tm_b5_df['產業別'] != 'ETF / 債券 / 其他']
                        
                        if not tm_b5_df.empty:
                            # 面積權重固定為 1
                            tm_b5_df['計數'] = 1 
                            today_counts = tm_b5_df['產業別'].value_counts().to_dict()

                            def format_industry_label(industry):
                                t_count = today_counts.get(industry, 0)
                                return f"<b>{industry}</b><br><span style='font-size: 13px;'>{t_count}檔</span>"
                            tm_b5_df['產業別'] = tm_b5_df['產業別'].apply(format_industry_label)

                            # 繪圖熱力數值一律使用「最新一週 1000張增減」來上色
                            tm_b5_df['熱力數值'] = tm_b5_df['數值_最新週']

                            # 🚀 修正 1：建立四個乾淨的格式化欄位（強制指定兩位小數），徹底根除長尾小數點
                            tm_b5_df['千張週增減_格式化'] = tm_b5_df['數值_最新週'].apply(lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%")
                            tm_b5_df['6周一千_格式化'] = tm_b5_df['數值_6周'].apply(lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%")
                            tm_b5_df['四百最新_格式化'] = tm_b5_df['數值_400_最新'].apply(lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%")
                            tm_b5_df['6周四百_格式化'] = tm_b5_df['數值_400_6周'].apply(lambda x: f"+{x:.2f}%" if x > 0 else f"{x:.2f}%")

                            # 🚀 修正 2：依據單選按鈕動態切換便籤文字 (6周排序顯示6周累積，其餘顯示週增)
                            def format_clean_stock_label(row):
                                name = str(row.get('股票名稱', ''))
                                if "6周增減" in b5_filter:
                                    val_str = row.get('6周一千_格式化', '0.00%')
                                    return f"<b>{name}</b><br><span style='font-size: 11px; color: #E5E7EB;'>6周: {val_str}</span>"
                                else:
                                    d_str = row.get('千張週增減_格式化', '0.00%')
                                    return f"<b>{name}</b><br><span style='font-size: 11px; color: #E5E7EB;'>大戶週增 {d_str}</span>"
                                    
                            tm_b5_df['顯示名稱'] = tm_b5_df.apply(format_clean_stock_label, axis=1)

                            # 將格式化完成的欄位送進 hover_columns 內
                            hover_columns = [
                                '股票代號', 
                                '千張週增減_格式化', 
                                '6周一千_格式化', 
                                '四百最新_格式化', 
                                '6周四百_格式化'
                            ]

                            # 定義紅綠漸層色階
                            custom_continuous_scale = [
                                [0.0, "rgba(0, 230, 118, 0.85)"],  
                                [0.5, "rgba(30, 41, 59, 0.95)"],   
                                [1.0, "rgba(255, 75, 75, 0.85)"]   
                            ]

                            import plotly.express as px
                            fig = px.treemap(
                                tm_b5_df,
                                path=[px.Constant("🔥 大股東雙向共振池"), '產業別', '顯示名稱'], 
                                values='計數',
                                color='熱力數值', 
                                color_continuous_scale=custom_continuous_scale, 
                                color_continuous_midpoint=0, 
                                hover_data=hover_columns
                            )
                            fig.update_coloraxes(showscale=False)

                            fig.update_traces(
                                textinfo="label", 
                                textfont=dict(color="white", size=14),
                                marker=dict(line=dict(color='#0B0F19', width=2), pad=dict(t=35, l=10, r=10, b=10)),
                                hovertemplate=(
                                    '<b>%{label}</b><br>'
                                    '股票代號: %{customdata[0]}<br>'
                                    '千張大戶本週: <b>%{customdata[1]}</b><br>'
                                    '千張大戶6週累積: <b>%{customdata[2]}</b><br>' # 🚀 修正點：改用格式化欄位，杜絕破圖
                                    '----------------<br>'
                                    '400張大戶本週: %{customdata[3]}<br>'
                                    '400張大戶6週累積: <b>%{customdata[4]}</b><br>' # 🚀 修正點：改用格式化欄位，杜絕破圖
                                    '<extra></extra>' 
                                )
                            )
                            
                            fig.update_layout(
                                margin=dict(t=30, l=0, r=0, b=0),
                                height=650, 
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="sans-serif") 
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                        else:
                            st.info("⚪ 目前過濾後的名單中沒有一般產業的股票。")

                        # ==========================================
                        # 🗑️ 在下方顯示被剔除的 ETF / 債券 / 特別股清單 (單行 HTML + 格式化連動)
                        # ==========================================
                        if not b5_excluded_etfs.empty:
                            st.write("")
                            st.markdown("##### 🗑️ 本次已剔除的非一般產業 (ETF / 特別股 / 債券)")
                            st.caption("以下標的已符合大戶共振與排序條件，但因非一般企業已從上方產業聚落中剔除。💡 **游標懸停可查看大戶持股明細。**")
                            
                            tags_html = ""
                            import html
                            
                            # 🚀 修正 1：建立一個安全轉換單一數字的函數，取代會報錯的 pd.to_numeric(...).fillna()
                            def safe_float_convert(val):
                                try:
                                    return float(str(val).replace('+', '').replace('%', '').replace(',', '').strip())
                                except:
                                    return 0.0
                            
                            for _, r in b5_excluded_etfs.iterrows():
                                name = str(r.get('股票名稱', ''))
                                sid = str(r.get('股票代號', ''))
                                
                                # 🚀 修正 2：使用安全轉換函數處理數值
                                num_6w = safe_float_convert(r.get('6周增減(一千)', '0'))
                                num_w = safe_float_convert(r.get(target_color_col, '0'))
                                num_400_w = safe_float_convert(r.get(f"{latest_col_400}(四百)", '0'))
                                num_400_6w = safe_float_convert(r.get('6周增減(四百)', '0'))
                                
                                safe_name = html.escape(name, quote=True)
                                safe_sid = html.escape(sid, quote=True)
                                
                                # 最下方膠囊標籤的文字，也跟著單選按鈕同步切換顯示模式！
                                if "6周增減" in b5_filter:
                                    d_val = num_6w
                                    label_text = "6周"
                                else:
                                    d_val = num_w
                                    label_text = "千張"
                                
                                if d_val > 0:
                                    bg_color = "rgba(255, 75, 75, 0.15)"   
                                    border_color = "rgba(255, 75, 75, 0.4)" 
                                    text_color = "#FF4B4B"                  
                                    d_str = f"+{d_val:.2f}%"
                                elif d_val < 0:
                                    bg_color = "rgba(0, 230, 118, 0.15)"   
                                    border_color = "rgba(0, 230, 118, 0.4)" 
                                    text_color = "#00E676"                  
                                    d_str = f"{d_val:.2f}%"
                                else:
                                    bg_color = "rgba(30, 41, 59, 0.6)"     
                                    border_color = "#334155"
                                    text_color = "#94A3B8"
                                    d_str = "0.00%"
                                    
                                # 🚀 修正 3：修復換行符號錯字 (把 &n#10; 修正為 &#10;)
                                tooltip_text = (
                                    f"【{safe_name}】&#10;"
                                    f"股票代號: {safe_sid}&#10;"
                                    f"千張大戶本週: {num_w:+.2f}%&#10;"
                                    f"千張大戶6週累積: {num_6w:+.2f}%&#10;"
                                    f"----------------&#10;"
                                    f"400張中實戶本週: {num_400_w:+.2f}%&#10;"
                                    f"400張中實戶6週累積: {num_400_6w:+.2f}%"
                                )
                                
                                tags_html += f"<div title=\"{tooltip_text}\" style=\"background-color: {bg_color}; color: #E2E8F0; border: 1px solid {border_color}; padding: 6px 14px; border-radius: 20px; margin: 5px; display: inline-flex; align-items: center; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); cursor: help; transition: transform 0.2s;\">{safe_name} ({safe_sid}) <span style='color: {text_color}; font-weight: bold; margin-left: 8px;'>{label_text} {d_str}</span></div>"
                            
                            st.markdown(f"<div style='margin-top: 5px; line-height: 2.4;'>{tags_html}</div>", unsafe_allow_html=True)
                    else:
                        st.info("⚪ 找不到產業字典，無法繪製產業板塊圖。")

                else:
                    st.info("⚪ 條件嚴苛，本週完全沒有 1000張與400張「長短線皆同步雙增」的標的。")
            else:
                st.error("⚠️ 資料表欄位解析失敗，請確認前方大戶表中包含 '▼6周增減' 與最新日期 (如 '▼0618') 欄位。")
        else:
            st.warning("⚠️ 請確認前方 1000張 與 400張 大戶分頁有成功載入並產生資料，才能啟動共振掃描。")
            
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
    
    st.markdown("### 🎣 區塊 6：鉅額交易動向", unsafe_allow_html=True)
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
# 🎭 幕後無縫換頁引擎 (先定義成函數，供全站各區塊的 st.stop() 呼叫)切換頁避免卡死
# ==========================================
def render_proxy_buttons():
    """將隱藏按鈕打包成函數，確保在 st.stop() 切斷程式前能被提早渲染"""
    def change_page(page_name):
        st.session_state.current_page = page_name
        st.query_params["page"] = page_name 

    with st.container():
        st.button("NavToNews", on_click=change_page, args=("news",))
        st.button("NavToPool", on_click=change_page, args=("pool",))
        st.button("NavToB1", on_click=change_page, args=("b1",))
        st.button("NavToB2", on_click=change_page, args=("b2",))
        st.button("NavToB3", on_click=change_page, args=("b3",))
        st.button("NavToB4", on_click=change_page, args=("b4",))
        st.button("NavToB5", on_click=change_page, args=("b5",))
        st.button("NavToB6", on_click=change_page, args=("b6",))
        st.button("NavToContact", on_click=change_page, args=("contact",))



# ==========================================↓↓↓
# 🔒 觀察名單專屬包廂鎖 頂級核心數據分析觀察名單 (🚨 必須放在計分部分檔案最下方！)
# ==========================================
if current_page in ["all", "pool"]:
    
    # 🧙 核心修正：加上 .container()！
    # 這樣才能把「標題」跟「下方的內容」全部打包裝在一起，避免標題被覆蓋消失！
    with top_pool_slot.container():
        st.write("---")
        st.markdown("<div id='section-top-pool'></div>", unsafe_allow_html=True)

        df_b5_1000 = get_df_safe('df_blk5_1000')
        df_b5_400 = get_df_safe('df_blk5')
        
        # ==========================================
        # 🚀 修正 1：統一並簡化所有區塊的「最新日期」掃描邏輯
        # ==========================================
        all_files = glob.glob(os.path.join(DATA_DIR, "*"))
        anchor_date_str = "00000000"
        d_b1_inst, d_b23_chip, d_b4_margin, d_b5_share = "00000000", "00000000", "00000000", "00000000"
        
        if all_files: # 防呆：確保資料夾內真的有檔案
            for f in all_files:
                filename = os.path.basename(f)
                match = re.search(r'(202\d{5})', filename)
                if match:
                    file_date = match.group(1)
                    # 總檔期基準
                    if file_date > anchor_date_str: anchor_date_str = file_date
                    
                    # 區塊 1
                    if "持股排名變化" in filename or "JSON_History" in filename:
                        if file_date > d_b1_inst: d_b1_inst = file_date
                    # 區塊 2 & 3
                    elif "佔成交比" in filename or "連買" in filename or "買賣超" in filename:
                        if file_date > d_b23_chip: d_b23_chip = file_date
                    # 區塊 4
                    elif "融資" in filename or "融券" in filename or "借券" in filename or "資券" in filename:
                        if file_date > d_b4_margin: d_b4_margin = file_date
                    # 區塊 5
                    elif "大股東" in filename or "神秘金字塔" in filename or "集保" in filename:
                        if file_date > d_b5_share: d_b5_share = file_date

        # ==========================================
        # 🚀 日期格式化工具與動態標題渲染
        # ==========================================
        def fmt_d(date_str):
            if date_str and len(date_str) >= 8 and date_str != "00000000":
                return f"{date_str[4:6]}/{date_str[6:8]}"
            return "--/--"

        # 👇 渲染您專屬的科技風漸層橫幅標題
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                    border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; border-radius: 10px;
                    text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
            <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
                ⛲ 觀察名單
            </h2>
            <div style='font-size:13px; color:#00D2FF; font-weight:500; margin-top:8px;'>
                 基準日 : 📍法人持股: {fmt_d(d_b1_inst)} ｜ 📍法人買況: {fmt_d(d_b23_chip)} ｜ 📍資券: {fmt_d(d_b4_margin)} ｜ 📍大腿: {fmt_d(d_b5_share)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 容器
        with st.container(border=True):
            st.info("💡 我們試著觀察近5/20/60/120日法人動向持股上升的變化前段班且當天持續買入的標的，搭配其他掃貨、連買、大腿數據等，看看是否能找出藏在法人們口袋裡的標的，然而買盤的延續性、資券及大腿動向也是相當重要的。(試著參考▼明細)")

            # 🚨 關鍵阻斷器：確保各區塊都有數據
            if 'df_blk2_1' not in st.session_state or st.session_state['df_blk2_1'].empty or 'df_blk5_1000' not in st.session_state or st.session_state['df_blk5_1000'].empty:
                st.warning("⚠️ 記憶體中尚無最新數據 (或尚未載入大股東資料)，請點擊下方按鈕啟動全市場掃描引擎。")
                c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
                with c_btn2:
                    if st.button("🚀 啟動全市場掃描 (計算總分)", type="primary", use_container_width=True):
                        st.query_params["page"] = "all"
                        st.rerun()
                # 🛑 防呆卡死：提早渲染隱藏按鈕，避免頂部導覽列失效！
                render_proxy_buttons()
                
                st.stop() #  絕對停止！不准用舊的 0 分往下算！
            
            # --- 以下保留您原本的正式運算數據分析邏輯 ---
            # df_b1 = st.session_state.get('my_final_df', pd.DataFrame()).copy()
            # ...

            # ---------------- 開始正式運算數據分析觀察名單打底及積分 ----------------
            df_b1 = st.session_state.get('my_final_df', pd.DataFrame()).copy()
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
                        df_fs = robust_read_csv_pool(sorted(fo_sell_files, reverse=True)[0])
                        id_c = next((c for c in df_fs.columns if '代號' in c), None)
                        if id_c: fo_sell_ids = set(df_fs[id_c].astype(str).str.replace(r'\D', '', regex=True))
                    
                    it_sell_files = glob.glob(os.path.join(DATA_DIR, "*投信賣出佔成交比*5日*.csv"))
                    if not it_sell_files: it_sell_files = glob.glob(os.path.join(DATA_DIR, "*投信賣出佔成交比*.csv"))
                    if it_sell_files:
                        df_is = robust_read_csv_pool(sorted(it_sell_files, reverse=True)[0])
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

                bad_b2_vol = ['持平', '調節洗盤', '劇烈倒貨', '觀望']
                bad_b2_iss = ['轉賣反轉', '籌碼沉澱中', '今日量縮持平']

                block_sids = set()
                try:
                    if 'fetch_block_trades' in globals():
                        temp_block = fetch_block_trades()
                        if not temp_block.empty:
                            block_sids = set(temp_block['證券代號'].astype(str).str.replace(r'\D', '', regex=True))
                except: pass
###########
                # ==========================================
                # 🚀 修正 2：終極版代號清洗與「動態欄位」智慧轉換引擎
                # ==========================================
                def ultra_clean_id(val):
                    """將任何奇怪型別或夾帶小數點、空白的代號，全部扒光剩下純數字字串"""
                    v = str(val).strip().replace('.0', '')
                    return re.sub(r'\D', '', v)

                def raw_delta_to_trend(val):
                    """把原始 CSV 的數字增減，當場轉換為大戶動態文字"""
                    try:
                        v = float(str(val).replace('+', '').replace('%', '').strip())
                        if v >= 1.5: return "🔥 大增"
                        if v >= 0.5: return "📈 增"
                        if v > 0: return "↗ 微增"
                        if v == 0: return "🔄 持平"
                        if v > -0.5: return "↘ 微減"
                        return "🚨 減/大減"
                    except: return "無資料"

                dict_1000, dict_400 = {}, {}
                
                # ------------------------------------------
                # 🎯 處理 1000 張大戶字典 (支援雙模態)
                # ------------------------------------------
                if not df_b5_1000.empty and '股票代號' in df_b5_1000.columns:
                    if '週動態' in df_b5_1000.columns:
                        # 情況 A：讀取到的是區塊 5 處理過的表格
                        dict_1000 = {ultra_clean_id(k): str(v) for k, v in zip(df_b5_1000['股票代號'], df_b5_1000['週動態'])}
                    else:
                        # 情況 B：讀取到的是原始 CSV！自動尋找增減欄位並當場轉換！
                        delta_col = next((c for c in df_b5_1000.columns if '1千張增減' in c or '1000張增減' in c or '增減' in c), None)
                        if delta_col:
                            dict_1000 = {ultra_clean_id(k): raw_delta_to_trend(v) for k, v in zip(df_b5_1000['股票代號'], df_b5_1000[delta_col])}

                # ------------------------------------------
                # 🎯 處理 400 張大戶字典 (支援雙模態)
                # ------------------------------------------
                if not df_b5_400.empty and '股票代號' in df_b5_400.columns:
                    if '週動態' in df_b5_400.columns:
                        dict_400 = {ultra_clean_id(k): str(v) for k, v in zip(df_b5_400['股票代號'], df_b5_400['週動態'])}
                    else:
                        delta_col = next((c for c in df_b5_400.columns if '400張增減' in c or '總增減' in c or '增減' in c), None)
                        if delta_col:
                            dict_400 = {ultra_clean_id(k): raw_delta_to_trend(v) for k, v in zip(df_b5_400['股票代號'], df_b5_400[delta_col])}
                # ==========================================

                results = []
                for _, row in pool_df.iterrows():
                    # 在迴圈內，一樣用最高規格把代號洗乾淨
                    sid = ultra_clean_id(row['股票代號'])
                    sname = str(row.get('股票名稱', '')).strip()
                    b1_dyn = str(row.get(dyn_col, '')) if dyn_col else '-'
                    
                    try:
                        delta_val = float(row.get('△', 0.0))
                        b1_delta = "0.00" if abs(delta_val) < 0.005 else (f"+{delta_val:.2f}" if delta_val > 0 else f"{delta_val:.2f}")
                    except: b1_delta = "0.00"
                    
                    if sid in block_sids: b1_dyn = f"{b1_dyn} | 🎣 鉅額交易"
                    b1_rank = str(row.get(rank_col, '-')) if rank_col else '-'
                    
                    score, details = 0.0, [] 
                    
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
                    
                    r_b4_mar, b4_list_count = "", 0
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
                        for b4_df in [df_b4_mar_pct, df_b4_mar_vol, df_b4_sho_pct, df_b4_sho_vol, df_b4_mp_pct, df_b4_mp_vol]:
                            if not b4_df.empty and sid in b4_df['股票代號'].values and '漲跌幅%' in b4_df.columns:
                                try: change_val = float(str(b4_df.loc[b4_df['股票代號'] == sid, '漲跌幅%'].iloc[0]).replace('%', '')); break 
                                except: pass
                        if change_val > 0:
                            score += 0.7; details.append("榜上+當日上漲: +0.7")
                            if change_val > 3: score += 0.7; details.append("榜上+漲幅>3%: +0.7")
                                
                        short_decrease_val = 0.0
                        if not df_b4_sho_pct.empty and sid in df_b4_sho_pct['股票代號'].values:
                            s_col = next((c for c in df_b4_sho_pct.columns if '當日' in str(c) and ('%' in str(c) or '增減' in str(c))), None)
                            if s_col:
                                try: short_decrease_val = float(str(df_b4_sho_pct.loc[df_b4_sho_pct['股票代號'] == sid, s_col].iloc[0]).replace('%', ''))
                                except: pass
                        if abs(short_decrease_val) >= 1: score += 1.2; details.append("空頭認輸(借券減>1%): +1.2")

                    # ==========================================
                    # 🚀 修正 3：利用極速字典精準抓取動態
                    # ==========================================
                    r_b5_1000, r_b5_400 = "-", "-"
                    
                    # 取出 1000 張動態
                    trend_1000_val = dict_1000.get(sid, "")
                    if trend_1000_val:
                        if '大增' in trend_1000_val: score += 2.0; r_b5_1000 = "🔥千張大增(+2)"; details.append("千張大增: +2")
                        elif '增' in trend_1000_val and '微' not in trend_1000_val: score += 1.0; r_b5_1000 = "📈千張增(+1)"; details.append("千張增: +1")
                        elif '微增' in trend_1000_val: score += 0.5; r_b5_1000 = "↗️千微增(+0.5)"; details.append("千張微增: +0.5")
                        elif '大減' in trend_1000_val: score -= 0.5; r_b5_1000 = "🚨千大減(-0.5)"; details.append("千張大減: -0.5")
                        elif '減' in trend_1000_val: score -= 0.5; r_b5_1000 = "📉千減(-0.5)"; details.append("千張減: -0.5")
                        else: r_b5_1000 = f"千{trend_1000_val}"

                    # 取出 400 張動態
                    trend_400_val = dict_400.get(sid, "")
                    if trend_400_val:
                        if '大增' in trend_400_val: score += 1.0; r_b5_400 = "🔥四百大增(+1)"; details.append("四百大增: +1")
                        elif '增' in trend_400_val and '微' not in trend_400_val: score += 0.5; r_b5_400 = "📈四百增(+0.5)"; details.append("四百增: +0.5")
                        elif '微增' in trend_400_val: score += 0.0; r_b5_400 = "↗️四百微增(0)"
                        elif '大減' in trend_400_val: score -= 0.0; r_b5_400 = "🚨四百大減(0)" 
                        elif '減' in trend_400_val: score -= 0.0; r_b5_400 = "📉四百減(0)"
                        else: r_b5_400 = f"四百{trend_400_val}"

                    # 雙引擎共振加分
                    if ('增' in trend_1000_val and '減' in trend_400_val):
                        score += 1.0; details.append("🌟籌碼極集中: +1"); r_b5_1000 = f"{r_b5_1000}🌟"

                    r_b5 = f"{r_b5_1000} | {r_b5_400}" if (r_b5_1000 != "-" or r_b5_400 != "-") else "-"
                    
                    is_fo_sell = sid in fo_sell_ids; is_it_sell = sid in it_sell_ids
                    if is_fo_sell and is_it_sell: r_warn = "🚨外投雙倒"; score -= 2.0; details.append("外投雙倒: -2")
                    elif is_fo_sell: r_warn = "⚠️外資倒"
                    elif is_it_sell: r_warn = "⚠️投信倒"
                    else: r_warn = "-"

                    results.append({
                        '總分': score, '代號': sid, '名稱': sname, '▼明細': " \n".join(details) if details else "無加扣分", '△': b1_delta,
                        '最新動態': b1_dyn, '今日上榜': b1_rank, '賣出警示': r_warn,
                        '外買佔比': r_b2_1, '投買佔比': r_b2_2, '外佔發行': r_b2_3, '投佔發行': r_b2_4,
                        '外日連': r_b3_fd, '外週連': r_b3_fw, '投日連': r_b3_id, '投週連': r_b3_iw,
                        '資減': r_b4_mar, '借減': r_b4_sho, '券增': r_b4_mp, '大股東動向': r_b5
                    })
                    
                res_df = pd.DataFrame(results).sort_values(by='總分', ascending=False).drop_duplicates(subset=['代號']).reset_index(drop=True)
                
                # ==========================================
                # 🔥 Delta (▼變量) 計算引擎與存檔防禦網
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
                            prev_df = gs_history[gs_history['紀錄日期'] == available_dates[1]]
                            id_col = '代號' if '代號' in prev_df.columns else '股票代號' if '股票代號' in prev_df.columns else None
                            if id_col: prev_scores_dict = dict(zip(prev_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True), prev_df['總分']))
                except Exception as e: 
                    st.warning(f"⚠️ 無法讀取 Google Sheets 歷史紀錄以計算變量，錯誤訊息：{e}")

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
                cols.insert(cols.index('總分') + 1, '▼變量')
                cols.insert(cols.index('名稱') + 1, '▼明細')
                cols.insert(cols.index('▼明細') + 1, '△')
                cols.insert(cols.index('今日上榜') + 1, '賣出警示')
                res_df = res_df[cols]
                st.session_state['top_pool_df'] = res_df
                
                # 🛑 終極防呆鎖死機制：絕對不准存 0 分進去！
                valid_calc = False
                if not res_df.empty and '總分' in res_df.columns:
                    valid_calc = (res_df['總分'] > 0).sum() >= 5 # 至少要有 5 檔股票總分大於 0 才算合法運算
                    
                if valid_calc and anchor_date_str != "00000000":
                    save_df = res_df.copy()
                    save_df.insert(0, '紀錄日期', anchor_date_str)
                    if st.session_state.get('last_gsheet_save_date') != anchor_date_str:
                        try:
                            old_df = conn.read(spreadsheet=SHEET_URL, worksheet="選股歷史", ttl=0).dropna(how="all")
                            if not old_df.empty and '紀錄日期' in old_df.columns:
                                old_df['紀錄日期'] = old_df['紀錄日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(8)
                                final_save_df = pd.concat([old_df[old_df['紀錄日期'] != anchor_date_str], save_df], ignore_index=True)
                            else: final_save_df = save_df
                            conn.update(spreadsheet=SHEET_URL, worksheet="選股歷史", data=final_save_df)
                            st.session_state['last_gsheet_save_date'] = anchor_date_str
                            hist_combined = final_save_df.copy()
                        except Exception as e: st.warning(f"⚠️ 歷史同步暫緩({e})")
                elif not valid_calc:
                    st.warning("⚠️ 本次計算總分多數為 0，已啟動防呆攔截機制：暫不覆寫 Google Sheets 歷史紀錄。請點擊上方按鈕載入最新籌碼大數據。")

                # ==========================================
                # 🚀 終極 UI 修正：局部渲染魔法 (Fragment) 避免畫面亂跳
                # 解決點選按鈕或輸入密碼後，畫面瘋狂跳回頂端的問題！
                # ==========================================
                st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
                
                # 👇 建立局部渲染魔法函數，包裝所有互動區塊，保證網頁絕對不會亂跳！
                @st.fragment
                def render_pool_interactive_ui(f_res_df, f_hist_combined):
                    selected_view = st.radio(
                        "切換檢視面板：",
                        ["🔹 今日最新排行", "🔹 歷史分數追蹤表", "🔹 模型驗證：每週 Top 5 追蹤"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key="pool_view_state"
                    )
                    
                    if selected_view in ["🔹 今日最新排行", "今日最新排行"]:
                        st.dataframe(f_res_df, use_container_width=True, hide_index=True, column_config={"▼明細": st.column_config.TextColumn("▼明細", help="滑鼠游標停留在這裡查看", width="small", max_chars=4)})
                        
                        st.write("---")
                        st.markdown("### 🧩 觀察名單中的資金聚落")
                        st.caption("將上方觀察名單轉換為產業面積大小，觀察法人口袋中持股變化集中的標的，切換顯示 總分 ▼變量  △ 名次 一覽 (我們排除 ETF 與債券)。")
                        
                        if not f_res_df.empty and 'STOCK_DICT' in globals() and STOCK_DICT:
                            st.write("")
                            c_opt, c_search = st.columns([3, 1.5])
                            with c_opt:
                                pool_filter = st.radio("設定觀測範圍與排序：", 
                                    ["全部顯示 (預設)", "顯示總分前100名", "顯示 ▼變量 前100名", "顯示 △ 前100名"], 
                                    horizontal=True, key="pool_treemap_filter"
                                )
                            with c_search:
                                pool_search = st.text_input("🔍 板塊內標的搜尋", placeholder="輸入代號/名稱以聚焦...", key="pool_treemap_search")

                            # 複製一份專門用來處理的 DataFrame
                            treemap_pool_df = f_res_df.copy()

                            # 💡 資料前處理：轉換數值欄位以供排序與格式化
                            treemap_pool_df['數值_總分'] = pd.to_numeric(treemap_pool_df['總分'], errors='coerce').fillna(0.0)
                            treemap_pool_df['數值_△'] = pd.to_numeric(treemap_pool_df['△'].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0.0)
                            
                            if '▼變量' in treemap_pool_df.columns:
                                treemap_pool_df['數值_變量'] = pd.to_numeric(treemap_pool_df['▼變量'], errors='coerce').fillna(0.0)
                            else:
                                treemap_pool_df['數值_變量'] = 0.0

                            if "總分" in pool_filter:
                                treemap_pool_df = treemap_pool_df.nlargest(100, '數值_總分')
                            elif "變量" in pool_filter:
                                treemap_pool_df = treemap_pool_df.nlargest(100, '數值_變量')
                            elif "△" in pool_filter:
                                treemap_pool_df = treemap_pool_df.nlargest(100, '數值_△')

                            if pool_search:
                                query = pool_search.strip()
                                treemap_pool_df = treemap_pool_df[
                                    treemap_pool_df['代號'].astype(str).str.contains(query, case=False, na=False) | 
                                    treemap_pool_df['名稱'].astype(str).str.contains(query, case=False, na=False)
                                ]
                                if treemap_pool_df.empty:
                                    st.warning(f"找不到符合「{query}」的標的。")

                            treemap_pool_df['產業別'] = treemap_pool_df['代號'].astype(str).apply(
                                lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他")
                            )
                            treemap_pool_df['產業別'] = treemap_pool_df['產業別'].replace('', 'ETF / 債券 / 其他')

                            pool_excluded_etfs = treemap_pool_df[treemap_pool_df['產業別'] == 'ETF / 債券 / 其他'].sort_values(by='代號').copy()
                            treemap_pool_df = treemap_pool_df[treemap_pool_df['產業別'] != 'ETF / 債券 / 其他']

                            if not treemap_pool_df.empty:
                                treemap_pool_df['計數'] = 1 
                                today_counts = treemap_pool_df['產業別'].value_counts().to_dict()

                                def format_industry_label(industry):
                                    t_count = today_counts.get(industry, 0)
                                    return f"<b>{industry}</b><br><span style='font-size: 13px;'>{t_count}檔</span>"
                                treemap_pool_df['產業別'] = treemap_pool_df['產業別'].apply(format_industry_label)

                                treemap_pool_df['總分_格式化'] = treemap_pool_df['數值_總分'].apply(lambda x: f"{x:.1f}")
                                treemap_pool_df['△_格式化'] = treemap_pool_df['數值_△'].apply(lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}")

                                def format_clean_stock_label(row):
                                    name = row.get('名稱', '')
                                    score = row.get('總分_格式化', '0.0')
                                    return f"<b>{name}</b><br><span style='font-size: 11px; color: #E5E7EB;'>{score}分</span>"
                                treemap_pool_df['顯示名稱'] = treemap_pool_df.apply(format_clean_stock_label, axis=1)

                                hover_columns = ['代號', '總分_格式化', '▼明細', '△_格式化', '最新動態', '大股東動向'] 

                                custom_dark_colors = [
                                    "rgba(60, 84, 62, 0.85)",     "rgba(78, 34, 28, 0.85)",     "rgba(81, 81, 168, 0.85)",    "rgba(167, 77, 110, 0.85)", 
                                    "rgba(67, 38, 58, 0.85)",     "rgba(244, 124, 35, 0.85)",   "rgba(177, 128, 236, 0.85)",  "rgba(13, 82, 89, 0.85)", 
                                    "rgba(111, 97, 94, 0.85)",    "rgba(196, 8, 28, 0.85)",     "rgba(30, 41, 59, 0.85)",     "rgba(77, 83, 60, 0.85)", 
                                    "rgba(107, 29, 47, 0.85)",    "rgba(70, 130, 180, 0.85)",   "rgba(133, 100, 4, 0.85)",    "rgba(30, 27, 75, 0.85)", 
                                    "rgba(6, 78, 59, 0.85)",      "rgba(154, 52, 18, 0.85)",    "rgba(112, 26, 117, 0.85)",   "rgba(51, 65, 85, 0.85)"
                                ]

                                import plotly.express as px
                                fig = px.treemap(
                                    treemap_pool_df,
                                    path=[px.Constant("板塊資金聚落"), '產業別', '顯示名稱'], 
                                    values='計數',
                                    color='產業別', 
                                    hover_data=hover_columns, 
                                    color_discrete_sequence=custom_dark_colors
                                )

                                fig.update_traces(
                                    textinfo="label", 
                                    textfont=dict(color="white", size=15),
                                    marker=dict(line=dict(color='#0B0F19', width=2), pad=dict(t=35, l=10, r=10, b=10)),
                                    hovertemplate=(
                                        '<b>%{label}</b><br>'
                                        '股票代號: %{customdata[0]}<br>'
                                        '模型總分: <b>%{customdata[1]} 分</b><br>'
                                        '▼明細: %{customdata[2]}<br>'
                                        '△: %{customdata[3]}<br>'
                                        '最新動態: %{customdata[4]}<br>'
                                        '大股東動向: %{customdata[5]}<br>'
                                        '<extra></extra>' 
                                    )
                                )
                                
                                fig.update_layout(
                                    margin=dict(t=30, l=0, r=0, b=0),
                                    height=650, 
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    font=dict(family="sans-serif") 
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                if not pool_search:
                                    st.info("⚪ 目前觀察名單中沒有一般產業的股票。")

                            if not pool_excluded_etfs.empty:
                                st.write("")
                                st.markdown("##### 🗑️ 本次已剔除的非一般產業 (ETF / 債券 / 指數)")
                                st.caption("以下標的已進榜觀察名單，但因非一般企業已從上方產業聚落中剔除。💡 **游標懸停於標籤可查看詳細分數與大股東動向。**")
                                
                                tags_html = ""
                                import html
                                
                                for _, r in pool_excluded_etfs.iterrows():
                                    name = str(r.get('名稱', ''))
                                    sid = str(r.get('代號', ''))
                                    detail = str(r.get('▼明細', '-'))
                                    dyn = str(r.get('最新動態', '-'))
                                    holder = str(r.get('大股東動向', '-'))
                                    
                                    d_val = r.get('數值_△', 0.0)
                                    s_val = r.get('數值_總分', 0.0)
                                    
                                    safe_name = html.escape(name, quote=True)
                                    safe_sid = html.escape(sid, quote=True)
                                    safe_detail = html.escape(detail, quote=True)
                                    safe_dyn = html.escape(dyn, quote=True)
                                    safe_holder = html.escape(holder, quote=True)
                                    
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
                                        f"模型總分: {s_val:.1f} 分&#10;"
                                        f"單日△: {d_str}&#10;"
                                        f"▼明細: {safe_detail}&#10;"
                                        f"最新動態: {safe_dyn}&#10;"
                                        f"大股東動向: {safe_holder}"
                                    )
                                    
                                    tags_html += f"<div title=\"{tooltip_text}\" style=\"background-color: {bg_color}; color: #E2E8F0; border: 1px solid {border_color}; padding: 6px 14px; border-radius: 20px; margin: 5px; display: inline-flex; align-items: center; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); cursor: help; transition: transform 0.2s;\">{safe_name} ({safe_sid}) <span style='color: {text_color}; font-weight: bold; margin-left: 8px;'>△ {d_str}</span></div>"
                                
                                st.markdown(f"<div style='margin-top: 5px; line-height: 2.4;'>{tags_html}</div>", unsafe_allow_html=True)
                                
                        else:
                            st.info("⚪ 尚無數據或找不到產業字典，無法繪製產業板塊圖。")

                    elif selected_view == "🔹 歷史分數追蹤表":
                        try:
                            if not f_hist_combined.empty:
                                recent_dates = sorted(f_hist_combined['紀錄日期'].unique(), reverse=True)[:20]
                                df_h = f_hist_combined[f_hist_combined['紀錄日期'].isin(recent_dates)].copy()
                                id_col = '代號' if '代號' in df_h.columns else '股票代號' if '股票代號' in df_h.columns else None
                                if id_col and '總分' in df_h.columns:
                                    df_h['日期'] = df_h['紀錄日期'].apply(lambda x: f"{x[4:6]}/{x[6:]}" if len(x)==8 else x)
                                    df_h['代號'] = df_h[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True)
                                    hist_pivot = df_h[['代號', '總分', '日期']].pivot_table(index='代號', columns='日期', values='總分', aggfunc='first').reset_index()
                                    sorted_date_columns = sorted([col for col in hist_pivot.columns if col not in ['代號', '名稱']], reverse=True)
                                    hist_pivot = hist_pivot[['代號'] + sorted_date_columns]
                                    hist_pivot.insert(1, '名稱', hist_pivot['代號'].map(dict(zip(f_res_df['代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True), f_res_df['名稱']))).fillna('-'))
                                    hist_pivot = hist_pivot[hist_pivot['名稱'] != '-']
                                    if not hist_pivot.empty and sorted_date_columns[0] in hist_pivot.columns:
                                        st.dataframe(hist_pivot.sort_values(by=sorted_date_columns[0], ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)
                                        st.info("我們也記錄了法人們口袋名單在觀察名單的總分變化，試著學習觀察籌碼動能的延續性與驗證 ▼變量...")
                                    else:
                                        st.warning("⚪ 尚無足夠的歷史分數紀錄。")
                            else: 
                                st.warning("⚪ 尚無足夠的歷史分數紀錄。")
                        except Exception as e: 
                            st.error(f"發生錯誤: {e}")

                    elif selected_view == "🔹 模型驗證：每週 Top 5 追蹤":
                        st.markdown("### 🏆 嚴選 5 檔模型追蹤")
                        st.info("💡 我們先排除了法人丟出籌碼警示的標的，並根據總分與當日△選出前 5 名，但是有時候倒貨僅是換手，這個部分還相當困難阿，真是傷腦筋")
                        if not f_res_df.empty:
                            safe_df = f_res_df[f_res_df['賣出警示'] == "-"].copy()
                            if not safe_df.empty:
                                safe_df['數值△'] = pd.to_numeric(safe_df['△'].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0)
                                top5_df = safe_df.sort_values(by=['總分', '數值△'], ascending=[False, False]).head(5).drop(columns=['數值△'])
                                
                                cols = st.columns(5)
                                for idx, (i, row) in enumerate(top5_df.iterrows()):
                                    with cols[idx]:
                                        delta_str = str(row['△'])
                                        delta_color = "#FF4B4B" if "+" in delta_str else ("#00E272" if "-" in delta_str else "#E2E8F0")
                                        st.markdown(f"""
                                            <div style="background-color:rgba(0, 210, 255, 0.05); border-top: 3px solid #00D2FF; padding: 10px; border-radius: 5px;">
                                                <h4 style="margin:0; color:#E2E8F0;">{row['名稱']}</h4>
                                                <p style="margin:0; font-size:12px; color:#A0AEC0;">{row['代號']}</p>
                                                <h2 style="margin:10px 0; color:#00D2FF;">{row['總分']:.1f} 分</h2>
                                                <p style="margin:0; font-size:14px;"><strong>當日△:</strong> <span style="color:{delta_color}; font-weight:bold;">{delta_str}</span></p>
                                                <p style="margin:5px 0 0 0; font-size:12px; line-height:1.2;">{row['大股東動向']}</p>
                                            </div>
                                        """, unsafe_allow_html=True)
                                
                                st.write("")
                                st.dataframe(top5_df[['代號', '名稱', '總分', '▼變量', '△', '最新動態', '▼明細']], use_container_width=True, hide_index=True)
                                
                                st.write("---")
                                c_space, c_main = st.columns([3, 2])
                                with c_main:
                                    with st.expander("🔐 站長用寫入追蹤名單", expanded=True):
                                        track_pw = st.text_input("密碼", type="password", key="track_pw")
                                        
                                        if track_pw == "DDong888":
                                            st.markdown("""
                                            <style>
                                            div[data-testid="stButton"] > button { padding: 0.25rem 0.5rem; font-size: 14px; }
                                            </style>
                                            """, unsafe_allow_html=True)
                                            
                                            if st.button("💾 儲存至 Google 雲端", type="primary", use_container_width=True):
                                                with st.spinner("正在抓取當前收盤價並寫入雲端..."):
                                                    import datetime
                                                    track_date = datetime.datetime.now().strftime("%Y-%m-%d")
                                                    current_prices = {}
                                                    import yfinance as yf
                                                    for sid in top5_df['代號']:
                                                        try:
                                                            p_df = yf.download(f"{sid}.TW", period="1d", progress=False)
                                                            if p_df.empty: p_df = yf.download(f"{sid}.TWO", period="1d", progress=False)
                                                            if not p_df.empty:
                                                                val = p_df['Close'].iloc[-1]
                                                                current_prices[sid] = round(float(val.iloc[0] if isinstance(val, pd.Series) else val), 2)
                                                            else: current_prices[sid] = 0.0
                                                        except: current_prices[sid] = 0.0
                                                    
                                                    top5_df['鎖定日期'] = track_date
                                                    top5_df['鎖定收盤價'] = top5_df['代號'].astype(str).map(current_prices)
                                                    
                                                    try:
                                                        try: old_track = conn.read(spreadsheet=SHEET_URL, worksheet="歷史名單回測觀察", ttl=0).dropna(how="all")
                                                        except: old_track = pd.DataFrame()
                                                        new_track = pd.concat([old_track, top5_df], ignore_index=True)
                                                        conn.update(spreadsheet=SHEET_URL, worksheet="歷史名單回測觀察", data=new_track)
                                                        st.success(f"✅ 已成功將 {track_date} 的名單寫入 Google Sheets！")
                                                    except Exception as e:
                                                        st.error(f"❌ 寫入失敗：{e} (請確認 Google Sheets 是否已建立『歷史名單回測觀察』工作表)")
                                        elif track_pw != "": st.error("密碼錯誤")
                                            
                        st.markdown("### 📊 歷史名單回測觀察")
                        try:
                            history_track_df = conn.read(spreadsheet=SHEET_URL, worksheet="歷史名單回測觀察", ttl=0).dropna(how="all")
                            if not history_track_df.empty:
                                selected_week = st.selectbox("選擇要回顧的鎖定日期", sorted(history_track_df['鎖定日期'].unique(), reverse=True))
                                week_df = history_track_df[history_track_df['鎖定日期'] == selected_week].copy()
                                
                                import datetime
                                from datetime import timedelta
                                lock_date_obj = datetime.datetime.strptime(selected_week, "%Y-%m-%d")
                                days_passed = (datetime.datetime.now() - lock_date_obj).days
                                
                                is_expired = days_passed >= 28 
                                
                                if is_expired:
                                    status_tag = "🔴 已結案 (凍結在第4週)"
                                    target_start = lock_date_obj + timedelta(days=28)
                                    start_str = target_start.strftime("%Y-%m-%d")
                                    end_str = (target_start + timedelta(days=5)).strftime("%Y-%m-%d")
                                else:
                                    weeks_passed = (days_passed // 7) + 1
                                    status_tag = f"🟢 追蹤中 (第 {weeks_passed} 週)"
                                    start_str = None 

                                st.markdown(f"**目前狀態：** `{status_tag}` ｜ **已鎖定：** `{days_passed} 天`")

                                with st.spinner("正在連線抓取檢測價格..."):
                                    import yfinance as yf
                                    latest_prices = {}
                                    for sid in week_df['代號'].astype(str).str.replace(r'\.0$', '', regex=True):
                                        try:
                                            ticker_tw = f"{sid}.TW"
                                            ticker_two = f"{sid}.TWO"
                                            if start_str: 
                                                p_df = yf.download(ticker_tw, start=start_str, end=end_str, progress=False)
                                                if p_df.empty: p_df = yf.download(ticker_two, start=start_str, end=end_str, progress=False)
                                                if not p_df.empty:
                                                    val = p_df['Close'].iloc[0] 
                                                    latest_prices[sid] = round(float(val.iloc[0] if isinstance(val, pd.Series) else val), 2)
                                                else: latest_prices[sid] = 0.0
                                            else: 
                                                p_df = yf.download(ticker_tw, period="1d", progress=False)
                                                if p_df.empty: p_df = yf.download(ticker_two, period="1d", progress=False)
                                                if not p_df.empty:
                                                    val = p_df['Close'].iloc[-1]
                                                    latest_prices[sid] = round(float(val.iloc[0] if isinstance(val, pd.Series) else val), 2)
                                                else: latest_prices[sid] = 0.0
                                        except: latest_prices[sid] = 0.0

                                col_price_name = "結案價格" if is_expired else "最新價格"
                                week_df[col_price_name] = week_df['代號'].astype(str).str.replace(r'\.0$', '', regex=True).map(latest_prices)
                                
                                def calc_price_return(row):
                                    try:
                                        lock_p = float(row.get('鎖定收盤價', 0))
                                        curr_p = float(row.get(col_price_name, 0))
                                        if lock_p > 0 and curr_p > 0:
                                            pct = ((curr_p - lock_p) / lock_p) * 100
                                            if pct > 0: return f"🚀 +{pct:.1f}%"
                                            elif pct < 0: return f"🩸 {pct:.1f}%"
                                            else: return "0.0%"
                                        return "-"
                                    except: return "-"
                                    
                                week_df['區間報酬'] = week_df.apply(calc_price_return, axis=1)

                                if not f_res_df.empty:
                                    today_scores = dict(zip(f_res_df['代號'].astype(str), f_res_df['總分']))
                                    week_df['今日分數'] = week_df['代號'].astype(str).str.replace(r'\.0$', '', regex=True).map(today_scores).fillna(0)
                                    
                                    def score_diff(row):
                                        try:
                                            diff = float(row['今日分數']) - float(row['總分']) 
                                            if diff > 0: return f"📈 +{diff:.1f}"
                                            elif diff < 0: return f"📉 {diff:.1f}"
                                            else: return "-"
                                        except: return "-"
                                        
                                    week_df['模型分數變化'] = week_df.apply(score_diff, axis=1)
                                    
                                    # 1. 在顯示清單的 '鎖定日期' 後面，插入 '▼明細' 欄位
                                    show_cols = ['鎖定日期', '▼明細', '代號', '名稱', '鎖定收盤價', col_price_name, '區間報酬', '總分', '今日分數', '模型分數變化']

                                    # 2. 為了避免長串的權重文字把版面撐壞，套用跟首頁一樣的 TextColumn 設定，讓它變成滑鼠懸停顯示
                                    st.dataframe(
                                        week_df[[c for c in show_cols if c in week_df.columns]], 
                                        use_container_width=True, 
                                        hide_index=True,
                                        column_config={
                                            "▼明細": st.column_config.TextColumn(
                                                "▼明細", 
                                                help="滑鼠游標停留在這裡，查看鎖定當時的各項權重分數", 
                                                width="small", 
                                                max_chars=4
                                            )
                                        }
                                    )
                                    
                                    if is_expired:
                                        st.info("🔒 此梯次名單已追蹤滿 4 週。為了客觀評估波段策略，此表已凍結於結案當時的收盤價與績效，不再隨每日盤勢波動。")
                                    else:
                                        st.info("💡 **驗證方法**：觀察鎖定股票的『區間報酬』是否為正，並核對『模型分數變化』是否持續上升。這能印證籌碼集中度與股價的連動性！")
                        except Exception as e:
                            st.write("⚪ 尚無歷史追蹤紀錄，請輸入密碼鎖定第一筆，或確認 Google Sheets 已建立工作表。")

                # 👇 呼叫這個局部渲染魔法函數，把剛剛算好的分數傳進去！
                render_pool_interactive_ui(res_df, hist_combined)
# ==========================================
# ✉️ 獨立分頁：聯絡我們 
# ==========================================
if current_page == "contact":
    # 標題也換成一致的藍色科技光暈
    st.markdown("<h2 style='color: #00D2FF; text-align: center; margin-top: 30px; text-shadow: 0 0 10px rgba(0,210,255,0.5);'>✉️ 聯絡管家</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        # 💡 調整欄位比例：原本是 [1, 4]，改為 [1.5, 3.5] 讓圖片區塊變寬放大
        col_img, col_text = st.columns([1.5, 3.5])
        
        with col_img:
            npc_image_path = os.path.join(image_folder, "75743.jpg")
            try:
                img_base64 = get_image_base64(npc_image_path)
                # 💡 圖片圓外框改為科技藍，加上微發光陰影
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%; padding: 10px;">
                        <img src="{img_base64}" style="width: 100%; max-width: 220px; border-radius: 50%; border: 1px solid rgba(0, 210, 255, 0.7); box-shadow: 0 0 20px rgba(0, 210, 255, 0.4);">
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.markdown("<div style='font-size: 80px; text-align: center; color: #00D2FF;'>🦇</div>", unsafe_allow_html=True)

        with col_text:
            # 💡 對話框改為玻璃藍卡片 (Glassmorphism) 效果，並更新台詞
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(0, 210, 255, 0.05) 0%, rgba(0, 210, 255, 0.12) 100%); 
                            padding: 20px 25px; 
                            border-radius: 12px; 
                            border-left: 2px solid #00D2FF; 
                            border-top: 1px solid rgba(0, 210, 255, 0.2); 
                            border-right: 1px solid rgba(0, 210, 255, 0.2); 
                            border-bottom: 1px solid rgba(0, 210, 255, 0.2); 
                            box-shadow: 0 8px 25px rgba(0, 210, 255, 0.1); 
                            backdrop-filter: blur(4px); 
                            height: 100%; 
                            display: flex; 
                            align-items: center;">
                    <p style="margin: 0; font-size: 17px; color: #E2E8F0; line-height: 1.8; letter-spacing: 0.5px;">
                        「夜安，股市冒險家。<br>
                        如果您在平台中發現任何系統異常，或是對本平台有任何建議，<br>
                        歡迎將寫好的紙條傳遞到後台交給我處理。😱」
                    </p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        st.write("") # 留白增加呼吸感
        
        with st.form("contact_us_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: sender_name = st.text_input("您的稱呼 (選填)", placeholder="例如：股市冒險家")
            with c2: sender_email = st.text_input("電子信箱 (選填)", placeholder="若需回覆請務必留下 Email")
                
            message_body = st.text_area("回報內容 / 建議事項*", placeholder="請描述您遇到的問題或建議...", height=120)
            submit_btn = st.form_submit_button("傳送紙條 ✉️", use_container_width=True)
            
            if submit_btn:
                if not message_body.strip():
                    st.error("⚠️ 傳送失敗：紙條上似乎空無一字喔！")
                else:
                    try:
                        import datetime
                        try:
                            old_contact_df = conn.read(spreadsheet=SHEET_URL, worksheet="聯絡我們", ttl=0)
                            old_contact_df = old_contact_df.dropna(how="all")
                        except:
                            old_contact_df = pd.DataFrame(columns=["時間", "稱呼", "信箱", "內容"])
                        
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        new_data = pd.DataFrame([{"時間": now_str, "稱呼": sender_name.strip() if sender_name else "匿名使用者", "信箱": sender_email.strip() if sender_email else "-", "內容": message_body.strip()}])
                        
                        final_contact_df = pd.concat([old_contact_df, new_data], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="聯絡我們", data=final_contact_df)
                        
                        st.toast("您的訊息已悄悄送達派對後台...", icon="🦇")
                        st.success("✨ 感謝回報！您的建議是盛宴最棒的點綴。")
                    except Exception as e:
                        st.error(f"❌ 傳送失敗，後台連線異常：{str(e)}")
    # 🛑 補上隱藏的傀儡按鈕，避免在聯絡我們頁面時頂部導覽列失效網頁卡死！
    render_proxy_buttons()
    
    # 🛑 最核心的魔法：渲染完聯絡表單後，直接強制停止後續程式！完全不讀取底下的大數據！
    st.stop()
    
        
# ==========================================
# 🧪 測試區：Google Sheets 連線測試
# ==========================================
# ==========================================
# 🎭 幕後無縫換頁引擎 (正常情況下在這裡渲染)
# ==========================================
# 如果程式順利走到這裡(沒有被上面的 st.stop 攔截)，就渲染按鈕
render_proxy_buttons()


# ==========================================
# 🧪 測試區：Google Sheets 連線測試
# ==========================================
#if st.button("🔄 立即強制同步大數據"):
    # 在這裡做完你的資料更新邏輯...
    
    # 強制網頁從頭重跑，清洗並更新畫面
    #st.rerun()
