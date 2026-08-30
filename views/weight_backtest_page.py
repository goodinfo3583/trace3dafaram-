# views/weight_backtest_page.py
import streamlit as st
import pandas as pd
import re
import os
import glob
import datetime

# ==========================================
# 🌟 導入背景喚醒引擎
# ==========================================
try:
    from views.sidebar import ensure_b1_to_b5_loaded
except ImportError:
    def ensure_b1_to_b5_loaded(DATA_DIR): pass

try:
    from views.b6_page import sync_b6_data
except ImportError:
    def sync_b6_data(DATA_DIR): pass

try:
    from views.b7_page import sync_b7_data, sync_pledge_data, sync_pledge_history_data
except ImportError:
    def sync_b7_data(DATA_DIR): pass
    def sync_pledge_data(DATA_DIR): pass
    def sync_pledge_history_data(DATA_DIR): pass

# ==========================================
# 🌟 萬能鑰匙：對接全站暫存變數
# ==========================================
KEY_MAP = {
    'b0_price': ['b0_price'],
    'b1_final_df': ['b1_final_df', 'my_final_df'],
    'b1_down_final_df': ['b1_down_final_df'],
    'b1_foreign_df': ['b1_foreign_df'],
    'b2_1': ['b2_1', 'df_blk2_1'],
    'b2_2': ['b2_2', 'df_blk2_2'],
    'b2_3': ['b2_3', 'df_blk2_3'],
    'b2_4': ['b2_4', 'df_blk2_4'],
    'b3_main': ['b3_main', 'df_blk3_main'],
    'b4_margin_pct': ['b4_margin_pct', 'df_margin_pct'],
    'b4_short_pct': ['b4_short_pct', 'df_short_pct'],
    'b4_margin_plus_pct': ['b4_margin_plus_pct', 'df_margin_plus_pct'],
    'b4_margin_vol': ['b4_margin_vol', 'df_margin_vol'],
    'b4_short_vol': ['b4_short_vol', 'df_short_vol'],
    'b4_margin_plus_vol': ['b4_margin_plus_vol', 'df_margin_plus_vol'],
    'b4_margin_inc_pct': ['b4_margin_inc_pct', 'df_margin_inc_pct'],
    'b4_short_inc_pct': ['b4_short_inc_pct', 'df_short_inc_pct'],
    'b4_margin_inc_vol': ['b4_margin_inc_vol', 'df_margin_inc_vol'],
    'b4_short_inc_vol': ['b4_short_inc_vol', 'df_short_inc_vol'],
    'b4_short_inc_amt': ['b4_short_inc_amt', 'df_short_inc_amt'],
    'b4_short_dec_amt': ['b4_short_dec_amt', 'df_short_dec_amt'],
    'b5_1000': ['b5_1000', 'df_blk5_1000', 'df_blk5'],
    'b5_800': ['b5_800', 'df_blk5_800'],
    'b5_600': ['b5_600', 'df_blk5_600'],
    'b5_400': ['b5_400', 'df_blk5_400'],
    'b5_resonance': ['b5_resonance', 'df_b5_resonance', 'df_resonance', 'df_長短線共振'],
    'b5_double': ['b5_double', 'df_b5_double', 'df_double', 'df_雙向共振'],
    'b6_today': ['b6_today', 'b6_today_df'],      
    'b6_hist': ['b6_hist', 'b6_hist_matrix'],     
    'b7_main': ['b7_main', 'df_blk7_main', 'df_b7_main'],
    'b7_pledge': ['b7_pledge', 'df_pledge', 'df_b7_pledge'],
    'b7_pledge_history': ['b7_pledge_history', 'df_pledge_history', 'df_b7_pledge_history']
}

def get_df(primary_key):
    for k in KEY_MAP.get(primary_key, [primary_key]):
        df = st.session_state.get(k)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df.copy()
    return pd.DataFrame()

