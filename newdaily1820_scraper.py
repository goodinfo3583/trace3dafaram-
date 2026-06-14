import time
import random
import pandas as pd
import os
import requests
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ==========================================
# 1. 基本設定區塊
# ==========================================
SAVE_DIR = "Goodinfo_Rankings"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

today = datetime.now().strftime("%Y%m%d")
taifex_date = datetime.now().strftime("%Y/%m/%d") # 期交所需要的日期格式

print(f"啟動爬蟲系統，目標日期：{today}\n" + "="*40)

# ==========================================
# 🚀 階段一：TWSE 證交所 & TPEx 櫃買中心 API (精準狙擊版)
# ==========================================
print(">> [階段一] 執行證交所與櫃買中心 API 擷取...")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 為了防止被櫃買中心阻擋，給予完整的假瀏覽器頭
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 🎯 步驟 1：先透過上市大盤，找出「真正的最後交易日」
print(f" └─ 🔍 正在向證交所校準「最新交易日」...")
url_cal = f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={today}&response=json"
real_date_str = today # 預設為今天
roc_month = f"{int(today[:4]) - 1911}/{today[4:6]}" # 預設民國年月
res_cal_data = None 

try:
    res_cal = requests.get(url_cal, headers=headers, timeout=10, verify=False).json()
    if res_cal.get("stat") == "OK" and "data" in res_cal and len(res_cal["data"]) > 0:
        res_cal_data = res_cal # 先把資料存起來，等等直接用，省一次請求
        
        # 從最後一筆資料抓取日期 (例如 "115/06/12")
        latest_roc_date = res_cal["data"][-1][0]
        parts = latest_roc_date.split('/')
        real_year = int(parts[0]) + 1911
        
        # 組裝成通關密碼
        real_date_str = f"{real_year}{parts[1]}{parts[2]}" # 西元年月日 "20260612"
        roc_month = f"{parts[0]}/{parts[1]}"               # 民國年月 "115/06" (專門給櫃買用)
        print(f"    🎯 校準成功！避開假日，真實最後交易日為: {real_date_str}")
except Exception as e:
    print(f"    ⚠️ 校準失敗，將使用預設今日日期: {e}")


# 🎯 步驟 2：拿著正確的日期 (real_date_str)，準備一擊必殺
TWSE_APIS = {
    "大盤上市成交量": url_cal, # 網址一樣，但我們等等直接拿剛抓好的資料
    "三大法人買賣超金額": f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?date={real_date_str}&response=json",
    "鉅額交易": f"https://www.twse.com.tw/rwd/zh/block/BFIAUU?date={real_date_str}&selectType=S&response=json",
}

TPEX_APIS = {
    # 櫃買中心只吃「民國年月」最穩定，我們就給它 115/06
    "大盤上櫃成交量": f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=zh-tw&o=json&d={roc_month}", 
}

# --- 處理 TWSE (上市) ---
for name, url in TWSE_APIS.items():
    file_path = os.path.join(SAVE_DIR, f"{real_date_str}-{name}.csv")
    print(f" └─ 📡 正在直連抓取: {name}...")
    try:
        # 如果是大盤資料，剛剛校準時已經抓過了，直接轉換
        if name == "大盤上市成交量" and res_cal_data:
            res = res_cal_data
        else:
            res = requests.get(url, headers=headers, timeout=10, verify=False).json()
            time.sleep(1.5) # 乖寶寶防封鎖延遲
            
        if res.get("stat") == "OK" and "data" in res and len(res["data"]) > 0:
            df = pd.DataFrame(res["data"], columns=res.get("fields", []))
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"    ✅ 成功存檔！共 {len(df)} 筆資料。")
        else:
            print(f"    ❌ 伺服器回傳無資料。")
    except Exception as e:
        print(f"    ⚠️ 發生錯誤: {e}")

# --- 處理 TPEX (上櫃) ---
for name, url in TPEX_APIS.items():
    file_path = os.path.join(SAVE_DIR, f"{real_date_str}-{name}.csv")
    print(f" └─ 📡 正在直連抓取: {name}...")
    try:
        res = requests.get(url, headers=headers, timeout=10, verify=False).json()
        if "aaData" in res and len(res["aaData"]) > 0:
            columns = ["日期", "成交千股", "成交金額(千元)", "成交筆數", "櫃買指數", "漲跌點數"]
            df = pd.DataFrame(res["aaData"], columns=columns)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"    ✅ 成功存檔！共 {len(df)} 筆資料。")
        else:
            print(f"    ❌ 伺服器回傳無資料。")
    except Exception as e:
        print(f"    ⚠️ 發生錯誤: {e}")


