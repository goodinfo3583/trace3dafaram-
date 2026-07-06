import streamlit as st
import pandas as pd
import os
import glob
import re
import requests
from collections import defaultdict

# ==========================================
# 🌟 全域股票字典讀取引擎
# ==========================================
@st.cache_data(ttl=86400)
def load_stock_dict():
    STOCK_DICT = {}
    search_pattern = os.path.join("./Goodinfo_Rankings", "*上市櫃*csv")
    files = glob.glob(search_pattern)
    if files:
        try:
            df = pd.read_csv(files[0])
            for col in ['股票代號', '代號', '證券代號']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df[col] = df[col].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                    
            for _, row in df.iterrows():
                sid = str(row.get('股票代號', row.get('代號', ''))).strip()
                name = str(row.get('股票名稱', row.get('名稱', ''))).strip()
                ind = str(row.get('產業別', row.get('產業', 'ETF / 債券 / 其他'))).strip()
                if sid:
                    STOCK_DICT[sid] = {"id": sid, "name": name, "industry": ind}
        except Exception as e:
            st.error(f"字典讀取錯誤: {e}")
    return STOCK_DICT

# ==========================================
# 🌟 本地 CSV 預載入與外資數據讀取引擎
# ==========================================
def preload_all_csv_data():
    DATA_DIR = "./Goodinfo_Rankings"
    
    def safe_load(key, kw1, kw2=""):
        if key in st.session_state and not st.session_state[key].empty: return
        files = glob.glob(os.path.join(DATA_DIR, f"*{kw1}*.csv"))
        if kw2: files = [f for f in files if kw2 in f]
        if files:
            for enc in ['cp950', 'utf-8-sig', 'utf-8']:
                try:
                    df = pd.read_csv(sorted(files, reverse=True)[0], encoding=enc)
                    if not df.empty:
                        df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
                        id_col = next((c for c in df.columns if '代號' in c or 'code' in c.lower()), None)
                        nm_col = next((c for c in df.columns if '名稱' in c or 'name' in c.lower()), None)
                        
                        rename_dict = {}
                        if id_col and id_col != '股票代號': rename_dict[id_col] = '股票代號'
                        if nm_col and nm_col != '股票名稱': rename_dict[nm_col] = '股票名稱'
                        if rename_dict: df = df.rename(columns=rename_dict)
                        
                        if '股票代號' in df.columns:
                            df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                            
                        st.session_state[key] = df
                        return
                except: continue
        st.session_state[key] = pd.DataFrame()

    safe_load('df_blk2_1', '外資買', '成交')
    safe_load('df_blk2_2', '投信買', '成交')
    safe_load('df_blk2_3', '外資買', '發行')
    safe_load('df_blk2_4', '投信買', '發行')
    safe_load('df_blk3_main', '連買')
    safe_load('df_margin_pct', '融資減少幅度')
    safe_load('df_margin_vol', '融資減少張數')
    safe_load('df_short_pct', '借券賣出減少幅度')
    safe_load('df_short_vol', '借券賣出減少張數')
    safe_load('df_margin_plus_pct', '融券增加幅度')
    safe_load('df_margin_plus_vol', '融券增加張數')
    safe_load('df_blk5', '400張')
    if st.session_state.get('df_blk5', pd.DataFrame()).empty: safe_load('df_blk5', '大股東')
    safe_load('df_blk5_1000', '1000張')
    if st.session_state.get('df_blk5_1000', pd.DataFrame()).empty: safe_load('df_blk5_1000', '大股東')

@st.cache_data(ttl=3600)
def load_foreign_ratio_data(data_dir="./Goodinfo_Rankings"):
    foreign_csvs = glob.glob(os.path.join(data_dir, "*外資持股比例*.csv"))
    if not foreign_csvs:
        return pd.DataFrame()
        
    files_by_date = defaultdict(list)
    for f in foreign_csvs:
        date_match = re.search(r'(202\d{5})', os.path.basename(f))
        if date_match:
            files_by_date[date_match.group(1)].append(f)
            
    daily_dfs = []
    for date_str, files in files_by_date.items():
        chunks = []
        for f in files:
            try:
                temp_df = pd.read_csv(f)
                temp_df.columns = temp_df.columns.str.replace(r'\s+', '', regex=True)
                cols_to_keep = ['代號', '名稱', '外資持股(%)']
                temp_df = temp_df[[c for c in cols_to_keep if c in temp_df.columns]]
                chunks.append(temp_df)
            except Exception:
                pass 
                
        if chunks:
            day_df = pd.concat(chunks, ignore_index=True)
            day_df['代號'] = day_df['代號'].astype(str).str.strip()
            day_df = day_df.drop_duplicates(subset=['代號'])
            
            day_df = day_df.rename(columns={
                '代號': '股票代號',
                '外資持股(%)': f'外資持股_{date_str}'
            })
            day_df = day_df.drop(columns=['名稱'], errors='ignore')
            daily_dfs.append(day_df)

    if not daily_dfs:
        return pd.DataFrame()

    final_foreign_df = daily_dfs[0]
    for i in range(1, len(daily_dfs)):
        final_foreign_df = pd.merge(final_foreign_df, daily_dfs[i], on='股票代號', how='outer')
        
    final_foreign_df = final_foreign_df.fillna(0.0)
    return final_foreign_df

