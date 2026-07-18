import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="籌碼雙向透視鏡", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ 籌碼雙向透視鏡")
st.markdown("直接解析 60 日歷史總表，提供 **「特定券商進出追蹤」** 與 **「個股主力溯源矩陣」** 兩大核心功能！")

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
# 讀取 CSV 歷史總表
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
            
        recent_df['stock_code'] = recent_df['stock_code'].astype(str)
        recent_df['券商全名'] = recent_df['broker_id'].astype(str) + " " + recent_df['broker_name']
        
        return recent_df, latest_date.strftime("%Y-%m-%d"), [d.strftime("%Y-%m-%d") for d in unique_dates[:lookback_days]]
        
    except Exception as e:
        return None, str(e), []

# --- 網頁 UI 共用設定區 ---
col_slider, col_empty = st.columns([1, 1])
with col_slider:
    lookback = st.slider("選擇要分析的最近交易天數", min_value=3, max_value=60, value=10)

with st.spinner(f"📡 正在載入近 {lookback} 日籌碼資料..."):
    df_raw, info, date_list = fetch_broker_data(lookback)
    stock_dict = get_stock_names_dict()

if df_raw is not None and not df_raw.empty:
    st.success(f"✅ 資料載入成功！最新交易日: **{info}** | 分析區間共 {len(date_list)} 天。")
    
    # 建立雙標籤頁
    tab1, tab2 = st.tabs(["🏦 視角一：特定券商進出追蹤 (以券商找股)", "🎯 視角二：個股主力籌碼溯源 (以股找券商)"])
    
    # ==========================================
    # Tab 1: 以券商找股 (你原本的功能)
    # ==========================================
    with tab1:
        broker_list = sorted(df_raw['券商全名'].unique())
        selected_broker = st.selectbox("請選擇要進行『X光透視』的券商分點:", broker_list, key="broker_select")
        
        # 將原始資料依股票群組加總
        broker_data = df_raw[df_raw['券商全名'] == selected_broker].groupby('stock_code').agg(
            總買進=('buy_vol', 'sum'),
            總賣出=('sell_vol', 'sum'),
            淨買超=('net_vol', 'sum'),
            交易天數=('trade_date', 'nunique')
        ).reset_index()
        
        broker_data['股票名稱'] = broker_data['stock_code'].map(lambda x: stock_dict.get(x, "-"))
        broker_data['股票代號'] = broker_data['stock_code']
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔥 區間買超排行")
            buy_df = broker_data[broker_data['淨買超'] > 0].sort_values(by='淨買超', ascending=False).head(15)
            if not buy_df.empty:
                st.dataframe(buy_df[['股票代號', '股票名稱', '總買進', '總賣出', '淨買超', '交易天數']], hide_index=True, use_container_width=True)
            else:
                st.info("該期間內無買超紀錄。")

        with col2:
            st.subheader("📉 區間賣超排行")
            sell_df = broker_data[broker_data['淨買超'] < 0].sort_values(by='淨買超', ascending=True).head(15)
            if not sell_df.empty:
                st.dataframe(sell_df[['股票代號', '股票名稱', '總買進', '總賣出', '淨買超', '交易天數']], hide_index=True, use_container_width=True)
            else:
                st.info("該期間內無賣超紀錄。")

    # ==========================================
    # Tab 2: 以股找券商 (全新時間序列矩陣)
    # ==========================================
    with tab2:
        # 整理出該資料庫中「有紀錄」的股票清單供選擇
        available_stocks = sorted(df_raw['stock_code'].unique())
        stock_options = [f"{code} {stock_dict.get(code, '-')}" for code in available_stocks]
        
        selected_stock_display = st.selectbox("請選擇要查詢的主力溯源標的 (僅列出資料庫有紀錄之股票):", stock_options, key="stock_select")
        selected_stock_code = selected_stock_display.split(" ")[0]
        
        # 篩選該檔股票的所有交易紀錄
        stock_data = df_raw[df_raw['stock_code'] == selected_stock_code].copy()
    # ... (保留前面相同的讀取邏輯) ...

        # 在 Tab 2 中，進行日期欄位的強制排序
        if not stock_data.empty:
            # 1. 取得所有日期並進行正確排序
            date_cols = sorted([c for c in stock_data['trade_date'].dt.strftime("%m/%d").unique()])
            
            # 2. 製作 Pivot Table (並強制指定欄位順序)
            pivot_df = stock_data.pivot_table(
                index='券商全名', 
                columns='trade_date', 
                values='net_vol', 
                aggfunc='sum', 
                fill_value=0
            )
            # 轉回 MM/DD 格式並強制排序
            pivot_df.columns = [d.strftime("%m/%d") for d in pivot_df.columns]
            pivot_df = pivot_df[sorted(pivot_df.columns)]
            
            # 3. 計算籌碼集中度：統計「區間淨買超」與「總成交量比例」
            pivot_df['總淨買超'] = pivot_df.sum(axis=1)
            
            # 4. 顯示
            st.dataframe(
                pivot_df.sort_values(by='總淨買超', ascending=False),
                use_container_width=True
            )
            
            # 計算該區間的「總淨買超」，並以此排序找出最大主力
            pivot_df['區間總淨買超'] = pivot_df.sum(axis=1)
            pivot_df = pivot_df.sort_values(by='區間總淨買超', ascending=False)
            
            # 將 DataFrame 格式化顯示 (標記紅綠色)
            st.markdown(f"### 📊 {selected_stock_display} - 券商進出時間序列矩陣")
            st.caption("正數代表買超，負數代表賣超。數值由左至右為時間推進。")
            
            # 使用 Streamlit 內建的樣式設定，讓表格顯示得更專業
            st.dataframe(
                pivot_df,
                use_container_width=True,
                height=600  # 讓表格高一點，方便上下滾動看 700 多家券商
            )
        else:
            st.info("這檔股票近期沒有大型券商進出紀錄。")

else:
    st.error(f"🚨 無法取得資料，錯誤訊息: {info}")