# ==========================================
# 🚀 階段二：TAIFEX 期交所 HTML 扒表術
# ==========================================
print("\n>> [階段二] 執行期交所網頁解析 (TAIFEX)...")
headers = {'User-Agent': 'Mozilla/5.0'}

# 1. 臺指選擇權PC比
print(" └─ 📡 正在抓取: 臺指選擇權PC比...")
try:
    res = requests.post("https://www.taifex.com.tw/cht/3/pcRatio", data={"queryStartDate": taifex_date, "queryEndDate": taifex_date}, headers=headers)
    dfs = pd.read_html(StringIO(res.text))
    for df in dfs:
        if '買賣權未平倉量比率%' in df.columns or (isinstance(df.columns, pd.MultiIndex) and '買賣權未平倉量比率%' in [c[-1] for c in df.columns]):
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            df.to_csv(os.path.join(SAVE_DIR, f"{today}-臺指選擇權PC比.csv"), index=False, encoding='utf-8-sig')
            print(f"    ✅ 成功存檔！")
            break
except Exception as e: print(f"    ⚠️ 失敗: {e}")

# 2. 三大法人期貨多空 (TX)
print(" └─ 📡 正在抓取: 三大法人期貨多空單...")
try:
    res = requests.post("https://www.taifex.com.tw/cht/3/futContractsDate", data={"queryDate": taifex_date}, headers=headers)
    dfs = pd.read_html(StringIO(res.text))
    for df in dfs:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{c[0]}_{c[1]}" if c[0] != c[1] else c[0] for c in df.columns]
        
        if df.astype(str).apply(lambda x: x.str.contains('外資').any()).any():
            df.to_csv(os.path.join(SAVE_DIR, f"{today}-三大法人期貨多空.csv"), index=False, encoding='utf-8-sig')
            print(f"    ✅ 成功存檔！")
            break
except Exception as e: print(f"    ⚠️ 失敗: {e}")

# 3. 臺指選擇權行情簡表 (⭐ 終極暴力找表法 + 精準導彈版 ⭐)
print(" └─ 📡 正在抓取: 臺指選擇權行情簡表...")
try:
    # 🔑 關鍵修復：補上 "commodity_id": "TXO"，明確告訴期交所我們要抓「臺指選擇權」！
    payload = {
        "queryDate": taifex_date, 
        "MarketCode": "0", 
        "commodity_id": "TXO" 
    }
    res = requests.post("https://www.taifex.com.tw/cht/3/optDailyMarketReport", data=payload, headers=headers)
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 暴力破解：找出網頁中所有的 table，只要裡面有「履約價」三個字，就是我們要的！
    tables = soup.find_all('table')
    target_table = None
    for tb in tables:
        if '履約價' in tb.text:
            target_table = str(tb)
            break
            
    if target_table:
        df = pd.read_html(StringIO(target_table))[0]
        
        # 🔑 智慧合併多層表頭 (過濾 Unnamed 與重複字眼)
        if isinstance(df.columns, pd.MultiIndex):
            new_cols = []
            for c in df.columns:
                valid_parts = []
                for part in c:
                    part_str = str(part).strip()
                    if "Unnamed" not in part_str and part_str not in valid_parts:
                        valid_parts.append(part_str)
                new_cols.append("_".join(valid_parts))
            df.columns = new_cols
        
        # 🔑 過濾掉網頁中的「小計」列，只保留真正的數字資料
        strike_col = next((col for col in df.columns if '履約價' in col), None)
        if strike_col:
            df[strike_col] = pd.to_numeric(df[strike_col], errors='coerce')
            df = df.dropna(subset=[strike_col])
            
        if not df.empty:
            df.to_csv(os.path.join(SAVE_DIR, f"{today}臺指選擇權行情簡表.csv"), index=False, encoding='utf-8-sig')
            print(f"    ✅ 成功存檔！共抓取 {len(df)} 筆精準選擇權資料。")
        else:
            print(f"    ❌ 表格內容為空，可能今日尚未結算。")
    else:
        print(f"    ❌ 找不到包含「履約價」的資料表格。")
