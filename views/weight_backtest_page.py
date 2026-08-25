# views/weight_backtest_page.py
import streamlit as st
import pandas as pd

# 引入萬能鑰匙 (對應 sidebar 的設定)
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
    """統一清理股票代號格式"""
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
    base_option = st.selectbox(
        "請選擇第一關過濾條件 (只有符合此條件的標的才會進行後續計分)：",
        ["全市場掃描 (上市櫃全納入)", "只看 B1 籌碼正向進榜", "只看 B5 千張大戶增持", "只看 B3 法人連續買超"]
    )

    # 建立候選池 Base DataFrame
    base_df = pd.DataFrame()
    if base_option == "全市場掃描 (上市櫃全納入)":
        if STOCK_DICT:
            base_df = pd.DataFrame([{"統一代號": str(v["id"]), "股票名稱": v["name"], "產業別": v.get("industry", "未分類")} for v in STOCK_DICT.values() if len(str(v["id"])) <= 4])
    elif base_option == "只看 B1 籌碼正向進榜":
        b1_df = clean_stock_id(get_df('b1_final_df'))
        if not b1_df.empty: base_df = b1_df[['統一代號', '股票名稱']].drop_duplicates()
    elif base_option == "只看 B5 千張大戶增持":
        b5_df = clean_stock_id(get_df('b5_1000'))
        if not b5_df.empty: base_df = b5_df[['統一代號', '股票名稱']].drop_duplicates()
    elif base_option == "只看 B3 法人連續買超":
        b3_df = clean_stock_id(get_df('b3_main'))
        if not b3_df.empty: base_df = b3_df[['統一代號', '股票名稱']].drop_duplicates()

    if base_df.empty:
        st.warning("⚠️ 尚未載入該基底的資料表，請先點擊側邊欄搜尋或在觀察名單執行「全市場掃描」。")
        return

    st.success(f"✅ 已鎖定候選池：共 **{len(base_df)}** 檔標的準備進行計分。")
    st.write("")

    # ==========================================
    # 2. 自訂權重面板 (Weight Configuration)
    # ==========================================
    st.markdown("#### 2️⃣ 設定計分權重 (Weights)")
    st.caption("請為各區塊設定加權分數 (設定為 0 代表不計分，負數代表扣分)")
    
    with st.expander("⚙️ 展開設定各區塊權重", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown("**B1 法人動向**")
            w_b1_up = st.number_input("B1 正向進榜 (次)", value=1.0, step=0.5)
            w_b1_down = st.number_input("B1 衰退進榜 (次)", value=-1.0, step=0.5)
            
        with c2:
            st.markdown("**B2/B3 籌碼集中**")
            w_b2 = st.number_input("B2 法人掃貨 (榜)", value=1.5, step=0.5)
            w_b3 = st.number_input("B3 法人連買 (榜)", value=2.0, step=0.5)
            
        with c3:
            st.markdown("**B4 資券變化**")
            w_b4_good = st.number_input("融資減/券增 (有利)", value=1.0, step=0.5)
            
        with c4:
            st.markdown("**B5/B7 大戶與董監**")
            w_b5 = st.number_input("B5 千張大戶增", value=3.0, step=0.5)
            w_b7 = st.number_input("B7 董監增/質押降", value=1.5, step=0.5)

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
                
                # 紀錄明細 (如果有加減分的話)
                sign = "+" if weight > 0 else ""
                detail_str = f"[{rule_name} {sign}{weight}] "
                base_df.loc[mask, '得分明細'] += detail_str

            # --- 開始依序套用各區塊權重 ---
            
            # B1 區塊 (計算上榜數量)
            b1_df = clean_stock_id(get_df('b1_final_df'))
            if not b1_df.empty and w_b1_up != 0:
                if '上榜數量' in b1_df.columns:
                    for _, row in b1_df.iterrows():
                        cnt = int(row['上榜數量']) if pd.notna(row['上榜數量']) else 0
                        if cnt > 0:
                            mask = base_df['統一代號'] == row['統一代號']
                            base_df.loc[mask, '總分'] += (w_b1_up * cnt)
                            base_df.loc[mask, '得分明細'] += f"[B1上榜{cnt}次 +{w_b1_up * cnt}] "

            apply_score('b1_down_final_df', w_b1_down, "B1衰退")
            
            # B2 區塊 (四個榜單)
            for k in ['b2_1', 'b2_2', 'b2_3', 'b2_4']:
                apply_score(k, w_b2, "B2掃貨")
                
            # B3 區塊
            apply_score('b3_main', w_b3, "B3連買")
            
            # B4 區塊 (對多頭有利的榜單)
            for k in ['b4_margin_pct', 'b4_short_pct', 'b4_margin_plus_pct', 'b4_margin_vol', 'b4_short_vol', 'b4_margin_plus_vol']:
                apply_score(k, w_b4_good, "B4券資有利")
                
            # B5 區塊
            apply_score('b5_1000', w_b5, "B5千張大戶")
            
            # B7 區塊
            apply_score('b7_main', w_b7, "B7董監增")

            # ==========================================
            # 4. 結果展示
            # ==========================================
            base_df = base_df.sort_values(by='總分', ascending=False).reset_index(drop=True)
            
            # 過濾掉 0 分的標的 (如果使用者想看)
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
                
                # 調整欄位顯示名稱
                display_df = result_df[['統一代號', '股票名稱', '總分', '得分明細']].rename(columns={'統一代號': '股票代號'})
                st.dataframe(
                    display_df.style.applymap(highlight_score, subset=['總分']), 
                    use_container_width=True,
                    hide_index=True
                )
                
                st.info("💡 **未來回測擴充方向**：目前的結果是基於『今日最新數據』的計分。未來當您的 `History_Archive` 累積足夠的歷史 CSV 後，我們可以寫一支迴圈，讓系統回到過去每一天執行這個策略，並計算 T+5、T+20 日的真實上漲勝率！")
            else:
                st.warning("沒有標的符合您的計分條件。")
