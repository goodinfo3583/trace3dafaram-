# views/weight_backtest_page.py
import streamlit as st
import pandas as pd
import re
import os
import glob

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
    'b5_400': ['b5_400', 'df_blk5'],
    'b5_1000': ['b5_1000', 'df_blk5_1000'],
    'b5_800': ['b5_800', 'df_blk5_800'],
    'b5_600': ['b5_600', 'df_blk5_600'],
    'b5_400': ['b5_400', 'df_blk5_400'],
    'b5_resonance': ['b5_resonance', 'df_b5_resonance', 'df_resonance', 'df_長短線共振'],
    'b5_double': ['b5_double', 'df_b5_double', 'df_double', 'df_雙向共振'],
    'b6_today': ['b6_today', 'b6_today_df'],      # <-- 新增這行 B6 鉅額今日
    'b6_hist': ['b6_hist', 'b6_hist_matrix'],     # <-- 新增這行 B6 鉅額歷史
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
# 🌟 B0 專屬背景喚醒：讀取每日成交價量
# ==========================================
def sync_b0_data(DATA_DIR):
    search_patterns = [os.path.join(DATA_DIR, "*成交價*.csv")]
    files = []
    for pattern in search_patterns:
        files.extend(glob.glob(pattern))
    if not files: return
    
    # 永遠只抓最新的一天
    latest_file = sorted(files, reverse=True)[0]
    df = None
    for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
        try:
            df = pd.read_csv(latest_file, encoding=enc, header=0)
            break
        except: pass
        
    if df is not None and not df.empty:
        # 去除所有欄位名稱中的空白 (例如將 '漲跌 幅' 變成 '漲跌幅')
        df.columns = [str(c).replace(' ', '').replace('\u3000', '').replace('\ufeff', '').replace('\xa0', '') for c in df.columns]
        c_code = next((c for c in df.columns if '代號' in c), None)
        if c_code:
            df['統一代號'] = df[c_code].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        st.session_state['b0_price'] = df
#        
def show_weight_backtest_page(STOCK_DICT, DATA_DIR="data"):
    # 🌟 自動喚醒 B0 價量資料
    if 'b0_price' not in st.session_state: sync_b0_data(DATA_DIR)
    # 背景自動載入原始資料
    ensure_b1_to_b5_loaded(DATA_DIR)
    
    # 🌟 自動喚醒 B6 鉅額資料
    if 'b6_today_df' not in st.session_state:
        sync_b6_data(DATA_DIR)

    # 🌟 自動喚醒 B7 董監資料
    if 'b7_main' not in st.session_state: sync_b7_data(DATA_DIR)
    if 'b7_pledge' not in st.session_state: sync_pledge_data(DATA_DIR)
    if 'b7_pledge_history' not in st.session_state: sync_pledge_history_data(DATA_DIR)

    st.markdown("<h2 style='color: #38BDF8;'>⚖️ 策略實驗室：自訂權重與勝率回測</h2>", unsafe_allow_html=True)
    st.caption("打造專屬於您的選股邏輯，透過多重條件交集與大數據計分，找出最具爆發力的潛力股。")
    st.write("---")

    # ==========================================
    # 0. 建立完美全市場候選池
    # ==========================================
    pool_dict = {}
    if STOCK_DICT:
        for v in STOCK_DICT.values():
            sid = str(v.get("id", "")).strip()
            if sid: pool_dict[sid] = {"統一代號": sid, "股票名稱": v.get("name", ""), "產業別": v.get("industry", "未分類")}
                
    # 補上 B1 的遺漏標的 (常見 ETF)
    df_b1_raw = clean_stock_id(get_df('b1_final_df'))
    if not df_b1_raw.empty:
        for _, row in df_b1_raw.iterrows():
            sid = str(row['統一代號']).strip()
            if sid and sid not in pool_dict:
                pool_dict[sid] = {"統一代號": sid, "股票名稱": str(row.get('股票名稱', '')), "產業別": "ETF/基金/其他"}
                
    # 補上 B2 的遺漏標的 (特定債券、DR 等)
    for b2_key in ['b2_1', 'b2_2', 'b2_3', 'b2_4']:
        df_b2_tmp = clean_stock_id(get_df(b2_key))
        if not df_b2_tmp.empty:
            for _, row in df_b2_tmp.iterrows():
                sid = str(row['統一代號']).strip()
                if sid and sid not in pool_dict:
                    pool_dict[sid] = {"統一代號": sid, "股票名稱": str(row.get('股票名稱', '')), "產業別": "ETF/基金/其他"}

    # 補上 B4 的遺漏標的 (特定新發行 ETF 或純資券標的)
    for b4_key in ['b4_margin_pct', 'b4_short_pct', 'b4_margin_plus_pct', 'b4_margin_inc_pct', 'b4_short_inc_pct']:
        df_b4_tmp = clean_stock_id(get_df(b4_key))
        if not df_b4_tmp.empty:
            for _, row in df_b4_tmp.iterrows():
                sid = str(row['統一代號']).strip()
                if sid and sid not in pool_dict:
                    pool_dict[sid] = {"統一代號": sid, "股票名稱": str(row.get('股票名稱', '')), "產業別": "ETF/基金/其他"}

    base_df = pd.DataFrame(list(pool_dict.values()))
    if base_df.empty:
        st.warning("⚠️ 無法建立候選池，請確認資料庫狀態。")
        return

    # ==========================================
    # 1. 第一關：過濾器面版 (支援跨模組展開與交集)
    # ==========================================
    col_title, col_reset = st.columns([3, 1])
    with col_title:
        st.markdown(f"#### 1️⃣ 設定嚴格過濾條件 (目前全市場總候選池共 {len(base_df)} 檔)")
        st.caption("💡 跨模組複選為「交集 (嚴格篩選)」。動態特徵內的多選可切換交集或聯集。")
    with col_reset:
        def reset_filters():           
            # 強制將所有篩選器設回預設值 (最安全穩定的清空法)
            # 清空 B0 篩選器
            st.session_state['filter_b0_price'] = (0.0, 5000.0)
            st.session_state['filter_b0_vol'] = 0
            st.session_state['filter_b0_amt'] = 0.0
            st.session_state['filter_b0_pct'] = (-10.0, 10.0)
            st.session_state['filter_b0_per'] = 0.0
            st.session_state['filter_b0_exclude_loss'] = False
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
            
            # 清空 B3 篩選器
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
            
            # 清空 B4 篩選器
            st.session_state['filter_b4_top_n'] = 50
            for k in ['pct_41', 'vol_41', 'pct_42', 'vol_42', 'pct_43', 'vol_43', 'pct_inc_margin', 'pct_inc_short', 'amt_short_dec', 'amt_short_inc']:
                st.session_state[f'filter_b4_{k}'] = False
                
            # --- 新增的 B4 滑桿與加速特徵清空 ---
            st.session_state['filter_b4_price_chg'] = (-10.0, 10.0)
            for k in ['acc_margin_dec', 'acc_sbl_dec', 'acc_margin_inc', 'acc_sbl_inc']:
                st.session_state[f'filter_b4_{k}'] = False
            # -----------------------------------

            st.session_state['filter_b4_radio'] = "交集 (必須同時符合勾選特徵)"
            st.session_state['filter_b4_multi'] = []

            # 清空 B5 篩選器
            for k in ['long_short', 'double', '6w_1000', '6w_800', '6w_600', '6w_400']:
                st.session_state[f'filter_b5_{k}'] = False
            for k in ['1000', '800', '600', '400']:
                st.session_state[f'filter_b5_trend_{k}'] = []
                
            # 清空 B6 篩選器
            st.session_state['filter_b6_today'] = False
            st.session_state['filter_b6_amt_min'] = 0.0
            st.session_state['filter_b6_status'] = []

            # 清空 B7 篩選器
            st.session_state['filter_b7_hold_pct'] = (0.0, 100.0)
            st.session_state['filter_b7_pledge_pct'] = (0.0, 100.0)
            st.session_state['filter_b7_hold_trend'] = []
            st.session_state['filter_b7_pledge_trend'] = []
            st.session_state['filter_b7_6m_inc'] = False

        st.button("🧹 清空所有篩選條件", on_click=reset_filters, use_container_width=True)
