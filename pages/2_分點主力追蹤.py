import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="券商分點追蹤", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ 頂級券商分點買賣超追蹤")
st.markdown("直接解析 60 日歷史總表，動態查詢**特定券商分點 (如凱基-台北)** 的近期買賣超排行！")

# 🌟 統一使用這份每天都會更新的 2.6MB 歷史原始檔
TARGET_URL = "https://raw.githubusercontent.com/voidful/tw-institutional-stocker/main/data/broker/broker_history.csv"

# ========================================================
# 動態獲取台股「代號對應名稱」的對照字典
# ========================================================
@st.cache_data(ttl=86400)
def get_stock_names_dict():
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    try:
        res = requests.get(url, timeout=10)
        df = pd.DataFrame(res.json())
        return dict(zip(df['Code'], df['Name']))
    except Exception:
        return {}

# ========================================================
# 讀取 CSV 並將資料依照「券商」視角進行彙整
# ========================================================
@st.cache_data(ttl=3600)
def fetch_broker_data(lookback_days=10):
    try:
        df = pd.read_csv(TARGET_URL)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        latest_date = df['trade_date'].max()
        
        # 根據回測天數切出資料
        cutoff_date = latest_date - pd.Timedelta(days=lookback_days * 1.5) 
        recent_df = df[df['trade_date'] >= cutoff_date]
        
        unique_dates = sorted(recent_df['trade_date'].unique(), reverse=True)
        if len(unique_dates) > lookback_days:
            exact_cutoff = unique_dates[lookback_days - 1]
            recent_df = recent_df[recent_df['trade_date'] >= exact_cutoff]
            
        # 核心群組運算：這次的視角是「這個分點，對這檔股票買賣了多少」
        grouped = recent_df.groupby(['broker_id', 'broker_name', 'stock_code']).agg(
            總買進=('buy_vol', 'sum'),
            總賣出=('sell_vol', 'sum'),
            淨買超=('net_vol', 'sum'),
            交易天數=('trade_date', 'nunique')
        ).reset_index()

        return grouped, latest_date.strftime("%Y-%m-%d")
        
    except Exception as e:
        return None, str(e)

# --- 網頁 UI 顯示區 ---
col_slider, col_empty = st.columns([1, 1])
with col_slider:
    lookback = st.slider("選擇要分析的最近交易天數", min_value=3, max_value=60, value=10)

with st.spinner(f"📡 正在載入近 {lookback} 日籌碼資料..."):
    df, info = fetch_broker_data(lookback)

if df is not None and not df.empty:
    # 建立「券商代號 + 名稱」的選單清單
    df['券商全名'] = df['broker_id'].astype(str) + " " + df['broker_name']
    broker_list = sorted(df['券商全名'].unique())
    
    st.success(f"✅ 資料載入成功！最新交易日: **{info}** | 共收錄 {len(broker_list)} 家分點資料。")
    
    # 下拉選單讓使用者指定券商
    selected_broker = st.selectbox("請選擇要進行『X光透視』的券商分點:", broker_list)
    
    # 篩選出該券商的所有交易紀錄
    broker_data = df[df['券商全名'] == selected_broker].copy()
    
    # 映射股票名稱
    stock_dict = get_stock_names_dict()
    broker_data['股票名稱'] = broker_data['stock_code'].astype(str).map(lambda x: stock_dict.get(x, "-"))
    broker_data['股票代號'] = broker_data['stock_code'].astype(str)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 買超前 10 名")
        # 篩選淨買超大於 0，並由大到小排序
        buy_df = broker_data[broker_data['淨買超'] > 0].sort_values(by='淨買超', ascending=False).head(10)
        
        if not buy_df.empty:
            st.dataframe(
                buy_df[['股票代號', '股票名稱', '總買進', '總賣出', '淨買超', '交易天數']],
                column_config={"淨買超": st.column_config.NumberColumn(format="%d 📈")},
                hide_index=True, use_container_width=True
            )
        else:
            st.info("該期間內無買超紀錄。")

    with col2:
        st.subheader("📉 賣超前 10 名")
        # 篩選淨買超小於 0，並由小到大(負越多越上面)排序
        sell_df = broker_data[broker_data['淨買超'] < 0].sort_values(by='淨買超', ascending=True).head(10)
        
        if not sell_df.empty:
            st.dataframe(
                sell_df[['股票代號', '股票名稱', '總買進', '總賣出', '淨買超', '交易天數']],
                column_config={"淨買超": st.column_config.NumberColumn(format="%d 📉")},
                hide_index=True, use_container_width=True
            )
        else:
            st.info("該期間內無賣超紀錄。")
else:
    st.error(f"🚨 無法取得資料，錯誤訊息: {info}")