except Exception as e: 
    print(f"    ⚠️ 失敗: {e}")


# ==========================================
# 🐢 階段三：Goodinfo 模擬點擊瀏覽器
# ==========================================
GOODINFO_TARGETS = {
    "外資賣出佔成交比(3日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E8%B3%A3%E5%87%BA%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+3%E6%97%A5%40%40%E5%A4%96%E8%B3%87%E8%B3%A3%E5%87%BA%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E5%A4%96%E8%B3%87+%E2%80%93+3%E6%97%A5",
    "外資買超佔成交比(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E8%B2%B7%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+5%E6%97%A5%40%40%E5%A4%96%E8%B3%87%E8%B2%B7%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E5%A4%96%E8%B3%87+%E2%80%93+5%E6%97%A5",
    "外資買超佔發行張數(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E8%B2%B7%E8%B6%85%E4%BD%94%E7%99%BC%E8%A1%8C%E5%BC%B5%E6%95%B8+%E2%80%93+5%E6%97%A5%40%40%E5%A4%96%E8%B3%87%E8%B2%B7%E8%B6%85%E4%BD%94%E7%99%BC%E8%A1%8C%E5%BC%B5%E6%95%B8%40%40%E5%A4%96%E8%B3%87+%E2%80%93+5%E6%97%A5",
    "投信買超佔成交比(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8A%95%E4%BF%A1%E8%B2%B7%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+5%E6%97%A5%40%40%E6%8A%95%E4%BF%A1%E8%B2%B7%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E6%8A%95%E4%BF%A1+%E2%80%93+5%E6%97%A5",
    "投信賣出佔成交比(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8A%95%E4%BF%A1%E8%B3%A3%E5%87%BA%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+5%E6%97%A5%40%40%E6%8A%95%E4%BF%A1%E8%B3%A3%E5%87%BA%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E6%8A%95%E4%BF%A1+%E2%80%93+5%E6%97%A5",
    "投信買超佔發行張數(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8A%95%E4%BF%A1%E8%B2%B7%E8%B6%85%E4%BD%94%E7%99%BC%E8%A1%8C%E5%BC%B5%E6%95%B8+%E2%80%93+5%E6%97%A5%40%40%E6%8A%95%E4%BF%A1%E8%B2%B7%E8%B6%85%E4%BD%94%E7%99%BC%E8%A1%8C%E5%BC%B5%E6%95%B8%40%40%E6%8A%95%E4%BF%A1+%E2%80%93+5%E6%97%A5",
    "成交價1-300名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "成交價301-600名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "成交價601-900名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "外資連續買超(週)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E9%80%A3%E8%B2%B7+%E2%80%93+%E9%80%B1%40%40%E5%A4%96%E8%B3%87%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85%40%40%E5%A4%96%E8%B3%87%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85+%E2%80%93+%E9%80%B1",
    "外資連續買超(日)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E9%80%A3%E8%B2%B7+%E2%80%93+%E6%97%A5%40%40%E5%A4%96%E8%B3%87%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85%40%40%E5%A4%96%E8%B3%87%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85+%E2%80%93+%E6%97%A5",
    "投信連續買超(週)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E6%8A%95%E4%BF%A1%E9%80%A3%E8%B2%B7+%E2%80%93+%E9%80%B1%40%40%E6%8A%95%E4%BF%A1%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85%40%40%E6%8A%95%E4%BF%A1%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85+%E2%80%93+%E9%80%B1",
    "投信連續買超(日)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E6%8A%95%E4%BF%A1%E9%80%A3%E8%B2%B7+%E2%80%93+%E6%97%A5%40%40%E6%8A%95%E4%BF%A1%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85%40%40%E6%8A%95%E4%BF%A1%E9%80%A3%E7%BA%8C%E8%B2%B7%E8%B6%85+%E2%80%93+%E6%97%A5",
    "三大法人賣超佔成交比(5日累計排名)":"https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B3%A3%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+5%E6%97%A5%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B3%A3%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA+%E2%80%93+5%E6%97%A5",
    "外資賣超佔成交比(3日累計排名)":"https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E8%B3%A3%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+3%E6%97%A5%40%40%E5%A4%96%E8%B3%87%E8%B3%A3%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E5%A4%96%E8%B3%87+%E2%80%93+3%E6%97%A5",
    "外資持股比例1-300名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例301-600名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例601-900名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例901-1200名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例1201-1500名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例1501-1800名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例1801-2100名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "外資持股比例2101-2315名":"https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%A4%96%E8%B3%87%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B",
    "三大法人買超佔成交比(5日累計排名)":"https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B2%B7%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94+%E2%80%93+5%E6%97%A5%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B2%B7%E8%B6%85%E4%BD%94%E6%88%90%E4%BA%A4%E6%AF%94%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA+%E2%80%93+5%E6%97%A5",
}

