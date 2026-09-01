#views/broker_page.py
import streamlit as st
import pandas as pd
from utils.data_utils import calculate_chip_concentration

@st.cache_data(ttl=3600)
def load_raw_broker_history(url):
    try:
        df = pd.read_csv(url, dtype={'stock_code': str})
        return df
    except Exception as e:
        st.error(f"載入原始明細失敗: {e}")
        return pd.DataFrame()

def render(STOCK_DICT=None):
    st.title("券商分點淨買力與集中度追蹤")
    st.markdown("觀察前 15 大分點買賣力道相抵後的淨流向，追蹤籌碼集中度連續性與券商進出矩陣。")
    
    stock_options = []
    if STOCK_DICT:
        unique_options = {f"{v['id']} {v['name']}" for v in STOCK_DICT.values() if len(str(v['id'])) <= 4}
        stock_options = sorted(list(unique_options))
    
    default_index = 0
    for idx, opt in enumerate(stock_options):
        if opt.startswith("1709"):
            default_index = idx + 1
            break

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_stock_str = st.selectbox(
            "請選擇要查詢的股票：", 
            options=[""] + stock_options,
            index=default_index,
            key="broker_search_input"
        )
    
    if selected_stock_str:
        target_stock = selected_stock_str.split(" ")[0].strip()
        display_name = selected_stock_str
        
        st.info(f"正在從遠端資料庫撈取 **{display_name}** 的籌碼明細，請稍候...")
        remote_csv_url = "https://raw.githubusercontent.com/goodinfo3583/tw-broker-data/main/data/broker/broker_history.csv"
        
        try:
            df_raw_all = load_raw_broker_history(remote_csv_url)
            
            if not df_raw_all.empty:
                df_trend = calculate_chip_concentration(remote_csv_url, target_stock)
                
                if not df_trend.empty:
                    st.success("✅ 數據載入成功！")
                    latest_data = df_trend.iloc[-1]
                    
                    st.metric(
                        label=f"{latest_data['trade_date']} 最新券商分點集中度", 
                        value=f"{latest_data['concentration_%']}%",
                        delta=f"淨買超 {latest_data['net_buy']:,} 張"
                    )
                    
                    st.subheader(f"📊 {display_name} 分點集中度連續性走勢")
                    st.bar_chart(df_trend, x="trade_date", y="concentration_%")
                    
                    with st.expander("📅 展開查看：近 60 日集中度與淨買超歷史表", expanded=False):
                        df_trend_disp = df_trend.sort_values('trade_date', ascending=False).head(60).copy()
                        df_trend_disp = df_trend_disp[['trade_date', 'net_buy', 'concentration_%']]
                        df_trend_disp.columns = ['交易日期', '淨買超(張)', '集中度(%)']
                        st.dataframe(df_trend_disp, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader(f"🔍 {display_name} 券商分點明細與進出矩陣")
                
                stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
                
                if not stock_raw.empty:
                    broker_col = next((c for c in ['broker', 'broker_name', '券商名稱', '券商', 'name'] if c in stock_raw.columns), None)
                    
                    if broker_col is None:
                        st.error("⚠️ 無法在資料庫中找到「券商名稱」欄位！")
                    else:
                        available_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)
                        
                        tab1, tab2, tab3 = st.tabs(["🔹 單日進出明細", "🔹 區間囤貨追蹤 (近60日)", "🔹 歷史進出矩陣 (近30日)"])
                        
                        # --------- 標籤 1: 單日明細 ---------
                        with tab1:
                            selected_date = st.selectbox("請選擇要查看的交易日期：", available_dates, key="daily_date_sel")
                            daily_raw = stock_raw[stock_raw['trade_date'] == selected_date]
                            
                            col_buy, col_sell = st.columns(2)
                            
                            def format_daily_table(df, is_buy):
                                if df.empty: return None
                                df = df.copy()
                                if not is_buy: df['net_vol'] = df['net_vol'].abs()
                                df = df.sort_values('net_vol', ascending=False).head(15)
                                df = df[[broker_col, 'net_vol']]
                                df.columns = ['券商名稱', '張數']
                                return df

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

                        # --------- 標籤 2: 區間囤貨 (近60日) ---------
                        with tab2:
                            st.markdown("##### 🕵️‍♂️ 誰在連續吃貨？誰在持續倒貨？")
                            recent_dates = available_dates[:60]
                            recent_raw = stock_raw[stock_raw['trade_date'].isin(recent_dates)].copy()
                            
                            recent_raw['real_net_vol'] = recent_raw.apply(
                                lambda x: abs(x['net_vol']) if x['side'] == 'buy' else -abs(x['net_vol']), axis=1
                            )
                            
                            hoard_df = recent_raw.groupby(broker_col).agg(
                                買進總計=('real_net_vol', lambda x: x[x > 0].sum()),
                                賣出總計=('real_net_vol', lambda x: abs(x[x < 0].sum())),
                                區間淨買賣=('real_net_vol', 'sum')
                            ).reset_index()
                            
                            col_hoard, col_dump = st.columns(2)
                            
                            def fmt_dash(val):
                                if pd.isna(val) or val == 0: 
                                    return "-"
                                return "{:,.0f}".format(val)
                            
                            with col_hoard:
                                st.markdown("##### 📈 近 60 日囤貨分點 (全榜)")
                                hoarders = hoard_df[hoard_df['區間淨買賣'] > 0].sort_values('區間淨買賣', ascending=False)
                                if not hoarders.empty:
                                    hoarders.columns = ['券商名稱', '總買(張)', '總賣(張)', '淨買超(張)']
                                    styled_hoard = hoarders.style.format({
                                        '總買(張)': fmt_dash, 
                                        '總賣(張)': fmt_dash, 
                                        '淨買超(張)': fmt_dash
                                    })
                                    st.dataframe(styled_hoard, use_container_width=True, hide_index=True)
                                else: 
                                    st.write("區間內無明顯囤貨分點")
                                    
                            with col_dump:
                                st.markdown("##### 📉 近 60 日倒貨分點 (全榜)")
                                dumpers = hoard_df[hoard_df['區間淨買賣'] < 0].sort_values('區間淨買賣', ascending=True).copy()
                                if not dumpers.empty:
                                    dumpers['區間淨買賣'] = dumpers['區間淨買賣'].abs()
                                    dumpers.columns = ['券商名稱', '總買(張)', '總賣(張)', '淨賣超(張)']
                                    styled_dump = dumpers.style.format({
                                        '總買(張)': fmt_dash, 
                                        '總賣(張)': fmt_dash, 
                                        '淨賣超(張)': fmt_dash
                                    })
                                    st.dataframe(styled_dump, use_container_width=True, hide_index=True)
                                else: 
                                    st.write("區間內無明顯倒貨分點")

                        # --------- 標籤 3: 歷史進出矩陣 (近30日) ---------
                        with tab3:
                            st.markdown("##### 🗺️ 分點淨買賣力道矩陣")
                            st.write("橫列為各分點，縱欄顯示**近 30 個交易日**。但「動態連買/連賣」是往前回溯**所有歷史資料**統計而成。")
                            st.write("若表格顯示「-」代表當日該分點**未進榜 (前15大)**，中斷則重新計算天數。")
                            
                            # 🌟 改良：使用「全部」歷史資料來做精準統計
                            all_matrix_raw = stock_raw.copy()
                            
                            if not all_matrix_raw.empty:
                                all_matrix_raw['signed_vol'] = all_matrix_raw.apply(
                                    lambda x: abs(x['net_vol']) if x['side'] == 'buy' else -abs(x['net_vol']), axis=1
                                )
                                
                                # --- 1. 計算全歷史的週資料 ---
                                all_matrix_raw['date_dt'] = pd.to_datetime(all_matrix_raw['trade_date'])
                                all_matrix_raw['year_week'] = all_matrix_raw['date_dt'].dt.strftime('%Y-%W')
                                weekly_sum = all_matrix_raw.groupby([broker_col, 'year_week'])['signed_vol'].sum().unstack(fill_value=0)
                                week_cols = sorted(weekly_sum.columns, reverse=True)
                                
                                # --- 2. 建立全歷史的日資料樞紐分析表 ---
                                full_pivot = all_matrix_raw.pivot_table(
                                    index=broker_col, 
                                    columns='trade_date', 
                                    values='signed_vol', 
                                    aggfunc='sum'
                                )
                                all_dates_sorted = sorted(full_pivot.columns, reverse=True)
                                
                                # --- 3. 畫面顯示區間裁切 (近30日) ---
                                display_dates = all_dates_sorted[:30]
                                # 複製出要顯示的 DataFrame
                                pivot_df = full_pivot[display_dates].copy()
                                # 區間累計「只」計算畫面上這30天內的加總，才不會跟畫面數字對不起來
                                pivot_df['區間累計'] = pivot_df.sum(axis=1)
                                pivot_df = pivot_df.sort_values('區間累計', ascending=False)
                                
                                # --- 4. 計算日連買動態 (從全歷史資料 full_pivot 去追蹤) ---
                                def calc_daily_streak(row_name):
                                    if row_name not in full_pivot.index: return "-"
                                    row = full_pivot.loc[row_name]
                                    streak = 0
                                    sign = None
                                    for c in all_dates_sorted:
                                        val = row.get(c, 0)
                                        if pd.isna(val) or val == 0:
                                            break  # 沒進榜或是0即中斷
                                        current_sign = 1 if val > 0 else -1
                                        if sign is None:
                                            sign = current_sign
                                            streak = sign
                                        elif sign == current_sign:
                                            streak += sign
                                        else:
                                            break  # 轉買或轉賣即中斷
                                    if streak > 0: return f"連買 {streak} 日"
                                    elif streak < 0: return f"連賣 {-streak} 日"
                                    else: return "-"
                                    
                                pivot_df['日連買動態'] = pivot_df.index.to_series().apply(calc_daily_streak)

                                # --- 5. 計算週連買動態 (從全歷史資料 weekly_sum 去追蹤) ---
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
                                
                                # --- 6. 收尾與排版 ---
                                # 將顯示範圍內的 NaN 填補為 "-"
                                pivot_df[display_dates] = pivot_df[display_dates].fillna("-")
                                
                                # 更改 index 名稱為中文券商分點
                                pivot_df.index.name = "中文券商分點"
                                
                                # 調整欄位順序：日連買動態、週連買動態、區間累計放前面，之後依日期排列
                                cols = ['日連買動態', '週連買動態', '區間累計'] + display_dates
                                pivot_df = pivot_df[cols]
                                
                                # 🎨 內建字體顏色渲染函式
                                def color_net_vol(val):
                                    if isinstance(val, str):
                                        if val == "-": return 'color: #64748B;' # 未進榜顯示為暗灰色
                                        if "連買" in val: return 'color: #FF4B4B;' # 連買顯示紅色
                                        if "連賣" in val: return 'color: #00E272;' # 連賣顯示綠色
                                    try:
                                        v = float(val)
                                        if v > 0: return 'color: #FF4B4B;'
                                        elif v < 0: return 'color: #00E272;'
                                    except: pass
                                    return 'color: #94A3B8;'
                                
                                # 相容 Pandas 新舊版本的 styling 寫法
                                if hasattr(pivot_df.style, 'map'):
                                    styled_pivot = pivot_df.style.map(color_net_vol).format(lambda x: "{:,.0f}".format(x) if isinstance(x, (int, float)) else x)
                                else:
                                    styled_pivot = pivot_df.style.applymap(color_net_vol).format(lambda x: "{:,.0f}".format(x) if isinstance(x, (int, float)) else x)
                                
                                st.dataframe(styled_pivot, use_container_width=True)
                            else:
                                st.write("無足夠資料產生矩陣")
                                
                else:
                    st.warning(f"在歷史總帳本中，找不到 **{display_name}** 的紀錄。")
            else:
                st.warning("⚠️ 找不到資料。遠端資料庫可能是空的。")
                
        except Exception as e:
            st.error(f"讀取資料失敗：{e}")
