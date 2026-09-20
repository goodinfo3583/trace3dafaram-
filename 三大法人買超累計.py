# institutional_buy_scraper.py
import time
import random
import pandas as pd
import os
import glob
from io import StringIO
from datetime import datetime, timedelta
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select # 🌟 新增：專門處理下拉選單的官方模組
# 🌟 匯入終極突破武器 (SeleniumBase) 🌟
from seleniumbase import Driver

# ==========================================
# 1. 設定區塊 (絕對路徑定位與跨夜邏輯)
# ==========================================
# 🌟 指定儲存路徑 (依照你的需求)
SAVE_DIR = r"C:\Users\User\Desktop\爬蟲\data"
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

# 目標基礎網址 (三大法人累計買超)
BASE_URL = "https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=%E7%86%B1%E9%96%80%E6%8E%92%E8%A1%8C&INDUSTRY_CAT=%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E7%B4%AF%E8%A8%88%E8%B2%B7%E8%B6%85%E5%BC%B5%E6%95%B8+%E2%80%93+%E7%95%B6%E6%97%A5%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E7%B4%AF%E8%A8%88%E8%B2%B7%E8%B6%85%40%40%E4%B8%89%E5%A4%A7%E6%B3%95%E4%BA%BA%E8%B2%B7%E8%B6%85%E5%BC%B5%E6%95%B8+%E2%80%93+%E7%95%B6%E6%97%A5"
CF_KEYWORDS = ["Just a moment", "Cloudflare", "請稍候", "Attention", "驗證"]

# ==========================================
# 2. 啟動瀏覽器 (SeleniumBase 真人記憶版)
# ==========================================
print("\n>> 正在啟動 Google Chrome 瀏覽器 (使用 SeleniumBase UC 模式)...")

# 在設定的資料夾旁邊建立 cookie 設定檔
profile_path = os.path.join(os.path.dirname(SAVE_DIR), "chrome_profile")
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
    
    print(" └─ 🎭 真人環境部署完成：已啟用 Cookie 記憶體！")
except Exception as e:
    print(f"啟動 Chrome 失敗！錯誤細節: {e}")
    exit()

# ==========================================
# 3. 核心抓取模組 (全新穩定版選單偵測)
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

def get_date_options():
    """尋找日期的下拉選單"""
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        texts = [opt.text.strip() for opt in s.find_elements(By.TAG_NAME, "option")]
        if any("最新資料" in t or "202" in t for t in texts):
            return texts
    return []

def get_rank_options():
    """尋找名次的下拉選單"""
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        texts = [opt.text.strip() for opt in s.find_elements(By.TAG_NAME, "option")]
        # 改用 300 或 高→低 來當作偵測名次選單的特徵，避免被空白干擾
        if any("300" in t or "高→低" in t for t in texts):
            return texts
    return []

def select_option(target_text):
    """安全地點擊特定的下拉選單選項並觸發網頁更新"""
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        options = s.find_elements(By.TAG_NAME, "option")
        texts = [opt.text.strip() for opt in options]
        if target_text in texts:
            try:
                # 使用官方 Select 物件進行切換
                sel = Select(s)
                sel.select_by_visible_text(target_text)
                # 雙重保險：強迫觸發 onChange 事件
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", s)
                return True
            except Exception as e:
                print(f"選單點擊發生錯誤: {e}")
    return False

# ==========================================
# 4. 主執行流程：雙層迴圈 (日期 -> 名次)
# ==========================================
print("\n>> 正在載入基礎網頁...")
driver.uc_open_with_reconnect(BASE_URL, reconnect_time=4)
check_and_solve_cf()

target_dates = get_date_options()[:3] # 我們只要抓前 3 天
print(f"\n>> 📅 成功抓取目標日期，準備執行: {target_dates}")

success_count = 0
total_tasks = 0

