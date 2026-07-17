import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="主力囤貨雷達", page_icon="🎯", layout="wide")
st.title("🎯 主力連續收購 (鎖碼) 飆股雷達")
st.markdown("這裡顯示最近 10 天內，被單一券商分點**「連續大買、且幾乎不賣」**的籌碼集中標的。")

# 這裡填寫你 GitHub 上的 JSON Raw 網址
TARGET_URL = "https://raw.githubusercontent.com/goodifo3583/trace3dafaram-/main/docs/data/smart_money_targets.json"

@st.cache_data(ttl=3600)
def load_smart_money():
    try:
        res = requests.get(TARGET_URL)
        res.raise_for_status()
        return pd.DataFrame(res.json())
    except:
        return pd.DataFrame()

df = load_smart_money()

if not df.empty:
    st.dataframe(
        df,
        column_config={
            "股票代號": st.column_config.TextColumn("代號"),
            "十日買賣超": st.column_config.NumberColumn("10日淨買超(張)", format="%d 📈"),
            "十日總買進": st.column_config.NumberColumn("10日買進總量"),
            "十日總賣出": st.column_config.NumberColumn("10日賣出總量"),
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("目前尚未產生主力囤貨名單，或網路讀取失敗。")
