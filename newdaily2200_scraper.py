import time
import random
import pandas as pd
import os
from io import StringIO
from datetime import datetime
from selenium.webdriver.common.by import By
# 🌟 匯入終極突破武器 🌟
import undetected_chromedriver as uc 
import subprocess
import re
# ==========================================
# 1. 設定區塊
# ==========================================
SAVE_DIR = "data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

today = datetime.now().strftime("%Y%m%d")

TARGETS = {
    "融資融券餘額(TWSE)": "https://www.twse.com.tw/zh/trading/margin/mi-margn.html", 
    "借券賣出減少張數(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%80%9F%E5%88%B8%E8%B3%A3%E5%87%BA%E6%B8%9B%E5%B0%91%E5%BC%B5%E6%95%B8+%285%E6%97%A5%29%40%40%E5%80%9F%E5%88%B8%E8%B3%A3%E5%87%BA%E5%A2%9E%E6%B8%9B%E5%BC%B5%E6%95%B8%40%40%E6%B8%9B%E5%B0%91%E5%BC%B5%E6%95%B8+%E2%80%93+5%E6%97%A5",
    "融資減少張數(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E8%9E%8D%E8%B3%87%E6%B8%9B%E5%B0%91%E5%BC%B5%E6%95%B8+%285%E6%97%A5%29%40%40%E8%9E%8D%E8%B3%87%E5%A2%9E%E6%B8%9B%E5%BC%B5%E6%95%B8%40%40%E6%B8%9B%E5%B0%91%E5%BC%B5%E6%95%B8+%E2%80%93+5%E6%97%A5",
    "融券增加張數(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E8%9E%8D%E5%88%B8%E5%A2%9E%E5%8A%A0%E5%BC%B5%E6%95%B8+%285%E6%97%A5%29%40%40%E8%9E%8D%E5%88%B8%E5%A2%9E%E6%B8%9B%E5%BC%B5%E6%95%B8%40%40%E5%A2%9E%E5%8A%A0%E5%BC%B5%E6%95%B8+%E2%80%93+5%E6%97%A5",
    "融資減少幅度(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E8%9E%8D%E8%B3%87%E6%B8%9B%E5%B0%91%E5%B9%85%E5%BA%A6+%285%E6%97%A5%29%40%40%E8%9E%8D%E8%B3%87%E5%A2%9E%E6%B8%9B%E5%B9%85%E5%BA%A6%40%40%E6%B8%9B%E5%B0%91%E5%B9%85%E5%BA%A6+%E2%80%93+5%E6%97%A5",
    "融券增加幅度(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E8%9E%8D%E5%88%B8%E5%A2%9E%E5%8A%A0%E5%B9%85%E5%BA%A6+%285%E6%97%A5%29%40%40%E8%9E%8D%E5%88%B8%E5%A2%9E%E6%B8%9B%E5%B9%85%E5%BA%A6%40%40%E5%A2%9E%E5%8A%A0%E5%B9%85%E5%BA%A6+%E2%80%93+5%E6%97%A5",
    "借券賣出減少幅度(5日累計排名)" :"https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%80%9F%E5%88%B8%E8%B3%A3%E5%87%BA%E6%B8%9B%E5%B0%91%E5%B9%85%E5%BA%A6+%285%E6%97%A5%29%40%40%E5%80%9F%E5%88%B8%E8%B3%A3%E5%87%BA%E5%A2%9E%E6%B8%9B%E5%B9%85%E5%BA%A6%40%40%E6%B8%9B%E5%B0%91%E5%B9%85%E5%BA%A6+%E2%80%93+5%E6%97%A5",
    "融資增加幅度(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E8%9E%8D%E8%B3%87%E5%A2%9E%E5%8A%A0%E5%B9%85%E5%BA%A6+%283%E6%97%A5%29%40%40%E8%9E%8D%E8%B3%87%E5%A2%9E%E6%B8%9B%E5%B9%85%E5%BA%A6%40%40%E5%A2%9E%E5%8A%A0%E5%B9%85%E5%BA%A6+%E2%80%93+3%E6%97%A5",
    "借券賣出增加幅度(5日累計排名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%80%9F%E5%88%B8%E8%B3%A3%E5%87%BA%E5%A2%9E%E5%8A%A0%E5%B9%85%E5%BA%A6+%285%E6%97%A5%29%40%40%E5%80%9F%E5%88%B8%E8%B3%A3%E5%87%BA%E5%A2%9E%E6%B8%9B%E5%B9%85%E5%BA%A6%40%40%E5%A2%9E%E5%8A%A0%E5%B9%85%E5%BA%A6+%E2%80%93+5%E6%97%A5"
    "董監庫藏股(1-300名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29",
    "董監庫藏股(301-600名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29",
    "董監庫藏股(601-900名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29",
    "董監庫藏股(901-1200名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29", 
    "董監庫藏股(1201-1500名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29",
    "董監庫藏股(1501-1800名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29",
    "董監庫藏股(1801-1967名(高→低)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%BA%AB%E8%97%8F%E8%82%A1%E7%A5%A8%40%40%E6%8C%81%E8%82%A1%E6%AF%94%E4%BE%8B%28%25%29",
}