#
    filtered_df = base_df.copy()
    any_filter_applied = False

    # 取得 B0 最新資料日期
    b0_latest_date_str = "未知日期"
    df_b0 = get_df('b0_price')
    if not df_b0.empty and '股價日期' in df_b0.columns:
        date_raw = str(df_b0['股價日期'].iloc[0])
        b0_latest_date_str = f"2026/{date_raw}" if "/" in date_raw else date_raw

    # --- 模組 B0 展開面板 ---
    with st.expander(f"💰 B0 基礎價量與估值過濾 (資料基準日: {b0_latest_date_str})", expanded=True):
        st.markdown("**🔹 1. 流動性過濾 (剔除冷門股/殭屍股)**")
        c_b0_1, c_b0_2 = st.columns(2)
        b0_vol_min = c_b0_1.number_input("📈 當日成交張數大於 (張)：", min_value=0, value=0, step=500, key="filter_b0_vol")
        b0_amt_min = c_b0_2.number_input("💵 當日成交額大於 (百萬)：", min_value=0.0, value=0.0, step=50.0, key="filter_b0_amt")
        
        st.markdown("**🔹 2. 價格與當日強弱勢過濾**")
        c_b0_3, c_b0_4 = st.columns(2)
        b0_price_range = c_b0_3.slider("🎯 股價區間 (元)：", 0.0, 5000.0, (0.0, 5000.0), 10.0, key="filter_b0_price")
        b0_pct_range = c_b0_4.slider("🚀 當日漲跌幅區間 (%)：", -10.0, 10.0, (-10.0, 10.0), 0.5, key="filter_b0_pct")
        
        st.markdown("**🔹 3. 估值安全過濾**")
        c_b0_5, c_b0_6 = st.columns(2)
        b0_per_max = c_b0_5.number_input("⚖️ 本益比 (PER) 小於 (設定 0 為不限)：", min_value=0.0, value=0.0, step=5.0, key="filter_b0_per")
        st.write("") # 排版微調用
        b0_exclude_loss = c_b0_6.checkbox("🚫 排除虧損公司 (PER 為負或無資料)", key="filter_b0_exclude_loss")

    b1_sorted_dates = st.session_state.get('b1_sorted_dates', [])
    b1_latest_date_str = "未知日期"
    if b1_sorted_dates and len(str(b1_sorted_dates[0])) == 8:
        d_str = str(b1_sorted_dates[0])
        b1_latest_date_str = f"{d_str[:4]}/{d_str[4:6]}/{d_str[6:]}"
    
    # --- 模組 B1 展開面板 ---
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
            "拉動滑桿設定過濾範圍 (設定為 0~100 代表不作限制)：", 
            min_value=0.0, max_value=100.0, value=(0.0, 100.0), step=0.5, key="filter_b1_ratio"
        )

        st.markdown("**🔹 3. 區間累計持股增減 (ΔChange %)**")
        st.caption("設定特定區間內的持股增減幅度 (預設 -100~100 代表不限制，拉動至 0~100 即可尋找純增加的標的)")
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

    # 取得 B2 最新資料日期
    b2_latest_date_str = "未知日期"
    df_b2_1_tmp = get_df('b2_1')
    if not df_b2_1_tmp.empty:
        for c in df_b2_1_tmp.columns:
            if "成交比%" in c:
                raw_date = c.replace("成交比%", "")
                if len(raw_date) == 4:
                    b2_latest_date_str = f"2026/{raw_date[:2]}/{raw_date[2:]}"
                else:
                    b2_latest_date_str = raw_date
                break

    # --- 模組 B2 展開面板 ---
    with st.expander(f"🚀 B2 法人突擊掃貨 (資料基準日: {b2_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 掃貨榜單 (勾選多個代表必須「同時進榜」)**")
        b2_top_n = st.slider("👑 排名過濾：設定最新進榜的擷取範圍 (名次)", min_value=10, max_value=300, value=50, step=10, key="filter_b2_top_n")
        c_b2_1, c_b2_2 = st.columns(2)
        b2_1_chk = c_b2_1.checkbox(f"外資買超佔【5日成交量】(前 {b2_top_n} 名)", key="filter_b2_1")
        b2_2_chk = c_b2_2.checkbox(f"投信買超佔【5日成交量】(前 {b2_top_n} 名)", key="filter_b2_2")
        b2_3_chk = c_b2_1.checkbox(f"外資買超佔【5日發行數】(前 {b2_top_n} 名)", key="filter_b2_3")
        b2_4_chk = c_b2_2.checkbox(f"投信買超佔【5日發行數】(前 {b2_top_n} 名)", key="filter_b2_4")

        st.markdown("**🔹 2. 突擊動態特徵 (今日短動態)**")
        b2_trend_logic = st.radio("B2 特徵篩選邏輯：", ["交集 (必須同時符合勾選特徵)", "聯集 (符合任一即可)"], horizontal=True, key="filter_b2_radio")
        
        # 加上詳細定義說明的選項 (只顯示在前端，不影響背後字串比對)
        b2_trend_display_map = {
            "🔥 強延續": "🔥 強延續 (當日買盤加速 > 5日基準)",
            "🔥 持續加碼": "🔥 持續加碼 (當日買佔發行 > 0%)",
            "🆕 今日突擊卡位": "🆕 今日突擊卡位 (近5日未進榜，今日首度買超)",
            "⚠️ 趨緩": "⚠️ 趨緩 (當日續買，但力道 < 5日基準)",
            "🔄 持平": "🔄 持平 (當日成交比 = 0%)",
            "🔄 今日量縮持平": "🔄 今日量縮持平 (當日發行比 = 0%)",
            "📉 調節洗盤": "📉 調節洗盤 (當日微幅賣超調節)",
            "💤 籌碼沉澱中": "💤 籌碼沉澱中 (近5日未進榜且當日無買超)",
            "🚨 轉賣反轉": "🚨 轉賣反轉 (當日賣超 < 0%)",
            "🚨 劇烈倒貨": "🚨 劇烈倒貨 (當日強烈賣出)",
            "⚪ 觀望": "⚪ 觀望 (當日無資料)"
        }
        
        # 讓 UI 顯示完整的說明文字
        selected_display_trends = st.multiselect("可複選突擊動態：", list(b2_trend_display_map.values()), key="filter_b2_multi")
        
        # 將 UI 選擇的長字串，還原回原始的短字串供後台過濾使用
        b2_trends = [raw_trend for d_trend in selected_display_trends for raw_trend, desc in b2_trend_display_map.items() if d_trend == desc]
    
    # 取得 B3 最新資料日期 (取四個表的最新一天作為代表)
    b3_latest_date_str = "未知日期"
    df_b3_tmp = get_df('b3_main')
    if not df_b3_tmp.empty and 'b3_data' in st.session_state:
        # 從 b3_data tuple 中取日期
        dates = [d for _, d in st.session_state['b3_data'].values() if d and d != "00000000"]
        if dates:
            b3_latest_date_str = f"2026/{max(dates)[4:6]}/{max(dates)[6:]}"

    # --- 模組 B3 展開面板 ---
    with st.expander(f"🔥 B3 法人連續買超 (資料基準日: {b3_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 連買榜單 (勾選多個代表必須「同時進榜」)**")
        
        # 使用欄位來並排 Checkbox 和 Slider，節省空間
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
        # 還原短字串供過濾使用
        b3_trends = [t.split(" (")[0] for t in selected_b3_trends]

    # 取得 B4 最新資料日期 (取雷達日期作為代表)
    b4_latest_date_str = "未知日期"
    if 'b4_squeeze_radar' in st.session_state and st.session_state['b4_squeeze_radar']['date']:
        b4_latest_date_str = st.session_state['b4_squeeze_radar']['date']

    # --- 模組 B4 展開面板 ---
    with st.expander(f"⚔️ B4 資券動向與雷達 (資料基準日: {b4_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 資券榜單 (勾選多個代表必須「同時進榜」)**")
        b4_top_n = st.slider("👑 排名過濾：設定最新進榜的擷取範圍 (名次)", min_value=10, max_value=300, value=50, step=10, key="filter_b4_top_n")
        
        c_b4_1, c_b4_2 = st.columns(2)
        with c_b4_1:
            b4_41_pct = st.checkbox(f"融資減少幅度【5日累計比】(前 {b4_top_n} 名)", key="filter_b4_pct_41")
            b4_42_pct = st.checkbox(f"借券賣出減少幅度【5日累計比】(前 {b4_top_n} 名)", key="filter_b4_pct_42")
            b4_43_pct = st.checkbox(f"融券增加幅度【5日累計比】(前 {b4_top_n} 名)", key="filter_b4_pct_43")
            b4_inc_margin_pct = st.checkbox(f"融資增加幅度【5日累計比】(前 {b4_top_n} 名)", key="filter_b4_pct_inc_margin")
            b4_short_dec_amt = st.checkbox(f"借券賣出減少金額【5日累計】(前 {b4_top_n} 名)", key="filter_b4_amt_short_dec")
        with c_b4_2:
            b4_41_vol = st.checkbox(f"融資減少張數【5日累計張】(前 {b4_top_n} 名)", key="filter_b4_vol_41")
            b4_42_vol = st.checkbox(f"借券賣出減少張數【5日累計張】(前 {b4_top_n} 名)", key="filter_b4_vol_42")
            b4_43_vol = st.checkbox(f"融券增加張數【5日累計張】(前 {b4_top_n} 名)", key="filter_b4_vol_43")
            b4_inc_short_pct = st.checkbox(f"借券賣出增加幅度【5日累計比】(前 {b4_top_n} 名)", key="filter_b4_pct_inc_short")
            b4_short_inc_amt = st.checkbox(f"借券賣出增加金額【5日累計】(前 {b4_top_n} 名)", key="filter_b4_amt_short_inc")

        st.markdown("**🔹 2. 今日漲跌幅區間過濾 (%)**")
        b4_price_chg = st.slider("設定漲跌幅區間 (預設 -10~10 代表不限制，設定 2~10 代表只找大漲的標的)：", -10.0, 10.0, (-10.0, 10.0), 0.5, key="filter_b4_price_chg")

        st.markdown("**🔹 3. 籌碼加速特徵 (當日短線資金力道 > 5日均)**")
        st.caption("🚨 自動轉換為『金額』運算：當日資金變動必須超過 1,000 萬元，且當日資金動能大於 5日平均，徹底過濾低價股雜訊！")
        c_acc1, c_acc2 = st.columns(2)
        b4_acc_margin_dec = c_acc1.checkbox("⏩ 融資加速退場 (破千萬資金)", key="filter_b4_acc_margin_dec")
        b4_acc_sbl_dec = c_acc1.checkbox("⏩ 借券加速回補 (破千萬資金)", key="filter_b4_acc_sbl_dec")
        # UI 明確加上「+ 當日下跌」的條件標示
        b4_acc_margin_inc = c_acc2.checkbox("⚠️ 融資加速套牢 (破千萬資金 + 當日下跌)", key="filter_b4_acc_margin_inc")
        b4_acc_sbl_inc = c_acc2.checkbox("⚠️ 借券加速放空 (破千萬資金)", key="filter_b4_acc_sbl_inc")

        st.markdown("**🔹 4. 雷達動態特徵 (軋空與套牢訊號)**")
        b4_trend_logic = st.radio("B4 特徵篩選邏輯：", ["交集 (必須同時符合勾選特徵)", "聯集 (符合任一即可)"], horizontal=True, key="filter_b4_radio")
        
        b4_trend_display_map = {
            "💥 終極": "💥 終極 (法人買超+收紅+融資減.借券減.融券增 3項全中)",
            "🚀 強軋": "🚀 強軋 (法人買超+收紅+前述資券特徵 3中2)",
            "🔥 點火": "🔥 點火 (法人買超+收紅+前述資券特徵 3中1)",
            "🔼 進駐": "🔼 進駐 (僅法人買超+收紅，籌碼尚未發動軋空)",
            "☠️ 極危": "☠️ 極危 (法人賣超+收黑+融資增.借券增 2項全中)",
            "🚨 高危": "🚨 高危 (法人賣超+收黑+前述資券特徵 2中1)",
            "⚠️ 初危": "⚠️ 初危 (僅法人賣超+收黑，籌碼尚未發動套牢)"
        }
        
        selected_b4_trends_display = st.multiselect("可複選雷達特徵：", list(b4_trend_display_map.values()), key="filter_b4_multi")
        b4_trends = [raw for d in selected_b4_trends_display for raw, desc in b4_trend_display_map.items() if d == desc]
        ########################################################################################
    # 取得 B5 最新資料日期
    b5_latest_date_str = "未知日期"
    df_b5_tmp = get_df('b5_1000')
    if not df_b5_tmp.empty:
        col_latest = next((c for c in df_b5_tmp.columns if c.startswith('▼') and '6周' not in c), None)
        if col_latest:
            date_str = col_latest.replace('▼', '')
            b5_latest_date_str = f"2026/{date_str[:2]}/{date_str[2:]}"

    # --- 模組 B5 展開面板 ---
    with st.expander(f"🐳 B5 大腿動向 (資料基準日: {b5_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 共振榜單過濾**")
        c_b5_1, c_b5_2 = st.columns(2)
        b5_long_short = c_b5_1.checkbox("🎯 長短線共振 (1000張與400張波段+本週皆同步加碼)", key="filter_b5_long_short")
        b5_double = c_b5_2.checkbox("🎯 雙引擎共振 (1000張與400張本週同步增加)", key="filter_b5_double")

        st.markdown("**🔹 2. 波段吸籌過濾 (6周增減 > 0)**")
        st.caption("挑選近一個半月內，大戶籌碼持續呈現「淨流入」的波段保護傘標的。")
        c_b5_6w1, c_b5_6w2, c_b5_6w3, c_b5_6w4 = st.columns(4)
        b5_6w_1000 = c_b5_6w1.checkbox("👑 1000張 6周增加", key="filter_b5_6w_1000")
        b5_6w_800 = c_b5_6w2.checkbox("🦅 800張 6周增加", key="filter_b5_6w_800")
        b5_6w_600 = c_b5_6w3.checkbox("🦉 600張 6周增加", key="filter_b5_6w_600")
        b5_6w_400 = c_b5_6w4.checkbox("🐺 400張 6周增加", key="filter_b5_6w_400")

        st.markdown("**🔹 3. 各級距大戶週動態過濾**")
        st.caption("支援多選，可精準挑選籌碼『劇增』或『大增』的飆股防線。")
        
        trend_options_b5 = ["🚀 劇增", "🔥 大增", "📈 小增", "↗️ 微增", "🔄 持平", "↘️ 微減", "📉 小減", "⚠️ 大減", "🚨 劇減"]
        
        c_b5_lvl1, c_b5_lvl2 = st.columns(2)
        b5_trend_1000 = c_b5_lvl1.multiselect("👑 1000張大戶週動態：", trend_options_b5, key="filter_b5_trend_1000")
        b5_trend_800 = c_b5_lvl2.multiselect("🦅 800張大戶週動態：", trend_options_b5, key="filter_b5_trend_800")
        
        c_b5_lvl3, c_b5_lvl4 = st.columns(2)
        b5_trend_600 = c_b5_lvl3.multiselect("🦉 600張大戶週動態：", trend_options_b5, key="filter_b5_trend_600")
        b5_trend_400 = c_b5_lvl4.multiselect("🐺 400張大戶週動態：", trend_options_b5, key="filter_b5_trend_400")

        # 取得 B6 最新資料日期
    b6_latest_date_str = "未知日期"
    dynamic_price_col_b6 = st.session_state.get('b6_dynamic_price_col')
    if dynamic_price_col_b6 and "▼" in dynamic_price_col_b6:
        # 將 "▼0605 成交價" 轉為日期
        date_part = dynamic_price_col_b6.split(' ')[0].replace('▼', '')
        if len(date_part) == 4:
            b6_latest_date_str = f"2026/{date_part[:2]}/{date_part[2:]}"

    # --- 模組 B6 展開面板 ---
    with st.expander(f"💎 B6 鉅額交易動向 (資料基準日: {b6_latest_date_str})", expanded=False):
        st.markdown("**🔹 1. 今日鉅額交易過濾**")
        b6_today_chk = st.checkbox("🎯 今日有發生鉅額交易", key="filter_b6_today")
        
        st.markdown("**🔹 2. 資金規模過濾**")
        st.caption("過濾出具備絕對影響力的破億鉅額交易。")
        b6_amt_min = st.slider("💰 鉅額總額大於 (億)：", min_value=0.0, max_value=50.0, value=0.0, step=0.5, key="filter_b6_amt_min")
        
        st.markdown("**🔹 3. 防守狀態過濾**")
        b6_status_options = ["🛡️ 防守成功 (收盤 >= 鉅額均價)", "🚨 跌破防線 (收盤 < 鉅額均價)"]
        b6_status_chk = st.multiselect("可精準挑選主力防線狀態：", b6_status_options, key="filter_b6_status")

    # 取得 B7 最新資料月份 (自動解析 Goodinfo 的 26M07 格式或 202607 格式)
    b7_latest_date_str = "未知月份"
    df_b7_tmp = get_df('b7_main')
    
    if not df_b7_tmp.empty:
        # 尋找包含 "持股%" 的欄位，並萃取出前面的月份字串
        raw_months = [c.replace('持股%', '') for c in df_b7_tmp.columns if '持股%' in c]
        
        valid_months = []
        for m in raw_months:
            # 兼容 26M07 (Goodinfo格式) 或 202607 (傳統格式)
            if re.match(r'^\d{2}M\d{2}$', m) or re.match(r'^\d{4,6}$', m):
                valid_months.append(m)
                
        if valid_months:
            # 排序取最新
            best_m = sorted(valid_months, reverse=True)[0]
            
            if 'M' in best_m:
                # 處理 26M07 -> 2026/07
                y, m = best_m.split('M')
                b7_latest_date_str = f"20{y}/{m}"
            elif len(best_m) == 6:
                # 處理 202607 -> 2026/07
                b7_latest_date_str = f"{best_m[:4]}/{best_m[4:]}"

    # --- 模組 B7 展開面板 ---
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
        st.caption("挑選近半年內，大股東/董監事持續將籌碼收回口袋的波段保護傘標的。")
        
