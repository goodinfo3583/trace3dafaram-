import time
import random
import pandas as pd
import os
from io import StringIO
from datetime import datetime
import subprocess
import re

# 🌟 匯入終極突破武器 🌟
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By

# ==========================================
# 1. 設定區塊
# ==========================================
SAVE_DIR = "data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

today = datetime.now().strftime("%Y%m")

TARGETS = {
    "董監質押比(1-300名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29",
    "董監質押比(301-600名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29", 
    "董監質押比(601-900名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29",
    "董監質押比(901-1200名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29",
    "董監質押比(1201-1500名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29",
    "董監質押比(1501-1800名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29",
    "董監質押比(1801-1969名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29%40%40%E5%85%A8%E9%AB%94%E8%91%A3%E7%9B%A3%40%40%E8%B3%AA%E6%8A%BC%E6%AF%94%E4%BE%8B%28%25%29",
}

# ==========================================
# 2. 啟動瀏覽器 (undetected_chromedriver 破甲版)
# ==========================================
print("正在啟動 Google Chrome 瀏覽器...")
options = uc.ChromeOptions()

# 我們現在有 Xvfb 虛擬螢幕，所以不需要 --headless，這能讓 Goodinfo 以為我們是真人
options.add_argument('--no-sandbox')               
options.add_argument('--disable-dev-shm-usage')    
options.add_argument('--disable-gpu')              
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
options.add_argument('--window-size=1920,1080')

version_main = None
try:
    out = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
    match = re.search(r'(\d+)\.', out)
    if match:
        version_main = int(match.group(1))
        print(f" └─ 🔍 自動偵測到伺服器 Chrome 主版本為: {version_main}")
except Exception as e:
    pass

try:
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
        
        # 🌟 修改這裡：使用正則表達式自動抓取名次區間
        target_rank = None
        match = re.search(r'\((\d+)-(\d+)名', name_suffix)
        if match:
            target_rank = (match.group(1), match.group(2))
        else:
            match_last = re.search(r'\((\d+)-.*?名', name_suffix)
            if match_last and int(match_last.group(1)) > 300:
                target_rank = (match_last.group(1), "")
                
        # 如果是 1-300 名 (第一頁)，不需要切換，直接設為 None 略過點擊
        if target_rank and target_rank[0] == "1":
            target_rank = None
            
        if target_rank and "goodinfo" in url:
            print(f" └─ 🔍 偵測到需要切換名次，自動點擊選單 (包含 '{target_rank[0]}' 名)...")
            time.sleep(5)
            try:
                options_elements = driver.find_elements(By.TAG_NAME, "option")
                for opt in options_elements:
                    # 只要選項文字包含我們要的起始名次 (例如 901) 就點擊
                    if target_rank[0] in opt.text: 
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
                
                # 💡 救援機制：等了 30 秒如果還沒出來，按一次 F5 重新整理
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
            
        if target_df is not None:
            for col in target_df.columns:
                if '代號' in col:
                    target_df = target_df[target_df[col] != col]
                    break
                    
            target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f" └─ ✅ 資料已成功儲存至: {file_path}")
        else:
            print(f" └─ ❌ 失敗！等了 60 秒還是沒有看到股票資料。")
            screenshot_name = f"error_shot_{index+1}.png"
            driver.save_screenshot(screenshot_name)
            
    except Exception as e:
        print(f" └─ ⚠️ 發生未知的錯誤: {e}")
    
    if index < len(TARGETS) - 1:
        sleep_time = random.uniform(20, 40)
        print(f" └─ [防封鎖機制] 隨機休息 {sleep_time:.2f} 秒，準備抓下一個...\n")
        time.sleep(sleep_time)

print("-" * 40 + "\n🎉 下載任務已全數執行完畢！所有檔名皆已自動格式化！")
driver.quit()
