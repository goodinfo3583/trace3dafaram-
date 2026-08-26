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
    """取得 Session 內的資料表"""
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
    # 0. 建立全市場候選池 (大解放：不再做任何刪減)
    # ==========================================
    pool = []
    if STOCK_DICT:
        for v in STOCK_DICT.values():
            sid = str(v.get("id", "")).strip()
            ind = str(v.get("industry", ""))
            # 只要有代碼，不管長度是 4 碼、5 碼還是包含英文字母的 ETF，一律納入候選池！
            if sid:
                pool.append({"統一代號": sid, "股票名稱": v.get("name", ""), "產業別": ind if ind else "未分類"})
    
    base_df = pd.DataFrame(pool)
    if not base_df.empty:
        # 強制剃除重複代號 (防呆)
        base_df = base_df.drop_duplicates(subset=['統一代號']).reset_index(drop=True)
    else:
        st.warning("⚠️ 無法載入股票字典檔，請確認系統資料。")
        return

    # ==========================================
    # 1. 第一關：嚴格過濾器 (依據 B1~B7 分類)
    # ==========================================
    st.markdown(f"#### 1️⃣ 選擇選股池基底 (目前全市場總候選池共 {len(base_df)} 檔)")
    
    # 取得 B1 資料的最新日期並格式化
    b1_sorted_dates = st.session_state.get('b1_sorted_dates', [])
    b1_latest_date_str = "未知日期"
    if b1_sorted_dates and len(str(b1_sorted_dates[0])) == 8:
        d_str = str(b1_sorted_dates[0])
        b1_latest_date_str = f"{d_str[:4]}/{d_str[4:6]}/{d_str[6:]}"

    base_category = st.selectbox(
        "請選擇第一關過濾的籌碼模組：",
        [
            "🌍 全市場掃描 (不做額外過濾)",
            f"📈 B1 法人持股動向 (資料基準日: {b1_latest_date_str})",
            "🚀 B2 法人突擊掃貨 (建置中)",
            "🔥 B3 法人連續買超 (建置中)",
            "📉 B4 資券籌碼變化 (建置中)",
            "🐳 B5 大戶籌碼動向 (建置中)",
            "🛡️ B7 董監內部防線 (建置中)"
        ]
    )

    filtered_df = base_df.copy()

    # ------------------------------------------
    # 🎯 模組 B1：法人持股動向 (細緻化過濾)
    # ------------------------------------------
    if "B1 法人持股動向" in base_category:
        st.markdown("**🔹 請勾選要交集過濾的條件 (若勾選多個，標的必須「同時符合」)：**")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        b1_delta = c1.checkbox("當日△上升 (>0)")
        b1_5d = c2.checkbox("🔴 5日上榜")
        b1_20d = c3.checkbox("🟡 20日上榜")
        b1_60d = c4.checkbox("🟢 60日上榜")
        b1_120d = c5.checkbox("🔵 120日上榜")

        df_b1 = clean_stock_id(get_df('b1_final_df'))
        
        if not df_b1.empty:
            hit_mask = pd.Series(True, index=df_b1.index)
            any_checked = False

            if b1_delta:
                any_checked = True
                df_b1['num_delta'] = pd.to_numeric(df_b1['△'].astype(str).str.replace('%', '', regex=False).str.replace('+', '', regex=False), errors='coerce').fillna(0)
                hit_mask &= (df_b1['num_delta'] > 0)
                
            if b1_5d:
                any_checked = True
                hit_mask &= df_b1['今日上榜'].astype(str).str.contains('🔴5日')
                
            if b1_20d:
                any_checked = True
                hit_mask &= df_b1['今日上榜'].astype(str).str.contains('🟡20日')
                
            if b1_60d:
                any_checked = True
                hit_mask &= df_b1['今日上榜'].astype(str).str.contains('🟢60日')
                
            if b1_120d:
                any_checked = True
                hit_mask &= df_b1['今日上榜'].astype(str).str.contains('🔵120日')

            if any_checked:
                hit_codes = df_b1[hit_mask]['統一代號'].unique()
                filtered_df = filtered_df[filtered_df['統一代號'].isin(hit_codes)]
                st.success(f"✅ B1 過濾完成！共有 **{len(filtered_df)}** 檔標的符合條件。")
                
                # 🔬 除錯透視鏡：讓您隨時檢查被挑出的名單是不是真的符合！
                debug_mode = st.checkbox("🔬 開啟除錯透視鏡 (檢核名單與數據)")
                if debug_mode:
                    debug_df = pd.merge(filtered_df, df_b1[['統一代號', '今日上榜', '△']], on='統一代號', how='left')
                    st.write(f"🔍 檢核明細 (共 {len(debug_df)} 筆)：")
                    st.dataframe(debug_df, use_container_width=True, hide_index=True)

            else:
                st.info("👆 請在上方至少勾選一項條件，目前預設顯示全市場標的。")
        else:
            st.warning("⚠️ 找不到 B1 法人持股動向數據，請確認資料是否已讀取。")

    # ------------------------------------------
    # 佔位符：其他模組建置中
    # ------------------------------------------
    elif "建置中" in base_category:
        st.info(f"🚧 此模組的精細過濾器建置中，請先測試 B1 模組。")

    st.write("---")

    # ==========================================
    # 2. 第二關：自訂權重計分面板 (暫時保留原狀)
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

            b1_df = clean_stock_id(get_df('b1_final_df'))
            if not b1_df.empty and w_b1_up != 0 and '上榜數量' in b1_df.columns:
                for _, row in b1_df.iterrows():
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