# ==========================================
# 🌟 區塊 1：GitHub 抓取與核心母表合併引擎
# ==========================================
@st.cache_data(ttl=3600)
def fetch_github_json_all():
    days_list = [5, 20, 60, 120]
    json_dfs = {}
    account, repo, branch = "goodinfo3583", "DDong_tw-institutional-stocker", "main"
    
    for d in days_list:
        url = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/top_three_inst_change_{d}_up.json"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                df['股票代號'] = df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                df['股票名稱'] = df['name'].astype(str).str.strip()
                df = df.rename(columns={'three_inst_ratio': '法人持股', 'change': f'{d}日ΔChange'})
                df[f'{d}日排名'] = (df.index + 1).astype(int) 
                json_dfs[d] = df[['股票代號', '股票名稱', '法人持股', f'{d}日ΔChange', f'{d}日排名']]
            else: json_dfs[d] = pd.DataFrame()
        except Exception: json_dfs[d] = pd.DataFrame()
        
    latest_all_df = pd.DataFrame()
    try:
        url_all = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/stock_three_inst_latest.json"
        res_all = requests.get(url_all, timeout=5)
        if res_all.status_code == 200:
            temp_df = pd.DataFrame(res_all.json())
            if not temp_df.empty and 'code' in temp_df.columns and 'change' in temp_df.columns:
                temp_df['股票代號'] = temp_df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                temp_df['股票代號'] = temp_df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                latest_all_df = temp_df[['股票代號', 'change']].rename(columns={'change': '精準單日△'})
    except Exception: pass
    return json_dfs, latest_all_df

def extract_date_from_filename(filename):
    m8 = re.search(r'(202\d{5})', filename)
    if m8: return m8.group(1)
    return None

