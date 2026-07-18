import streamlit as st
import pandas as pd

st.set_page_config(page_title="主力囤貨雷達", page_icon="🎯", layout="wide")
st.title("🎯 主力連續收購 (鎖碼) 飆股雷達")
st.markdown("直接剖析開源專案 **60 日歷史總表 (`broker_history.csv`)**，精準抓出只進不出的鎖碼大戶！")

# 🌟 直接對準那份 2.6MB 的歷史大補帖！
TARGET_URL = "https://raw.githubusercontent.com/voidful/tw-institutional-stocker/main/data/broker/broker_history.csv"

@st.cache_data(ttl=3600)  # 快取一小時
def fetch_and_calculate_smart_money(lookback_days=10):
    try:
        # 1. 瞬間下載並讀取 2.6MB 的 CSV
        df = pd.read_csv(TARGET_URL)
        
        # 2. 確保日期格式正確，並找出最新的交易日
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        latest_date = df['trade_date'].max()
        
        # 3. 根據你想要的回測天數，切出「最近 N 天」的資料
        cutoff_date = latest_date - pd.Timedelta(days=lookback_days * 1.5) # 乘以1.5是為了包含假日
        recent_df = df[df['trade_date'] >= cutoff_date]
        
        # 如果切出來的天數大於我們設定的，就精確取最後 N 個交易日
        unique_dates = sorted(recent_df['trade_date'].unique(), reverse=True)
        if len(unique_dates) > lookback_days:
            exact_cutoff = unique_dates[lookback_days - 1]
            recent_df = recent_df[recent_df['trade_date'] >= exact_cutoff]
            
        # 4. 核心群組運算 (找出同一家券商對同一檔股票的總買賣)
        grouped = recent_df.groupby(['stock_code', 'broker_name', 'broker_id']).agg(
            十日總買進=('buy_vol', 'sum'),
            十日總賣出=('sell_vol', 'sum'),
            十日買賣超=('net_vol', 'sum'),
            交易天數=('trade_date', 'nunique')
        ).reset_index()

        # 5. 主力鎖碼嚴格條件：淨買超 > 500，買進大於賣出的 3 倍，且至少買了 3 天
        smart_money = grouped[
            (grouped['十日買賣超'] > 500) & 
            (grouped['十日總買進'] > grouped['十日總賣出'] * 3) & 
            (grouped['交易天數'] >= 3)
        ]
        
        # 排序與美化欄位名稱
        smart_money = smart_money.sort_values(by='十日買賣超', ascending=False).head(50)
        smart_money['券商分點'] = smart_money['broker_id'].astype(str) + " " + smart_money['broker_name']
        smart_money = smart_money[['stock_code', '券商分點', '交易天數', '十日總買進', '十日總賣出', '十日買賣超']]
        smart_money = smart_money.rename(columns={'stock_code': '股票代號'})
        
        return smart_money, latest_date.strftime("%Y-%m-%d")
        
    except Exception as e:
        return pd.DataFrame(), str(e)

# --- 網頁 UI 顯示區 ---
# 加上一個滑桿，讓你隨時可以動態調整要看「最近幾天」的主力
lookback = st.slider("選擇要分析的最近交易天數 (尋找短/中/長線主力)", min_value=3, max_value=30, value=10)

with st.spinner(f"📡 正在下載遠端歷史資料庫，並即時運算近 {lookback} 日籌碼..."):
    df, info = fetch_and_calculate_smart_money(lookback)

if df is not None and not df.empty:
    st.success(f"🎉 運算完成！資料已推進至最新交易日: **{info}** | 總共抓到 {len(df)} 檔鎖碼標的。")
    
    st.dataframe(
        df,
        column_config={
            "股票代號": st.column_config.TextColumn("代號"),
            "十日買賣超": st.column_config.NumberColumn("淨買超(張)", format="%d 📈"),
            "交易天數": st.column_config.NumberColumn("出手天數", format="%d 天"),
        },
        use_container_width=True,
        hide_index=True
    )
elif df is not None and df.empty:
    st.warning(f"目前沒有符合嚴格條件的標的。(最新資料日期: {info})")
else:
    st.error(f"🚨 無法取得遠端資料，錯誤訊息: {info}")
