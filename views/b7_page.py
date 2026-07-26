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
        
        # 清理欄位名稱中的所有空白 (包含 \xa0 不換行空白)
        df.columns = [str(c).replace(' ', '').replace('\u3000', '').replace('\ufeff', '').replace('\xa0', '') for c in df.columns]
        
        # 精準解析 "個股代號/名稱"
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
        
        # 精準鎖定神秘金字塔的「持股比例」欄位
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
            
        # 🛡️ 這裡就是防止笛卡爾積記憶體爆炸的護城河
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
            董監事動向
        </h2>
    </div>
    """, unsafe_allow_html=True)

    df_b7 = st.session_state['b7_main']
    if df_b7.empty:
        st.warning("⚠️ 在資料夾中找不到董監事持股資料，請確認檔名包含「神秘金字塔」與「董監事持股」。")
    else:
        st.dataframe(df_b7, use_container_width=True, hide_index=True)
