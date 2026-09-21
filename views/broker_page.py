#views/broker_page.py
import streamlit as st
import pandas as pd
import requests
import urllib.parse
from utils.data_utils import calculate_chip_concentration

# ==========================================
# ⚙️ 基礎設定 (改成 Hugging Face 遠端網址)
# ==========================================
HF_BASE_URL = "https://huggingface.co/datasets/goodinfo3583/tw-broker-parquet/resolve/main"

# 🌟 1. 滿血版 Parquet 讀取引擎 (保留供個股查詢使用)
@st.cache_data(show_spinner=False, ttl=3600)
def load_full_blood_broker_history():
    remote_parquet_url = f"{HF_BASE_URL}/broker_summary_master.parquet"
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

# 🌟 2. 標籤與共用格式函數
BROKER_TAGS = {"凱基台北": "⚠️隔日沖", "統一城中": "⚠️隔日沖", "元大土城永寧": "⚠️隔日沖", "美林": "🌐外資", "台灣摩根士丹利": "🌐外資"}
def apply_broker_tags(broker_name):
    name_str = str(broker_name)
    tag = BROKER_TAGS.get(name_str, "")
    return f"{name_str} {tag}" if tag else name_str

def fmt_float(val): 
    if isinstance(val, str): return val 
    return "{:,.1f}".format(val) if isinstance(val, (float, int)) and not pd.isna(val) else "-"

def fmt_int(val): 
    if isinstance(val, str): return val
    return "{:,.0f}".format(val) if isinstance(val, (float, int)) and not pd.isna(val) else "-"

