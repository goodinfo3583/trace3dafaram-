import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="主力囤貨雷達", page_icon="🎯", layout="wide")
st.title("🎯 主力囤貨雷達")

TARGET_URL = "https://raw.githubusercontent.com/voidful/tw-institutional-stocker/main/data/broker/broker_history.csv"

# ========================================================
# 🌟 新增功能：動態獲取台股「代號對應名稱」的對照字典
# ========================================================
@st.cache_data(ttl=86400) # 快取一天即可，股票名稱不會天天變
def get_stock_names_dict():
    # 這裡直接呼叫證交所與櫃買中心的公開 API，自動建立字典，完全不需要維護本地檔案！
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    try:
        res = requests.get(url, timeout=10)
        df = pd.DataFrame(res.json())
        # 建立 { '2330': '台積電', '2891': '中信金' } 的字典
        return dict(zip(df['Code'], df['Name']))
    except Exception:
        # 萬一 API 掛掉，就回傳空字典，程式依然能跑，只是沒名字
        return {}

# ========================================================
# 核心資料抓取與運算
# ========================================================
@st.cache_data(ttl=3600)
def fetch_and_calculate_smart_money(lookback_days=10):
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
            
        # 核心群組運算
        grouped = recent_df.groupby(['stock_code', 'broker_name', 'broker_id']).agg(
            總買進=('buy_vol', 'sum'),
            總賣出=('sell_vol', 'sum'),
            淨買超=('net_vol', 'sum'),
            交易天數=('trade_date', 'nunique')
        ).reset_index()

        # 主力鎖碼條件
        smart_money = grouped[
            (grouped['淨買超'] > 500) & 
            (grouped['總買進'] > grouped['總賣出'] * 3) & 
            (grouped['交易天數'] >= 3)
        ]
        
        smart_money = smart_money.sort_values(by='淨買超', ascending=False).head(50)
        smart_money['券商分點'] = smart_money['broker_id'].astype(str) + " " + smart_money['broker_name']
        smart_money['股票代號'] = smart_money['stock_code'].astype(str)
        
        # 取得股票名稱對照字典，並對應上去 (找不到的就顯示 "-")
        stock_dict = get_stock_names_dict()
        smart_money['股票名稱'] = smart_money['股票代號'].map(lambda x: stock_dict.get(x, "-"))
        
        # 調整欄位順序
        smart_money = smart_money[['股票代號', '股票名稱', '券商分點', '交易天數', '總買進', '總賣出', '淨買超']]
        
        return smart_money, latest_date.strftime("%Y-%m-%d")
        
    except Exception as e:
        return pd.DataFrame(), str(e)

# --- 網頁 UI 顯示區 ---
# 💡 將最大值調整為 60
lookback = st.slider("選擇要分析的最近交易天數 (尋找短/中/長線主力)", min_value=3, max_value=60, value=10)

with st.spinner(f"📡 正在下載遠端歷史資料庫，並即時運算近 {lookback} 日籌碼..."):
    df, info = fetch_and_calculate_smart_money(lookback)

if df is not None and not df.empty:
    st.success(f"🎉 運算完成！資料已推進至最新交易日: **{info}** | 總共抓到 {len(df)} 檔鎖碼標的。")
    
    st.dataframe(
        df,
        column_config={
            "股票代號": st.column_config.TextColumn("代號"),
            "股票名稱": st.column_config.TextColumn("名稱"),
            "淨買超": st.column_config.NumberColumn("淨買超(張)", format="%d 📈"),
            "交易天數": st.column_config.NumberColumn("出手天數", format="%d 天"),
        },
        use_container_width=True,
        hide_index=True
    )
elif df is not None and df.empty:
    st.warning(f"目前沒有符合嚴格條件的標的。(最新資料日期: {info})")
else:
    st.error(f"🚨 無法取得資料，錯誤訊息: {info}")
