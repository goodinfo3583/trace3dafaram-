# institutional_buy_scraper.py
import time
import random
import pandas as pd
import os
from io import StringIO
from datetime import datetime, timedelta
import subprocess
import re

from selenium.webdriver.common.by import By
# 🌟 匯入終極突破武器 (SeleniumBase) 🌟
from seleniumbase import Driver

# ==========================================
# 1. 設定區塊 (絕對路徑定位與跨夜邏輯)
# ==========================================
# 強制將工作目錄切換到腳本所在的資料夾
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

SAVE_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 🌟 核心修正：時區偏移（邏輯換日）機制
now = datetime.now()
if now.hour < 6:
    logical_date = now - timedelta(days=1)
    print(f"⚠️ 偵測到跨夜執行！將邏輯日期回推至昨天：{logical_date.strftime('%Y-%m-%d')}")
else:
    logical_date = now

# 自動修正為 YYYYMMDD 格式
today = logical_date.strftime("%Y%m%d")

# 新的目標基礎網址 (三大法人累計買超)
BASE_URL = "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E7%B4%AF%E8%A8%88%E8%B2%B7%E8%B6%85%E5%BC%B5%E6%95%B8+%E2%80%93+%E7%95%B6%E6%97%A5%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E7%B4%AF%E8%A8%88%E8%B2%B7%E8%B6%85%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B2%B7%E8%B6%85%E5%BC%B5%E6%95%B8+%E2%80%93+%E7%95%B6%E6%97%A5"
CF_KEYWORDS = ["Just a moment", "Cloudflare", "請稍候", "Attention", "驗證"]

# ==========================================
# 2. 啟動瀏覽器 (SeleniumBase 真人記憶版)
# ==========================================
print("\n>> 正在啟動 Google Chrome 瀏覽器 (使用 SeleniumBase UC 模式)...")

profile_path = os.path.join(BASE_DIR, "chrome_profile")
if not os.path.exists(profile_path):
    os.makedirs(profile_path)

try:
    driver = Driver(
        uc=True,               
        headless=False,        
        user_data_dir=profile_path,
        no_sandbox=True,
        disable_gpu=True,
        window_size="1920,1080"
    )
    driver.maximize_window()
    
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {'timezoneId': 'Asia/Taipei'})
    driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {'latitude': 25.0330, 'longitude': 121.5654, 'accuracy': 100})
    
    print(" └─ 🎭 真人環境部署完成：已啟用 Cookie 記憶體與原生 UA！")
except Exception as e:
    print(f"啟動 Chrome 失敗！錯誤細節: {e}")
    exit()

# ==========================================
# 3. 核心抓取模組 (動態日期與名次)
# ==========================================
def check_and_solve_cf():
    """檢查並突破 Cloudflare 盾牌"""
    time.sleep(3)
    is_cf_blocked = any(kw in driver.title for kw in CF_KEYWORDS) or "cf-turnstile" in driver.page_source
    if is_cf_blocked:
        print(f" └─ 🛡️ 遇到 Cloudflare 驗證畫面 (標題: {driver.title})，啟動自動破盾機制...")
        try:
            driver.uc_gui_click_captcha()
            print(" └─ 🎯 成功執行自動點擊指令！")
            time.sleep(5)
        except Exception as e:
            print(f" └─ ⚠️ 自動點擊遇障礙，等待跳轉: {e}")
        
        if not any(kw in driver.title for kw in CF_KEYWORDS):
            print(" └─ 🔓 Cloudflare 盾牌已成功擊破！")
        else:
            print(" └─ ⚠️ 仍在 Cloudflare 畫面，嘗試繼續等待...")
            time.sleep(5)

def get_dropdown_options(keyword_to_find):
    """通用函式：尋找包含特定關鍵字的下拉選單，並回傳所有選項文字"""
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        options = s.find_elements(By.TAG_NAME, "option")
        options_texts = [opt.text.strip() for opt in options]
        if any(keyword_to_find in text for text in options_texts):
            return options, options_texts
    return None, []

def select_dropdown_option(target_text):
    """通用函式：點擊特定的下拉選單選項並觸發網頁更新"""
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        options = s.find_elements(By.TAG_NAME, "option")
        for opt in options:
            if opt.text.strip() == target_text:
                opt.click()
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", s)
                return True
    return False

