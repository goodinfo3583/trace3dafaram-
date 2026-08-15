#views/b7_page.py
import streamlit as st
import pandas as pd
import os
import glob
import re

# ==========================================
# ⚙️ 區塊 7：董監持股運算引擎
# ==========================================
def process_directors_data(DATA_DIR):
    """讀取並合併多個月份的董監事持股資料"""
    search_patterns = [
        os.path.join(DATA_DIR, "*神秘金字塔*董監事*.csv"),
        os.path.join(DATA_DIR, "*董監事持股*.csv")
    ]
    files = set()
    for pattern in search_patterns:
        files.update(glob.glob(pattern))
    
    if not files: return pd.DataFrame()
    
    merged_df = None
    processed_months = set() 
    
    for f in sorted(list(files), reverse=True):
        m = re.search(r'(202[0-9]{3,5})', os.path.basename(f))
        if not m: continue
        month_str = m.group(1)[:6] 
        
        if month_str in processed_months:
            continue
            
        df = None
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                df = pd.read_csv(f, encoding=enc, header=0)
                break
            except: pass
            
        if df is None or df.empty: continue
        
        df.columns = [str(c).replace(' ', '').replace('\u3000', '').replace('\ufeff', '').replace('\xa0', '') for c in df.columns]
        
        c_id_name = next((c for c in df.columns if '代號' in c and '名稱' in c), None)
        if c_id_name:
            df['股票代號'] = df[c_id_name].astype(str).str.extract(r'(\d+)', expand=False)
            df['股票名稱'] = df[c_id_name].astype(str).str.replace(r'^\d+', '', regex=True).str.strip()
        else:
            c_code = next((c for c in df.columns if '代號' in c or '代碼' in c), None)
            c_name = next((c for c in df.columns if '名稱' in c), None)
            if c_code and c_name:
                df['股票代號'] = df[c_code].astype(str).str.extract(r'(\d+)', expand=False)
                df['股票名稱'] = df[c_name].astype(str).str.strip()
            else:
                continue
                
        df = df.dropna(subset=['股票代號'])
        
        c_this_month = next((c for c in df.columns if c == '本月' or c == '本月%'), None)
        c_prev_month = next((c for c in df.columns if c == '前一月'), None)
        
        keep_cols = ['股票代號', '股票名稱']
        
        if c_this_month:
            df[f'{month_str}持股%'] = pd.to_numeric(df[c_this_month].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
            processed_months.add(month_str)
            keep_cols.append(f'{month_str}持股%')
            
        if c_prev_month:
            df[f'{month_str}_前一月'] = pd.to_numeric(df[c_prev_month].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
            keep_cols.append(f'{month_str}_前一月')
            
        df_clean = df[keep_cols].drop_duplicates(subset=['股票代號'])
        
        if merged_df is None:
            merged_df = df_clean
        else:
            merged_df = pd.merge(merged_df, df_clean, on=['股票代號', '股票名稱'], how='outer')

    if merged_df is not None and not merged_df.empty:
        sorted_months = sorted(list(processed_months), reverse=True)
        if len(sorted_months) >= 2:
            m1, m2 = sorted_months[0], sorted_months[1]
            if f'{m1}持股%' in merged_df.columns and f'{m2}持股%' in merged_df.columns:
                merged_df['近月增減%'] = merged_df[f'{m1}持股%'] - merged_df[f'{m2}持股%']
        
        if '近月增減%' not in merged_df.columns and len(sorted_months) >= 1:
            m1 = sorted_months[0]
            if f'{m1}持股%' in merged_df.columns and f'{m1}_前一月' in merged_df.columns:
                merged_df['近月增減%'] = merged_df[f'{m1}持股%'] - merged_df[f'{m1}_前一月']
                
        if '近月增減%' in merged_df.columns:
            def get_trend(val):
                if pd.isna(val): return "無"
                if val >= 1.0: return "🔥 大增"
                if val >= 0.1: return "📈 增"
                if val > 0: return "↗️ 微增"
                if val == 0: return "🔄 持平"
                if val > -0.1: return "↘️ 微減"
                return "🚨 減/大減"
                
            merged_df['動態'] = merged_df['近月增減%'].round(2).apply(get_trend)
            merged_df['近月增減%'] = merged_df['近月增減%'].round(2)
            
        cols_order = ['股票代號', '股票名稱']
        if '動態' in merged_df.columns: cols_order.extend(['動態', '近月增減%'])
        for m in sorted_months:
            if f'{m}持股%' in merged_df.columns: cols_order.append(f'{m}持股%')
            
        merged_df = merged_df[[c for c in cols_order if c in merged_df.columns]]
        if '近月增減%' in merged_df.columns:
            merged_df = merged_df.sort_values('近月增減%', ascending=False)
            
        return merged_df
        
    return pd.DataFrame()


# ==========================================
# ⚙️ 區塊 7：董監質押比最新月份 (第一張表)
# ==========================================
def process_pledge_data(DATA_DIR):
    """讀取並合併董監質押比資料，自動過濾僅保留最新月份"""
    search_pattern = os.path.join(DATA_DIR, "*董監質押*.csv")
    files = glob.glob(search_pattern)
    
    if not files: return pd.DataFrame()
    
    df_list = []
    for f in files:
        df = None
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                df = pd.read_csv(f, encoding=enc, header=0)
                break
            except: pass
            
        if df is not None and not df.empty:
            df_list.append(df)
            
    if not df_list: return pd.DataFrame()
    
    merged_df = pd.concat(df_list, ignore_index=True)
    
    c_code = next((c for c in merged_df.columns if str(c).replace(" ", "") == "代號"), None)
    c_month = next((c for c in merged_df.columns if str(c).replace(" ", "") == "持股資料月份"), None)
    
    if c_code and c_month:
        merged_df = merged_df.dropna(subset=[c_code, c_month])
        merged_df[c_code] = merged_df[c_code].astype(str).str.strip()
        merged_df[c_month] = merged_df[c_month].astype(str).str.strip()
        
        latest_month = merged_df[c_month].max()
        merged_df = merged_df[merged_df[c_month] == latest_month]
        merged_df = merged_df.drop_duplicates(subset=[c_code], keep='first')
    
    requested_cols = [
        "排名", "代號", "名稱", "持股 資料 月份",
        "全體 董監 持股 (%)", "全體 董監 質押 (%)", 
        "全體 董監 持股 (萬張)", "全體 董監 質押 (萬張)", 
        "全體 董監 增減 張數"
    ]
    
    actual_cols = []
    rename_dict = {}
    for req_c in requested_cols:
        req_clean = req_c.replace(" ", "")
        matched_col = next((c for c in merged_df.columns if str(c).replace(" ", "").replace('\u3000', '') == req_clean), None)
        if matched_col:
            actual_cols.append(matched_col)
            rename_dict[matched_col] = req_c
            
    if actual_cols:
        merged_df = merged_df[actual_cols]
        merged_df = merged_df.rename(columns=rename_dict)
    
    if "排名" in merged_df.columns:
        merged_df["排名"] = pd.to_numeric(merged_df["排名"], errors='coerce')
        merged_df = merged_df.dropna(subset=["排名"])
        merged_df = merged_df.sort_values(by="排名", ascending=True)

    return merged_df


# ==========================================
# ⚙️ 區塊 7 新增：董監質押歷史趨勢引擎 (第二張表)
# ==========================================
def process_pledge_history_data(DATA_DIR):
    """橫向展開歷史月份的質押比，避免笛卡爾積"""
    search_pattern = os.path.join(DATA_DIR, "*董監質押*.csv")
    files = glob.glob(search_pattern)
    
    if not files: return pd.DataFrame()
    
    df_list = []
    for f in files:
        df = None
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                df = pd.read_csv(f, encoding=enc, header=0)
                break
            except: pass
        if df is not None and not df.empty:
            df_list.append(df)
            
    if not df_list: return pd.DataFrame()
    
    merged_df = pd.concat(df_list, ignore_index=True)
    
    # 鎖定必備欄位 (無視空白符號)
    c_code = next((c for c in merged_df.columns if str(c).replace(" ", "") == "代號"), None)
    c_name = next((c for c in merged_df.columns if str(c).replace(" ", "") == "名稱"), None)
    c_month = next((c for c in merged_df.columns if str(c).replace(" ", "") == "持股資料月份"), None)
    c_pledge = next((c for c in merged_df.columns if str(c).replace(" ", "").replace('\u3000', '') == "全體董監質押(%)"), None)
    
    if not all([c_code, c_name, c_month, c_pledge]):
        return pd.DataFrame()
        
    merged_df = merged_df.dropna(subset=[c_code, c_month])
    merged_df[c_code] = merged_df[c_code].astype(str).str.strip()
    merged_df[c_name] = merged_df[c_name].astype(str).str.strip()
    merged_df[c_month] = merged_df[c_month].astype(str).str.strip()
    
    # 確保質押比是數值格式
    merged_df[c_pledge] = pd.to_numeric(merged_df[c_pledge].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
    
    # 🛡️ 核心防呆：同代號+同月份 僅保留第一筆，徹底杜絕笛卡爾積
    merged_df = merged_df.drop_duplicates(subset=[c_code, c_month], keep='first')
    
    # 🔄 樞紐分析：將月份拉成橫向表頭
    pivot_df = merged_df.pivot(index=[c_code, c_name], columns=c_month, values=c_pledge).reset_index()
    
    # 取得所有月份欄位，由新排到舊 (例如：26M07, 26M06, 26M05)
    month_cols = sorted([c for c in pivot_df.columns if c not in [c_code, c_name]], reverse=True)
    
    # 自動計算近兩月增減差距
    if len(month_cols) >= 2:
        m1, m2 = month_cols[0], month_cols[1]
        pivot_df['近月質押增減(%)'] = pivot_df[m1] - pivot_df[m2]
        
    # 重新安排欄位順序：代號、名稱、增減(%)、最新月、上月...
    cols_order = [c_code, c_name]
    if '近月質押增減(%)' in pivot_df.columns:
        cols_order.append('近月質押增減(%)')
    cols_order.extend(month_cols)
    pivot_df = pivot_df[cols_order]
    
    # 重新命名欄位使其更易讀
    rename_dict = {c_code: "代號", c_name: "名稱"}
    for m in month_cols:
        rename_dict[m] = f"{m} 質押(%)"
    pivot_df = pivot_df.rename(columns=rename_dict)
    
    # 依照最新月份的質押比例由高至低排序
    if month_cols:
        latest_col = f"{month_cols[0]} 質押(%)"
        pivot_df = pivot_df.sort_values(by=latest_col, ascending=False)

    return pivot_df


# ==========================================
# 🔄 資料同步接口
# ==========================================
def sync_b7_data(DATA_DIR):
    st.session_state['b7_main'] = process_directors_data(DATA_DIR)
    
def sync_pledge_data(DATA_DIR):
    st.session_state['b7_pledge'] = process_pledge_data(DATA_DIR)

def sync_pledge_history_data(DATA_DIR):
    st.session_state['b7_pledge_history'] = process_pledge_history_data(DATA_DIR)


# ==========================================
# 🖼️ 前台畫面渲染 (三頁籤切換)
# ==========================================
def show_b7_page(DATA_DIR, STOCK_DICT):
    if 'b7_main' not in st.session_state:
        with st.spinner("⏳ 載入董監持股數據中..."):
            sync_b7_data(DATA_DIR)
            
    if 'b7_pledge' not in st.session_state:
        with st.spinner("⏳ 載入董監質押最新數據中..."):
            sync_pledge_data(DATA_DIR)
            
    if 'b7_pledge_history' not in st.session_state:
        with st.spinner("⏳ 載入董監質押歷史數據中..."):
            sync_pledge_history_data(DATA_DIR)
            
    st.write("---")
    st.markdown("<div id='section-7'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; 
                border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
        <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
            董監事籌碼動向
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # 🎯 建立三個分頁
    tab1, tab2, tab3 = st.tabs(["🔹 董監質押比增減", "🔹 董監質押歷史趨勢", "🔹 董監持股比增減"])

    # --- 分頁 1：董監質押比增減 (最新單月) ---
    with tab1:
        df_pledge = st.session_state['b7_pledge']
        if df_pledge.empty:
            st.warning("⚠️ 找不到董監質押比資料，請確認 data 資料夾中存在相關 CSV 檔案。")
        else:
            st.dataframe(df_pledge, use_container_width=True, hide_index=True)
            
    # --- 分頁 2：董監質押歷史趨勢 (跨月橫向比較) ---
    with tab2:
        df_history = st.session_state['b7_pledge_history']
        if df_history.empty:
            st.warning("⚠️ 歷史質押資料不足或欄位無法解析。")
        else:
            st.dataframe(df_history, use_container_width=True, hide_index=True)

    # --- 分頁 3：董監持股比增減 (原有的持股動態) ---
    with tab3:
        df_b7 = st.session_state['b7_main']
        if df_b7.empty:
            st.warning("⚠️ 在資料夾中找不到董監事持股資料，請確認檔名包含「神秘金字塔」與「董監事持股」。")
        else:
            st.dataframe(df_b7, use_container_width=True, hide_index=True)
