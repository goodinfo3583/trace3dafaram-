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
    st.title("🕵️‍♂️ 主力券商分點追蹤 (Beta)")
    st.markdown("透過每日全市場券商進出明細，追蹤大戶籌碼集中度與區間囤貨特徵。")
    
    # ==========================================
    # 🌟 統一的華麗下拉搜尋選單
    # ==========================================
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
                # ==========================================
                # 區塊 A：大局觀 (籌碼集中度走勢圖與歷史表)
                # ==========================================
                df_trend = calculate_chip_concentration(remote_csv_url, target_stock)
                
                if not df_trend.empty:
                    st.success("✅ 數據載入成功！")
                    latest_data = df_trend.iloc[-1]
                    st.metric(
                        label=f"{latest_data['trade_date']} 最新籌碼集中度", 
                        value=f"{latest_data['concentration_%']}%",
                        delta=f"淨買超 {latest_data['net_buy']:,} 張"
                    )
                    st.subheader(f"📊 {display_name} 近期籌碼集中度走勢")
                    st.bar_chart(df_trend, x="trade_date", y="concentration_%")
                    
                    # 🌟 升級一：近 60 日籌碼集中度歷史表 (用 expander 收合保持版面乾淨)
                    with st.expander("📅 展開查看：近 60 日籌碼集中度歷史表", expanded=False):
                        df_trend_disp = df_trend.sort_values('trade_date', ascending=False).head(60).copy()
                        df_trend_disp = df_trend_disp[['trade_date', 'net_buy', 'concentration_%']]
                        df_trend_disp.columns = ['交易日期', '淨買超(張)', '集中度(%)']
                        st.dataframe(df_trend_disp, use_container_width=True, hide_index=True)
                
                # ==========================================
                # 區塊 B：主力現形表 (單日明細 vs 區間囤貨)
                # ==========================================
                st.markdown("---")
                st.subheader(f"🔍 {display_name} 主力分點進出解析")
                
                stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
                
                if not stock_raw.empty:
                    # 自動尋找券商名稱欄位
                    broker_col = next((c for c in ['broker', 'broker_name', '券商名稱', '券商', 'name'] if c in stock_raw.columns), None)
                    
                    if broker_col is None:
                        st.error("⚠️ 無法在資料庫中找到「券商名稱」欄位！")
                    else:
                        available_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)
                        
                        # 🌟 升級二：雙頁籤設計
                        tab1, tab2 = st.tabs(["📅 單日進出明細", "🏦 區間囤貨追蹤 (近60日)"])
                        
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
                                st.markdown("##### 🔴 買超前 15 大券商")
                                styled_buy = format_daily_table(daily_raw[daily_raw['side'] == 'buy'], True)
                                if styled_buy is not None: st.dataframe(styled_buy, use_container_width=True, hide_index=True)
                                else: st.write("當日無資料")
                                
                            with col_sell:
                                st.markdown("##### 🟢 賣超前 15 大券商")
                                styled_sell = format_daily_table(daily_raw[daily_raw['side'] == 'sell'], False)
                                if styled_sell is not None: st.dataframe(styled_sell, use_container_width=True, hide_index=True)
                                else: st.write("當日無資料")

                        # --------- 標籤 2: 區間囤貨 (近60日) ---------
                        with tab2:
                            st.markdown("##### 🕵️‍♂️ 誰在偷偷吃貨？誰在瘋狂倒貨？")
                            # 擷取近 60 個有交易的日期
                            recent_dates = available_dates[:60]
                            recent_raw = stock_raw[stock_raw['trade_date'].isin(recent_dates)].copy()
                            
                            # 標準化淨買賣張數 (買超為正，賣超為負)
                            recent_raw['real_net_vol'] = recent_raw.apply(
                                lambda x: abs(x['net_vol']) if x['side'] == 'buy' else -abs(x['net_vol']), axis=1
                            )
                            
                            # 將這 60 天內出現過的券商進行分組加總
                            hoard_df = recent_raw.groupby(broker_col).agg(
                                買進總計=('real_net_vol', lambda x: x[x > 0].sum()),
                                賣出總計=('real_net_vol', lambda x: abs(x[x < 0].sum())),
                                區間淨買賣=('real_net_vol', 'sum')
                            ).reset_index()
                            
                            col_hoard, col_dump = st.columns(2)
                            
                            with col_hoard:
                                st.markdown("##### 📈 近 60 日囤貨大戶 (Top 15)")
                                top_hoarders = hoard_df[hoard_df['區間淨買賣'] > 0].sort_values('區間淨買賣', ascending=False).head(15)
                                if not top_hoarders.empty:
                                    top_hoarders.columns = ['券商名稱', '總買(張)', '總賣(張)', '淨買超(張)']
                                    st.dataframe(top_hoarders, use_container_width=True, hide_index=True)
                                else:
                                    st.write("區間內無明顯囤貨大戶")
                                    
                            with col_dump:
                                st.markdown("##### 📉 近 60 日倒貨大戶 (Top 15)")
                                top_dumpers = hoard_df[hoard_df['區間淨買賣'] < 0].sort_values('區間淨買賣', ascending=True).head(15).copy()
                                if not top_dumpers.empty:
                                    # 將倒貨的淨買賣轉為絕對值方便閱讀
                                    top_dumpers['區間淨買賣'] = top_dumpers['區間淨買賣'].abs()
                                    top_dumpers.columns = ['券商名稱', '總買(張)', '總賣(張)', '淨賣超(張)']
                                    st.dataframe(top_dumpers, use_container_width=True, hide_index=True)
                                else:
                                    st.write("區間內無明顯倒貨大戶")
                                    
                else:
                    st.warning(f"在歷史總帳本中，找不到 **{display_name}** 的紀錄。")
            else:
                st.warning("⚠️ 找不到資料。遠端資料庫可能是空的。")
                
        except Exception as e:
            st.error(f"讀取資料失敗：{e}")
