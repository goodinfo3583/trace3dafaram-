import pandas as pd
import glob
import json
import os

print("============= 🕵️‍♂️ 籌碼雷達運算中心啟動 =============")

# 1. 檢查資料夾檔案
# 💡 請特別注意：請確認你的 CSV 檔名與路徑到底在哪裡！
# 如果是跟著前面 Goodinfo 爬蟲走，路徑應該是 "Goodinfo_Rankings/*"
search_path = "Goodinfo_Rankings/*.csv" 
file_paths = sorted(glob.glob(search_path), reverse=True)
print(f" ├─ 📂 目標路徑: {search_path}")
print(f" ├─ 📊 共搜集到 {len(file_paths)} 個歷史資料檔。")

# 篩選出大戶分點明細的檔案 (這裡可依你實際的檔名關鍵字調整)
broker_files = [f for f in file_paths if "成交價" in f or "持股比例" in f][:10]
print(f" ├─ 🔍 篩選出最近 10 個分點交易檔: {[os.path.basename(f) for f in broker_files]}")

if not broker_files:
    print(" ❌ 🚨 致命錯誤：找不到任何分點交易 CSV 檔案！請確認爬蟲是否有成功存檔。")
    # 就算失敗也生出一個空 json，避免網頁端讀取 404
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/smart_money_targets.json", "w") as f: f.write("[]")
    exit()

df_list = []
for f in broker_files:
    try:
        temp_df = pd.read_csv(f)
        print(f" ├─ 📖 讀取成功: {os.path.basename(f)} | 資料筆數: {len(temp_df)}")
        df_list.append(temp_df)
    except Exception as e:
        print(f" ├─ ⚠️ 讀取失敗: {os.path.basename(f)} | 原因: {e}")

all_trades = pd.concat(df_list, ignore_index=True)
print(f" ├─ 💥 籌碼矩陣合併完成！總列數: {len(all_trades)}")
print(f" ├─ 📋 欄位名稱清單: {list(all_trades.columns)}")

# 💡 這裡加上防呆：防止欄位名稱跟對方的專案不一樣
# 假設你的欄位叫 '代號', '名稱', '買進張數' 等，請在這裡對齊
# 如果發現欄位不對，可以在這裡用 rename 改名

try:
    # 進行群組計算
    # 這裡先用最寬鬆的條件統計
    grouped = all_trades.groupby(by=lambda x: True) # 暫時的語法佔位
    
    # 由於不知道你實際抓進來的 CSV 內部欄位，我們先印出前三行樣品在 GitHub Actions 日誌裡
    print(" ├─ 🧪 CSV 內容樣品預覽:")
    print(all_trades.head(3).to_string())
    
    # 【改為超寬鬆條件】先確保一定有資料輸出
    smart_money = all_trades.head(20) # 先拿前 20 筆試水溫
    
    output_dir = "docs/data"
    os.makedirs(output_dir, exist_ok=True)
    smart_money.to_json(f"{output_dir}/smart_money_targets.json", orient='records', force_ascii=False)
    print(f" ✅ 順利導出 JSON！共計 {len(smart_money)} 筆資料。")

except Exception as e:
    print(f" ❌ 🚨 計算過程中崩潰: {e}")
    with open("docs/data/smart_money_targets.json", "w") as f: f.write("[]")
