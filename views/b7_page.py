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
                # 讀取資料
                df = pd.read_csv(f, encoding=enc, header=0)
                break
            except: pass
            
        if df is None or df.empty: continue
        
        # 🌟 關鍵修復 1：清理欄位名稱中的所有空白 (把 "本  月" 變成 "本月")
        df.columns = [str(c).replace(' ', '').replace('\u3000', '').replace('\ufeff', '') for c in df.columns]
        
        # 🌟 關鍵修復 2：精準解析 "個股代號/名稱"
        c_id_name = next((c for c in df.columns if '代號' in c and '名稱' in c), None)
        if c_id_name:
            # 抽出數字作為代號
            df['股票代號'] = df[c_id_name].astype(str).str.extract(r'(\d+)', expand=False)
            # 移除開頭的數字作為名稱，避免 1101台泥 的狀況
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
        
        # 🌟 關鍵修復 3：精準鎖定神秘金字塔的「持股比例」欄位
        # (Pandas 如果遇到重複欄位名稱，第二個會變成 本月.1，所以第一個「本月」一定就是百分比)
        c_this_month = next((c for c in df.columns if c == '本月' or c == '本月%'), None)
        c_prev_month = next((c for c in df.columns if c == '前一月'), None)
        
        keep_cols = ['股票代號', '股票名稱']
        
        if c_this_month:
            # 轉化為數字，去除 % 和逗號
            df[f'{month_str}持股%'] = pd.to_numeric(df[c_this_month].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
            all_months.add(month_str)
            keep_cols.append(f'{month_str}持股%')
            
        # 如果只有單一檔案，我們順便擷取檔案內的「前一月」，當作備用的趨勢計算基準
        if c_prev_month:
            df[f'{month_str}_前一月'] = pd.to_numeric(df[c_prev_month].astype(str).str.replace('%', '').str.replace(',', ''), errors='coerce')
            keep_cols.append(f'{month_str}_前一月')
            
        df_clean = df[keep_cols].drop_duplicates(subset=['股票代號'])
        
        if merged_df is None:
            merged_df = df_clean
        else:
            merged_df = pd.merge(merged_df, df_clean, on=['股票代號', '股票名稱'], how='outer')

    if merged_df is not None and not merged_df.empty:
        sorted_months = sorted(list(all_months), reverse=True)
        
        # 🤖 捨棄座標走勢圖，自己計算真正的趨勢與動態
        if len(sorted_months) >= 2:
            # 狀況 A：如果資料夾有多個檔案 (例如 202606 和 202605)
            m1, m2 = sorted_months[0], sorted_months[1]
            if f'{m1}持股%' in merged_df.columns and f'{m2}持股%' in merged_df.columns:
                merged_df['近期增減%'] = merged_df[f'{m1}持股%'] - merged_df[f'{m2}持股%']
        elif len(sorted_months) == 1:
            # 狀況 B：如果只有一個檔案，利用該檔案自帶的「前一月」來比較
            m1 = sorted_months[0]
            if f'{m1}持股%' in merged_df.columns and f'{m1}_前一月' in merged_df.columns:
                merged_df['近期增減%'] = merged_df[f'{m1}持股%'] - merged_df[f'{m1}_前一月']
                
        # 產生對應的中文動態
        if '近期增減%' in merged_df.columns:
            def get_trend(val):
                if pd.isna(val): return "無"
                if val >= 1.0: return "🔥 大增"
                if val >= 0.1: return "📈 增"
                if val > 0: return "↗️ 微增"
                if val == 0: return "🔄 持平"
                if val > -0.1: return "↘️ 微減"
                return "🚨 減/大減"
                
            merged_df['動態'] = merged_df['近期增減%'].round(2).apply(get_trend)
            merged_df['近期增減%'] = merged_df['近期增減%'].round(2)
            
        # 重新整理並排序欄位 (把最新的月份放在最前面)
        cols_order = ['股票代號', '股票名稱']
        if '動態' in merged_df.columns: cols_order.extend(['動態', '近期增減%'])
        for m in sorted_months:
            if f'{m}持股%' in merged_df.columns: cols_order.append(f'{m}持股%')
            
        merged_df = merged_df[[c for c in cols_order if c in merged_df.columns]]
        
        # 依照近期增減排行，大增的排在最前面
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
            👔 董監事動向 (近月比較)
        </h2>
    </div>
    """, unsafe_allow_html=True)

    df_b7 = st.session_state['b7_main']
    if df_b7.empty:
        st.warning("⚠️ 在資料夾中找不到董監事持股資料，請確認檔名包含「神秘金字塔」與「董監事持股」。")
    else:
        st.dataframe(df_b7, use_container_width=True, hide_index=True)
