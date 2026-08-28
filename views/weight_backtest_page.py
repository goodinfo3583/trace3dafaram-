# views/weight_backtest_page.py
import streamlit as st
import pandas as pd
import re

# ==========================================
# 🌟 導入背景喚醒引擎
# ==========================================
try:
    from views.sidebar import ensure_b1_to_b5_loaded
except ImportError:
    def ensure_b1_to_b5_loaded(DATA_DIR): pass

# ==========================================
# 🌟 萬能鑰匙：對接全站暫存變數
# ==========================================
KEY_MAP = {
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
    'b5_400': ['b5_400', 'df_blk5'],
    'b5_1000': ['b5_1000', 'df_blk5_1000'],
    'b5_resonance': ['b5_resonance', 'df_b5_resonance', 'df_resonance', 'df_長短線共振'],
    'b5_double': ['b5_double', 'df_b5_double', 'df_double', 'df_雙向共振'],
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

def show_weight_backtest_page(STOCK_DICT, DATA_DIR="data"):
    # 背景自動載入原始資料
    ensure_b1_to_b5_loaded(DATA_DIR)

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
            for k in ['pct_41', 'vol_41', 'pct_42', 'vol_42', 'pct_43', 'vol_43', 'pct_inc_margin', 'pct_inc_short']:
                st.session_state[f'filter_b4_{k}'] = False
                
            # --- 新增的 B4 滑桿與加速特徵清空 ---
            st.session_state['filter_b4_price_chg'] = (-10.0, 10.0)
            for k in ['acc_margin_dec', 'acc_sbl_dec', 'acc_margin_inc', 'acc_sbl_inc']:
                st.session_state[f'filter_b4_{k}'] = False
            # -----------------------------------

            st.session_state['filter_b4_radio'] = "交集 (必須同時符合勾選特徵)"
            st.session_state['filter_b4_multi'] = []

            st.session_state['filter_b5_1000'] = False

        st.button("🧹 清空所有篩選條件", on_click=reset_filters, use_container_width=True)

    filtered_df = base_df.copy()
    any_filter_applied = False

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
    #
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
        with c_b4_2:
            b4_41_vol = st.checkbox(f"融資減少張數【5日累計張】(前 {b4_top_n} 名)", key="filter_b4_vol_41")
            b4_42_vol = st.checkbox(f"借券賣出減少張數【5日累計張】(前 {b4_top_n} 名)", key="filter_b4_vol_42")
            b4_43_vol = st.checkbox(f"融券增加張數【5日累計張】(前 {b4_top_n} 名)", key="filter_b4_vol_43")
            b4_inc_short_pct = st.checkbox(f"借券賣出增加幅度【5日累計比】(前 {b4_top_n} 名)", key="filter_b4_pct_inc_short")

        st.markdown("**🔹 2. 今日漲跌幅區間過濾 (%)**")
        b4_price_chg = st.slider("設定漲跌幅區間 (預設 -10~10 代表不限制，設定 2~10 代表只找大漲的標的)：", -10.0, 10.0, (-10.0, 10.0), 0.5, key="filter_b4_price_chg")

        st.markdown("**🔹 3. 籌碼加速特徵 (當日短線力道 > 5日均幅)**")
        c_acc1, c_acc2 = st.columns(2)
        b4_acc_margin_dec = c_acc1.checkbox("⏩ 融資加速退場 (當日減幅 > 5日均)", key="filter_b4_acc_margin_dec")
        b4_acc_sbl_dec = c_acc1.checkbox("⏩ 借券加速回補 (當日減幅 > 5日均)", key="filter_b4_acc_sbl_dec")
        b4_acc_margin_inc = c_acc2.checkbox("⚠️ 融資加速套牢 (當日增幅 > 5日均)", key="filter_b4_acc_margin_inc")
        b4_acc_sbl_inc = c_acc2.checkbox("⚠️ 借券加速放空 (當日增幅 > 5日均)", key="filter_b4_acc_sbl_inc")

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

    # --- 展開面板 (預留) ---
    with st.expander("🐳 B5 大戶籌碼動向 (建置中)", expanded=False):
        b5_1000 = st.checkbox("千張大戶持股增加 (測試鈕)", key="filter_b5_1000")

    with st.expander("📉 其他籌碼動向模組 (建置中)", expanded=False):
        st.info("包含法人突擊掃貨、連買、資券動向等模組，將於後續開放。")
        

    # ==========================================
    # 執行過濾邏輯
    # ==========================================
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
        'b4_short_inc_pct': b4_inc_short_pct
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

    # 處理 B4 短線籌碼加速特徵過濾 (嚴格方向性與均值運算)
    acc_configs = [
        (b4_acc_margin_dec, 'b4_margin_pct', 'dec'), (b4_acc_sbl_dec, 'b4_short_pct', 'dec'),
        (b4_acc_margin_inc, 'b4_margin_inc_pct', 'inc'), (b4_acc_sbl_inc, 'b4_short_inc_pct', 'inc')
    ]
    for is_checked, df_key, direction in acc_configs:
        if is_checked:
            any_filter_applied = True
            df_acc = clean_stock_id(get_df(df_key))
            if not df_acc.empty:
                col_today = next((c for c in df_acc.columns if '當日' in c and '%' in c), next((c for c in df_acc.columns if '當日' in c), None))
                col_5d = next((c for c in df_acc.columns if '5日' in c and '%' in c), next((c for c in df_acc.columns if '5日' in c), None))
                
                if col_today and col_5d:
                    # 保留原始正負號，才能正確判斷是增加還是減少
                    df_acc['num_today'] = pd.to_numeric(df_acc[col_today], errors='coerce').fillna(0)
                    df_acc['num_5d'] = pd.to_numeric(df_acc[col_5d], errors='coerce').fillna(0)
                    
                    if direction == 'inc':
                        # 【加速套牢/放空】：當日必須是正值(有增加)，且當日的增幅 > 5日平均增幅
                        valid_acc_codes = df_acc[(df_acc['num_today'] > 0) & (df_acc['num_today'] > (df_acc['num_5d'] / 5.0))]['統一代號'].unique()
                    else:
                        # 【加速退場/回補】：當日必須是負值(有減少)，且當日的減幅(負得更多) < 5日平均減幅
                        valid_acc_codes = df_acc[(df_acc['num_today'] < 0) & (df_acc['num_today'] < (df_acc['num_5d'] / 5.0))]['統一代號'].unique()
                        
                    filtered_df = filtered_df[filtered_df['統一代號'].isin(valid_acc_codes)]
                else:
                    st.warning(f"⚠️ {df_key} 缺乏當日或5日欄位，無法計算加速特徵。")
                    filtered_df = filtered_df.iloc[0:0]

    # 處理 B5 過濾 (測試用)
    if b5_1000:
        any_filter_applied = True
        df_b5 = clean_stock_id(get_df('b5_1000'))
        if not df_b5.empty:
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b5['統一代號'])]
        else:
            filtered_df = filtered_df.iloc[0:0] 
    # ==========================================
    # 過濾結果結算與除錯檢核
    # ==========================================
    if any_filter_applied:
        st.success(f"✅ 過濾完成！共有 **{len(filtered_df)}** 檔標的符合您的跨模組條件。")
        debug_mode = st.checkbox("🔬 開啟除錯透視鏡 (核對名單與過濾數值)")
        if debug_mode:
            # 撈出需要檢核的核心欄位 (加入 ΔChange 欄位，證明系統沒有混淆)
            check_cols = [
                '統一代號', '今日上榜', '△', '法人持股', '最新動態',
                '5日ΔChange', '20日ΔChange', '60日ΔChange', '120日ΔChange'
            ]
            debug_df = pd.merge(filtered_df, df_b1_raw[[c for c in check_cols if c in df_b1_raw.columns]], on='統一代號', how='left')
            
            # 加入 B2 四大表的動態，供核對
            b2_labels = zip(['b2_1', 'b2_2', 'b2_3', 'b2_4'], ['外資成交動態', '投信成交動態', '外資發行動態', '投信發行動態'])
            for b2_key, col_name in b2_labels:
                df_b2_tmp = clean_stock_id(get_df(b2_key))
                if not df_b2_tmp.empty and '今日短動態' in df_b2_tmp.columns:
                    debug_df = pd.merge(debug_df, df_b2_tmp[['統一代號', '今日短動態']].rename(columns={'今日短動態': f'B2_{col_name}'}), on='統一代號', how='left')

            # 加入 B3 狀態供核對
            df_b3_main = get_df('b3_main')
            if not df_b3_main.empty:
                df_b3_main = clean_stock_id(df_b3_main)
                # 將「連買週期數」與「狀態動態」合併成好讀的字串
                df_b3_main['B3_組合狀態'] = df_b3_main['連買類型'] + "(" + df_b3_main['連買週期數'].astype(str) + ")-" + df_b3_main['狀態動態']
                b3_summary = df_b3_main.groupby('統一代號')['B3_組合狀態'].apply(lambda x: " | ".join(x)).reset_index()
                debug_df = pd.merge(debug_df, b3_summary.rename(columns={'B3_組合狀態': 'B3_連買狀態'}), on='統一代號', how='left')

            # 加入 B4 雷達狀態供核對
            sq_df_debug = clean_stock_id(st.session_state.get('b4_squeeze_radar', {}).get('df', pd.DataFrame()))
            rk_df_debug = clean_stock_id(st.session_state.get('b4_risk_radar', {}).get('df', pd.DataFrame()))
            
            if not sq_df_debug.empty:
                debug_df = pd.merge(debug_df, sq_df_debug[['統一代號', '軋空評估']], on='統一代號', how='left')
            if not rk_df_debug.empty:
                debug_df = pd.merge(debug_df, rk_df_debug[['統一代號', '套牢評估']], on='統一代號', how='left')

            # 加入 B4 8大資券的 5日與當日動態供核對
            b4_debug_keys = {
                'b4_margin_pct': '融資減幅', 'b4_margin_vol': '融資減張',
                'b4_short_pct': '借券減幅', 'b4_short_vol': '借券減張',
                'b4_margin_plus_pct': '融券增幅', 'b4_margin_plus_vol': '融券增張',
                'b4_margin_inc_pct': '融資增幅', 'b4_short_inc_pct': '借券增幅'
            }
            for k, label in b4_debug_keys.items():
                df_tmp = clean_stock_id(get_df(k))
                if not df_tmp.empty:
                    # 智慧搜尋當日與5日欄位 (相容各種資料庫命名)
                    col_today = next((c for c in df_tmp.columns if '當日' in c and '%' in c), next((c for c in df_tmp.columns if '當日' in c), None))
                    col_5d = next((c for c in df_tmp.columns if '5日' in c and '%' in c), next((c for c in df_tmp.columns if '5日' in c), None))
                    
                    extract_cols = ['統一代號']
                    rename_dict = {}
                    if col_today:
                        extract_cols.append(col_today)
                        rename_dict[col_today] = f"B4_{label}_當日"
                    if col_5d:
                        extract_cols.append(col_5d)
                        rename_dict[col_5d] = f"B4_{label}_5日"
                        
                    if len(extract_cols) > 1:
                        # 將抽出的欄位與 debug_df 合併
                        debug_df = pd.merge(debug_df, df_tmp[extract_cols].rename(columns=rename_dict), on='統一代號', how='left')

            st.write(f"🔍 檢核明細 (共 {len(debug_df)} 筆)：")
            st.dataframe(debug_df, use_container_width=True, hide_index=True)
            #
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
            apply_score('b7_main', w_b7, "董監增持")

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
