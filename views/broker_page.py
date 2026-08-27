import streamlit as st
import pandas as pd
# 🌟 同時引入集中度計算工具，以及萬用股票字典
from utils.data_utils import calculate_chip_concentration, STOCK_DICT

# 建立快取機制，避免每次點選不同日期都要重新下載 CSV
@st.cache_data(ttl=3600)
def load_raw_broker_data(url):
    try:
        df = pd.read_csv(url)
        df['stock_code'] = df['stock_code'].astype(str)
        return df
    except Exception as e:
        st.error(f"載入原始明細失敗: {e}")
        return pd.DataFrame()

def render():
    """券商分點頁面的主畫面邏輯"""
    st.title("🕵️‍♂️ 主力券商分點追蹤 (Beta)")
    st.markdown("透過每日全市場券商進出明細，追蹤大戶籌碼集中度與背後分點。")
    
    # 建立一個輸入框讓你可以自由更換股票
    target_stock = st.text_input("請輸入要查詢的股票代號 (例如 1709 或 3413)：", value="1709", max_chars=4)
    
    if target_stock:
        # ==========================================
        # 🌟 痛點一解決：從字典中找出股票名稱
        # ==========================================
        stock_info = STOCK_DICT.get(target_stock, {})
        stock_name = stock_info.get("name", "") if isinstance(stock_info, dict) else ""
        
        # 組合顯示名稱 (例如 "3413 京鼎")
        display_name = f"{target_stock} {stock_name}".strip()
        
        st.info(f"正在從遠端資料庫撈取 **{display_name}** 的籌碼明細，請稍候...")
        
        # 你的 tw-broker-data 遠端資料庫網址
        remote_csv_url = "https://raw.githubusercontent.com/goodinfo3583/tw-broker-data/main/data/broker/broker_history.csv"
        
        try:
            # 1. 呼叫工具箱進行計算 (畫圖用)
            df_trend = calculate_chip_concentration(remote_csv_url, target_stock)
            
            # 2. 呼叫原始資料庫 (看主力明細用)
            df_raw_all = load_raw_broker_data(remote_csv_url)
            
            if not df_trend.empty and not df_raw_all.empty:
                st.success("✅ 數據載入成功！")
                
                # ==========================================
                # 區塊 A：大局觀 (籌碼集中度走勢)
                # ==========================================
                latest_data = df_trend.iloc[-1]
                st.metric(
                    label=f"{latest_data['trade_date']} {display_name} 最新籌碼集中度", 
                    value=f"{latest_data['concentration_%']}%",
                    delta=f"淨買超 {latest_data['net_buy']:,} 張"
                )
                
                st.subheader(f"📊 {display_name} 近期籌碼集中度走勢")
                st.bar_chart(df_trend, x="trade_date", y="concentration_%")
                
                # ==========================================
                # 🌟 痛點二解決：區塊 B (每日主力現形表)
                # ==========================================
                st.markdown("---")
                st.subheader(f"🔍 {display_name} 每日主力分點進出明細")
                
                # 從總表篩選出這檔股票的明細
                stock_raw = df_raw_all[df_raw_all['stock_code'] == target_stock].copy()
                
                if not stock_raw.empty:
                    # 抓出所有有交易的日期，並由新到舊排序
                    available_dates = sorted(stock_raw['trade_date'].unique(), reverse=True)
                    
                    # 讓使用者可以用下拉選單選擇想看哪一天的明細 (預設是最新一天)
                    selected_date = st.selectbox("請選擇要查看的交易日期：", available_dates)
                    
                    # 過濾出被選中那一天的明細
                    daily_raw = stock_raw[stock_raw['trade_date'] == selected_date]
                    
                    # 將畫面切成左右兩半
                    col1, col2 = st.columns(2)
                    
                    # 左半邊：買超大戶
                    with col1:
                        st.markdown("##### 🔴 買超前 15 大券商")
                        buy_df = daily_raw[daily_raw['side'] == 'buy'].copy()
                        # 只留下我們想看的欄位，並照買超張數排序
                        buy_df = buy_df[['broker_name', 'price', 'net_vol', 'pct']].sort_values('net_vol', ascending=False)
                        buy_df.columns = ['券商名稱', '買均價', '買超張數', '佔總量(%)']
                        
                        # 顯示表格 (hide_index=True 可以隱藏左邊醜醜的序號)
                        st.dataframe(buy_df, use_container_width=True, hide_index=True)
                        
                    # 右半邊：賣超大戶
                    with col2:
                        st.markdown("##### 🟢 賣超前 15 大券商")
                        sell_df = daily_raw[daily_raw['side'] == 'sell'].copy()
                        # 為了閱讀方便，把賣超的負數張數轉成絕對值 (正數)
                        sell_df['net_vol'] = sell_df['net_vol'].abs()
                        sell_df = sell_df[['broker_name', 'price', 'net_vol', 'pct']].sort_values('net_vol', ascending=False)
                        sell_df.columns = ['券商名稱', '賣均價', '賣超張數', '佔總量(%)']
                        
                        st.dataframe(sell_df, use_container_width=True, hide_index=True)
                        
            else:
                st.warning(f"⚠️ 找不到 **{display_name}** 的資料。可能是遠端資料尚未更新，或該股不在抓取名單內。")
                
        except Exception as e:
            st.error(f"讀取資料失敗：{e}")
