# views/b7_page.py
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
    # 支援新舊檔名格式
    files = glob.glob(os.path.join(DATA_DIR, "*神秘金字塔*董監事*.csv")) + \
            glob.glob(os.path.join(DATA_DIR, "*董監事持股*.csv"))
    
    if not files: return pd.DataFrame()
    
    merged_df = None
    all_months = set()
    
    for f in files:
        # 擷取檔名的前綴日期，例如 20260615 -> 擷取前6碼 202606
        m = re.search(r'(202[0-9]{3,5})', os.path.basename(f))
        if not m: continue
        month_str = m.group(1)[:6] 
        
        df = None
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                df = pd.read_csv(f, encoding=enc)
                break
            except: pass
            
        if df is None or df.empty: continue
        
        # 清理欄位名稱
        df.columns = [re.sub(r'\s+', '', str(c)).replace('\ufeff', '') for c in df.columns]
        
        # 判斷代號與名稱
        c_code = next((c for c in df.columns if '代號' in c or '代碼' in c), None)
        c_name = next((c for c in df.columns if '名稱' in c), None)
        
        if '股票代號/名稱' in df.columns:
            df['股票代號'] = df['股票代號/名稱'].astype(str).str.extract(r'(\d+)', expand=False)
            df['股票名稱'] = df['股票代號/名稱'].astype(str).str.replace(r'^\d+', '', regex=True).str.strip()
        elif c_code and c_name:
            df['股票代號'] = df[c_code].astype(str).str.extract(r'(\d+)', expand=False)
            df['股票名稱'] = df[c_name].astype(str).str.strip()
        else:
            continue
            
        df = df.dropna(subset=['股票代號'])
        
        # 尋找董監持股欄位
        c_hold = next((c for c in df.columns if '持股' in c and ('%' in c or '比例' in c)), None)
        if not c_hold: c_hold = next((c for c in df.columns if '持股' in c), None)
            
        if c_hold:
            df[f'{month_str}持股%'] = pd.to_numeric(df[c_hold].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
            all_months.add(month_str)
            
        # 尋找質押欄位 (可選)
        c_pledge = next((c for c in df.columns if '質押' in c and ('%' in c or '比例' in c)), None)
        if c_pledge:
            df[f'{month_str}質押%'] = pd.to_numeric(df[c_pledge].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
            
        keep_cols = ['股票代號', '股票名稱']
        if c_hold: keep_cols.append(f'{month_str}持股%')
        if c_pledge: keep_cols.append(f'{month_str}質押%')
        
        df_clean = df[keep_cols].drop_duplicates(subset=['股票代號'])
        
        if merged_df is None:
            merged_df = df_clean
        else:
            merged_df = pd.merge(merged_df, df_clean, on=['股票代號', '股票名稱'], how='outer')

    if merged_df is not None and not merged_df.empty:
        sorted_months = sorted(list(all_months), reverse=True)
        
        # 🤖 計算最新趨勢動向
        if len(sorted_months) >= 2:
            m1, m2 = sorted_months[0], sorted_months[1]
            if f'{m1}持股%' in merged_df.columns and f'{m2}持股%' in merged_df.columns:
                merged_df['近期增減%'] = merged_df[f'{m1}持股%'] - merged_df[f'{m2}持股%']
                
                def get_trend(val):
                    if pd.isna(val): return "無"
                    if val >= 1.0: return "🔥 大增"
                    if val >= 0.1: return "📈 增"
                    if val > 0: return "↗️ 微增"
                    if val == 0: return "🔄 持平"
                    if val > -0.1: return "↘️ 微減"
                    return "🚨 減/大減"
                merged_df['動向'] = merged_df['近期增減%'].apply(get_trend)
        
        # 重新排序欄位
        cols_order = ['股票代號', '股票名稱']
        if '動向' in merged_df.columns: cols_order.extend(['動向', '近期增減%'])
        
        for m in sorted_months:
            if f'{m}持股%' in merged_df.columns: cols_order.append(f'{m}持股%')
            if f'{m}質押%' in merged_df.columns: cols_order.append(f'{m}質押%')
            
        merged_df = merged_df[[c for c in cols_order if c in merged_df.columns]]
        if '近期增減%' in merged_df.columns:
            merged_df = merged_df.sort_values('近期增減%', ascending=False)
        
        return merged_df
        
    return pd.DataFrame()

def sync_b7_data(DATA_DIR):
    """供系統背景與按鈕呼叫的同步接口"""
    st.session_state['b7_main'] = process_directors_data(DATA_DIR)

# ==========================================
# 🖼️ 前台畫面渲染
# ==========================================
def show_b7_page(DATA_DIR, STOCK_DICT):
    if 'b7_main' not in st.session_state:
        with st.spinner("⏳ 載入董監動向數據中..."):
            sync_b7_data(DATA_DIR)
            
    st.write("---")
    st.markdown("<div id='section-7'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(16,185,129,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #10b981; border-bottom: 1px solid #10b981; padding: 15px 20px; 
                border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(16, 189, 129, 0.2); margin-bottom: 20px;">
        <h2 style="color: #ecfdf5; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(16, 185, 129, 0.8);">
            👔 董監事動向
        </h2>
    </div>
    """, unsafe_allow_html=True)

    df_b7 = st.session_state['b7_main']
    if df_b7.empty:
        st.warning("⚠️ 在資料夾中找不到董監事持股資料，請確認檔名包含「神秘金字塔」與「董監事持股」。")
    else:
        st.dataframe(df_b7, use_container_width=True, hide_index=True)
