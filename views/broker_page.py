# views/broker_page.py
import streamlit as st
import pandas as pd
from utils.data_utils import calculate_chip_concentration

# 🌟 1. 滿血版 Parquet 讀取引擎
@st.cache_data(show_spinner=False, ttl=3600)
def load_full_blood_broker_history():
    remote_parquet_url = "https://huggingface.co/datasets/goodinfo3583/tw-broker-parquet/resolve/main/broker_summary_master.parquet"
    try:
        columns_to_read = ['日期', '股票代號', '券商代號', '券商名稱', '買賣超股數', '總買進股數', '總買進金額', '買賣超金額']
        df = pd.read_parquet(remote_parquet_url, columns=columns_to_read)
        df = df.rename(columns={'日期': 'trade_date', '股票代號': 'stock_code', '券商名稱': 'broker_name', '券商代號': 'broker', '買賣超股數': 'net_vol_shares'})
        df['stock_code'] = df['stock_code'].astype('category')
        df['broker'] = df['broker'].astype('category')
        df['broker_name'] = df['broker_name'].astype('category')
        df['trade_date'] = df['trade_date'].dt.strftime('%Y-%m-%d').astype('category')
        df['net_vol'] = df['net_vol_shares'] / 1000
        df['side'] = df['net_vol'].apply(lambda x: 'buy' if x > 0 else 'sell').astype('category')
        return df
    except Exception as e:
        st.error(f"載入滿血版明細失敗: {e}")
        return pd.DataFrame()
    
def sync_b8_data():
    if 'b8_summary_df' in st.session_state: return
    try:
        df_raw = load_full_blood_broker_history()
        if df_raw.empty: return
        broker_col = next((c for c in ['broker_name', 'broker', '券商名稱', '券商', 'name'] if c in df_raw.columns), None)
        if not broker_col: return
        df_light = df_raw[['trade_date', 'stock_code', broker_col, 'net_vol', 'side']].copy()
        df_light['signed_vol'] = df_light['net_vol'].abs()
        df_light.loc[df_light['side'] == 'sell', 'signed_vol'] = -df_light['signed_vol']

        valid_dates = df_light['trade_date'].dropna().unique()
        all_dates = sorted(valid_dates, reverse=True)
        if not all_dates: return
        latest_date = all_dates[0]

        latest_buys = df_light[(df_light['trade_date'] == latest_date) & (df_light['signed_vol'] > 0)]
        day_candidates = latest_buys[['stock_code', broker_col]].drop_duplicates()
        df_day_filtered = pd.merge(df_light, day_candidates, on=['stock_code', broker_col], how='inner')

        scan_pivot = df_day_filtered.pivot_table(index=['stock_code', broker_col], columns='trade_date', values='signed_vol', aggfunc='sum')
        def calc_daily(row):
            streak = 0
            for c in all_dates:
                if pd.isna(row.get(c, 0)) or row.get(c, 0) <= 0: break
                streak += 1
            return streak
            
        scan_pivot['連買日數'] = scan_pivot.apply(calc_daily, axis=1)
        valid_sum_cols = [c for c in all_dates[:20] if c in scan_pivot.columns]
        scan_pivot['近期買超總張數'] = scan_pivot[valid_sum_cols].sum(axis=1)

        df_week = df_light.dropna(subset=['trade_date']).copy()
        df_week['date_dt'] = pd.to_datetime(df_week['trade_date'], errors='coerce')
        df_week = df_week.dropna(subset=['date_dt'])
        df_week['year_week'] = df_week['date_dt'].dt.strftime('%Y-%W')
        weekly_raw = df_week.groupby(['stock_code', broker_col, 'year_week'], as_index=False)['signed_vol'].sum()
        all_weeks = sorted(weekly_raw['year_week'].unique(), reverse=True)
        if not all_weeks: return
        
        latest_week_buys = weekly_raw[(weekly_raw['year_week'] == all_weeks[0]) & (weekly_raw['signed_vol'] > 0)]
        week_candidates = latest_week_buys[['stock_code', broker_col]].drop_duplicates()
        df_week_filtered = pd.merge(weekly_raw, week_candidates, on=['stock_code', broker_col], how='inner')
        weekly_sum = df_week_filtered.pivot_table(index=['stock_code', broker_col], columns='year_week', values='signed_vol', aggfunc='sum')
        def calc_weekly(row):
            streak = 0
            for c in all_weeks:
                if pd.isna(row.get(c, 0)) or row.get(c, 0) <= 0: break
                streak += 1
            return streak
            
        weekly_sum['連買週數'] = weekly_sum.apply(calc_weekly, axis=1)
        df_day = scan_pivot.reset_index()[['stock_code', broker_col, '連買日數', '近期買超總張數']]
        df_wk = weekly_sum.reset_index()[['stock_code', broker_col, '連買週數']]
        final_b8 = pd.merge(df_day, df_wk, on=['stock_code', broker_col], how='outer').fillna(0)
        stock_summary = final_b8.groupby('stock_code').agg({'連買日數': 'max', '連買週數': 'max', '近期買超總張數': 'max'}).reset_index().rename(columns={'stock_code': '統一代號'})

        st.session_state['b8_summary_df'] = stock_summary
        st.session_state['b8_latest_date'] = latest_date
        import gc; del df_raw, df_light, scan_pivot, weekly_sum, final_b8; gc.collect()
    except Exception as e:
        print(f"B8 背景載入失敗: {e}")

