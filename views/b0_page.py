import streamlit as st
import pandas as pd
import os

# ==========================================
# 💡 效能救星：只讀取爬蟲腳本算好的輕量化 Parquet
# ==========================================
@st.cache_data(show_spinner=False, ttl=300)
def load_b0_data(DATA_DIR):
    latest_path = os.path.join(DATA_DIR, "B0_latest_calculated.parquet")
    history_path = os.path.join(DATA_DIR, "B0_lite_history.parquet")
    
    try:
        df_today = pd.read_parquet(latest_path) if os.path.exists(latest_path) else pd.DataFrame()
        df_lite_hist = pd.read_parquet(history_path) if os.path.exists(history_path) else pd.DataFrame()
        return df_today, df_lite_hist
    except Exception as e:
        print(f"讀取 B0 快取失敗: {e}")
        return pd.DataFrame(), pd.DataFrame()

def sync_b0_data(DATA_DIR):
    df_today, _ = load_b0_data(DATA_DIR)
    if not df_today.empty:
        st.session_state['b0_price'] = df_today

# ==========================================
# 🚀 互動儀表板
# ==========================================
@st.fragment
def render_b0_interactive_dashboard(df_b0, df_history):
    top_container = st.container()

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
            per_options = ["全部顯示", "PER < 15 (低估值)", "PER < 30 (合理)", "僅顯示獲利公司 (PER>0)"]
            sel_per = st.selectbox("⚖️ 估值(PER)過濾", per_options)
            
        st.markdown("---")
        special_opts = [opt for opt in df_b0['B0_特殊型態'].unique() if opt != "-"]
        sel_special = st.multiselect("🕵️ 特殊洗盤與窒息量篩選 (高勝率買點)", special_opts, placeholder="未選擇則顯示全部")

    filtered_df = df_b0.copy()
    if search_kw:
        filtered_df = filtered_df[filtered_df['統一代號'].astype(str).str.contains(search_kw) | filtered_df['股票名稱'].astype(str).str.contains(search_kw)]
    if vol_filter > 0:
        filtered_df = filtered_df[filtered_df['成交張數_num'] >= vol_filter]
    if sel_status:
        filtered_df = filtered_df[filtered_df['B0_量價狀態'].isin(sel_status)]
        
    if sel_per == "PER < 15 (低估值)":
        filtered_df = filtered_df[(filtered_df['PER'] > 0) & (filtered_df['PER'] < 15)]
    elif sel_per == "PER < 30 (合理)":
        filtered_df = filtered_df[(filtered_df['PER'] > 0) & (filtered_df['PER'] < 30)]
    elif sel_per == "僅顯示獲利公司 (PER>0)":
        filtered_df = filtered_df[filtered_df['PER'] > 0]

    if sel_special:
        filtered_df = filtered_df[filtered_df['B0_特殊型態'].isin(sel_special)]

    with top_container:
        st.markdown("### 📊 盤面結構 (基於當前篩選條件)")
        
        valid_codes = filtered_df['統一代號'].unique()
        hist_filtered = df_history[df_history['統一代號'].isin(valid_codes)]
        
        breadth_history = hist_filtered.groupby('標準日期').agg(
            漲家數=('漲跌幅', lambda x: (x > 0).sum()),
            跌家數=('漲跌幅', lambda x: (x < 0).sum()),
            平盤數=('漲跌幅', lambda x: (x == 0).sum()),
            漲停數=('漲跌幅', lambda x: (x >= 9.5).sum()),
            跌停數=('漲跌幅', lambda x: (x <= -9.5).sum())
        ).reset_index().sort_values('標準日期', ascending=False)
        
        up_count = down_count = flat_count = limit_up_count = limit_down_count = 0
        prev_up = prev_down = prev_flat = prev_l_up = prev_l_down = None
        
        if len(breadth_history) > 0:
            up_count = breadth_history.iloc[0]['漲家數']
            down_count = breadth_history.iloc[0]['跌家數']
            flat_count = breadth_history.iloc[0]['平盤數']
            limit_up_count = breadth_history.iloc[0]['漲停數']
            limit_down_count = breadth_history.iloc[0]['跌停數']
            
        if len(breadth_history) > 1:
            prev_up = breadth_history.iloc[1]['漲家數']
            prev_down = breadth_history.iloc[1]['跌家數']
            prev_flat = breadth_history.iloc[1]['平盤數']
            prev_l_up = breadth_history.iloc[1]['漲停數']
            prev_l_down = breadth_history.iloc[1]['跌停數']
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("漲家數 📈", f"{up_count} 家", delta=None if prev_up is None else f"{int(up_count - prev_up)} 家")
        m2.metric("跌家數 📉", f"{down_count} 家", delta=None if prev_down is None else f"{int(down_count - prev_down)} 家", delta_color="inverse")
        m3.metric("平盤數 ➖", f"{flat_count} 家", delta=None if prev_flat is None else f"{int(flat_count - prev_flat)} 家", delta_color="off")
        m4.metric("漲停數 🚀", f"{limit_up_count} 家", delta=None if prev_l_up is None else f"{int(limit_up_count - prev_l_up)} 家")
        m5.metric("跌停數 ☠️", f"{limit_down_count} 家", delta=None if prev_l_down is None else f"{int(limit_down_count - prev_l_down)} 家", delta_color="inverse")
        
        limit_up_df = filtered_df[filtered_df['漲跌幅'] >= 9.5]
        limit_down_df = filtered_df[filtered_df['漲跌幅'] <= -9.5]
        
        if not limit_up_df.empty:
            with st.expander(f"✨ 查看 {len(limit_up_df)} 檔漲停標的"):
                lu_list = (limit_up_df['統一代號'] + " " + limit_up_df['股票名稱']).tolist()
                st.write("、".join(lu_list))
                
        if not limit_down_df.empty:
            with st.expander(f"⚠️ 查看 {len(limit_down_df)} 檔跌停標的"):
                ld_list = (limit_down_df['統一代號'] + " " + limit_down_df['股票名稱']).tolist()
                st.write("、".join(ld_list))

        if len(breadth_history) > 0:
            st.markdown("##### 📅 歷史盤面變化")
            breadth_table = breadth_history.head(15).set_index('標準日期').T
            breadth_table.columns = [str(c)[-4:] for c in breadth_table.columns]
            st.dataframe(breadth_table, use_container_width=True)

        st.markdown("---")

    tab_basic, tab_momentum = st.tabs(["🔹 全市場基礎量價", "🔹 資金動能雷達"])

    with tab_basic:
        display_cols = ['統一代號', '股票名稱', '成交', '漲跌幅', '成交張數', '成交額(百萬)', '成交金額日變化率', 'PER', '5日均量', '5日均額', 'B0_量價狀態', 'B0_特殊型態']
        view_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()

        st.markdown(f"**共找到 {len(view_df)} 檔符合條件的標的**")
        
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
                "PER": st.column_config.NumberColumn("本益比", format="%.2f"),
                "B0_量價狀態": st.column_config.TextColumn("量價主力照妖鏡", width="large"),
                "B0_特殊型態": st.column_config.TextColumn("特殊型態雷達", width="medium"),
            }
        )

    with tab_momentum:
        st.markdown("#### 資金動力渦輪：找出真正的行情燃料")
        st.caption("本區塊先行排除流動性太差的標的 (成交額 > 5000萬 且 股價 > 10元)，以避免倍數失真。")

        momentum_df = filtered_df[
            (filtered_df['成交額(百萬)'] > 50) & 
            (filtered_df['成交'] > 10) &
            (filtered_df.get('5日均額', 0) > 10) 
        ].copy()
        
        momentum_df['額度增加絕對值'] = momentum_df['成交額(百萬)'] - momentum_df.get('5日均額', 0)
        
        st.markdown("---")
        st.markdown("##### 🏆 成交額大熱鍋(8/12起算)")
        st.caption("市場資金總量增加最多，代表用錢和量砸出來的活絡程度，也可看族群性 (主升段發動或大型法人調倉，已排除流動性過差標的，也不看籌碼流向何處)")
        
        periods = [5, 10, 20, 30, 45]
        for p in periods:
            avg_col = f'{p}日均額'
            if avg_col in momentum_df.columns:
                momentum_df[f'較{p}日均額增加'] = momentum_df['成交額(百萬)'] - momentum_df[avg_col]
        
        abs_tab_names = ["🔥 成交金額增加短中長趨勢"] + [f"🔹相較 {p} 日均額" for p in periods]
        abs_tabs = st.tabs(abs_tab_names)
        
        with abs_tabs[0]:
            summary_cols_abs = ['統一代號', '股票名稱', '成交金額日變化率', '成交額(百萬)']
            summary_col_config_abs = {
                "統一代號": st.column_config.TextColumn("代號"),
                "股票名稱": st.column_config.TextColumn("名稱"),
                "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                "成交額(百萬)": st.column_config.NumberColumn("今日成交額", format="%.0f"),
            }
            for p in periods:
                if f'較{p}日均額增加' in momentum_df.columns:
                    summary_cols_abs.append(f'較{p}日均額增加')
                    summary_col_config_abs[f'較{p}日均額增加'] = st.column_config.NumberColumn(f"較{p}日增加", format="+%.0f")
            
            if '較5日均額增加' in momentum_df.columns:
                top_abs_summary = momentum_df.sort_values('較5日均額增加', ascending=False).head(50)
            else:
                top_abs_summary = momentum_df.sort_values('成交額(百萬)', ascending=False).head(50)
                
            st.dataframe(
                top_abs_summary[summary_cols_abs],
                use_container_width=True, hide_index=True, height=500,
                column_config=summary_col_config_abs
            )

        for idx, p in enumerate(periods):
            with abs_tabs[idx + 1]:
                avg_col = f'{p}日均額'
                if avg_col in momentum_df.columns:
                    top_abs = momentum_df.sort_values(f'較{p}日均額增加', ascending=False).head(30)
                    display_cols_abs = ['統一代號', '股票名稱', f'較{p}日均額增加', '成交額(百萬)', avg_col, '成交金額日變化率', '漲跌幅']
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


        st.markdown("---")
        st.markdown("##### 🚀 出量點火器 (8/12起算)")
        st.caption("看相較5日均額最敏感，找看看突然異常放量的股票 (可能突破第一根，或波段重新發動，須留意延續性)")      

        for p in periods:
            avg_col = f'{p}日均額'
            if avg_col in momentum_df.columns:
                safe_avg = momentum_df[avg_col].replace(0, 0.01)
                momentum_df[f'{p}日爆發倍數'] = (momentum_df['成交額(百萬)'] / safe_avg).fillna(0)
        
        tab_names = ["🔥 異常點火短中長趨勢"] + [f"🔹相較 {p} 日均額" for p in periods]
        ignition_tabs = st.tabs(tab_names)
        
        with ignition_tabs[0]:
            summary_cols = ['統一代號', '股票名稱', '成交金額日變化率', '成交額(百萬)']
            summary_col_config = {
                "統一代號": st.column_config.TextColumn("代號"),
                "股票名稱": st.column_config.TextColumn("名稱"),
                "成交金額日變化率": st.column_config.NumberColumn("日變化率(%)", format="%+.1f %%"),
                "成交額(百萬)": st.column_config.NumberColumn("今日成交額", format="%.0f"),
            }
            
            for p in periods:
                if f'{p}日爆發倍數' in momentum_df.columns:
                    summary_cols.append(f'{p}日爆發倍數')
                    summary_col_config[f'{p}日爆發倍數'] = st.column_config.NumberColumn(f"{p}日倍數", format="%.1fx")
                    
            if '5日爆發倍數' in momentum_df.columns:
                top_summary = momentum_df.sort_values('5日爆發倍數', ascending=False).head(50)
            else:
                top_summary = momentum_df.sort_values('成交額(百萬)', ascending=False).head(50)
                
            st.dataframe(
                top_summary[summary_cols],
                use_container_width=True, hide_index=True, height=500,
                column_config=summary_col_config
            )

        for idx, p in enumerate(periods):
            with ignition_tabs[idx + 1]: 
                if f'{p}日爆發倍數' in momentum_df.columns:
                    top_ratio = momentum_df.sort_values(f'{p}日爆發倍數', ascending=False).head(30)
                    display_cols_ratio = ['統一代號', '股票名稱', f'{p}日爆發倍數', '成交額(百萬)', f'{p}日均額', '成交金額日變化率', '漲跌幅']
                    
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
        
        st.markdown("---")
        st.markdown("##### 📈 持續資金水龍頭 (8/12起算)")
        st.caption("若是短大於長週期 代表成交金額持續擴張，而不是單日爆量，這裡只看成交金額，不看籌碼流向何處")
        
        def get_fund_trend(row):
            try:
                today = float(row.get('成交額(百萬)', 0))
                ma5 = float(row.get('5日均額', 0))
                ma10 = float(row.get('10日均額', 0))
                ma20 = float(row.get('20日均額', 0))
                
                if ma5 > 0 and ma10 > 0 and ma20 > 0:
                    if ma5 > ma10 and ma10 > ma20: return "🔥 資金湧入 (延續性強)"
                    elif today > ma5 and ma5 <= ma10: return "⚡ 單日點火 (需觀察)"
                    elif ma5 < ma10 and ma10 < ma20: return "💧 資金退潮 (動能弱)"
                    else: return "⚖️ 震盪換手"
                return "⚪ 資料不足"
            except:
                return "-"
                
        momentum_df['資金延續趨勢'] = momentum_df.apply(get_fund_trend, axis=1)
        
        trend_df = momentum_df.sort_values('成交額(百萬)', ascending=False).head(150)
        trend_cols = ['統一代號', '股票名稱', '資金延續趨勢', '成交額(百萬)', '5日均額', '10日均額', '20日均額', '30日均額']
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

