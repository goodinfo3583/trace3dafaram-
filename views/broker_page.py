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
    # 修正命名：改為更精確的「券商分點淨買力」與「集中度」
    st.title("券商分點淨買力與集中度追蹤 (Beta)")
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
                    
                    # 依據集中度定義顯示顏色
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
                        
                        # 🌟 升級：新增第三個頁籤「歷史進出矩陣」
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
                            
                            # 🎨 格式化函式：將 0 轉為 "-" (代表未進榜)，其餘加上千分位逗號
                            def fmt_dash(val):
                                if pd.isna(val) or val == 0: 
                                    return "-"
                                return "{:,.0f}".format(val)
                            
                            with col_hoard:
                                st.markdown("##### 📈 近 60 日囤貨分點 (全榜)")
                                # 移除 .head(15)，列出所有囤貨券商
                                hoarders = hoard_df[hoard_df['區間淨買賣'] > 0].sort_values('區間淨買賣', ascending=False)
                                if not hoarders.empty:
                                    hoarders.columns = ['券商名稱', '總買(張)', '總賣(張)', '淨買超(張)']
                                    # 套用格式化函式
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
                                # 移除 .head(15)，列出所有倒貨券商
                                dumpers = hoard_df[hoard_df['區間淨買賣'] < 0].sort_values('區間淨買賣', ascending=True).copy()
                                if not dumpers.empty:
                                    dumpers['區間淨買賣'] = dumpers['區間淨買賣'].abs()
                                    dumpers.columns = ['券商名稱', '總買(張)', '總賣(張)', '淨賣超(張)']
                                    # 套用格式化函式
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
                            st.write("橫列為各分點，縱欄為交易日期。若顯示「-」代表當日該分點**未擠進買賣前 15 大 (未進榜)**，而非交易量為零。")
                            
                            matrix_dates = available_dates[:30]
                            matrix_raw = stock_raw[stock_raw['trade_date'].isin(matrix_dates)].copy()
                            
                            if not matrix_raw.empty:
                                matrix_raw['signed_vol'] = matrix_raw.apply(
                                    lambda x: abs(x['net_vol']) if x['side'] == 'buy' else -abs(x['net_vol']), axis=1
                                )
                                
                                # 製作樞紐分析表 (此時缺漏的日期會是 NaN)
                                pivot_df = matrix_raw.pivot_table(
                                    index=broker_col, 
                                    columns='trade_date', 
                                    values='signed_vol', 
                                    aggfunc='sum'
                                )
                                
                                # 🌟 修正：在填補字串前先計算「區間累計」，這樣 NaN 會被當作 0 計算，不會報錯
                                pivot_df['區間累計'] = pivot_df.sum(axis=1)
                                pivot_df = pivot_df.sort_values('區間累計', ascending=False)
                                
                                # 🌟 修正：將未進榜的 NaN 填補為 "-"
                                pivot_df = pivot_df.fillna("-")
                                
                                # 調整欄位順序：區間累計放第一欄，日期由新到舊排列
                                cols = ['區間累計'] + sorted([c for c in pivot_df.columns if c != '區間累計'], reverse=True)
                                pivot_df = pivot_df[cols]
                                
                                # 🎨 內建字體顏色渲染函式
                                def color_net_vol(val):
                                    if val == "-": return 'color: #64748B;' # 未進榜顯示為暗灰色
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
