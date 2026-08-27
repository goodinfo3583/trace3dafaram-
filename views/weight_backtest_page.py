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
    # 0. 建立完美全市場候選池 (聯集字典檔與大數據庫)
    # ==========================================
    pool_dict = {}
    
    if STOCK_DICT:
        for v in STOCK_DICT.values():
            sid = str(v.get("id", "")).strip()
            if sid:
                pool_dict[sid] = {
                    "統一代號": sid, 
                    "股票名稱": v.get("name", ""), 
                    "產業別": v.get("industry", "未分類")
                }
                
    df_b1_raw = clean_stock_id(get_df('b1_final_df'))
    if not df_b1_raw.empty:
        for _, row in df_b1_raw.iterrows():
            sid = str(row['統一代號']).strip()
            if sid and sid not in pool_dict:
                pool_dict[sid] = {
                    "統一代號": sid,
                    "股票名稱": str(row.get('股票名稱', '')),
                    "產業別": "ETF/基金/其他" 
                }
                
    base_df = pd.DataFrame(list(pool_dict.values()))
    if base_df.empty:
        st.warning("⚠️ 無法建立候選池，請確認資料庫狀態。")
        return

    # ==========================================
    # 1. 第一關：嚴格過濾器 (支援跨模組展開與交集)
    # ==========================================
    st.markdown(f"#### 1️⃣ 設定嚴格過濾條件 (目前全市場總候選池共 {len(base_df)} 檔)")
    st.caption("💡 **跨模組複選功能**：不同模組間的勾選會進行「交集 (嚴格篩選)」。動態特徵內的多選則為「聯集 (符合其一即可)」。")
    
    filtered_df = base_df.copy()
    any_filter_applied = False

    b1_sorted_dates = st.session_state.get('b1_sorted_dates', [])
    b1_latest_date_str = "未知日期"
    if b1_sorted_dates and len(str(b1_sorted_dates[0])) == 8:
        d_str = str(b1_sorted_dates[0])
        b1_latest_date_str = f"{d_str[:4]}/{d_str[4:6]}/{d_str[6:]}"

    # --- 模組 B1 展開面板 ---
    with st.expander(f"📈 B1 法人持股動向 (資料基準日: {b1_latest_date_str})", expanded=True):
        st.markdown("**🔹 1. 近期進榜天數與變化**")
        c1, c2, c3, c4, c5 = st.columns(5)
        b1_delta = c1.checkbox("當日△上升 (>0)")
        b1_5d = c2.checkbox("🔴 5日上榜")
        b1_20d = c3.checkbox("🟡 20日上榜")
        b1_60d = c4.checkbox("🟢 60日上榜")
        b1_120d = c5.checkbox("🔵 120日上榜")

        st.markdown("**🔹 2. 法人持股比例區間 (%)**")
        b1_ratio_min, b1_ratio_max = st.slider(
            "拉動滑桿設定過濾範圍 (設定為 0~100 代表不作限制)：", 
            min_value=0.0, max_value=100.0, value=(0.0, 100.0), step=0.5
        )

        st.markdown("**🔹 3. 區間累計持股增減 (ΔChange %)**")
        st.caption("設定特定區間內的持股增減幅度 (預設 -100~100 代表不限制，拉動至 0~100 即可尋找純增加的標的)")
        c_chg1, c_chg2 = st.columns(2)
        with c_chg1:
            b1_5d_chg = st.slider("5日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5)
            b1_60d_chg = st.slider("60日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5)
        with c_chg2:
            b1_20d_chg = st.slider("20日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5)
            b1_120d_chg = st.slider("120日 ΔChange", -100.0, 100.0, (-100.0, 100.0), 0.5)

        st.markdown("**🔹 4. 最新動態特徵**")
        b1_trend_logic = st.radio("特徵篩選邏輯：", ["交集 (必須同時符合勾選的所有特徵)", "聯集 (符合其中任一特徵即可)"], horizontal=True)
        trend_options = [
            "📈 上升", "📉 下降", "🪜 階梯吸籌", "🛡️ 穩健吸籌", "⚠️ 趨緩", 
            "🚀 衝進🔴5日榜單", "🚀 衝進🟡20日榜單", "🚀 衝進🟢60日榜單", "🚀 衝進🔵120日榜單"
        ]
        b1_trends = st.multiselect("請選擇要過濾的動態特徵：", trend_options)

    # --- 模組 B2~B7 展開面板 (預留) ---
    with st.expander("🐳 B5 大戶籌碼動向 (建置中)", expanded=False):
        b5_1000 = st.checkbox("千張大戶持股增加 (測試鈕)")

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

    # 處理 B5 過濾 (測試用)
    if b5_1000:
        any_filter_applied = True
        df_b5 = clean_stock_id(get_df('b5_1000'))
        if not df_b5.empty:
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df_b5['統一代號'])]
        else:
            filtered_df = filtered_df.iloc[0:0] 

    # 過濾結果結算與除錯檢核
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
            st.write(f"🔍 檢核明細 (共 {len(debug_df)} 筆)：")
            st.dataframe(debug_df, use_container_width=True, hide_index=True)
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