def clean_stock_id(df):
    if df.empty: return df
    col_id = '股票代號' if '股票代號' in df.columns else ('代號' if '代號' in df.columns else None)
    if col_id:
        df['統一代號'] = df[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    return df

# ==========================================
# 🌟 數據潔癖最終版：嚴格檔名過濾 + 強制數值轉換 + 防禦空值覆蓋
# ==========================================
def sync_b0_data(DATA_DIR):
    import os, glob, re
    import pandas as pd
    
    # 🎯 防線 1：絕對嚴格鎖定「成交價」三個字，阻絕其他籌碼檔案干擾
    search_patterns = [os.path.join(DATA_DIR, "*成交價*.csv")]
    files = []
    for pattern in search_patterns:
        files.extend(glob.glob(pattern))
    if not files: return
    
    all_dfs = []
    # 步驟 1：讀取並以「日期」定錨
    for f in files:
        df = None 
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                # 🎯 防線 2：統一先用字串讀取，避免 Pandas 被千分位逗號干擾導致型態錯亂
                df = pd.read_csv(f, encoding=enc, header=0, dtype=str)
                break
            except: pass
            
        if df is not None and not df.empty:
            # 清除所有欄位名稱的隱形空白與換行符號
            df.columns = [re.sub(r'[\s\n\r\t\u3000\ufeff]+', '', str(c)) for c in df.columns]
            
            c_code = next((c for c in df.columns if '代號' in c), None)
            date_col = next((c for c in df.columns if '日期' in c), None)
            
            if c_code and date_col:
                df['統一代號'] = df[c_code].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df['標準日期'] = df[date_col].astype(str).str.strip()
                
                # 🎯 防線 3：強力清洗數值！拔除逗號並轉為乾淨數字
                vol_col = next((c for c in df.columns if c in ['成交張數', '總量', '成交量', '累積成交張數', '張數']), None)
                if vol_col:
                    df['成交張數_num'] = pd.to_numeric(df[vol_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    df['成交張數'] = df['成交張數_num'] 
                else:
                    df['成交張數_num'] = 0
                    df['成交張數'] = 0

                amt_col = next((c for c in df.columns if c in ['成交額(百萬)', '成交金額', '成交額', '總金額']), None)
                if amt_col:
                    df['成交額_num'] = pd.to_numeric(df[amt_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    df['成交額(百萬)'] = df['成交額_num']
                else:
                    df['成交額_num'] = 0
                    df['成交額(百萬)'] = 0
                    
                # 確保 PER、成交價、漲跌幅 被正確轉換，避免在透視鏡中變成空字串
                if 'PER' in df.columns:
                    df['PER'] = pd.to_numeric(df['PER'].astype(str).str.replace(',', ''), errors='coerce')
                if '成交' in df.columns:
                    df['成交'] = pd.to_numeric(df['成交'].astype(str).str.replace(',', ''), errors='coerce')
                if '漲跌幅' in df.columns:
                    df['漲跌幅'] = pd.to_numeric(df['漲跌幅'].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce')

                all_dfs.append(df)
                
    if not all_dfs: return
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 🎯 防線 4：強者生存去重法！同一天若有多筆資料，優先保留「成交張數最大」的那筆，絕不讓空資料上位
    combined_df = combined_df.sort_values(by=['統一代號', '標準日期', '成交張數_num'], ascending=[True, True, False])
    combined_df = combined_df.drop_duplicates(subset=['統一代號', '標準日期'], keep='first')
    
    # 找出系統中真實存在的最新日期
    unique_dates = sorted(combined_df['標準日期'].unique(), reverse=True)
    if not unique_dates: return
    latest_date = unique_dates[0]
    
    # 取出最新一日資料
    df_today = combined_df[combined_df['標準日期'] == latest_date].copy()
    
    # 嚴格依照日期排排站，抓出真材實料的 5 天
    sorted_df = combined_df.sort_values(by=['統一代號', '標準日期'], ascending=[True, False])
    top5_df = sorted_df.groupby('統一代號').head(5)
    
    # 精準計算 5 日均量與 5 日均額
    avg_data = top5_df.groupby('統一代號').agg(
        **{
            '5日均量': ('成交張數_num', 'mean'),
            '5日均額': ('成交額_num', 'mean')
        }
    ).reset_index()
        
    df_today = pd.merge(df_today, avg_data, on='統一代號', how='left')
    df_today['5日均量'] = df_today['5日均量'].round(0)
    df_today['5日均額'] = df_today['5日均額'].round(2)
    
    df_today['股價日期'] = latest_date
        
    def get_vp_status(row):
        pct = row.get('漲跌幅', 0)
        if pd.isna(pct): pct = 0
        vol = row.get('成交張數_num', 0)
        avg_v = row.get('5日均量', 0)
        if avg_v == 0 or vol == 0: return "⚪ 無明顯動能"
        ratio = vol / avg_v
        if ratio >= 1.5: v_stat = "放量"
        elif ratio <= 0.7: v_stat = "縮量"
        else: v_stat = "平量"
        if pct >= 4.0: p_stat = "大漲"
        elif pct > 1.5: p_stat = "價升"
        elif pct >= -1.5: p_stat = "滯漲"
        elif pct > -4.0: p_stat = "小跌"
        else: p_stat = "大跌"
        comb = f"{v_stat}{p_stat}"
        mapping = {
            "放量大漲": "🚀 放量大漲 (量價齊升，持續看漲)", "縮量大漲": "🔒 縮量大漲 (鎖倉高控盤，延續上漲)", "平量大漲": "✈️ 平量大漲 (一致看漲無拋壓，加速上漲)",
            "縮量價升": "📈 價升量縮 (量價背離，下方承接看拉高)", "放量滯漲": "⚠️ 放量滯漲 (拋壓增大，即將見頂反轉)", "平量滯漲": "⏸️ 平量滯漲 (拋壓增大，高位見頂)",
            "縮量小跌": "📉 縮量小跌 (主力洗盤止跌，擇機進場)", "放量小跌": "🛡️ 放量小跌 (見底信號，越跌越買反轉)", "平量小跌": "🥀 平量價縮 (下跌中繼，弱反彈信號)",
            "縮量大跌": "☠️ 縮量大跌 (一致看空無承接，加速下跌)", "放量大跌": "🩸 放量大跌 (跟風砸盤，高位出貨持續跌)", "平量大跌": "🕳️ 平量大跌 (一致看空無承接，加速下跌)"
        }
        return mapping.get(comb, "⚖️ 溫和震盪整理")

    df_today['B0_量價狀態'] = df_today.apply(get_vp_status, axis=1)
    st.session_state['b0_price'] = df_today
# ==========================================
# 🌟 主程式
# ==========================================
def show_weight_backtest_page(STOCK_DICT, DATA_DIR="data"):
    if 'b0_price' not in st.session_state: sync_b0_data(DATA_DIR)
    ensure_b1_to_b5_loaded(DATA_DIR)
    if 'b6_today_df' not in st.session_state: sync_b6_data(DATA_DIR)
    if 'b7_main' not in st.session_state: sync_b7_data(DATA_DIR)
    if 'b7_pledge' not in st.session_state: sync_pledge_data(DATA_DIR)
    if 'b7_pledge_history' not in st.session_state: sync_pledge_history_data(DATA_DIR)

    st.markdown("<h2 style='color: #38BDF8;'>權重自訂與勝率回測寶庫</h2>", unsafe_allow_html=True)
    st.caption("打造專屬於您的選股邏輯，透過多重條件交集與大數據計分，找出最具爆發力的潛力股。")
    st.write("---")

    # 0. 建立完美全市場候選池
    pool_dict = {}
    if STOCK_DICT:
        for v in STOCK_DICT.values():
            sid = str(v.get("id", "")).strip()
            if sid: pool_dict[sid] = {"統一代號": sid, "股票名稱": v.get("name", ""), "產業別": v.get("industry", "未分類")}
                
    df_b1_raw = clean_stock_id(get_df('b1_final_df'))
    if not df_b1_raw.empty:
        for _, row in df_b1_raw.iterrows():
            sid = str(row['統一代號']).strip()
            if sid and sid not in pool_dict: pool_dict[sid] = {"統一代號": sid, "股票名稱": str(row.get('股票名稱', '')), "產業別": "ETF/基金/其他"}
                
    for b2_key in ['b2_1', 'b2_2', 'b2_3', 'b2_4']:
        df_b2_tmp = clean_stock_id(get_df(b2_key))
        if not df_b2_tmp.empty:
            for _, row in df_b2_tmp.iterrows():
                sid = str(row['統一代號']).strip()
                if sid and sid not in pool_dict: pool_dict[sid] = {"統一代號": sid, "股票名稱": str(row.get('股票名稱', '')), "產業別": "ETF/基金/其他"}

    for b4_key in ['b4_margin_pct', 'b4_short_pct', 'b4_margin_plus_pct', 'b4_margin_inc_pct', 'b4_short_inc_pct']:
        df_b4_tmp = clean_stock_id(get_df(b4_key))
        if not df_b4_tmp.empty:
            for _, row in df_b4_tmp.iterrows():
                sid = str(row['統一代號']).strip()
                if sid and sid not in pool_dict: pool_dict[sid] = {"統一代號": sid, "股票名稱": str(row.get('股票名稱', '')), "產業別": "ETF/基金/其他"}

    base_df = pd.DataFrame(list(pool_dict.values()))
    if base_df.empty:
        st.warning("⚠️ 無法建立候選池，請確認資料庫狀態。")
        return

    # 1. 第一關：過濾器面版
    col_title, col_reset = st.columns([3, 1])
    with col_title:
        st.markdown(f"#### 1️⃣ 設定嚴格過濾條件 (目前總候選池共 {len(base_df)} 檔)")
    with col_reset:
        def reset_filters():            
            st.session_state['filter_b0_price'] = (0.0, 25000.0)
            st.session_state['filter_b0_vol'] = 0
            st.session_state['filter_b0_amt'] = 0.0
            st.session_state['filter_b0_pct'] = (-10.0, 10.0)
            st.session_state['filter_b0_per'] = 0.0
            st.session_state['filter_b0_exclude_loss'] = False
            st.session_state['filter_b0_vp_status'] = [] 
            st.session_state['filter_b1_delta'] = False
            st.session_state['filter_b1_5d'] = False
            st.session_state['filter_b1_20d'] = False
            st.session_state['filter_b1_60d'] = False
            st.session_state['filter_b1_120d'] = False
            st.session_state['filter_b1_ratio'] = (0.0, 100.0)
            st.session_state['filter_b1_5d_chg'] = (-100.0, 100.0)
            st.session_state['filter_b1_60d_chg'] = (-100.0, 100.0)
            st.session_state['filter_b1_20d_chg'] = (-100.0, 100.0)
            st.session_state['filter_b1_120d_chg'] = (-100.0, 100.0)
            st.session_state['filter_b1_radio'] = "交集 (必須同時符合勾選的所有特徵)"
            st.session_state['filter_b1_multi'] = []
            
            st.session_state['filter_b2_top_n'] = 50
            st.session_state['filter_b2_1'] = False
            st.session_state['filter_b2_2'] = False
            st.session_state['filter_b2_3'] = False
            st.session_state['filter_b2_4'] = False
            st.session_state['filter_b2_radio'] = "交集 (必須同時符合勾選特徵)"
            st.session_state['filter_b2_multi'] = []
            
            st.session_state['filter_b3_fo_day'] = False
            st.session_state['filter_b3_fo_day_n'] = 1
            st.session_state['filter_b3_it_day'] = False
            st.session_state['filter_b3_it_day_n'] = 1
            st.session_state['filter_b3_fo_wk'] = False
            st.session_state['filter_b3_fo_wk_n'] = 1
            st.session_state['filter_b3_it_wk'] = False
            st.session_state['filter_b3_it_wk_n'] = 1
            st.session_state['filter_b3_radio'] = "交集 (必須同時符合勾選特徵)"
            st.session_state['filter_b3_multi'] = []
            
            st.session_state['filter_b4_top_n'] = 50
            for k in ['pct_41', 'vol_41', 'pct_42', 'vol_42', 'pct_43', 'vol_43', 'pct_inc_margin', 'pct_inc_short', 'amt_short_dec', 'amt_short_inc']:
                st.session_state[f'filter_b4_{k}'] = False
                
            st.session_state['filter_b4_price_chg'] = (-10.0, 10.0)
            for k in ['acc_margin_dec', 'acc_sbl_dec', 'acc_margin_inc', 'acc_sbl_inc']:
                st.session_state[f'filter_b4_{k}'] = False

            st.session_state['filter_b4_radio'] = "交集 (必須同時符合勾選特徵)"
            st.session_state['filter_b4_multi'] = []

            for k in ['long_short', 'double', '6w_1000', '6w_800', '6w_600', '6w_400']:
                st.session_state[f'filter_b5_{k}'] = False
            for k in ['1000', '800', '600', '400']:
                st.session_state[f'filter_b5_trend_{k}'] = []
                
            st.session_state['filter_b6_today'] = False
            st.session_state['filter_b6_amt_min'] = 0.0
            st.session_state['filter_b6_status'] = []

            st.session_state['filter_b7_hold_pct'] = (0.0, 100.0)
            st.session_state['filter_b7_pledge_pct'] = (0.0, 100.0)
            st.session_state['filter_b7_hold_trend'] = []
            st.session_state['filter_b7_pledge_trend'] = []
            st.session_state['filter_b7_6m_inc'] = False

        st.button("🧹 清空所有篩選條件", on_click=reset_filters, use_container_width=True)

    filtered_df = base_df.copy()
    any_filter_applied = False

    b0_latest_date_str = "未知日期"
    df_b0 = get_df('b0_price')
    if not df_b0.empty and '股價日期' in df_b0.columns:
        date_raw = str(df_b0['股價日期'].iloc[0])
        # 【精準修正】針對完整的 8 碼日期 (如 20260828) 進行準確切片
        if len(date_raw) >= 8:
            b0_latest_date_str = f"{date_raw[:4]}/{date_raw[4:6]}/{date_raw[6:8]}"
        elif len(date_raw) >= 4:
            b0_latest_date_str = f"2026/{date_raw[-4:-2]}/{date_raw[-2:]}"
        else:
            b0_latest_date_str = date_raw
            
    # --- 模組 B0 ---
    with st.expander(f"💰 B0 基礎價量與估值過濾 (資料基準日: {b0_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 流動性過濾 (剔除冷門股/殭屍股)**")
        c_b0_1, c_b0_2 = st.columns(2)
        b0_vol_min = c_b0_1.number_input("📈 當日成交張數大於 (張)：", min_value=0, value=0, step=500, key="filter_b0_vol")
        b0_amt_min = c_b0_2.number_input("💵 當日成交額大於 (百萬)：", min_value=0.0, value=0.0, step=50.0, key="filter_b0_amt")
        
        st.markdown("**🔹 2. 價格與當日強弱勢過濾**")
        c_b0_3, c_b0_4 = st.columns(2)
        b0_price_range = c_b0_3.slider("🎯 股價區間 (元)：", 0.0, 25000.0, (0.0, 25000.0), 10.0, key="filter_b0_price")
        b0_pct_range = c_b0_4.slider("🚀 當日漲跌幅區間 (%)：", -10.0, 10.0, (-10.0, 10.0), 0.5, key="filter_b0_pct")
        
        st.markdown("**🔹 3. 估值安全過濾**")
        c_b0_5, c_b0_6 = st.columns(2)
        b0_per_max = c_b0_5.number_input("⚖️ 本益比 (PER) 小於 (設定 0 為不限)：", min_value=0.0, value=0.0, step=5.0, key="filter_b0_per")
        st.write("") 
        b0_exclude_loss = c_b0_6.checkbox("🚫 排除虧損公司 (PER 為負或無資料)", key="filter_b0_exclude_loss")

        st.markdown("**🔹 4. 股市量價動能矩陣 (主力照妖鏡)**")
        st.caption("透過自動比對當日價量與「近5日均量」，精準判斷主力是正在洗盤、吸籌還是出貨。")
        vp_options = [
            "🚀 放量大漲 (量價齊升，持續看漲)", "🔒 縮量大漲 (鎖倉高控盤，延續上漲)", "✈️ 平量大漲 (一致看漲無拋壓，加速上漲)",
            "📈 價升量縮 (量價背離，下方承接看拉高)", "⚠️ 放量滯漲 (拋壓增大，即將見頂反轉)", "⏸️ 平量滯漲 (拋壓增大，高位見頂)",
            "📉 縮量小跌 (主力洗盤止跌，擇機進場)", "🛡️ 放量小跌 (見底信號，越跌越買反轉)", "🥀 平量價縮 (下跌中繼，弱反彈信號)",
            "☠️ 縮量大跌 (一致看空無承接，加速下跌)", "🩸 放量大跌 (跟風砸盤，高位出貨持續跌)", "🕳️ 平量大跌 (一致看空無承接，加速下跌)"
        ]
        b0_vp_status = st.multiselect("🎯 可複選您想尋找的量價型態：", vp_options, key="filter_b0_vp_status")

    # --- 模組 B1 ---
    b1_sorted_dates = st.session_state.get('b1_sorted_dates', [])
    b1_latest_date_str = "未知日期"
    if b1_sorted_dates and len(str(b1_sorted_dates[0])) == 8:
        d_str = str(b1_sorted_dates[0])
        b1_latest_date_str = f"{d_str[:4]}/{d_str[4:6]}/{d_str[6:]}"
    
    with st.expander(f"📈 B1 法人持股動向 (資料基準日: {b1_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 近期進榜天數與變化**")
        c1, c2, c3, c4, c5 = st.columns(5)
        b1_delta = c1.checkbox("當日△上升 (>0)", key="filter_b1_delta")
        b1_5d = c2.checkbox("🔴 5日上榜", key="filter_b1_5d")
        b1_20d = c3.checkbox("🟡 20日上榜", key="filter_b1_20d")
        b1_60d = c4.checkbox("🟢 60日上榜", key="filter_b1_60d")
        b1_120d = c5.checkbox("🔵 120日上榜", key="filter_b1_120d")

        st.markdown("**🔹 2. 法人持股比例區間 (%)**")
        b1_ratio_min, b1_ratio_max = st.slider(
            "設定過濾範圍 (設定為 0~100 代表不作限制)：", 
            min_value=0.0, max_value=100.0, value=(0.0, 100.0), step=0.5, key="filter_b1_ratio"
        )

        st.markdown("**🔹 3. 區間累計持股增減 (ΔChange %)**")
        c_chg1, c_chg2 = st.columns(2)
        with c_chg1:
            b1_5d_chg = st.slider("5日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5, key="filter_b1_5d_chg")
            b1_60d_chg = st.slider("60日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5, key="filter_b1_60d_chg")
        with c_chg2:
            b1_20d_chg = st.slider("20日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5, key="filter_b1_20d_chg")
            b1_120d_chg = st.slider("120日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5, key="filter_b1_120d_chg")

        st.markdown("**🔹 4. 最新動態特徵**")
        b1_trend_logic = st.radio("特徵篩選邏輯：", ["交集 (必須同時符合勾選的所有特徵)", "聯集 (符合其中任一特徵即可)"], horizontal=True, key="filter_b1_radio")
        trend_options = [
            "📈 上升", "📉 下降", "🪜 階梯吸籌", "🛡️ 穩健吸籌", "⚠️ 趨緩", 
            "🚀 衝進🔴5日榜單", "🚀 衝進🟡20日榜單", "🚀 衝進🟢60日榜單", "🚀 衝進🔵120日榜單"
        ]
        b1_trends = st.multiselect("請選擇要過濾的動態特徵：", trend_options, key="filter_b1_multi")

    # --- 模組 B2 ---
    b2_latest_date_str = "未知日期"
    df_b2_1_tmp = get_df('b2_1')
    if not df_b2_1_tmp.empty:
        for c in df_b2_1_tmp.columns:
            if "成交比%" in c:
                raw_date = c.replace("成交比%", "")
                if len(raw_date) == 4: b2_latest_date_str = f"2026/{raw_date[:2]}/{raw_date[2:]}"
                else: b2_latest_date_str = raw_date
                break

    with st.expander(f"🚀 B2 法人突擊掃貨 (資料基準日: {b2_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 掃貨榜單**")
        b2_top_n = st.slider("👑 排名過濾：設定最新進榜的擷取範圍 (名次)", min_value=10, max_value=300, value=50, step=10, key="filter_b2_top_n")
        c_b2_1, c_b2_2 = st.columns(2)
        b2_1_chk = c_b2_1.checkbox(f"外資買超佔【5日成交量】(前 {b2_top_n} 名)", key="filter_b2_1")
        b2_2_chk = c_b2_2.checkbox(f"投信買超佔【5日成交量】(前 {b2_top_n} 名)", key="filter_b2_2")
        b2_3_chk = c_b2_1.checkbox(f"外資買超佔【5日發行數】(前 {b2_top_n} 名)", key="filter_b2_3")
        b2_4_chk = c_b2_2.checkbox(f"投信買超佔【5日發行數】(前 {b2_top_n} 名)", key="filter_b2_4")

        st.markdown("**🔹 2. 突擊動態特徵**")
        b2_trend_logic = st.radio("B2 特徵篩選邏輯：", ["交集 (必須同時符合勾選特徵)", "聯集 (符合任一即可)"], horizontal=True, key="filter_b2_radio")
        b2_trend_display_map = {
            "🔥 強延續": "🔥 強延續 (當日買盤加速 > 5日基準)", "🔥 持續加碼": "🔥 持續加碼 (當日買佔發行 > 0%)",
            "🆕 今日突擊卡位": "🆕 今日突擊卡位 (近5日未進榜，今日首度買超)", "⚠️ 趨緩": "⚠️ 趨緩 (當日續買，但力道 < 5日基準)",
            "🔄 持平": "🔄 持平 (當日成交比 = 0%)", "🔄 今日量縮持平": "🔄 今日量縮持平 (當日發行比 = 0%)",
            "📉 調節洗盤": "📉 調節洗盤 (當日微幅賣超調節)", "💤 籌碼沉澱中": "💤 籌碼沉澱中 (近5日未進榜且當日無買超)",
            "🚨 轉賣反轉": "🚨 轉賣反轉 (當日賣超 < 0%)", "🚨 劇烈倒貨": "🚨 劇烈倒貨 (當日強烈賣出)", "⚪ 觀望": "⚪ 觀望 (當日無資料)"
        }
        selected_display_trends = st.multiselect("可複選突擊動態：", list(b2_trend_display_map.values()), key="filter_b2_multi")
        b2_trends = [raw_trend for d_trend in selected_display_trends for raw_trend, desc in b2_trend_display_map.items() if d_trend == desc]
    
    # --- 模組 B3 ---
    b3_latest_date_str = "未知日期"
    df_b3_tmp = get_df('b3_main')
    if not df_b3_tmp.empty and 'b3_data' in st.session_state:
        dates = [d for _, d in st.session_state['b3_data'].values() if d and d != "00000000"]
        if dates: b3_latest_date_str = f"2026/{max(dates)[4:6]}/{max(dates)[6:]}"

    with st.expander(f"🔥 B3 法人連續買超 (資料基準日: {b3_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 連買榜單**")
        col_b3_1, col_b3_1_s, col_b3_2, col_b3_2_s = st.columns([1.2, 1, 1.2, 1])
        with col_b3_1: b3_fo_day_chk = st.checkbox("🌐 外資日連買", key="filter_b3_fo_day")
        with col_b3_1_s: b3_fo_day_n = st.number_input("連買大於(天)", min_value=1, value=1, step=1, key="filter_b3_fo_day_n", label_visibility="collapsed")
        with col_b3_2: b3_it_day_chk = st.checkbox("🏦 投信日連買", key="filter_b3_it_day")
        with col_b3_2_s: b3_it_day_n = st.number_input("連買大於(天)", min_value=1, value=1, step=1, key="filter_b3_it_day_n", label_visibility="collapsed")

        col_b3_3, col_b3_3_s, col_b3_4, col_b3_4_s = st.columns([1.2, 1, 1.2, 1])
        with col_b3_3: b3_fo_wk_chk = st.checkbox("🌐 外資週連買", key="filter_b3_fo_wk")
        with col_b3_3_s: b3_fo_wk_n = st.number_input("連買大於(週)", min_value=1, value=1, step=1, key="filter_b3_fo_wk_n", label_visibility="collapsed")
        with col_b3_4: b3_it_wk_chk = st.checkbox("🏦 投信週連買", key="filter_b3_it_wk")
        with col_b3_4_s: b3_it_wk_n = st.number_input("連買大於(週)", min_value=1, value=1, step=1, key="filter_b3_it_wk_n", label_visibility="collapsed")

        st.markdown("**🔹 2. 連買動態特徵**")
        b3_trend_logic = st.radio("B3 特徵篩選邏輯：", ["交集 (必須同時符合勾選特徵)", "聯集 (符合任一即可)"], horizontal=True, key="filter_b3_radio")
        b3_trend_options = [
            "🔥 波段認養 (日連買10天以上)", "⚡ 買盤點火 (日連買5~9天)", "🆕 試單觀察 (日連買1~4天)",
            "👑 長線主控 (週連買10週以上)", "🚀 趨勢加溫 (週連買5~9週)", "🌱 週線發動 (週連買1~4週)"
        ]
        selected_b3_trends = st.multiselect("可複選連買動態：", b3_trend_options, key="filter_b3_multi")
        b3_trends = [t.split(" (")[0] for t in selected_b3_trends]

    # --- 模組 B4 ---
    b4_latest_date_str = "未知日期"
    if 'b4_squeeze_radar' in st.session_state and st.session_state['b4_squeeze_radar']['date']:
        b4_latest_date_str = st.session_state['b4_squeeze_radar']['date']

    with st.expander(f"⚔️ B4 資券動向與雷達 (資料基準日: {b4_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 資券榜單**")
        b4_top_n = st.slider("👑 排名過濾：設定最新進榜的擷取範圍 (名次)", min_value=10, max_value=300, value=50, step=10, key="filter_b4_top_n")
        c_b4_1, c_b4_2 = st.columns(2)
        with c_b4_1:
            b4_41_pct = st.checkbox(f"融資減少幅度【5日累計比】", key="filter_b4_pct_41")
            b4_42_pct = st.checkbox(f"借券賣出減少幅度【5日累計比】", key="filter_b4_pct_42")
            b4_43_pct = st.checkbox(f"融券增加幅度【5日累計比】", key="filter_b4_pct_43")
            b4_inc_margin_pct = st.checkbox(f"融資增加幅度【5日累計比】", key="filter_b4_pct_inc_margin")
            b4_short_dec_amt = st.checkbox(f"借券賣出減少金額【5日累計】", key="filter_b4_amt_short_dec")
        with c_b4_2:
            b4_41_vol = st.checkbox(f"融資減少張數【5日累計張】", key="filter_b4_vol_41")
            b4_42_vol = st.checkbox(f"借券賣出減少張數【5日累計張】", key="filter_b4_vol_42")
            b4_43_vol = st.checkbox(f"融券增加張數【5日累計張】", key="filter_b4_vol_43")
            b4_inc_short_pct = st.checkbox(f"借券賣出增加幅度【5日累計比】", key="filter_b4_pct_inc_short")
            b4_short_inc_amt = st.checkbox(f"借券賣出增加金額【5日累計】", key="filter_b4_amt_short_inc")

        st.markdown("**🔹 2. 今日漲跌幅區間過濾 (%)**")
        b4_price_chg = st.slider("設定漲跌幅區間：", -10.0, 10.0, (-10.0, 10.0), 0.5, key="filter_b4_price_chg")

        st.markdown("**🔹 3. 籌碼加速特徵 (當日資金 > 1千萬且大於5日均)**")
        c_acc1, c_acc2 = st.columns(2)
        b4_acc_margin_dec = c_acc1.checkbox("⏩ 融資加速退場 (破千萬資金)", key="filter_b4_acc_margin_dec")
        b4_acc_sbl_dec = c_acc1.checkbox("⏩ 借券加速回補 (破千萬資金)", key="filter_b4_acc_sbl_dec")
        b4_acc_margin_inc = c_acc2.checkbox("⚠️ 融資加速套牢 (破千萬資金 + 當日下跌)", key="filter_b4_acc_margin_inc")
        b4_acc_sbl_inc = c_acc2.checkbox("⚠️ 借券加速放空 (破千萬資金)", key="filter_b4_acc_sbl_inc")

        st.markdown("**🔹 4. 雷達動態特徵**")
        b4_trend_logic = st.radio("B4 特徵篩選邏輯：", ["交集 (必須同時符合勾選特徵)", "聯集 (符合任一即可)"], horizontal=True, key="filter_b4_radio")
        b4_trend_display_map = {
            "💥 終極": "💥 終極 (法人買超+收紅+融資減.借券減.融券增 3項全中)", "🚀 強軋": "🚀 強軋 (法人買超+收紅+前述資券特徵 3中2)",
            "🔥 點火": "🔥 點火 (法人買超+收紅+前述資券特徵 3中1)", "🔼 進駐": "🔼 進駐 (僅法人買超+收紅，籌碼尚未發動軋空)",
            "☠️ 極危": "☠️ 極危 (法人賣超+收黑+融資增.借券增 2項全中)", "🚨 高危": "🚨 高危 (法人賣超+收黑+前述資券特徵 2中1)", "⚠️ 初危": "⚠️ 初危 (僅法人賣超+收黑)"
        }
        selected_b4_trends_display = st.multiselect("可複選雷達特徵：", list(b4_trend_display_map.values()), key="filter_b4_multi")
        b4_trends = [raw for d in selected_b4_trends_display for raw, desc in b4_trend_display_map.items() if d == desc]
        
    # --- 模組 B5 ---
    b5_latest_date_str = "未知日期"
    df_b5_tmp = get_df('b5_1000')
    if not df_b5_tmp.empty:
        col_latest = next((c for c in df_b5_tmp.columns if c.startswith('▼') and '6周' not in c), None)
        if col_latest: b5_latest_date_str = f"2026/{col_latest.replace('▼', '')[:2]}/{col_latest.replace('▼', '')[2:]}"

    with st.expander(f"🐳 B5 大腿動向 (資料基準日: {b5_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 共振榜單過濾**")
        c_b5_1, c_b5_2 = st.columns(2)
        b5_long_short = c_b5_1.checkbox("🎯 長短線共振 (1000張與400張波段+本週皆同步加碼)", key="filter_b5_long_short")
        b5_double = c_b5_2.checkbox("🎯 雙引擎共振 (1000張與400張本週同步增加)", key="filter_b5_double")

        st.markdown("**🔹 2. 波段吸籌過濾 (6周增減 > 0)**")
        c_b5_6w1, c_b5_6w2, c_b5_6w3, c_b5_6w4 = st.columns(4)
        b5_6w_1000 = c_b5_6w1.checkbox("👑 1000張 6周增加", key="filter_b5_6w_1000")
        b5_6w_800 = c_b5_6w2.checkbox("🦅 800張 6周增加", key="filter_b5_6w_800")
        b5_6w_600 = c_b5_6w3.checkbox("🦉 600張 6周增加", key="filter_b5_6w_600")
        b5_6w_400 = c_b5_6w4.checkbox("🐺 400張 6周增加", key="filter_b5_6w_400")

        st.markdown("**🔹 3. 各級距大戶週動態過濾**")
        trend_options_b5 = ["🚀 劇增", "🔥 大增", "📈 小增", "↗️ 微增", "🔄 持平", "↘️ 微減", "📉 小減", "⚠️ 大減", "🚨 劇減"]
        c_b5_lvl1, c_b5_lvl2 = st.columns(2)
        b5_trend_1000 = c_b5_lvl1.multiselect("👑 1000張大戶週動態：", trend_options_b5, key="filter_b5_trend_1000")
        b5_trend_800 = c_b5_lvl2.multiselect("🦅 800張大戶週動態：", trend_options_b5, key="filter_b5_trend_800")
        c_b5_lvl3, c_b5_lvl4 = st.columns(2)
        b5_trend_600 = c_b5_lvl3.multiselect("🦉 600張大戶週動態：", trend_options_b5, key="filter_b5_trend_600")
        b5_trend_400 = c_b5_lvl4.multiselect("🐺 400張大戶週動態：", trend_options_b5, key="filter_b5_trend_400")

    # --- 模組 B6 ---
    b6_latest_date_str = "未知日期"
    dynamic_price_col_b6 = st.session_state.get('b6_dynamic_price_col')
    if dynamic_price_col_b6 and "▼" in dynamic_price_col_b6:
        date_part = dynamic_price_col_b6.split(' ')[0].replace('▼', '')
        if len(date_part) == 4: b6_latest_date_str = f"2026/{date_part[:2]}/{date_part[2:]}"

    with st.expander(f"💎 B6 鉅額交易動向 (資料基準日: {b6_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 今日鉅額交易過濾**")
        b6_today_chk = st.checkbox("🎯 今日有發生鉅額交易", key="filter_b6_today")
        st.markdown("**🔹 2. 資金規模過濾**")
        b6_amt_min = st.slider("💰 鉅額總額大於 (億)：", min_value=0.0, max_value=50.0, value=0.0, step=0.5, key="filter_b6_amt_min")
        st.markdown("**🔹 3. 防守狀態過濾**")
        b6_status_options = ["🛡️ 防守成功 (收盤 >= 鉅額均價)", "🚨 跌破防線 (收盤 < 鉅額均價)"]
        b6_status_chk = st.multiselect("可精準挑選主力防線狀態：", b6_status_options, key="filter_b6_status")

    # --- 模組 B7 ---
    b7_latest_date_str = "未知月份"
    df_b7_tmp = get_df('b7_main')
    if not df_b7_tmp.empty:
        raw_months = [c.replace('持股%', '') for c in df_b7_tmp.columns if '持股%' in c]
        valid_months = [m for m in raw_months if re.match(r'^\d{2}M\d{2}$', m) or re.match(r'^\d{4,6}$', m)]
        if valid_months:
            best_m = sorted(valid_months, reverse=True)[0]
            if 'M' in best_m: b7_latest_date_str = f"20{best_m.split('M')[0]}/{best_m.split('M')[1]}"
            elif len(best_m) == 6: b7_latest_date_str = f"{best_m[:4]}/{best_m[4:]}"

    with st.expander(f"👔 B7 董監事籌碼動向 (資料基準月: {b7_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 最新董監持股與質押比例 (%)**")
        c_b7_1, c_b7_2 = st.columns(2)
        b7_hold_pct = c_b7_1.slider("🛡️ 董監持股比例區間：", 0.0, 100.0, (0.0, 100.0), 0.5, key="filter_b7_hold_pct")
        b7_pledge_pct = c_b7_2.slider("⚠️ 董監質押比例區間 (拉低以避險)：", 0.0, 100.0, (0.0, 100.0), 0.5, key="filter_b7_pledge_pct")

        st.markdown("**🔹 2. 近月董監持股與質押動態**")
        c_b7_3, c_b7_4 = st.columns(2)
        b7_hold_options = ["🔥 大增", "📈 增", "↗️ 微增", "🔄 持平", "↘️ 微減", "🚨 減/大減"]
        b7_hold_trend = c_b7_3.multiselect("🛡️ 持股增減動態 (尋找內部人加碼)：", b7_hold_options, key="filter_b7_hold_trend")
        b7_pledge_options = ["🚨 暴增", "⚠️ 大增", "↗️ 微增", "➖ 持平", "↘️ 微減", "✅ 大減", "🌟 遽減"]
        b7_pledge_trend = c_b7_4.multiselect("⚠️ 質押增減動態 (尋找質押下降)：", b7_pledge_options, key="filter_b7_pledge_trend")

        st.markdown("**🔹 3. 波段持股過濾**")
        b7_6m_inc = st.checkbox("🎯 近半年董監波段持股增加 (> 0)", key="filter_b7_6m_inc")
        
    # ==========================================
    # 執行過濾邏輯
    # ==========================================
    # B0 過濾
    b0_price_min, b0_price_max = b0_price_range
    b0_pct_min, b0_pct_max = b0_pct_range
    if not df_b0.empty and (b0_vol_min > 0 or b0_amt_min > 0 or b0_price_min > 0 or b0_price_max < 25000.0 or b0_pct_min > -10.0 or b0_pct_max < 10.0 or b0_per_max > 0 or b0_exclude_loss):
        any_filter_applied = True
        b0_mask = pd.Series(True, index=df_b0.index)
        if '成交' in df_b0.columns:
            df_b0['num_price'] = pd.to_numeric(df_b0['成交'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            b0_mask &= df_b0['num_price'].between(b0_price_min, b0_price_max)
        if '漲跌幅' in df_b0.columns:
            df_b0['num_pct'] = pd.to_numeric(df_b0['漲跌幅'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
            b0_mask &= df_b0['num_pct'].between(b0_pct_min, b0_pct_max)
        if '成交張數' in df_b0.columns and b0_vol_min > 0:
            df_b0['num_vol'] = pd.to_numeric(df_b0['成交張數'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            b0_mask &= (df_b0['num_vol'] >= b0_vol_min)
        if '成交額(百萬)' in df_b0.columns and b0_amt_min > 0:
            df_b0['num_amt'] = pd.to_numeric(df_b0['成交額(百萬)'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            b0_mask &= (df_b0['num_amt'] >= b0_amt_min)
        if 'PER' in df_b0.columns:
            df_b0['num_per'] = pd.to_numeric(df_b0['PER'], errors='coerce')
            if b0_per_max > 0: b0_mask &= ((df_b0['num_per'] > 0) & (df_b0['num_per'] <= b0_per_max)) | (df_b0['num_per'].isna())
            if b0_exclude_loss: b0_mask &= (df_b0['num_per'] > 0)
        
        valid_b0_codes = df_b0[b0_mask]['統一代號'].unique()
        filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b0_codes)]
        
    if b0_vp_status and not df_b0.empty and 'B0_量價狀態' in df_b0.columns:
        any_filter_applied = True
        valid_vp_codes = df_b0[df_b0['B0_量價狀態'].isin(b0_vp_status)]['統一代號'].unique()
        filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_vp_codes)]
        
    # B1 過濾
    if not df_b1_raw.empty:
        hit_mask = pd.Series(True, index=df_b1_raw.index)
        b1_checked = False
        if b1_delta:
            b1_checked = True
            df_b1_raw['num_delta'] = pd.to_numeric(df_b1_raw['△'].astype(str).str.replace('%', '', regex=False).str.replace('+', '', regex=False), errors='coerce').fillna(0)
            hit_mask &= (df_b1_raw['num_delta'] > 0)
        if b1_5d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🔴5日')
        if b1_20d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🟡20日')
        if b1_60d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🟢60日')
        if b1_120d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🔵120日')
        if b1_ratio_min > 0.0 or b1_ratio_max < 100.0:
            b1_checked = True
            df_b1_raw['num_ratio'] = pd.to_numeric(df_b1_raw['法人持股'].astype(str).str.replace('%', '', regex=False).replace('未進榜', '0'), errors='coerce').fillna(0)
            hit_mask &= df_b1_raw['num_ratio'].between(b1_ratio_min, b1_ratio_max)
        change_configs = {'5日ΔChange': b1_5d_chg, '20日ΔChange': b1_20d_chg, '60日ΔChange': b1_60d_chg, '120日ΔChange': b1_120d_chg}
        for col_name, (min_val, max_val) in change_configs.items():
            if min_val > -100.0 or max_val < 100.0:
                b1_checked = True
                if col_name in df_b1_raw.columns:
                    df_b1_raw[f'num_{col_name}'] = pd.to_numeric(df_b1_raw[col_name].astype(str).str.replace('%', '', regex=False).str.replace('+', '', regex=False), errors='coerce')
                    hit_mask &= df_b1_raw[f'num_{col_name}'].between(min_val, max_val)
        if b1_trends:
            b1_checked = True
            is_and_logic = "交集" in b1_trend_logic
            trend_mask = pd.Series(True, index=df_b1_raw.index) if is_and_logic else pd.Series(False, index=df_b1_raw.index)
            for trend in b1_trends:
                if "衝進" in trend:
                    core_tag = trend.replace("🚀 衝進", "").replace("榜單", "")
                    current_cond = (df_b1_raw['最新動態'].astype(str).str.contains("衝進", regex=False, na=False) & df_b1_raw['最新動態'].astype(str).str.contains(core_tag, regex=False, na=False))
                else: current_cond = df_b1_raw['最新動態'].astype(str).str.contains(trend, regex=False, na=False)
                if is_and_logic: trend_mask &= current_cond
                else: trend_mask |= current_cond
            hit_mask &= trend_mask
        if b1_checked:
            any_filter_applied = True
            hit_codes = df_b1_raw[hit_mask]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(hit_codes)]
            
    # B2 過濾
    b2_checks = {'b2_1': b2_1_chk, 'b2_2': b2_2_chk, 'b2_3': b2_3_chk, 'b2_4': b2_4_chk}
    for b2_key, is_checked in b2_checks.items():
        if is_checked:
            any_filter_applied = True
            df_b2_tmp = clean_stock_id(get_df(b2_key))
            if not df_b2_tmp.empty:
                latest_col = next((c for c in df_b2_tmp.columns if '%' in c), None)
                if latest_col:
                    df_b2_tmp['num_latest'] = pd.to_numeric(df_b2_tmp[latest_col].astype(str).replace("未進榜", 0), errors='coerce').fillna(0)
                    df_b2_tmp = df_b2_tmp[df_b2_tmp['num_latest'] > 0].head(b2_top_n)
                filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b2_tmp['統一代號'])]
    if b2_trends:
        any_filter_applied = True
        is_and_logic_b2 = "交集" in b2_trend_logic
        b2_dfs = [clean_stock_id(get_df(k)) for k in ['b2_1', 'b2_2', 'b2_3', 'b2_4']]
        b2_combined = pd.concat([df[['統一代號', '今日短動態']] for df in b2_dfs if not df.empty and '今日短動態' in df.columns])
        if not b2_combined.empty:
            b2_dynamics = b2_combined.groupby('統一代號')['今日短動態'].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index()
            trend_mask_b2 = pd.Series(True, index=b2_dynamics.index) if is_and_logic_b2 else pd.Series(False, index=b2_dynamics.index)
            for trend in b2_trends:
                curr_cond = b2_dynamics['今日短動態'].str.contains(trend, regex=False, na=False)
                if is_and_logic_b2: trend_mask_b2 &= curr_cond
                else: trend_mask_b2 |= curr_cond
            filtered_df = filtered_df[filtered_df['統一代號'].isin(b2_dynamics[trend_mask_b2]['統一代號'].unique())]

    # B3 過濾
    df_b3_main = get_df('b3_main')
    if not df_b3_main.empty:
        b3_checks = {'🌐 外資日連買': (b3_fo_day_chk, b3_fo_day_n), '🏦 投信日連買': (b3_it_day_chk, b3_it_day_n), '🌐 外資週連買': (b3_fo_wk_chk, b3_fo_wk_n), '🏦 投信週連買': (b3_it_wk_chk, b3_it_wk_n)}
        for type_name, (is_checked, min_n) in b3_checks.items():
            if is_checked:
                any_filter_applied = True
                df_b3_tmp = clean_stock_id(df_b3_main[(df_b3_main['連買類型'] == type_name) & (df_b3_main['連買週期數'] >= min_n)])
                if not df_b3_tmp.empty: filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b3_tmp['統一代號'])]
        if b3_trends:
            any_filter_applied = True
            is_and_logic_b3 = "交集" in b3_trend_logic
            b3_dynamics = clean_stock_id(df_b3_main.groupby('股票代號')['狀態動態'].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index())
            trend_mask_b3 = pd.Series(True, index=b3_dynamics.index) if is_and_logic_b3 else pd.Series(False, index=b3_dynamics.index)
            for trend in b3_trends:
                curr_cond = b3_dynamics['狀態動態'].str.contains(trend, regex=False, na=False)
                if is_and_logic_b3: trend_mask_b3 &= curr_cond
                else: trend_mask_b3 |= curr_cond
            filtered_df = filtered_df[filtered_df['統一代號'].isin(b3_dynamics[trend_mask_b3]['統一代號'].unique())]

    # B4 過濾
    b4_checks = {'b4_margin_pct': b4_41_pct, 'b4_margin_vol': b4_41_vol, 'b4_short_pct': b4_42_pct, 'b4_short_vol': b4_42_vol, 'b4_margin_plus_pct': b4_43_pct, 'b4_margin_plus_vol': b4_43_vol, 'b4_margin_inc_pct': b4_inc_margin_pct, 'b4_short_inc_pct': b4_inc_short_pct, 'b4_short_dec_amt': b4_short_dec_amt, 'b4_short_inc_amt': b4_short_inc_amt}
    for b4_key, is_checked in b4_checks.items():
        if is_checked:
            any_filter_applied = True
            df_b4_tmp = clean_stock_id(get_df(b4_key))
            if not df_b4_tmp.empty: filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b4_tmp.head(b4_top_n)['統一代號'])]
    if b4_trends:
        any_filter_applied = True
        is_and_logic_b4 = "交集" in b4_trend_logic
        b4_radar_combined = pd.concat([
            clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame()))[['統一代號', '軋空評估']].rename(columns={'軋空評估': '雷達動態'}) if not clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame())).empty and '軋空評估' in clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame())).columns else pd.DataFrame(),
            clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame()))[['統一代號', '套牢評估']].rename(columns={'套牢評估': '雷達動態'}) if not clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame())).empty and '套牢評估' in clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame())).columns else pd.DataFrame()
        ])
        if not b4_radar_combined.empty:
            b4_dynamics = b4_radar_combined.groupby('統一代號')['雷達動態'].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index()
            trend_mask_b4 = pd.Series(True, index=b4_dynamics.index) if is_and_logic_b4 else pd.Series(False, index=b4_dynamics.index)
            for trend in b4_trends:
                curr_cond = b4_dynamics['雷達動態'].str.contains(trend, regex=False, na=False)
                if is_and_logic_b4: trend_mask_b4 &= curr_cond
                else: trend_mask_b4 |= curr_cond
            filtered_df = filtered_df[filtered_df['統一代號'].isin(b4_dynamics[trend_mask_b4]['統一代號'].unique())]
    if b4_price_chg[0] > -10.0 or b4_price_chg[1] < 10.0:
        any_filter_applied = True
        combined_price_df = pd.concat([
            clean_stock_id(get_df('b4_margin_pct'))[['統一代號', '漲跌幅%']] if not clean_stock_id(get_df('b4_margin_pct')).empty and '漲跌幅%' in clean_stock_id(get_df('b4_margin_pct')).columns else pd.DataFrame(),
            clean_stock_id(get_df('b4_margin_inc_pct'))[['統一代號', '漲跌幅%']] if not clean_stock_id(get_df('b4_margin_inc_pct')).empty and '漲跌幅%' in clean_stock_id(get_df('b4_margin_inc_pct')).columns else pd.DataFrame()
        ]).drop_duplicates(subset=['統一代號'])
        if not combined_price_df.empty: filtered_df = filtered_df[filtered_df['統一代號'].isin(combined_price_df[(combined_price_df['漲跌幅%'] >= b4_price_chg[0]) & (combined_price_df['漲跌幅%'] <= b4_price_chg[1])]['統一代號'].unique())]
    acc_configs = [(b4_acc_margin_dec, 'b4_margin_vol', 'dec'), (b4_acc_sbl_dec, 'b4_short_vol', 'dec'), (b4_acc_margin_inc, 'b4_margin_inc_vol', 'inc'), (b4_acc_sbl_inc, 'b4_short_inc_vol', 'inc')]
    for is_checked, df_key, direction in acc_configs:
        if is_checked:
            any_filter_applied = True
            df_acc = clean_stock_id(get_df(df_key))
            if not df_acc.empty:
                col_today = next((c for c in df_acc.columns if '當日' in c and '張' in c), next((c for c in df_acc.columns if '當日' in c), None))
                col_5d = next((c for c in df_acc.columns if '5日' in c and '張' in c), next((c for c in df_acc.columns if '5日' in c), None))
                col_price = '成交' if '成交' in df_acc.columns else None
                if col_today and col_5d and col_price:
                    df_acc['num_today'] = pd.to_numeric(df_acc[col_today].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
                    df_acc['num_5d'] = pd.to_numeric(df_acc[col_5d].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
                    df_acc['price'] = pd.to_numeric(df_acc[col_price].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
                    col_pct = next((c for c in df_acc.columns if '漲跌幅' in c.replace(' ', '')), None)
                    df_acc['pct_chg'] = pd.to_numeric(df_acc[col_pct].astype(str).str.replace('%', '', regex=False), errors='coerce').fillna(0) if col_pct else 0
                    df_acc['amt_today'] = df_acc['num_today'] * df_acc['price'] * 1000
                    df_acc['amt_5d_avg'] = (df_acc['num_5d'] / 5.0) * df_acc['price'] * 1000
                    amt_threshold = 10000000 
                    if direction == 'inc':
                        if 'margin' in df_key: valid_acc_codes = df_acc[(df_acc['amt_today'] >= amt_threshold) & (df_acc['amt_today'] > df_acc['amt_5d_avg']) & (df_acc['pct_chg'] < 0)]['統一代號'].unique()
                        else: valid_acc_codes = df_acc[(df_acc['amt_today'] >= amt_threshold) & (df_acc['amt_today'] > df_acc['amt_5d_avg'])]['統一代號'].unique()
                    else: valid_acc_codes = df_acc[(df_acc['amt_today'] <= -amt_threshold) & (df_acc['amt_today'] < df_acc['amt_5d_avg'])]['統一代號'].unique()
                    filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_acc_codes)]

    # B5 過濾
    df_1k = clean_stock_id(get_df('b5_1000'))
    df_800 = clean_stock_id(get_df('b5_800'))
    df_600 = clean_stock_id(get_df('b5_600'))
    df_400 = clean_stock_id(get_df('b5_400'))
    if b5_long_short or b5_double:
        if not df_1k.empty and not df_400.empty:
            any_filter_applied = True
            latest_col_1k = next((c for c in df_1k.columns if c.startswith('▼') and '6周' not in c), None)
            latest_col_400 = next((c for c in df_400.columns if c.startswith('▼') and '6周' not in c), None)
            valid_resonance_codes = set()
            if b5_long_short and latest_col_1k and latest_col_400:
                cond_1k = (pd.to_numeric(df_1k['▼6周增減'], errors='coerce').fillna(0) > 0) & (pd.to_numeric(df_1k[latest_col_1k], errors='coerce').fillna(0) > 0)
                cond_400 = (pd.to_numeric(df_400['▼6周增減'], errors='coerce').fillna(0) > 0) & (pd.to_numeric(df_400[latest_col_400], errors='coerce').fillna(0) > 0)
                valid_resonance_codes.update(set(df_1k[cond_1k]['統一代號']).intersection(set(df_400[cond_400]['統一代號'])))
            if b5_double:
                set_1k_inc = set(df_1k[df_1k['週動態'].astype(str).str.contains('增', na=False)]['統一代號'])
                set_400_inc = set(df_400[df_400['週動態'].astype(str).str.contains('增', na=False)]['統一代號'])
                if b5_long_short: valid_resonance_codes.intersection_update(set_1k_inc.intersection(set_400_inc))
                else: valid_resonance_codes.update(set_1k_inc.intersection(set_400_inc))
            filtered_df = filtered_df[filtered_df['統一代號'].isin(list(valid_resonance_codes))]
    b5_6w_configs = [(b5_6w_1000, df_1k, "1000張"), (b5_6w_800, df_800, "800張"), (b5_6w_600, df_600, "600張"), (b5_6w_400, df_400, "400張")]
    for is_checked, df_lvl, lvl_name in b5_6w_configs:
        if is_checked:
            any_filter_applied = True
            if not df_lvl.empty and '▼6周增減' in df_lvl.columns: filtered_df = filtered_df[filtered_df['統一代號'].isin(df_lvl[pd.to_numeric(df_lvl['▼6周增減'], errors='coerce').fillna(0) > 0]['統一代號'].unique())]
    b5_trend_configs = [(b5_trend_1000, df_1k, "1000張"), (b5_trend_800, df_800, "800張"), (b5_trend_600, df_600, "600張"), (b5_trend_400, df_400, "400張")]
    for trends, df_lvl, lvl_name in b5_trend_configs:
        if trends:
            any_filter_applied = True
            if not df_lvl.empty and '週動態' in df_lvl.columns: filtered_df = filtered_df[filtered_df['統一代號'].isin(df_lvl[df_lvl['週動態'].isin(trends)]['統一代號'].unique())]

    # B6 過濾
    if b6_today_chk or b6_amt_min > 0 or b6_status_chk:
        df_b6 = clean_stock_id(get_df('b6_today'))
        if not df_b6.empty:
            any_filter_applied = True
            b6_mask = pd.Series(True, index=df_b6.index)
            if b6_amt_min > 0:
                df_b6['num_amt'] = pd.to_numeric(df_b6['總額(億)'], errors='coerce').fillna(0)
                b6_mask &= (df_b6['num_amt'] >= b6_amt_min)
            if b6_status_chk and dynamic_price_col_b6 in df_b6.columns:
                def check_b6_status(row):
                    try:
                        prices = [float(p) for p in str(row[dynamic_price_col_b6]).split(' / ')]
                        avg_p = sum(prices) / len(prices)
                        c_p = float(str(row['▼收盤價']).replace(',', ''))
                        return "🛡️ 防守成功 (收盤 >= 鉅額均價)" if c_p >= avg_p else "🚨 跌破防線 (收盤 < 鉅額均價)"
                    except: return "未知"
                df_b6['__status'] = df_b6.apply(check_b6_status, axis=1)
                b6_mask &= df_b6['__status'].isin(b6_status_chk)
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b6[b6_mask]['統一代號'].unique())]
            
    # B7 過濾
    b7_hold_min, b7_hold_max = b7_hold_pct
    b7_pledge_min, b7_pledge_max = b7_pledge_pct
    if b7_hold_min > 0 or b7_hold_max < 100.0 or b7_pledge_min > 0 or b7_pledge_max < 100.0:
        df_b7_pledge = clean_stock_id(get_df('b7_pledge'))
        if not df_b7_pledge.empty:
            any_filter_applied = True
            b7_mask = pd.Series(True, index=df_b7_pledge.index)
            if b7_hold_min > 0 or b7_hold_max < 100.0:
                df_b7_pledge['num_hold'] = pd.to_numeric(df_b7_pledge['全體 董監 持股 (%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
                b7_mask &= df_b7_pledge['num_hold'].between(b7_hold_min, b7_hold_max)
            if b7_pledge_min > 0 or b7_pledge_max < 100.0:
                df_b7_pledge['num_pledge'] = pd.to_numeric(df_b7_pledge['全體 董監 質押 (%)'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
                b7_mask &= df_b7_pledge['num_pledge'].between(b7_pledge_min, b7_pledge_max)
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b7_pledge[b7_mask]['統一代號'].unique())]
    if b7_hold_trend:
        df_b7_main = clean_stock_id(get_df('b7_main'))
        if not df_b7_main.empty and '動態' in df_b7_main.columns:
            any_filter_applied = True
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b7_main[df_b7_main['動態'].isin(b7_hold_trend)]['統一代號'].unique())]
    if b7_pledge_trend:
        df_b7_hist = clean_stock_id(get_df('b7_pledge_history'))
        if not df_b7_hist.empty and '動態' in df_b7_hist.columns:
            any_filter_applied = True
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b7_hist[df_b7_hist['動態'].isin(b7_pledge_trend)]['統一代號'].unique())]
    if b7_6m_inc:
        df_b7_main = clean_stock_id(get_df('b7_main'))
        if not df_b7_main.empty and '▼近半年增減%' in df_b7_main.columns:
            any_filter_applied = True
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b7_main[pd.to_numeric(df_b7_main['▼近半年增減%'], errors='coerce').fillna(0) > 0]['統一代號'].unique())]

    # ==========================================
    # 過濾結果結算與 除錯透視鏡 檢核
    # ==========================================
    if any_filter_applied:
        st.success(f"✅ 過濾完成！共有 **{len(filtered_df)}** 檔標的符合您的跨模組條件。")
        debug_mode = st.checkbox("🔬 開啟除錯透視鏡 (核對名單與過濾數值)")
        if debug_mode:
            df_b0_debug = clean_stock_id(get_df('b0_price')).drop_duplicates(subset=['統一代號'])
            debug_df = filtered_df.copy()
            if not df_b0_debug.empty:
                b0_cols = ['統一代號']
                rename_dict = {}
                # 🎯 這裡加入了 '股價日期' 以及您要的 '5日均額'
                for col in ['股價日期', '成交', '漲跌幅', '成交張數', '成交額(百萬)', 'PER', '5日均量', '5日均額', 'B0_量價狀態']:
                    if col in df_b0_debug.columns:
                        b0_cols.append(col)
                        # 🎯 針對 5日均額 給予您指定的專屬名稱
                        if col == '5日均額':
                            rename_dict[col] = 'B0_5日均成交額(百萬)'
                        else:
                            rename_dict[col] = f'B0_{col}' if not col.startswith('B0_') else col
                            
                debug_df = pd.merge(debug_df, df_b0_debug[b0_cols].rename(columns=rename_dict), on='統一代號', how='left')

            check_cols = ['統一代號', '今日上榜', '△', '法人持股', '最新動態', '5日ΔChange', '20日ΔChange', '60日ΔChange', '120日ΔChange']
            df_b1_debug = df_b1_raw[[c for c in check_cols if c in df_b1_raw.columns]].drop_duplicates(subset=['統一代號'])
            debug_df = pd.merge(debug_df, df_b1_debug, on='統一代號', how='left')
            
            b2_labels = zip(['b2_1', 'b2_2', 'b2_3', 'b2_4'], ['外資成交動態', '投信成交動態', '外資發行動態', '投信發行動態'])
            for b2_key, col_name in b2_labels:
                df_b2_tmp = clean_stock_id(get_df(b2_key)).drop_duplicates(subset=['統一代號'])
                if not df_b2_tmp.empty and '今日短動態' in df_b2_tmp.columns: debug_df = pd.merge(debug_df, df_b2_tmp[['統一代號', '今日短動態']].rename(columns={'今日短動態': f'B2_{col_name}'}), on='統一代號', how='left')

            df_b3_main = get_df('b3_main')
            if not df_b3_main.empty:
                df_b3_main = clean_stock_id(df_b3_main).drop_duplicates(subset=['統一代號', '連買類型']) 
                df_b3_main['B3_組合狀態'] = df_b3_main['連買類型'] + "(" + df_b3_main['連買週期數'].astype(str) + ")-" + df_b3_main['狀態動態']
                b3_summary = df_b3_main.groupby('統一代號')['B3_組合狀態'].apply(lambda x: " | ".join(x)).reset_index()
                debug_df = pd.merge(debug_df, b3_summary.rename(columns={'B3_組合狀態': 'B3_連買狀態'}), on='統一代號', how='left')

            sq_df_debug = clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame())).drop_duplicates(subset=['統一代號'])
            rk_df_debug = clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame())).drop_duplicates(subset=['統一代號'])
            if not sq_df_debug.empty: debug_df = pd.merge(debug_df, sq_df_debug[['統一代號', '軋空評估']], on='統一代號', how='left')
            if not rk_df_debug.empty: debug_df = pd.merge(debug_df, rk_df_debug[['統一代號', '套牢評估']], on='統一代號', how='left')
                
            b4_debug_keys = {'b4_margin_pct': '融資減幅', 'b4_margin_vol': '融資減張', 'b4_short_pct': '借券減幅', 'b4_short_vol': '借券減張', 'b4_margin_plus_pct': '融券增幅', 'b4_margin_plus_vol': '融券增張', 'b4_margin_inc_pct': '融資增幅', 'b4_short_inc_pct': '借券增幅', 'b4_margin_inc_vol': '融資增張', 'b4_short_inc_vol': '借券增張', 'b4_short_dec_amt': '借券實際減額', 'b4_short_inc_amt': '借券實際增額'}
            for k, label in b4_debug_keys.items():
                df_tmp = clean_stock_id(get_df(k)).drop_duplicates(subset=['統一代號'])
                if not df_tmp.empty:
                    col_today = next((c for c in df_tmp.columns if '當日' in c and ('%' in c or '張' in c)), next((c for c in df_tmp.columns if '當日' in c), None))
                    col_5d = next((c for c in df_tmp.columns if '5日' in c and ('%' in c or '張' in c)), next((c for c in df_tmp.columns if '5日' in c), None))
                    extract_cols = ['統一代號']
                    rename_dict = {}
                    if col_today:
                        extract_cols.append(col_today)
                        rename_dict[col_today] = f"B4_{label}_當日"
                    if col_5d:
                        extract_cols.append(col_5d)
                        rename_dict[col_5d] = f"B4_{label}_5日"
                    if '張' in label and '成交' in df_tmp.columns and col_today:
                        df_tmp['num_today_calc'] = pd.to_numeric(df_tmp[col_today].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
                        df_tmp['price_calc'] = pd.to_numeric(df_tmp['成交'].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0)
                        df_tmp[f"B4_{label}_當日估算(萬)"] = (df_tmp['num_today_calc'] * df_tmp['price_calc'] * 1000 / 10000).round(1)
                        extract_cols.append(f"B4_{label}_當日估算(萬)")
                    if len(extract_cols) > 1: debug_df = pd.merge(debug_df, df_tmp[extract_cols].rename(columns=rename_dict), on='統一代號', how='left')

            b5_debug_keys = {'b5_1000': 'B5_1000張', 'b5_800': 'B5_800張', 'b5_600': 'B5_600張', 'b5_400': 'B5_400張'}
            for df_key, label in b5_debug_keys.items():
                df_b5_tmp = clean_stock_id(get_df(df_key)).drop_duplicates(subset=['統一代號'])
                if not df_b5_tmp.empty:
                    latest_col = next((c for c in df_b5_tmp.columns if c.startswith('▼') and '6周' not in c), None)
                    extract_cols = ['統一代號']
                    rename_dict = {}
                    if '週動態' in df_b5_tmp.columns:
                        extract_cols.append('週動態')
                        rename_dict['週動態'] = f"{label}_週動態"
                    if latest_col:
                        extract_cols.append(latest_col)
                        rename_dict[latest_col] = f"{label}_最新週"
                    if '▼6周增減' in df_b5_tmp.columns:
                        extract_cols.append('▼6周增減')
                        rename_dict['▼6周增減'] = f"{label}_6周"
                    if len(extract_cols) > 1: debug_df = pd.merge(debug_df, df_b5_tmp[extract_cols].rename(columns=rename_dict), on='統一代號', how='left')
            
            if 'B5_1000張_週動態' in debug_df.columns and 'B5_400張_週動態' in debug_df.columns:
                def check_resonance(row):
                    res = []
                    inc_1k = "增" in str(row.get('B5_1000張_週動態', ''))
                    inc_400 = "增" in str(row.get('B5_400張_週動態', ''))
                    if inc_1k and inc_400: res.append("雙引擎")
                    try:
                        v1k_wk = float(str(row.get('B5_1000張_最新週', '0')).replace('%','').replace('+',''))
                        v1k_6wk = float(str(row.get('B5_1000張_6周', '0')).replace('%','').replace('+',''))
                        v400_wk = float(str(row.get('B5_400張_最新週', '0')).replace('%','').replace('+',''))
                        v400_6wk = float(str(row.get('B5_400張_6周', '0')).replace('%','').replace('+',''))
                        if v1k_wk > 0 and v1k_6wk > 0 and v400_wk > 0 and v400_6wk > 0: res.append("長短線")
                    except: pass
                    return " | ".join(res) if res else ""
                debug_df['B5_共振狀態'] = debug_df.apply(check_resonance, axis=1)

            df_b6_debug = clean_stock_id(get_df('b6_today')).drop_duplicates(subset=['統一代號'])
            if not df_b6_debug.empty:
                b6_cols = ['統一代號', '總額(億)']
                dynamic_col = st.session_state.get('b6_dynamic_price_col')
                if dynamic_col and dynamic_col in df_b6_debug.columns and '▼收盤價' in df_b6_debug.columns:
                    def get_debug_b6_status(row):
                        try:
                            prices = [float(p) for p in str(row[dynamic_col]).split(' / ')]
                            avg_p = sum(prices) / len(prices)
                            c_p = float(str(row['▼收盤價']).replace(',', ''))
                            return "🛡️ 防守成功" if c_p >= avg_p else "🚨 跌破防線"
                        except: return "未知"
                    df_b6_debug['B6_防守狀態'] = df_b6_debug.apply(get_debug_b6_status, axis=1)
                    b6_cols.extend([dynamic_col, '▼收盤價', 'B6_防守狀態'])
                elif dynamic_col and dynamic_col in df_b6_debug.columns: b6_cols.append(dynamic_col)
                elif '▼收盤價' in df_b6_debug.columns: b6_cols.append('▼收盤價')
                debug_df = pd.merge(debug_df, df_b6_debug[b6_cols].rename(columns={'總額(億)': 'B6_總額(億)', dynamic_col: 'B6_成交均價' if dynamic_col else 'B6_成交均價', '▼收盤價': 'B6_收盤價'}), on='統一代號', how='left')

            df_b7_pledge = clean_stock_id(get_df('b7_pledge')).drop_duplicates(subset=['統一代號'])
            if not df_b7_pledge.empty:
                cols = ['統一代號']
                rename_dict = {}
                if '全體 董監 持股 (%)' in df_b7_pledge.columns:
                    cols.append('全體 董監 持股 (%)')
                    rename_dict['全體 董監 持股 (%)'] = 'B7_董監持股%'
                if '全體 董監 質押 (%)' in df_b7_pledge.columns:
                    cols.append('全體 董監 質押 (%)')
                    rename_dict['全體 董監 質押 (%)'] = 'B7_董監質押%'
                debug_df = pd.merge(debug_df, df_b7_pledge[cols].rename(columns=rename_dict), on='統一代號', how='left')

            df_b7_main = clean_stock_id(get_df('b7_main')).drop_duplicates(subset=['統一代號'])
            if not df_b7_main.empty and '動態' in df_b7_main.columns:
                b7_main_cols = ['統一代號', '近月增減%', '動態']
                b7_main_rename = {'近月增減%': 'B7_持股近月增減%', '動態': 'B7_持股動態'}
                if '▼近半年增減%' in df_b7_main.columns:
                    b7_main_cols.append('▼近半年增減%')
                    b7_main_rename['▼近半年增減%'] = 'B7_持股近半年增減%'
                debug_df = pd.merge(debug_df, df_b7_main[b7_main_cols].rename(columns=b7_main_rename), on='統一代號', how='left')
            df_b7_hist = clean_stock_id(get_df('b7_pledge_history')).drop_duplicates(subset=['統一代號'])
            if not df_b7_hist.empty and '動態' in df_b7_hist.columns: debug_df = pd.merge(debug_df, df_b7_hist[['統一代號', '近月質押增減(%)', '動態']].rename(columns={'近月質押增減(%)': 'B7_質押近月增減%', '動態': 'B7_質押動態'}), on='統一代號', how='left')
            
            st.write(f"🔍 檢核明細 (共 {len(debug_df)} 筆)：")
            st.dataframe(debug_df, use_container_width=True, hide_index=True)
            st.session_state['debug_df'] = debug_df 
    else:
        st.info("👆 請在上方展開模組中至少設定一項條件，目前預設顯示全市場標的。")

    st.write("---")

    # ==========================================
    # 2. 第二關：自訂權重計分面板 (擴充版)
    # ==========================================
    st.markdown("#### 2️⃣ 設定計分權重 (Weights)")
    st.caption("為各項籌碼動向設定加權分數 (設定為 0 代表不計分，負數代表扣分)")
    
    with st.expander("⚙️ 展開設定各區塊權重", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**法人持股動向**")
            w_b1_up = st.number_input("法人正向進榜 (次)", value=1.0, step=0.5)
            w_b1_down = st.number_input("法人衰退進榜 (次)", value=-1.0, step=0.5)
            w_b2 = st.number_input("法人單日突擊掃貨", value=1.5, step=0.5)
            w_b3 = st.number_input("法人連續買超", value=2.0, step=0.5)
        with c2:
            st.markdown("**資券籌碼變化**")
            w_b4_good = st.number_input("融資減/融券增", value=1.0, step=0.5)
            w_b4_short_dec = st.number_input("借券賣出減少", value=1.5, step=0.5) 
            w_b4_short_inc = st.number_input("借券賣出增加", value=-1.5, step=0.5) 
            w_b4_price_up = st.number_input("今日大漲(>3%)", value=0.0, step=0.5) 
        with c3:
            st.markdown("**大戶波段防線**")
            w_b5 = st.number_input("千張大戶持股增加", value=3.0, step=0.5)
            w_b5_800 = st.number_input("800張大戶持股增加", value=2.0, step=0.5) 
            w_b5_600 = st.number_input("600張大戶持股增加", value=1.5, step=0.5) 
            w_b5_400 = st.number_input("400張大戶持股增加", value=1.0, step=0.5) 
        with c4:
            st.markdown("**特定資金與董監防線**")
            w_b6 = st.number_input("鉅額防守成功", value=1.5, step=0.5)
            w_b7 = st.number_input("董監增持/質押降", value=1.5, step=0.5)

    # ==========================================
    # 3. 執行計分運算 (Scoring Engine) - 修正互動按鈕狀態流失
    # ==========================================
    if st.button("🚀 開始計算籌碼火力分數", type="primary", use_container_width=True):
        with st.spinner("🧠 籌碼大數據融合計算中..."):
            score_df = filtered_df.copy()
            score_df['總分'] = 0.0
            score_df['得分明細'] = ""

            def apply_score(target_df_key, weight, rule_name):
                df = clean_stock_id(get_df(target_df_key))
                if df.empty or weight == 0: return
                hit_codes = df['統一代號'].unique()
                mask = score_df['統一代號'].isin(hit_codes)
                score_df.loc[mask, '總分'] += weight
                sign = "+" if weight > 0 else ""
                score_df.loc[mask, '得分明細'] += f"[{rule_name} {sign}{weight}] "

            if not df_b1_raw.empty and w_b1_up != 0 and '上榜數量' in df_b1_raw.columns:
                for _, row in df_b1_raw.iterrows():
                    cnt = int(row['上榜數量']) if pd.notna(row['上榜數量']) else 0
                    if cnt > 0:
                        mask = score_df['統一代號'] == row['統一代號']
                        score_df.loc[mask, '總分'] += (w_b1_up * cnt)
                        score_df.loc[mask, '得分明細'] += f"[法人正向{cnt}次 +{w_b1_up * cnt}] "

            apply_score('b1_down_final_df', w_b1_down, "法人衰退")
            for k in ['b2_1', 'b2_2', 'b2_3', 'b2_4']: apply_score(k, w_b2, "法人掃貨")
            apply_score('b3_main', w_b3, "法人連買")
            for k in ['b4_margin_pct', 'b4_margin_plus_pct', 'b4_margin_vol', 'b4_margin_plus_vol']:
                apply_score(k, w_b4_good, "資券有利")
                
            for k in ['b4_short_pct', 'b4_short_vol', 'b4_short_dec_amt']: apply_score(k, w_b4_short_dec, "借券減少")
            for k in ['b4_short_inc_pct', 'b4_short_inc_vol', 'b4_short_inc_amt']: apply_score(k, w_b4_short_inc, "借券增加")
            
            if w_b4_price_up != 0:
                df_b0_price = get_df('b0_price')
                if not df_b0_price.empty and '漲跌幅' in df_b0_price.columns:
                    df_b0_price['num_pct'] = pd.to_numeric(df_b0_price['漲跌幅'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
                    valid_up_codes = df_b0_price[df_b0_price['num_pct'] > 3.0]['統一代號'].unique()
                    mask = score_df['統一代號'].isin(valid_up_codes)
                    score_df.loc[mask, '總分'] += w_b4_price_up
                    sign = "+" if w_b4_price_up > 0 else ""
                    score_df.loc[mask, '得分明細'] += f"[大漲>3% {sign}{w_b4_price_up}] "

            apply_score('b5_1000', w_b5, "千張大戶")
            apply_score('b5_800', w_b5_800, "800張大戶")
            apply_score('b5_600', w_b5_600, "600張大戶")
            apply_score('b5_400', w_b5_400, "400張大戶")
            
            if w_b6 != 0:
                df_b6 = clean_stock_id(get_df('b6_today'))
                dynamic_col = st.session_state.get('b6_dynamic_price_col')
                if not df_b6.empty and dynamic_col in df_b6.columns:
                    def check_success(row):
                        try:
                            prices = [float(p) for p in str(row[dynamic_col]).split(' / ')]
                            avg_p = sum(prices) / len(prices)
                            c_p = float(str(row['▼收盤價']).replace(',', ''))
                            return c_p >= avg_p
                        except: return False
                    df_b6['is_success'] = df_b6.apply(check_success, axis=1)
                    hit_codes = df_b6[df_b6['is_success']]['統一代號'].unique()
                    mask = score_df['統一代號'].isin(hit_codes)
                    score_df.loc[mask, '總分'] += w_b6
                    sign = "+" if w_b6 > 0 else ""
                    score_df.loc[mask, '得分明細'] += f"[鉅額防守 {sign}{w_b6}] "

            if w_b7 != 0:
                df_b7_main = clean_stock_id(get_df('b7_main'))
                if not df_b7_main.empty and '近月增減%' in df_b7_main.columns:
                    valid_inc_codes = df_b7_main[pd.to_numeric(df_b7_main['近月增減%'], errors='coerce') > 0]['統一代號'].unique()
                    mask = score_df['統一代號'].isin(valid_inc_codes)
                    score_df.loc[mask, '總分'] += w_b7
                    sign = "+" if w_b7 > 0 else ""
                    score_df.loc[mask, '得分明細'] += f"[董監增持 {sign}{w_b7}] "

                df_b7_hist = clean_stock_id(get_df('b7_pledge_history'))
                if not df_b7_hist.empty and '近月質押增減(%)' in df_b7_hist.columns:
                    valid_dec_codes = df_b7_hist[pd.to_numeric(df_b7_hist['近月質押增減(%)'], errors='coerce') < 0]['統一代號'].unique()
                    mask = score_df['統一代號'].isin(valid_dec_codes)
                    score_df.loc[mask, '總分'] += w_b7
                    sign = "+" if w_b7 > 0 else ""
                    score_df.loc[mask, '得分明細'] += f"[質押下降 {sign}{w_b7}] "

            # 將結果鎖定到 session_state，避免互動時表格消失
            score_df = score_df.sort_values(by='總分', ascending=False).reset_index(drop=True)
            st.session_state['scored_result'] = score_df[score_df['總分'] != 0].copy()
            st.session_state['score_calculated'] = True

    # ==========================================
    # 4. 結果展示 & 模擬交易模型驗證 (使用 session_state 保持狀態)
    # ==========================================
    if st.session_state.get('score_calculated', False) and 'scored_result' in st.session_state:
        result_df = st.session_state['scored_result']

        st.write("---")
        st.markdown(f"### 🏆 策略計分與模型驗證 (共 {len(result_df)} 檔獲取分數)")
        
        tab_result, tab_track = st.tabs(["📊 今日策略計分結果", "🎯 歷史模型驗證追蹤 (模擬交易)"])

        with tab_result:
            if not result_df.empty:
                display_df = result_df[['統一代號', '股票名稱', '產業別', '總分', '得分明細']].rename(columns={'統一代號': '股票代號'})
                display_df.insert(0, '寫入追蹤 (本週上限5檔)', False)
                
                st.caption("💡 勾選下方『寫入追蹤』，即可將該檔標的與目前的策略過濾特徵，存入歷史模型庫中觀察。")
                
                # 互動表格
                edited_df = st.data_editor(
                    display_df,
                    column_config={
                        "寫入追蹤 (本週上限5檔)": st.column_config.CheckboxColumn(
                            "寫入追蹤",
                            help="勾選欲寫入追蹤系統的標的",
                            default=False,
                        ),
                        "總分": st.column_config.NumberColumn(
                            "總分",
                            help="策略加權總分",
                            format="%.1f",
                        )
                    },
                    disabled=["股票代號", "股票名稱", "產業別", "總分", "得分明細"],
                    hide_index=True,
                    use_container_width=True,
                    key="editor_save_track"
                )
                
                selected_rows = edited_df[edited_df['寫入追蹤 (本週上限5檔)'] == True]
                
                st.write("---")
                col_save1, col_save2 = st.columns([1, 1])
                with col_save1:
                    st.markdown(f"#### 💾 儲存今日策略模型 (已勾選 {len(selected_rows)} 檔)")
                
                with col_save2:
                    # 🎯 將判斷加在按鈕按下去的瞬間
                    if st.button("寫入模擬追蹤 (導覽登入)", icon=":material/database:", use_container_width=True, type="primary"):
                                    
                        # 1. 檢查登入狀態
                        if not st.session_state.get("logged_in", False):
                            st.error("⚠️ 守衛：「寫入追蹤清單需要綁定帳號！正在為您導向登入頁面...」")
                            import time
                            time.sleep(1.5) # 稍微停頓讓使用者看到提示
                            st.query_params["page"] = "login"
                            st.rerun()
                        else:
                        # 2. 已登入才執行原本的寫入邏輯
                            username = st.session_state.get("username", "guest")
                            with st.spinner("寫入中..."):

                                try:
                                    from streamlit_gsheets import GSheetsConnection
                                    conn = st.connection("gsheets", type=GSheetsConnection)
                                    # 🎯 直接綁定您的專屬 Google Sheets 網址
                                    SHEET_URL = "https://docs.google.com/spreadsheets/d/1TxHDahg8ul6lmUtDN-7X75cBXbkU0jaZ3M9zg6exBgU/edit?gid=687268023#gid=687268023"                                 

                                    track_date = datetime.datetime.now().strftime("%Y-%m-%d")
                                    today_obj = datetime.datetime.now()
                                    monday_obj = today_obj - datetime.timedelta(days=today_obj.weekday())
                                    monday_str = monday_obj.strftime("%Y-%m-%d")
                                    
                                    try: 
                                        old_track = conn.read(spreadsheet=SHEET_URL, worksheet="實驗室模型追蹤", ttl=0).dropna(how="all")
                                    except: 
                                        old_track = pd.DataFrame(columns=['鎖定日期', '代號', '名稱', '鎖定收盤價', '總分', '得分明細', '當下策略特徵', '追蹤狀態'])
                                    
                                    this_week_count = 0
                                    if not old_track.empty and '鎖定日期' in old_track.columns:
                                        old_track['date_obj'] = pd.to_datetime(old_track['鎖定日期'], errors='coerce')
                                        this_week_data = old_track[old_track['date_obj'] >= pd.to_datetime(monday_str)]
                                        this_week_count = len(this_week_data)
                                        old_track = old_track.drop(columns=['date_obj'])
                                        
                                    if this_week_count + len(selected_rows) > 5:
                                        st.error(f"❌ 寫入失敗：每週最多只能存取 5 檔標的。您本週已存取 {this_week_count} 檔，本次勾選 {len(selected_rows)} 檔，已達上限。")
                                    else:
                                        save_targets = selected_rows.copy()
                                        save_targets['鎖定日期'] = track_date
                                        
                                        df_b0_price = get_df('b0_price')
                                        price_dict = {}
                                        if not df_b0_price.empty and '成交' in df_b0_price.columns:
                                            for _, row in df_b0_price.iterrows():
                                                try: price_dict[str(row['統一代號'])] = float(str(row['成交']).replace(',', ''))
                                                except: pass
                                        
                                        save_targets['鎖定收盤價'] = save_targets['股票代號'].map(price_dict).fillna(0.0)
                                        save_targets['追蹤狀態'] = "追蹤中"
                                        
                                        debug_df_global = st.session_state.get('debug_df', pd.DataFrame())
                                        save_targets['當下策略特徵'] = ""
                                        
                                        if not debug_df_global.empty:
                                            debug_cols_to_keep = [c for c in debug_df_global.columns if c not in ['統一代號', '股票名稱', '產業別', '總分', '得分明細']]
                                            for idx, row in save_targets.iterrows():
                                                matched = debug_df_global[debug_df_global['統一代號'] == row['股票代號']]
                                                if not matched.empty:
                                                    features = []
                                                    for col in debug_cols_to_keep:
                                                        val = str(matched[col].iloc[0])
                                                        if val != 'nan' and val != 'None' and val != '':
                                                            features.append(f"{col}:{val}")
                                                    save_targets.at[idx, '當下策略特徵'] = " | ".join(features)[:1000]
                                        else:
                                            save_targets['當下策略特徵'] = "無詳細特徵紀錄 (未開啟除錯透視鏡)"
                                        
                                        final_save_df = save_targets[['鎖定日期', '股票代號', '股票名稱', '鎖定收盤價', '總分', '得分明細', '當下策略特徵', '追蹤狀態']].rename(columns={'股票代號': '代號', '股票名稱': '名稱'})
                                        
                                        if not old_track.empty and '鎖定日期' in old_track.columns and '代號' in old_track.columns:
                                            for _, row in final_save_df.iterrows():
                                                mask = (old_track['鎖定日期'] == row['鎖定日期']) & (old_track['代號'] == row['代號'])
                                                old_track = old_track[~mask]
                                                
                                        new_track = pd.concat([old_track, final_save_df], ignore_index=True)
                                        conn.update(spreadsheet=SHEET_URL, worksheet="實驗室模型追蹤", data=new_track)
                                        
                                        if 'pending_watchlist_adds' not in st.session_state:
                                            st.session_state['pending_watchlist_adds'] = []
                                        for _, row in final_save_df.iterrows():
                                            item = f"{row['代號']} {row['名稱']}"
                                            if item not in st.session_state['pending_watchlist_adds']:
                                                st.session_state['pending_watchlist_adds'].append(item)
                                                
                                        st.success(f"✅ 成功將 {len(selected_rows)} 檔標的寫入模型驗證庫！(本週已使用 {this_week_count + len(selected_rows)}/5 扣打)")
                                        st.info("💡 已自動為您標記，之後若開啟 Watchlist (自選股) 頁面，可直接無縫加入。")
                                        
                                except Exception as e:
                                    st.error(f"❌ 寫入失敗：{e}。請確認 Google Sheets 已建立名為「實驗室模型追蹤」的工作表。")

            else:
                st.warning("名單中沒有標的符合您的嚴格過濾條件，或得分為 0。")

        # ----------------------------------------------------
        # 歷史模型驗證區塊 (Tab 2)
        # ----------------------------------------------------
        with tab_track:
            st.markdown("### 📈 策略勝率回測雷達")
            st.caption("驗證您所設定的條件與權重，在過去 1~2 個月內的實際表現，藉此優化策略。")
            try:
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                # 🎯 直接綁定您的專屬 Google Sheets 網址
                SHEET_URL = "https://docs.google.com/spreadsheets/d/1TxHDahg8ul6lmUtDN-7X75cBXbkU0jaZ3M9zg6exBgU/edit?gid=687268023#gid=687268023"
                
                history_track_df = conn.read(spreadsheet=SHEET_URL, worksheet="實驗室模型追蹤", ttl=0).dropna(how="all")
                
                if not history_track_df.empty:
                    today_obj = datetime.datetime.now()
                    monday_obj = today_obj - datetime.timedelta(days=today_obj.weekday())
                    monday_str = monday_obj.strftime("%Y-%m-%d")
                    history_track_df['date_obj'] = pd.to_datetime(history_track_df['鎖定日期'], errors='coerce')
                    this_week_data = history_track_df[history_track_df['date_obj'] >= pd.to_datetime(monday_str)]
                    
                    st.info(f"📊 **本週追蹤額度狀態：已使用 {len(this_week_data)} / 5 檔**")
                    
                    selected_week = st.selectbox("📅 選擇要回顧的策略發動日", sorted(history_track_df['鎖定日期'].astype(str).unique(), reverse=True), key="sel_track_date")
                    week_df = history_track_df[history_track_df['鎖定日期'] == selected_week].copy()
                    
                    lock_date_obj = datetime.datetime.strptime(selected_week, "%Y-%m-%d")
                    days_passed = (datetime.datetime.now() - lock_date_obj).days
                    
                    is_expired = days_passed >= 60 
                    
                    if is_expired:
                        status_tag = "🔴 已結案 (追蹤期滿 2 個月)"
                        st.info("🔒 此策略模型已追蹤滿 2 個月。")
                    else:
                        weeks_passed = (days_passed // 7) + 1
                        status_tag = f"🟢 追蹤中 (第 {weeks_passed} 週)"
                    
                    st.markdown(f"**目前狀態：** `{status_tag}` ｜ **距今發動天數：** `{days_passed} 天`")
                    
                    df_b0_today = get_df('b0_price')
                    latest_prices = {}
                    if not df_b0_today.empty and '成交' in df_b0_today.columns:
                        for _, row in df_b0_today.iterrows():
                            try: latest_prices[str(row['統一代號'])] = float(str(row['成交']).replace(',', ''))
                            except: pass
                    
                    week_df['最新價格'] = week_df['代號'].astype(str).map(latest_prices).fillna(0.0)
                    
                    def calc_price_return(row):
                        try:
                            lock_p = float(row.get('鎖定收盤價', 0))
                            curr_p = float(row.get('最新價格', 0))
                            if lock_p > 0 and curr_p > 0:
                                pct = ((curr_p - lock_p) / lock_p) * 100
                                if pct > 0: return f"🚀 +{pct:.1f}%"
                                elif pct < 0: return f"🩸 {pct:.1f}%"
                                else: return "0.0%"
                            return "-"
                        except: return "-"
                    
                    week_df['區間報酬'] = week_df.apply(calc_price_return, axis=1)
                    
                    show_cols = ['代號', '名稱', '鎖定收盤價', '最新價格', '區間報酬', '總分', '得分明細', '當下策略特徵']
                    
                    st.dataframe(
                        week_df[[c for c in show_cols if c in week_df.columns]], 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "當下策略特徵": st.column_config.TextColumn(
                                "🔍 當下策略特徵 (滑過查看)", 
                                help="紀錄當時觸發的所有量價與籌碼狀態，供您回顧優化策略用。", 
                                width="medium", 
                                max_chars=30
                            ),
                            "得分明細": st.column_config.TextColumn(
                                "🏆 得分明細", 
                                width="medium"
                            )
                        }
                    )
                else:
                    st.info("⚪ 目前實驗室模型庫中尚無紀錄。請先在上方設定條件，勾選標的後點擊「寫入模擬追蹤系統」。")
            except Exception as e:
                st.warning("⚪ 尚無歷史追蹤紀錄，或 Google Sheets 尚未建立名為「實驗室模型追蹤」的工作表。")