# ==========================================
# 🌟 主渲染入口
# ==========================================
def show_b0_page(DATA_DIR, STOCK_DICT):
    df_b0, df_history = load_b0_data(DATA_DIR)
    
    if df_b0.empty:
        st.warning("⚠️ 目前資料庫中無任何有效的成交價檔案，請確認 `data` 資料夾狀態。")
        return

    date_raw = str(df_b0['股價日期'].iloc[0])
    b0_latest_date_str = date_raw
    if len(date_raw) >= 8:
        b0_latest_date_str = f"{date_raw[:4]}/{date_raw[4:6]}/{date_raw[6:8]}"
    elif len(date_raw) == 4:
        b0_latest_date_str = f"2026/{date_raw[:2]}/{date_raw[2:]}"

    st.markdown("## 🏆 量價與估值掃描")
    st.caption(f"資料基準日: **{b0_latest_date_str}** ｜ 透視全市場資金動能與主力控盤狀態。")
    st.write("---")
    
    def resolve_stock_name(row):
        raw_name = str(row.get('B0_原始名稱', '')).strip()
        if raw_name and raw_name.lower() != 'nan' and raw_name != 'none': return raw_name
        code = str(row.get('統一代號', ''))
        if STOCK_DICT:
            dict_name = STOCK_DICT.get(code, {}).get("name", "")
            if dict_name: return dict_name
        return ""
        
    df_b0['股票名稱'] = df_b0.apply(resolve_stock_name, axis=1)
    render_b0_interactive_dashboard(df_b0, df_history)
