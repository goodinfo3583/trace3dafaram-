# views/weight_backtest_page.py
import streamlit as st
import pandas as pd
import re

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
    # 🟢 幫您預留大戶共振與雙向共振的變數，若您的 B5 頁面變數名稱不同，可在此修改
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

def show_weight_backtest_page(STOCK_DICT):
    st.markdown("<h2 style='color: #38BDF8;'>⚖️ 策略實驗室：自訂權重與勝率回測</h2>", unsafe_allow_html=True)
    st.caption("打造專屬於您的選股邏輯，透過大數據運算找出最具爆發力的潛力股。")
    st.write("---")

    # ==========================================
    # 1. 基底選擇 (Base Universe)
    # ==========================================
    st.markdown("#### 1️⃣ 選擇選股池基底 (Base)")
    st.caption("基底是策略的「第一道濾網」。決定了有哪些標的具備被計分的資格。")
    
    base_options = [
        "🌍 全市場掃描 (上市櫃全納入)",
        "📈 法人動向：單日 △ 增加 (極短線強勢)",
        "📈 法人動向：波段歷史進榜 (趨勢成型)",
        "🚀 突擊掃貨：外資買超佔比進榜",
        "🚀 突擊掃貨：投信買超佔比進榜",
        "🔥 連續買超：外資連買標的",
        "🔥 連續買超：投信連買標的",
        "🐳 大戶動向：千張大戶持股增加",
        "🎯 大戶動向：長短線共振 / 雙向共振",
        "📉 資券變化：借券餘額減少 (軋空潛力)"
    ]
    base_option = st.selectbox("請選擇第一關過濾條件：", base_options)

    # 建立候選池 Base DataFrame
    base_df = pd.DataFrame()
    
    if base_option == "🌍 全市場掃描 (上市櫃全納入)":
        if STOCK_DICT:
            base_df = pd.DataFrame([{"統一代號": str(v["id"]), "股票名稱": v["name"], "產業別": v.get("industry", "未分類")} for v in STOCK_DICT.values() if len(str(v["id"])) <= 4])
            
    elif base_option == "📈 法人動向：單日 △ 增加 (極短線強勢)":
        df = clean_stock_id(get_df('b1_final_df'))
        if not df.empty and '△' in df.columns:
            # 轉換 △ 為數字並過濾 > 0
            df['num_delta'] = pd.to_numeric(df['△'].astype(str).str.replace('%', '').str.replace('+', ''), errors='coerce').fillna(0)
            base_df = df[df['num_delta'] > 0][['統一代號', '股票名稱']].drop_duplicates()
            
    elif base_option == "📈 法人動向：波段歷史進榜 (趨勢成型)":
        df = clean_stock_id(get_df('b1_final_df'))
        if not df.empty: base_df = df[['統一代號', '股票名稱']].drop_duplicates()
            
    elif base_option == "🚀 突擊掃貨：外資買超佔比進榜":
        df1 = clean_stock_id(get_df('b2_1')) # 外資佔成交
        df3 = clean_stock_id(get_df('b2_3')) # 外資佔發行
        combined = pd.concat([df1, df3]).drop_duplicates(subset=['統一代號']) if not df1.empty or not df3.empty else pd.DataFrame()
        if not combined.empty: base_df = combined[['統一代號', '股票名稱']]
            
    elif base_option == "🚀 突擊掃貨：投信買超佔比進榜":
        df2 = clean_stock_id(get_df('b2_2')) # 投信佔成交
        df4 = clean_stock_id(get_df('b2_4')) # 投信佔發行
        combined = pd.concat([df2, df4]).drop_duplicates(subset=['統一代號']) if not df2.empty or not df4.empty else pd.DataFrame()
        if not combined.empty: base_df = combined[['統一代號', '股票名稱']]

    elif base_option == "🔥 連續買超：外資連買標的":
        df = clean_stock_id(get_df('b3_main'))
        if not df.empty:
            # 尋找含有「外資」及「連買」的欄位
            target_cols = [c for c in df.columns if '外資' in str(c) and '買' in str(c)]
            if target_cols:
                df['num_buy'] = pd.to_numeric(df[target_cols[0]].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
                base_df = df[df['num_buy'] > 0][['統一代號', '股票名稱']].drop_duplicates()

    elif base_option == "🔥 連續買超：投信連買標的":
        df = clean_stock_id(get_df('b3_main'))
        if not df.empty:
            target_cols = [c for c in df.columns if '投信' in str(c) and '買' in str(c)]
            if target_cols:
                df['num_buy'] = pd.to_numeric(df[target_cols[0]].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
                base_df = df[df['num_buy'] > 0][['統一代號', '股票名稱']].drop_duplicates()
                
    elif base_option == "🐳 大戶動向：千張大戶持股增加":
        df = clean_stock_id(get_df('b5_1000'))
        if not df.empty: base_df = df[['統一代號', '股票名稱']].drop_duplicates()
        
    elif base_option == "🎯 大戶動向：長短線共振 / 雙向共振":
        df_res = clean_stock_id(get_df('b5_resonance'))
        df_dbl = clean_stock_id(get_df('b5_double'))
        combined = pd.concat([df_res, df_dbl]).drop_duplicates(subset=['統一代號']) if not df_res.empty or not df_dbl.empty else pd.DataFrame()
        if not combined.empty: 
            base_df = combined[['統一代號', '股票名稱']]
        else:
            st.error("⚠️ 尚未抓取到『共振』相關的資料表。請確認您已在系統中載入過大戶頁面，或資料庫名稱已正確對應。")
            
    elif base_option == "📉 資券變化：借券餘額減少 (軋空潛力)":
        df1 = clean_stock_id(get_df('b4_short_pct'))
        df2 = clean_stock_id(get_df('b4_short_vol'))
        combined = pd.concat([df1, df2]).drop_duplicates(subset=['統一代號']) if not df1.empty or not df2.empty else pd.DataFrame()
        if not combined.empty: base_df = combined[['統一代號', '股票名稱']]

    if base_df.empty:
        st.warning("⚠️ 該基底目前無資料。請先點擊側邊欄搜尋，或至各對應頁面載入最新大數據。")
        return

    st.success(f"✅ 已鎖定候選池：共 **{len(base_df)}** 檔標的準備進行計分。")
    st.write("")

    # ==========================================
    # 2. 自訂權重面板 (Weight Configuration)
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
            
            # 初始化分數欄位
            base_df['總分'] = 0.0
            base_df['得分明細'] = ""

            def apply_score(target_df_key, weight, rule_name):
                df = clean_stock_id(get_df(target_df_key))
                if df.empty or weight == 0: return
                
                # 找出有進榜的股票代號
                hit_codes = df['統一代號'].unique()
                mask = base_df['統一代號'].isin(hit_codes)
                
                base_df.loc[mask, '總分'] += weight
                
                sign = "+" if weight > 0 else ""
                detail_str = f"[{rule_name} {sign}{weight}] "
                base_df.loc[mask, '得分明細'] += detail_str

            # --- 開始依序套用各區塊權重 ---
            
            # 法人動向 (計算上榜數量)
            b1_df = clean_stock_id(get_df('b1_final_df'))
            if not b1_df.empty and w_b1_up != 0:
                if '上榜數量' in b1_df.columns:
                    for _, row in b1_df.iterrows():
                        cnt = int(row['上榜數量']) if pd.notna(row['上榜數量']) else 0
                        if cnt > 0:
                            mask = base_df['統一代號'] == row['統一代號']
                            base_df.loc[mask, '總分'] += (w_b1_up * cnt)
                            base_df.loc[mask, '得分明細'] += f"[法人正向{cnt}次 +{w_b1_up * cnt}] "

            apply_score('b1_down_final_df', w_b1_down, "法人衰退")
            
            # 法人突擊掃貨 (四個榜單)
            for k in ['b2_1', 'b2_2', 'b2_3', 'b2_4']:
                apply_score(k, w_b2, "法人掃貨")
                
            # 法人連續買超
            apply_score('b3_main', w_b3, "法人連買")
            
            # 資券有利榜單
            for k in ['b4_margin_pct', 'b4_short_pct', 'b4_margin_plus_pct', 'b4_margin_vol', 'b4_short_vol', 'b4_margin_plus_vol']:
                apply_score(k, w_b4_good, "資券有利")
                
            # 千張大戶
            apply_score('b5_1000', w_b5, "千張大戶")
            
            # 董監動向
            apply_score('b7_main', w_b7, "董監增持")

            # ==========================================
            # 4. 結果展示
            # ==========================================
            base_df = base_df.sort_values(by='總分', ascending=False).reset_index(drop=True)
            result_df = base_df[base_df['總分'] != 0].copy()

            st.write("---")
            st.markdown(f"### 🏆 策略計分結果 (共 {len(result_df)} 檔獲取分數)")
            
            if not result_df.empty:
                # 幫分數加上顏色
                def highlight_score(val):
                    if val >= 5: return 'color: #FF4B4B; font-weight: bold'
                    elif val > 0: return 'color: #38BDF8'
                    elif val < 0: return 'color: #00E676'
                    return ''
                
                display_df = result_df[['統一代號', '股票名稱', '總分', '得分明細']].rename(columns={'統一代號': '股票代號'})
                st.dataframe(
                    display_df.style.map(highlight_score, subset=['總分']), 
                    use_container_width=True,
                    hide_index=True
                )
                
                st.info("💡 **未來回測擴充方向**：目前的結果是基於『今日最新數據』的計分。未來當您的 `History_Archive` 累積足夠的歷史 CSV 後，系統即可回到過去每一天執行此策略，驗證 T+5、T+20 日的真實上漲勝率！")
            else:
                st.warning("沒有標的符合您的計分條件。")
