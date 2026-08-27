import streamlit as st
import pandas as pd
from utils.data_utils import calculate_chip_concentration

# 建立快取機制，讀取遠端的「原始交易歷史總檔」
@st.cache_data(ttl=3600)
def load_raw_broker_history(url):
    try:
        # 強制將代號轉為字串以防掉 0
        df = pd.read_csv(url, dtype={'stock_code': str})
        return df
    except Exception as e:
        st.error(f"載入原始明細失敗: {e}")
        return pd.DataFrame()

def render(STOCK_DICT=None):
    """券商分點頁面的主畫面邏輯"""
    st.title("🕵️‍♂️ 主力券商分點追蹤 (Beta)")
    st.markdown("透過每日全市場券商進出明細，追蹤大戶籌碼集中度與背後分點。")
    
    # ==========================================
    # 🌟 統一的華麗下拉搜尋選單
    # ==========================================
    stock_options = []
    if STOCK_DICT:
        # 自動產生下拉選單，並剃除重複
        unique_options = {f"{v['id']} {v['name']}" for v in STOCK_DICT.values() if len(str(v['id'])) <= 4}
        stock_options = sorted(list(unique_options))
    
    # 預設選項設定為 1709 和益
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
                # 區塊 A：大局觀 (籌碼集中度走勢圖)
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
                
                # 區塊 B：每日主力現形表 (分點買賣清單)
                st.markdown("---")
                st.subheader(f"🔍 {display_name} 每日主力分點進出明細")
                
                stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
                
                if not stock_raw.empty:
                    # ==========================================
                    # 🌟 智慧探測儀：自動尋找券商與均價欄位
                    # ==========================================
                    broker_col = next((c for c in ['broker', 'broker_name', '券商名稱', '券商', 'name'] if c in stock_raw.columns), None)
                    price_col = next((c for c in ['price', 'avg_price', '均價', '買進均價', '賣出均價'] if c in stock_raw.columns), None)
                    
                    if broker_col is None:
                        # 如果真的連券商代號都找不到，就把所有的欄位印出來給你看！
                        st.error(f"⚠️ 無法在資料庫中找到「券商名稱」欄位！目前資料庫實際擁有的欄位有：\n{', '.join(stock_raw.columns)}")
                    else:
                        available_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)
                        selected_date = st.selectbox("請選擇要查看的交易日期：", available_dates)
                        daily_raw = stock_raw[stock_raw['trade_date'] == selected_date]
                        
                        col1, col2 = st.columns(2)
                        
                        # 🎨 幫 DataFrame 整理欄位的函式 (暫時移除漸層色，避開 matplotlib 報錯)
                        def format_table(df, is_buy):
                            if df.empty: return None
                            df = df.copy()
                            
                            # 賣超轉正數
                            if not is_buy: df['net_vol'] = df['net_vol'].abs()
                                
                            df = df.sort_values('net_vol', ascending=False).head(15)
                            
                            # 動態組合要顯示的欄位
                            display_cols = [broker_col]
                            if price_col: display_cols.append(price_col)
                            display_cols.extend(['net_vol', 'pct'])
                            df = df[display_cols]
                            
                            # 重新命名欄位為中文
                            new_names = ['券商名稱']
                            if price_col: new_names.append('均價')
                            new_names.extend(['張數', '佔總量(%)'])
                            df.columns = new_names
                            
                            return df

                        with col1:
                            st.markdown("##### 🔴 買超前 15 大券商")
                            buy_df = daily_raw[daily_raw['side'] == 'buy']
                            styled_buy = format_table(buy_df, is_buy=True)
                            if styled_buy is not None:
                                st.dataframe(styled_buy, use_container_width=True, hide_index=True)
                            else:
                                st.write("當日無買超資料")
                                
                        with col2:
                            st.markdown("##### 🟢 賣超前 15 大券商")
                            sell_df = daily_raw[daily_raw['side'] == 'sell']
                            styled_sell = format_table(sell_df, is_buy=False)
                            if styled_sell is not None:
                                st.dataframe(styled_sell, use_container_width=True, hide_index=True)
                            else:
                                st.write("當日無賣超資料")
                else:
                    st.warning(f"在歷史總帳本中，找不到 **{display_name}** 的紀錄。")
            else:
                st.warning("⚠️ 找不到資料。遠端資料庫可能是空的。")
                
        except Exception as e:
            st.error(f"讀取資料失敗：{e}")
