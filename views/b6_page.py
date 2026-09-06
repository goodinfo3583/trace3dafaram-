# views/b6_page.py
import streamlit as st
import pandas as pd
import os
import glob
import yfinance as yf
from utils.data_utils import robust_read_csv

# ==========================================
# 🌟 區塊 6 專屬工具函數區 (純運算，無 UI)
# ==========================================
def clean_number_for_display(val):
    """清理數字顯示格式"""
    try:
        if pd.isna(val) or str(val).strip() == '-': return '-'
        f = float(str(val).replace(',', ''))
        return str(int(f)) if f.is_integer() else str(f).rstrip('0').rstrip('.')
    except: return str(val)

# 💡 效能救星 1：快取歷史鉅額交易的檔案合併 (10分鐘更新一次)
@st.cache_data(show_spinner=False, ttl=600)
def build_historical_block_matrix(DATA_DIR):
    """歷史矩陣建立器"""
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
            col_name = short_date
            if col_name not in date_cols: date_cols.append(col_name)
            
            df = robust_read_csv(f)
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
        valid_date_cols.sort(reverse=True)
        
        if valid_date_cols:
            latest_col = valid_date_cols[0]
            new_latest_col = f"▼{latest_col}"
            master_df = master_df.rename(columns={latest_col: new_latest_col})
            valid_date_cols[0] = new_latest_col
            
        master_df = master_df[['代號', '股票名稱'] + valid_date_cols]
        if valid_date_cols:
            master_df = master_df.sort_values(by=valid_date_cols[0], ascending=False)
            
    return master_df, [os.path.basename(f) for f in target_files]

# 💡 效能救星 2：把 yfinance 報價跟今日鉅額交易計算快取起來 (5 分鐘更新一次)
@st.cache_data(show_spinner=False, ttl=300)
def get_cached_b6_today(DATA_DIR):
    """處理今日鉅額交易，並抓取即時收盤價"""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*鉅額*.csv")), reverse=True)
    if not files:
        return None, None
        
    latest_file = files[0]
    block_date = os.path.basename(latest_file).replace('-', '').replace('_', '')[:8]
    df_block = robust_read_csv(latest_file)
    
    display_df = None
    dynamic_price_col = f"▼{block_date[-4:]} 成交價"

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
                '成交價': lambda x: ' / '.join(sorted(set([f"{float(i):.2f}".rstrip('0').rstrip('.') for i in x.dropna()]))),
                '成交股數': 'sum',
                '成交金額': 'sum'
            }).reset_index()

            grouped_block['成交張數'] = (grouped_block['成交股數'] / 1000).astype(int).apply(lambda x: f"{x:,}")
            grouped_block['總額(億)'] = (grouped_block['成交金額'] / 100000000).apply(lambda x: f"{x:.2f}".rstrip('0').rstrip('.'))

            # --- YFinance 股價獲取 ---
            unique_ids = grouped_block['代號'].unique()
            close_price_dict = {}
            if len(unique_ids) > 0:
                tw_tickers = [f"{sid}.TW" for sid in unique_ids]
                two_tickers = [f"{sid}.TWO" for sid in unique_ids]
                all_tickers = " ".join(tw_tickers + two_tickers)
                try:
                    df_yf = yf.download(all_tickers, period="5d", progress=False)
                    if not df_yf.empty and 'Close' in df_yf:
                        close_data = df_yf['Close']
                        if isinstance(close_data, pd.Series):
                            if hasattr(close_data, 'name') and close_data.name:
                                close_data = close_data.to_frame(name=close_data.name)
                            else:
                                close_data = close_data.to_frame()

                        for sid in unique_ids:
                            tkr_tw, tkr_two = f"{sid}.TW", f"{sid}.TWO"
                            target_tkr = None
                            if tkr_tw in close_data.columns and not close_data[tkr_tw].dropna().empty: target_tkr = tkr_tw
                            elif tkr_two in close_data.columns and not close_data[tkr_two].dropna().empty: target_tkr = tkr_two
                            
                            if target_tkr:
                                last_price = close_data[target_tkr].dropna().iloc[-1]
                                close_price_dict[sid] = str(round(last_price, 2))
                except Exception: pass

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
            
            display_df = grouped_block[['代號', '股票名稱', '交易別', '成交價', '▼收盤價', '成交張數', '總額(億)']].copy()
            display_df = display_df.rename(columns={'成交價': dynamic_price_col})

    return display_df, dynamic_price_col

