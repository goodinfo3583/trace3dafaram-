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
from selenium.webdriver.support.ui import Select

# ==========================================
# 1. 設定區塊
# ==========================================
SAVE_DIR = "data"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

today = datetime.now().strftime("%Y%m%d")

TARGETS = {
    "神秘金字塔 - 股權類股排行(5日之400張以上股東排行)": "https://norway.twsthr.info/StockHoldersTopWeek.aspx",
    "大股東1000張數週增減(1-300名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(301-600名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(601-900名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(901-1200名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(1201-1500名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(1501-1800名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(1801-2100名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
    "大股東1000張數週增減(2101-2368名)": "https://goodinfo.tw/tw/StockList.asp?RPT_TIME=&MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29%40%40%E6%8C%81%E8%82%A11%E5%8D%83%E5%BC%B5%E4%BB%A5%E4%B8%8B%40%40%E6%8C%81%E6%9C%89%E6%AF%94%E4%BE%8B%28%25%29",
}

# ==========================================
# 2. 啟動瀏覽器 (undetected_chromedriver 破甲版)
# ==========================================
print("正在啟動 Google Chrome 瀏覽器...")
options = uc.ChromeOptions()

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
    print(f"\n[{index+1}/{len(TARGETS)}] 正在處理總目標: {name_suffix}")
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # 萃取目標名次 (例如 "301")
        target_start = None
        match = re.search(r'(\d+)-\d+名', name_suffix)
        if match and match.group(1) != "1":
            target_start = match.group(1)

        # 預期的排名 (用來驗證資料)
        expected_rank = target_start if target_start else "1"

        if "goodinfo" in url:
            
            # 主動等待時間下拉選單出現
            for _ in range(15):
                try:
                    sels = driver.find_elements(By.TAG_NAME, "select")
                    if any("W" in s.text for s in sels):
                        break
                except: pass
                time.sleep(1)

            weeks_to_scrape = []
            
            # 1. 動態抓取週別選項 (剔除最新資料，只保留 2026WXX 格式)
            try:
                selects = driver.find_elements(By.TAG_NAME, "select")
                for sel in selects:
                    if "W" in sel.text:
                        options = sel.find_elements(By.TAG_NAME, "option")
                        for opt in options:
                            w_match = re.search(r'(202\d{1}W\d{2})', opt.text)
                            if w_match:
                                w_str = w_match.group(1)
                                if w_str not in [w[1] for w in weeks_to_scrape]:
                                    weeks_to_scrape.append((opt.text.strip(), w_str))
                        if weeks_to_scrape:
                            break
            except Exception as e:
                print(f" └─ ⚠️ 無法抓取週別選項: {e}")

            # 🌟 未來修改點：如果之後每個禮拜六只抓最新一週，就把下面的 [:7] 改成 [:1]
            weeks_to_scrape = weeks_to_scrape[:7]
            
            if not weeks_to_scrape:
                print(" └─ ⚠️ 嚴重警告：抓不到週別資料，跳過。")
                continue

            print(f" └─ 📅 準備抓取的週別清單: {[w[1] for w in weeks_to_scrape]}")

            # 2. 開始針對這 7 週進行輪迴抓取
            for w_idx, (week_text, week_str) in enumerate(weeks_to_scrape):
                file_name = f"{today}_{week_str}_{name_suffix}.csv"
                file_path = os.path.join(SAVE_DIR, file_name)
                
                # Goodinfo 表格內的週別格式沒有前兩碼 (例如 2026W32 在表格裡是 26W32)
                table_week_str = week_str[2:]
                
                print(f"   └─ ⏳ [{w_idx+1}/{len(weeks_to_scrape)}] 正在處理週別: {week_str}")

                target_df = None
                
                # 🌟 加入重試迴圈：如果驗證發現抓到舊資料，會重新點擊選單
                for attempt in range(3):
                    # 【步驟 A】: 切換週別
                    try:
                        changed = False
                        selects = driver.find_elements(By.TAG_NAME, "select")
                        for sel in selects:
                            if "W" in sel.text:
                                s = Select(sel)
                                if s.first_selected_option.text.strip() != week_text:
                                    s.select_by_visible_text(week_text)
                                    changed = True
                                break
                        if changed:
                            time.sleep(3) # 切換後給予緩衝
                    except: pass

                    # 【步驟 B】: 切換名次
                    if target_start:
                        target_rank_text = f"{target_start}~"
                        try:
                            changed = False
                            selects = driver.find_elements(By.TAG_NAME, "select")
                            for sel in selects:
                                if "~300" in sel.text and "~600" in sel.text:
                                    s = Select(sel)
                                    if target_rank_text not in s.first_selected_option.text:
                                        for opt in s.options:
                                            if target_rank_text in opt.text:
                                                s.select_by_visible_text(opt.text)
                                                changed = True
                                                break
                                    break
                            if changed:
                                time.sleep(3)
                        except: pass

                    # 【步驟 C】: 提取表格與『雙重驗證』
                    print("     └─ 正在等待網頁重載並進行資料驗證...")
                    is_verified = False
                    
                    for i in range(15): # 最多等15秒讓網頁刷新
                        try:
                            html = driver.page_source
                            tables = pd.read_html(StringIO(html))
                            for df in tables:
                                if isinstance(df.columns, pd.MultiIndex):
                                    df.columns = df.columns.get_level_values(-1)
                                df.columns = [str(col).strip() for col in df.columns]
                                
                                has_goodinfo_cols = any('代號' in col or '名稱' in col for col in df.columns)
                                if has_goodinfo_cols and len(df) >= 2:
                                    
                                    # 🌟 驗證 1：檢查表格內的週別是否正確
                                    week_match = True
                                    week_col = next((c for c in df.columns if '週別' in c), None)
                                    if week_col:
                                        first_week_val = str(df[week_col].dropna().iloc[0])
                                        if table_week_str not in first_week_val:
                                            week_match = False
                                            
                                    # 🌟 驗證 2：檢查表格內的第一筆排名是否正確
                                    rank_match = True
                                    rank_col = next((c for c in df.columns if '排名' in c), None)
                                    if rank_col:
                                        # 將排名轉為字串並去除浮點數(如 301.0 -> 301)
                                        first_rank_val = str(df[rank_col].dropna().iloc[0]).replace(".0", "")
                                        if first_rank_val != expected_rank:
                                            rank_match = False
                                            
                                    # 如果週別跟名次都對上了，代表網頁確定更新完畢！
                                    if week_match and rank_match:
                                        target_df = df
                                        is_verified = True
                                        break
                                        
                            if is_verified:
                                break # 驗證成功，跳出等待迴圈
                        except: pass
                        time.sleep(1) # 如果驗證失敗，等1秒再抓一次HTML檢查

                    if is_verified:
                        print(f"     └─ ⚡ 雙重驗證通過！成功鎖定正確表格。")
                        break # 資料正確，跳出重試迴圈，準備存檔
                    else:
                        print(f"     └─ ⚠️ 資料尚未更新 (Attempt {attempt+1}/3)，強制重整頁面重試...")
                        driver.refresh()
                        time.sleep(5)

                # 【步驟 D】: 儲存檔案
                if target_df is not None:
                    for col in target_df.columns:
                        if '代號' in col:
                            target_df = target_df[target_df[col] != col] # 過濾標題列
                            break
                    target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    print(f"     └─ ✅ 正確資料已儲存至: {file_path}")
                else:
                    print(f"     └─ ❌ 嚴重失敗！驗證 3 次均抓不到正確表格。")
                    driver.save_screenshot(f"error_shot_{index+1}_{week_str}.png")

                # 若不是該名次的最後一週，稍微休息
                if w_idx < len(weeks_to_scrape) - 1:
                    time.sleep(random.uniform(3, 6))

        else:
            # ==============================================================
            # 🌟 非 Goodinfo (如 神秘金字塔) 單次抓取邏輯
            # ==============================================================
            file_name = f"{today}_{name_suffix}.csv"
            file_path = os.path.join(SAVE_DIR, file_name)
            
            print(" └─ 正在等待網頁驗證與表格載入 (非 Goodinfo 網站)...")
            target_df = None
            for i in range(60):
                try:
                    html = driver.page_source
                    if i == 30:
                        driver.refresh()
                        time.sleep(4)
                        continue
                    tables = pd.read_html(StringIO(html))
                    for df in tables:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.get_level_values(-1)
                        df.columns = [str(col).strip() for col in df.columns]
                        
                        if len(df) >= 2:
                            target_df = df
                            break
                    if target_df is not None:
                        print(f" └─ ⚡ 成功解析表格！(耗時約 {i+1} 秒)")
                        break
                except:
                    pass
                time.sleep(1)

            if target_df is not None:
                for col in target_df.columns:
                    if '代號' in col or '股號' in col:
                        target_df = target_df[target_df[col] != col]
                        break
                target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                print(f" └─ ✅ 資料已儲存至: {file_path}")
            else:
                print(f" └─ ❌ 失敗！抓不到表格。")

        # 每個大項目換網址前的大休息
        if index < len(TARGETS) - 1:
            sleep_time = random.uniform(20, 35)
            print(f"\n └─ [防封鎖機制] 隨機大休息 {sleep_time:.2f} 秒，準備切換下一個目標...")
            time.sleep(sleep_time)

    except Exception as e:
        print(f" └─ ⚠️ 發生未知的錯誤: {e}")

print("-" * 40 + "\n🎉 歷史下載與驗證任務全數執行完畢！")
driver.quit()