# ==========================================
    # 執行過濾邏輯
    # ==========================================
    # 處理 B0 基礎價量過濾引擎
    b0_price_min, b0_price_max = b0_price_range
    b0_pct_min, b0_pct_max = b0_pct_range
    
    if not df_b0.empty and (b0_vol_min > 0 or b0_amt_min > 0 or b0_price_min > 0 or b0_price_max < 5000.0 or b0_pct_min > -10.0 or b0_pct_max < 10.0 or b0_per_max > 0 or b0_exclude_loss):
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
            if b0_per_max > 0:
                b0_mask &= ((df_b0['num_per'] > 0) & (df_b0['num_per'] <= b0_per_max)) | (df_b0['num_per'].isna())
            if b0_exclude_loss:
                b0_mask &= (df_b0['num_per'] > 0)
        
        valid_b0_codes = df_b0[b0_mask]['統一代號'].unique()
        filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b0_codes)]
        
    if not df_b1_raw.empty:
        hit_mask = pd.Series(True, index=df_b1_raw.index)
        b1_checked = False

        # 1. 天數與 △ 檢查
        if b1_delta:
            b1_checked = True
            df_b1_raw['num_delta'] = pd.to_numeric(df_b1_raw['△'].astype(str).str.replace('%', '', regex=False).str.replace('+', '', regex=False), errors='coerce').fillna(0)
            hit_mask &= (df_b1_raw['num_delta'] > 0)
            
        if b1_5d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🔴5日')
        if b1_20d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🟡20日')
        if b1_60d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🟢60日')
        if b1_120d: b1_checked = True; hit_mask &= df_b1_raw['今日上榜'].astype(str).str.contains('🔵120日')

        # 2. 法人持股區間檢查
        if b1_ratio_min > 0.0 or b1_ratio_max < 100.0:
            b1_checked = True
            df_b1_raw['num_ratio'] = pd.to_numeric(df_b1_raw['法人持股'].astype(str).str.replace('%', '', regex=False).replace('未進榜', '0'), errors='coerce').fillna(0)
            hit_mask &= df_b1_raw['num_ratio'].between(b1_ratio_min, b1_ratio_max)

        # 3. 區間累計持股增減 (ΔChange) 檢查
        change_configs = {
            '5日ΔChange': b1_5d_chg, '20日ΔChange': b1_20d_chg,
            '60日ΔChange': b1_60d_chg, '120日ΔChange': b1_120d_chg
        }
        for col_name, (min_val, max_val) in change_configs.items():
            # 只要滑桿被拉動過，就啟動過濾機制
            if min_val > -100.0 or max_val < 100.0:
                b1_checked = True
                if col_name in df_b1_raw.columns:
                    # 容錯處理：拿掉 fillna(0.0)，讓無資料的股票保持 NaN，從而完美被 between 阻擋！
                    df_b1_raw[f'num_{col_name}'] = pd.to_numeric(
                        df_b1_raw[col_name].astype(str).str.replace('%', '', regex=False).str.replace('+', '', regex=False), 
                        errors='coerce'
                    )
                    hit_mask &= df_b1_raw[f'num_{col_name}'].between(min_val, max_val)

        # 4. 最新動態特徵檢查 (支援 交集 AND / 聯集 OR)
        if b1_trends:
            b1_checked = True
            is_and_logic = "交集" in b1_trend_logic
            
            # 若為交集(AND)，預設為 True (往下扣除)；若為聯集(OR)，預設為 False (往上疊加)
            trend_mask = pd.Series(True, index=df_b1_raw.index) if is_and_logic else pd.Series(False, index=df_b1_raw.index)
            
            for trend in b1_trends:
                # 處理 "衝進" 的雙重防呆比對
                if "衝進" in trend:
                    core_tag = trend.replace("🚀 衝進", "").replace("榜單", "")
                    current_cond = (
                        df_b1_raw['最新動態'].astype(str).str.contains("衝進", regex=False, na=False) & 
                        df_b1_raw['最新動態'].astype(str).str.contains(core_tag, regex=False, na=False)
                    )
                else:
                    # 一般特徵比對
                    current_cond = df_b1_raw['最新動態'].astype(str).str.contains(trend, regex=False, na=False)
                
                # 依照使用者選擇的邏輯進行合併
                if is_and_logic:
                    trend_mask &= current_cond
                else:
                    trend_mask |= current_cond
                    
            hit_mask &= trend_mask

        # 應用 B1 過濾結果
        if b1_checked:
            any_filter_applied = True
            hit_codes = df_b1_raw[hit_mask]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(hit_codes)]
            
    # 處理 B2 過濾
    b2_checks = {'b2_1': b2_1_chk, 'b2_2': b2_2_chk, 'b2_3': b2_3_chk, 'b2_4': b2_4_chk}
    for b2_key, is_checked in b2_checks.items():
        if is_checked:
            any_filter_applied = True
            df_b2_tmp = clean_stock_id(get_df(b2_key))
            if not df_b2_tmp.empty:
                # 找出最新一日的欄位 (通常是包含 % 的那欄)
                latest_col = next((c for c in df_b2_tmp.columns if '%' in c), None)
                if latest_col:
                    # 強制轉型，剔除數值為 0 或未進榜的標的
                    df_b2_tmp['num_latest'] = pd.to_numeric(df_b2_tmp[latest_col].astype(str).replace("未進榜", 0), errors='coerce').fillna(0)
                    df_b2_tmp = df_b2_tmp[df_b2_tmp['num_latest'] > 0]
                    # 因為 B2 原始資料已經依據 latest_col 遞減排序，直接 head(N) 即可精準取得前 N 名
                    df_b2_tmp = df_b2_tmp.head(b2_top_n)
                
                filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b2_tmp['統一代號'])]
            else:
                st.warning(f"⚠️ 找不到 {b2_key} 相關數據，過濾結果為空。")
                filtered_df = filtered_df.iloc[0:0]

    if b2_trends:
        any_filter_applied = True
        is_and_logic_b2 = "交集" in b2_trend_logic
        b2_dfs = [clean_stock_id(get_df(k)) for k in ['b2_1', 'b2_2', 'b2_3', 'b2_4']]
        b2_combined = pd.concat([df[['統一代號', '今日短動態']] for df in b2_dfs if not df.empty and '今日短動態' in df.columns])
        
        if not b2_combined.empty:
            # 彙整每檔股票跨 4 個表的所有 B2 動態
            b2_dynamics = b2_combined.groupby('統一代號')['今日短動態'].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index()
            trend_mask_b2 = pd.Series(True, index=b2_dynamics.index) if is_and_logic_b2 else pd.Series(False, index=b2_dynamics.index)
            
            for trend in b2_trends:
                curr_cond = b2_dynamics['今日短動態'].str.contains(trend, regex=False, na=False)
                if is_and_logic_b2: trend_mask_b2 &= curr_cond
                else: trend_mask_b2 |= curr_cond
            
            valid_b2_codes = b2_dynamics[trend_mask_b2]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b2_codes)]
        else:
            st.warning("⚠️ 找不到任何 B2 動態數據。")
            filtered_df = filtered_df.iloc[0:0]

    # 處理 B3 過濾
    df_b3_main = get_df('b3_main')
    if not df_b3_main.empty:
        b3_checks = {
            '🌐 外資日連買': (b3_fo_day_chk, b3_fo_day_n),
            '🏦 投信日連買': (b3_it_day_chk, b3_it_day_n),
            '🌐 外資週連買': (b3_fo_wk_chk, b3_fo_wk_n),
            '🏦 投信週連買': (b3_it_wk_chk, b3_it_wk_n)
        }
        
        for type_name, (is_checked, min_n) in b3_checks.items():
            if is_checked:
                any_filter_applied = True
                # 取出符合類型，且連買週期數 >= 設定值的標的
                df_b3_tmp = df_b3_main[(df_b3_main['連買類型'] == type_name) & (df_b3_main['連買週期數'] >= min_n)]
                
                if not df_b3_tmp.empty:
                    df_b3_tmp = clean_stock_id(df_b3_tmp)
                    filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b3_tmp['統一代號'])]
                else:
                    st.warning(f"⚠️ 找不到大於 {min_n} 的 {type_name} 數據，過濾結果為空。")
                    filtered_df = filtered_df.iloc[0:0]

        if b3_trends:
            any_filter_applied = True
            is_and_logic_b3 = "交集" in b3_trend_logic
            
            # 把每檔股票的所有 B3 狀態 (日/週) 組合起來
            b3_dynamics = df_b3_main.groupby('股票代號')['狀態動態'].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index()
            b3_dynamics = clean_stock_id(b3_dynamics)
            
            trend_mask_b3 = pd.Series(True, index=b3_dynamics.index) if is_and_logic_b3 else pd.Series(False, index=b3_dynamics.index)
            
            for trend in b3_trends:
                curr_cond = b3_dynamics['狀態動態'].str.contains(trend, regex=False, na=False)
                if is_and_logic_b3: trend_mask_b3 &= curr_cond
                else: trend_mask_b3 |= curr_cond
            
            valid_b3_codes = b3_dynamics[trend_mask_b3]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b3_codes)]

    # 處理 B4 過濾
    b4_checks = {
        'b4_margin_pct': b4_41_pct, 'b4_margin_vol': b4_41_vol,
        'b4_short_pct': b4_42_pct, 'b4_short_vol': b4_42_vol,
        'b4_margin_plus_pct': b4_43_pct, 'b4_margin_plus_vol': b4_43_vol,
        'b4_margin_inc_pct': b4_inc_margin_pct,
        'b4_short_inc_pct': b4_inc_short_pct,
        'b4_short_dec_amt': b4_short_dec_amt,  # 新增借券減額
        'b4_short_inc_amt': b4_short_inc_amt   # 新增借券增額
    }
    for b4_key, is_checked in b4_checks.items():
        if is_checked:
            any_filter_applied = True
            df_b4_tmp = clean_stock_id(get_df(b4_key))
            if not df_b4_tmp.empty:
                # 取得前 N 名 (B4原始資料已依據漲跌幅或特定條件排好序)
                df_b4_tmp = df_b4_tmp.head(b4_top_n)
                filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b4_tmp['統一代號'])]
            else:
                st.warning(f"⚠️ 找不到 {b4_key} 相關數據，過濾結果為空。")
                filtered_df = filtered_df.iloc[0:0]

    # 處理 B4 雷達特徵過濾
    if b4_trends:
        any_filter_applied = True
        is_and_logic_b4 = "交集" in b4_trend_logic
        
        sq_df = clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame()))
        rk_df = clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame()))
        
        b4_radar_combined = pd.DataFrame()
        if not sq_df.empty and '軋空評估' in sq_df.columns:
            b4_radar_combined = pd.concat([b4_radar_combined, sq_df[['統一代號', '軋空評估']].rename(columns={'軋空評估': '雷達動態'})])
        if not rk_df.empty and '套牢評估' in rk_df.columns:
            b4_radar_combined = pd.concat([b4_radar_combined, rk_df[['統一代號', '套牢評估']].rename(columns={'套牢評估': '雷達動態'})])

        if not b4_radar_combined.empty:
            b4_dynamics = b4_radar_combined.groupby('統一代號')['雷達動態'].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index()
            trend_mask_b4 = pd.Series(True, index=b4_dynamics.index) if is_and_logic_b4 else pd.Series(False, index=b4_dynamics.index)
            
            for trend in b4_trends:
                curr_cond = b4_dynamics['雷達動態'].str.contains(trend, regex=False, na=False)
                if is_and_logic_b4: trend_mask_b4 &= curr_cond
                else: trend_mask_b4 |= curr_cond
                
            valid_b4_codes = b4_dynamics[trend_mask_b4]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b4_codes)]
        else:
            st.warning("⚠️ 找不到任何 B4 雷達數據。")
            filtered_df = filtered_df.iloc[0:0]

    # 處理 B4 漲跌幅區間過濾 (從涵蓋面最廣的融資增減表中建立全局漲跌幅字典)
    if b4_price_chg[0] > -10.0 or b4_price_chg[1] < 10.0:
        any_filter_applied = True
        b4_price_ref1 = clean_stock_id(get_df('b4_margin_pct'))
        b4_price_ref2 = clean_stock_id(get_df('b4_margin_inc_pct'))
        
        combined_price_df = pd.concat([
            b4_price_ref1[['統一代號', '漲跌幅%']] if not b4_price_ref1.empty and '漲跌幅%' in b4_price_ref1.columns else pd.DataFrame(),
            b4_price_ref2[['統一代號', '漲跌幅%']] if not b4_price_ref2.empty and '漲跌幅%' in b4_price_ref2.columns else pd.DataFrame()
        ]).drop_duplicates(subset=['統一代號'])
        
        if not combined_price_df.empty:
            valid_price_codes = combined_price_df[(combined_price_df['漲跌幅%'] >= b4_price_chg[0]) & (combined_price_df['漲跌幅%'] <= b4_price_chg[1])]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_price_codes)]
    ############
    # 處理 B4 短線籌碼加速特徵過濾 (🔥 升級版：張數 × 股價 = 真實資金動能)
    acc_configs = [
        (b4_acc_margin_dec, 'b4_margin_vol', 'dec'), (b4_acc_sbl_dec, 'b4_short_vol', 'dec'),
        (b4_acc_margin_inc, 'b4_margin_inc_vol', 'inc'), (b4_acc_sbl_inc, 'b4_short_inc_vol', 'inc')
    ]
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
                    
                    # 💡 攔截漲跌幅 (自動相容各種包含空白的欄位名稱)
                    col_pct = next((c for c in df_acc.columns if '漲跌幅' in c.replace(' ', '')), None)
                    df_acc['pct_chg'] = pd.to_numeric(df_acc[col_pct].astype(str).str.replace('%', '', regex=False), errors='coerce').fillna(0) if col_pct else 0
                    
                    # 估算金額 = 張數 × 股價 × 1000
                    df_acc['amt_today'] = df_acc['num_today'] * df_acc['price'] * 1000
                    df_acc['amt_5d_avg'] = (df_acc['num_5d'] / 5.0) * df_acc['price'] * 1000
                    amt_threshold = 10000000 
                    
                    if direction == 'inc':
                        if 'margin' in df_key:
                            # 🚨【融資加速套牢】：必須是大跌/收黑 (pct_chg < 0) 才能叫套牢！
                            valid_acc_codes = df_acc[
                                (df_acc['amt_today'] >= amt_threshold) & 
                                (df_acc['amt_today'] > df_acc['amt_5d_avg']) &
                                (df_acc['pct_chg'] < 0)
                            ]['統一代號'].unique()
                        else:
                            # 【借券加速放空】：一般只要借券金額異常飆高即可
                            valid_acc_codes = df_acc[
                                (df_acc['amt_today'] >= amt_threshold) & 
                                (df_acc['amt_today'] > df_acc['amt_5d_avg'])
                            ]['統一代號'].unique()
                    else:
                        # 【加速退場/回補】：當日流出金額負更多
                        valid_acc_codes = df_acc[
                            (df_acc['amt_today'] <= -amt_threshold) & 
                            (df_acc['amt_today'] < df_acc['amt_5d_avg'])
                        ]['統一代號'].unique()
                        
                    filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_acc_codes)]
                else:
                    st.warning(f"⚠️ {df_key} 缺乏當日、5日或成交價欄位，無法計算資金動能。")
                    filtered_df = filtered_df.iloc[0:0]
                    ########################
    # 處理 B5 過濾引擎
    df_1k = clean_stock_id(get_df('b5_1000'))
    df_800 = clean_stock_id(get_df('b5_800'))
    df_600 = clean_stock_id(get_df('b5_600'))
    df_400 = clean_stock_id(get_df('b5_400'))

    # 1. 處理共振過濾
    if b5_long_short or b5_double:
        if df_1k.empty or df_400.empty:
            st.warning("⚠️ 缺乏 1000張 或 400張 資料，無法計算共振。")
            filtered_df = filtered_df.iloc[0:0]
        else:
            any_filter_applied = True
            latest_col_1k = next((c for c in df_1k.columns if c.startswith('▼') and '6周' not in c), None)
            latest_col_400 = next((c for c in df_400.columns if c.startswith('▼') and '6周' not in c), None)
            
            valid_resonance_codes = set()
            
            if b5_long_short and latest_col_1k and latest_col_400:
                # 長短線共振：1k與400的 6周與本週 皆需 > 0
                cond_1k = (pd.to_numeric(df_1k['▼6周增減'], errors='coerce').fillna(0) > 0) & (pd.to_numeric(df_1k[latest_col_1k], errors='coerce').fillna(0) > 0)
                cond_400 = (pd.to_numeric(df_400['▼6周增減'], errors='coerce').fillna(0) > 0) & (pd.to_numeric(df_400[latest_col_400], errors='coerce').fillna(0) > 0)
                set_1k = set(df_1k[cond_1k]['統一代號'])
                set_400 = set(df_400[cond_400]['統一代號'])
                valid_resonance_codes.update(set_1k.intersection(set_400))
                
            if b5_double:
                # 雙引擎共振：1k與400 週動態皆包含「增」
                cond_1k_inc = df_1k['週動態'].astype(str).str.contains('增', na=False)
                cond_400_inc = df_400['週動態'].astype(str).str.contains('增', na=False)
                set_1k_inc = set(df_1k[cond_1k_inc]['統一代號'])
                set_400_inc = set(df_400[cond_400_inc]['統一代號'])
                
                # 如果兩者都有勾，取聯集；如果只有勾雙引擎，就只用雙引擎的交集
                if b5_long_short: valid_resonance_codes.intersection_update(set_1k_inc.intersection(set_400_inc))
                else: valid_resonance_codes.update(set_1k_inc.intersection(set_400_inc))
                
            filtered_df = filtered_df[filtered_df['統一代號'].isin(list(valid_resonance_codes))]

    # 2. 處理波段吸籌過濾 (6周增減 > 0)
    b5_6w_configs = [
        (b5_6w_1000, df_1k, "1000張"), (b5_6w_800, df_800, "800張"),
        (b5_6w_600, df_600, "600張"), (b5_6w_400, df_400, "400張")
    ]
    for is_checked, df_lvl, lvl_name in b5_6w_configs:
        if is_checked:
            any_filter_applied = True
            if not df_lvl.empty and '▼6周增減' in df_lvl.columns:
                cond = pd.to_numeric(df_lvl['▼6周增減'], errors='coerce').fillna(0) > 0
                valid_codes = df_lvl[cond]['統一代號'].unique()
                filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_codes)]
            else:
                st.warning(f"⚠️ {lvl_name} 資料庫缺乏 6周增減欄位，過濾為空。")
                filtered_df = filtered_df.iloc[0:0]

    # 3. 處理各級距動態過濾 (交集邏輯)
    b5_trend_configs = [
        (b5_trend_1000, df_1k, "1000張"), (b5_trend_800, df_800, "800張"),
        (b5_trend_600, df_600, "600張"), (b5_trend_400, df_400, "400張")
    ]
    for trends, df_lvl, lvl_name in b5_trend_configs:
        if trends:
            any_filter_applied = True
            if not df_lvl.empty and '週動態' in df_lvl.columns:
                valid_lvl_codes = df_lvl[df_lvl['週動態'].isin(trends)]['統一代號'].unique()
                filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_lvl_codes)]
            else:
                st.warning(f"⚠️ {lvl_name} 資料庫尚未建立或缺乏動態欄位，過濾為空。")
                filtered_df = filtered_df.iloc[0:0]

    # 處理 B6 過濾引擎
    if b6_today_chk or b6_amt_min > 0 or b6_status_chk:
        df_b6 = clean_stock_id(get_df('b6_today'))
        if not df_b6.empty:
            any_filter_applied = True
            b6_mask = pd.Series(True, index=df_b6.index)
            
            # 資金規模
            if b6_amt_min > 0:
                df_b6['num_amt'] = pd.to_numeric(df_b6['總額(億)'], errors='coerce').fillna(0)
                b6_mask &= (df_b6['num_amt'] >= b6_amt_min)
            
            # 防守狀態
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
            
            valid_b6_codes = df_b6[b6_mask]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b6_codes)]
        else:
            st.warning("⚠️ 缺乏 B6 今日鉅額交易資料，過濾為空。請確認 B6 頁面已載入資料。")
            filtered_df = filtered_df.iloc[0:0]

    # 處理 B7 過濾引擎
    b7_hold_min, b7_hold_max = b7_hold_pct
    b7_pledge_min, b7_pledge_max = b7_pledge_pct

    # 1. 處理持股/質押比例過濾
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

            valid_b7_codes = df_b7_pledge[b7_mask]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_b7_codes)]

    # 2. 處理持股動態過濾
    if b7_hold_trend:
        df_b7_main = clean_stock_id(get_df('b7_main'))
        if not df_b7_main.empty and '動態' in df_b7_main.columns:
            any_filter_applied = True
            valid_hold_codes = df_b7_main[df_b7_main['動態'].isin(b7_hold_trend)]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_hold_codes)]

    # 3. 處理質押動態過濾
    if b7_pledge_trend:
        df_b7_hist = clean_stock_id(get_df('b7_pledge_history'))
        if not df_b7_hist.empty and '動態' in df_b7_hist.columns:
            any_filter_applied = True
            valid_pledge_codes = df_b7_hist[df_b7_hist['動態'].isin(b7_pledge_trend)]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_pledge_codes)]

    # 4. 處理近半年波段持股增加
    if b7_6m_inc:
        df_b7_main = clean_stock_id(get_df('b7_main'))
        if not df_b7_main.empty and '▼近半年增減%' in df_b7_main.columns:
            any_filter_applied = True
            valid_6m_codes = df_b7_main[pd.to_numeric(df_b7_main['▼近半年增減%'], errors='coerce').fillna(0) > 0]['統一代號'].unique()
            filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_6m_codes)]
        else:
            st.warning("⚠️ 缺乏 B7 近半年持股數據，波段過濾為空。")
            filtered_df = filtered_df.iloc[0:0]
