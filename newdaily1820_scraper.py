import time
import random
import pandas as pd
import os
import requests
from io import StringIO
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 
# 🌟 匯入終極突破武器 🌟
from seleniumbase import Driver
import subprocess
import re

# ==========================================
# 1. 基本設定區塊
# ==========================================
SAVE_DIR = "data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

today = datetime.now().strftime("%Y%m%d")
taifex_date = datetime.now().strftime("%Y/%m/%d")

print(f"啟動爬蟲系統，目標日期：{today}\n" + "="*40)

# ==========================================
# 🚀 階段一：TWSE 證交所 & TPEx 櫃買中心 API 
# ==========================================
print(">> [階段一] 執行證交所與櫃買中心 API 擷取...")

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Referer': 'https://www.tpex.org.tw/',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest'
}

print(f" └─ 🔍 正在向證交所校準「最新交易日」...")
url_cal = f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={today}&response=json"
real_date_str = today 
roc_full_date = f"{int(today[:4]) - 1911}/{today[4:6]}/{today[6:]}" 
roc_month = f"{int(today[:4]) - 1911}/{today[4:6]}" 
res_cal_data = None 

try:
    res_cal = session.get(url_cal, headers=headers, timeout=10, verify=False).json()
    if res_cal.get("stat") == "OK" and "data" in res_cal and len(res_cal["data"]) > 0:
        res_cal_data = res_cal 
        latest_roc_date = res_cal["data"][-1][0]
        parts = latest_roc_date.split('/')
        real_year = int(parts[0]) + 1911
        real_date_str = f"{real_year}{parts[1].zfill(2)}{parts[2].zfill(2)}"
        roc_full_date = latest_roc_date 
        roc_month = f"{parts[0]}/{parts[1].zfill(2)}" 
        print(f"    🎯 校準成功！真實最新交易日為: {real_date_str}")
except Exception as e:
    print(f"    ⚠️ 校準失敗，將使用系統今日日期: {e}")

TWSE_APIS = {
    "大盤上市成交量": url_cal,
    "三大法人買賣超金額": f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?date={real_date_str}&response=json",
    "鉅額交易": f"https://www.twse.com.tw/rwd/zh/block/BFIAUU?date={real_date_str}&selectType=S&response=json",
}

for name, url in TWSE_APIS.items():
    file_path = os.path.join(SAVE_DIR, f"{real_date_str}-{name}.csv")
    print(f" └─ 📡 正在直連抓取: {name}...")
    try:
        if name == "大盤上市成交量" and res_cal_data:
            res = res_cal_data 
        else:
            time.sleep(1.5) 
            res = session.get(url, headers=headers, timeout=10, verify=False).json()
            
        if res.get("stat") == "OK" and "data" in res and len(res["data"]) > 0:
            df = pd.DataFrame(res["data"], columns=res.get("fields", []))
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"    ✅ 成功存檔！共 {len(df)} 筆資料。")
        else:
            print(f"    ❌ 伺服器回傳無資料。")
    except Exception as e:
        print(f"    ⚠️ 發生錯誤: {e}")

name = "大盤上櫃成交量"
file_path = os.path.join(SAVE_DIR, f"{real_date_str}-{name}.csv")
print(f" └─ 📡 正在直連抓取: {name}...")

try:
    session.get("https://www.tpex.org.tw/zh-tw/", headers=headers, timeout=5, verify=False)
except:
    pass

tpex_urls = [
    f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=zh-tw&o=json&d={roc_full_date}", 
    f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=zh-tw&o=json&d={roc_month}",
    f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=zh-tw&o=json"
]

tpex_success = False
for url in tpex_urls:
    time.sleep(1.5) 
    try:
        res = session.get(url, headers=headers, timeout=10, verify=False)
        if res.status_code == 200:
            res_json = res.json()
            if "tables" in res_json and len(res_json["tables"]) > 0 and "data" in res_json["tables"][0]:
                data_list = res_json["tables"][0]["data"]
                if len(data_list) > 0:
                    columns = ["日期", "成交千股", "成交金額(千元)", "成交筆數", "櫃買指數", "漲跌點數"]
                    df = pd.DataFrame(data_list, columns=columns)
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    print(f"    ✅ 成功存檔！共 {len(df)} 筆資料。")
                    tpex_success = True
                    break
    except Exception:
        pass 

if not tpex_success:
    print(f"    ❌ 伺服器回傳無資料 (可能是非交易日或伺服器異常)。")

# ==========================================
# 🚀 階段二：TAIFEX 期交所 HTML 扒表術
# ==========================================
print("\n>> [階段二] 執行期交所網頁解析 (TAIFEX)...")
headers = {'User-Agent': 'Mozilla/5.0'}

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

print(" └─ 📡 正在抓取: 臺指選擇權行情簡表...")
try:
    payload = {
        "queryDate": taifex_date, 
        "MarketCode": "0", 
        "commodity_id": "TXO" 
    }
    res = requests.post("https://www.taifex.com.tw/cht/3/optDailyMarketReport", data=payload, headers=headers)
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(res.text, 'html.parser')
    
    tables = soup.find_all('table')
    target_table = None
    for tb in tables:
        if '履約價' in tb.text:
            target_table = str(tb)
            break
            
    if target_table:
        df = pd.read_html(StringIO(target_table))[0]
        
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
# 🐢 階段三：Goodinfo 模擬點擊瀏覽器 (多國語言雷達修正版)
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
    "成交價901-1200名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "成交價1201-1500名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "成交價1501-1800名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "成交價1801-2100名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
    "成交價2101-2392名(高→低)": "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%88%90%E4%BA%A4%E5%83%B9+%28%E9%AB%98%E2%86%92%E4%BD%8E%29%40%40%E6%88%90%E4%BA%A4%E5%83%B9%40%40%E7%94%B1%E9%AB%98%E2%86%92%E4%BD%8E",
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
# ==========================================
# 🐢 階段三：Goodinfo 模擬點擊瀏覽器 (SeleniumBase 破甲版)
# ==========================================
print("\n>> [階段三] 啟動 SeleniumBase (UC 模式) 瀏覽器...")