# 🌟 2. 標籤與共用格式函數
BROKER_TAGS = {"凱基台北": "⚠️隔日沖", "統一城中": "⚠️隔日沖", "元大土城永寧": "⚠️隔日沖", "美林": "🌐外資", "台灣摩根士丹利": "🌐外資"}
def apply_broker_tags(broker_name):
    name_str = str(broker_name)
    tag = BROKER_TAGS.get(name_str, "")
    return f"{name_str} {tag}" if tag else name_str

def fmt_float(val): return "{:,.1f}".format(val) if isinstance(val, (float, int)) and not pd.isna(val) else "-"
def fmt_int(val): return "{:,.0f}".format(val) if isinstance(val, (float, int)) and not pd.isna(val) else "-"

# 🌟 3. 個股儀表板 Fragment
@st.fragment
def render_broker_dashboard(target_stock, display_name, df_raw_all, df_trend):
    latest_data = df_trend.iloc[-1]
    st.metric(label=f"{latest_data['trade_date']} 最新券商分點集中度", value=f"{latest_data['concentration_%']}%", delta=f"淨買超 {latest_data['net_buy']:,} 張")
    
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    st.subheader(f"📊 {display_name} 籌碼與股價共振走勢")
    
    df_trend_plot = df_trend.copy().dropna(subset=['stock_price'])
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    colors = ['#FF4B4B' if val > 0 else '#00E272' for val in df_trend_plot['concentration_%']]
    fig_trend.add_trace(go.Bar(x=df_trend_plot['trade_date'], y=df_trend_plot['concentration_%'], marker_color=colors, name='單日集中度', opacity=0.4), secondary_y=True)
    
    if '5日集中度(%)' in df_trend_plot.columns: fig_trend.add_trace(go.Scatter(x=df_trend_plot['trade_date'], y=df_trend_plot['5日集中度(%)'], mode='lines', line=dict(color='#FFD700', width=2), name='5日集中度'), secondary_y=True)
    if '10日集中度(%)' in df_trend_plot.columns: fig_trend.add_trace(go.Scatter(x=df_trend_plot['trade_date'], y=df_trend_plot['10日集中度(%)'], mode='lines', line=dict(color='#FF8C00', width=1.5, dash='dot'), name='10日集中度'), secondary_y=True)
    if '20日集中度(%)' in df_trend_plot.columns: fig_trend.add_trace(go.Scatter(x=df_trend_plot['trade_date'], y=df_trend_plot['20日集中度(%)'], mode='lines', line=dict(color='#FF00FF', width=1.5, dash='dash'), name='20日集中度'), secondary_y=True)
    fig_trend.add_trace(go.Scatter(x=df_trend_plot['trade_date'], y=df_trend_plot['stock_price'], mode='lines+markers', line=dict(color='#38bdf8', width=2), name='市場均價(股價)'), secondary_y=False)
    
    stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
    broker_col = next((c for c in ['broker_name', 'broker', '券商名稱', '券商', 'name'] if c in stock_raw.columns), None)
    if not stock_raw.empty and broker_col:
        recent_20_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)[:20]
        recent_20_raw = stock_raw[stock_raw['trade_date'].isin(recent_20_dates)]
        top_broker_agg = recent_20_raw.groupby(broker_col).agg(淨買張數=('net_vol', 'sum'), 總買進金額=('總買進金額', 'sum'), 總買進股數=('總買進股數', 'sum')).sort_values('淨買張數', ascending=False)
        if not top_broker_agg.empty and top_broker_agg.iloc[0]['淨買張數'] > 0:
            top1_name = top_broker_agg.index[0]
            top1_cost = round(top_broker_agg.iloc[0]['總買進金額'] / top_broker_agg.iloc[0]['總買進股數'], 2)
            fig_trend.add_hline(y=top1_cost, line_color="#FF4B4B", line_width=1.5, line_dash="dash", annotation_text=f"🚩 最大主力 ({top1_name}) 防守成本: {top1_cost}元", annotation_position="bottom right", annotation_font=dict(color="#FF4B4B"), secondary_y=False)

    fig_trend.update_layout(
        height=400, template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(type='category', tickmode='array', tickvals=df_trend_plot['trade_date'], ticktext=df_trend_plot['trade_date'].str.slice(5, 10), tickangle=45)
    )
    fig_trend.update_yaxes(title_text="<b>股價 (元)</b>", secondary_y=False, gridcolor='#334155')
    fig_trend.update_yaxes(title_text="<b>集中度 (%)</b>", secondary_y=True, showgrid=False)
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
    
    with st.expander("📅 展開查看：近 60 日集中度與淨買超歷史表", expanded=False):
        df_trend_disp = df_trend.sort_values('trade_date', ascending=False).head(60).copy()[['trade_date', 'net_buy', 'concentration_%']]
        df_trend_disp.columns = ['交易日期', '淨買超(張)', '集中度(%)']
        st.dataframe(df_trend_disp.style.format({'淨買超(張)': fmt_float, '集中度(%)': "{:.2f}"}), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(f"🔍 {display_name} 券商分點進出明細")
    if broker_col is None: return st.error("⚠️ 無法在資料庫中找到「券商名稱」欄位！")
    available_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)
    tab1, tab2, tab3 = st.tabs(["🔹 單日進出明細", "🔹 區間囤貨 (近60日)", "🔹 歷史進出 (近30日)"])
    
    with tab1:
        selected_date = st.selectbox("請選擇要查看的交易日期：", available_dates, key="daily_date_sel")
        daily_raw = stock_raw[stock_raw['trade_date'] == selected_date]
        col_buy, col_sell = st.columns(2)
        
        def format_daily_table(df, is_buy):
            if df.empty: return None
            df = df.copy().drop_duplicates(subset=[broker_col])
            if not is_buy: 
                df['net_vol'] = df['net_vol'].abs()
                if '買賣超金額' in df.columns: df['買賣超金額'] = df['買賣超金額'].abs()
            df = df.sort_values('net_vol', ascending=False).head(15)
            df['均價'] = (df['總買進金額'] / df['總買進股數']).fillna(0).round(2)
            if not is_buy: df['均價'] = (df['買賣超金額'].abs() / (df['net_vol']*1000)).fillna(0).round(2)
            df[broker_col] = df[broker_col].apply(apply_broker_tags)
            
            if '買賣超金額' in df.columns:
                df['金額(萬)'] = (df['買賣超金額'] / 10000).round(0)
                df = df[[broker_col, 'net_vol', '均價', '金額(萬)']]
                df.columns = ['券商名稱', '張數', '均價', '金額(萬)']
                return df.style.format({'張數': fmt_float, '均價': "{:.2f}", '金額(萬)': fmt_int})
            else:
                df = df[[broker_col, 'net_vol', '均價']]
                df.columns = ['券商名稱', '張數', '均價']
                return df.style.format({'張數': fmt_float, '均價': "{:.2f}"})

        with col_buy:
            st.markdown("##### 🔴 淨買超前 15 大分點")
            styled_buy = format_daily_table(daily_raw[daily_raw['side'] == 'buy'], True)
            if styled_buy is not None: st.dataframe(styled_buy, use_container_width=True, hide_index=True)
            else: st.write("當日無資料")
            
        with col_sell:
            st.markdown("##### 🟢 淨賣超前 15 大分點")
            styled_sell = format_daily_table(daily_raw[daily_raw['side'] == 'sell'], False)
            if styled_sell is not None: st.dataframe(styled_sell, use_container_width=True, hide_index=True)
            else: st.write("當日無資料")

    with tab2:
        st.markdown("##### 🕵️‍♂️ 誰在拿真金白銀連續吃貨？")
        recent_raw = stock_raw[stock_raw['trade_date'].isin(available_dates[:60])].copy()
        hoard_df = recent_raw.groupby(broker_col).agg(區間淨買超張數=('net_vol', 'sum'), 區間總買進股數=('總買進股數', 'sum'), 區間總買進金額=('總買進金額', 'sum'), 區間淨買賣金額=('買賣超金額', 'sum')).reset_index()
        hoard_df['均價'] = (hoard_df['區間總買進金額'] / hoard_df['區間總買進股數']).fillna(0).round(2)
        hoard_df['斥資(億)'] = (hoard_df['區間淨買賣金額'] / 100000000).round(2)
        hoard_df[broker_col] = hoard_df[broker_col].apply(apply_broker_tags)
        
        col_hoard, col_dump = st.columns(2)
        with col_hoard:
            st.markdown("##### 📈 近 60 日囤貨分點 (斥資破億榜)")
            hoarders = hoard_df[hoard_df['區間淨買超張數'] > 0].sort_values('斥資(億)', ascending=False)
            if not hoarders.empty:
                hoarders.columns = ['券商名稱', '淨買超(張)', '總買(股)', '總買(元)', '淨買(元)', '均價', '斥資(億)']
                styled_hoard = hoarders[['券商名稱', '淨買超(張)', '均價', '斥資(億)']].style.format({'淨買超(張)': fmt_float, '均價': "{:.2f}", '斥資(億)': "{:.2f}"})
                try: styled_hoard = styled_hoard.background_gradient(subset=['斥資(億)'], cmap='Reds')
                except: pass
                st.dataframe(styled_hoard, use_container_width=True, hide_index=True)
            else: st.write("無明顯囤貨")
                
        with col_dump:
            st.markdown("##### 📉 近 60 日倒貨分點")
            dumpers = hoard_df[hoard_df['區間淨買超張數'] < 0].sort_values('斥資(億)', ascending=True).copy()
            if not dumpers.empty:
                dumpers['斥資(億)'] = dumpers['斥資(億)'].abs()
                dumpers['區間淨買超張數'] = dumpers['區間淨買超張數'].abs()
                dumpers.columns = ['券商名稱', '淨賣超(張)', '總買(股)', '總買(元)', '淨賣(元)', '均價', '提款(億)']
                styled_dump = dumpers[['券商名稱', '淨賣超(張)', '均價', '提款(億)']].style.format({'淨賣超(張)': fmt_float, '均價': "{:.2f}", '提款(億)': "{:.2f}"})
                try: styled_dump = styled_dump.background_gradient(subset=['提款(億)'], cmap='Greens')
                except: pass
                st.dataframe(styled_dump, use_container_width=True, hide_index=True)
            else: st.write("無明顯倒貨")

    with tab3:
        st.markdown("##### 🗺️ 分點淨買賣力道")
        st.markdown("橫列為各分點，縱欄顯示**近 30 個交易日**。數字為買賣超張數，小數點代表零股交易，`-0.0` 表示賣出數量小於一張。")
        all_matrix_raw = stock_raw.copy()
        if not all_matrix_raw.empty:
            all_matrix_raw['signed_vol'] = all_matrix_raw.apply(lambda x: abs(x['net_vol']) if x['side'] == 'buy' else -abs(x['net_vol']), axis=1)
            all_matrix_raw['date_dt'] = pd.to_datetime(all_matrix_raw['trade_date'])
            all_matrix_raw['year_week'] = all_matrix_raw['date_dt'].dt.strftime('%Y-%W')
            weekly_sum = all_matrix_raw.groupby([broker_col, 'year_week'])['signed_vol'].sum().unstack(fill_value=0)
            week_cols = sorted(weekly_sum.columns, reverse=True)
            
            full_pivot = all_matrix_raw.pivot_table(index=broker_col, columns='trade_date', values='signed_vol', aggfunc='sum')
            all_dates_sorted = sorted(full_pivot.columns, reverse=True)
            display_dates = all_dates_sorted[:30]
            pivot_df = full_pivot[display_dates].copy()
            pivot_df['區間累計'] = pivot_df.sum(axis=1)
            pivot_df = pivot_df.sort_values('區間累計', ascending=False)
            
            def calc_daily_streak(row_name):
                if row_name not in full_pivot.index: return "-"
                row = full_pivot.loc[row_name]
                streak = 0; sign = None
                for c in all_dates_sorted:
                    if pd.isna(row.get(c, 0)) or row.get(c, 0) == 0: break  
                    current_sign = 1 if row.get(c, 0) > 0 else -1
                    if sign is None: sign = current_sign; streak = sign
                    elif sign == current_sign: streak += sign
                    else: break  
                if streak > 0: return f"連買 {streak} 日"
                elif streak < 0: return f"連賣 {-streak} 日"
                else: return "-"
                
            pivot_df['日連買動態'] = pivot_df.index.to_series().apply(calc_daily_streak)
            def calc_weekly_streak(broker_name):
                if weekly_sum.empty or broker_name not in weekly_sum.index: return "-"
                row = weekly_sum.loc[broker_name]
                streak = 0; sign = None
                for c in week_cols:
                    if pd.isna(row.get(c, 0)) or row.get(c, 0) == 0: break
                    current_sign = 1 if row.get(c, 0) > 0 else -1
                    if sign is None: sign = current_sign; streak = sign
                    elif sign == current_sign: streak += sign
                    else: break
                if streak > 0: return f"連買 {streak} 週"
                elif streak < 0: return f"連賣 {-streak} 週"
                else: return "-"
                
            pivot_df['週連買動態'] = pivot_df.index.to_series().apply(calc_weekly_streak)
            pivot_df[display_dates] = pivot_df[display_dates].fillna("-")
            pivot_df.index = pivot_df.index.to_series().apply(apply_broker_tags)
            pivot_df.index.name = "券商分點"
            
            cols = ['日連買動態', '週連買動態', '區間累計'] + display_dates
            pivot_df = pivot_df[cols]
            sort_option = st.radio("🔍 排序依據：", ["依區間累計排序(預設)", "依連買日數排序", "依連買週數排序"], horizontal=True, key=f"sort_radio_{target_stock}")
            
            def extract_streak_num(val):
                if isinstance(val, str) and "連買" in val:
                    try: return int(''.join(filter(str.isdigit, val)))
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

            if hasattr(pivot_df.style, 'map'): styled_pivot = pivot_df.style.map(color_net_vol).format(fmt_float)
            else: styled_pivot = pivot_df.style.applymap(color_net_vol).format(fmt_float)
            st.dataframe(styled_pivot, use_container_width=True)
        else: st.write("無足夠資料產出")

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

    st.markdown("觀察前 15 大分點買賣力道相抵後的淨流向，追蹤籌碼集中度連續性與券商進出。(已加入小數點優化與冷門股濾網)")
    
    with st.expander("🌍 全市場連買分點快搜 (尋找主力連續吃貨標的)", expanded=False):
        st.markdown("此功能將掃描資料庫中所有股票，找出當前處於「連續買超」或「重金砸盤」狀態的特定分點與個股。", unsafe_allow_html=True)

        col_mode, col_filter = st.columns([3, 1])
        with col_mode:
            scan_mode = st.radio(
                "請選擇全市場排行方式：", 
                ["依日連買排行", "依週連買排行", "依近期買超張數排行", "依單一分點買超金額排行", "依單一股票買超金額排行", "依集中度斜率(Δ)排行", "依股價乖離率(吃豆腐)排行"], 
                horizontal=True, key="global_broker_scan_radio"
            )
        with col_filter:
            # 🚀 新增：成交量過濾器，預設排除近20日總成交額低於 1 億元的水餃股
            min_amount_filter = st.number_input("排除20日總成交額低於(億元)的冷門股：", min_value=0, value=1, step=1)
        
        c_scan, c_clear = st.columns([3, 1])
        with c_scan:
            if st.button("🚀 開始全市場掃描", use_container_width=True, type="primary"):
                with st.spinner("正在進行全市場運算 (包含動態標籤判定)，請稍候..."):
                    df_raw_all = load_full_blood_broker_history()
                    if not df_raw_all.empty:
                        broker_col = next((c for c in ['broker_name', 'broker', '券商名稱', '券商', 'name'] if c in df_raw_all.columns), None)
                        if broker_col:
                            scan_df = df_raw_all[['trade_date', 'stock_code', broker_col, 'net_vol', '總買進股數', '總買進金額', '買賣超金額']].copy()
                            valid_dates = scan_df['trade_date'].dropna().unique()
                            all_dates = sorted(valid_dates, reverse=True)
                            
                            if all_dates:
                                latest_date = all_dates[0]
                                df_20d = scan_df[scan_df['trade_date'].isin(all_dates[:20])]
                                
                                # 🚀 執行冷門股過濾
                                market_20d = df_20d.groupby('stock_code')['總買進金額'].sum().reset_index()
                                valid_stocks = market_20d[market_20d['總買進金額'] >= (min_amount_filter * 100000000)]['stock_code']
                                df_20d = df_20d[df_20d['stock_code'].isin(valid_stocks)]
                                scan_df = scan_df[scan_df['stock_code'].isin(valid_stocks)]
                                
                                # 💡 1. 集中度斜率 (Δ Concentration) 掃描
                                if scan_mode == "依集中度斜率(Δ)排行":
                                    daily_vol = df_20d.groupby(['trade_date', 'stock_code'])['總買進股數'].sum() / 1000
                                    df_buy = df_20d[df_20d['net_vol'] > 0]
                                    df_sell = df_20d[df_20d['net_vol'] < 0]

                                    top15_buy = df_buy.sort_values(['trade_date', 'stock_code', 'net_vol'], ascending=[True, True, False]).groupby(['trade_date', 'stock_code']).head(15).groupby(['trade_date', 'stock_code'])['net_vol'].sum()
                                    top15_sell = df_sell.sort_values(['trade_date', 'stock_code', 'net_vol'], ascending=[True, True, True]).groupby(['trade_date', 'stock_code']).head(15).groupby(['trade_date', 'stock_code'])['net_vol'].sum()

                                    daily_net = top15_buy.fillna(0) - top15_sell.abs().fillna(0)
                                    conc_df = pd.DataFrame({'net_buy': daily_net, 'vol': daily_vol}).reset_index().sort_values('trade_date')

                                    conc_df['5d_net'] = conc_df.groupby('stock_code')['net_buy'].transform(lambda x: x.rolling(5, min_periods=1).sum())
                                    conc_df['5d_vol'] = conc_df.groupby('stock_code')['vol'].transform(lambda x: x.rolling(5, min_periods=1).sum())
                                    conc_df['20d_net'] = conc_df.groupby('stock_code')['net_buy'].transform(lambda x: x.rolling(20, min_periods=1).sum())
                                    conc_df['20d_vol'] = conc_df.groupby('stock_code')['vol'].transform(lambda x: x.rolling(20, min_periods=1).sum())

                                    conc_df['5日集中度(%)'] = (conc_df['5d_net'] / conc_df['5d_vol'] * 100).fillna(0).round(2)
                                    conc_df['20日集中度(%)'] = (conc_df['20d_net'] / conc_df['20d_vol'] * 100).fillna(0).round(2)
                                    conc_df['Δ集中度(5-20日)'] = (conc_df['5日集中度(%)'] - conc_df['20日集中度(%)']).round(2)

                                    result_df = conc_df[conc_df['trade_date'] == latest_date].copy()

                                    # 計算股價趨勢 (最新股價 vs 20日均價) 供動態標籤使用
                                    market_20d_amt = df_20d.groupby('stock_code').agg(amt_20d=('總買進金額', 'sum'), sh_20d=('總買進股數', 'sum')).reset_index()
                                    market_20d_amt['vwap_20d'] = (market_20d_amt['amt_20d'] / market_20d_amt['sh_20d']).fillna(0)
                                    
                                    latest_price_df = df_20d[df_20d['trade_date'] == latest_date].groupby('stock_code').agg(amt_1d=('總買進金額', 'sum'), sh_1d=('總買進股數', 'sum')).reset_index()
                                    latest_price_df['最新股價'] = (latest_price_df['amt_1d'] / latest_price_df['sh_1d']).fillna(0).round(2)
                                    
                                    price_trend = pd.merge(market_20d_amt[['stock_code', 'vwap_20d']], latest_price_df[['stock_code', '最新股價']], on='stock_code')
                                    price_trend['price_diff_%'] = ((price_trend['最新股價'] - price_trend['vwap_20d']) / price_trend['vwap_20d'] * 100).fillna(0)

                                    result_df = pd.merge(result_df, price_trend, on='stock_code')

                                    def get_status(row):
                                        d_conc = row['Δ集中度(5-20日)']
                                        p_diff = row['price_diff_%']
                                        if d_conc >= 3 and p_diff <= 3: return "🌟 偷偷吸籌 (看好)"
                                        if d_conc >= 3 and p_diff > 3: return "🚀 量價齊揚 (多頭)"
                                        if d_conc <= -3 and p_diff > 3: return "⚠️ 逢高出貨 (危險)"
                                        if d_conc <= -3 and p_diff <= 3: return "🛑 籌碼渙散 (弱勢)"
                                        if d_conc > 0: return "↗️ 偏多"
                                        return "➡️ 盤整/偏空"

                                    result_df['籌碼動態'] = result_df.apply(get_status, axis=1)
                                    result_df = result_df[result_df['vol'] > 0].sort_values('Δ集中度(5-20日)', ascending=False)
                                    result_df = result_df[['stock_code', '5日集中度(%)', '20日集中度(%)', 'Δ集中度(5-20日)', '最新股價', '籌碼動態']]

                                # 💡 2. 股價乖離率 (吃豆腐) 掃描
                                elif scan_mode == "依股價乖離率(吃豆腐)排行":
                                    agg_20d = df_20d.groupby(['stock_code', broker_col]).agg(net_vol=('net_vol', 'sum'), buy_amt=('總買進金額', 'sum'), buy_shares=('總買進股數', 'sum')).reset_index()
                                    latest_price = (df_20d[df_20d['trade_date'] == latest_date].groupby('stock_code')['總買進金額'].sum() / df_20d[df_20d['trade_date'] == latest_date].groupby('stock_code')['總買進股數'].sum()).fillna(0).round(2)
                                    
                                    agg_20d = agg_20d[agg_20d['net_vol'] > 0]
                                    top_broker = agg_20d.sort_values(['stock_code', 'net_vol'], ascending=[True, False]).groupby('stock_code').head(1)
                                    top_broker['主力成本'] = (top_broker['buy_amt'] / top_broker['buy_shares']).fillna(0).round(2)
                                    
                                    dev_df = pd.merge(top_broker, latest_price.rename('最新股價'), on='stock_code')
                                    dev_df['乖離率(%)'] = ((dev_df['最新股價'] - dev_df['主力成本']) / dev_df['主力成本'] * 100).round(2)
                                    dev_df['絕對乖離'] = dev_df['乖離率(%)'].abs()
                                    
                                    def get_dev_status(row):
                                        dev = row['乖離率(%)']
                                        if abs(dev) <= 2: return "🎯 成本保衛戰 (極佳吃豆腐點)"
                                        if 2 < dev <= 5: return "🚀 脫離成本區"
                                        if dev > 5: return "🔥 主力已拉開獲利 (追高風險)"
                                        if dev < -2: return "🩸 主力套牢中 (防守失敗)"
                                        return "-"

                                    dev_df['吃豆腐動態'] = dev_df.apply(get_dev_status, axis=1)
                                    result_df = dev_df.sort_values('絕對乖離', ascending=True)
                                    result_df = result_df[['stock_code', broker_col, '主力成本', '最新股價', '乖離率(%)', 'net_vol', '吃豆腐動態']].rename(columns={'net_vol': '主力囤貨(張)'})

                                # 其餘原有的掃描功能
                                else:
                                    agg_20d = df_20d.groupby(['stock_code', broker_col]).agg(
                                        近期買超總張數=('net_vol', 'sum'), 區間總買進股數=('總買進股數', 'sum'),
                                        區間總買進金額=('總買進金額', 'sum'), 區間買賣超金額=('買賣超金額', 'sum')
                                    ).reset_index()
                                    
                                    if scan_mode == "依單一分點買超金額排行":
                                        result_df = agg_20d[agg_20d['區間買賣超金額'] > 0].copy()
                                        result_df['均價'] = (result_df['區間總買進金額'] / result_df['區間總買進股數']).fillna(0).round(2)
                                        result_df['斥資(億)'] = (result_df['區間買賣超金額'] / 100000000).round(2)
                                        result_df = result_df.sort_values('斥資(億)', ascending=False)[['stock_code', broker_col, '近期買超總張數', '均價', '斥資(億)']]

                                    elif scan_mode == "依單一股票買超金額排行":
                                        buy_only_20d = agg_20d[agg_20d['區間買賣超金額'] > 0].copy()
                                        stock_agg = buy_only_20d.groupby('stock_code').agg(
                                            近期買超總張數=('近期買超總張數', 'sum'), 區間總買進股數=('區間總買進股數', 'sum'),
                                            區間總買進金額=('區間總買進金額', 'sum'), 區間買賣超金額=('區間買賣超金額', 'sum'),
                                            參與大戶=(broker_col, lambda x: ', '.join(x.dropna().unique()[:5]))
                                        ).reset_index()
                                        stock_agg['均價'] = (stock_agg['區間總買進金額'] / stock_agg['區間總買進股數']).fillna(0).round(2)
                                        stock_agg['斥資(億)'] = (stock_agg['區間買賣超金額'] / 100000000).round(2)
                                        result_df = stock_agg.sort_values('斥資(億)', ascending=False)[['stock_code', '參與大戶', '近期買超總張數', '均價', '斥資(億)']].rename(columns={'參與大戶': broker_col})

                                    elif scan_mode in ["依日連買排行", "依近期買超張數排行"]:
                                        latest_buys = scan_df[(scan_df['trade_date'] == latest_date) & (scan_df['net_vol'] > 0)]
                                        df_candidates = pd.merge(scan_df, latest_buys[['stock_code', broker_col]].drop_duplicates(), on=['stock_code', broker_col], how='inner')
                                        scan_pivot = df_candidates.pivot_table(index=['stock_code', broker_col], columns='trade_date', values='net_vol', aggfunc='sum')
                                        
                                        def calc_global_daily_streak(row):
                                            streak = 0
                                            for c in all_dates:
                                                if pd.isna(row.get(c, 0)) or row.get(c, 0) <= 0: break
                                                streak += 1
                                            return streak
                                            
                                        scan_pivot['連買日數'] = scan_pivot.apply(calc_global_daily_streak, axis=1)
                                        result_df = pd.merge(scan_pivot.reset_index()[['stock_code', broker_col, '連買日數']], agg_20d, on=['stock_code', broker_col])
                                        result_df = result_df[result_df['連買日數'] >= 1].copy() 
                                        result_df['均價'] = (result_df['區間總買進金額'] / result_df['區間總買進股數']).fillna(0).round(2)
                                        result_df['斥資(億)'] = (result_df['區間買賣超金額'] / 100000000).round(2)
                                        if scan_mode == "依日連買排行": result_df = result_df[result_df['連買日數'] >= 2].sort_values(['連買日數', '近期買超總張數'], ascending=[False, False])
                                        else: result_df = result_df[result_df['近期買超總張數'] > 0].sort_values(['近期買超總張數', '連買日數'], ascending=[False, False])
                                        result_df = result_df[['stock_code', broker_col, '連買日數', '近期買超總張數', '均價', '斥資(億)']]

                                    else:
                                        scan_df['date_dt'] = pd.to_datetime(scan_df['trade_date'], errors='coerce')
                                        scan_df = scan_df.dropna(subset=['date_dt'])
                                        scan_df['year_week'] = scan_df['date_dt'].dt.strftime('%Y-%W')
                                        weekly_raw = scan_df.groupby(['stock_code', broker_col, 'year_week'], as_index=False)['net_vol'].sum()
                                        all_weeks = sorted(weekly_raw['year_week'].unique(), reverse=True)
                                        if all_weeks:
                                            df_candidates_wk = pd.merge(weekly_raw, weekly_raw[(weekly_raw['year_week'] == all_weeks[0]) & (weekly_raw['net_vol'] > 0)][['stock_code', broker_col]].drop_duplicates(), on=['stock_code', broker_col], how='inner')
                                            weekly_sum = df_candidates_wk.pivot_table(index=['stock_code', broker_col], columns='year_week', values='net_vol', aggfunc='sum')
                                            def calc_global_weekly_streak(row):
                                                streak = 0
                                                for c in all_weeks:
                                                    if pd.isna(row.get(c, 0)) or row.get(c, 0) <= 0: break
                                                    streak += 1
                                                return streak
                                            weekly_sum['連買週數'] = weekly_sum.apply(calc_global_weekly_streak, axis=1)
                                            df_candidates_4w = pd.merge(scan_df, weekly_raw[(weekly_raw['year_week'] == all_weeks[0]) & (weekly_raw['net_vol'] > 0)][['stock_code', broker_col]].drop_duplicates(), on=['stock_code', broker_col], how='inner')
                                            df_candidates_4w = df_candidates_4w[df_candidates_4w['year_week'].isin(all_weeks[:4])]
                                            agg_4w = df_candidates_4w.groupby(['stock_code', broker_col]).agg(
                                                近期買超總張數=('net_vol', 'sum'), 區間總買進股數=('總買進股數', 'sum'), 區間總買進金額=('總買進金額', 'sum'), 區間買賣超金額=('買賣超金額', 'sum')
                                            ).reset_index()
                                            result_df = pd.merge(weekly_sum.reset_index()[['stock_code', broker_col, '連買週數']], agg_4w, on=['stock_code', broker_col])
                                            result_df = result_df[result_df['連買週數'] >= 2].sort_values(['連買週數', '近期買超總張數'], ascending=[False, False])
                                            result_df['均價'] = (result_df['區間總買進金額'] / result_df['區間總買進股數']).fillna(0).round(2)
                                            result_df['斥資(億)'] = (result_df['區間買賣超金額'] / 100000000).round(2)
                                            result_df = result_df[['stock_code', broker_col, '連買週數', '近期買超總張數', '均價', '斥資(億)']]

                                # 🚀 統一名稱轉換與欄位對齊 (修復遺失股票名稱的Bug)
                                if STOCK_DICT and 'stock_code' in result_df.columns:
                                    result_df['股票名稱'] = result_df['stock_code'].astype(str).apply(
                                        lambda x: STOCK_DICT.get(x, {}).get('name', '-')
                                    )
                                    if '股票名稱' in result_df.columns:
                                        cols = result_df.columns.tolist()
                                        cols.insert(1, cols.pop(cols.index('股票名稱')))
                                        result_df = result_df[cols]
                                
                                if scan_mode == "依單一股票買超金額排行": result_df.rename(columns={'stock_code': '股票代號', broker_col: '參與大戶(前5大)'}, inplace=True)
                                elif scan_mode == "依集中度斜率(Δ)排行": result_df.rename(columns={'stock_code': '股票代號'}, inplace=True)
                                elif scan_mode == "依股價乖離率(吃豆腐)排行": result_df.rename(columns={'stock_code': '股票代號', broker_col: '最大主力分點'}, inplace=True)
                                else: result_df.rename(columns={'stock_code': '股票代號', broker_col: '券商分點'}, inplace=True)
                                    
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
                st.success(f"🎯 掃描結果 ({cached_mode})：共發現 {len(cached_res)} 組特徵。")
                
                # 🚀 修復所有小數點：嚴格控制為兩位數或千分位
                format_dict = {
                    '近期買超總張數': "{:,.1f}", '均價': "{:.2f}", '斥資(億)': "{:.2f}", '主力囤貨(張)': "{:,.1f}",
                    '5日集中度(%)': "{:.2f}", '20日集中度(%)': "{:.2f}", 'Δ集中度(5-20日)': "{:.2f}", 
                    '主力成本': "{:.2f}", '最新股價': "{:.2f}", '乖離率(%)': "{:.2f}"
                }
                styled_res = cached_res.head(100).style.format(format_dict)
                
                if '斥資(億)' in cached_res.columns:
                    try: styled_res = styled_res.background_gradient(subset=['斥資(億)'], cmap='Reds')
                    except: pass
                elif '乖離率(%)' in cached_res.columns:
                    try: styled_res = styled_res.background_gradient(subset=['乖離率(%)'], cmap='coolwarm_r') # 越近 0 越紅
                    except: pass
                elif 'Δ集中度(5-20日)' in cached_res.columns:
                    try: styled_res = styled_res.background_gradient(subset=['Δ集中度(5-20日)'], cmap='Reds')
                    except: pass
                    
                st.dataframe(styled_res, use_container_width=True, hide_index=True)
            else:
                st.info("目前市場上無明顯的分點特徵。")

    # 🌟 2. 個股查詢器 🌟
    stock_options = []
    if STOCK_DICT:
        unique_options = {f"{v['id']} {v['name']}" for v in STOCK_DICT.values() if len(str(v['id'])) <= 4}
        stock_options = sorted(list(unique_options))
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_stock_str = st.selectbox("請選擇要查詢的股票：", options=[""] + stock_options, index=0, key="broker_search_input")
          
    if selected_stock_str:
        target_stock = selected_stock_str.split(" ")[0].strip()
        display_name = selected_stock_str
        df_raw_all = load_full_blood_broker_history()
        if not df_raw_all.empty:
            stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
            if not stock_raw.empty:
                try: df_trend = calculate_chip_concentration(stock_raw)
                except Exception as e: df_trend = pd.DataFrame()
                if not df_trend.empty: render_broker_dashboard(target_stock, display_name, df_raw_all, df_trend)
                else:
                    import datetime
                    dummy_df = pd.DataFrame({'trade_date': [datetime.datetime.today().strftime('%Y-%m-%d')], 'concentration_%': [0], 'net_buy': [0]})
                    render_broker_dashboard(target_stock, display_name, df_raw_all, dummy_df)
                    st.warning("⚠️ 查無此檔股票的近期集中度資料。")
            else: st.warning(f"⚠️ 資料庫中找不到 {display_name} 的交易紀錄。")
        else: st.warning("⚠️ 找不到資料。滿血版資料庫可能是空的。")
