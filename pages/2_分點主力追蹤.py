import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="券商分點追蹤", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ 頂級券商分點買賣超與相關性分析")

# 這裡替換成該專案的真實 GitHub 原始碼網址 (Raw URL)
# 例如: https://raw.githubusercontent.com/他的帳號/他的專案/main/docs/data/broker_stats.json
TARGET_JSON_URL = "請在這裡貼上他 GitHub 上 broker_stats.json 的 Raw 網址"

@st.cache_data(ttl=3600) # 快取 1 小時，避免一直重複下載
def fetch_broker_data():
    try:
        res = requests.get(TARGET_JSON_URL)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"無法取得資料，請確認網址或網路狀態: {e}")
        return None

data = fetch_broker_data()

if data:
    st.success(f"✅ 資料更新時間: {data.get('updated', '未知')} | 分析天數: {data.get('analysis_days', 60)}天")
    
    # 取出結果列表
    results = data.get("results", [])
    
    # 建立一個下拉選單讓你可以選券商
    broker_names = [f"{r['broker_id']} - {r['broker_name']}" for r in results]
    selected_broker = st.selectbox("選擇要分析的券商分點:", broker_names)
    
    # 找出選中券商的詳細資料
    for r in results:
        if f"{r['broker_id']} - {r['broker_name']}" == selected_broker:
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔥 買超前 10 名")
                buy_df = pd.DataFrame(r['top_buy_stocks'])
                if not buy_df.empty:
                    # 只顯示重要欄位
                    st.dataframe(buy_df[['stock_code', 'stock_name', 'total_net_vol', 'trading_days', 'avg_net_vol']], hide_index=True)
            
            with col2:
                st.subheader("📉 賣超前 10 名")
                sell_df = pd.DataFrame(r['top_sell_stocks'])
                if not sell_df.empty:
                    st.dataframe(sell_df[['stock_code', 'stock_name', 'total_net_vol', 'trading_days', 'avg_net_vol']], hide_index=True)
            break
