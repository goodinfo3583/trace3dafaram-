import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="主力囤貨雷達", page_icon="🎯", layout="wide")
st.title("🎯 主力連續收購 (鎖碼) 飆股雷達")

# ⚠️ 請確保這裡的網址是點擊 GitHub 檔案右大角的 "Raw" 按鈕後複製的網址！
TARGET_URL = "https://raw.githubusercontent.com/goodinfo3583/trace3dafaram-/main/docs/data/smart_money_targets.json"

st.info("🔍 正在啟動後台連線與資料流盲測...")

# 1. 測試網路連線與檔案是否存在
try:
    res = requests.get(TARGET_URL, timeout=10)
    st.write(f"📡 伺服器回應狀態碼: `{res.status_code}`")
    
    if res.status_code == 404:
        st.error("🚨 錯誤：GitHub 雲端找不到該 JSON 檔案！請確認 `find_smart_money.py` 是否有成功在雲端執行並生成檔案，或確認分支名稱是否為 `main`。")
    elif res.status_code == 200:
        raw_text = res.text
        st.write(f"📦 成功下載資料！檔案大小: `{len(raw_text)}` 字元。")
        
        # 顯示前 200 個字元看長怎樣
        with st.expander("👀 點開檢視雲端原始數據 (前 200 字)"):
            st.code(raw_text[:200])
            
        # 2. 嘗試解析 JSON
        try:
            json_data = res.json()
            df = pd.DataFrame(json_data)
            
            if df.empty:
                st.warning("⚠️ 雲端檔案存在，但經過『主力篩選條件』過濾後，結果為 0 筆！請調鬆 `find_smart_money.py` 的篩選標準。")
            else:
                st.success(f"🎉 成功解碼籌碼矩陣！共抓取到 `{len(df)}` 檔主力鎖碼標的。")
                
                # 顯示表格
                st.dataframe(
                    df,
                    column_config={
                        "股票代號": st.column_config.TextColumn("代號"),
                        "十日買賣超": st.column_config.NumberColumn("10日淨買超(張)", format="%d 📈"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
        except Exception as json_err:
            st.error(f"🚨 JSON 解析失敗！可能檔案格式被寫壞了。錯誤細節: {json_err}")
            
except Exception as net_err:
    st.error(f"🚨 核心網路連線崩潰！無法連接到 GitHub。錯誤細節: {net_err}")
