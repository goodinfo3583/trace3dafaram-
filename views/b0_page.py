# views/b0_page.py
import streamlit as st
import pandas as pd
import os
import glob
import re

# ==========================================
# 🌟 數據潔癖最終版：嚴格檔名過濾 + 強制數值轉換 + 防禦空值覆蓋
# (完全繼承您的嚴謹邏輯，作為 B0 專屬背景引擎)
# ==========================================
def sync_b0_data(DATA_DIR):
    # 🎯 防線 1：絕對嚴格鎖定「成交價」三個字，阻絕其他籌碼檔案干擾
    search_patterns = [os.path.join(DATA_DIR, "*成交價*.csv")]
    files = []
    for pattern in search_patterns:
        files.extend(glob.glob(pattern))
    
    if not files:
        print("⚠️ [B0引擎] 找不到任何成交價 CSV 檔案。")
        return
    
    all_dfs = []
    # 步驟 1：讀取並以「日期」定錨
    for f in files:
        df = None 
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                # 🎯 防線 2：統一先用字串讀取，避免 Pandas 被千分位逗號干擾
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
                    
                # 確保 PER、成交價、漲跌幅 被正確轉換
                if 'PER' in df.columns:
                    df['PER'] = pd.to_numeric(df['PER'].astype(str).str.replace(',', ''), errors='coerce')
                if '成交' in df.columns:
                    df['成交'] = pd.to_numeric(df['成交'].astype(str).str.replace(',', ''), errors='coerce')
                if '漲跌幅' in df.columns:
                    df['漲跌幅'] = pd.to_numeric(df['漲跌幅'].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce')

                all_dfs.append(df)
                
    if not all_dfs: return
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 🎯 防線 4：強者生存去重法！同一天若有多筆資料，優先保留「成交張數最大」的那筆
    combined_df = combined_df.sort_values(by=['統一代號', '標準日期', '成交張數_num'], ascending=[True, True, False])
    combined_df = combined_df.drop_duplicates(subset=['統一代號', '標準日期'], keep='first')
    
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
    
    # 存入 Session State 供全站使用
    st.session_state['b0_price'] = df_today


# ==========================================
# 🌟 頁面渲染主程式
# ==========================================
def show_b0_page(DATA_DIR, STOCK_DICT):
    # 確保 B0 數據已載入記憶體
    if 'b0_price' not in st.session_state:
        with st.spinner("🚀 B0 基礎價量引擎啟動中..."):
            sync_b0_data(DATA_DIR)
            
    df_b0 = st.session_state.get('b0_price', pd.DataFrame())
    
    if df_b0.empty:
        st.warning("⚠️ 目前資料庫中無任何有效的成交價檔案，請確認 `data` 資料夾狀態。")
        return

    # 取得最新日期 (美化顯示)
    date_raw = str(df_b0['股價日期'].iloc[0])
    b0_latest_date_str = date_raw
    if len(date_raw) >= 8:
        b0_latest_date_str = f"{date_raw[:4]}/{date_raw[4:6]}/{date_raw[6:8]}"
    elif len(date_raw) == 4: # 處理可能只有 0828 的情況
        b0_latest_date_str = f"2026/{date_raw[:2]}/{date_raw[2:]}"

    # UI 標題
    st.markdown("<h2 style='color: #38BDF8;'>⚖️ B0 基礎量價與估值掃描</h2>", unsafe_allow_html=True)
    st.caption(f"資料基準日: **{b0_latest_date_str}** ｜ 透視全市場資金動能與主力控盤狀態。")
    st.write("---")
    
    # 🎯 映射股票名稱
    if '股票名稱' not in df_b0.columns:
        def get_stock_name(code):
            return STOCK_DICT.get(str(code), {}).get("name", "") if STOCK_DICT else ""
        df_b0.insert(1, '股票名稱', df_b0['統一代號'].apply(get_stock_name))

    # ==========================================
    # 🕵️‍♂️ 頁面專屬過濾器
    # ==========================================
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_kw = st.text_input("🔍 搜尋代號/名稱", placeholder="例如: 2330 或 台積電")
    with col2:
        vol_filter = st.number_input("📈 成交量大於 (張)", min_value=0, value=0, step=1000)
    with col3:
        status_options = sorted(df_b0['B0_量價狀態'].unique().tolist())
        sel_status = st.multiselect("🎯 過濾量價型態", status_options, placeholder="預設顯示全部")

    # 執行過濾
    view_df = df_b0.copy()
    if search_kw:
        view_df = view_df[view_df['統一代號'].str.contains(search_kw) | view_df['股票名稱'].str.contains(search_kw)]
    if vol_filter > 0:
        view_df = view_df[view_df['成交張數_num'] >= vol_filter]
    if sel_status:
        view_df = view_df[view_df['B0_量價狀態'].isin(sel_status)]

    # 篩選要顯示的完美欄位
    display_cols = ['統一代號', '股票名稱', '成交', '漲跌幅', '成交張數', '成交額(百萬)', 'PER', '5日均量', '5日均額', 'B0_量價狀態']
    view_df = view_df[[c for c in display_cols if c in view_df.columns]].copy()

    # ==========================================
    # 📊 渲染數據表 (使用潔癖級別的對齊與顏色)
    # ==========================================
    st.markdown(f"**共找到 {len(view_df)} 檔符合條件的標的**")
    
    st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "統一代號": st.column_config.TextColumn("代號", width="small"),
            "股票名稱": st.column_config.TextColumn("名稱", width="small"),
            "成交": st.column_config.NumberColumn("成交價", format="%.2f"),
            "漲跌幅": st.column_config.NumberColumn(
                "漲跌幅(%)", 
                format="%.2f",
                # 用顏色標示漲跌
                help="紅色為漲，綠色為跌 (依台股習慣)"
            ),
            "成交張數": st.column_config.NumberColumn("今日成交(張)", format="%d"),
            "5日均量": st.column_config.NumberColumn("5日均量(張)", format="%d"),
            "成交額(百萬)": st.column_config.NumberColumn("成交額(百萬)", format="%.2f"),
            "5日均額": st.column_config.NumberColumn("5日均成交額(百萬)", format="%.2f"),
            "PER": st.column_config.NumberColumn("本益比", format="%.2f"),
            "B0_量價狀態": st.column_config.TextColumn("量價主力照妖鏡", width="large"),
        }
    )
