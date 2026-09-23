# views/b2_page.py
import streamlit as st
import pandas as pd
import os
import glob
import re
from functools import reduce

def extract_date_from_name(filename):
    """從檔名萃取 8 碼日期 (202XXXXX)"""
    match = re.search(r'(202\d{5})', str(filename))
    return match.group(1) if match else "00000000"

# ==========================================
# 🛠️ 核心引擎：通用檔案讀取與處理 (瘦身關鍵)
# ==========================================
def process_b2_files(files, target_col_keyword, val_col_suffix):
    """通用的檔案讀取、合併與動態判定引擎"""
    if not files:
        return pd.DataFrame()

    df_list = []
    today_data = {}
    latest_col_name = f"{extract_date_from_name(files[0])[-4:]}{val_col_suffix}"

    for idx, f in enumerate(files):
        try:
            # 讀取並標準化欄位名稱
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '股票代號', name_col: '股票名稱'})
            
            # 💡 記憶體瘦身：將字串轉為 category 型態，大幅節省記憶體
            df['股票代號'] = df['股票代號'].astype(str).str.strip().astype('category')
            df['股票名稱'] = df['股票名稱'].astype(str).str.strip().astype('category')
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 尋找目標欄位
            col_today = next((c for c in df.columns if '當日' in c and target_col_keyword in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and target_col_keyword in c), None)
            
            if idx == 0 and col_today:
                today_data = dict(zip(df['股票代號'], pd.to_numeric(df[col_today], errors='coerce').astype('float32')))
                
            if col_5d:
                col_name = f"{d_label}{val_col_suffix}"
                # 💡 記憶體瘦身：數值欄位強制轉為 float32
                df_s = df[['股票代號', '股票名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: col_name})
                df_s[col_name] = pd.to_numeric(df_s[col_name], errors='coerce').astype('float32')
                df_list.append(df_s)
        except Exception:
            continue

    if not df_list:
        return pd.DataFrame()

    # 高效合併所有日期的 DataFrame
    final_df = reduce(lambda left, right: pd.merge(left, right, on=['股票代號', '股票名稱'], how='outer'), df_list)
    final_df = final_df.fillna(0.0) # 保持數值型態，不要填入字串

    if latest_col_name in final_df.columns:
        final_df = final_df.sort_values(by=latest_col_name, ascending=False)
        
        # 判定動態 (取代原本複雜的邏輯)
        def get_trend(row):
            code = row['股票代號']
            base = row.get(latest_col_name, 0.0)
            today = today_data.get(code, None)
            
            if pd.isna(today): return "⚪ 觀望 (無資料)"
            
            # 👇 這裡加上 :.2f 限制小數點後兩位
            val_str = f"({today:.2f}%)"
            
            if "發行數" in val_col_suffix:
                if base == 0: return f"🆕 今日突擊卡位 {val_str}" if today > 0 else "💤 籌碼沉澱中"
                if today < 0: return f"🚨 轉賣反轉 {val_str}"
                elif today > 0: return f"🔥 持續加碼 {val_str}"
                return "🔄 今日量縮持平"
            else:
                if today > 0: return f"{'🔥 強延續' if today > base else '⚠️ 趨緩'} {val_str}"
                elif today < 0: return f"{'🚨 劇烈倒貨' if abs(today) > abs(base) else '📉 調節洗盤'} {val_str}"
                return f"🔄 持平 {val_str}"

        final_df.insert(2, '今日短動態', final_df.apply(get_trend, axis=1))

    return final_df

# ==========================================
# 💡 效能救星 1：快取所有的檔案讀取、合併與運算
# ==========================================
@st.cache_data(show_spinner=False, ttl=300)
def get_cached_b2_data(DATA_DIR):
    """將 B2 四大區塊的資料一次性讀取與合併，並存入快取記憶體中"""
    
    files_21 = sorted(glob.glob(os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")), reverse=True)[:10]
    files_22 = sorted(glob.glob(os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")), reverse=True)[:10]
    files_23 = sorted(glob.glob(os.path.join(DATA_DIR, "*外資買超佔發行張數*.csv")), key=extract_date_from_name, reverse=True)[:10]
    files_24 = sorted(glob.glob(os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")), key=extract_date_from_name, reverse=True)[:10]

    df_21 = process_b2_files(files_21, target_col_keyword='買', val_col_suffix='成交比%')
    df_22 = process_b2_files(files_22, target_col_keyword='買', val_col_suffix='成交比%')
    df_23 = process_b2_files(files_23, target_col_keyword='買賣超佔發行張數', val_col_suffix='發行數%')
    df_24 = process_b2_files(files_24, target_col_keyword='買賣超佔發行張數', val_col_suffix='發行數%')

    return df_21, df_22, df_23, df_24


# ==========================================
# 🚀 局部渲染魔法：四個獨立的 Fragment
# ==========================================
def render_block(df, title, keys, is_block_1=False):
    st.write("---")
    if is_block_1:
        st.markdown("""
        <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                    border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; 
                    border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
            <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">法人掃貨</h2>
        </div>
        """, unsafe_allow_html=True)
        
    st.header(title)
    if df is not None and not df.empty:
        if "成交量" in title:
            st.info("動態 🔥 強延續 (買盤加速) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (強烈賣出)")
            
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key=keys[0])
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key=keys[1])
        
        # 修正：先轉回 string 才能做 len() 和 endswith() 判斷
        code_str = df['股票代號'].astype(str)
        mask = (code_str.str.len() == 4)
        if show_etf: mask |= ((code_str.str.len() >= 5) & (~code_str.str.endswith('B')))
        if show_bond: mask |= code_str.str.endswith('B')
        
        display_df = df[mask].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning(f"⚠️ 記憶體中無 {title} 數據。")

@st.fragment
def render_b2_1(df_21): render_block(df_21, "外資 5 日 買超佔標的成交量", ["fo_etf_v9", "fo_bond_v9"], True)

@st.fragment
def render_b2_2(df_22): render_block(df_22, "投信 5 日 買超佔標的成交量", ["sitc_etf_v9", "sitc_bond_v9"])

@st.fragment
def render_b2_3(df_23): render_block(df_23, "外資 5 日 買超佔公司發行張數", ["foreign_etf_final_v3", "foreign_bond_final_v3"])

@st.fragment
def render_b2_4(df_24): render_block(df_24, "投信 5 日 買超佔公司發行張數", ["sitc_etf_final_v3", "sitc_bond_final_v3"])

# ==========================================
# 🖼️ 前台畫面渲染主程式
# ==========================================
def show_b2_page(DATA_DIR):
    """B2 專屬頁面 UI 渲染"""
    df_21, df_22, df_23, df_24 = get_cached_b2_data(DATA_DIR)
    
    # 👇 補上這段：將資料寫入 session_state，讓懸浮卡片與選股過濾頁面能抓到資料
    st.session_state['df_blk2_1'] = df_21
    st.session_state['df_blk2_2'] = df_22
    st.session_state['df_blk2_3'] = df_23
    st.session_state['df_blk2_4'] = df_24
    
    # 同時寫入簡寫 key，以對接 weight_backtest_page.py 裡面的 KEY_MAP
    st.session_state['b2_1'] = df_21
    st.session_state['b2_2'] = df_22
    st.session_state['b2_3'] = df_23
    st.session_state['b2_4'] = df_24

    # 利用 4 個獨立的 Fragment 渲染
    render_b2_1(df_21)
    render_b2_2(df_22)
    render_b2_3(df_23)
    render_b2_4(df_24)
    
def sync_b2_data(DATA_DIR):
    """供背景或其他頁面喚醒 B2 資料使用"""
    df_21, df_22, df_23, df_24 = get_cached_b2_data(DATA_DIR)
    st.session_state['df_blk2_1'] = df_21
    st.session_state['df_blk2_2'] = df_22
    st.session_state['df_blk2_3'] = df_23
    st.session_state['df_blk2_4'] = df_24
    st.session_state['b2_1'] = df_21
    st.session_state['b2_2'] = df_22
    st.session_state['b2_3'] = df_23
    st.session_state['b2_4'] = df_24