@st.cache_data(ttl=300)
def build_block1_master_df():
    DATA_DIR = "./Goodinfo_Rankings"
    date_files = defaultdict(lambda: {'txt': [], 'csv': []})
    all_csv_files = glob.glob(os.path.join(DATA_DIR, "*JSON*.csv"))
    
    for f in all_csv_files:
        d_label = extract_date_from_filename(os.path.basename(f))
        if d_label: date_files[d_label]['csv'].append(f)

    sorted_dates = sorted(date_files.keys(), reverse=True)
    f_df = pd.DataFrame()
    
    j_dfs, l_all_df = fetch_github_json_all()

    if sorted_dates:
        for i, date_label in enumerate(sorted_dates[:30]): 
            day_dfs = []
            if date_files[date_label]['csv']:
                df = pd.read_csv(date_files[date_label]['csv'][0], encoding='utf-8-sig')
                if '股票代號' in df.columns:
                    df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                    df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
                    df = df.rename(columns={'法人持股': f"{date_label}持股%"})
                    day_dfs.append(df)
                
            day_dfs = [df for df in day_dfs if not df.empty]
            if not day_dfs: continue
                
            df_day_raw = pd.concat(day_dfs, ignore_index=True)
            def agg_sections_func(x):
                valid_x = set()
                for val in x:
                    if pd.notna(val) and str(val).strip() != "":
                        for p in str(val).split(','): valid_x.add(p.strip())
                return ",".join([s for s in ['5日', '20日', '60日', '120日'] if s in valid_x])
                
            agg_dict = {f"{date_label}持股%": 'max', '上榜區塊': agg_sections_func}
            df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg(agg_dict).reset_index().rename(columns={'上榜區塊': f"{date_label}_區塊"})
                
            if f_df is None or f_df.empty: f_df = df_day
            else: f_df = pd.merge(f_df, df_day, on=['股票代號', '股票名稱'], how='outer')
                
        if f_df is not None and not f_df.empty:
            d_cols = sorted([c for c in f_df.columns if '持股%' in c], reverse=True)
            for c in d_cols: f_df[c] = pd.to_numeric(f_df[c], errors='coerce').fillna(0)
                
            def generate_tags(sections):
                if pd.isna(sections) or not sections: return ""
                sec_list = str(sections).split(',')
                tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if key in sec_list]
                return " ".join(tags)
                
            latest_sect_col = f"{sorted_dates[0]}_區塊"
            if latest_sect_col not in f_df.columns: f_df[latest_sect_col] = ""
            
            f_df['今日上榜'] = f_df[latest_sect_col].apply(generate_tags)
            f_df['上榜數量'] = f_df['今日上榜'].apply(lambda x: str(x).count('日'))
                
            def evaluate_trend(row):
                if len(d_cols) < 2: return "⚪ 資料不足"
                dynamics, v0, v1 = [], row[d_cols[0]], row[d_cols[1]]
                diff1 = v0 - v1  
                if diff1 > 0:
                    is_slowing = False
                    if len(d_cols) >= 3:
                        v2 = row[d_cols[2]]
                        if v0 > v1 > v2 > 0: dynamics.append("🪜 階梯吸籌")
                        elif len(d_cols) >= 4 and v0 >= v1 >= v2 >= row[d_cols[3]] > 0 and v0 > row[d_cols[3]]: dynamics.append("🛡️ 穩健吸籌")
                        if v1 != 0 and v2 != 0 and diff1 < (v1 - v2): dynamics.append("⚠️ 趨緩"); is_slowing = True
                    if not is_slowing: dynamics.append("📈 上升")
                elif diff1 < 0: dynamics.append("📉 下降")
                else: dynamics.append("🔄 持平")
                    
                today_list = [s for s in str(row.get(f"{sorted_dates[0]}_區塊", "")).split(',') if s]
                yest_list = [s for s in str(row.get(f"{sorted_dates[1]}_區塊", "")).split(',') if s]
                
                if v0 > 0 and v1 == 0 and any(row[c] > 0 for c in d_cols[2:]): dynamics.append("🔄 洗盤回歸")
                if 1 <= len(yest_list) <= 3 and len(today_list) > len(yest_list):
                    new_entries = [i for i in today_list if i not in yest_list]
                    tags = [tag for tag, key in [('🔴5日', '5日'), ('🟡20日', '20日'), ('🟢60日', '60日'), ('🔵120日', '120日')] if any(key in item for item in new_entries)]
                    if tags: dynamics.append(f"🚀 衝進{'、'.join(tags)}榜單")
                return " | ".join(dynamics)
                    
            f_df['最新動態'] = f_df.apply(evaluate_trend, axis=1)
            f_df['法人持股'] = f_df[d_cols[0]]
            
            if not l_all_df.empty and '股票代號' in l_all_df.columns:
                f_df = pd.merge(f_df, l_all_df, on='股票代號', how='left')
                f_df['△'] = f_df['精準單日△'].fillna(0.0)
            else:
                if len(d_cols) >= 2:
                    f_df['△'] = f_df.apply(lambda row: row[d_cols[0]] - row[d_cols[1]] if row[d_cols[1]] > 0.001 else 0.0, axis=1)
                else: f_df['△'] = 0.0
                
            f_df['法人金額'] = 0.0 

            for d in [5, 20, 60, 120]:
                if d in j_dfs and not j_dfs[d].empty:
                    temp_json = j_dfs[d][['股票代號', f'{d}日ΔChange', f'{d}日排名']]
                    f_df = pd.merge(f_df, temp_json, on='股票代號', how='left')

            col_ref = f_df.set_index('股票代號')['上榜數量'].to_dict()
            for col in d_cols: f_df[col] = f_df[col].apply(lambda x: "未進榜" if pd.isna(x) or abs(x) < 0.0001 else f"{x:.2f}")

            f_df['今日有上榜_排序'] = f_df['今日上榜'] != ""
            if d_cols:
                f_df = f_df.sort_values(by=['今日有上榜_排序', '上榜數量', d_cols[0]], ascending=[False, False, False])
            
            return f_df, sorted_dates, d_cols, col_ref
    
    return pd.DataFrame(), [], [], {}

# 💡 啟動引擎
def init_all_data():
    if 'my_final_df' not in st.session_state or st.session_state['my_final_df'].empty or st.session_state.get('force_reload', False):
        with st.spinner("⚡ 背景引擎啟動中，正在載入全市場籌碼數據... (僅需數秒)"):
            json_dfs, latest_all_df = fetch_github_json_all()
            final_df, sorted_dates, date_cols, color_ref = build_block1_master_df()
            st.session_state['my_final_df'] = final_df
            st.session_state['sorted_dates'] = sorted_dates 
            preload_all_csv_data()  
            st.session_state['force_reload'] = False
