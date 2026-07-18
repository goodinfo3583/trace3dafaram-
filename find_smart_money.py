import pandas as pd
import requests
import io
from datetime import datetime, timedelta
import os

print("============= 🕵️‍♂️ 主力籌碼雷達運算中心啟動 (遠端直連版) =============")

# 1. 自動往前推算日期，去對方 GitHub 抓取最近 10 個交易日的 CSV
df_list = []
days_collected = 0
current_date = datetime.now()

# 嘗試往前找 20 天，湊滿 10 個有交易的日子
for i in range(20):
    if days_collected >= 10:
        break
        
    date_str = (current_date - timedelta(days=i)).strftime("%Y-%m-%d")
    url = f"https://raw.githubusercontent.com/voidful/tw-institutional-stocker/main/data/broker/broker_trades_{date_str}.csv"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            print(f" ├─ 📥 成功下載遠端資料: broker_trades_{date_str}.csv")
            # 讀取 CSV 並加上日期標籤
            df = pd.read_csv(io.StringIO(res.text))
            df['交易日期'] = date_str
            df_list.append(df)
            days_collected += 1
        elif res.status_code == 404:
            # 假日沒有開盤，或是對方還沒上傳
            pass
    except Exception as e:
        print(f" ├─ ⚠️ 網路錯誤 {date_str}: {e}")

# =====================================================================
# 確保 JSON 檔案一定會被建立 (防止 GitHub Actions 當機)
output_dir = "docs/data"
os.makedirs(output_dir, exist_ok=True)
json_path = f"{output_dir}/smart_money_targets.json"

if not df_list:
    print(" ❌ 🚨 致命錯誤：無法從遠端取得任何券商交易 CSV。")
    with open(json_path, "w") as f: f.write("[]")
    exit()

# 2. 合併所有資料
all_trades = pd.concat(df_list, ignore_index=True)
print(f" ├─ 💥 籌碼矩陣合併完成！總計分析了 {len(all_trades)} 筆交易紀錄。")
print(f" ├─ 📋 遠端 CSV 欄位名稱為: {list(all_trades.columns)}")

try:
    # 3. 欄位容錯對位 (因為我們不知道對方的欄位確切叫什麼)
    col_stock = next((c for c in all_trades.columns if '股票' in c or 'stock' in c.lower() or c == '代號'), None)
    col_broker = next((c for c in all_trades.columns if '券商' in c or 'broker' in c.lower()), None)
    col_buy = next((c for c in all_trades.columns if '買進' in c or 'buy' in c.lower()), None)
    col_sell = next((c for c in all_trades.columns if '賣出' in c or 'sell' in c.lower()), None)
    col_net = next((c for c in all_trades.columns if '買賣超' in c or 'net' in c.lower()), None)

    if not all([col_stock, col_broker, col_buy, col_sell, col_net]):
        print(" ❌ 找不到關鍵對應欄位，請檢查日誌印出的欄位名稱。")
        with open(json_path, "w") as f: f.write("[]")
        exit()

    # 4. 核心魔法：將「股票」與「券商」群組，計算這幾天的總買賣超
    grouped = all_trades.groupby([col_stock, col_broker]).agg(
        十日總買進=(col_buy, 'sum'),
        十日總賣出=(col_sell, 'sum'),
        十日買賣超=(col_net, 'sum'),
        交易天數=('交易日期', 'nunique')
    ).reset_index()

    # 5. 主力篩選條件 (這裡我設定為：總買進>500張 且 買進是賣出的 3 倍以上)
    smart_money = grouped[
        (grouped['十日總買進'] > 500) & 
        (grouped['十日總買進'] > grouped['十日總賣出'] * 3) & 
        (grouped['交易天數'] >= 3)
    ]

    # 6. 排序並輸出最精華的前 50 名
    smart_money = smart_money.sort_values(by='十日買賣超', ascending=False).head(50)
    
    # 為了配合前端，把動態找到的股票欄位名稱改為統一的「股票代號」
    smart_money = smart_money.rename(columns={col_stock: '股票代號', col_broker: '券商分點'})

    # 存檔
    smart_money.to_json(json_path, orient='records', force_ascii=False)
    print(f" ✅ 順利導出主力名單 JSON！共計 {len(smart_money)} 檔鎖碼飆股。")

except Exception as e:
    print(f" ❌ 🚨 計算過程中崩潰: {e}")
    with open(json_path, "w") as f: f.write("[]")
