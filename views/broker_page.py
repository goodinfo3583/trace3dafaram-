# views/broker_page.py
import streamlit as st
import pandas as pd
from utils.data_utils import calculate_chip_concentration

# 🌟 效能救星 1：極致省記憶體版讀取引擎
@st.cache_data(show_spinner=False, ttl=3600)
def load_full_blood_broker_history():
    remote_parquet_url = "https://huggingface.co/datasets/goodinfo3583/tw-broker-parquet/resolve/main/broker_summary_master.parquet"
    try:
        # 1. 指定需要的欄位 (不要讀取 均買價、均賣價 等字串，節省極大記憶體)
        columns_to_read = ['日期', '股票代號', '券商代號', '券商名稱', '買賣超股數', '總買進股數', '總買進金額', '買賣超金額']
        df = pd.read_parquet(remote_parquet_url, columns=columns_to_read)
        
        df = df.rename(columns={
            '日期': 'trade_date', 
            '股票代號': 'stock_code', 
            '券商名稱': 'broker_name',
            '券商代號': 'broker',
            '買賣超股數': 'net_vol_shares'
        })
        
        # 2. 致命優化：將字串強制轉為 Category 型別！(記憶體瞬間從 800MB 降到 100MB 以下)
        df['stock_code'] = df['stock_code'].astype('category')
        df['broker'] = df['broker'].astype('category')
        df['broker_name'] = df['broker_name'].astype('category')
        
        # 將 Timestamp 直接轉為字串格式 (YYYY-MM-DD)
        df['trade_date'] = df['trade_date'].dt.strftime('%Y-%m-%d').astype('category')
        
        df['net_vol'] = df['net_vol_shares'] / 1000 # 降低精確度省記憶體
        df['side'] = df['net_vol'].apply(lambda x: 'buy' if x > 0 else 'sell').astype('category')
        
        return df
    except Exception as e:
        st.error(f"載入滿血版明細失敗: {e}")
        return pd.DataFrame()
    
def sync_b8_data():
    """在背景預先計算好全市場的 B8 券商連買狀態並存入 session_state"""
    if 'b8_summary_df' in st.session_state:
        return

    try:
        # 讀取滿血版資料
        df_raw = load_full_blood_broker_history()
        if df_raw.empty: return

        # 優先抓取中文券商名稱
        broker_col = next((c for c in ['broker_name', 'broker', '券商名稱', '券商', 'name'] if c in df_raw.columns), None)
        if not broker_col: return

        # 🚀 記憶體防爆 1：只留下需要的欄位
        df_light = df_raw[['trade_date', 'stock_code', broker_col, 'net_vol', 'side']].copy()
        
        # 轉換為 signed_vol (淨買賣張數)
        df_light['signed_vol'] = df_light['net_vol'].abs()
        df_light.loc[df_light['side'] == 'sell', 'signed_vol'] = -df_light['signed_vol']

        valid_dates = df_light['trade_date'].dropna().unique()
        all_dates = sorted(valid_dates, reverse=True)
        if not all_dates: return
        latest_date = all_dates[0]

        # 🚀 記憶體防爆 2：日連買只追蹤「最新一天有買超」的候選人
        latest_buys = df_light[(df_light['trade_date'] == latest_date) & (df_light['signed_vol'] > 0)]
        day_candidates = latest_buys[['stock_code', broker_col]].drop_duplicates()
        df_day_filtered = pd.merge(df_light, day_candidates, on=['stock_code', broker_col], how='inner')

        scan_pivot = df_day_filtered.pivot_table(index=['stock_code', broker_col], columns='trade_date', values='signed_vol', aggfunc='sum')
        
        def calc_daily(row):
            streak = 0
            for c in all_dates:
                val = row.get(c, 0)
                if pd.isna(val) or val <= 0: break
                streak += 1
            return streak
            
        scan_pivot['連買日數'] = scan_pivot.apply(calc_daily, axis=1)
        valid_sum_cols = [c for c in all_dates[:20] if c in scan_pivot.columns]
        scan_pivot['近期買超總張數'] = scan_pivot[valid_sum_cols].sum(axis=1)

        # 🚀 記憶體防爆 3：週連買只追蹤「最新一週有買超」的候選人
        df_week = df_light.dropna(subset=['trade_date']).copy()
        df_week['date_dt'] = pd.to_datetime(df_week['trade_date'], errors='coerce')
        df_week = df_week.dropna(subset=['date_dt'])
        df_week['year_week'] = df_week['date_dt'].dt.strftime('%Y-%W')
        
        weekly_raw = df_week.groupby(['stock_code', broker_col, 'year_week'], as_index=False)['signed_vol'].sum()
        all_weeks = sorted(weekly_raw['year_week'].unique(), reverse=True)
        if not all_weeks: return
        latest_week = all_weeks[0]
        
        latest_week_buys = weekly_raw[(weekly_raw['year_week'] == latest_week) & (weekly_raw['signed_vol'] > 0)]
        week_candidates = latest_week_buys[['stock_code', broker_col]].drop_duplicates()
        df_week_filtered = pd.merge(weekly_raw, week_candidates, on=['stock_code', broker_col], how='inner')
        
        weekly_sum = df_week_filtered.pivot_table(index=['stock_code', broker_col], columns='year_week', values='signed_vol', aggfunc='sum')
        
        def calc_weekly(row):
            streak = 0
            for c in all_weeks:
                val = row.get(c, 0)
                if pd.isna(val) or val <= 0: break
                streak += 1
            return streak
            
        weekly_sum['連買週數'] = weekly_sum.apply(calc_weekly, axis=1)

        # 4. 合併並找出最佳分點特徵
        df_day = scan_pivot.reset_index()[['stock_code', broker_col, '連買日數', '近期買超總張數']]
        df_wk = weekly_sum.reset_index()[['stock_code', broker_col, '連買週數']]
        
        final_b8 = pd.merge(df_day, df_wk, on=['stock_code', broker_col], how='outer').fillna(0)
        
        stock_summary = final_b8.groupby('stock_code').agg({
            '連買日數': 'max',
            '連買週數': 'max',
            '近期買超總張數': 'max'
        }).reset_index().rename(columns={'stock_code': '統一代號'})

        # 存入全域變數
        st.session_state['b8_summary_df'] = stock_summary
        st.session_state['b8_latest_date'] = latest_date

        # 清空暫存記憶體
        import gc
        del df_raw, df_light, scan_pivot, weekly_sum, final_b8
        gc.collect()

    except Exception as e:
        print(f"B8 背景載入失敗: {e}")
        
