# views/b1_page.py
import streamlit as st
import pandas as pd
import os
import glob
import re
import html
import datetime
import requests
import plotly.express as px
from collections import defaultdict

# ==========================================
# 🌟 區塊 1 專屬工具函數區 (純運算，無 UI)
# ==========================================

@st.cache_data(ttl=3600)
def load_foreign_ratio_data(data_dir):
    """掃描資料夾中所有外資持股比例的 CSV 檔案"""
    foreign_csvs = glob.glob(os.path.join(data_dir, "*外資持股比例*.csv"))
    if not foreign_csvs: return pd.DataFrame()
        
    files_by_date = defaultdict(list)
    for f in foreign_csvs:
        date_match = re.search(r'(202\d{5})', os.path.basename(f))
        if date_match: files_by_date[date_match.group(1)].append(f)
            
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
            except: pass
                
        if chunks:
            day_df = pd.concat(chunks, ignore_index=True)
            day_df['代號'] = day_df['代號'].astype(str).str.strip()
            day_df = day_df.drop_duplicates(subset=['代號'])
            day_df = day_df.rename(columns={
                '代號': '股票代號',
                '名稱': '股票名稱',
                '外資持股(%)': f'外資持股_{date_str}'
            })
            day_df = day_df.drop(columns=['股票名稱'], errors='ignore')
            daily_dfs.append(day_df)

    if not daily_dfs: return pd.DataFrame()

    final_foreign_df = daily_dfs[0]
    for i in range(1, len(daily_dfs)):
        final_foreign_df = pd.merge(final_foreign_df, daily_dfs[i], on='股票代號', how='outer')
        
    return final_foreign_df.fillna(0.0)

@st.cache_data(ttl=600)
def fetch_github_json_all():
    """從 GitHub 取得最新的正向法人籌碼 JSON (維持原版 5/20/60/120)"""
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
        except: json_dfs[d] = pd.DataFrame()
        
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
    except: pass
    
    return json_dfs, latest_all_df

def extract_date_from_filename(filename):
    m8 = re.search(r'(202\d{5})', filename)
    if m8: return m8.group(1)
    return None

@st.cache_data(ttl=300)
def build_block1_master_df(data_dir):
    """合併所有歷史快照與 GitHub 即時數據，產生正向全域母表"""
    date_files = defaultdict(lambda: {'txt': [], 'csv': []})
    all_csv_files = glob.glob(os.path.join(data_dir, "*JSON*.csv"))
    
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
            
            return f_df, sorted_dates, d_cols, col_ref, j_dfs
    
    return pd.DataFrame(), [], [], {}, {}

# 抓取持股衰竭
@st.cache_data(ttl=600)
def fetch_github_json_down():
    """獨立抓取法人持股衰退(負向)的 JSON 資料"""
    days_list = [5, 10, 20, 30] 
    json_dfs = {}
    
    account, repo, branch = "voidful", "tw-institutional-stocker", "main"

    for d in days_list:
        url = f"https://raw.githubusercontent.com/{account}/{repo}/{branch}/docs/data/top_three_inst_change_{d}_down.json"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                if not df.empty:
                    df['股票代號'] = df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                    df['股票名稱'] = df['name'].astype(str).str.strip()
                    
                    df = df.rename(columns={
                        'three_inst_ratio': '法人持股', 
                        'change': '累積衰退'
                    })
                    df['排名'] = (df.index + 1).astype(int) 
                    
                    # 拿掉 % 符號的動作，保留純數值，才能順利存入 CSV 計算單日歷史△
                    json_dfs[d] = df[['排名', '股票代號', '股票名稱', '法人持股', '累積衰退']]
                else:
                    json_dfs[d] = pd.DataFrame()
            else:
                json_dfs[d] = pd.DataFrame()
        except:
            json_dfs[d] = pd.DataFrame()
            
    return json_dfs

