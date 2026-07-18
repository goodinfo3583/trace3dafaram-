import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="主力囤貨雷達", page_icon="🎯", layout="wide")
st.title("🎯 主力連續收購 (鎖碼) 飆股雷達")
st.markdown("直接解析開源巨量數據庫，抓出近期**「連續大買、只進不出」**的籌碼集中標的！")

# 🌟 這裡直接對準那位大神的 GitHub JSON 檔案！
TARGET_URL = "https://raw.githubusercontent.com/voidful/tw-institutional-stocker/main/docs/data/broker_stats.json"

@st.cache_data(ttl=3600)
def fetch_and_filter_smart_money():
    try:
        # 下載大神的 JSON
        res = requests.get(TARGET_URL, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        # 準備一個空串列來裝我們篩選出來的「飆股」
        smart_money_list = []
        
        # 解析大神的 JSON 結構
        results = data.get("results", [])
        
        for broker in results:
            broker_name = f"{broker['broker_id']} {broker['broker_name']}"
            
            # 檢查這個券商買超前 10 名的股票
            for stock in broker.get("top_buy_stocks", []):
                
                # 🎯 我們的核心鎖碼過濾條件：
                buy_vol = stock.get("total_buy_vol", 0)
                sell_vol = stock.get("total_sell_vol", 0)
                net_vol = stock.get("total_net_vol", 0)
                days = stock.get("trading_days", 0)
                
                # 條件：總買進大於 500 張 + 買進是賣出的 3 倍以上 + 至少買了 3 天
                # (因為有時候賣出是 0，為了避免除以 0 報錯，用乘法檢查)
                if net_vol > 500 and buy_vol > (sell_vol * 3) and days >= 3:
                    smart_money_list.append({
                        "券商分點": broker_name,
                        "股票代號": str(stock.get("stock_code")),
                        "股票名稱": stock.get("stock_name"),
                        "交易天數": f"{days} 天",
                        "總買進(張)": buy_vol,
                        "總賣出(張)": sell_vol,
                        "淨買超(張)": net_vol
                    })
                    
        return pd.DataFrame(smart_money_list), data.get("updated", "未知")
        
    except Exception as e:
        st.error(f"🚨 抓取遠端資料失敗！錯誤細節: {e}")
        return pd.DataFrame(), "未知"

# 執行抓取與過濾
df, update_time = fetch_and_filter_smart_money()

if not df.empty:
    st.success(f"🎉 成功攔截開源數據！資料更新時間: {update_time} | 共抓到 {len(df)} 檔鎖碼標的。")
    
    # 按照淨買超張數，由高到低排序
    df = df.sort_values(by="淨買超(張)", ascending=False)
    
    # 顯示漂亮的表格
    st.dataframe(
        df,
        column_config={
            "淨買超(張)": st.column_config.NumberColumn("10日淨買超", format="%d 📈"),
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning(f"目前沒有符合「主力鎖碼」嚴格條件的標的。(資料更新時間: {update_time})")
