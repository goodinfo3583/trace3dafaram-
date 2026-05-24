import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import re


# ==========================================
# 1. 網頁基本設定 & 頂部蜂蜜幸運祝福
# ==========================================
st.set_page_config(page_title="台股籌碼五大核心矩陣儀表板", layout="wide")

st.markdown("""
<div style='text-align: center; background-color: #FFFDF0; padding: 20px; border-radius: 15px; border: 2px dashed #FFB700;'>
    <h1 style='color: #DDA400; margin-bottom: 5px;'>🐝 祝阿東順利畢業 - 每天都是美好的一天 🍯</h1>
    <p style='color: #665220; font-size: 16px; font-weight: bold;'>🌾 論文衝刺必勝 ｜ 香臘滿滿 ｜ 加速起漲雷達 ლ(∘◕‵ƹ′◕ლ)</p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("📊 系統全數領域展開：法人持股比 ｜ 短線法人買佔成交量 ｜ 法人買佔發行量比對 (本站進行數據分析僅供參考而非推薦個股與飆股另請愛惜荷包小心騙騙)")

DATA_DIR = "./Goodinfo_Rankings"

def extract_date_from_name(filepath):
    filename = os.path.basename(filepath)
    date_match = re.search(r'(\d+)', filename)
    return date_match.group(1) if date_match else "00000000"

# ==========================================
# 👑 頂級核心：【三大法人多空評分 + 3日短線飆速置頂爆發榜】
# ==========================================
st.markdown("## 🏆 頂級核心：解鎖中")
st.write("🔥 **戰術策略說明**：以長線為絕對基底，放寬偵測：今日數據對比前1天、前2天或前3天只要有實質增加（含突破未進榜斷層）即鎖定！")



# ==========================================
# 🔍 個股籌碼快搜 (全區塊聯動掃描版)
# ==========================================
st.write("---")
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.subheader("🔍 個股籌碼快搜 (全方位診斷)")

# 🛠️ 定義強韌的搜尋函式
def robust_search_engine(df, query):
    if df is None or df.empty:
        return pd.DataFrame()
        
    df = df.loc[:, ~df.columns.duplicated()].copy()
    query = str(query).strip()
    mask = pd.Series(False, index=df.index)
    
    if '股票代號' in df.columns:
        df['股票代號'] = df['股票代號'].astype(str).str.strip()
        mask = mask | (df['股票代號'] == query)
        
    if '股票名稱' in df.columns:
        df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
        mask = mask | df['股票名稱'].str.contains(query, na=False, case=False)
        
    return df[mask]

# 🎯 建立通用掃描與顯示工具
def scan_and_display(title, session_key, query):
    df = st.session_state.get(session_key, pd.DataFrame())
    res = robust_search_engine(df, query)
    
    if not res.empty:
        st.write(f"**{title}**")
        st.dataframe(res, use_container_width=True)
    else:
        st.info(f"⚪ {title}：無資料 (未進榜)")

# 🎯 搜尋輸入框
search_query = st.text_input("請輸入想觀測的股票代號或名稱 (例如: 3231 或 緯創)：", key="global_search_final")

if search_query:
    st.write(f"### 🎯 綜合診斷標的：{search_query}")
    
    # ==========================================
    # 👑 區塊 1：中長線三大法人持股
    # ==========================================
    st.write("#### 👑 區塊 1：中長線三大法人持股")
    
    if 'my_final_df' in st.session_state:
        q_blk1 = robust_search_engine(st.session_state['my_final_df'], search_query)
        
        if not q_blk1.empty:
            st.dataframe(q_blk1.drop(columns=["秘密3日斜率"], errors='ignore'), use_container_width=True)
            
            # --- 任務 2：擴充為 30 日 ---
            chart_cols = [c for c in q_blk1.columns if "持股%" in c]
            if chart_cols:
                target_cols = chart_cols[:30] # 抓取最近 30 天
                
                # --- 任務 1：解決歸零斷崖連線問題 ---
                # 抓取數值，將 0 強制替換為 NaN，然後 dropna。
                # 這樣 Streamlit 折線圖就會自動跳過未進榜的日期，將已知數據「平滑連線」，非常真實。
                raw_vals = pd.to_numeric(q_blk1.iloc[0][target_cols].values, errors='coerce')
                t_ser = pd.Series(
                    raw_vals, 
                    index=[c.split(' ')[0] for c in target_cols]
                ).replace(0, np.nan).dropna().iloc[::-1]
                
                if not t_ser.empty:
                    st.write(f"📈 **持股 {len(t_ser)}日波段真實軌跡 ({q_blk1.iloc[0].get('股票名稱', '標的')})**")
                    st.line_chart(t_ser, height=240)
                    
                    # --- 任務 3：新增 2, 3, 5, 20 日斜率面版 ---
                    st.markdown("##### 🚀 籌碼斜率 (與最新持股相比淨增減)")
                    
                    def get_slope(n_days):
                        # 確保天數足夠
                        if len(target_cols) >= n_days:
                            v_new = pd.to_numeric(q_blk1.iloc[0][target_cols[0]], errors='coerce')
                            v_old = pd.to_numeric(q_blk1.iloc[0][target_cols[n_days-1]], errors='coerce')
                            
                            # 確保數據有效且不為0 (未進榜)
                            if pd.notna(v_new) and pd.notna(v_old) and v_old != 0 and v_new != 0:
                                diff = round(v_new - v_old, 2)
                                return f"{diff:+.2f} %"
                        return "無對應資料"

                    # 使用 st.columns 排版，做出漂亮的儀表板效果
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("2日斜率", get_slope(2))
                    col2.metric("3日斜率", get_slope(3))
                    col3.metric("5日斜率", get_slope(5))
                    col4.metric("20日斜率", get_slope(20))
                else:
                    st.info("⚪ 該標的有效數據過少，無法繪製波段圖表。")
        else:
            st.info("⚪ 無資料 (該標的未進入中長線榜單)")
    else:
        st.error("⚠️ 尚未載入區塊 1 資料。請確認上方區塊 1 已執行。")
    # ==========================================
    # 📊 區塊 2：(替換為您的實際名稱)
    # ==========================================
    st.write("---")
    st.write("#### 📊 區塊 2：動能與外資診斷 (暫定)")
    
    c1, c2 = st.columns(2)
    with c1: scan_and_display("🔹 區塊 2-1", 'df_blk2_1', search_query)
    with c2: scan_and_display("🔹 區塊 2-2", 'df_blk2_2', search_query)
    
    c3, c4 = st.columns(2)
    with c3: scan_and_display("🔹 區塊 2-3", 'df_blk2_3', search_query)
    with c4: scan_and_display("🔹 區塊 2-4", 'df_blk2_4', search_query)

    # ==========================================
    # 📊 區塊 3：(替換為您的實際名稱)
    # ==========================================
    st.write("---")
    st.write("#### 📊 區塊 3：特定籌碼或大戶診斷 (暫定)")
    scan_and_display("🔹 區塊 3 綜合列表", 'df_blk3_main', search_query)

    # ==========================================
    # 📊 區塊 4：籌碼變動排名診斷 (融資/借券/融券) - 無分頁版
    # ==========================================
    st.write("---")
    st.write("#### 📊 區塊 4：籌碼變動排名診斷")
    
    st.markdown("##### 📉 融資減少")
    c1, c2 = st.columns(2)
    with c1: scan_and_display("【幅度】", 'df_margin_pct', search_query)
    with c2: scan_and_display("【張數】", 'df_margin_vol', search_query)
        
    st.markdown("##### 📉 借券賣出減少")
    c3, c4 = st.columns(2)
    with c3: scan_and_display("【幅度】", 'df_short_pct', search_query)
    with c4: scan_and_display("【張數】", 'df_short_vol', search_query)
        
    st.markdown("##### 📈 融券增加")
    c5, c6 = st.columns(2)
    with c5: scan_and_display("【幅度】", 'df_margin_plus_pct', search_query)
    with c6: scan_and_display("【張數】", 'df_margin_plus_vol', search_query)
        
 
# ==========================================
# 🧭 側邊欄導航 (無感互動+視覺特效版)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 大盤總體經濟指標")

c_btn1, c_btn2 = st.sidebar.columns(2)
with c_btn1:
    st.link_button("📈 恐懼貪婪", "https://www.wantgoo.com/global/macroeconomics/fearandgreed", use_container_width=True)
with c_btn2:
    st.link_button("⚠️ VIX 指數", "https://www.wantgoo.com/global/vix", use_container_width=True)


# 1. 戰情室快速導航
st.sidebar.markdown("---")
st.sidebar.header("📍 戰情室快速導航")
st.sidebar.markdown("[🔍 個股籌碼快搜 (診斷區)](#section-search)")
st.sidebar.markdown("[👑 區塊1：法人持股比追蹤](#section-1)")
st.sidebar.markdown("[🎯 區塊2-1：外資 5 日淨買佔成交量](#section-2-1)")
st.sidebar.markdown("[🎯 區塊2-2：投信 5 日淨買佔成交量](#section-2-2)")
st.sidebar.markdown("[🎯 區塊2-3：外資 5 日淨買佔發行量](#section-2-3)")
st.sidebar.markdown("[🎯 區塊2-4：投信 5 日淨超佔發行量](#section-2-4)")
st.sidebar.markdown("[📅 區塊3：法人連續買超](#section-3)")
st.sidebar.markdown("[🔄 區塊4-1：融資減少動向](#section-4-1)")
st.sidebar.markdown("[🔄 區塊4-2：借券賣出減少動向](#section-4-2)")
st.sidebar.markdown("[🔄 區塊4-3：融券增加動向](#section-4-3)")
# ==========================================
# 🏠 核心五大區塊
# ==========================================

# ==========================================
# 🏠 區塊1：中長線 三大法人 持股比例 追蹤 (字串精確比對+柔和護眼版)
# ==========================================
st.write("---")
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)
st.header("👑 區塊1：中長線 三大法人 持股比例 追蹤")

import re
import os
import glob
import pandas as pd
from collections import defaultdict

# 1. 解析引擎 (嚴格依賴分隔線)
def parse_special_txt(file_path, date_label):
    parsed_data = []
    target_col = f"{date_label}持股%"
    current_section = None
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line_str = line.strip()
                
                # 🛑 【絕對斷路器】：只要遇到分隔線，立刻清空狀態
                if line_str.startswith("---") or line_str.startswith("==="):
                    current_section = None
                    continue
                
                # 💡 【區塊開關】：讀到對應標題才開啟
                if "三大法人持股變化排名" in line_str or ("排名" in line_str and "日)" in line_str):
                    # 必須先比對 120日 再比對 20日
                    if "120日" in line_str: current_section = "120日"
                    elif "20日" in line_str: current_section = "20日"
                    elif "5日" in line_str: current_section = "5日"
                    elif "60日" in line_str: current_section = "60日"
                    continue
                
                # 抓取資料：必須在開啟狀態，且該行是資料(數字開頭)才抓
                parts = line_str.split('\t')
                if current_section and len(parts) >= 5 and parts[0].isdigit():
                    try: holding_pct = float(parts[-2])
                    except ValueError: continue
                    
                    stock_str = parts[1].strip()  
                    m = re.match(r'^(\d+)(.*)', stock_str)
                    stock_id = m.group(1) if m else stock_str
                    stock_name = m.group(2).strip() if m else stock_str
                    
                    parsed_data.append({
                        '股票代號': stock_id,
                        '股票名稱': stock_name,
                        target_col: holding_pct,
                        '上榜區塊': current_section
                    })
    except Exception:
        pass
    return pd.DataFrame(parsed_data)

# 聚合相同標的的不同榜單標籤
def agg_sections_func(x):
    valid_x = set([s for s in x if pd.notna(s) and s != ""])
    order = ['5日', '20日', '60日', '120日']
    return ",".join([s for s in order if s in valid_x])

# ==========================================
# 🔄 多日歷史資料合併與邏輯運算
# ==========================================
txt_pattern = os.path.join(DATA_DIR, "*持股排名變化*.txt")
all_txt_files = glob.glob(txt_pattern)

# 依日期分群
date_files = defaultdict(list)
for f in all_txt_files:
    date_label = os.path.basename(f)[:8]
    if date_label.isdigit():
        date_files[date_label].append(f)

sorted_dates = sorted(date_files.keys(), reverse=True)

if sorted_dates:
    final_df = None
    
    for i, date_label in enumerate(sorted_dates[:30]):
        is_latest = (i == 0)
        day_dfs = []
        
        for file_path in date_files[date_label]:
            df_part = parse_special_txt(file_path, date_label)
            if not df_part.empty:
                day_dfs.append(df_part)
                
        if not day_dfs: continue
            
        df_day_raw = pd.concat(day_dfs, ignore_index=True)
        target_col = f"{date_label}持股%"
        
        if is_latest:
            df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg({
                target_col: 'max',  
                '上榜區塊': agg_sections_func
            }).reset_index()
        else:
            df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg({
                target_col: 'max'
            }).reset_index()
            
        if final_df is None: final_df = df_day
        else: final_df = pd.merge(final_df, df_day, on=['股票代號', '股票名稱'], how='outer')
            
    if final_df is not None and not final_df.empty:
        date_cols = sorted([c for c in final_df.columns if '持股%' in c], reverse=True)
        for c in date_cols:
            final_df[c] = pd.to_numeric(final_df[c], errors='coerce').fillna(0)
            
        # 🔥 【終極修正】：改成絕對陣列比對，避免 "20日" 吃到 "120日" 的豆腐
        def generate_tags(sections):
            if pd.isna(sections) or not sections: return ""
            sec_list = str(sections).split(',')
            tags = []
            if '5日' in sec_list: tags.append('🔴5日')
            if '20日' in sec_list: tags.append('🟡20日')
            if '60日' in sec_list: tags.append('🟢60日')
            if '120日' in sec_list: tags.append('🔵120日')
            return " ".join(tags)
            
        if '上榜區塊' not in final_df.columns:
            final_df['上榜區塊'] = ""
            
        final_df['今日上榜'] = final_df['上榜區塊'].apply(generate_tags)
        final_df['上榜數量'] = final_df['今日上榜'].apply(lambda x: str(x).count('日'))
            
        def evaluate_trend(row):
            if len(date_cols) < 2: return "⚪ 資料不足"
            v0, v1 = row[date_cols[0]], row[date_cols[1]]
            diff1 = v0 - v1  
            if diff1 > 0:
                if len(date_cols) >= 3:
                    v2 = row[date_cols[2]]
                    if v1 != 0 and v2 != 0:
                        diff2 = v1 - v2
                        if diff2 > 0 and diff1 < diff2: return "⚠️ 趨緩"
                return "📈 上升"
            elif diff1 < 0: return "📉 下降"
            else: return "🔄 持平"
                
        final_df['最新動態'] = final_df.apply(evaluate_trend, axis=1)
        
        if date_cols:
            final_df = final_df.sort_values(by=['上榜數量', date_cols[0]], ascending=[False, False])
            
        color_ref = final_df.set_index('股票代號')['上榜數量'].to_dict()
        cols = ['股票代號', '股票名稱', '今日上榜', '最新動態'] + date_cols
        final_df = final_df[cols]
        
        # ==========================================
        # 🔧 UI 顯示與底色渲染
        # ==========================================
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="blk1_etf_sync")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="blk1_bond_sync")
        
        is_bond = final_df['股票代號'].str.endswith('B')
        is_etf = (final_df['股票代號'].str.len() >= 5) & (~is_bond)
        is_stock = final_df['股票代號'].str.len() == 4
        
        mask = is_stock
        if show_etf: mask |= is_etf
        if show_bond: mask |= is_bond
            
        filtered_df = final_df[mask].copy()
        
        for c in date_cols:
            filtered_df[c] = filtered_df[c].apply(lambda x: f"{x:.2f}" if x != 0 else "-")
        filtered_df.index = range(1, len(filtered_df) + 1)
        
        # 🎨 護眼淺色系底色
        def highlight_row(row):
            cnt = color_ref.get(row['股票代號'], 0)
            if cnt == 4: bg = 'background-color: rgba(255, 0, 0, 0.15)'     
            elif cnt == 3: bg = 'background-color: rgba(255, 165, 0, 0.15)'    
            elif cnt == 2: bg = 'background-color: rgba(0, 128, 0, 0.15)'    
            elif cnt == 1: bg = 'background-color: rgba(0, 127, 255, 0.15)'    
            else: bg = ''                                                   
            return [bg] * len(row)

        styled_df = filtered_df.style.apply(highlight_row, axis=1)
        
        st.info("💡 **多榜單共振說明：** 5/20/60/120日，代表法人持股變化數據分析後於前段班，多榜單籌碼集中度極高。")
        st.success(f"📊 已成功串聯最近 {len(date_cols)} 個交易日的持股數據 (排序優先級：今日上榜數量 > 今日持股%)：")
        st.session_state['my_final_df'] = final_df
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("⚠️ 讀取到的檔案皆無效或無資料，請檢查 TXT 內容。")
else:
    st.write("⚠️ 目前暫無持股比例追蹤數據。")


# ==========================================
# 🎯 區塊2-1：外資 5 日買超 佔成交量比 追蹤 (穩定精確版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-1'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-1：外資 5 日買超 佔成交量比 追蹤")

csv_pattern = os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")
all_csv_files = glob.glob(csv_pattern)

if not all_csv_files:
    st.warning("⚠️ 找不到任何包含『外資買超佔成交比』的 CSV 檔案。")
else:
    all_csv_files.sort(reverse=True)
    target_files = all_csv_files[:14]
    base_df = None
    latest_day_today_data = {}

    for idx, f in enumerate(target_files):
        try:
            # 強制讀取並清洗所有欄位名稱 (移除空格、換行、BOM)
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 確保代號/名稱存在
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '代號', name_col: '名稱'})
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 自動偵測欄位 (包含關鍵字即可)
            col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
            
            # 存當日數據
            if idx == 0 and col_today:
                latest_day_today_data = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            # 合併歷史
            if col_5d:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}買佔比%"})
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
        except Exception:
            continue

    if base_df is not None:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 強健排序：依據最新日期數值排序
        latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}買佔比%"
        if latest_col_name in csv_display.columns:
            csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
            
        # 增加當日買佔比欄位處理
        csv_display['當日買佔比%'] = csv_display['股票代號'].map(latest_day_today_data).fillna(0)
            
        # 動態判定邏輯
        def evaluate_continuity(row):
            today = latest_day_today_data.get(row['股票代號'], 0)
            base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
            if pd.isna(today): return "⚪ 觀望"
            if today > 0: return "🔥 強延續" if today > base else "⚠️ 趨緩"
            elif today < 0: return "🚨 劇烈倒貨" if abs(today) > abs(base) else "📉 調節洗盤"
            return "🔄 持平"

        csv_display['今日短動態'] = csv_display.apply(evaluate_continuity, axis=1)
        
        # 動態說明對照表
        st.info("""
        💡 **外資動態說明：** 🔥 強延續 (買盤加速) | ⚠️ 趨緩 (買盤力道減弱) | 🔄 持平 | 📉 調節洗盤 (微幅調節) | 🚨 劇烈倒貨 (強烈賣出)
        """)
        
        # UI 與過濾
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="fo_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="fo_bond_v9")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 調整欄位順序
        cols = ["股票代號", "股票名稱", "今日短動態", "當日買佔比%"] + [c for c in csv_display.columns if "買佔比%" in c and c != "當日買佔比%"]
        csv_display = csv_display[cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
    else:
        st.error("❌ 無法讀取外資買超數據，請檢查 CSV 欄位名稱是否包含『5日』與『成交』關鍵字。")

# ==========================================
# 🎯 區塊2-2：投信 5 日買超 佔成交量比 追蹤 (穩定修復版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-2'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-2：投信 5 日買超 佔成交量比 追蹤")

csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if not all_files_sitc:
    st.warning("⚠️ 找不到任何包含『投信買超佔成交比』的 CSV 檔案。")
else:
    all_files_sitc.sort(reverse=True)
    target_files = all_files_sitc[:14]
    base_df = None
    latest_day_today_data_sitc = {}

    for idx, f in enumerate(target_files):
        try:
            # 1. 強制讀取並清洗欄位 (移除空格、換行、BOM)
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 2. 確保代號/名稱欄位存在並清理
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '代號', name_col: '名稱'})
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 3. 自動偵測關鍵欄位 (只要包含關鍵字即可)
            col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
            
            if idx == 0 and col_today:
                latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}買佔比%"})
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
        except Exception:
            continue

    if base_df is not None:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 4. 強健排序
        latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}買佔比%"
        if latest_col_name in csv_display.columns:
            csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
            
        # 5. 增加當日數據並判定動態
        csv_display['當日買佔比%'] = csv_display['股票代號'].map(latest_day_today_data_sitc).fillna(0)
        
        def evaluate_continuity(row):
            today = latest_day_today_data_sitc.get(row['股票代號'], 0)
            base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
            if pd.isna(today): return "⚪ 觀望"
            if today > 0: return "🔥 強延續" if today > base else "⚠️ 趨緩"
            elif today < 0: return "🚨 劇烈倒貨" if abs(today) > abs(base) else "📉 調節洗盤"
            return "🔄 持平"

        csv_display['今日短動態'] = csv_display.apply(evaluate_continuity, axis=1)
        
        # 動態說明
        st.info("""
        💡 **投信動態說明：** 🔥 強延續 (法人認養中) | ⚠️ 趨緩 (買盤力道減弱) | 🔄 持平 | 📉 調節洗盤 (微幅調節) | 🚨 劇烈倒貨 (短線獲利了結)
        """)
        
        # 篩選邏輯
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_v9")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 欄位順序調整
        cols = ["股票代號", "股票名稱", "今日短動態", "當日買佔比%"] + [c for c in csv_display.columns if "買佔比%" in c and c != "當日買佔比%"]
        csv_display = csv_display[cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
    else:
        st.error("❌ 無法讀取投信買超數據，請確認 CSV 檔案內含有『5日』與『成交』欄位。")

# ==========================================
# 🎯 區塊2-3：外資 5 日買超佔發行張數 追蹤 (穩定精確版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-3'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-3：外資 5 日買超佔發行張數 追蹤")
csv_pattern_fo = os.path.join(DATA_DIR, "*外資買超佔發行張數*.csv")
all_files_fo = glob.glob(csv_pattern_fo)

if not all_files_fo:
    st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
else:
    sorted_files = sorted(all_files_fo, key=extract_date_from_name, reverse=True)[:10]
    base_df = None
    date_labels = []
    latest_day_today_data_fo = {}

    for idx, f in enumerate(sorted_files):
        try:
            # 1. 強制讀取並清洗 BOM 頭與所有空格
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 2. 確保代號名稱欄位存在並清理
            if '代號' not in df.columns or '名稱' not in df.columns:
                continue
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 3. 對應 CSV 內的標準名稱 (移除空格後的名稱)
            col_today = '當日買賣超佔發行張數'
            col_5d = '5日買賣超佔發行張數'
            
            if idx == 0 and col_today in df.columns:
                latest_day_today_data_fo = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d in df.columns:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}外資買發張數%"})
                
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            
            date_labels.append(d_label)
        except Exception:
            continue

    if base_df is not None and len(date_labels) > 0:
        # 清理資料與名稱對應
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 4. 強健排序：改用最新日期數值排序，避開 _base_order 的 NaN 風險
        latest_5d_col = f"{date_labels[0]}外資買發張數%"
        if latest_5d_col in csv_display.columns:
            csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
        
        # 動態判定邏輯
        def judge_today_alert_fo(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, 0)
            val_today = latest_day_today_data_fo.get(stock_id, 0)
            
            if val_5d == 0 or val_5d == "未進榜":
                return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
            
            if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
            elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
            return "🔄 今日量縮持平"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_fo, axis=1)
        
        # UI 與過濾邏輯
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="foreign_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="foreign_bond_final_v3")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 表格顯示
        history_cols = [c for c in csv_display.columns if "外資買發張數%" in c]
        csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯 {len(date_labels)} 個交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
    else:
        st.error("❌ 無法讀取外資數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")


# ==========================================
# 🎯 區塊2-4：投信 5 日買超佔發行張數 追蹤 (最終穩定版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-4'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-4：投信 5 日買超佔發行張數 追蹤")
csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if not all_files_sitc:
    st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
else:
    sorted_files = sorted(all_files_sitc, key=extract_date_from_name, reverse=True)[:10]
    base_df = None
    date_labels = []
    latest_day_today_data_sitc = {}

    for idx, f in enumerate(sorted_files):
        try:
            # 1. 強制以 utf-8-sig 讀取，並移除標題列的 BOM 與所有空格
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 2. 確保代號名稱欄位存在並清理
            if '代號' not in df.columns or '名稱' not in df.columns:
                continue
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 3. 對應 CSV 內的標準名稱 (移除空格後的名稱)
            col_today = '當日買賣超佔發行張數'
            col_5d = '5日買賣超佔發行張數'
            
            if idx == 0 and col_today in df.columns:
                latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d in df.columns:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}投信買發張數%"})
                
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            
            date_labels.append(d_label)
        except Exception:
            continue

    if base_df is not None and len(date_labels) > 0:
        # 進行表格清理
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 4. 強健排序法：依據最新一日的數值排序，而非使用容易出錯的 _base_order
        latest_5d_col = f"{date_labels[0]}投信買發張數%"
        if latest_5d_col in csv_display.columns:
            csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
        
        # 動態判定邏輯
        def judge_today_alert_sitc(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, 0)
            val_today = latest_day_today_data_sitc.get(stock_id, 0)
            
            if val_5d == 0 or val_5d == "未進榜":
                return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
            
            if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
            elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
            return "🔄 今日量縮持平"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_sitc, axis=1)
        
        # UI 過濾
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_final_v3")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 顯示
        history_cols = [c for c in csv_display.columns if "投信買發張數%" in c]
        csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯 {len(date_labels)} 個交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
    else:
        st.error("❌ 無法讀取投信數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")


# ==========================================
# 📅 區塊三：外資與投信連續買超 (日/週全景戰情室)
# ==========================================
st.write("---")
st.markdown("<div id='section-3'></div>", unsafe_allow_html=True)
st.header("📅 區塊3：連續買超")

st.info("""
💡 **狀態動態評估依據：**
* 連買 10以上天/週 🔥 波段認養
* 連買 5 ~ 9 天/週 ⚡ 買盤點火
* 連買 1 ~ 4 天/週 🆕 試單觀察
""")

def read_live_ln_report(file_keyword, strict_type, exact_field_name, prefix_keyword, col_label):
    if strict_type == "日":
        search_pattern1 = os.path.join(DATA_DIR, f"*{file_keyword}*(日)*.csv")
        search_pattern2 = os.path.join(DATA_DIR, f"*{file_keyword}*日*.csv")
        target_files = glob.glob(search_pattern1) + glob.glob(search_pattern2)
        target_files = [f for f in target_files if "週" not in os.path.basename(f) and "周" not in os.path.basename(f) and "wk" not in os.path.basename(f).lower()]
    else:
        search_pattern1 = os.path.join(DATA_DIR, f"*{file_keyword}*(週)*.csv")
        search_pattern2 = os.path.join(DATA_DIR, f"*{file_keyword}*週*.csv")
        target_files = glob.glob(search_pattern1) + glob.glob(search_pattern2)
        
    target_files = list(set(target_files))
    if not target_files: return pd.DataFrame(), None
        
    latest_file = sorted(target_files, key=extract_date_from_name, reverse=True)[0]
    date_str = extract_date_from_name(latest_file) 
    
    try:
        # 強制指定 utf-8-sig 以解決中文亂碼，並清除欄位中的隱形字元
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        df.columns = df.columns.astype(str).str.replace('\n', '').str.replace(' ', '').str.replace('\ufeff', '').str.strip()
        
        # 動態查找欄位
        col_id = next((c for c in df.columns if '代號' in c), df.columns[0])
        col_name = next((c for c in df.columns if '名稱' in c), df.columns[1])
        
        target_key = exact_field_name.replace(' ', '')
        if target_key in df.columns:
            target_data_col = target_key
        else:
            matched_cols = [c for c in df.columns if '買賣' in c and strict_type in c]
            target_data_col = matched_cols[0] if matched_cols else df.columns[2]
            
        df[target_data_col] = pd.to_numeric(df[target_data_col], errors='coerce').fillna(0)
        df_sorted = df[df[target_data_col] > 0].sort_values(by=target_data_col, ascending=False)
        
        if df_sorted.empty: return pd.DataFrame(), date_str
            
        output_df = pd.DataFrame()
        output_df["股票代號"] = df_sorted[col_id].astype(str).str.strip()
        output_df["股票名稱"] = df_sorted[col_name].astype(str).str.strip()
        
        def get_status_tag(val):
            if val >= 10: return "🔥 波段認養"
            elif val >= 5: return "⚡ 買盤點火"
            else: return "🆕 試單觀察"
                
        output_df["狀態動態"] = df_sorted[target_data_col].apply(get_status_tag)
        output_df[col_label] = df_sorted[target_data_col].astype(int)
        
        real_pct_trade = [c for c in df_sorted.columns if prefix_keyword in c and "佔成交" in c]
        real_pct_issue = [c for c in df_sorted.columns if prefix_keyword in c and "佔發行量" in c]
        
        if real_pct_trade: output_df["佔成交(%)"] = pd.to_numeric(df_sorted[real_pct_trade[0]], errors='coerce').fillna(0.0)
        else: output_df["佔成交(%)"] = 0.0
            
        if real_pct_issue: output_df["佔發行量(%)"] = pd.to_numeric(df_sorted[real_pct_issue[0]], errors='coerce').fillna(0.0)
        else: output_df["佔發行量(%)"] = 0.0
            
        output_df.index = range(1, len(output_df) + 1)
        return output_df, date_str
    except Exception as e:
        return pd.DataFrame(), f"解讀失敗: {str(e)}"

# 執行排程與渲染 (與您原先邏輯相同)
live_fo_day, date_fo_day = read_live_ln_report("外資連續買超", "日", "外資連續買賣日數", "外資", "最新連買天數")
# ... (下方保持原本排程呼叫) ...

# ========================================================
# 🚀 執行排程
# ========================================================
live_fo_day, date_fo_day = read_live_ln_report("外資連續買超", "日", "外資連續買賣日數", "外資", "最新連買天數")
if live_fo_day.empty and date_fo_day is None: 
    live_fo_day, date_fo_day = read_live_ln_report("外資連買", "日", "外資連續買賣日數", "外資", "最新連買天數")

live_it_day, date_it_day = read_live_ln_report("投信連續買超", "日", "投信連續買賣日數", "投信", "最新連買天數")
if live_it_day.empty and date_it_day is None:
    live_it_day, date_it_day = read_live_ln_report("投信連買", "日", "投信連續買賣日數", "投信", "最新連買天數")
if live_it_day.empty:
    live_it_day, date_it_day = read_live_ln_report("外資連續買超", "日", "投信連續買賣日數", "投信", "最新連買天數")
    if live_it_day.empty:
        live_it_day, date_it_day = read_live_ln_report("外資連買", "日", "投信連續買賣日數", "投信", "最新連買天數")

live_fo_wk, date_fo_wk = read_live_ln_report("外資連續買超", "週", "外資連續買賣週數", "外資", "最新連買週數")
if live_fo_wk.empty and date_fo_wk is None:
    live_fo_wk, date_fo_wk = read_live_ln_report("外資連買", "週", "外資連續買賣週數", "外資", "最新連買週數")

live_it_wk, date_it_wk = read_live_ln_report("投信連續買超", "週", "投信連續買賣週數", "投信", "最新連買週數")
if live_it_wk.empty and date_it_wk is None:
    live_it_wk, date_it_wk = read_live_ln_report("投信連買", "週", "投信連續買賣週數", "投信", "最新連買週數")
if live_it_wk.empty:
    live_it_wk, date_it_wk = read_live_ln_report("外資連續買超", "週", "投信連續買賣週數", "投信", "最新連買週數")
    if live_it_wk.empty:
        live_it_wk, date_it_wk = read_live_ln_report("外資連買", "週", "投信連續買賣週數", "投信", "最新連買週數")

# ========================================================
# 🖼️ 視覺介面渲染 (左外資、右投信)
# ========================================================
st.subheader("⚡ 最新單日連續買超")
c_day1, c_day2 = st.columns(2)

with c_day1:
    st.markdown(f"🌐 **外資最新日連買** *(最新檔案日期: {date_fo_day if date_fo_day else '無資料'})*")
    if not live_fo_day.empty:
        st.dataframe(live_fo_day, use_container_width=True)
    else:
        st.write("無資料")

with c_day2:
    st.markdown(f"🏦 **投信最新日連買** *(最新檔案日期: {date_it_day if date_it_day else '無資料'})*")
    if not live_it_day.empty:
        st.dataframe(live_it_day, use_container_width=True)
    else:
        st.write("無資料")

st.write(" ") 

st.subheader("📅 最新單週連續波段買超")
c_wk1, c_wk2 = st.columns(2)

with c_wk1:
    st.markdown(f"🌐 **外資最新週連買** *(最新檔案日期: {date_fo_wk if date_fo_wk else '無資料'})*")
    if not live_fo_wk.empty:
        st.dataframe(live_fo_wk, use_container_width=True)
    else:
        st.write("無資料")

with c_wk2:
    st.markdown(f"🏦 **投信最新週連買** *(最新檔案日期: {date_it_wk if date_it_wk else '無資料'})*")
    if not live_it_wk.empty:
        st.dataframe(live_it_wk, use_container_width=True)
    else:
        st.write("無資料")

# ==========================================
# 🛠️ 必備函數：強硬讀取法 (解決 Big5/UTF-8 亂碼)
# ==========================================
def robust_read_csv(file_path):
    # 強制嘗試台灣常見編碼 (cp950 為 Big5)
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            # 簡單檢查：如果出現了亂碼常見字元，就換下一個編碼
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    # 真的都不行就強制讀取並忽略錯誤
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# ==========================================
# 🛠️ 必備函數：強硬讀取法
# ==========================================
def robust_read_csv(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# ==========================================
# 🛠️ 必備函數：強硬讀取法
# ==========================================
def robust_read_csv(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')
# ==========券資比資料請一起搬遷============
# ==========================================
# 📅 區塊 4-1：融資減少動向 (5日累計)
# ==========================================
st.write("---")
st.markdown("<div id='section-4-1'></div>", unsafe_allow_html=True)
st.header("📅 區塊 4-1：融資減少動向")

# 🛠️ 新增：自訂標的顯示過濾 UI (已刪除紫色勾勾符號)
st.write("🔧 **自訂標的顯示過濾：**")
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1:
    show_etf = st.checkbox("顯示 ETF", value=True, key="margin_show_etf")
with f_col2:
    show_bond = st.checkbox("顯示債券/債券ETF", value=True, key="margin_show_bond")
st.write("") 

# --- 讀取函數 ---
def get_specific_margin_data(keyword):
    found_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        if '.git' in root or 'venv' in root: continue
        for file in files:
            if file.lower().endswith(".csv") and keyword in file:
                found_files.append(os.path.join(root, file))
    
    if not found_files:
        return pd.DataFrame(), f"找不到包含『{keyword}』的檔案"
    
    latest_file = sorted(found_files, key=lambda x: os.path.basename(x), reverse=True)[0]
    file_name = os.path.basename(latest_file)
    
    try:
        df = robust_read_csv(latest_file)
        if df.empty:
            return pd.DataFrame(), f"讀取成功但內容為空: {file_name}"
        
        df.columns = df.columns.astype(str).str.replace('\ufeff', '').str.strip()
        
        for col in df.columns:
            if "幅度" in col or "張數" in col or "%" in col or "％" in col:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.replace('%', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df, file_name
    except Exception as e:
        return pd.DataFrame(), f"讀取崩潰 ({file_name}): {str(e)}"

# --- 欄位清理與過濾函數 ---
def process_margin_df(df, type_name):
    if df.empty: return df
    df = df.copy()
    
    # 🔥 精準且無情的刪除「更新日期」欄位
    # 只要欄位名稱包含「更新」和「日期」這兩個關鍵字，就直接抹除
    cols_to_drop = [c for c in df.columns if "更新" in str(c) and "日期" in str(c)]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        
    # 🔥 模糊關鍵字定位截斷位置 (確保不會因為 CSV 內的空格導致找不到欄位)
    target_idx = -1
    if type_name == "幅度":
        for i, col in enumerate(df.columns):
            # 只要包含「3個月」和「%」就視為截斷點
            if "3個月" in str(col) and ("%" in str(col) or "％" in str(col)):
                target_idx = i
                break
    else: # 張數
        for i, col in enumerate(df.columns):
            # 只要包含「3個月」和「張數」就視為截斷點
            if "3個月" in str(col) and "張數" in str(col):
                target_idx = i
                break
                
    if target_idx != -1:
        df = df.iloc[:, :target_idx+1]
        
    # --- 執行 ETF 與 債券過濾邏輯 ---
    col_name = next((c for c in df.columns if '名稱' in c), None)
    col_id = next((c for c in df.columns if '代號' in c), None)
    
    if col_name and col_id:
        df[col_id] = df[col_id].astype(str).str.strip()
        df[col_name] = df[col_name].astype(str).str.strip()
        
        mask_bond = df[col_name].str.contains('債', na=False) | df[col_id].str.endswith('B', na=False)
        mask_etf = df[col_id].str.startswith('00', na=False)
        
        if not show_bond:
            df = df[~mask_bond]
        if not show_etf:
            df = df[~(mask_etf & ~mask_bond)] 

    # --- 重置 Index 並讓它從 1 開始 ---
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    
    return df

# ==========================================
# 📊 畫面佈局顯示
# ==========================================
c1, c2 = st.columns(2)

with c1:
    st.subheader("📉 融資減少比例排名")
    df_pct, msg_pct = get_specific_margin_data("融資減少幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度")
    
    if not df_pct_clean.empty:
        st.info(f"💡 最新來源: {msg_pct}")
        st.dataframe(df_pct_clean, use_container_width=True)
    else:
        st.warning(f"⚠️ {msg_pct} 或 過濾後無相符資料")

with c2:
    st.subheader("📉 融資減少張數排名")
    df_vol, msg_vol = get_specific_margin_data("融資減少張數")
    df_vol_clean = process_margin_df(df_vol, "張數")
    
    if not df_vol_clean.empty:
        st.info(f"💡 最新來源: {msg_vol}")
        st.dataframe(df_vol_clean, use_container_width=True)
    else:
        st.warning(f"⚠️ {msg_vol} 或 過濾後無相符資料")
        # 存入 4-1
        st.session_state['df_margin_pct'] = df_pct_clean
        st.session_state['df_margin_vol'] = df_vol_clean
# ==========================================
# 📅 區塊 4-2：借券賣出減少動向 (5日累計)
# ==========================================
st.write("---")
st.markdown("<div id='section-4-2'></div>", unsafe_allow_html=True)
st.header("📅 區塊 4-2：借券賣出減少動向")

# 🛠️ 標的顯示過濾 UI
st.write("🔧 **自訂標的顯示過濾：**")
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1:
    show_etf_42 = st.checkbox("顯示 ETF", value=True, key="stock_show_etf_42")
with f_col2:
    show_bond_42 = st.checkbox("顯示債券/債券ETF", value=True, key="stock_show_bond_42")
st.write("") 

# --- 畫面佈局顯示 (直接復用 get_specific_margin_data 與 process_margin_df) ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📉 借券賣出減少比例排名")
    # 🔥 關鍵修改：關鍵字改為「借券賣出減少幅度」
    df_pct, msg_pct = get_specific_margin_data("借券賣出減少幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度") # 沿用相同的清理邏輯
    
    if not df_pct_clean.empty:
        st.info(f"💡 最新來源: {msg_pct}")
        st.dataframe(df_pct_clean, use_container_width=True)
    else:
        st.warning(f"⚠️ {msg_pct} 或 過濾後無相符資料")

with c2:
    st.subheader("📉 借券賣出減少張數排名")
    # 🔥 關鍵修改：關鍵字改為「借券賣出減少張數」
    df_vol, msg_vol = get_specific_margin_data("借券賣出減少張數")
    df_vol_clean = process_margin_df(df_vol, "張數")
    
    if not df_vol_clean.empty:
        st.info(f"💡 最新來源: {msg_vol}")
        st.dataframe(df_vol_clean, use_container_width=True)
    else:
        st.warning(f"⚠️ {msg_vol} 或 過濾後無相符資料")
       # 存入 4-2
        st.session_state['df_short_pct'] = df_pct_clean_short
        st.session_state['df_short_vol'] = df_vol_clean_short
# ==========================================
# 📅 區塊 4-3：融券增加動向 (5日累計)
# ==========================================
st.write("---")
st.markdown("<div id='section-4-3'></div>", unsafe_allow_html=True)
st.header("📅 區塊 4-3：融券增加動向 (5日累計)")

# 🛠️ 標的顯示過濾 UI
st.write("🔧 **自訂標的顯示過濾：**")
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1:
    show_etf_43 = st.checkbox("顯示 ETF", value=True, key="stock_show_etf_43")
with f_col2:
    show_bond_43 = st.checkbox("顯示債券/債券ETF", value=True, key="stock_show_bond_43")
st.write("") 

# --- 畫面佈局顯示 ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📈 融券增加比例排名")
    # 🔥 關鍵修改：關鍵字改為「融券增加幅度」
    df_pct, msg_pct = get_specific_margin_data("融券增加幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度") # 沿用相同的清理邏輯
    
    if not df_pct_clean.empty:
        st.info(f"💡 最新來源: {msg_pct}")
        st.dataframe(df_pct_clean, use_container_width=True)
    else:
        st.warning(f"⚠️ {msg_pct} 或 過濾後無相符資料")

with c2:
    st.subheader("📈 融券增加張數排名")
    # 🔥 關鍵修改：關鍵字改為「融券增加張數」
    df_vol, msg_vol = get_specific_margin_data("融券增加張數")
    df_vol_clean = process_margin_df(df_vol, "張數") # 沿用相同的清理邏輯
    
    if not df_vol_clean.empty:
        st.info(f"💡 最新來源: {msg_vol}")
        st.dataframe(df_vol_clean, use_container_width=True)
    else:
        st.warning(f"⚠️ {msg_vol} 或 過濾後無相符資料")
        # 存入 4-3
        st.session_state['df_margin_plus_pct'] = df_pct_clean_plus
        st.session_state['df_margin_plus_vol'] = df_vol_clean_plus
# ==========券資比資料請一起搬遷============
# ==========================================
# 📊 【蜂蜜計數器】本站累計觀測人次統計
# ==========================================
st.write("---")

# 🌟 新增防護罩：如果伺服器上沒有這個資料夾，就自動建立一個，避免當機
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

counter_file = os.path.join(DATA_DIR, "counter.txt")
if not os.path.exists(counter_file):
    with open(counter_file, "w") as f: f.write("1")
    count = 1
else:
    with open(counter_file, "r") as f:
        try: count = int(f.read().strip()) + 1
        except: count = 1
    with open(counter_file, "w") as f: f.write(str(count))

st.markdown(f"<p style='text-align: center; font-size: 16px; color: #DDA400; font-weight: bold;'>🐝 🍯 迷途不回家的小蜜蜂： {count} 隻 ｜ 祝阿東甜美收尾，順利通關畢業！ 🍯 🐝</p>", unsafe_allow_html=True)