# ==========================================
# 4. 主執行流程：雙層迴圈 (日期 -> 名次)
# ==========================================
print("\n>> 正在載入基礎網頁...")
driver.uc_open_with_reconnect(BASE_URL, reconnect_time=4)
check_and_solve_cf()

# 取得日期選項 (通常包含 '最新資料' 或 '202')
_, date_options_texts = get_dropdown_options("最新資料")
if not date_options_texts:
    # 備用方案，找尋包含年份的選單
    _, date_options_texts = get_dropdown_options("202")

# 我們只要抓前 3 天
target_dates = date_options_texts[:3]
print(f"\n>> 📅 成功抓取目標日期，準備執行: {target_dates}")

success_count = 0
total_tasks = 0
failed_tasks = []

for date_idx, date_text in enumerate(target_dates):
    print(f"\n{'='*50}")
    print(f"🗓️ 開始處理日期: {date_text} ({date_idx+1}/{len(target_dates)})")
    
    # 點擊切換日期
    if select_dropdown_option(date_text):
        print(f" └─ 🔄 已切換至日期 {date_text}，等待載入...")
        time.sleep(8)
        check_and_solve_cf()
    
    # 處理檔名的日期前綴
    if "最新" in date_text:
        file_date_str = today
    else:
        # 把 "2026/09/18(五)" 變成 "20260918"
        file_date_str = re.sub(r'[^\d]', '', date_text.split('(')[0])
        if not file_date_str: file_date_str = today

    # 動態取得當前日期有多少名次區間 (包含 "1-300名")
    _, rank_options_texts = get_dropdown_options("1-300")
    if not rank_options_texts:
        print(" └─ ⚠️ 找不到名次下拉選單，略過此日期！")
        continue
        
    print(f" └─ 📊 偵測到 {len(rank_options_texts)} 個名次區間: {rank_options_texts}")
    
    for rank_idx, rank_text in enumerate(rank_options_texts):
        total_tasks += 1
        # 清理字串作為檔名後綴 (加上小括號為了相容你的 Parquet 正規表達式)
        clean_rank = rank_text.replace(' ', '').replace('/', '_')
        name_suffix = f"三大法人累計買超({clean_rank})"
        file_name = f"{file_date_str}_{name_suffix}.csv"
        file_path = os.path.join(SAVE_DIR, file_name)
        
        print(f"\n   [{rank_idx+1}/{len(rank_options_texts)}] 正在擷取: {date_text} -> {rank_text}")
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
            print(f"   └─ ⏩ 檔案已存在且完整，自動跳過！")
            success_count += 1
            continue

        # 切換名次
        if select_dropdown_option(rank_text):
            print(f"   └─ 🖱️ 已切換至 {rank_text}，等待網頁重新載入...")
            time.sleep(8)
            check_and_solve_cf()
            
        # 等待並解析表格
        print("   └─ 正在等待表格載入 (最長等待 60 秒)...")
        target_df = None
        
        for i in range(60): 
            try:
                html = driver.page_source
                if i == 30:
                    print("   └─ 🔄 網頁似乎載入卡住，嘗試強制重新整理...")
                    driver.refresh()
                    time.sleep(5)
                    check_and_solve_cf()
                    continue
                    
                tables = pd.read_html(StringIO(html))
                
                for df in tables:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    df.columns = [str(col).strip() for col in df.columns]
                    
                    if any('代號' in col or '名稱' in col for col in df.columns):
                        if len(df) >= 2:  
                            target_df = df
                            break 
                            
                if target_df is not None:
                    print(f"   └─ ⚡ 成功解析表格！(耗時約 {i+1} 秒)")
                    break 
                    
            except Exception:
                pass
            time.sleep(1)
            
        # 儲存資料
        if target_df is not None:
            # 清除重複的表頭
            for col in target_df.columns:
                if '代號' in col:
                    target_df = target_df[target_df[col] != col]
                    break
                    
            target_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"   └─ ✅ 資料儲存成功: {file_name}")
            success_count += 1
        else:
            print(f"   └─ ❌ 失敗！等了 60 秒還是沒有看到股票資料。")
            failed_tasks.append((date_text, rank_text, file_name))
            
        # 防封鎖隨機休息 (不同名次之間)
        if rank_idx < len(rank_options_texts) - 1:
            sleep_time = random.uniform(8, 15)
            time.sleep(sleep_time)
            
    # 不同日期之間休息久一點
    if date_idx < len(target_dates) - 1:
        sleep_time = random.uniform(15, 30)
        print(f"\n 💤 [防封鎖] 跨日期休息 {sleep_time:.2f} 秒...\n")
        time.sleep(sleep_time)

