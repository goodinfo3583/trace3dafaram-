import time
import random
import pandas as pd
import os
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ==========================================
# 1. 設定區塊
# ==========================================
SAVE_DIR = "Goodinfo_Rankings"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 自動取得今天的日期，格式為 YYYYMMDD
today = datetime.now().strftime("%Y%m%d")

# ⭐ 任務清單：已將 TWSE 移至第 1 順位方便測試 ⭐
TARGETS = {
    "神秘金字塔 - 股權類股排行(5日之400張以上股東排行)": "https://norway.twsthr.info/StockHoldersTopWeek.aspx",
    "大股東1000張數週增加(1-300名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8%40%40%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8",
    "大股東1000張數週增加(301-600名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8%40%40%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8",
    "大股東1000張數週增加(601-900名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8%40%40%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8",
    "大股東1000張數週增加(901-913名(高→低))": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8%40%40%E6%8C%81%E8%82%A1%E8%B6%85%E9%81%8E1%E5%8D%83%E5%BC%B5%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%E9%80%B1%E5%A2%9E%E5%8A%A0%E6%95%B8",
    
    }

# ==========================================
# 2. 啟動瀏覽器 (已升級為 GitHub Actions 雲端無頭模式)
# ==========================================
print("正在啟動 Google Chrome 瀏覽器...")
options = Options()

# 💡 雲端伺服器必備的 3 個參數 (沒有螢幕也能跑)
options.add_argument("--headless=new") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 💡 偽裝成真人瀏覽器，降低被 Goodinfo 阻擋的機率
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.page_load_strategy = 'eager' 

try:
    driver = webdriver.Chrome(options=options)
except Exception as e:
    print(f"啟動 Chrome 失敗！錯誤細節: {e}")
    exit()

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
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
                    
                    # ⭐ 升級：雙模辨識！涵蓋 Goodinfo 股票表 與 TWSE 總表 ⭐
                    has_goodinfo_cols = any('代號' in col or '名稱' in col for col in df.columns)
                    has_twse_cols = any('項目' in col or '今日餘額' in col for col in df.columns)
                    
                    if has_goodinfo_cols or has_twse_cols:
                        # 證交所的總表列數比較少(大約只有3列資料)，所以條件放寬到 > 2
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
            # 清除 Goodinfo 表格中重複的標題列 (安全檢查，不會影響 TWSE)
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
            print(f" └─ 📸 已拍下錯誤截圖：'{screenshot_name}'。")
            
    except Exception as e:
        print(f" └─ ⚠️ 發生未知的錯誤: {e}")
    
    if index < len(TARGETS) - 1:
        sleep_time = random.uniform(20, 40)
        print(f" └─ [防封鎖機制] 隨機休息 {sleep_time:.2f} 秒，準備抓下一個...\n")
        time.sleep(sleep_time)

print("-" * 40 + "\n🎉 下載任務已全數執行完畢！所有檔名皆已自動格式化！")
driver.quit()
