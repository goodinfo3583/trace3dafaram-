import streamlit as st
import pandas as pd
import os
import glob
import re

# ==========================================
# ⚙️ 區塊 7：董監持股運算引擎 (原邏輯)
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
        
        # 清理欄位名稱中的所有空白
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
# ⚙️ 區塊 7 新增：董監質押比運算引擎
# ==========================================
def process_pledge_data(DATA_DIR):
    """讀取並合併所有名次的董監質押比資料，並只保留指定欄位"""
    search_pattern = os.path.join(DATA_DIR, "*董監質押比*.csv")
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
    
    # 垂直合併所有檔案 (包含 1-300名, 301-600名, 202606董監質押比(1-300名(高→低))_2.csv 等)
    merged_df = pd.concat(df_list, ignore_index=True)
    
    # 定義您指定要擷取的目標欄位 (去除因連點產生的空字串)
    requested_cols = [
        "排名", "代號", "名稱", "成交", "持股 資料 月份", 
        "全體 董監 持股 (萬張)", "全體 董監 增減 張數", "全體 董監 持股 (%)", 
        "全體 董監 質押 (萬張)", "全體 董監 質押 (%)"
    ]
    
    # 🎯 精準欄位對應機制：
    # 為了防止原始檔案中的半形/全形空白干擾，我們用去除空白的方式來找出 DataFrame 實際對應的欄位名稱
    actual_cols = []
    for req_c in requested_cols:
        req_clean = req_c.replace(" ", "")
        matched_col = next((c for c in merged_df.columns if str(c).replace(" ", "").replace('\u3000', '') == req_clean), None)
        if matched_col:
            actual_cols.append(matched_col)
            
    # 只保留成功對應的欄位
    if actual_cols:
        merged_df = merged_df[actual_cols]
    
    # 將「排名」轉換為數值並重新排序，確保 1~1969 名順序正確
    rank_col = next((c for c in merged_df.columns if '排名' in c), None)
    if rank_col:
        merged_df[rank_col] = pd.to_numeric(merged_df[rank_col], errors='coerce')
        # 移除沒有排名的無效行並重新排序
        merged_df = merged_df.dropna(subset=[rank_col])
        merged_df = merged_df.sort_values(by=rank_col, ascending=True)

    return merged_df


# ==========================================
# 🔄 資料同步接口
# ==========================================
def sync_b7_data(DATA_DIR):
    st.session_state['b7_main'] = process_directors_data(DATA_DIR)
    
def sync_pledge_data(DATA_DIR):
    st.session_state['b7_pledge'] = process_pledge_data(DATA_DIR)


# ==========================================
# 🖼️ 前台畫面渲染 (支援雙 DataFrame 切換)
# ==========================================
def show_b7_page(DATA_DIR, STOCK_DICT):
    # 檢查狀態，若無則載入
    if 'b7_main' not in st.session_state:
        with st.spinner("⏳ 載入董監持股數據中..."):
            sync_b7_data(DATA_DIR)
            
    if 'b7_pledge' not in st.session_state:
        with st.spinner("⏳ 載入董監質押比數據中..."):
            sync_pledge_data(DATA_DIR)
            
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

    # 建立兩個分頁標籤來切換 DataFrame
    tab1, tab2 = st.tabs(["📊 董監持股增減", "🔗 董監質押比排行"])

    # --- 分頁 1：原有的董監持股動態 ---
    with tab1:
        df_b7 = st.session_state['b7_main']
        if df_b7.empty:
            st.warning("⚠️ 在資料夾中找不到董監事持股資料，請確認檔名包含「神秘金字塔」與「董監事持股」。")
        else:
            st.dataframe(df_b7, use_container_width=True, hide_index=True)

    # --- 分頁 2：新增的董監質押比 ---
    with tab2:
        df_pledge = st.session_state['b7_pledge']
        if df_pledge.empty:
            st.warning("⚠️ 找不到董監質押比資料，請確認 data 資料夾中存在如 `202606董監質押比(1-300名(高→低))_2.csv` 的檔案。")
        else:
            st.dataframe(df_pledge, use_container_width=True, hide_index=True)
