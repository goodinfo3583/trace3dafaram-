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
from selenium.webdriver.support.ui import Select  # 🌟 新增：專門控制下拉選單的神器！

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
        
        # ==============================================================
        # 🌟 無腦萃取起始名次
        # ==============================================================
        target_start = None
        match = re.search(r'(\d+)-\d+名', name_suffix)
        if match and match.group(1) != "1":
            target_start = match.group(1)

        # ==============================================================
        # 🌟 專屬 Goodinfo 的 7 週時光機抓取邏輯
        # ==============================================================
        if "goodinfo" in url:
            
            # 🌟 關鍵防護 1：主動等待時間下拉選單出現 (避免網頁卡住只抓到最新資料)
            for _ in range(15):
                try:
                    sels = driver.find_elements(By.TAG_NAME, "select")
                    if any("W" in s.text for s in sels):
                        break
                except:
                    pass
                time.sleep(1)

            weeks_to_scrape = []
            
            # 1. 掃描下拉選單，動態抓取最近 7 週的選項
            try:
                selects = driver.find_elements(By.TAG_NAME, "select")
                for sel in selects:
                    if "最新資料" in sel.text or "W" in sel.text:
                        options = sel.find_elements(By.TAG_NAME, "option")
                        for opt in options:
                            txt = opt.text.strip()
                            if "最新資料" in txt or txt.startswith("最新"):
                                if "最新資料" not in [w[1] for w in weeks_to_scrape]:
                                    weeks_to_scrape.append((txt, "最新資料"))
                            else:
                                w_match = re.search(r'(202\d{1}W\d{2})', txt)
                                if w_match:
                                    w_str = w_match.group(1)
                                    if w_str not in [w[1] for w in weeks_to_scrape]:
                                        weeks_to_scrape.append((txt, w_str))
                        if weeks_to_scrape:
                            break # 找到對的下拉選單就跳出
            except Exception as e:
                print(f" └─ ⚠️ 無法抓取週別選項: {e}")

            # 限制只抓前 7 週，如果真的都沒抓到，就用最新資料兜底
            weeks_to_scrape = weeks_to_scrape[:7]
            if not weeks_to_scrape:
                weeks_to_scrape = [("最新資料", "最新資料")]

            print(f" └─ 📅 偵測到可抓取的週別: {[w[1] for w in weeks_to_scrape]}")

            # 2. 開始針對這 7 週進行輪迴抓取
            for w_idx, (week_text, week_str) in enumerate(weeks_to_scrape):
                file_name = f"{today}_{week_str}_{name_suffix}.csv"
                file_path = os.path.join(SAVE_DIR, file_name)
                
                print(f"   └─ ⏳ [{w_idx+1}/{len(weeks_to_scrape)}] 正在處理週別: {week_str}")

                # 【步驟 A】: 切換週別 (🌟 導入 Select 並且加入防護重試機制)
                for attempt in range(3):
                    try:
                        changed = False
                        selects = driver.find_elements(By.TAG_NAME, "select")
                        for sel in selects:
                            if week_text in sel.text or "最新資料" in sel.text or "W" in sel.text:
                                s = Select(sel)
                                # 如果當前選的不是我們要的週別，才進行切換
                                if s.first_selected_option.text.strip() != week_text.strip():
                                    s.select_by_visible_text(week_text)
                                    changed = True
                                break
                        if changed:
                            print(f"     └─ 🖱️ 切換週別為 {week_str}，等待網頁重新載入...")
                            time.sleep(8) # 延長等待，確保 DOM 刷新完畢
                        break # 成功切換就跳出重試迴圈
                    except Exception as e:
                        time.sleep(2) # 若報錯 (如 stale element) 則休息2秒重試

                # 【步驟 B】: 切換名次
                if target_start:
                    target_rank_text = f"{target_start}~" # 🌟 神奇小撇步：尋找 "301~" 這種格式
                    for attempt in range(3):
                        try:
                            changed = False
                            # 重新尋找 select，因為切換週別後舊的已經灰飛煙滅了
                            selects = driver.find_elements(By.TAG_NAME, "select")
                            for sel in selects:
                                # 確認這個 select 是負責選名次的
                                if "~300" in sel.text and "~600" in sel.text:
                                    s = Select(sel)
                                    for opt in s.options:
                                        if target_rank_text in opt.text: # 只要選項裡有 "301~" 這種字眼就對了！
                                            if not opt.is_selected():
                                                s.select_by_visible_text(opt.text)
                                                changed = True
                                            break
                                    break
                            if changed:
                                print(f"     └─ 🖱️ 再次切換名次為 {target_start} 起，等待網頁重新載入...")
                                time.sleep(8)
                            break # 成功切換就跳出重試迴圈
                        except Exception as e:
                            time.sleep(2)

                # 【步驟 C】: 解析表格
                print("     └─ 正在等待網頁驗證與表格載入...")
                target_df = None
                for i in range(60):
                    try:
                        html = driver.page_source
                        if i == 30:
                            print("     └─ 🔄 網頁似乎載入卡住，強制重新整理...")
                            driver.refresh()
                            time.sleep(4)
                            continue
                            
                        tables = pd.read_html(StringIO(html))
                        for df in tables:
                            if isinstance(df.columns, pd.MultiIndex):
                                df.columns = df.columns.get_level_values(-1)
                            df.columns = [str(col).strip() for col in df.columns]
                            
                            has_goodinfo_cols = any('代號' in col or '名稱' in col for col in df.columns)
                            if has_goodinfo_cols and len(df) >= 2:
                                target_df = df
                                break
                                
                        if target_df is not None:
                            print(f"     └─ ⚡ 成功解析表格！(耗時約 {i+1} 秒)")
                            break
                    except:
                        pass
                    time.sleep(1)

                # 【步驟 D】: 儲存檔案
                if target_df is not None:
                    for col in target_df.columns:
                        if '代號' in col:
                            target_df = target_df[target_df[col] != col] # 過濾表頭
                            break
                    target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    print(f"     └─ ✅ 歷史資料儲存至: {file_path}")
                else:
                    print(f"     └─ ❌ 失敗！抓不到表格。")
                    driver.save_screenshot(f"error_shot_{index+1}_{week_str}.png")

                # 若不是該名次的最後一週，稍微休息
                if w_idx < len(weeks_to_scrape) - 1:
                    time.sleep(random.uniform(5, 8))

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

print("-" * 40 + "\n🎉 7 週歷史下載任務全數執行完畢！")
driver.quit()
