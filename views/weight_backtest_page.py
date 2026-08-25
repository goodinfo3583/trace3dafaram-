# views/weight_backtest_page.py
import streamlit as st
import pandas as pd
import re

# ==========================================
# 🌟 導入背景喚醒引擎：確保未點擊頁面時也能抓到原始大數據
# ==========================================
try:
    from views.sidebar import ensure_b1_to_b5_loaded
except ImportError:
    def ensure_b1_to_b5_loaded(DATA_DIR): pass

# ==========================================
# 🌟 萬能鑰匙：對接全站暫存變數 (隱藏開發代號)
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
    """統一清理股票代號格式，確保大數據比對精準"""
    if df.empty: return df
    col_id = '股票代號' if '股票代號' in df.columns else ('代號' if '代號' in df.columns else None)
    if col_id:
        df['統一代號'] = df[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    return df

def show_weight_backtest_page(STOCK_DICT, DATA_DIR="data"):
    # 背景自動載入原始資料，確保資料庫充實
    ensure_b1_to_b5_loaded(DATA_DIR)

    st.markdown("<h2 style='color: #38BDF8;'>⚖️ 策略實驗室：自訂權重與勝率回測</h2>", unsafe_allow_html=True)
    st.caption("打造專屬於您的選股邏輯，透過多重條件交集與大數據計分，找出最具爆發力的潛力股與 ETF。")
    st.write("---")

    # ==========================================
    # 1. 建立候選池 (新增 ETF 納入開關)
    # ==========================================
    st.markdown("#### 0️⃣ 候選池範圍設定")
    include_etf = st.checkbox("🎯 同時納入 ETF 標的 (如 0050、0056、00878 等)", value=True)
    st.write("")

    pool = []
    if STOCK_DICT:
        for v in STOCK_DICT.values():
            sid = str(v["id"])
            ind = v.get("industry", "")
            # 條件：代號長度 4 碼且為純數字
            if len(sid) == 4 and sid.isdigit():
                is_etf = "ETF" in ind or "ETN" in ind or "指數" in ind
                if is_etf and not include_etf:
                    continue  # 如果不包含 ETF 且剛好是 ETF，就跳過
                pool.append({"統一代號": sid, "股票名稱": v["name"], "產業別": ind if ind else "ETF/其他"})
    
    base_df = pd.DataFrame(pool)
    if base_df.empty:
        st.warning("⚠️ 無法載入股票字典檔，請確認系統資料。")
        return

    # ==========================================
    # 2. 嚴格過濾器 (多重條件交集面板)
    # ==========================================
    st.markdown(f"#### 1️⃣ 設定嚴格過濾條件 (目前候選池共 {len(base_df)} 檔)")
    st.caption("您可以同時勾選多個條件。系統會進行「交集 (AND)」篩選，留下的標的才會進入下一關計分。")
    
    filters = {}
    tab1, tab2, tab3 = st.tabs(["📈 法人動向與連續買超", "🐳 大戶與董監動向", "📉 突擊掃貨與資券"])
    
    with tab1:
        st.markdown("**🔹 法人持股動向**")
        c1, c2 = st.columns(2)
        filters['b1_any'] = c1.checkbox("近期有進榜紀錄 (不限天數)")
        filters['b1_delta_pos'] = c2.checkbox("單日 △ 呈現正數上升 (>0)")
        
        st.markdown("**🔹 法人連續買超**")
        c3, c4 = st.columns(2)
        filters['b3_foreign'] = c3.checkbox("外資連續買超 (>0天)")
        filters['b3_trust'] = c4.checkbox("投信連續買超 (>0天)")
        
    with tab2:
        st.markdown("**🔹 大戶籌碼共振 (註：通常 ETF 無此數據)**")
        c5, c6 = st.columns(2)
        filters['b5_1000'] = c5.checkbox("千張大戶持股增加")
        filters['b5_resonance'] = c6.checkbox("大戶長短線共振 (400與1000張同增)")
        
        st.markdown("**🔹 內部人防線**")
        filters['b7_pledge'] = c7.checkbox("董監持股增加 或 質押減少") if 'c7' in locals() else st.checkbox("董監持股增加 或 質押減少", key="b7_pledge_chk")

    with tab3:
        st.markdown("**🔹 突擊掃貨 (買超佔比)**")
        filters['b2_any'] = st.checkbox("外資或投信買超佔比進榜 (佔成交/發行量)")
        
        st.markdown("**🔹 軋空與融資變化**")
        filters['b4_short'] = st.checkbox("借券餘額減少 (具備潛在軋空動能)")

    # 執行交集過濾邏輯
    filtered_df = base_df.copy()
    
    if filters['b1_any']:
        df = clean_stock_id(get_df('b1_final_df'))
        if not df.empty:
            filtered_df = filtered_df[filtered_df['統一代號'].isin(df['統一代號'])]
            
    if filters['b1_delta_pos']:
        df = clean_stock_id(get_df('b1_final_df'))
        if not df.empty and '△' in df.columns:
            df['num_delta'] = pd.to_numeric(df['△'].astype(str).str.replace('%', '').str.replace('+', ''), errors='coerce').fillna(0)
            hit = df[df['num_delta'] > 0]['統一代號']
            filtered_df = filtered_df[filtered_df['統一代號'].isin(hit)]
            
    if filters['b3_foreign']:
        df = clean_stock_id(get_df('b3_main'))
        if not df.empty:
            cols = [c for c in df.columns if '外資' in str(c) and '買' in str(c)]
            if cols:
                df['n_buy'] = pd.to_numeric(df[cols[0]].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
                hit = df[df['n_buy'] > 0]['統一代號']
                filtered_df = filtered_df[filtered_df['統一代號'].isin(hit)]
                
    if filters['b3_trust']:
        df = clean_stock_id(get_df('b3_main'))
        if not df.empty:
            cols = [c for c in df.columns if '投信' in str(c) and '買' in str(c)]
            if cols:
                df['n_buy'] = pd.to_numeric(df[cols[0]].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
                hit = df[df['n_buy'] > 0]['統一代號']
                filtered_df = filtered_df[filtered_df['統一代號'].isin(hit)]
                
    if filters['b5_1000']:
        df = clean_stock_id(get_df('b5_1000'))
        if not df.empty: filtered_df = filtered_df[filtered_df['統一代號'].isin(df['統一代號'])]
        
    if filters['b5_resonance']:
        df = clean_stock_id(get_df('b5_resonance'))
        if not df.empty: filtered_df = filtered_df[filtered_df['統一代號'].isin(df['統一代號'])]

    if filters['b7_pledge']:
        df = clean_stock_id(get_df('b7_main'))
        if not df.empty: filtered_df = filtered_df[filtered_df['統一代號'].isin(df['統一代號'])]
        
    if filters['b2_any']:
        combined = pd.concat([clean_stock_id(get_df(k)) for k in ['b2_1', 'b2_2', 'b2_3', 'b2_4']])
        if not combined.empty:
            filtered_df = filtered_df[filtered_df['統一代號'].isin(combined['統一代號'].unique())]
            
    if filters['b4_short']:
        combined = pd.concat([clean_stock_id(get_df('b4_short_pct')), clean_stock_id(get_df('b4_short_vol'))])
        if not combined.empty:
            filtered_df = filtered_df[filtered_df['統一代號'].isin(combined['統一代號'].unique())]

    st.success(f"✅ 過濾完成！共有 **{len(filtered_df)}** 檔標的 (含個股與勾選的ETF) 符合您的條件，準備進入計分。")
    st.write("---")

    # ==========================================
    # 3. 自訂權重面板 (Weight Configuration)
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
    # 4. 執行計分運算 (Scoring Engine)
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

            # --- 套用計分 ---
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
            # 5. 結果展示
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