# ==========================================
# ⚙️ 後台資料引擎 (Data Engine)：寫入 Session
# ==========================================
def sync_b6_data(DATA_DIR):
    """在背景計算歷史矩陣與今日最新鉅額交易，並寫入 Session State 給其它元件存取"""
    # 1. 歷史矩陣處理
    hist_matrix, detected_files = build_historical_block_matrix(DATA_DIR)
    st.session_state['b6_hist_matrix'] = hist_matrix
    st.session_state['b6_hist_files'] = detected_files

    # 2. 今日鉅額交易處理
    display_df, dynamic_price_col = get_cached_b6_today(DATA_DIR)
    st.session_state['b6_today_df'] = display_df
    st.session_state['b6_dynamic_price_col'] = dynamic_price_col


# ==========================================
# 🚀 局部渲染魔法：UI 與表格的結界
# ==========================================
@st.fragment
def render_b6_dashboard(display_df, dynamic_price_col, hist_matrix, detected_files):
    tab_today, tab_hist = st.tabs(["🔹 今日最新鉅額交易", "🔹 歷史防守價追蹤表"])

    with tab_today:
        if display_df is not None and not display_df.empty:
            def highlight_price(row):
                styles = [''] * len(row)
                try:
                    target_idx = row.index.get_loc(dynamic_price_col)
                    prices = [float(p) for p in str(row[dynamic_price_col]).split(' / ')]
                    avg_p = sum(prices) / len(prices)
                    c_p = float(str(row['▼收盤價']).replace(',', ''))
                    
                    if c_p > avg_p: styles[target_idx] = 'color: #FF4B4B; font-weight: bold;'
                    elif c_p == avg_p: styles[target_idx] = 'color: #FFA500; font-weight: bold;'
                    else: styles[target_idx] = 'color: #00E272; font-weight: bold;'
                except: pass
                return styles

            st.dataframe(display_df.style.apply(highlight_price, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("🕒 目前查無今日鉅額交易資料，請確認資料夾中是否有對應的 CSV 檔案。")

    with tab_hist:
        if detected_files:
            st.caption(f"📡 已自動讀取 {len(detected_files)} 天的歷史檔案，組合中...")
            
        if hist_matrix is not None and not hist_matrix.empty:
            st.dataframe(hist_matrix, use_container_width=True, hide_index=True)
        else:
            st.info("📂 資料夾內尚無足夠的歷史交易紀錄，請確認檔名包含「鉅額」字樣。")

# ==========================================
# 🖼️ 畫面渲染主程式
# ==========================================


    """B6 專屬頁面 UI 渲染"""
    if 'b6_today_df' not in st.session_state:
        with st.spinner("⏳ 載入鉅額交易與即時收盤價中..."):
            sync_b6_data(DATA_DIR)

    st.write("---")
    st.markdown("<div id='section-6'></div>", unsafe_allow_html=True)
    st.markdown("### 鉅額交易動向", unsafe_allow_html=True)
    st.write("💡 鉅額交易有時為大戶私下換手籌碼，成交價可作為「支撐/壓力」的防守線；如果短線跌破建議嚴設停損。")

    # 💡 呼叫被 Fragment 保護的互動區塊，傳入 Session state 的資料
    render_b6_dashboard(
        st.session_state.get('b6_today_df'),
        st.session_state.get('b6_dynamic_price_col'),
        st.session_state.get('b6_hist_matrix'),
        st.session_state.get('b6_hist_files', [])
    )