# 🌟 3. 個股儀表板 Fragment (完全不變)
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
        st.markdown("橫列為各分點，縱欄顯示**近 30 個交易日**。數字為買賣超張數，`-0.0` 表示賣出數量小於一張。")
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
                    val = row.get(c, 0)
                    if pd.isna(val) or abs(val) < 0.01: break  
                    current_sign = 1 if val > 0 else -1
                    if sign is None: sign = current_sign; streak = sign
                    elif sign == current_sign: streak += sign
                    else: break  
                if streak > 0: return f"🔥 連買 {streak} 日"
                elif streak < 0: return f"🩸 連賣 {-streak} 日"
                else: return "-"
                
            pivot_df['日連買動態'] = pivot_df.index.to_series().apply(calc_daily_streak)
            
            def calc_weekly_streak(broker_name):
                if weekly_sum.empty or broker_name not in weekly_sum.index: return "-"
                row = weekly_sum.loc[broker_name]
                streak = 0; sign = None
                for c in week_cols:
                    val = row.get(c, 0)
                    if pd.isna(val) or abs(val) < 0.01: break
                    current_sign = 1 if val > 0 else -1
                    if sign is None: sign = current_sign; streak = sign
                    elif sign == current_sign: streak += sign
                    else: break
                if streak > 0: return f"🔥 連買 {streak} 週"
                elif streak < 0: return f"🩸 連賣 {-streak} 週"
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
                    elif v < -0.01: return 'color: #00E272;'
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
    df_raw_all = load_full_blood_broker_history()
    if not df_raw_all.empty:
        latest_db_date = df_raw_all['trade_date'].astype(str).max()
        st.caption(f"🟢 當前遠端資料庫最新日期：**{latest_db_date}**")
        
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(14,165,233,0.3) 50%, rgba(15,23,42,1) 100%); 
                border-top: 1px solid #38bdf8; border-bottom: 1px solid #38bdf8; padding: 15px 20px; 
                border-radius: 10px; text-align: center; box-shadow: 0px 0px 20px rgba(56, 189, 248, 0.2); margin-bottom: 20px;">
        <h2 style="color: #e0f2fe; margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(56, 189, 248, 0.8);">
            券商主力淨買力與集中度追蹤
        </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("觀察前 15 大分點買賣力道相抵後的淨流向，追蹤籌碼集中度連續性與券商進出。")
    
    # 🌟 1. 全市場掃描器 🌟 (改為讀取 Hugging Face)
    with st.expander("🌍 全市場連買分點快搜 (尋找主力連續吃貨標的)", expanded=False):
        st.markdown("此功能將掃描資料庫中所有股票，找出當前處於「連續買超」或「重金砸盤」狀態的特定分點與個股。", unsafe_allow_html=True)

        scan_mode = st.radio(
            "請選擇全市場排行方式 (資料由後台批次每日運算)：", 
            [
                "🌟 依主力(Top15)買超張數排行 (復刻三竹)",
                "依股價乖離率(吃豆腐)排行"
            ], 
            horizontal=True, key="global_broker_scan_radio"
        )
        
        if st.button("🚀 載入最新掃描結果", use_container_width=True, type="primary"):
            # 轉換檔名並進行 URL 編碼以處理中文網址
            safe_name = scan_mode.replace(" ", "_").replace("(", "").replace(")", "").replace("🌟", "").replace("/", "_")
            file_name = f"scan_{safe_name}.parquet"
            file_url = f"{HF_BASE_URL}/{urllib.parse.quote(file_name)}"
            
            try:
                with st.spinner("正在從 Hugging Face 抓取最新名單..."):
                    result_df = pd.read_parquet(file_url)
                
                # 統一名稱轉換
                if STOCK_DICT and '股票代號' in result_df.columns:
                    result_df['股票名稱'] = result_df['股票代號'].astype(str).apply(lambda x: STOCK_DICT.get(x, {}).get('name', '-'))
                    cols = result_df.columns.tolist()
                    if '股票名稱' in cols:
                        cols.insert(1, cols.pop(cols.index('股票名稱')))
                        result_df = result_df[cols]
                
                st.session_state['broker_global_scan_result'] = result_df
                st.session_state['broker_global_scan_mode'] = scan_mode
                st.success("✅ 瞬間讀取完畢！")
            except Exception as e:
                st.warning(f"⚠️ 找不到後台運算檔案，請確認已上傳至 Hugging Face: {e}")

        if 'broker_global_scan_result' in st.session_state:
            cached_res = st.session_state['broker_global_scan_result']
            if not cached_res.empty:
                format_dict = {
                    '近期買超總張數': "{:,.1f}", '均價': "{:.2f}", '斥資(億)': "{:.2f}", '主力囤貨(張)': "{:,.1f}",
                    '主力成本': "{:.2f}", '最新股價': "{:.2f}", '乖離率(%)': "{:.2f}",
                    '最新日買超張數': "{:,.0f}", '最新均價': "{:.2f}"
                }
                styled_res = cached_res.style.format(format_dict)
                if '乖離率(%)' in cached_res.columns:
                    try: styled_res = styled_res.background_gradient(subset=['乖離率(%)'], cmap='coolwarm_r') 
                    except: pass
                st.dataframe(styled_res, use_container_width=True, hide_index=True)

    # 🌟 2. 籌碼集中動能 (Δ) 排行榜 🌟 (改為讀取 Hugging Face)
    with st.expander("📈 全市場籌碼集中動能 (Δ) 排行榜 (Top 200)", expanded=False):
        st.markdown(r"💡 **資料由後台每日自動運算。** 抓出籌碼急遽集中的飆股黑馬。")
        
        if st.button("🚀 載入動能排行榜", use_container_width=True, type="primary"):
            momentum_url = f"{HF_BASE_URL}/momentum_latest.parquet"
            meta_url = f"{HF_BASE_URL}/momentum_meta.txt"
            
            try:
                with st.spinner("正在從 Hugging Face 抓取動能排行..."):
                    res_df = pd.read_parquet(momentum_url)
                    
                    # 讀取天數 meta
                    calc_days = 6
                    try:
                        response = requests.get(meta_url)
                        if response.status_code == 200:
                            calc_days = int(response.text.strip())
                    except: pass
                
                if STOCK_DICT:
                    res_df['股票名稱'] = res_df['股票代號'].astype(str).apply(lambda x: STOCK_DICT.get(x, {}).get('name', '-'))
                
                st.session_state['momentum_scan_result'] = res_df
                st.session_state['momentum_calc_days'] = calc_days
                st.success("✅ 瞬間讀取完畢！")
            except Exception as e:
                st.warning(f"⚠️ 找不到動能後台檔案，請確認已上傳至 Hugging Face。錯誤: {e}")

        if 'momentum_scan_result' in st.session_state:
            res_df = st.session_state['momentum_scan_result']
            calc_days = st.session_state.get('momentum_calc_days', 6)
            
            tabs_names = ["單日集中度 Δ", "5日集中度 Δ"]
            if calc_days >= 11: tabs_names.append("10日集中度 Δ")
            if calc_days >= 21: tabs_names.append("20日集中度 Δ")
            tabs = st.tabs(tabs_names)
            
            def fmt_rank_chg(val):
                if pd.isna(val): return "🆕 新進榜"  
                if val == 0: return "-"             
                if val > 0: return f"↑ {int(val)}"
                return f"↓ {int(abs(val))}"
            
            def color_chg(val):
                if isinstance(val, str):
                    if '↑' in val: return 'color: #FF4B4B; font-weight: bold;'
                    if '↓' in val: return 'color: #00E272;'
                    if '🆕' in val: return 'color: #38bdf8; font-weight: bold;' 
                return 'color: #94A3B8;'

            def render_momentum_tab(df, prefix, rank_col_name):
                prefix_map = {"單日": "1d_conc", "5日": "5d_conc", "10日": "10d_conc", "20日": "20d_conc"}
                eng_conc_col = prefix_map.get(prefix)
                disp_df = df.copy()
                
                if eng_conc_col in disp_df.columns: disp_df.rename(columns={eng_conc_col: f'{prefix}集中度(%)'}, inplace=True)
                cols_to_show = ['股票代號', '股票名稱', '名次變化', f'{prefix}集中度(%)', f'{prefix}Δ', '主力買超(萬)', '最新動態', '今日上榜期程']
                valid_cols = [c for c in cols_to_show if c in disp_df.columns]
                
                disp_df['名次變化'] = disp_df.get(rank_col_name, pd.Series(dtype=float)).apply(fmt_rank_chg)
                if f'{prefix}Δ' in disp_df.columns: disp_df = disp_df.sort_values(f'{prefix}Δ', ascending=False).head(200)
                disp_df = disp_df[valid_cols]
                
                if f'{prefix}集中度(%)' in disp_df.columns: disp_df.rename(columns={f'{prefix}集中度(%)': '當前集中度(%)'}, inplace=True)
                disp_df.reset_index(drop=True, inplace=True); disp_df.index = disp_df.index + 1; disp_df.index.name = "名次"
                
                format_dict = {'當前集中度(%)': "{:.2f}", f'{prefix}Δ': "{:.2f}", '主力買超(萬)': "{:,.0f}"}
                safe_format_dict = {k: v for k, v in format_dict.items() if k in disp_df.columns}
                
                styled = disp_df.style.format(safe_format_dict)
                if '名次變化' in disp_df.columns: styled = styled.applymap(color_chg, subset=['名次變化'])
                try: 
                    if f'{prefix}Δ' in disp_df.columns: styled = styled.background_gradient(subset=[f'{prefix}Δ'], cmap='Reds')
                except: pass
                st.dataframe(styled, use_container_width=True)

            with tabs[0]: render_momentum_tab(res_df, "單日", "5d_rank_chg")
            with tabs[1]: render_momentum_tab(res_df, "5日", "5d_rank_chg")
            if calc_days >= 11:
                with tabs[2]: render_momentum_tab(res_df, "10日", "10d_rank_chg")
            if calc_days >= 21:
                with tabs[3]: render_momentum_tab(res_df, "20日", "20d_rank_chg")

    # 🌟 3. 個股查詢器 🌟
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
        if not df_raw_all.empty:
            stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
            if not stock_raw.empty:
                try: df_trend = calculate_chip_concentration(stock_raw)
                except Exception as e: df_trend = pd.DataFrame()
                if not df_trend.empty: render_broker_dashboard(target_stock, display_name, df_raw_all, df_trend)
            else: st.warning(f"⚠️ 資料庫中找不到 {display_name} 的交易紀錄。")