# 💡 效能救星 2：將所有圖表與選項封裝在 Fragment 內，避免切換日期時整頁重整
@st.fragment
def render_broker_dashboard(target_stock, display_name, df_raw_all, df_trend):
    latest_data = df_trend.iloc[-1]
    
    st.metric(
        label=f"{latest_data['trade_date']} 最新券商分點集中度", 
        value=f"{latest_data['concentration_%']}%",
        delta=f"淨買超 {latest_data['net_buy']:,} 張"
    )
    #集中度繪圖    
    import plotly.graph_objects as go
    st.subheader(f"📊 {display_name} 分點集中度連續性走勢")
    
    # 處理短日期 (只留 月-日)
    df_trend_plot = df_trend.copy()
    df_trend_plot['trade_date_short'] = pd.to_datetime(df_trend_plot['trade_date']).dt.strftime('%m-%d')
    
    fig_trend = go.Figure()
    
    # 根據正負值設定紅綠顏色
    colors = ['#FF4B4B' if val > 0 else '#00E272' for val in df_trend_plot['concentration_%']]
    
    fig_trend.add_trace(go.Bar(
        x=df_trend_plot['trade_date_short'], 
        y=df_trend_plot['concentration_%'],
        marker_color=colors,
        text=[f"{v:.1f}%" if abs(v)>0 else "" for v in df_trend_plot['concentration_%']],
        textposition='outside',
        textfont=dict(size=10, color="#E2E8F0")
    ))
    
    # 💡 畫上數值為 0 的黃色基準線
    fig_trend.add_hline(y=0, line_color="#FFD700", line_width=1.5, line_dash="dash")
    
    fig_trend.update_layout(
        height=320, 
        template='plotly_dark', 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(title="集中度 (%)", showgrid=True, gridcolor='#334155'),
        xaxis=dict(type='category', tickangle=45),
        dragmode='pan'
    )
    
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
    
    with st.expander("📅 展開查看：近 60 日集中度與淨買超歷史表", expanded=False):
        df_trend_disp = df_trend.sort_values('trade_date', ascending=False).head(60).copy()
        df_trend_disp = df_trend_disp[['trade_date', 'net_buy', 'concentration_%']]
        df_trend_disp.columns = ['交易日期', '淨買超(張)', '集中度(%)']
        st.dataframe(df_trend_disp, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(f"🔍 {display_name} 券商分點進出明細")
    
    stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
    
    if stock_raw.empty:
        st.warning(f"在歷史總帳本中，找不到 **{display_name}** 的紀錄。")
        return
        
    broker_col = next((c for c in ['broker_name', 'broker', '券商名稱', '券商', 'name'] if c in stock_raw.columns), None)
    
    if broker_col is None:
        st.error("⚠️ 無法在資料庫中找到「券商名稱」欄位！")
        return

    available_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)
    
    tab1, tab2, tab3 = st.tabs(["🔹 單日進出明細", "🔹 區間囤貨 (近60日)", "🔹 歷史進出 (近30日)"])
    