@st.cache_data(ttl=300)
def build_block1_down_master_df(data_dir):
    """合併所有【負向衰退】歷史快照，產生全域母表"""
    date_files = defaultdict(list)
    all_csv_files = glob.glob(os.path.join(data_dir, "*_Down_History.csv"))

    for f in all_csv_files:
        d_label = extract_date_from_filename(os.path.basename(f))
        if d_label: date_files[d_label].append(f)

    sorted_dates = sorted(date_files.keys(), reverse=True)
    f_df = pd.DataFrame()

    if sorted_dates:
        for i, date_label in enumerate(sorted_dates[:30]):
            df = pd.read_csv(date_files[date_label][0], encoding='utf-8-sig')
            if not df.empty and '股票代號' in df.columns:
                df['股票代號'] = df['股票代號'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df['股票代號'] = df['股票代號'].apply(lambda x: x.zfill(4) if x.isdigit() else x)
                df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
                
                # 防呆：確保法人持股為數值
                if df['法人持股'].dtype == object:
                    df['法人持股'] = df['法人持股'].astype(str).str.replace('%', '', regex=False)
                df['法人持股'] = pd.to_numeric(df['法人持股'], errors='coerce').fillna(0.0)

                df = df.rename(columns={'法人持股': f"{date_label}持股%"})

                def agg_sections_func(x):
                    valid_x = set()
                    for val in x:
                        if pd.notna(val) and str(val).strip() != "":
                            for p in str(val).split(','): valid_x.add(p.strip())
                    return ",".join(list(valid_x))

                agg_dict = {f"{date_label}持股%": 'max'}
                if '上榜區塊' in df.columns:
                    agg_dict['上榜區塊'] = agg_sections_func

                df_day = df.groupby(['股票代號', '股票名稱']).agg(agg_dict).reset_index()
                if '上榜區塊' in df.columns:
                    df_day = df_day.rename(columns={'上榜區塊': f"{date_label}_區塊"})

                if f_df is None or f_df.empty: f_df = df_day
                else: f_df = pd.merge(f_df, df_day, on=['股票代號', '股票名稱'], how='outer')

        if f_df is not None and not f_df.empty:
            d_cols = sorted([c for c in f_df.columns if '持股%' in c], reverse=True)
            for c in d_cols: f_df[c] = pd.to_numeric(f_df[c], errors='coerce').fillna(0)

            latest_sect_col = f"{sorted_dates[0]}_區塊"
            if latest_sect_col not in f_df.columns: f_df[latest_sect_col] = ""

            f_df['今日衰退上榜'] = f_df[latest_sect_col].fillna("")

            # 計算單日衰退 △
            if len(d_cols) >= 2:
                f_df['單日△'] = f_df.apply(lambda row: row[d_cols[0]] - row[d_cols[1]] if row[d_cols[1]] > 0.001 else 0.0, axis=1)
            else: 
                f_df['單日△'] = 0.0

            for col in d_cols:
                f_df[col] = f_df[col].apply(lambda x: "未進榜" if pd.isna(x) or abs(x) < 0.0001 else f"{x:.2f}")

            # 負向表單：依據單日△ 排序 (越負排越前面)
            f_df = f_df.sort_values(by=['單日△'], ascending=True)
            return f_df, sorted_dates, d_cols

    return pd.DataFrame(), [], []

# ==========================================
# ⚙️ 後台資料引擎 (Data Engine)
# ==========================================
def sync_b1_data(data_dir):
    """B1 專屬背景同步引擎"""
    final_df, sorted_dates, date_cols, color_ref, json_dfs = build_block1_master_df(data_dir)
    # 載入負向母表
    down_final_df, down_sorted_dates, down_date_cols = build_block1_down_master_df(data_dir)
    foreign_df = load_foreign_ratio_data(data_dir)
    
    st.session_state['b1_final_df'] = final_df
    st.session_state['b1_sorted_dates'] = sorted_dates
    st.session_state['b1_date_cols'] = date_cols
    st.session_state['b1_color_ref'] = color_ref
    st.session_state['b1_json_dfs'] = json_dfs
    st.session_state['b1_foreign_df'] = foreign_df
    
    st.session_state['b1_down_final_df'] = down_final_df
    st.session_state['b1_down_sorted_dates'] = down_sorted_dates
    st.session_state['b1_down_date_cols'] = down_date_cols

# ==========================================
# 🖼️ 前台畫面渲染 (Views)
# ==========================================
def show_b1_page(DATA_DIR, STOCK_DICT):
    """B1 專屬頁面 UI 渲染"""
    
    if 'b1_final_df' not in st.session_state:
        with st.spinner("⚡ 載入法人籌碼大數據中..."):
            sync_b1_data(DATA_DIR)
            
    final_df = st.session_state.get('b1_final_df', pd.DataFrame())
    sorted_dates = st.session_state.get('b1_sorted_dates', [])
    date_cols = st.session_state.get('b1_date_cols', [])
    color_ref = st.session_state.get('b1_color_ref', {})
    json_dfs = st.session_state.get('b1_json_dfs', {})
    df_foreign = st.session_state.get('b1_foreign_df', pd.DataFrame())
    
    down_final_df = st.session_state.get('b1_down_final_df', pd.DataFrame())
    down_date_cols = st.session_state.get('b1_down_date_cols', [])

    st.write("---")
    st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)

    if sorted_dates:
        latest_d = sorted_dates[0]
        fmt_date = f"{latest_d[:4]}/{latest_d[4:6]}/{latest_d[6:]}"
        st.markdown(
            f"<h2 style='margin-bottom: 0px;'>法人動向：三大法人短中長線持股比追蹤 "
            f"<span style='color:#00D2FF; font-size:16px; font-weight:500; margin-left:12px;'>基準日：{fmt_date}</span></h2>", 
            unsafe_allow_html=True
        )
    else:
        st.markdown("<h2 style='margin-bottom: 0px;'>👑 區塊1：三大法人短中長線持股比追蹤</h2>", unsafe_allow_html=True)

    # ------------------------------------------
    # 💾 站長專屬：JSON 200名快照存檔區
    # ------------------------------------------
    all_json_csvs = glob.glob(os.path.join(DATA_DIR, "*JSON_History.csv"))
    local_latest_date = "無紀錄"
    if all_json_csvs:
        dates = [m.group(1) for f in all_json_csvs if (m := re.search(r'(202\d{5})', os.path.basename(f)))]
        if dates: local_latest_date = max(dates)

    today_str = datetime.datetime.now().strftime("%Y%m%d")
    is_updated_today = (local_latest_date == today_str)
    status_icon = "✅" if is_updated_today else "⚠️"
    status_text = f"{status_icon} 本地最新: {local_latest_date}"

    st.write("") 
    c_btn1, c_btn2 = st.columns(2)

    with c_btn1: 
        st.link_button("📊 台股法人籌碼追蹤 (50名)", "https://goodinfo3583.github.io/DDong_tw-institutional-stocker/", use_container_width=True)

    with c_btn2:
        try: exp_container = st.popover(f"🛠 站長快照 ({status_text})", use_container_width=True)
        except AttributeError: exp_container = st.expander(f"🛠 站長：下載 200名快照 ({status_text})", expanded=False)
            
        with exp_container:
            if is_updated_today: st.success(f"✅ **今日已更新！** 資料夾中最新快照為 `{local_latest_date}`。")
            else: st.warning(f"⚠️ **今日尚未更新！** 資料夾中最新快照停留在 `{local_latest_date}`，請記得下載！")
                
            admin_pw = st.text_input("請輸入站長密碼以解鎖功能", type="password", key="admin_pw_input")
            
            if admin_pw == "DDong888": 
                st.success("🔓 驗證成功！請執行快照封存。")
                
                if st.button("🔄 強制抓取 GitHub 最新數據", use_container_width=True):
                    fetch_github_json_all.clear()
                    fetch_github_json_down.clear()
                    build_block1_master_df.clear()
                    build_block1_down_master_df.clear()
                    sync_b1_data(DATA_DIR) 
                    st.rerun()                     
                
                snap_date = st.date_input("選擇這份資料的實際基準日")
                st.write("")
                
                if st.button("💾 站長專屬：一鍵封存今日【正向】與【負向衰退】歷史數據", use_container_width=True, type="primary"):
                    date_str = snap_date.strftime("%Y%m%d")
                    
                    # --- 1. 處理正向數據 (5/20/60/120) ---
                    save_path_up = os.path.join(DATA_DIR, f"{date_str}_JSON_History.csv")
                    all_snap_up = []
                    for d in [5, 20, 60, 120]:
                        if d in json_dfs and not json_dfs[d].empty:
                            temp = json_dfs[d][['股票代號', '股票名稱', '法人持股']].copy()
                            temp['上榜區塊'] = f"{d}日"
                            all_snap_up.append(temp)
                    
                    if all_snap_up:
                        snap_df_up = pd.concat(all_snap_up, ignore_index=True)
                        snap_grouped_up = snap_df_up.groupby(['股票代號', '股票名稱']).agg({
                            '法人持股': 'max', '上榜區塊': lambda x: ",".join(set(x))
                        }).reset_index()
                        
                        # 儲存於伺服器供系統讀取
                        snap_grouped_up.to_csv(save_path_up, index=False, encoding='utf-8-sig')
                        
                        # 🌟 寫入 session_state，為了稍後給真正的下載按鈕使用
                        st.session_state['dl_csv_up'] = snap_grouped_up.to_csv(index=False).encode('utf-8-sig')
                        st.session_state['dl_name_up'] = f"{date_str}_JSON_History.csv"
                        st.success(f"✅ 成功生成【正向】歷史快照 ({len(snap_grouped_up)} 檔)！")
                    else: 
                        st.error("❌ 尚未獲取到 GitHub 正向數據，封存失敗。")

                    # --- 2. 處理負向數據 (5/10/20/30) ---
                    save_path_down = os.path.join(DATA_DIR, f"{date_str}_Down_History.csv")
                    all_snap_down = []
                    current_down_dfs = fetch_github_json_down()
                    
                    for d in [5, 10, 20, 30]:
                        if d in current_down_dfs and not current_down_dfs[d].empty:
                            temp = current_down_dfs[d].copy()
                            temp['上榜區塊'] = f"{d}日衰退"
                            all_snap_down.append(temp)
                    
                    if all_snap_down:
                        snap_df_down = pd.concat(all_snap_down, ignore_index=True)
                        snap_grouped_down = snap_df_down.groupby(['股票代號', '股票名稱']).agg({
                            '法人持股': 'max',
                            '上榜區塊': lambda x: ",".join(set(x)),
                            '累積衰退': 'first'
                        }).reset_index()
                        
                        # 儲存於伺服器供系統讀取
                        snap_grouped_down.to_csv(save_path_down, index=False, encoding='utf-8-sig')
                        
                        # 🌟 寫入 session_state
                        st.session_state['dl_csv_down'] = snap_grouped_down.to_csv(index=False).encode('utf-8-sig')
                        st.session_state['dl_name_down'] = f"{date_str}_Down_History.csv"
                        st.success(f"✅ 成功生成【負向衰退】歷史快照 ({len(snap_grouped_down)} 檔)！")
                    else: 
                        st.error("❌ 尚未獲取到 GitHub 負向數據，封存失敗。")
                        
                    # 清空快取重新載入母表
                    build_block1_master_df.clear() 
                    build_block1_down_master_df.clear()
                    
                # 🌟 實體的下載按鈕區塊：必須放在 st.button() 外，這樣點擊下載時按鈕才不會因為重整而消失！
                if 'dl_csv_up' in st.session_state and 'dl_csv_down' in st.session_state:
                    st.info("💡 系統已成功將歷史紀錄儲存於背景！若需保存實體檔案至電腦，請點擊下方按鈕下載：")
                    c_dl1, c_dl2 = st.columns(2)
                    with c_dl1:
                        st.download_button(
                            label="📥 下載實體【正向】CSV", 
                            data=st.session_state['dl_csv_up'], 
                            file_name=st.session_state['dl_name_up'],
                            mime="text/csv", type="primary", use_container_width=True
                        )
                    with c_dl2:
                        st.download_button(
                            label="📥 下載實體【負向】CSV", 
                            data=st.session_state['dl_csv_down'], 
                            file_name=st.session_state['dl_name_down'],
                            mime="text/csv", type="primary", use_container_width=True
                        )
                        
            elif admin_pw != "": 
                st.error("❌ 密碼錯誤，無法使用此功能。")


    # ==========================================
    # 🔧 UI 數據渲染 (四大榜單)
    # ==========================================
    c1, c2, c3 = st.columns([1, 1, 2])
    show_etf = c1.checkbox("顯示 ETF", value=True, key="blk1_etf_sync")
    show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="blk1_bond_sync")
    search_kw = c3.text_input("🔍 快速尋找標的 (輸入代號或名稱)", placeholder="例如: 2890 或 永豐金")

    tab5, tab20, tab60, tab120, tab_all = st.tabs([
        "🔴 5日排行", "🟡 20日排行", "🟢 60日排行", "🔵 120日排行", "📊 歷史軌跡全能池"
    ])

    def format_delta(x):
        try:
            val = float(x)
            if abs(val) < 0.005: return "0.00"
            return f"+{val:.2f}" if val > 0 else f"{val:.2f}"
        except: return "0.00"

    def get_local_tab_df(target_day_str):
        if final_df is None or final_df.empty: return pd.DataFrame()
        df = final_df[final_df['今日上榜'].str.contains(f'{target_day_str}日', na=False)].copy()
        if df.empty: return df
        
        is_bond = df['股票代號'].str.endswith('B')
        is_etf = (df['股票代號'].str.len() >= 5) & (~is_bond)
        is_stock = df['股票代號'].str.len() == 4
        mask = is_stock
        if show_etf: mask |= is_etf
        if show_bond: mask |= is_bond
        if search_kw:
            mask &= (df['股票代號'].str.contains(search_kw, na=False)) | (df['股票名稱'].str.contains(search_kw, na=False))
        df = df[mask].copy()
        
        rank_col = f'{target_day_str}日排名'
        change_col = f'{target_day_str}日ΔChange'
        
        if rank_col in df.columns:
            df = df.sort_values(by=rank_col, ascending=True)
        elif change_col in df.columns:
            df[change_col] = pd.to_numeric(df[change_col], errors='coerce').fillna(0)
            df = df.sort_values(by=change_col, ascending=False)
            df[f'{target_day_str}日排名'] = range(1, len(df) + 1)
            
        df['法人持股'] = df['法人持股'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
        df['△'] = df['△'].apply(format_delta)
        if change_col in df.columns: 
            df[change_col] = df[change_col].apply(format_delta)
            
        df['法人金額'] = "0.00" 
        df['最新動態'] = df['最新動態'].fillna("⚪ 尚無比對紀錄")
        return df

    with tab5:
        df_5 = get_local_tab_df(5)
        display_cols = ['5日排名', '股票代號', '股票名稱', '法人持股', '△', '5日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_5.empty: st.dataframe(df_5[[c for c in display_cols if c in df_5.columns]], use_container_width=True, hide_index=True)
        else: st.info("⚪ 尚無 5日進榜數據。")
    with tab20:
        df_20 = get_local_tab_df(20)
        display_cols = ['20日排名', '股票代號', '股票名稱', '法人持股', '△', '20日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_20.empty: st.dataframe(df_20[[c for c in display_cols if c in df_20.columns]], use_container_width=True, hide_index=True)
    with tab60:
        df_60 = get_local_tab_df(60)
        display_cols = ['60日排名', '股票代號', '股票名稱', '法人持股', '△', '60日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_60.empty: st.dataframe(df_60[[c for c in display_cols if c in df_60.columns]], use_container_width=True, hide_index=True)
    with tab120:
        df_120 = get_local_tab_df(120)
        display_cols = ['120日排名', '股票代號', '股票名稱', '法人持股', '△', '120日ΔChange', '法人金額', '最新動態', '今日上榜']
        if not df_120.empty: st.dataframe(df_120[[c for c in display_cols if c in df_120.columns]], use_container_width=True, hide_index=True)
            
    with tab_all:
        if final_df is not None and not final_df.empty:
            is_bond = final_df['股票代號'].str.endswith('B')
            is_etf = (final_df['股票代號'].str.len() >= 5) & (~is_bond)
            is_stock = final_df['股票代號'].str.len() == 4
            mask = is_stock
            if show_etf: mask |= is_etf
            if show_bond: mask |= is_bond
            if search_kw:
                mask &= (final_df['股票代號'].str.contains(search_kw, na=False)) | (final_df['股票名稱'].str.contains(search_kw, na=False))
                
            filtered_df = final_df[mask].copy()
            filtered_df['法人持股'] = filtered_df['法人持股'].apply(lambda x: f"{x:.2f}%")
            filtered_df['△'] = filtered_df['△'].apply(format_delta)
            
            def highlight_row(row):
                cnt = color_ref.get(row['股票代號'], 0)
                if cnt == 4: bg = 'background-color: rgba(240, 90, 90, 0.25)'     
                elif cnt == 3: bg = 'background-color: rgba(255, 165, 0, 0.25)'    
                elif cnt == 2: bg = 'background-color: rgba(80, 200, 120, 0.25)'    
                elif cnt == 1: bg = 'background-color: rgba(0, 127, 255, 0.25)'    
                else: bg = 'background-color: #111622; color: #E2E8F0'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
                return [bg] * len(row)
                
            all_display_cols = ['股票代號', '股票名稱', '今日上榜', '最新動態', '△'] + date_cols
            st.dataframe(filtered_df[all_display_cols].style.apply(highlight_row, axis=1), use_container_width=True)

    st.write("")
    st.info("💡 △是單日的法人持股增減(如果最新基準日未進前200榜，△會直接以歸0計算)；5/20/60/120日ΔChange為5/20/60/120期間的累積變化，我們可以試著短線與長線一起觀察。")

    # ==========================================
    # 📊 繪製區塊 ：產業聚落與資金輪動板塊 (Treemap)
    # ==========================================
    st.write("---")
    st.markdown("### 🧩 資金聚落板塊：三大法人進榜產業分佈")
    st.caption("透過區塊面積大小，觀察法人資金集中攻擊哪些產業。")
    st.info("💡 △ 是單日的法人持股增減；滑鼠懸停可觀察短長線的持股波段軌跡。底色越紅買超越強，△代表單日法人持股增減，但也要小心大買大賣的名單。")

    if not final_df.empty and STOCK_DICT:
        st.write("")
        c_opt, c_search = st.columns([2.5, 1.5])
        with c_opt:
            top_n_option = st.radio("設定觀測範圍：", ["顯示前 50 名", "顯示前 200 名"], horizontal=True)
            top_n = 50 if "50" in top_n_option else 200
            
        with c_search:
            treemap_search = st.text_input("🔍 板塊內標的搜尋", placeholder="輸入代號/名稱以聚焦...", label_visibility="visible")

        t_5, t_20, t_60, t_120, t_all = st.tabs(["🔴 5日排行", "🟡 20日排行", "🟢 60日排行", "🔵 120日排行", "🌟 綜合熱力池"])

        def render_period_treemap(period_days):
            if period_days == "all":
                has_tag = final_df['今日上榜'].astype(str).str.strip() != ""
                period_df = final_df[has_tag].copy()
                if period_df.empty:
                    st.info("⚪ 今日尚無任何標的上榜。")
                    return
                period_df['熱力數值'] = pd.to_numeric(period_df['△'].astype(str).str.replace('+', '').str.replace('%', ''), errors='coerce').fillna(0.0)
                period_df = period_df.nlargest(top_n, '熱力數值').copy()
                period_df['綜合△排名'] = period_df['熱力數值'].rank(ascending=False, method='min')
                rank_col, title_name = '綜合△排名', "🌟 綜合上榜熱力池"
            else:
                rank_col = f"{period_days}日排名"
                if rank_col not in final_df.columns:
                    st.info(f"⚪ 尚無 {period_days} 日排行資料。")
                    return
                period_df = final_df[final_df[rank_col] > 0].nsmallest(top_n, rank_col).copy()
                if period_df.empty:
                    st.info(f"⚪ {period_days} 日排行無符合資料。")
                    return
                period_df['熱力數值'] = pd.to_numeric(period_df['△'].astype(str).str.replace('+', '').str.replace('%', ''), errors='coerce').fillna(0.0)
                title_name = f"🏆 {period_days}日資金聚落"

            period_df['產業別'] = period_df['股票代號'].astype(str).apply(lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他"))
            period_df['產業別'] = period_df['產業別'].replace('', 'ETF / 債券 / 其他')
            period_df = period_df[period_df['產業別'] != 'ETF / 債券 / 其他']

            if period_df.empty:
                st.info("⚪ 剔除 ETF/債券 後無一般產業資料。")
                return

            if treemap_search:
                query = treemap_search.strip()
                period_df = period_df[period_df['股票代號'].astype(str).str.contains(query, case=False, na=False) | period_df['股票名稱'].astype(str).str.contains(query, case=False, na=False)]
                if period_df.empty:
                    st.warning(f"此週期榜單中，找不到符合「{query}」的標的。")
                    return

            period_df['計數'] = 1 
            period_df['單日△_格式化'] = period_df['熱力數值'].apply(lambda x: f"+{x:.2f}" if x > 0 else f"{x:.2f}")

            def format_block_label(row):
                name = str(row.get('股票名稱', ''))
                delta_str = row.get('單日△_格式化', '0.00')
                rank_val = row.get(rank_col, '-')
                try: rank_str = str(int(float(rank_val)))
                except: rank_str = str(rank_val)
                rank_display = f"△排行: {rank_str}" if period_days == "all" else f"排名: {rank_str}"
                return f"<b>{name}</b><br><span style='font-size: 11px; color: #E5E7EB;'>△ {delta_str}<br>{rank_display}</span>"
            
            period_df['顯示名稱'] = period_df.apply(format_block_label, axis=1)
            t_date_cols = sorted([c for c in period_df.columns if '持股%' in c], reverse=True)[:7]
            hover_columns = ['股票代號', '今日上榜', '最新動態', '單日△_格式化', rank_col] + t_date_cols
            custom_continuous_scale = [[0.0, "rgba(0, 230, 118, 0.85)"], [0.5, "rgba(30, 41, 59, 0.95)"], [1.0, "rgba(255, 75, 75, 0.85)"]]

            fig = px.treemap(
                period_df, path=[px.Constant(title_name), '產業別', '顯示名稱'], values='計數',                      
                color='熱力數值', color_continuous_scale=custom_continuous_scale, color_continuous_midpoint=0, hover_data=hover_columns
            )
            fig.update_coloraxes(showscale=False)

            rank_hover_label = "綜合△排行" if period_days == "all" else f"{period_days}日排行"
            hover_template = (
                '<b>%{label}</b><br>股票代號: %{customdata[0]}<br>今日上榜: %{customdata[1]}<br>'
                '最新動態: %{customdata[2]}<br>單日△: <b>%{customdata[3]}</b><br>'
                f'{rank_hover_label}: <b>第 %{{customdata[4]}} 名</b><br>----------------<br>'
            )
            for i, col in enumerate(t_date_cols):
                clean_date = col.replace("持股%", "") 
                hover_template += f'{clean_date} 持股比: %{{customdata[{5+i}]}}%<br>'
            hover_template += '<extra></extra>'

            fig.update_traces(
                textinfo="label", textfont=dict(color="white", size=14),
                marker=dict(line=dict(color='#0B0F19', width=2), pad=dict(t=35, l=10, r=10, b=10)), hovertemplate=hover_template
            )
            fig.update_layout(margin=dict(t=30, l=0, r=0, b=0), height=650, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="sans-serif"))
            st.plotly_chart(fig, use_container_width=True)

        with t_5: render_period_treemap(5)
        with t_20: render_period_treemap(20)
        with t_60: render_period_treemap(60)
        with t_120: render_period_treemap(120)
        with t_all: render_period_treemap("all")

        # 🗑️ ETF 與債券懸停與變色模塊 (單行 HTML)
        is_etf = final_df['股票代號'].astype(str).apply(lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他") in ["ETF / 債券 / 其他", ""])
        on_list = final_df['今日上榜'].astype(str).str.strip() != ""
        excluded_etfs = final_df[is_etf & on_list].sort_values(by='股票代號')
        
        if not excluded_etfs.empty:
            st.write("")
            st.markdown("##### 🗑️ 本次已剔除的非一般產業 (ETF / 債券 / 指數)")
            st.caption("這些標的雖有強大法人資金進駐上榜，但已從上方產業聚落中剔除。**游標懸停於標籤可查看詳細 7 日明細。**")
            
            tags_html = ""
            date_cols_master = sorted([c for c in final_df.columns if '持股%' in c], reverse=True)[:7]
            
            for _, r in excluded_etfs.iterrows():
                name, sid, tag, dyn = html.escape(str(r.get('股票名稱', '')), quote=True), html.escape(str(r.get('股票代號', '')), quote=True), html.escape(str(r.get('今日上榜', '無')), quote=True), html.escape(str(r.get('最新動態', '-')), quote=True)
                try: d_val = float(str(r.get('△', 0.0)).replace('+', '').replace('%', ''))
                except: d_val = 0.0
                    
                if d_val > 0: bg_color, border_color, text_color, d_str = "rgba(255, 75, 75, 0.15)", "rgba(255, 75, 75, 0.4)", "#FF4B4B", f"+{d_val:.2f}"
                elif d_val < 0: bg_color, border_color, text_color, d_str = "rgba(0, 230, 118, 0.15)", "rgba(0, 230, 118, 0.4)", "#00E676", f"{d_val:.2f}"
                else: bg_color, border_color, text_color, d_str = "rgba(30, 41, 59, 0.6)", "#334155", "#94A3B8", "0.00"
                    
                tooltip_text = f"【{name}】&#10;股票代號: {sid}&#10;今日上榜: {tag}&#10;最新動態: {dyn}&#10;單日△: {d_str}&#10;----------------&#10;"
                for col in date_cols_master:
                    clean_date = col.replace("持股%", "") 
                    tooltip_text += f"{clean_date} 持股比: {r.get(col, '0.00')}%&#10;"
                
                tags_html += f"<div title=\"{tooltip_text}\" style=\"background-color: {bg_color}; color: #E2E8F0; border: 1px solid {border_color}; padding: 6px 14px; border-radius: 20px; margin: 5px; display: inline-flex; align-items: center; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); cursor: help; transition: transform 0.2s;\">{name} ({sid}) <span style='color: {text_color}; font-weight: bold; margin-left: 8px;'>△ {d_str}</span></div>"
            
            st.markdown(f"<div style='margin-top: 5px; line-height: 2.4;'>{tags_html}</div>", unsafe_allow_html=True)
    else:
        st.info("⚪ 尚無全市場大數據或找不到產業字典，請確認背景掃描引擎已啟動。")

    # ==========================================
    # 📉 法人提款機：持股衰退 (負向) 追蹤區塊
    # ==========================================
    st.write("---")
    st.markdown("### 📉 法人提款機：持股持續衰退追蹤 (負向)")
    st.caption("觀察法人資金撤出的標的，這些通常是被法人連日賣超、持股比例下降的清單。")
    
    down_dfs = fetch_github_json_down()
    
    t_down_5, t_down_10, t_down_20, t_down_30, t_down_history, t_down_all = st.tabs([
        "🟢 5日衰退", "🟢 10日衰退", "🟢 20日衰退", "🟢 30日衰退", "📅 單日歷史快照", "📊 歷史衰退全能池"
    ])
    
    def render_down_table(day_key):
        if day_key in down_dfs and not down_dfs[day_key].empty:
            df_display = down_dfs[day_key].copy()
            df_display['法人持股'] = df_display['法人持股'].apply(lambda x: f"{float(x):.2f}%" if pd.notna(x) else "0.00%")
            df_display['累積衰退'] = df_display['累積衰退'].apply(lambda x: f"{float(x):.2f}%" if pd.notna(x) else "0.00%")
            
            st.dataframe(
                df_display.style.apply(lambda x: ['background-color: rgba(0, 230, 118, 0.1)'] * len(x), axis=1), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info(f"⚪ 尚無 {day_key} 日衰退數據。")

    with t_down_5: render_down_table(5)
    with t_down_10: render_down_table(10)
    with t_down_20: render_down_table(20)
    with t_down_30: render_down_table(30)
    
    with t_down_history:
        st.markdown("##### 📅 歷史衰退單日快照")
        down_history_files = glob.glob(os.path.join(DATA_DIR, "*_Down_History.csv"))
        
        if down_history_files:
            history_dates = sorted([re.search(r'(202\d{5})', os.path.basename(f)).group(1) for f in down_history_files if re.search(r'(202\d{5})', f)], reverse=True)
            if history_dates:
                selected_date = st.selectbox("選擇歷史日期", history_dates, key="down_history_select")
                target_file = os.path.join(DATA_DIR, f"{selected_date}_Down_History.csv")
                
                try:
                    df_hist = pd.read_csv(target_file, encoding='utf-8-sig')
                    if '法人持股' in df_hist.columns and df_hist['法人持股'].dtype != object:
                         df_hist['法人持股'] = df_hist['法人持股'].apply(lambda x: f"{x:.2f}%")
                    if '累積衰退' in df_hist.columns and df_hist['累積衰退'].dtype != object:
                         df_hist['累積衰退'] = df_hist['累積衰退'].apply(lambda x: f"{x:.2f}%")
                         
                    st.dataframe(
                        df_hist.style.apply(lambda x: ['background-color: rgba(0, 230, 118, 0.1)'] * len(x), axis=1), 
                        use_container_width=True, 
                        hide_index=True
                    )
                except Exception as e:
                    st.error("讀取歷史資料失敗。")
        else:
            st.info("⚪ 目前尚未儲存任何歷史衰退紀錄。站長可以透過上方快照功能每天存檔！")

    # 全能池歷史軌跡 (負向專用)
    with t_down_all:
        if not down_final_df.empty:
             display_cols = ['股票代號', '股票名稱', '今日衰退上榜', '單日△'] + down_date_cols
             
             down_pool_df = down_final_df.copy()
             down_pool_df['單日△'] = down_pool_df['單日△'].apply(lambda x: f"{x:.2f}" if x <= 0 else f"+{x:.2f}")

             def highlight_down_row(row):
                 return ['background-color: rgba(0, 230, 118, 0.1)'] * len(row)

             st.dataframe(
                 down_pool_df[display_cols].style.apply(highlight_down_row, axis=1), 
                 use_container_width=True, 
                 hide_index=True
             )
        else:
             st.info("⚪ 目前尚未累積足夠的歷史衰退快照。請確認站長快照有成功封存負向資料，累積多日後即可觀察軌跡。")


    # ==========================================
    # 🕵️‍♂️ [深潛實驗室] 雙引擎籌碼歷史軌跡
    # ==========================================
    st.write("---")
    if not df_foreign.empty and not final_df.empty:
        with st.expander("🕵️‍♂️ [深潛實驗室] 籌碼 20 日歷史軌跡透視鏡 (內資推估 vs 外資)", expanded=False):
            st.caption("透過 20 日的持股比例變化，精準透視法人是在「短線洗盤」還是「長線階梯式建倉」。")
            
            foreign_dates = {c.replace('外資持股_', '') for c in df_foreign.columns if '外資持股_' in c}
            total_dates = {c.replace('持股%', '') for c in final_df.columns if '持股%' in c}
            common_dates = sorted(list(foreign_dates & total_dates), reverse=True)[:20]
            
            if common_dates:
                f_need_cols = ['股票代號'] + [f'外資持股_{d}' for d in common_dates]
                df_calc = pd.merge(final_df, df_foreign[f_need_cols], on='股票代號', how='inner')
                
                def clean_pct(val):
                    try: return float(str(val).replace('%', '').replace(',', ''))
                    except: return 0.0
                
                dom_display_cols, for_display_cols = [], []
                
                for d in common_dates:
                    tot_val, for_val = df_calc[f'{d}持股%'].apply(clean_pct), df_calc[f'外資持股_{d}'].apply(clean_pct)
                    dom_col, for_out_col = f'內資_{d[-4:]}', f'外資_{d[-4:]}'
                    
                    df_calc[f'{dom_col}_raw'] = (tot_val - for_val).clip(lower=0)
                    df_calc[dom_col] = df_calc[f'{dom_col}_raw'].apply(lambda x: f"{x:.2f}%")
                    dom_display_cols.append(dom_col)
                    
                    df_calc[f'{for_out_col}_raw'] = for_val
                    df_calc[for_out_col] = df_calc[f'{for_out_col}_raw'].apply(lambda x: f"{x:.2f}%")
                    for_display_cols.append(for_out_col)
                
                df_calc = df_calc[df_calc['今日上榜'].astype(str).str.strip() != ""]
                tab_dom, tab_for = st.tabs(["🕵️‍♂️ 內資 (投信+自營) 20日軌跡", "🌎 外資大腿 20日軌跡"])
                base_cols = ['股票代號', '股票名稱', '今日上榜', '△']
                
                with tab_dom:
                    st.markdown("##### 🔍 尋找「投信/自營商」連續鎖碼股")
                    st.caption("內資常專注於中小型爆發股，若連續多日比例上升，代表投信作帳行情啟動。")
                    latest_dom_col = f'內資_{common_dates[0][-4:]}_raw'
                    df_dom_sorted = df_calc.sort_values(by=latest_dom_col, ascending=False).head(40)
                    st.dataframe(df_dom_sorted[base_cols + dom_display_cols], use_container_width=True, hide_index=True)
                    
                with tab_for:
                    st.markdown("##### 🔍 尋找「外資大腿」長線階梯建倉股")
                    st.caption("外資資金龐大，若發現持股比例連續 1~2 週穩步增長，代表真正的長線資金進駐。")
                    latest_for_col = f'外資_{common_dates[0][-4:]}_raw'
                    df_for_sorted = df_calc.sort_values(by=latest_for_col, ascending=False).head(40)
                    st.dataframe(df_for_sorted[base_cols + for_display_cols], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ 找不到主表與外資表的共通日期，請確認資料是否已同步。")