version_main = None
try:
    out = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
    match = re.search(r'(\d+)\.', out)
    if match: version_main = int(match.group(1))
    print(f" └─ 🔍 自動偵測到伺服器 Chrome 主版本為: {version_main}")
except Exception: pass

if version_main:
    ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version_main}.0.0.0 Safari/537.36"
else:
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

try:
    # 🌟 啟動 SeleniumBase UC 模式
    # 因為你的環境有掛 xvfb-run (虛擬顯示器)，所以 headless 必須設為 False
    driver = Driver(
        uc=True,               # 啟動反偵測模式
        headless=False,        # 交由 xvfb 處理畫面，不使用瀏覽器原生 headless
        agent=ua,              # 套用 Windows User-Agent
        no_sandbox=True,
        disable_gpu=True,
        window_size="1920,1080"
    )
    
    # CDP 深度偽裝依然完美相容
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {'timezoneId': 'Asia/Taipei'})
    driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {'latitude': 25.0330, 'longitude': 121.5654, 'accuracy': 100})
    driver.execute_cdp_cmd('Emulation.setUserAgentOverride', {
        "userAgent": ua,
        "acceptLanguage": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "platform": "Win32" 
    })
    print(" └─ 🎭 CDP 深度偽裝完成：已切換為台灣時區與 Windows 平台！")
except Exception as e:
    print(f"啟動 Chrome 失敗！錯誤細節: {e}")
    exit()

print(f"開始執行 Goodinfo 下載任務，共計 {len(GOODINFO_TARGETS)} 個檔案。\n" + "-"*40)

CF_KEYWORDS = ["Just a moment", "Cloudflare", "請稍候", "Attention", "驗證"]

for index, (name_suffix, url) in enumerate(GOODINFO_TARGETS.items()):
    file_name = f"{today}{name_suffix}.csv"
    file_path = os.path.join(SAVE_DIR, file_name)
    print(f"[{index+1}/{len(GOODINFO_TARGETS)}] 正在擷取: {file_name}")
    
    try:
        # 🌟 SeleniumBase 專屬破盾絕招 1：帶有繞過機制的開啟方式
        driver.uc_open_with_reconnect(url, reconnect_time=4)
        time.sleep(3) 
        
        is_cf_blocked = False
        if any(kw in driver.title for kw in CF_KEYWORDS) or "cf-turnstile" in driver.page_source:
            is_cf_blocked = True

        if is_cf_blocked:
            print(f" └─ 🛡️ 遇到 Cloudflare 驗證畫面 (標題: {driver.title})，啟動 SeleniumBase 自動破盾機制...")
            try:
                # 🌟 SeleniumBase 專屬破盾絕招 2：自動尋找 iframe 並點擊核取方塊
                # 這行直接取代了原本所有複雜的 Tab、空白鍵與座標計算！
                driver.uc_gui_click_captcha()
                print(" └─ 🎯 成功執行自動點擊指令！")
                time.sleep(5)
            except Exception as e:
                print(f" └─ ⚠️ 自動點擊遇障礙，等待跳轉: {e}")
            
            # 檢查是否通關
            if not any(kw in driver.title for kw in CF_KEYWORDS):
                print(" └─ 🔓 Cloudflare 盾牌已成功擊破！")
        # ==========================================================
        
        target_start = None
        match = re.search(r'(\d+)-\d+名', name_suffix)
        if match and match.group(1) != "1": 
            target_start = match.group(1)
            
        if target_start:
            print(f" └─ 🔍 偵測到需要切換名次，幫你自動點擊下拉選單 ({target_start} 名起)...")
            time.sleep(5) 
            try:
                options_elements = driver.find_elements(By.TAG_NAME, "option")
                for opt in options_elements:
                    if target_start in opt.text:
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
                if i == 30:
                    print(" └─ 🔄 網頁似乎載入卡住，嘗試強制重新整理...")
                    driver.refresh()
                    time.sleep(3)
                    continue
                    
                tables = pd.read_html(StringIO(html))
                for df in tables:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    df.columns = [str(col).strip() for col in df.columns]
                    
                    if '代號' in df.columns or '名稱' in df.columns:
                        if len(df) >= 1: 
                            target_df = df
                            break 
                if target_df is not None:
                    print(f" └─ ⚡ 成功解析表格！(耗時約 {i+1} 秒)")
                    break 
            except Exception: pass
            time.sleep(1) 
            
        if target_df is not None:
            if '代號' in target_df.columns:
                target_df = target_df[target_df['代號'] != '代號'] 
            
            target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f" └─ ✅ 成功存檔！")
        else:
            print(f" └─ ❌ 失敗！盲測診斷標題：【{driver.title}】")
            driver.save_screenshot(f"error_shot_{index+1}.png")
            
    except Exception as e:
        print(f" └─ ⚠️ 發生未知的錯誤: {e}")
    
    if index < len(GOODINFO_TARGETS) - 1:
        sleep_time = random.uniform(20, 40)
        print(f" └─ [防封鎖] 隨機休息 {sleep_time:.2f} 秒...\n")
        time.sleep(sleep_time)

print("-" * 40 + "\n🎉 爬蟲任務全數完成！")
driver.quit()