# --------- 標籤 1: 單日明細 ---------
    with tab1:
        # 💡 在這裡切換日期，只會局部更新這個 Fragment，不會影響到上方的搜尋欄！
        selected_date = st.selectbox("請選擇要查看的交易日期：", available_dates, key="daily_date_sel")
        daily_raw = stock_raw[stock_raw['trade_date'] == selected_date]
        
        col_buy, col_sell = st.columns(2)
        
        def format_daily_table(df, is_buy):
            if df.empty: return None
            df = df.copy()
            
            # 以「券商名稱」為基準去除重複的資料列
            df = df.drop_duplicates(subset=[broker_col])
            
            # 如果是賣方，將張數與金額轉為正數以利閱讀
            if not is_buy: 
                df['net_vol'] = df['net_vol'].abs()
                if '買賣超金額' in df.columns:
                    df['買賣超金額'] = df['買賣超金額'].abs()
            
            # 依張數由大到小排序，抓出前 15 大
            df = df.sort_values('net_vol', ascending=False).head(15)
            
            # 🚀 滿血升級：加入金額欄位 (轉換為「萬元」方便閱讀)
            if '買賣超金額' in df.columns:
                df['金額(萬)'] = (df['買賣超金額'] / 10000).round(0)
                df = df[[broker_col, 'net_vol', '金額(萬)']]
                df.columns = ['券商名稱', '張數', '金額(萬)']
                
                # 套用千分位逗號格式
                return df.style.format({
                    '張數': "{:,.1f}",    # 保留一位小數，精準顯示零股
                    '金額(萬)': "{:,.0f}"
                })
            else:
                # 備用方案：若沒抓到金額欄位，維持原樣
                df = df[[broker_col, 'net_vol']]
                df.columns = ['券商名稱', '張數']
                return df.style.format({'張數': "{:,.1f}"})

        with col_buy:
            st.markdown("##### 🔴 淨買超前 15 大分點")
            styled_buy = format_daily_table(daily_raw[daily_raw['side'] == 'buy'], True)
            if styled_buy is not None: 
                st.dataframe(styled_buy, use_container_width=True, hide_index=True)
            else: 
                st.write("當日無資料")
            
        with col_sell:
            st.markdown("##### 🟢 淨賣超前 15 大分點")
            styled_sell = format_daily_table(daily_raw[daily_raw['side'] == 'sell'], False)
            if styled_sell is not None: 
                st.dataframe(styled_sell, use_container_width=True, hide_index=True)
            else: 
                st.write("當日無資料")

    # --------- 標籤 2: 區間囤貨 (近60日) 🚀 滿血升級版 🚀 ---------
    with tab2:
        st.markdown("##### 🕵️‍♂️ 誰在拿真金白銀連續吃貨？")
        recent_dates = available_dates[:60]
        recent_raw = stock_raw[stock_raw['trade_date'].isin(recent_dates)].copy()
        
        # 滿血聚合：算張數、金額與均價
        hoard_df = recent_raw.groupby(broker_col).agg(
            區間淨買超張數=('net_vol', 'sum'),
            區間總買進股數=('總買進股數', 'sum'),
            區間總買進金額=('總買進金額', 'sum'),
            區間淨買賣金額=('買賣超金額', 'sum')
        ).reset_index()
        
        # 計算平均防守成本與斥資(億)
        hoard_df['主力平均成本'] = (hoard_df['區間總買進金額'] / hoard_df['區間總買進股數']).fillna(0).round(2)
        hoard_df['囤貨斥資(億)'] = (hoard_df['區間淨買賣金額'] / 100000000).round(2)
        
        col_hoard, col_dump = st.columns(2)
        
        def fmt_dash(val):
            if pd.isna(val) or val == 0: return "-"
            return "{:,.0f}".format(val)
        
        with col_hoard:
            st.markdown("##### 📈 近 60 日囤貨分點 (斥資破億榜)")
            hoarders = hoard_df[hoard_df['區間淨買超張數'] > 0].sort_values('囤貨斥資(億)', ascending=False)
            
            if not hoarders.empty:
                hoarders_display = hoarders[[broker_col, '區間淨買超張數', '主力平均成本', '囤貨斥資(億)']]
                hoarders_display.columns = ['券商名稱', '淨買超(張)', '均買價', '斥資(億)']
                
                styled_hoard = hoarders_display.style.format({
                    '淨買超(張)': fmt_dash, 
                    '均買價': "{:.2f}",
                    '斥資(億)': "{:.2f}"
                })
                # 如果你的 Streamlit 版本較新，可以用 background_gradient 讓金額越大的越紅
                try:
                    styled_hoard = styled_hoard.background_gradient(subset=['斥資(億)'], cmap='Reds')
                except:
                    pass
                
                st.dataframe(styled_hoard, use_container_width=True, hide_index=True)
            else: 
                st.write("區間內無明顯囤貨分點")
                
        with col_dump:
            st.markdown("##### 📉 近 60 日倒貨分點")
            dumpers = hoard_df[hoard_df['區間淨買超張數'] < 0].sort_values('囤貨斥資(億)', ascending=True).copy()
            
            if not dumpers.empty:
                dumpers['囤貨斥資(億)'] = dumpers['囤貨斥資(億)'].abs()
                dumpers['區間淨買超張數'] = dumpers['區間淨買超張數'].abs()
                
                dumpers_display = dumpers[[broker_col, '區間淨買超張數', '囤貨斥資(億)']]
                dumpers_display.columns = ['券商名稱', '淨賣超(張)', '提款(億)']
                
                styled_dump = dumpers_display.style.format({
                    '淨賣超(張)': fmt_dash, 
                    '提款(億)': "{:.2f}"
                })
                try:
                    styled_dump = styled_dump.background_gradient(subset=['提款(億)'], cmap='Greens')
                except:
                    pass
                
                st.dataframe(styled_dump, use_container_width=True, hide_index=True)
            else: 
                st.write("區間內無明顯倒貨分點")

    # --------- 標籤 3: 歷史進出矩陣 (近30日) ---------
    with tab3:
        st.markdown("##### 🗺️ 分點淨買賣力道")
        st.write("橫列為各分點，縱欄顯示**近 30 個交易日**。")
        
        all_matrix_raw = stock_raw.copy()
        
        if not all_matrix_raw.empty:
            all_matrix_raw['signed_vol'] = all_matrix_raw.apply(
                lambda x: abs(x['net_vol']) if x['side'] == 'buy' else -abs(x['net_vol']), axis=1
            )
            
            all_matrix_raw['date_dt'] = pd.to_datetime(all_matrix_raw['trade_date'])
            all_matrix_raw['year_week'] = all_matrix_raw['date_dt'].dt.strftime('%Y-%W')
            weekly_sum = all_matrix_raw.groupby([broker_col, 'year_week'])['signed_vol'].sum().unstack(fill_value=0)
            week_cols = sorted(weekly_sum.columns, reverse=True)
            
            full_pivot = all_matrix_raw.pivot_table(
                index=broker_col, 
                columns='trade_date', 
                values='signed_vol', 
                aggfunc='sum'
            )
            all_dates_sorted = sorted(full_pivot.columns, reverse=True)
            
            display_dates = all_dates_sorted[:30]
            pivot_df = full_pivot[display_dates].copy()
            pivot_df['區間累計'] = pivot_df.sum(axis=1)
            pivot_df = pivot_df.sort_values('區間累計', ascending=False)
            
            def calc_daily_streak(row_name):
                if row_name not in full_pivot.index: return "-"
                row = full_pivot.loc[row_name]
                streak = 0
                sign = None
                for c in all_dates_sorted:
                    val = row.get(c, 0)
                    if pd.isna(val) or val == 0:
                        break  
                    current_sign = 1 if val > 0 else -1
                    if sign is None:
                        sign = current_sign
                        streak = sign
                    elif sign == current_sign:
                        streak += sign
                    else:
                        break  
                if streak > 0: return f"連買 {streak} 日"
                elif streak < 0: return f"連賣 {-streak} 日"
                else: return "-"
                
            pivot_df['日連買動態'] = pivot_df.index.to_series().apply(calc_daily_streak)

            def calc_weekly_streak(broker_name):
                if weekly_sum.empty or broker_name not in weekly_sum.index:
                    return "-"
                row = weekly_sum.loc[broker_name]
                streak = 0
                sign = None
                for c in week_cols:
                    val = row.get(c, 0)
                    if val == 0 or pd.isna(val):
                        break
                    current_sign = 1 if val > 0 else -1
                    if sign is None:
                        sign = current_sign
                        streak = sign
                    elif sign == current_sign:
                        streak += sign
                    else:
                        break
                if streak > 0: return f"連買 {streak} 週"
                elif streak < 0: return f"連賣 {-streak} 週"
                else: return "-"
                
            pivot_df['週連買動態'] = pivot_df.index.to_series().apply(calc_weekly_streak)
            
            pivot_df[display_dates] = pivot_df[display_dates].fillna("-")
            pivot_df.index.name = "中文券商分點"
            
            cols = ['日連買動態', '週連買動態', '區間累計'] + display_dates
            pivot_df = pivot_df[cols]

            sort_option = st.radio(
                "🔍 排序依據：", 
                ["依區間累計排序(預設)", "依連買日數排序", "依連買週數排序"], 
                horizontal=True,
                key=f"sort_radio_{target_stock}"
            )
            
            def extract_streak_num(val):
                if isinstance(val, str) and "連買" in val:
                    try:
                        return int(''.join(filter(str.isdigit, val)))
                    except: return 0
                return 0

            if sort_option == "依連買日數排序":
                pivot_df['sort_key'] = pivot_df['日連買動態'].apply(extract_streak_num)
                pivot_df = pivot_df.sort_values(['sort_key', '區間累計'], ascending=[False, False]).drop(columns=['sort_key'])
            
            elif sort_option == "依連買週數排序":
                pivot_df['sort_key'] = pivot_df['週連買動態'].apply(extract_streak_num)
                pivot_df = pivot_df.sort_values(['sort_key', '區間累計'], ascending=[False, False]).drop(columns=['sort_key'])
            
            def color_net_vol(val):
                if isinstance(val, str):
                    if val == "-": return 'color: #64748B;' 
                    if "連買" in val: return 'color: #FF4B4B;' 
                    if "連賣" in val: return 'color: #00E272;' 
                try:
                    v = float(val)
                    if v > 0: return 'color: #FF4B4B;'
                    elif v < 0: return 'color: #00E272;'
                except: pass
                return 'color: #94A3B8;'
            
            if hasattr(pivot_df.style, 'map'):
                styled_pivot = pivot_df.style.map(color_net_vol).format(lambda x: "{:,.0f}".format(x) if isinstance(x, (int, float)) else x)
            else:
                styled_pivot = pivot_df.style.applymap(color_net_vol).format(lambda x: "{:,.0f}".format(x) if isinstance(x, (int, float)) else x)
            
            st.dataframe(styled_pivot, use_container_width=True)
        else:
            st.write("無足夠資料產出")