for date_idx, date_text in enumerate(target_dates):
    print(f"\n{'='*50}")
    print(f"🗓️ 開始處理日期: {date_text} ({date_idx+1}/{len(target_dates)})")
    
    # 切換日期
    if select_option(date_text):
        print(f" └─ 🔄 已切換至日期 {date_text}，等待載入...")
        time.sleep(6)
        check_and_solve_cf()
    
    # 處理檔名的日期前綴
    if "最新" in date_text:
        file_date_str = today
    else:
        # 把 "2026/09/18(五)" 變成 "20260918"
        file_date_str = re.sub(r'[^\d]', '', date_text.split('(')[0])
        if not file_date_str: file_date_str = today

    # 動態取得當前日期的名次區間
    rank_options_texts = get_rank_options()
    
    if not rank_options_texts:
        print(" └─ ⚠️ 找不到名次下拉選單，可能今天只有一頁資料！將直接抓取當前頁面...")
        rank_options_texts = ["全覽"] # 給予一個虛擬名稱讓迴圈可以跑一次
    else:
        print(f" └─ 📊 偵測到 {len(rank_options_texts)} 個名次區間: {rank_options_texts}")
    
    for rank_idx, rank_text in enumerate(rank_options_texts):
        total_tasks += 1
        clean_rank = rank_text.replace(' ', '').replace('/', '_')
        name_suffix = f"三大法人累計買超({clean_rank})"
        file_name = f"{file_date_str}_{name_suffix}.csv"
        file_path = os.path.join(SAVE_DIR, file_name)
        
        print(f"\n   [{rank_idx+1}/{len(rank_options_texts)}] 正在擷取: {date_text} -> {rank_text}")
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
            print(f"   └─ ⏩ 檔案已存在且完整，自動跳過！")
            success_count += 1
            continue

        # 如果不是虛擬名稱，就進行切換
        if rank_text != "全覽":
            if select_option(rank_text):
                print(f"   └─ 🖱️ 已切換至 {rank_text}，等待網頁重新載入...")
                time.sleep(6)
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
            
        # 防封鎖隨機休息 (不同名次之間)
        if rank_idx < len(rank_options_texts) - 1:
            sleep_time = random.uniform(8, 15)
            time.sleep(sleep_time)
            
    # 不同日期之間休息久一點
    if date_idx < len(target_dates) - 1:
        sleep_time = random.uniform(15, 30)
        print(f"\n 💤 [防封鎖] 跨日期休息 {sleep_time:.2f} 秒...\n")
        time.sleep(sleep_time)

print("-" * 40 + f"\n🎉 下載任務已全數執行完畢！最終成功率：{success_count}/{total_tasks}")
driver.quit()

# ==========================================
# 5. 智慧動態分類與 Parquet 轉換引擎
# ==========================================
print("\n>> [階段 3.5] 啟動資料自動整併引擎 (轉換 Parquet 並保留原始 CSV 檔案)...")

def convert_monthly_to_parquet(save_dir):
    # 🌟 修改點：強制只抓包含「三大法人累計買超」的 CSV 檔案，不要碰其他的！
    all_csvs = glob.glob(os.path.join(save_dir, "*三大法人累計買超*.csv"))
    
    if not all_csvs:
        print(" └─ ⚠️ 找不到任何『三大法人累計買超』的 CSV 檔案，請確認爬蟲是否成功。")
        return

    # 建立分類字典，將屬於同日期、同類別的檔案分組
    category_groups = {}
    for file_path in all_csvs:
        filename = os.path.basename(file_path)
        # 萃取日期 例如: 20260918_三大法人累計買超(1-300名).csv
        match = re.match(r'^(\d{4,8})[-_]?(.*)\.csv$', filename)
        if match:
            file_date = match.group(1)
            # 強制將類別定名，不再看括號裡面的名次
            clean_category = "三大法人累計買超" 
            
            group_key = f"{file_date}_{clean_category}"
            
            if group_key not in category_groups:
                category_groups[group_key] = []
            category_groups[group_key].append(file_path)

    # 逐一將各分類的 CSV 垂直合併並轉存為 Parquet
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
            
    print(" └─ 📁 只有『三大法人累計買超』被處理，不會干擾你其他資料夾的檔案。")

# 執行轉換
convert_monthly_to_parquet(SAVE_DIR)
print("\n>> 程式全數執行完畢！(已依照要求取消自動上傳 GitHub，請手動確認資料) 🎉")
