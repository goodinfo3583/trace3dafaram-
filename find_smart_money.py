import pandas as pd
import glob
import json
import os

# 1. 抓取最近 10 天的券商交易檔案
# 假設你的檔案路徑在 data/broker/
file_paths = sorted(glob.glob("data/broker/broker_trades_*.csv"), reverse=True)[:10]

if not file_paths:
    print("找不到券商交易紀錄")
    exit()

df_list = []
for f in file_paths:
    try:
        temp_df = pd.read_csv(f)
        df_list.append(temp_df)
    except Exception as e:
        pass

# 2. 合併最近 10 天的所有資料
all_trades = pd.concat(df_list, ignore_index=True)

# 3. 核心魔法：將「股票」與「券商」群組，計算這 10 天的總買賣超
# 假設欄位名稱為：'股票代號', '股票名稱', '券商分點', '買賣超' (請依實際 CSV 欄位名稱修改)
grouped = all_trades.groupby(['股票代號', '股票名稱', '券商分點']).agg(
    十日總買進=('買進', 'sum'),
    十日總賣出=('賣出', 'sum'),
    十日買賣超=('買賣超', 'sum'),
    交易天數=('日期', 'nunique') # 計算這10天內，該券商有幾天在買賣這檔股票
).reset_index()

# 4. 篩選條件：尋找「真正在囤貨」的主力！
# 條件 A：十日總買賣超 > 1000 張 (代表是大買家)
# 條件 B：十日總賣出幾乎為 0 (買進/賣出 比例極度懸殊，代表他只進不出，正在鎖碼)
# 條件 C：交易天數 >= 3 天 (代表不是一日遊的隔日沖)
smart_money = grouped[
    (grouped['十日買賣超'] > 500) & 
    (grouped['十日總買進'] > grouped['十日總賣出'] * 5) & 
    (grouped['交易天數'] >= 3)
]

# 5. 排序並輸出最精華的前 50 名
smart_money = smart_money.sort_values(by='十日買賣超', ascending=False).head(50)

# 將結果存成極輕量的 JSON 檔案 (供網頁讀取)
output_dir = "docs/data"
os.makedirs(output_dir, exist_ok=True)
smart_money.to_json(f"{output_dir}/smart_money_targets.json", orient='records', force_ascii=False)

print("✅ 主力囤貨名單分析完成！已輸出至 docs/data/smart_money_targets.json")