# ==========================================
# 🖼️ 主渲染入口
# ==========================================
def render(STOCK_DICT=None):
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; 
                border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
        <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
            券商主力淨買力與集中度追蹤
        </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("觀察前 15 大分點買賣力道相抵後的淨流向，追蹤籌碼集中度連續性與券商進出。(已升級滿血版金額運算)")
    
    stock_options = []
    if STOCK_DICT:
        unique_options = {f"{v['id']} {v['name']}" for v in STOCK_DICT.values() if len(str(v['id'])) <= 4}
        stock_options = sorted(list(unique_options))
    
    default_index = 0

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_stock_str = st.selectbox(
            "請選擇要查詢的股票：", 
            options=[""] + stock_options,
            index=default_index,
            key="broker_search_input"
        )

    # 🌟 全市場分點連買掃描器 🌟
    with st.expander("🌍 全市場連買分點快搜 (尋找主力連續吃貨標的)", expanded=False):
        st.markdown("此功能將掃描資料庫中所有股票，找出當前處於「連續買超」狀態的最高天數/週數分點。", unsafe_allow_html=True)

        scan_mode = st.radio(
            "請選擇全市場排行方式：", 
            ["依日連買排行", "依週連買排行", "依近期買超張數排行"],
            horizontal=True,
            key="global_broker_scan_radio"
        )
        
        c_scan, c_clear = st.columns([3, 1])
        with c_scan:
            if st.button("🚀 開始全市場掃描", use_container_width=True, type="primary"):
                with st.spinner("正在進行全市場運算 (啟動記憶體防爆機制)，請稍候..."):
                    df_raw_all = load_full_blood_broker_history()
                    
                    if not df_raw_all.empty:
                        # 🚀 記憶體防爆 1：只保留需要的欄位，淨買賣超直接用 net_vol，不要再做 apply
                        scan_df = df_raw_all[['trade_date', 'stock_code', 'broker_name', 'net_vol']].copy()
                        
                        valid_dates = scan_df['trade_date'].dropna().unique()
                        all_dates = sorted(valid_dates, reverse=True)
                        if not all_dates:
                            st.warning("無有效日期資料")
                            st.stop()
                            
                        latest_date = all_dates[0]
                        
                        if scan_mode in ["依日連買排行", "依近期買超張數排行"]:
                            # 🚀 記憶體防爆 2：只抓出「最新交易日有買超」的股票與分點！(過濾掉 95% 不相干的資料)
                            latest_buys = scan_df[(scan_df['trade_date'] == latest_date) & (scan_df['net_vol'] > 0)]
                            candidates = latest_buys[['stock_code', 'broker_name']].drop_duplicates()
                            
                            # 把完整的資料與候選名單做 inner join，瞬間把 600 萬筆縮小到只剩幾萬筆
                            df_candidates = pd.merge(scan_df, candidates, on=['stock_code', 'broker_name'], how='inner')
                            
                            # 現在 Pivot 絕對不會當機了
                            scan_pivot = df_candidates.pivot_table(
                                index=['stock_code', 'broker_name'], 
                                columns='trade_date', 
                                values='net_vol', 
                                aggfunc='sum'
                            )
                            
                            def calc_global_daily_streak(row):
                                streak = 0
                                for c in all_dates:
                                    val = row.get(c, 0)
                                    if pd.isna(val) or val <= 0:
                                        break
                                    streak += 1
                                return streak
                                
                            scan_pivot['連買日數'] = scan_pivot.apply(calc_global_daily_streak, axis=1)
                            
                            result_df = scan_pivot[scan_pivot['連買日數'] >= 1].copy() 
                            valid_sum_cols = [c for c in all_dates[:20] if c in result_df.columns]
                            result_df['近期買超總張數'] = result_df[valid_sum_cols].sum(axis=1)
                            
                            if scan_mode == "依日連買排行":
                                result_df = result_df[result_df['連買日數'] >= 2].reset_index().sort_values(['連買日數', '近期買超總張數'], ascending=[False, False])
                            else:
                                result_df = result_df[result_df['近期買超總張數'] > 0].reset_index().sort_values(['近期買超總張數', '連買日數'], ascending=[False, False])
                                
                            result_df = result_df[['stock_code', 'broker_name', '連買日數', '近期買超總張數']]
                            
                        else:
                            # --- 週排行防爆版 ---
                            scan_df['date_dt'] = pd.to_datetime(scan_df['trade_date'], errors='coerce')
                            scan_df = scan_df.dropna(subset=['date_dt'])
                            scan_df['year_week'] = scan_df['date_dt'].dt.strftime('%Y-%W')
                            
                            # 同樣的招式：先以週聚合
                            weekly_raw = scan_df.groupby(['stock_code', 'broker_name', 'year_week'], as_index=False)['net_vol'].sum()
                            all_weeks = sorted(weekly_raw['year_week'].unique(), reverse=True)
                            latest_week = all_weeks[0]
                            
                            # 找出「最新一週有買超」的候選人
                            latest_week_buys = weekly_raw[(weekly_raw['year_week'] == latest_week) & (weekly_raw['net_vol'] > 0)]
                            candidates_wk = latest_week_buys[['stock_code', 'broker_name']].drop_duplicates()
                            
                            df_candidates_wk = pd.merge(weekly_raw, candidates_wk, on=['stock_code', 'broker_name'], how='inner')
                            
                            weekly_sum = df_candidates_wk.pivot_table(index=['stock_code', 'broker_name'], columns='year_week', values='net_vol', aggfunc='sum')
                            
                            def calc_global_weekly_streak(row):
                                streak = 0
                                for c in all_weeks:
                                    val = row.get(c, 0)
                                    if pd.isna(val) or val <= 0:
                                        break
                                    streak += 1
                                return streak
                                
                            weekly_sum['連買週數'] = weekly_sum.apply(calc_global_weekly_streak, axis=1)
                            
                            result_df = weekly_sum[weekly_sum['連買週數'] >= 2].copy()
                            valid_sum_weeks = [c for c in all_weeks[:4] if c in result_df.columns]
                            result_df['近期買超總張數'] = result_df[valid_sum_weeks].sum(axis=1)
                            
                            result_df = result_df.reset_index().sort_values(['連買週數', '近期買超總張數'], ascending=[False, False])
                            result_df = result_df[['stock_code', 'broker_name', '連買週數', '近期買超總張數']]

                        # 映射名稱
                        if STOCK_DICT:
                            result_df['股票名稱'] = result_df['stock_code'].astype(str).apply(
                                lambda x: STOCK_DICT.get(x, {}).get('name', '-')
                            )
                            if '股票名稱' in result_df.columns:
                                cols = result_df.columns.tolist()
                                cols.insert(1, cols.pop(cols.index('股票名稱')))
                                result_df = result_df[cols]
                        
                        result_df.rename(columns={'stock_code': '股票代號', 'broker_name': '券商分點'}, inplace=True)
                        
                        st.session_state['broker_global_scan_result'] = result_df
                        st.session_state['broker_global_scan_mode'] = scan_mode
        
        with c_clear:
            if st.button("🗑️ 清除暫存", use_container_width=True):
                st.session_state.pop('broker_global_scan_result', None)
                st.rerun()

        if 'broker_global_scan_result' in st.session_state:
            cached_res = st.session_state['broker_global_scan_result']
            cached_mode = st.session_state.get('broker_global_scan_mode', '未知模式')
            
            if not cached_res.empty:
                st.success(f"🎯 掃描結果 ({cached_mode})：共發現 {len(cached_res)} 組主力特徵。")
                styled_res = cached_res.head(100).style.format({'近期買超總張數': "{:,.0f}"})
                st.dataframe(styled_res, use_container_width=True, hide_index=True)
            else:
                st.info("目前市場上無明顯的分點特徵。")
          
    if selected_stock_str:
        target_stock = selected_stock_str.split(" ")[0].strip()
        display_name = selected_stock_str
        
        # 載入全市場資料 (這裡會秒開，因為有快取)
        df_raw_all = load_full_blood_broker_history()
        
        if not df_raw_all.empty:
            # 🚀 效能大躍進：直接在本地把這檔股票切出來
            stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
            
            if not stock_raw.empty:
                try:
                    # 🚀 將已經切好的資料傳給工具箱，0.01 秒瞬間算出集中度！
                    df_trend = calculate_chip_concentration(stock_raw)
                except Exception as e:
                    print(f"集中度計算錯誤: {e}")
                    df_trend = pd.DataFrame()
                    
                if not df_trend.empty:
                    render_broker_dashboard(target_stock, display_name, df_raw_all, df_trend)
                else:
                    # 給一個合法的假日期避免圖表崩潰
                    import datetime
                    dummy_date = datetime.datetime.today().strftime('%Y-%m-%d')
                    dummy_df = pd.DataFrame({'trade_date': [dummy_date], 'concentration_%': [0], 'net_buy': [0]})
                    render_broker_dashboard(target_stock, display_name, df_raw_all, dummy_df)
                    st.warning("⚠️ 查無此檔股票的近期集中度資料。")
            else:
                st.warning(f"⚠️ 資料庫中找不到 {display_name} 的交易紀錄。")
        else:
            st.warning("⚠️ 找不到資料。滿血版資料庫可能是空的。")