print("\n>> [階段三] 啟動 Google Chrome 瀏覽器 (針對 Goodinfo)...")
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.page_load_strategy = 'eager' 

# 👇 為了在 GitHub Actions 運行，這四行絕對不能少！ 👇
options.add_argument('--headless=new')             
options.add_argument('--no-sandbox')               
options.add_argument('--disable-dev-shm-usage')    
options.add_argument('--disable-gpu')              
# 👆 ------------------------------------------- 👆

try:
    driver = webdriver.Chrome(options=options)
except Exception as e:
    print(f"啟動 Chrome 失敗！錯誤細節: {e}")
    exit()

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

print(f"開始執行 Goodinfo 下載任務，共計 {len(GOODINFO_TARGETS)} 個檔案。\n" + "-"*40)

for index, (name_suffix, url) in enumerate(GOODINFO_TARGETS.items()):
    file_name = f"{today}{name_suffix}.csv"
    file_path = os.path.join(SAVE_DIR, file_name)
    
    print(f"[{index+1}/{len(GOODINFO_TARGETS)}] 正在擷取: {file_name}")
    
    try:
        driver.get(url)
        
        target_rank = None
        if "301" in name_suffix and "600" in name_suffix:
            target_rank = ("301", "600")
        elif "601" in name_suffix and "900" in name_suffix:
            target_rank = ("601", "900")
            
        if target_rank:
            print(f" └─ 🔍 偵測到需要切換名次，幫你自動點擊下拉選單 ({target_rank[0]}-{target_rank[1]} 名)...")
            time.sleep(5) 
            try:
                options_elements = driver.find_elements(By.TAG_NAME, "option")
                for opt in options_elements:
                    if target_rank[0] in opt.text and target_rank[1] in opt.text:
                        opt.click()
                        parent_select = opt.find_element(By.XPATH, "..")
                        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", parent_select)
                        print(f" └─ 🖱️ 成功點擊切換名次！等待網頁重新載入...")
                        time.sleep(8) 
                        break
            except Exception as e:
                print(f" └─ ⚠️ 無法自動切換選單: {e}")
        
        print(" └─ 等待網頁驗證、略過廣告與表格載入 (最長 60 秒)...")
        target_df = None
        
        for i in range(60): 
            try:
                html = driver.page_source
                tables = pd.read_html(StringIO(html))
                
                for df in tables:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    df.columns = [str(col).strip() for col in df.columns]
                    
                    if '代號' in df.columns or '名稱' in df.columns:
                        if len(df) > 5:
                            target_df = df
                            break 
                if target_df is not None:
                    print(f" └─ ⚡ 成功解析表格！(耗時約 {i+1} 秒)")
                    break 
            except Exception:
                pass
            time.sleep(1) 
            
        if target_df is not None:
            if '代號' in target_df.columns:
                target_df = target_df[target_df['代號'] != '代號'] 
            
            target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f" └─ ✅ 成功存檔！")
        else:
            print(f" └─ ❌ 失敗！等了 60 秒還是沒有看到股票資料。")
            driver.save_screenshot(f"error_shot_{index+1}.png")
            
    except Exception as e:
        print(f" └─ ⚠️ 發生未知的錯誤: {e}")
    
    if index < len(GOODINFO_TARGETS) - 1:
        sleep_time = random.uniform(20, 40)
        print(f" └─ [防封鎖] 隨機休息 {sleep_time:.2f} 秒...\n")
        time.sleep(sleep_time)

print("-" * 40 + "\n🎉 爬蟲任務全數完成！趕快去資料夾檢查熱騰騰的 CSV 吧！")
driver.quit()