# ==========================================
# 2. 啟動瀏覽器 (undetected-chromedriver 模式)
# ==========================================
print("\n>> 正在啟動 Google Chrome 瀏覽器 (使用 undetected_chromedriver 破甲版)...")
options = uc.ChromeOptions()

# 🌟 我們現在有 Xvfb 虛擬螢幕，所以不需要 --headless
options.add_argument('--no-sandbox')               
options.add_argument('--disable-dev-shm-usage')    
options.add_argument('--disable-gpu')              
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
options.add_argument('--window-size=1920,1080')

# 🌟 關鍵修復：自動偵測 GitHub 虛擬機的 Chrome 版本，防止 ChromeDriver 版本暴衝不匹配
version_main = None
try:
    # 透過指令查詢系統內的 Chrome 版本
    out = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
    match = re.search(r'(\d+)\.', out)
    if match:
        version_main = int(match.group(1))
        print(f" └─ 🔍 自動偵測到伺服器 Chrome 主版本為: {version_main}")
except Exception as e:
    print(f" └─ ⚠️ 無法自動偵測 Chrome 版本，將使用預設設定。")

try:
    # 🎯 這裡加上 version_main 參數，強迫驅動程式與瀏覽器版本同步！
    if version_main:
        driver = uc.Chrome(options=options, version_main=version_main)
    else:
        driver = uc.Chrome(options=options)
except Exception as e:
    print(f"啟動 Chrome 失敗！錯誤細節: {e}")
    exit()

# ==========================================
# 3. 執行抓取與表格解析
# ==========================================
print(f"\n開始執行下載任務，共計 {len(TARGETS)} 個檔案。\n日期標籤：{today}\n" + "-"*40)

for index, (name_suffix, url) in enumerate(TARGETS.items()):
    file_name = f"{today}{name_suffix}.csv"
    file_path = os.path.join(SAVE_DIR, file_name)
    
    print(f"[{index+1}/{len(TARGETS)}] 正在擷取: {name_suffix}")
    
    try:
        driver.get(url)
        
        # 針對 Goodinfo 的自動選單點擊邏輯
        target_rank = None
        if "301" in name_suffix and "600" in name_suffix:
            target_rank = ("301", "600")
        elif "601" in name_suffix and "900" in name_suffix:
            target_rank = ("601", "900")
            
        if target_rank and "goodinfo" in url:
            print(f" └─ 🔍 偵測到需要切換名次，自動點擊選單 ({target_rank[0]}-{target_rank[1]} 名)...")
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
        
        print(" └─ 正在等待網頁驗證、略過廣告與表格載入 (最長等待 60 秒)...")
        target_df = None
        
        for i in range(60): 
            try:
                html = driver.page_source
                tables = pd.read_html(StringIO(html))
                
                for df in tables:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    
                    df.columns = [str(col).strip() for col in df.columns]
                    
                    # 雙模辨識
                    has_goodinfo_cols = any('代號' in col or '名稱' in col for col in df.columns)
                    has_twse_cols = any('項目' in col or '今日餘額' in col for col in df.columns)
                    
                    if has_goodinfo_cols or has_twse_cols:
                        if len(df) >= 2:  
                            target_df = df
                            break 
                            
                if target_df is not None:
                    print(f" └─ ⚡ 成功解析表格！(耗時約 {i+1} 秒)")
                    break 
                    
            except Exception:
                pass
                
            time.sleep(1) 
            
        # ==========================================
        # 4. 儲存檔案
        # ==========================================
        if target_df is not None:
            for col in target_df.columns:
                if '代號' in col:
                    target_df = target_df[target_df[col] != col]
                    break
                    
            target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f" └─ ✅ 資料已成功儲存至: {file_path}")
        else:
            current_title = driver.title
            print(f" └─ ❌ 失敗！等了 60 秒還是沒有看到股票資料。")
            print(f" └─ 🔍 盲測診斷：當前網頁標題是【{current_title}】")
            
            screenshot_name = f"error_shot_{index+1}.png"
            driver.save_screenshot(screenshot_name)
            print(f" └─ 📸 已拍下錯誤截圖：'{screenshot_name}'。")
            
    except Exception as e:
        print(f" └─ ⚠️ 發生未知的錯誤: {e}")
    
    if index < len(TARGETS) - 1:
        sleep_time = random.uniform(20, 40)
        print(f" └─ [防封鎖機制] 隨機休息 {sleep_time:.2f} 秒，準備抓下一個...\n")
        time.sleep(sleep_time)

print("-" * 40 + "\n🎉 下載任務已全數執行完畢！所有檔名皆已自動格式化！")
driver.quit()
