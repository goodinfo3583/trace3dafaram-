# utils/data_utils.py 工具箱
import os
import glob
import re
import pandas as pd
import streamlit as st

# 在這裡定義資料夾路徑，全站共用核心工具箱 函式
DATA_DIR = "./data"

def extract_date_from_name(filename):
    """從檔名中萃取出 8 碼日期，供全站各區塊排序使用"""
    match = re.search(r'\d{8}', os.path.basename(filename))
    return match.group(0) if match else "00000000"

# 💡 優化 1：本機讀檔加入快取 (TTL=300，5分鐘內重複讀取瞬間完成)
@st.cache_data(show_spinner=False, ttl=300)
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

# 💡 優化 2：針對有資料清洗處理的 CSV 讀取加上快取
@st.cache_data(show_spinner=False, ttl=300)
def parse_json_history_csv(file_path, date_label):
    """避免excel最前方0消失，並處理欄位名稱"""
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

# 💡 優化 3：加入 show_spinner=False，避免背景讀取時畫面閃爍轉圈圈
@st.cache_data(show_spinner=False, ttl=60) 
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

@st.cache_data(show_spinner=False, ttl=60)
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

# utils/data_utils.py (替換原本的 calculate_chip_concentration)

# 💡 優化 4：滿血版 Parquet 集中度運算引擎 (光速本地版)
def calculate_chip_concentration(stock_df: pd.DataFrame) -> pd.DataFrame:
    """
    計算指定股票的每日籌碼集中度 (直接接收已經過濾好的 DataFrame，瞬間完成)
    """
    if stock_df.empty:
        return pd.DataFrame() 
        
    results = []
    
    # 依照「交易日期」進行分組運算
    for date, group in stock_df.groupby('trade_date'):
        # 當日該檔股票的「總成交張數」 = 所有分點的「總買進股數」加總 / 1000
        daily_total_volume = (group['總買進股數'].sum()) / 1000
        
        if daily_total_volume == 0:
            continue
            
        # 分出買賣方，並各自排序抓出前 15 大
        buy_side = group[group['net_vol'] > 0].sort_values('net_vol', ascending=False).head(15)
        sell_side = group[group['net_vol'] < 0].sort_values('net_vol', ascending=True).head(15)
        
        top15_buy_vol = buy_side['net_vol'].sum()
        top15_sell_vol = abs(sell_side['net_vol'].sum())
        
        daily_net_vol = top15_buy_vol - top15_sell_vol
        
        # 真正的集中度公式：(前15大淨買超) / 當日總成交量
        concentration_pct = round((daily_net_vol / daily_total_volume) * 100, 2)
        
        results.append({
            'trade_date': date,
            'top15_buy': top15_buy_vol,
            'top15_sell': top15_sell_vol,
            'net_buy': daily_net_vol,
            'concentration_%': concentration_pct
        })
        
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values('trade_date')
    return result_df

# 台股代號與名稱產業類別 萬用字典引擎
@st.cache_data(show_spinner=False, ttl=3600)
def get_stock_dictionary():
    """讀取證交所 ISIN 檔案，支援同時讀取上市、上櫃、興櫃多個檔案"""
    mapping = {}
    search_patterns = [
        "./data/*辨識號碼*.txt",
        "./*辨識號碼*.txt"
    ]
    dict_files = []
    for pattern in search_patterns:
        dict_files.extend(glob.glob(pattern))
        
    if not dict_files: return mapping
        
    for target_file in dict_files:
        raw_lines = []
        for encoding in ['utf-8-sig', 'utf-8', 'cp950', 'utf-16', 'big5']:
            try:
                with open(target_file, 'r', encoding=encoding) as f:
                    raw_lines = f.readlines()
                if len(raw_lines) > 10: break
            except: continue
                
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
                    
                    if sid.isalnum() and len(sid) <= 4: 
                        if sid not in mapping:
                            mapping[sname] = {"id": sid, "name": sname, "industry": industry}
                            mapping[sid] = {"id": sid, "name": sname, "industry": industry}
                    
    return mapping

# 啟動時直接在工具箱內載入字典，供外部呼叫
STOCK_DICT = get_stock_dictionary()
