# views/b0_page.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import re

# ==========================================
# 🌟 數據潔癖最終版：嚴格檔名過濾 + 強制數值轉換 + 防禦空值覆蓋
# ==========================================
def sync_b0_data(DATA_DIR):
    search_patterns = [os.path.join(DATA_DIR, "*成交價*.csv")]
    files = []
    for pattern in search_patterns:
        files.extend(glob.glob(pattern))
    
    if not files:
        print("⚠️ [B0引擎] 找不到任何成交價 CSV 檔案。")
        return
    
    all_dfs = []
    for f in files:
        df = None 
        for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                df = pd.read_csv(f, encoding=enc, header=0, dtype=str)
                break
            except: pass
            
        if df is not None and not df.empty:
            # 清除欄位名稱的隱藏空白
            df.columns = [re.sub(r'[\s\n\r\t\u3000\ufeff]+', '', str(c)) for c in df.columns]
            
            c_code = next((c for c in df.columns if '代號' in c), None)
            date_col = next((c for c in df.columns if '日期' in c), None)
            
            # 🎯 直接在原始 CSV 中抓取名稱欄位 (可能是名稱、股票名稱、證券名稱)
            name_col = next((c for c in df.columns if c in ['名稱', '股票名稱', '證券名稱']), None)
            
            if c_code and date_col:
                df['統一代號'] = df[c_code].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df['標準日期'] = df[date_col].astype(str).str.strip()
                
                # 🎯 保留原始 CSV 中的名稱，不再讓它被洗掉
                if name_col:
                    df['B0_原始名稱'] = df[name_col].astype(str).str.strip()
                else:
                    df['B0_原始名稱'] = ""
                
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
                    
                if 'PER' in df.columns:
                    df['PER'] = pd.to_numeric(df['PER'].astype(str).str.replace(',', ''), errors='coerce')
                if '成交' in df.columns:
                    df['成交'] = pd.to_numeric(df['成交'].astype(str).str.replace(',', ''), errors='coerce')
                if '漲跌幅' in df.columns:
                    df['漲跌幅'] = pd.to_numeric(df['漲跌幅'].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce')

                all_dfs.append(df)
                
    if not all_dfs: return
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 依成交張數排序去重，確保不被空資料蓋掉
    combined_df = combined_df.sort_values(by=['統一代號', '標準日期', '成交張數_num'], ascending=[True, True, False])
    combined_df = combined_df.drop_duplicates(subset=['統一代號', '標準日期'], keep='first')
    
    unique_dates = sorted(combined_df['標準日期'].unique(), reverse=True)
    if not unique_dates: return
    latest_date = unique_dates[0]
    
    df_today = combined_df[combined_df['標準日期'] == latest_date].copy()
    # === 此段程式碼運算不同期程的成交額平均值 ===
    sorted_df = combined_df.sort_values(by=['統一代號', '標準日期'], ascending=[True, False])
    
    # 🎯 擴充：計算多週期均額 (5, 10, 20, 30, 45日)
    avg_dict = {}
    periods = [5, 10, 20, 30, 45]
    
    for p in periods:
        top_p_df = sorted_df.groupby('統一代號').head(p)
        p_avg = top_p_df.groupby('統一代號').agg(
            **{
                f'{p}日均量': ('成交張數_num', 'mean'),
                f'{p}日均額': ('成交額_num', 'mean')
            }
        ).reset_index()
        # 逐一合併進 df_today
        df_today = pd.merge(df_today, p_avg, on='統一代號', how='left')
        
        # 四捨五入美化
        df_today[f'{p}日均量'] = df_today[f'{p}日均量'].round(0)
        df_today[f'{p}日均額'] = df_today[f'{p}日均額'].round(2)

    df_today['股價日期'] = latest_date
    # === 替換結束，下方接著 def get_vp_status(row): ===
    # 🎯 新增：取得上一交易日(昨日)的成交額，並計算「成交金額日變化率」
    # .nth(1) 代表在時間倒序中抓取第二筆 (即昨天) 的資料
    prev_day_df = sorted_df.groupby('統一代號').nth(1).reset_index()
    prev_day_df = prev_day_df[['統一代號', '成交額_num']].rename(columns={'成交額_num': '昨日成交額'})
    
    # 併入今日 dataframe
    df_today = pd.merge(df_today, prev_day_df, on='統一代號', how='left')
        
    # 避免除以 0 導致無限大，將昨日為 0 或 NaN 的防呆設為極小值 0.01
    safe_prev_amt = df_today['昨日成交額'].replace(0, 0.01).fillna(0.01)
    # 邏輯：(今日成交金額 ÷ 昨日成交金額 - 1) * 100，轉換為百分比格式
    df_today['成交金額日變化率'] = ((df_today['成交額_num'] / safe_prev_amt) - 1) * 100  

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
# 🌟 頁面渲染主程式
# ==========================================
def show_b0_page(DATA_DIR, STOCK_DICT):
    if 'b0_price' not in st.session_state:
        with st.spinner("🚀 基礎價量引擎啟動中..."):
            sync_b0_data(DATA_DIR)
            
    df_b0 = st.session_state.get('b0_price', pd.DataFrame())
    
    if df_b0.empty:
        st.warning("⚠️ 目前資料庫中無任何有效的成交價檔案，請確認 `data` 資料夾狀態。")
        return

    # 取得最新日期
    date_raw = str(df_b0['股價日期'].iloc[0])
    b0_latest_date_str = date_raw
    if len(date_raw) >= 8:
        b0_latest_date_str = f"{date_raw[:4]}/{date_raw[4:6]}/{date_raw[6:8]}"
    elif len(date_raw) == 4:
        b0_latest_date_str = f"2026/{date_raw[:2]}/{date_raw[2:]}"

    st.markdown("<h2 style='color: #38BDF8;'>量價與估值掃描</h2>", unsafe_allow_html=True)
    st.caption(f"資料基準日: **{b0_latest_date_str}** ｜ 透視全市場資金動能與主力控盤狀態。")
    st.write("---")
    
    # 🎯 完美解法：優先讀取 CSV 內的名稱，防禦 00400A 等新標的名稱遺失
    def resolve_stock_name(row):
        # 1. 優先拿原始 CSV 的名稱
        raw_name = str(row.get('B0_原始名稱', '')).strip()
        if raw_name and raw_name.lower() != 'nan' and raw_name != 'none':
            return raw_name
            
        # 2. 如果 CSV 真的漏了，才拿 STOCK_DICT 補底
        code = str(row.get('統一代號', ''))
        if STOCK_DICT:
            dict_name = STOCK_DICT.get(code, {}).get("name", "")
            if dict_name: 
                return dict_name
                
        return ""
        
    df_b0['股票名稱'] = df_b0.apply(resolve_stock_name, axis=1)

    # ==========================================
    # 🎛️ 全域篩選器 (置於 Tab 之上，讓所有分頁共享)
    # ==========================================
    with st.expander("🛠️ 全域條件篩選 (點擊展開/收合)", expanded=True):
        col1, col2, col3, col4 = st.columns([1.5, 1, 1.5, 1])
        with col1:
            search_kw = st.text_input("🔍 搜尋代號/名稱", placeholder="例如: 2330 或 台積電")
        with col2:
            vol_filter = st.number_input("成交量 > (張)", min_value=0, value=0, step=1000)
        with col3:
            status_options = sorted(df_b0['B0_量價狀態'].unique().tolist())
            sel_status = st.multiselect("🎯 狀態過濾", status_options, placeholder="預設全選")
        with col4:
            # 🎯 新增 PER 篩選
            per_options = ["全部顯示", "PER < 15 (低估值)", "PER < 30 (合理)", "僅顯示獲利公司 (PER>0)"]
            sel_per = st.selectbox("⚖️ 估值(PER)過濾", per_options)

    # 執行全域過濾邏輯
    filtered_df = df_b0.copy()
    if search_kw:
        filtered_df = filtered_df[filtered_df['統一代號'].str.contains(search_kw) | filtered_df['股票名稱'].str.contains(search_kw)]
    if vol_filter > 0:
        filtered_df = filtered_df[filtered_df['成交張數_num'] >= vol_filter]
    if sel_status:
        filtered_df = filtered_df[filtered_df['B0_量價狀態'].isin(sel_status)]
    
    # 執行 PER 過濾
    if sel_per == "PER < 15 (低估值)":
        filtered_df = filtered_df[(filtered_df['PER'] > 0) & (filtered_df['PER'] < 15)]
    elif sel_per == "PER < 30 (合理)":
        filtered_df = filtered_df[(filtered_df['PER'] > 0) & (filtered_df['PER'] < 30)]
    elif sel_per == "僅顯示獲利公司 (PER>0)":
        filtered_df = filtered_df[filtered_df['PER'] > 0]

    # ==========================================
    # 🗂️ 建立雙分頁 (Tabs)
    # ==========================================
    tab_basic, tab_momentum = st.tabs(["🔹 全市場基礎量價", "🔹 資金動能雷達"])

    # ------------------------------------------
    # 分頁 1：基礎量價總表
    # ------------------------------------------
    with tab_basic:
        display_cols = ['統一代號', '股票名稱', '成交', '漲跌幅', '成交張數', '成交額(百萬)', '成交金額日變化率', 'PER', '5日均量', '5日均額', 'B0_量價狀態']
        view_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()

        st.markdown(f"**共找到 {len(view_df)} 檔符合條件的標的**")
        
        # 🎯 乾淨還原版：不套用任何特殊 Style，讓缺失的 PER 統一顯示為預設的 None
        st.dataframe(
            view_df,
            use_container_width=True, hide_index=True, height=500,
            column_config={
                "統一代號": st.column_config.TextColumn("代號", width="small"),
                "股票名稱": st.column_config.TextColumn("名稱", width="small"),
                "成交": st.column_config.NumberColumn("成交價", format="%.2f"),
                "漲跌幅": st.column_config.NumberColumn("漲跌幅(%)", format="%.2f"),
                "成交張數": st.column_config.NumberColumn("今日成交(張)", format="%d"),
                "5日均量": st.column_config.NumberColumn("5日均量(張)", format="%d"),
                "成交額(百萬)": st.column_config.NumberColumn("成交額(百萬)", format="%.2f"),
                "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                "5日均額": st.column_config.NumberColumn("5日均成交額(百萬)", format="%.2f"),
                
                # 恢復為原本的 NumberColumn 設定，Streamlit 會自動將 NaN 顯示為 None
                "PER": st.column_config.NumberColumn("本益比", format="%.2f"),
                
                "B0_量價狀態": st.column_config.TextColumn("量價主力照妖鏡", width="large"),
            }
        )

    # === 替換 `with tab_momentum:` 區塊內的所有內容 ===
    with tab_momentum:
        st.markdown("#### 資金動力渦輪：找出真正的行情燃料")
        st.caption("本區塊先行排除流動性太差的標的 (成交額 > 5000萬 且 股價 > 10元)，以避免倍數失真，本表至8/12開始更新30日.45日還不準確。")

        # 1. 核心動能運算 (改吃過濾後的 filtered_df，讓上方篩選器連動生效)
        # 🎯 優化基期門檻：除了今日成交額 > 50 之外，要求 '5日均額' 至少 > 10，避免抓到無意義的殭屍股爆發
        momentum_df = filtered_df[
            (filtered_df['成交額(百萬)'] > 50) & 
            (filtered_df['成交'] > 10) &
            (filtered_df.get('5日均額', 0) > 10) # 新增防呆門檻
        ].copy()
        
        # A. 絕對值增量 (找出巨鯨)
        momentum_df['額度增加絕對值'] = momentum_df['成交額(百萬)'] - momentum_df['5日均額']
        
        # ==========================================
        # 🎯 雙榜單多週期進化版：絕對增額 (熱門焦點) & 爆發倍數 (異常點火)
        # ==========================================
        st.markdown("---")
        st.markdown("##### 🏆 成交額大熱鍋(各週期暴增倍數8/12起算)")
        st.caption("市場資金總量增加最多，代表用錢和量砸出來的活絡程度，也可看族群性 (主升段發動或大型法人調倉，已排除流動性過差標的，也不看籌碼流向何處)")
        
        periods = [5, 10, 20, 30, 45]
        
        # 🎯 先把所有週期的「絕對增加金額」都算出來
        for p in periods:
            avg_col = f'{p}日均額'
            if avg_col in momentum_df.columns:
                momentum_df[f'較{p}日均額增加'] = momentum_df['成交額(百萬)'] - momentum_df[avg_col]
        
        # 建立 🏆 熱門焦點的內部子分頁 (在最前方插入「成交金額增加短中長趨勢」)
        abs_tab_names = ["🔥 成交金額增加短中長趨勢"] + [f"🔹相較 {p} 日均額" for p in periods]
        abs_tabs = st.tabs(abs_tab_names)
        
        # ==========================================
        # 1. 渲染第一個分頁：成交金額增加短中長趨勢 (總表)
        # ==========================================
        with abs_tabs[0]:
            # 依照您指定的順序準備總表的欄位
            summary_cols_abs = ['統一代號', '股票名稱', '成交金額日變化率', '成交額(百萬)']
            summary_col_config_abs = {
                "統一代號": st.column_config.TextColumn("代號"),
                "股票名稱": st.column_config.TextColumn("名稱"),
                "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                "成交額(百萬)": st.column_config.NumberColumn("今日成交額", format="%.0f"),
            }
            
            # 動態將各週期的增加金額加入
            for p in periods:
                if f'較{p}日均額增加' in momentum_df.columns:
                    summary_cols_abs.append(f'較{p}日均額增加')
                    summary_col_config_abs[f'較{p}日均額增加'] = st.column_config.NumberColumn(f"較{p}日增加", format="+%.0f")
            
            # 排序：以 5 日增加金額為基準，抓出前 50 名榜單
            if '較5日均額增加' in momentum_df.columns:
                top_abs_summary = momentum_df.sort_values('較5日均額增加', ascending=False).head(50)
            else:
                top_abs_summary = momentum_df.sort_values('成交額(百萬)', ascending=False).head(50)
                
            st.dataframe(
                top_abs_summary[summary_cols_abs],
                use_container_width=True, hide_index=True, height=500,
                column_config=summary_col_config_abs
            )

        # ==========================================
        # 2. 渲染後續的各單一週期分頁
        # ==========================================
        for idx, p in enumerate(periods):
            # 注意 idx 要 +1，避開總表
            with abs_tabs[idx + 1]:
                avg_col = f'{p}日均額'
                if avg_col in momentum_df.columns:
                    top_abs = momentum_df.sort_values(f'較{p}日均額增加', ascending=False).head(30)
                    
                    display_cols_abs = [
                        '統一代號', 
                        '股票名稱', 
                        f'較{p}日均額增加', 
                        '成交額(百萬)', 
                        avg_col, 
                        '成交金額日變化率', 
                        '漲跌幅'
                    ]
                    
                    st.dataframe(
                        top_abs[display_cols_abs],
                        use_container_width=True, hide_index=True, height=400,
                        column_config={
                            "統一代號": st.column_config.TextColumn("代號"),
                            "股票名稱": st.column_config.TextColumn("名稱"),
                            f'較{p}日均額增加': st.column_config.NumberColumn(f"▲較{p}日均額增加", format="+%.0f"),
                            "成交額(百萬)": st.column_config.NumberColumn("今日成交額", format="%.0f"),
                            avg_col: st.column_config.NumberColumn(f"{p}日均額", format="%.0f"),
                            "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                            "漲跌幅": st.column_config.NumberColumn("漲跌幅%", format="%.2f")
                        }
                    )
                else:
                    st.warning(f"目前資料庫中尚未累積滿 {p} 日的歷史成交資料。")


        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 🚀 點火器 (各週期暴增倍數8/12起算)")
        st.caption("看相較5日均額最敏感，找看看突然異常放量的股票 (可能突破第一根，或波段重新發動，須留意延續性)")
        
        # 🎯 先把所有週期的倍數都算出來，才能在「總表」中一次呼叫使用
        periods = [5, 10, 20, 30, 45]
        for p in periods:
            avg_col = f'{p}日均額'
            if avg_col in momentum_df.columns:
                safe_avg = momentum_df[avg_col].replace(0, 0.01)
                momentum_df[f'{p}日爆發倍數'] = (momentum_df['成交額(百萬)'] / safe_avg).fillna(0)
        
        # 建立 🚀 異常點火的內部子分頁 (在最前方插入「異常點火短中長趨勢」)
        tab_names = ["🔥 異常點火短中長趨勢"] + [f"🔹相較 {p} 日均額" for p in periods]
        ignition_tabs = st.tabs(tab_names)
        
        # ==========================================
        # 1. 渲染第一個分頁：異常點火短中長趨勢 (總表)
        # ==========================================
        with ignition_tabs[0]:
            # 依照您指定的順序準備總表的欄位
            summary_cols = ['統一代號', '股票名稱', '成交金額日變化率', '成交額(百萬)']
            summary_col_config = {
                "統一代號": st.column_config.TextColumn("代號"),
                "股票名稱": st.column_config.TextColumn("名稱"),
                "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                "成交額(百萬)": st.column_config.NumberColumn("今日成交額", format="%.0f"),
            }
            
            # 將算好的各週期倍數動態加入欄位與格式設定中
            for p in periods:
                if f'{p}日爆發倍數' in momentum_df.columns:
                    summary_cols.append(f'{p}日爆發倍數')
                    summary_col_config[f'{p}日爆發倍數'] = st.column_config.NumberColumn(f"{p}日倍數", format="%.1fx")
                    
            # 排序：以 5 日爆發倍數作為預設排名依據，抓出前 50 名榜單
            if '5日爆發倍數' in momentum_df.columns:
                top_summary = momentum_df.sort_values('5日爆發倍數', ascending=False).head(50)
            else:
                top_summary = momentum_df.sort_values('成交額(百萬)', ascending=False).head(50)
                
            st.dataframe(
                top_summary[summary_cols],
                use_container_width=True, hide_index=True, height=500,
                column_config=summary_col_config
            )

        # ==========================================
        # 2. 渲染後續的各單一週期分頁
        # ==========================================
        for idx, p in enumerate(periods):
            # 注意 idx 要 +1，因為 ignition_tabs[0] 已經被總表用掉了
            with ignition_tabs[idx + 1]: 
                if f'{p}日爆發倍數' in momentum_df.columns:
                    top_ratio = momentum_df.sort_values(f'{p}日爆發倍數', ascending=False).head(30)
                    
                    display_cols_ratio = [
                        '統一代號', 
                        '股票名稱', 
                        f'{p}日爆發倍數', 
                        '成交額(百萬)', 
                        f'{p}日均額', 
                        '成交金額日變化率', 
                        '漲跌幅'
                    ]
                    
                    st.dataframe(
                        top_ratio[display_cols_ratio],
                        use_container_width=True, hide_index=True, height=400,
                        column_config={
                            "統一代號": st.column_config.TextColumn("代號"),
                            "股票名稱": st.column_config.TextColumn("名稱"),
                            f'{p}日爆發倍數': st.column_config.NumberColumn("🚀爆發倍數", format="%.1fx"),
                            "成交額(百萬)": st.column_config.NumberColumn("今日成交額", format="%.0f"),
                            f'{p}日均額': st.column_config.NumberColumn(f"{p}日均額", format="%.0f"),
                            "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                            "漲跌幅": st.column_config.NumberColumn("漲跌幅%", format="%.2f")
                        }
                    )
                else:
                    st.warning(f"目前資料庫中尚未累積滿 {p} 日的歷史成交資料。")
        # ------------------------------------------
        # 3. 資金趨勢總表 (均額多頭排列追蹤)
        # ------------------------------------------
        st.markdown("---")
        st.markdown("##### 📈 資金水龍頭看延續性 (各週期暴增倍數8/12起算)")
        st.caption("若是短大於長週期 代表成交金額持續擴張，而不是單日爆量，這裡只看成交金額，不看籌碼流向何處")
        
        # 建立趨勢判斷邏輯
        def get_fund_trend(row):
            try:
                today = float(row.get('成交額(百萬)', 0))
                ma5 = float(row.get('5日均額', 0))
                ma10 = float(row.get('10日均額', 0))
                ma20 = float(row.get('20日均額', 0))
                
                if ma5 > 0 and ma10 > 0 and ma20 > 0:
                    if ma5 > ma10 and ma10 > ma20:
                        return "🔥 資金湧入 (延續性強)"
                    elif today > ma5 and ma5 <= ma10:
                        return "⚡ 單日點火 (需觀察)"
                    elif ma5 < ma10 and ma10 < ma20:
                        return "💧 資金退潮 (動能弱)"
                    else:
                        return "⚖️ 震盪換手"
                return "⚪ 資料不足"
            except:
                return "-"
                
        momentum_df['資金延續趨勢'] = momentum_df.apply(get_fund_trend, axis=1)
        
        # 排序：以今日成交額為主，抓出全市場最具影響力的資金流向 (取前 150 名)
        trend_df = momentum_df.sort_values('成交額(百萬)', ascending=False).head(150)
        
        trend_cols = ['統一代號', '股票名稱', '資金延續趨勢', '成交額(百萬)', '5日均額', '10日均額', '20日均額', '30日均額']
        
        # 防禦機制：確保欄位都有被算出來才顯示
        display_trend_cols = [c for c in trend_cols if c in trend_df.columns]
        
        st.dataframe(
            trend_df[display_trend_cols],
            use_container_width=True, hide_index=True, height=600,
            column_config={
                "統一代號": st.column_config.TextColumn("代號"),
                "股票名稱": st.column_config.TextColumn("名稱"),
                "資金延續趨勢": st.column_config.TextColumn("資金延續狀態", width="medium"),
                "成交額(百萬)": st.column_config.NumberColumn("今日成交", format="%.0f"),
                "5日均額": st.column_config.NumberColumn("5日均", format="%.0f"),
                "10日均額": st.column_config.NumberColumn("10日均", format="%.0f"),
                "20日均額": st.column_config.NumberColumn("20日均", format="%.0f"),
                "30日均額": st.column_config.NumberColumn("30日均", format="%.0f"),
            }
        )
    # === 替換結束 ===