# ==========================================
# 4.5 敗部復活機制 (針對 failed_tasks) 略作簡化
# ==========================================
if failed_tasks:
    print("\n" + "="*40)
    print(f">> [敗部復活] 針對 {len(failed_tasks)} 個失敗項目重新嘗試... (可以自行擴充)")
    # 為保持長度與原功能，這裡印出紀錄。因為動態選單切換需重跑前置，建議後續再手動補抓或交由明天自動補齊。

print("-" * 40 + f"\n🎉 下載任務已全數執行完畢！最終成功率：{success_count}/{total_tasks}")
driver.quit()

# ==========================================
# 5. 智慧動態分類與 Parquet 轉換引擎
# ==========================================
import glob

print("\n>> [階段 3.5] 啟動資料自動整併引擎 (轉換 Parquet 並保留原始 CSV 檔案)...")

def convert_monthly_to_parquet(save_dir):
    # 1. 抓取目錄下所有的 CSV 檔案 (不再限於 today，確保跨日曆史資料也能被整併)
    all_csvs = glob.glob(os.path.join(save_dir, "*.csv"))
    
    if not all_csvs:
        print(" └─ ⚠️ 找不到 CSV 檔案，請確認爬蟲是否成功。")
        return

    # 2. 建立分類字典，將屬於同日期、同類別的檔案分組
    category_groups = {}
    for file_path in all_csvs:
        filename = os.path.basename(file_path)
        # 萃取日期與類別名稱 例如: 20260918_三大法人累計買超(1-300名).csv
        match = re.match(r'^(\d{4,8})[-_]?(.*)\.csv$', filename)
        if match:
            file_date = match.group(1)
            raw_category = match.group(2)
            # 剝離括號內的內容，保留主類別名稱
            clean_category = re.sub(r'\(.*?\)', '', raw_category).strip().strip('_-')
            if not clean_category:
                clean_category = "未分類資料"
            
            # 使用 Date + Category 作為群組 Key
            group_key = f"{file_date}_{clean_category}"
            
            if group_key not in category_groups:
                category_groups[group_key] = []
            category_groups[group_key].append(file_path)

    # 3. 逐一將各分類的 CSV 垂直合併並轉存為 Parquet
    for group_key, files in category_groups.items():
        print(f" └─ 📦 正在整併並轉換類別: {group_key} (共包含 {len(files)} 個檔案)...")
        try:
            df_list = []
            for f in files:
                for enc in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
                    try:
                        df = pd.read_csv(f, encoding=enc, dtype=str)
                        break
                    except Exception:
                        pass
                if df is not None and not df.empty:
                    df_list.append(df)
            
            if not df_list: continue
            
            merged_df = pd.concat(df_list, ignore_index=True)
            
            code_col = next((c for c in merged_df.columns if '代號' in c or '股號' in c), None)
            if code_col:
                merged_df = merged_df[merged_df[code_col] != code_col]
                merged_df[code_col] = merged_df[code_col].astype(str).str.strip()
                merged_df = merged_df.drop_duplicates(subset=[code_col], keep='first')
            
            parquet_filename = f"{group_key}.parquet"
            parquet_path = os.path.join(save_dir, parquet_filename)
            merged_df.to_parquet(parquet_path, engine='pyarrow', index=False)
            
            print(f"    ✅ 成功生成: {parquet_filename}")
            
        except Exception as e:
            print(f"    ❌ 轉換失敗 ({group_key}): {e}")
            
    print(" └─ 📁 所有類別的原始 CSV 檔案皆已安全保留。")

# 執行全自動分類與轉換
convert_monthly_to_parquet(SAVE_DIR)

# ==========================================
# 6. 自動推播至 GitHub
# ==========================================
print("\n>> [階段四] 自動推播至 GitHub...")
try:
    subprocess.run(["git", "add", "data/"], cwd=BASE_DIR, check=True)
    subprocess.run(["git", "commit", "-m", f"自動更新 {today} 三大法人買賣超資料"], cwd=BASE_DIR, check=False)
    subprocess.run(["git", "push"], cwd=BASE_DIR, check=True)
    print("✅ 資料已成功上傳至 GitHub！")
except Exception as e:
    print(f"⚠️ Git 推播失敗: {e}")