# ==========================================
# 過濾結果結算與除錯透視鏡檢核
# ==========================================
    if any_filter_applied:
        st.success(f"✅ 過濾完成！共有 **{len(filtered_df)}** 檔標的符合您的跨模組條件。")
        debug_mode = st.checkbox("🔬 開啟除錯透視鏡 (核對名單與過濾數值)")
        if debug_mode:
            # ==========================================
            # 🌟 加入 B0 基礎價量供核對
            # ==========================================
            df_b0_debug = clean_stock_id(get_df('b0_price')).drop_duplicates(subset=['統一代號'])
            debug_df = filtered_df.copy()
            if not df_b0_debug.empty:
                b0_cols = ['統一代號']
                rename_dict = {}
                for col in ['成交', '漲跌幅', '成交張數', '成交額(百萬)', 'PER']:
                    if col in df_b0_debug.columns:
                        b0_cols.append(col)
                        rename_dict[col] = f'B0_{col}'
                debug_df = pd.merge(debug_df, df_b0_debug[b0_cols].rename(columns=rename_dict), on='統一代號', how='left')

            check_cols = [
                '統一代號', '今日上榜', '△', '法人持股', '最新動態',
                '5日ΔChange', '20日ΔChange', '60日ΔChange', '120日ΔChange'
            ]
            # (以下是原本的 df_b1_debug 程式碼，維持不變...)
            check_cols = [
                '統一代號', '今日上榜', '△', '法人持股', '最新動態',
                '5日ΔChange', '20日ΔChange', '60日ΔChange', '120日ΔChange'
            ]
            # 🛡️ 斬斷笛卡爾積：合併前一律強制去重
            df_b1_debug = df_b1_raw[[c for c in check_cols if c in df_b1_raw.columns]].drop_duplicates(subset=['統一代號'])
            debug_df = pd.merge(filtered_df, df_b1_debug, on='統一代號', how='left')
            
            # 加入 B2 四大表的動態，供核對
            b2_labels = zip(['b2_1', 'b2_2', 'b2_3', 'b2_4'], ['外資成交動態', '投信成交動態', '外資發行動態', '投信發行動態'])
            for b2_key, col_name in b2_labels:
                df_b2_tmp = clean_stock_id(get_df(b2_key)).drop_duplicates(subset=['統一代號'])
                if not df_b2_tmp.empty and '今日短動態' in df_b2_tmp.columns:
                    debug_df = pd.merge(debug_df, df_b2_tmp[['統一代號', '今日短動態']].rename(columns={'今日短動態': f'B2_{col_name}'}), on='統一代號', how='left')

            # 加入 B3 狀態供核對
            df_b3_main = get_df('b3_main')
            if not df_b3_main.empty:
                df_b3_main = clean_stock_id(df_b3_main).drop_duplicates(subset=['統一代號', '連買類型']) 
                df_b3_main['B3_組合狀態'] = df_b3_main['連買類型'] + "(" + df_b3_main['連買週期數'].astype(str) + ")-" + df_b3_main['狀態動態']
                b3_summary = df_b3_main.groupby('統一代號')['B3_組合狀態'].apply(lambda x: " | ".join(x)).reset_index()
                debug_df = pd.merge(debug_df, b3_summary.rename(columns={'B3_組合狀態': 'B3_連買狀態'}), on='統一代號', how='left')

            # 加入 B4 雷達狀態供核對
            sq_df_debug = clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame())).drop_duplicates(subset=['統一代號'])
            rk_df_debug = clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame())).drop_duplicates(subset=['統一代號'])
            
            if not sq_df_debug.empty:
                debug_df = pd.merge(debug_df, sq_df_debug[['統一代號', '軋空評估']], on='統一代號', how='left')
            if not rk_df_debug.empty:
                debug_df = pd.merge(debug_df, rk_df_debug[['統一代號', '套牢評估']], on='統一代號', how='left')
                
            # 加入 B4 12大資券動態供核對 (包含實際金額)
            b4_debug_keys = {
                'b4_margin_pct': '融資減幅', 'b4_margin_vol': '融資減張',
                'b4_short_pct': '借券減幅', 'b4_short_vol': '借券減張',
                'b4_margin_plus_pct': '融券增幅', 'b4_margin_plus_vol': '融券增張',
                'b4_margin_inc_pct': '融資增幅', 'b4_short_inc_pct': '借券增幅',
                'b4_margin_inc_vol': '融資增張', 'b4_short_inc_vol': '借券增張',
                'b4_short_dec_amt': '借券實際減額', 'b4_short_inc_amt': '借券實際增額'
            }
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
                        
                    if len(extract_cols) > 1:
                        debug_df = pd.merge(debug_df, df_tmp[extract_cols].rename(columns=rename_dict), on='統一代號', how='left')

            # ==========================================
            # 🌟 加入 B5 大腿動向供核對
            # ==========================================
            b5_debug_keys = {
                'b5_1000': 'B5_1000張',
                'b5_800': 'B5_800張',
                'b5_600': 'B5_600張',
                'b5_400': 'B5_400張'
            }
            
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
                        
                    if len(extract_cols) > 1:
                        debug_df = pd.merge(debug_df, df_b5_tmp[extract_cols].rename(columns=rename_dict), on='統一代號', how='left')
            
            # 加入 B5 共振狀態判定
            if 'B5_1000張_週動態' in debug_df.columns and 'B5_400張_週動態' in debug_df.columns:
                def check_resonance(row):
                    res = []
                    inc_1k = "增" in str(row.get('B5_1000張_週動態', ''))
                    inc_400 = "增" in str(row.get('B5_400張_週動態', ''))
                    if inc_1k and inc_400:
                        res.append("雙引擎")
                    
                    try:
                        v1k_wk = float(str(row.get('B5_1000張_最新週', '0')).replace('%','').replace('+',''))
                        v1k_6wk = float(str(row.get('B5_1000張_6周', '0')).replace('%','').replace('+',''))
                        v400_wk = float(str(row.get('B5_400張_最新週', '0')).replace('%','').replace('+',''))
                        v400_6wk = float(str(row.get('B5_400張_6周', '0')).replace('%','').replace('+',''))
                        
                        if v1k_wk > 0 and v1k_6wk > 0 and v400_wk > 0 and v400_6wk > 0:
                            res.append("長短線")
                    except: pass
                    return " | ".join(res) if res else ""
                
                debug_df['B5_共振狀態'] = debug_df.apply(check_resonance, axis=1)


            # 加入 B6 鉅額交易供核對
            df_b6_debug = clean_stock_id(get_df('b6_today')).drop_duplicates(subset=['統一代號'])
            if not df_b6_debug.empty:
                b6_cols = ['統一代號', '總額(億)']
                dynamic_col = st.session_state.get('b6_dynamic_price_col')
                
                # 若同時有成交均價與收盤價，就自動幫您算出防守狀態
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
                    
                # 容錯處理：如果只有其中一個欄位
                elif dynamic_col and dynamic_col in df_b6_debug.columns:
                    b6_cols.append(dynamic_col)
                elif '▼收盤價' in df_b6_debug.columns:
                    b6_cols.append('▼收盤價')
                
                debug_df = pd.merge(debug_df, df_b6_debug[b6_cols].rename(columns={
                    '總額(億)': 'B6_總額(億)',
                    dynamic_col: 'B6_成交均價' if dynamic_col else 'B6_成交均價',
                    '▼收盤價': 'B6_收盤價'
                }), on='統一代號', how='left')

            # ==========================================
            # 🌟 加入 B7 董監動向供核對
            # ==========================================
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
                
                # 自動加入近半年增減% 供核對
                if '▼近半年增減%' in df_b7_main.columns:
                    b7_main_cols.append('▼近半年增減%')
                    b7_main_rename['▼近半年增減%'] = 'B7_持股近半年增減%'
                    
                debug_df = pd.merge(debug_df, df_b7_main[b7_main_cols].rename(columns=b7_main_rename), on='統一代號', how='left')
            df_b7_hist = clean_stock_id(get_df('b7_pledge_history')).drop_duplicates(subset=['統一代號'])
            if not df_b7_hist.empty and '動態' in df_b7_hist.columns:
                debug_df = pd.merge(debug_df, df_b7_hist[['統一代號', '近月質押增減(%)', '動態']].rename(columns={
                    '近月質押增減(%)': 'B7_質押近月增減%', '動態': 'B7_質押動態'
                }), on='統一代號', how='left')
            #####
            st.write(f"🔍 檢核明細 (共 {len(debug_df)} 筆)：")
            st.dataframe(debug_df, use_container_width=True, hide_index=True)
            #####           
    else:
        st.info("👆 請在上方展開模組中至少設定一項條件，目前預設顯示全市場標的。")

    st.write("---")

    # ==========================================
    # 2. 第二關：自訂權重計分面板
    # ==========================================
    st.markdown("#### 2️⃣ 設定計分權重 (Weights)")
    st.caption("為各項籌碼動向設定加權分數 (設定為 0 代表不計分，負數代表扣分)")
    
    with st.expander("⚙️ 展開設定各區塊權重", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**法人持股動向**")
            w_b1_up = st.number_input("法人正向進榜 (次)", value=1.0, step=0.5)
            w_b1_down = st.number_input("法人衰退進榜 (次)", value=-1.0, step=0.5)
        with c2:
            st.markdown("**突擊掃貨與連買**")
            w_b2 = st.number_input("法人單日突擊掃貨", value=1.5, step=0.5)
            w_b3 = st.number_input("法人連續買超", value=2.0, step=0.5)
        with c3:
            st.markdown("**資券籌碼變化**")
            w_b4_good = st.number_input("融資減/借券減", value=1.0, step=0.5)
        with c4:
            st.markdown("**大戶與董監防線**")
            w_b5 = st.number_input("千張大戶持股增加", value=3.0, step=0.5)
            w_b6 = st.number_input("鉅額防守成功", value=1.5, step=0.5)  # <-- 新增這行
            w_b7 = st.number_input("董監增持/質押降", value=1.5, step=0.5)

    # ==========================================
    # 3. 執行計分運算 (Scoring Engine)
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
            for k in ['b4_margin_pct', 'b4_short_pct', 'b4_margin_plus_pct', 'b4_margin_vol', 'b4_short_vol', 'b4_margin_plus_vol']:
                apply_score(k, w_b4_good, "資券有利")
            apply_score('b5_1000', w_b5, "千張大戶")
            
            # 處理 B6 鉅額防守成功加分
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

            # 處理 B7 董監增持 / 質押降 加分
            if w_b7 != 0:
                # 1. 董監持股增加 (近月增減 > 0)
                df_b7_main = clean_stock_id(get_df('b7_main'))
                if not df_b7_main.empty and '近月增減%' in df_b7_main.columns:
                    valid_inc_codes = df_b7_main[pd.to_numeric(df_b7_main['近月增減%'], errors='coerce') > 0]['統一代號'].unique()
                    mask = score_df['統一代號'].isin(valid_inc_codes)
                    score_df.loc[mask, '總分'] += w_b7
                    sign = "+" if w_b7 > 0 else ""
                    score_df.loc[mask, '得分明細'] += f"[董監增持 {sign}{w_b7}] "

                # 2. 董監質押下降 (近月質押增減 < 0)
                df_b7_hist = clean_stock_id(get_df('b7_pledge_history'))
                if not df_b7_hist.empty and '近月質押增減(%)' in df_b7_hist.columns:
                    valid_dec_codes = df_b7_hist[pd.to_numeric(df_b7_hist['近月質押增減(%)'], errors='coerce') < 0]['統一代號'].unique()
                    mask = score_df['統一代號'].isin(valid_dec_codes)
                    score_df.loc[mask, '總分'] += w_b7
                    sign = "+" if w_b7 > 0 else ""
                    score_df.loc[mask, '得分明細'] += f"[質押下降 {sign}{w_b7}] "

            # ==========================================
            # 4. 結果展示
            # ==========================================
            score_df = score_df.sort_values(by='總分', ascending=False).reset_index(drop=True)
            result_df = score_df[score_df['總分'] != 0].copy()

            st.write("---")
            st.markdown(f"### 🏆 策略計分結果 (共 {len(result_df)} 檔獲取分數)")
            
            if not result_df.empty:
                def highlight_score(val):
                    if val >= 5: return 'color: #FF4B4B; font-weight: bold'
                    elif val > 0: return 'color: #38BDF8'
                    elif val < 0: return 'color: #00E676'
                    return ''
                
                display_df = result_df[['統一代號', '股票名稱', '產業別', '總分', '得分明細']].rename(columns={'統一代號': '股票代號'})
                st.dataframe(
                    display_df.style.map(highlight_score, subset=['總分']), 
                    use_container_width=True,
                    hide_index=True
                )
            else:
                if len(score_df) > 0:
                    st.warning(f"名單中有 {len(score_df)} 檔標的符合過濾條件，但在您的權重設定下得分均為 0。")
                else:
                    st.warning("沒有任何標的符合您的嚴格過濾條件。")
