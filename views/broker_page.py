#views/broker_page.py
import streamlit as st
import pandas as pd
# 引入你剛剛寫好的工具箱
from utils.data_utils import calculate_chip_concentration

def render():
    """券商分點頁面的主畫面邏輯"""
    st.title("🕵️‍♂️ 主力券商分點追蹤 (Beta)")
    st.markdown("透過每日全市場券商進出明細，追蹤大戶籌碼集中度。")
    
    # 建立一個輸入框讓你可以自由更換股票
    # 預設放入你想觀察的 1709，你也可以隨時改成 2330 或 3413
    target_stock = st.text_input("請輸入要查詢的股票代號：", value="1709", max_chars=4)
    
    if target_stock:
        st.info(f"正在從遠端資料庫撈取 **{target_stock}** 的籌碼明細，請稍候...")
        
        # 你的 tw-broker-data 遠端資料庫網址
        remote_csv_url = "https://raw.githubusercontent.com/goodinfo3583/tw-broker-data/main/data/broker/broker_history.csv"
        
        try:
            # 呼叫工具箱進行計算
            df = calculate_chip_concentration(remote_csv_url, target_stock)
            
            if not df.empty:
                st.success("✅ 數據載入成功！")
                
                # 顯示最新一天的集中度數據卡片
                latest_data = df.iloc[-1]
                st.metric(
                    label=f"{latest_data['trade_date']} 最新籌碼集中度", 
                    value=f"{latest_data['concentration_%']}%",
                    delta=f"淨買超 {latest_data['net_buy']:,} 張"
                )
                
                # 畫出美美的長條圖
                st.subheader(f"📊 {target_stock} 近期籌碼集中度走勢")
                st.bar_chart(df, x="trade_date", y="concentration_%")
                
                # 附上原始數據表供查閱
                with st.expander("查看詳細數據表"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"⚠️ 找不到 **{target_stock}** 的資料。可能是這檔股票最近沒有被抓取，或遠端資料尚未更新。")
                
        except Exception as e:
            st.error(f"讀取資料失敗：{e}")
