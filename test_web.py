import streamlit as st
import pandas as pd
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
    <p style='color: #665220; font-size: 16px; font-weight: bold;'>🌾 論文衝刺必勝 ｜ 蜂蜜香氣滿滿 ｜ 短線 3 日加速起漲雷達</p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("📊 系統已將指標全數展開：中長線法人持股% ｜ 短線外資投信買佔比 ｜ 短線外資投信買佔發行 (已內建 3 日突發加速衝刺追蹤機制)")

DATA_DIR = "C:\\Users\\User\\Downloads\\Goodinfo_Rankings"

def extract_date_from_name(filepath):
    filename = os.path.basename(filepath)
    date_match = re.search(r'(\d+)', filename)
    return date_match.group(1) if date_match else "00000000"

# ==========================================
# ⚙️ 萬能解析與讀取核心層
# ==========================================
def parse_special_txt(file_path):
    parsed_data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if "TWSE" in line_str or "TPEx" in line_str:
                parts = re.split(r'\t+', line_str)
                if len(parts) < 4: parts = [p for p in line_str.split(' ') if p]
                if len(parts) >= 4:
                    stock_raw = parts[1]
                    holding_pct = parts[3]
                    match = re.match(r'(\d+)(.+)', stock_raw)
                    if match:
                        parsed_data.append({"代號": match.group(1), "名稱": match.group(2), "持股%": float(holding_pct)})
    df = pd.DataFrame(parsed_data)
    if not df.empty: df = df.drop_duplicates(subset=['代號'], keep='first')
    return df

def load_csv_trajectory(pattern_str, column_suffix_name):
    csv_pattern = os.path.join(DATA_DIR, pattern_str)
    all_files = glob.glob(csv_pattern)
    display_df, date_labels = pd.DataFrame(), []
    if all_files:
        sorted_files = sorted(all_files, key=extract_date_from_name, reverse=True)
        base_df = None
        for file_path in sorted_files:
            date_label = extract_date_from_name(file_path)
            date_labels.append(date_label)
            try:
                df_day = pd.read_csv(file_path, encoding='utf-8-sig')
                df_day['代號'] = df_day['代號'].astype(str).str.strip()
                df_day['名稱'] = df_day['名稱'].astype(str).str.strip()
                matched_cols = [c for c in df_day.columns if any(k in c for k in ['5', '佔', '買超', '賣出', '日', '週', '比', '連續'])]
                target_col = matched_cols[0] if matched_cols else df_day.columns[2]
                df_small = df_day[['代號', '名稱', target_col]].copy()
                df_small[target_col] = pd.to_numeric(df_small[target_col], errors='coerce')
                df_small = df_small.rename(columns={target_col: f"{date_label}_{column_suffix_name}"})
                base_df = df_small if base_df is None else pd.merge(base_df, df_small, on=['代號', '名稱'], how='outer')
            except: pass
        if base_df is not None and len(date_labels) >= 2:
            col_latest = f"{date_labels[0]}_{column_suffix_name}"
            col_prev = f"{date_labels[1]}_{column_suffix_name}"
            if col_latest in base_df.columns and col_prev in base_df.columns:
                def judge_csv_trend(row):
                    v_l, v_p = row[col_latest], row[col_prev]
                    if pd.isna(v_l) and pd.isna(v_p): return "💤 觀察中"
                    elif not pd.isna(v_l) and pd.isna(v_p): return "🆕 新進榜"
                    elif pd.isna(v_l) and not pd.isna(v_p): return "❌ 掉出榜"
                    else: return "🚀 加碼" if float(v_l) - float(v_p) > 0 else ("🚨 減碼" if float(v_l) - float(v_p) < 0 else "🔄 持平")
                base_df['動態'] = base_df.apply(judge_csv_trend, axis=1)
            else: base_df['動態'] = "⏳ 指標天數錯位"
            display_df = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
            safe_history_cols = [f"{d}_{column_suffix_name}" for d in date_labels if f"{d}_{column_suffix_name}" in display_df.columns]
            display_df = display_df[["股票代號", "股票名稱", "動態"] + safe_history_cols]
    return display_df, date_labels

# ==========================================
# ⚡ 數據預先同步載入層
# ==========================================
# 1. 讀取三大法人持股 TXT
txt_pattern = os.path.join(DATA_DIR, "*持股排名變化*.txt")
all_txt_files = glob.glob(txt_pattern)
track_display_df, txt_date_labels = pd.DataFrame(), []
if all_txt_files:
    sorted_txt_files = sorted(all_txt_files, key=extract_date_from_name, reverse=True)
    base_track_df = None
    for file_path in sorted_txt_files:
        date_label = extract_date_from_name(file_path)
        txt_date_labels.append(date_label)
        df_day = parse_special_txt(file_path)
        if not df_day.empty:
            df_day = df_day.rename(columns={"持股%": f"{date_label} 持股%"})
            base_track_df = df_day if base_track_df is None else pd.merge(base_track_df, df_day, on=['代號', '名稱'], how='outer')
    if base_track_df is not None and len(txt_date_labels) >= 2:
        col_latest = f"{txt_date_labels[0]} 持股%"
        col_previous = f"{txt_date_labels[1]} 持股%"
        if col_latest in base_track_df.columns and col_previous in base_track_df.columns:
            base_track_df['籌碼趨勢'] = base_track_df.apply(lambda r: "🆕 新進榜" if not pd.isna(r[col_latest]) and pd.isna(r[col_previous]) else ("❌ 掉出榜" if pd.isna(r[col_latest]) and not pd.isna(r[col_previous]) else ("📈 上升" if not pd.isna(r[col_latest]) and not pd.isna(r[col_previous]) and float(r[col_latest]) - float(r[col_previous]) > 0 else ("📉 下降" if not pd.isna(r[col_latest]) and not pd.isna(r[col_previous]) and float(r[col_latest]) - float(r[col_previous]) < 0 else "🔄 趨緩"))), axis=1)
        else: base_track_df['籌碼趨勢'] = "⏳ 天數錯位"
        idx_3d = min(2, len(txt_date_labels) - 1)
        col_3d = f"{txt_date_labels[idx_3d]} 持股%"
        base_track_df['秘密3日斜率'] = (pd.to_numeric(base_track_df[col_latest], errors='coerce').fillna(0) - pd.to_numeric(base_track_df[col_3d], errors='coerce').fillna(0)).round(2)
        track_display_df = base_track_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        safe_txt_cols = [f"{d} 持股%" for d in txt_date_labels if f"{d} 持股%" in track_display_df.columns]
        track_display_df = track_display_df[["股票代號", "股票名稱", "籌碼趨勢", "秘密3日斜率"] + safe_txt_cols]
        track_display_df["排序權重"] = track_display_df["籌碼趨勢"].map({"📈 上升": 1, "🆕 新進榜": 2, "🔄 趨緩": 3, "觀察中": 4, "❌ 掉出榜": 5, "⏳ 天數錯位": 6})
        track_display_df = track_display_df.sort_values(by="排序權重")
#  加載 CSV 表格軌跡 (並存全部展開)
csv_foreign_deal, _ = load_csv_trajectory("*外資買超佔成交比*.csv", "外資買佔比(%)")
csv_it_deal, _ = load_csv_trajectory("*投信買超佔成交比*.csv", "投信買佔比(%)")
csv_foreign_stock, _ = load_csv_trajectory("*外資買超佔發行張數*.csv", "外資買佔發行(%)")
csv_it_stock, _ = load_csv_trajectory("*投信買超佔發行張數*.csv", "投信買佔發行(%)")
csv_foreign_sell, _ = load_csv_trajectory("*外資賣出佔成交比*.csv", "外資賣佔比(%)")
csv_it_sell, _ = load_csv_trajectory("*投信賣出佔成交比*.csv", "投信賣佔比(%)")
csv_it_ln_day, _ = load_csv_trajectory("*投信連續買超(日)*.csv", "投信連買日")
csv_it_ln_wk, it_wk_dates = load_csv_trajectory("*投信連續買超(週)*.csv", "投信連買週")
csv_foreign_ln_day, _ = load_csv_trajectory("*外資連續買超(日)*.csv", "外資連買日")
csv_foreign_ln_wk, fo_wk_dates = load_csv_trajectory("*外資連續買超(週)*.csv", "外資連買週")

def get_latest_only(df, date_labels, col_suffix):
    if df.empty or not date_labels: return pd.DataFrame()
    latest_col = f"{date_labels[0]}_{col_suffix}"
    cols_to_keep = ["股票代號", "股票名稱", "動態"]
    if latest_col in df.columns: cols_to_keep.append(latest_col)
    return df[cols_to_keep]

latest_it_wk = get_latest_only(csv_it_ln_wk, it_wk_dates, "投信連買週")
latest_fo_wk = get_latest_only(csv_foreign_ln_wk, fo_wk_dates, "外資連買週")

# ==========================================
# 👑 頂級核心：【三大法人多空評分 + 3日短線飆速置頂爆發榜】
# ==========================================
st.markdown("## 🏆 頂級核心：選股偵測池")
st.write("🔥 **戰術策略說明**：以長線 TXT 檔案為絕對基底，放寬偵測：今日數據對比前1天、前2天或前3天只要有實質增加（含突破未進榜斷層）即鎖定！短線不再強迫四大表全數交集，只要短線 4 大指標任一命中，即列入黃金名單！")

# 確保所有核心短線多空 CSV 與長線 TXT 皆有讀取到資料
if (not track_display_df.empty and not csv_foreign_deal.empty and not csv_foreign_stock.empty 
    and not csv_it_deal.empty and not csv_it_stock.empty and not csv_foreign_sell.empty and not csv_it_sell.empty):
    
    import glob, os
    import numpy as np

    # 🌟 💡 1. 股票代號型態安全鎖：強制清洗並統一轉字串
    def align_stock_id_type(df, target_col):
        if df.empty: return df
        df = df.copy()
        df[target_col] = df[target_col].astype(str).str.strip()
        return df

    # 現場資料清洗
    clean_track = align_stock_id_type(track_display_df, "股票代號")
    clean_f_sell = align_stock_id_type(csv_foreign_sell, "股票代號")
    clean_i_sell = align_stock_id_type(csv_it_sell, "股票代號")
    
    # 🌟 💡 2. 核心大改版：長線基底計算
    try:
        chart_cols = [c for c in clean_track.columns if "持股%" in c]
        if len(chart_cols) >= 4:
            def clean_pct_val(series):
                return pd.to_numeric(series.astype(str).str.replace('%', ''), errors='coerce').fillna(0.0)
            
            v_today = clean_pct_val(clean_track[chart_cols[0]])
            v_t_1 = clean_pct_val(clean_track[chart_cols[1]])
            v_t_2 = clean_pct_val(clean_track[chart_cols[2]])
            v_t_3 = clean_pct_val(clean_track[chart_cols[3]])
            
            cond_inc_1 = (v_today - v_t_1 > 0)
            cond_inc_2 = (v_today - v_t_2 > 0)
            cond_inc_3 = (v_today - v_t_3 > 0)
            
            clean_track["長線戰略狀態"] = "🚨 觀察中"
            clean_track.loc[cond_inc_3, "長線戰略狀態"] = "📈 前3日扣增"
            clean_track.loc[cond_inc_2, "長線戰略狀態"] = "🚀 前2日加速"
            clean_track.loc[cond_inc_1, "長線戰略狀態"] = "🔥 前1日暴衝"
            
            base_pool = clean_track[clean_track["長線戰略狀態"].isin(["🔥 前1日暴衝", "🚀 前2日加速", "📈 前3日扣增"])].copy()
        else:
            base_pool = clean_track[clean_track["籌碼趨勢"].isin(["📈 上升", "🆕 新進榜"])].copy()
            base_pool["長線戰略狀態"] = base_pool["籌碼趨勢"]
    except:
        base_pool = clean_track[clean_track["籌碼趨勢"].isin(["📈 上升", "🆕 新進榜"])].copy()
        base_pool["長線戰略狀態"] = base_pool["籌碼趨勢"]

    # 🌟 💡 3. 完美同步 2-1~2-4 的動態數值擷取引擎
    def fetch_latest_dynamic(pattern, mode="ratio"):
        files = glob.glob(os.path.join(DATA_DIR, pattern))
        if not files: return pd.DataFrame(columns=["股票代號", "動態"])
        latest_file = sorted(files, key=lambda x: os.path.basename(x), reverse=True)[0]
        
        try:
            df = pd.read_csv(latest_file, encoding='utf-8-sig', dtype=str)
            df.columns = [str(c).replace(" ", "").strip() for c in df.columns]
            id_col = next((c for c in df.columns if c in ['代號', '股票代號', '證券代號']), None)
            if not id_col: return pd.DataFrame(columns=["股票代號", "動態"])
            df['股票代號'] = df[id_col].astype(str).str.strip()

            t_col = next((c for c in df.columns if '當日' in c), None)
            f_col = next((c for c in df.columns if '5日' in c), None)
            if not t_col: return pd.DataFrame(columns=["股票代號", "動態"])

            df['t'] = pd.to_numeric(df[t_col], errors='coerce')
            df['f'] = pd.to_numeric(df[f_col], errors='coerce') if f_col else 0

            def tag(r):
                t, f = r['t'], r['f']
                if pd.isna(t): return "未進榜"
                
                if mode == "ratio":  # 2-1, 2-2 佔比模式
                    if t > 0 and (pd.isna(f) or f == 0): return f"🆕 新進榜 (+{t}%)"
                    if t > f and t > 0: return f"🔥 強延續 (+{t}%)"
                    if 0 < t <= f: return f"⚠️ 放緩 (+{t}%)"
                    if t < 0: return f"🚨 轉賣 ({t}%)"
                    return "💤 觀望"
                else:                # 2-3, 2-4 張數模式
                    if t > 0 and (pd.isna(f) or f == 0): return f"🆕 突擊卡位 (+{t}%)"
                    if t > 0: return f"🔥 持續加碼 (+{t}%)"
                    if t < 0: return f"🚨 轉賣反轉 ({t}%)"
                    return "💤 觀望"
                    
            df["動態"] = df.apply(tag, axis=1)
            return df[["股票代號", "動態"]]
        except: 
            return pd.DataFrame(columns=["股票代號", "動態"])

    # 即時讀取 4 大檔案最新動態
    dyn_f_deal = fetch_latest_dynamic("*外資買超佔成交比*.csv", mode="ratio").rename(columns={"動態": "外資買比動態"})
    dyn_f_stock = fetch_latest_dynamic("*外資買超佔發行張數*.csv", mode="stock").rename(columns={"動態": "外資發行動態"})
    dyn_i_deal = fetch_latest_dynamic("*投信買超佔成交比*.csv", mode="ratio").rename(columns={"動態": "投信買比動態"})
    dyn_i_stock = fetch_latest_dynamic("*投信買超佔發行張數*.csv", mode="stock").rename(columns={"動態": "投信發行動態"})

    # 進行串接 (how="left" 保證基底標的全部留存)
    m = pd.merge(base_pool[["股票代號", "股票名稱", "長線戰略狀態", "秘密3日斜率"]], dyn_f_deal, on="股票代號", how="left").fillna("未進榜")
    m = pd.merge(m, dyn_f_stock, on="股票代號", how="left").fillna("未進榜")
    m = pd.merge(m, dyn_i_deal, on="股票代號", how="left").fillna("未進榜")
    m = pd.merge(m, dyn_i_stock, on="股票代號", how="left").fillna("未進榜")

    # 賣盤與連買天數保持原邏輯安全提取
    def extract_dyn_col(df, new_col_name):
        if df.empty: return pd.DataFrame(columns=["股票代號", new_col_name])
        target_col = "今日短動態" if "今日短動態" in df.columns else "動態"
        if target_col not in df.columns: return pd.DataFrame(columns=["股票代號", new_col_name])
        return df[["股票代號", target_col]].rename(columns={target_col: new_col_name})

    m = pd.merge(m, extract_dyn_col(clean_f_sell, "外資賣比動態"), on="股票代號", how="left").fillna("觀察中")
    m = pd.merge(m, extract_dyn_col(clean_i_sell, "投信賣比動態"), on="股票代號", how="left").fillna("觀察中")

    def get_latest_val(df_target, col_keyword):
        if df_target.empty: return pd.Series(0, index=m.index)
        val_cols = [c for c in df_target.columns if col_keyword in c and c not in ["股票代號", "股票名稱", "動態"]]
        if not val_cols: return pd.Series(0, index=m.index)
        sub_df = df_target[["股票代號", val_cols[0]]].rename(columns={val_cols[0]: "val_target"})
        merged_sub = pd.merge(m[["股票代號"]], sub_df, on="股票代號", how="left")
        return pd.to_numeric(merged_sub["val_target"], errors='coerce').fillna(0)

    v_it_d = get_latest_val(csv_it_ln_day, "投信連買日")
    v_it_w = get_latest_val(csv_it_ln_wk, "投信連買週")
    v_f_d = get_latest_val(csv_foreign_ln_day, "外資連買日")
    v_f_w = get_latest_val(csv_foreign_ln_wk, "外資連買週")

    # 🌟 💡 4. 關鍵戰術篩選器：只要 4 表有任一有效動態，就留下！
    def is_active(series):
        # 排除所有代表「無動作」的字眼
        inactive_words = ["未進榜", "觀望", "💤", "⚪", "⏳", "觀察中"]
        pattern = "|".join(inactive_words)
        return ~series.str.contains(pattern, na=False)

    short_term_hit = (
        is_active(m["外資買比動態"]) | 
        is_active(m["外資發行動態"]) | 
        is_active(m["投信買比動態"]) | 
        is_active(m["投信發行動態"])
    )
    elite_filtered = m[short_term_hit].copy()

    if not elite_filtered.empty:
        idx = elite_filtered.index
        
        # 🌟 計分系統升級：模糊特徵捕捉法 (兼容數值與字串)
        p1 = elite_filtered["外資買比動態"].str.contains("🔥|🆕|⚠️", na=False).astype(int)
        p2 = elite_filtered["外資發行動態"].str.contains("🔥|🆕|⚠️", na=False).astype(int)
        p3 = elite_filtered["投信買比動態"].str.contains("🔥|🆕|⚠️", na=False).astype(int)
        p4 = elite_filtered["投信發行動態"].str.contains("🔥|🆕|⚠️", na=False).astype(int)
        p5 = (v_it_d.loc[idx] > 0).astype(int)
        p6 = (v_it_w.loc[idx] > 0).astype(int)
        p7 = (v_f_d.loc[idx] > 0).astype(int)
        p8 = (v_f_w.loc[idx] > 0).astype(int)
        
        # 扣分捕捉：包含警訊符號，或是賣盤檔案中有加碼動作
        m1 = elite_filtered["外資賣比動態"].str.contains("🚨|❌|🚀|劇烈", na=False).astype(int)
        m2 = elite_filtered["投信賣比動態"].str.contains("🚨|❌|🚀|劇烈", na=False).astype(int)
        m3 = elite_filtered["外資買比動態"].str.contains("🚨|❌", na=False).astype(int)
        m4 = elite_filtered["外資發行動態"].str.contains("🚨|❌", na=False).astype(int)
        
        elite_filtered["籌碼淨得分"] = (p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8) - (m1 + m2 + m3 + m4)
        
        elite_final_result = elite_filtered.sort_values(by=["籌碼淨得分", "秘密3日斜率"], ascending=[False, False])
        
        def get_score_tag(score):
            if score >= 6: return f"👑 頂級爆發 ({score}分)"
            elif score >= 3: return f"🔥 強力共振 ({score}分)"
            elif score >= 1: return f"📈 籌碼溫增 ({score}分)"
            elif score == 0: return "🔄 多空拉鋸 (0分)"
            else: return f"🚨 賣壓警訊 ({score}分)"
            
        elite_final_result["戰情訊號"] = elite_final_result["籌碼淨得分"].apply(get_score_tag)
        
        view_elite_df = elite_final_result[[
            "股票代號", "股票名稱", "戰情訊號", "長線戰略狀態", 
            "外資買比動態", "外資發行動態", "投信買比動態", "投信發行動態"
        ]].copy()
        
        view_elite_df.columns = [
            "股票代號", "股票名稱", "戰情多空評分", "長線法人軌跡", 
            "外資買佔比", "外資買佔發行", "投信買佔比", "投信買佔發行"
        ]
        
        # 將索引從 1 開始
        view_elite_df.index = range(1, len(view_elite_df) + 1)
        
        st.success(f"🎯 戰情雷達：經『長線1~3日回推加碼』與『短線4表任一命中機制』交叉篩選，目前共追蹤到 **{len(view_elite_df)}** 檔潛在黑馬股！")
        st.dataframe(view_elite_df, use_container_width=True)
    else:
        st.info("💡 目前長線看增的名單中，短線 4 大指標檔案尚無任何一項產生聯手交集。")
else:
    st.error("❌ 頂級核心多空矩陣運算失敗，請確認資料夾中的外資/投信 CSV 檔案是否完整。")

# ==========================================
# 🔍 個股籌碼快搜 (診斷區) - 已還原摺線圖與斜率指標
# ==========================================
st.write("---")
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.subheader("🔍 個股籌碼快搜 (診斷區)")

search_query = st.text_input("請輸入你想觀測的股票名稱或代號：", key="global_search_top")

# 💡 1. 初始化所有搜尋變數，徹底防止 NameError
q_txt = q_f_deal = q_i_deal = q_f_stock = q_i_stock = pd.DataFrame()

if search_query and not track_display_df.empty:
    
    # 2. 執行核心搜尋
    q_txt = track_display_df[track_display_df['股票名稱'].str.contains(search_query, na=False) | track_display_df['股票代號'].str.contains(search_query, na=False)]
    
    try:
        if not csv_foreign_deal.empty:
            q_f_deal = csv_foreign_deal[csv_foreign_deal['股票名稱'].str.contains(search_query, na=False) | csv_foreign_deal['股票代號'].str.contains(search_query, na=False)]
        if not csv_it_deal.empty:
            q_i_deal = csv_it_deal[csv_it_deal['股票名稱'].str.contains(search_query, na=False) | csv_it_deal['股票代號'].str.contains(search_query, na=False)]
        if not csv_foreign_stock.empty:
            q_f_stock = csv_foreign_stock[csv_foreign_stock['股票名稱'].str.contains(search_query, na=False) | csv_foreign_stock['股票代號'].str.contains(search_query, na=False)]
        if not csv_it_stock.empty:
            q_i_stock = csv_it_stock[csv_it_stock['股票名稱'].str.contains(search_query, na=False) | csv_it_stock['股票代號'].str.contains(search_query, na=False)]
    except Exception as e:
        st.error(f"資料篩選過程發生錯誤: {e}")

    # 3. 輸出結果與還原功能
    if q_txt.empty:
        st.warning(f"⚠️ 系統中找不到與 '{search_query}' 相關的資料。")
    else:
        st.write(f"### 🎯 綜合診斷標的：{search_query}")
        st.write("📋 **1. 中長線三大法人持股變化軌跡：**")
        # 排除隱藏欄位後顯示
        st.dataframe(q_txt.drop(columns=["秘密3日斜率"], errors='ignore'), use_container_width=True)
        
        # 💡 4. 【還原】四大斜率指標 (多週期油門加速探針)
        try:
            chart_cols = [c for c in q_txt.columns if "持股%" in c]
            if chart_cols:
                v_latest = pd.to_numeric(q_txt.iloc[0][chart_cols[0]], errors='coerce')
                
                def get_diff_pct(days_back):
                    idx = min(days_back - 1, len(chart_cols) - 1)
                    v_back = pd.to_numeric(q_txt.iloc[0][chart_cols[idx]], errors='coerce')
                    if pd.isna(v_latest) or pd.isna(v_back):
                        return 0.0
                    return round(float(v_latest - v_back), 2)

                slope_df = pd.DataFrame({
                    "指標週期": ["⚡ 2日短線突發斜率", "📈 5日短線加速斜率", "🚀 10日中線轉折斜率", "🔒 20日月線波段鎖籌"],
                    "法人持股淨增減(%)": [get_diff_pct(2), get_diff_pct(5), get_diff_pct(10), get_diff_pct(20)]
                })
                st.write("📊 **三大法人持股多週期油門加速探針：**")
                st.dataframe(slope_df, use_container_width=True)
                
                # 💡 5. 【還原】21日折線圖 (全景軌跡)
                chart_cols_21 = chart_cols[:21]
                # 將欄位名稱簡化為日期，並翻轉順序以符合時間軸（左舊右新）
                t_ser = pd.Series(
                    pd.to_numeric(q_txt.iloc[0][chart_cols_21].values, errors='coerce'), 
                    index=[c.split(' ')[0] for c in chart_cols_21]
                ).iloc[::-1].dropna()
                
                if not t_ser.empty:
                    st.write(f"📈 **三大法人持股 21日波段全景軌跡曲線 ({q_txt.iloc[0]['股票名稱']})**")
                    st.line_chart(t_ser, height=240)
        except Exception as chart_err:
            st.info(f"圖表渲染暫無數據: {chart_err}")

        st.write("---")
        st.markdown("##### 🚀 核心主力短線進攻與鎖籌指標")
        c1, c2 = st.columns(2)
        
        # 💡 6. 修正後的標準 if-else，徹底移除程式碼亂碼 (DeltaGenerator)
        with c1:
            st.write("📊 **外資買佔比軌跡：**")
            if not q_f_deal.empty:
                st.dataframe(q_f_deal, use_container_width=True)
            else:
                st.write("無資料")
                
            st.write("🔒 **外資買佔發行軌跡：**")
            if not q_f_stock.empty:
                st.dataframe(q_f_stock, use_container_width=True)
            else:
                st.write("無資料")
                
        with c2:
            st.write("🥦 **投信買佔比軌跡：**")
            if not q_i_deal.empty:
                st.dataframe(q_i_deal, use_container_width=True)
            else:
                st.write("無資料")
                
            st.write("💎 **投信買佔發行軌跡：**")
            if not q_i_stock.empty:
                st.dataframe(q_i_stock, use_container_width=True)
            else:
                st.write("無資料")

elif search_query:
    st.info("請輸入代號或名稱開始診斷個股籌碼...")
# ==========================================
# 🧭 側邊欄導航 (雙指標總經風向球完全體)
# ==========================================
st.sidebar.header("⚡ 籌碼超級篩選器")
filter_trend = st.sidebar.selectbox("三大法人持股趨勢過濾：", ["全部顯示", "🔥 僅顯示『上升+新進榜』", "📈 僅顯示上升", "🆕 僅顯示新進榜"])

# 🌟 升級點：雙按鈕並聯，打造大盤風向球專區
st.sidebar.markdown("---")
st.sidebar.subheader("📊 大盤總體經濟指標")

c_btn1, c_btn2 = st.sidebar.columns(2)
with c_btn1:
    st.link_button(
        "📈 恐懼貪婪指數", 
        "https://www.wantgoo.com/global/macroeconomics/fearandgreed",
        use_container_width=True
    )
with c_btn2:
    st.link_button(
        "⚠️ VIX 恐慌指數", 
        "https://www.wantgoo.com/global/vix",
        use_container_width=True
    )
st.sidebar.markdown("---")
st.sidebar.header("📍 戰情室快速導航跳轉")
st.sidebar.markdown("""
[👑 區塊一：三大法人持股%](#section-1)

""")

# ==========================================
# 🏠 核心五大區塊
# ==========================================
st.write("---")
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)
st.header("🏢 區塊1：中長線 三大法人 持股比例 追蹤")
if not track_display_df.empty: st.dataframe(track_display_df.drop(columns=["秘密3日斜率"]), use_container_width=True)
# ==========================================
# ：多天期 5日 外資買賣佔成交量比軌跡追蹤 (CSV)
# ==========================================
st.write("---")
st.header("🎯 區塊2-1：外資 5 日買超 佔成交量比 追蹤")

# 1. 檔名搜尋採用模糊比對，精確鎖定外資檔案
csv_pattern = os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")
all_csv_files = glob.glob(csv_pattern)

if not all_csv_files:
    st.warning("⚠️ 找不到任何包含『外資買超佔成交比』的 CSV 檔案，請檢查路徑或檔名。")
else:
    # 將外資檔案依「由新到舊」排序
    all_csv_files.sort(reverse=True)
    target_files = all_csv_files[:14]
    
    # 精確欄位比對清單
    EXACT_TODAY_CANDIDATES = ['當日買進佔成交', '當日買賣超佔成交', '當日 買賣超 佔 成交']
    EXACT_5DAY_CANDIDATES = ['5日買進佔成交', '5日買賣超佔成交', '5日 買賣超 佔 成交']
    
    # 2. 提取最新一天 (0522) 作為基準主表
    latest_file = target_files[0]
    latest_filename = os.path.basename(latest_file)
    latest_date_str = latest_filename[:8]  
    latest_mmdd = f"{latest_date_str[4:6]}{latest_date_str[6:8]}" 
    
    try:
        df_base_raw = pd.read_csv(latest_file, dtype=str)
        
        col_today_exact = None
        for candidate in EXACT_TODAY_CANDIDATES:
            if candidate in df_base_raw.columns:
                col_today_exact = candidate
                break
                
        if '代號' not in df_base_raw.columns or '名稱' not in df_base_raw.columns or col_today_exact is None:
            st.error(f"❌ 最新基準檔案 `{latest_filename}` 缺少指定必要欄位。")
        else:
            df_base_raw = df_base_raw.dropna(subset=['代號', '名稱'])
            df_base_raw = df_base_raw[df_base_raw['代號'].str.strip() != ""]
            df_base_raw = df_base_raw.drop_duplicates(subset=['代號'])
            
            df_base_master = pd.DataFrame({
                '股票代號': df_base_raw['代號'].astype(str).str.strip(),
                '股票名稱': df_base_raw['名稱'].astype(str).str.strip(),
                '當日買佔比%': pd.to_numeric(df_base_raw[col_today_exact], errors='coerce')
            })
            
            df_base_master['_base_order'] = range(len(df_base_master))
            
            df_history_combined = df_base_master[['股票代號', '股票名稱']].copy()
            
            # 3. 完整跑完所有 target_files，橫向新增歷史各日資料
            for file_path in target_files:
                filename = os.path.basename(file_path)
                date_raw = filename[:8] 
                date_label = f"{date_raw[4:6]}{date_raw[6:8]}" if date_raw.isdigit() else date_raw
                target_grid_col = f"{date_label}買佔比%"
                
                try:
                    df_day = pd.read_csv(file_path, dtype=str)
                    col_5day_exact = None
                    for candidate in EXACT_5DAY_CANDIDATES:
                        if candidate in df_day.columns:
                            col_5day_exact = candidate
                            break
                    
                    if '代號' in df_day.columns and col_5day_exact is not None:
                        df_day_subset = df_day[['代號', '名稱', col_5day_exact]].copy()
                        df_day_subset = df_day_subset.dropna(subset=['代號', '名稱'])
                        df_day_subset['代號'] = df_day_subset['代號'].astype(str).str.strip()
                        df_day_subset['名稱'] = df_day_subset['名稱'].astype(str).str.strip()
                        df_day_subset = df_day_subset[df_day_subset['代號'] != ""]
                        df_day_subset = df_day_subset.drop_duplicates(subset=['代號'])
                        
                        df_day_subset[target_grid_col] = pd.to_numeric(df_day_subset[col_5day_exact], errors='coerce')
                        df_day_subset = df_day_subset[['代號', '名稱', target_grid_col]]
                        df_day_subset.columns = ['股票代號', '股票名稱', target_grid_col]
                        
                        df_history_combined = pd.merge(df_history_combined, df_day_subset, on=['股票代號', '股票名稱'], how='outer')
                except Exception:
                    pass

            # ==========================================
            # 🧠 延續性狀態分析
            # ==========================================
            latest_5d_col = f"{latest_mmdd}買佔比%"
            df_analysis = pd.merge(
                df_history_combined, 
                df_base_master[['股票代號', '股票名稱', '當日買佔比%']], 
                on=['股票代號', '股票名稱'], 
                how='left'
            )

            recent_3_cols = []
            for f_path in target_files[:3]:
                d_raw = os.path.basename(f_path)[:8]
                if len(d_raw) == 8 and d_raw.isdigit():
                    col_name = f"{d_raw[4:6]}{d_raw[6:8]}買佔比%"
                    if col_name in df_analysis.columns:
                        recent_3_cols.append(col_name)

            prev_cols = [c for c in recent_3_cols if c != latest_5d_col]
            df_analysis['baseline_3d'] = df_analysis[recent_3_cols].mean(axis=1) if recent_3_cols else None

            def evaluate_continuity(row):
                today = row.get('當日買佔比%', None)
                base_3d = row.get('baseline_3d', None)
                if pd.isna(today) or base_3d is None or pd.isna(base_3d): return "⚪ 觀望或無數據"
                
                has_past_data = any(pd.notna(row.get(c, None)) for c in prev_cols)
                if not has_past_data and today > 0: return "🆕 新進榜"
                
                if today > base_3d and today > 0: return "🔥 強延續"
                elif 0 < today <= base_3d: return "⚠️ 放緩 (持續買進)"
                elif today == 0: return "⚪ 觀望持平 (量縮)"
                elif today < 0:
                    if base_3d <= 0: return "❌ 法人轉賣反轉"
                    ratio = abs(today / base_3d)
                    return "🚨 劇烈倒貨 (籌碼洗盤)" if ratio >= 1.5 else "📉 調節洗盤 (尚屬健康)"
                return "⚪ 觀望持平"

            df_history_combined['今日短動態'] = df_analysis.apply(evaluate_continuity, axis=1)

            # ==========================================
            # 🛠️ 數據與篩選
            # ==========================================
            df_display = pd.merge(df_base_master, df_history_combined, on=['股票代號', '股票名稱'], how='left')
            df_display = df_display.sort_values(by='_base_order', ascending=True)
            
            st.write("🔧 **自訂標的顯示過濾：**")
            c1, c2 = st.columns(2)
            show_etf = c1.checkbox("顯示 ETF", value=True)
            show_bond = c2.checkbox("顯示 債券/債券ETF", value=True)
            
            is_bond = df_display['股票代號'].str.endswith('B')
            is_etf = (df_display['股票代號'].str.len() >= 5) & (~is_bond)
            is_stock = df_display['股票代號'].str.len() == 4
            
            mask = is_stock
            if show_etf: mask = mask | is_etf
            if show_bond: mask = mask | is_bond
            df_display = df_display[mask]
            
            # 重新排列順序並將 Index 轉為 1 開始
            base_cols = ['股票代號', '股票名稱', '今日短動態', '當日買佔比%']
            history_cols = [c for c in df_display.columns if '買佔比%' in c and c != '當日買佔比%']
            df_display = df_display[base_cols + history_cols]
            df_display.index = range(1, len(df_display) + 1)
            
            st.success(f"📊 已成功串聯 {len(target_files)} 個交易日，追蹤 {len(df_display)} 檔曾進榜的短線熱門股：")
            st.markdown("💡 **動態說明：** 🆕 新進榜：強勢空降。🔥 強延續：買盤動能加速。⚠️ 放緩 (持續買進)：買超力道低於近期均線。📉 調節洗盤：微幅轉賣調節。🚨 劇烈倒貨：強烈轉賣。❌ 法人轉賣反轉：趨勢翻空。")
            st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"❌ 處理主程式時發生錯誤: {e}")

# ==========================================
# ：多天期 5日 投信買賣佔成交量比軌跡追蹤 (CSV)
# ==========================================
st.write("---")
st.header("🎯 區塊2-2：投信 5 日買超 佔成交量比 追蹤")

# 1. 檔名搜尋採用模糊比對，精確鎖定投信檔案
csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")
all_csv_files_sitc = glob.glob(csv_pattern_sitc)

if not all_csv_files_sitc:
    st.warning("⚠️ 找不到任何包含『投信買超佔成交比』的 CSV 檔案。")
else:
    all_csv_files_sitc.sort(reverse=True)
    target_files_sitc = all_csv_files_sitc[:14]
    
    EXACT_TODAY_CANDIDATES = ['當日買進佔成交', '當日買賣超佔成交', '當日 買賣超 佔 成交']
    EXACT_5DAY_CANDIDATES = ['5日買進佔成交', '5日買賣超佔成交', '5日 買賣超 佔 成交']
    
    latest_file_sitc = target_files_sitc[0]
    latest_filename_sitc = os.path.basename(latest_file_sitc)
    latest_mmdd_sitc = f"{latest_filename_sitc[4:6]}{latest_filename_sitc[6:8]}"
    
    try:
        df_base_sitc = pd.read_csv(latest_file_sitc, dtype=str)
        df_base_sitc = df_base_sitc.dropna(subset=['代號', '名稱'])
        df_base_sitc = df_base_sitc[df_base_sitc['代號'].str.strip() != ""]
        df_base_sitc = df_base_sitc.drop_duplicates(subset=['代號'])
        
        # 尋找欄位
        col_today_sitc = next((c for c in EXACT_TODAY_CANDIDATES if c in df_base_sitc.columns), None)
        
        df_master_sitc = pd.DataFrame({
            '股票代號': df_base_sitc['代號'].astype(str).str.strip(),
            '股票名稱': df_base_sitc['名稱'].astype(str).str.strip(),
            '當日買佔比%': pd.to_numeric(df_base_sitc[col_today_sitc], errors='coerce')
        })
        df_master_sitc['_base_order'] = range(len(df_master_sitc))
        
        df_hist_sitc = df_master_sitc[['股票代號', '股票名稱']].copy()
        
        # 循環讀取歷史資料
        for file_path in target_files_sitc:
            filename = os.path.basename(file_path)
            date_label = f"{filename[4:6]}{filename[6:8]}" if filename[:8].isdigit() else filename[:8]
            target_col = f"{date_label}買佔比%"
            
            df_day = pd.read_csv(file_path, dtype=str)
            col_5d = next((c for c in EXACT_5DAY_CANDIDATES if c in df_day.columns), None)
            
            if col_5d:
                df_temp = df_day[['代號', '名稱', col_5d]].copy()
                df_temp.columns = ['股票代號', '股票名稱', target_col]
                df_temp['股票代號'] = df_temp['股票代號'].astype(str).str.strip()
                df_temp[target_col] = pd.to_numeric(df_temp[target_col], errors='coerce')
                df_hist_sitc = pd.merge(df_hist_sitc, df_temp, on=['股票代號', '股票名稱'], how='outer')

        # 延續性分析
        df_analysis_sitc = pd.merge(df_hist_sitc, df_master_sitc[['股票代號', '股票名稱', '當日買佔比%']], on=['股票代號', '股票名稱'], how='left')
        
        # 近3日平均
        recent_3 = [f"{os.path.basename(f)[4:6]}{os.path.basename(f)[6:8]}買佔比%" for f in target_files_sitc[:3]]
        prev_cols = [c for c in recent_3 if c != f"{latest_mmdd_sitc}買佔比%"]
        df_analysis_sitc['baseline_3d'] = df_analysis_sitc[[c for c in recent_3 if c in df_analysis_sitc.columns]].mean(axis=1)

        def evaluate(row):
            today = row.get('當日買佔比%', None)
            base = row.get('baseline_3d', None)
            if pd.isna(today) or base is None or pd.isna(base): return "⚪ 觀望或無數據"
            if not any(pd.notna(row.get(c, None)) for c in prev_cols) and today > 0: return "🆕 新進榜"
            if today > base and today > 0: return "🔥 強延續"
            elif 0 < today <= base: return "⚠️ 放緩 (持續買進)"
            elif today == 0: return "⚪ 觀望持平 (量縮)"
            elif today < 0:
                if base <= 0: return "❌ 法人轉賣反轉"
                return "🚨 劇烈倒貨 (籌碼洗盤)" if abs(today/base) >= 1.5 else "📉 調節洗盤 (尚屬健康)"
            return "⚪ 觀望持平"

        df_hist_sitc['今日短動態'] = df_analysis_sitc.apply(evaluate, axis=1)
        
        # 呈現設定
        df_show_sitc = pd.merge(df_master_sitc, df_hist_sitc, on=['股票代號', '股票名稱'], how='left')
        df_show_sitc = df_show_sitc.sort_values(by='_base_order')
        
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond")
        
        # 篩選遮罩
        mask = (df_show_sitc['股票代號'].str.len() == 4)
        if show_etf: mask = mask | ((df_show_sitc['股票代號'].str.len() >= 5) & (~df_show_sitc['股票代號'].str.endswith('B')))
        if show_bond: mask = mask | (df_show_sitc['股票代號'].str.endswith('B'))
        df_show_sitc = df_show_sitc[mask]
        
        # 欄位順序與 Index
        base_cols = ['股票代號', '股票名稱', '今日短動態', '當日買佔比%']
        df_show_sitc = df_show_sitc[base_cols + [c for c in df_show_sitc.columns if '買佔比%' in c and c != '當日買佔比%']]
        df_show_sitc.index = range(1, len(df_show_sitc) + 1)
        
        st.success(f"📊 已成功串聯 {len(target_files_sitc)} 個交易日，追蹤 {len(df_show_sitc)} 檔曾進榜的短線熱門股：")
        st.markdown("💡 **動態說明：** 🆕 新進榜：強勢空降。🔥 強延續：買盤動能加速。⚠️ 放緩 (持續買進)：買超力道低於近期均線。📉 調節洗盤：微幅轉賣調節  🚨 劇烈倒貨：強烈轉賣 ❌ 法人轉賣反轉：趨勢翻空。")
        st.dataframe(df_show_sitc, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ 處理投信程式時發生錯誤: {e}")

# ==========================================
# 🎯 區塊2-3：外資 5 日買超佔發行張數 追蹤
# ==========================================
st.write("---")
st.header("🎯 區塊2-3：外資 5 日買超佔發行張數 追蹤")
csv_pattern = os.path.join(DATA_DIR, "*外資買超佔發行張數*.csv")
all_csv_files = glob.glob(csv_pattern)

if all_csv_files:
    sorted_files = sorted(all_csv_files, key=extract_date_from_name, reverse=True)[:10]
    base_df, date_labels, latest_day_today_data = None, [], {}
    
    for idx, f in enumerate(sorted_files):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").strip() for c in df.columns]
            df = df.rename(columns={'代號':'代號', '名稱':'名稱', '股票代號':'代號', '股票名稱':'名稱'}) 
            df['代號'] = df['代號'].astype(str).str.replace(" ", "").str.strip()
            df['名稱'] = df['名稱'].astype(str).str.replace(" ", "").str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            if idx == 0:
                t_col = next((c for c in df.columns if '當日' in c and '發行' in c), None)
                if t_col: latest_day_today_data = dict(zip(df['代號'], pd.to_numeric(df[t_col], errors='coerce')))
            
            t_col = next((c for c in df.columns if '5日' in c and '發行' in c), df.columns[2])
            df_s = df[['代號', '名稱', t_col]].rename(columns={t_col: f"{d_label}外資買發張數%"})
            
            if base_df is None:
                base_df = df_s
                base_df['_base_order'] = range(len(base_df)) 
            else:
                base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
                
            date_labels.append(d_label)
        except Exception: continue

    if base_df is not None and len(date_labels) > 0:
        import numpy as np
        
        csv_display = base_df.copy()
        
        csv_display = csv_display.sort_values(by='_base_order', ascending=True, na_position='last')
        csv_display = csv_display.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        latest_5d_col = f"{date_labels[0]}外資買發張數%"
        
        def judge_today_alert(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, "未進榜")
            val_today = latest_day_today_data.get(stock_id, np.nan)
            
            if pd.isna(val_5d) or val_5d == "未進榜":
                if not pd.isna(val_today) and val_today > 0:
                    return f"🆕 今日突擊卡位 (+{val_today}%)"
                return "💤 籌碼沉澱中"
            
            if not pd.isna(val_today):
                if val_today < 0: return f"🚨 今日轉賣反轉 ({val_today}%)"
                elif val_today > 0: return f"🔥 今日持續加碼 (+{val_today}%)"
                else: return "🔄 今日量縮持平 (0.0%)"
            
            return "⏳ 歷史留存數據"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert, axis=1)
        
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="foreign_etf_v8")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="foreign_bond_v8")
        
        # ==========================================
        # 🚀 實戰升級：進階動態篩選與力道排序
        # ==========================================
        sort_filter_option = st.selectbox(
            "🎯 進階動態篩選與排序：",
            [
                "預設：依原始榜單排名置頂",
                "🔥 僅顯示『今日持續加碼』 (依買超力道由大到小排序)",
                "🆕 僅顯示『今日突擊卡位』 (依買超力道由大到小排序)",
                "🚨 僅顯示『今日轉賣反轉』 (依賣超力道由重到輕排序)"
            ],
            key="foreign_sort_v8"
        )
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 提取真實數值用於排序
        csv_display['_today_val'] = csv_display['股票代號'].map(latest_day_today_data).fillna(-999)
        
        # 依據使用者選擇進行過濾與排序
        if "今日持續加碼" in sort_filter_option:
            csv_display = csv_display[csv_display['今日短動態'].str.contains("今日持續加碼", na=False)]
            csv_display = csv_display.sort_values(by='_today_val', ascending=False)
        elif "今日突擊卡位" in sort_filter_option:
            csv_display = csv_display[csv_display['今日短動態'].str.contains("今日突擊卡位", na=False)]
            csv_display = csv_display.sort_values(by='_today_val', ascending=False)
        elif "今日轉賣反轉" in sort_filter_option:
            csv_display = csv_display[csv_display['今日短動態'].str.contains("今日轉賣反轉", na=False)]
            # 賣超是負數，由重到輕代表數值越小越前面 (ascending=True)
            csv_display = csv_display.sort_values(by='_today_val', ascending=True)

        # 整理欄位
        fixed_cols = ["股票代號", "股票名稱", "今日短動態"]
        history_cols = [f"{c}外資買發張數%" for c in sorted(list(set(date_labels)), reverse=True) if f"{c}外資買發張數%" in csv_display.columns]
        csv_display = csv_display[fixed_cols + history_cols]
        
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯 {len(date_labels)} 個交易日，符合條件追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)


# ==========================================
# 🎯 區塊2-4：投信 5 日買超佔發行張數 追蹤
# ==========================================
st.write("---")
st.header("🎯 區塊2-4：投信 5 日買超佔發行張數 追蹤")
csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if all_files_sitc:
    sorted_files = sorted(all_files_sitc, key=extract_date_from_name, reverse=True)[:10]
    base_df, date_labels, latest_day_today_data_sitc = None, [], {}
    
    for idx, f in enumerate(sorted_files):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").strip() for c in df.columns]
            df = df.rename(columns={'代號':'代號', '名稱':'名稱', '股票代號':'代號', '股票名稱':'名稱'}) 
            df['代號'] = df['代號'].astype(str).str.replace(" ", "").str.strip()
            df['名稱'] = df['名稱'].astype(str).str.replace(" ", "").str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            if idx == 0:
                t_col = next((c for c in df.columns if '當日' in c and '發行' in c), None)
                if t_col: latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[t_col], errors='coerce')))
            
            t_col = next((c for c in df.columns if '5日' in c and '發行' in c), df.columns[2])
            df_s = df[['代號', '名稱', t_col]].rename(columns={t_col: f"{d_label}投信買發張數%"})
            
            if base_df is None:
                base_df = df_s
                base_df['_base_order'] = range(len(base_df))
            else:
                base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
                
            date_labels.append(d_label)
        except Exception: continue

    if base_df is not None and len(date_labels) > 0:
        import numpy as np
        
        csv_display = base_df.copy()
        
        csv_display = csv_display.sort_values(by='_base_order', ascending=True, na_position='last')
        csv_display = csv_display.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        latest_5d_col = f"{date_labels[0]}投信買發張數%"
        
        def judge_today_alert_sitc(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, "未進榜")
            val_today = latest_day_today_data_sitc.get(stock_id, np.nan)
            
            if pd.isna(val_5d) or val_5d == "未進榜":
                if not pd.isna(val_today) and val_today > 0:
                    return f"🆕 今日突擊卡位 (+{val_today}%)"
                return "💤 籌碼沉澱中"
            
            if not pd.isna(val_today):
                if val_today < 0: return f"🚨 今日轉賣反轉 ({val_today}%)"
                elif val_today > 0: return f"🔥 今日持續加碼 (+{val_today}%)"
                else: return "🔄 今日量縮持平 (0.0%)"
            
            return "⏳ 歷史留存數據"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_sitc, axis=1)
        
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_v8")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_v8")
        
        # ==========================================
        # 🚀 實戰升級：進階動態篩選與力道排序
        # ==========================================
        sort_filter_option_sitc = st.selectbox(
            "🎯 進階動態篩選與排序：",
            [
                "預設：依原始榜單排名置頂",
                "🔥 僅顯示『今日持續加碼』 (依買超力道由大到小排序)",
                "🆕 僅顯示『今日突擊卡位』 (依買超力道由大到小排序)",
                "🚨 僅顯示『今日轉賣反轉』 (依賣超力道由重到輕排序)"
            ],
            key="sitc_sort_v8"
        )
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 提取真實數值用於排序
        csv_display['_today_val'] = csv_display['股票代號'].map(latest_day_today_data_sitc).fillna(-999)
        
        # 依據使用者選擇進行過濾與排序
        if "今日持續加碼" in sort_filter_option_sitc:
            csv_display = csv_display[csv_display['今日短動態'].str.contains("今日持續加碼", na=False)]
            csv_display = csv_display.sort_values(by='_today_val', ascending=False)
        elif "今日突擊卡位" in sort_filter_option_sitc:
            csv_display = csv_display[csv_display['今日短動態'].str.contains("今日突擊卡位", na=False)]
            csv_display = csv_display.sort_values(by='_today_val', ascending=False)
        elif "今日轉賣反轉" in sort_filter_option_sitc:
            csv_display = csv_display[csv_display['今日短動態'].str.contains("今日轉賣反轉", na=False)]
            csv_display = csv_display.sort_values(by='_today_val', ascending=True)
        
        fixed_cols = ["股票代號", "股票名稱", "今日短動態"]
        history_cols = [f"{c}投信買發張數%" for c in sorted(list(set(date_labels)), reverse=True) if f"{c}投信買發張數%" in csv_display.columns]
        csv_display = csv_display[fixed_cols + history_cols]
        
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯 {len(date_labels)} 個交易日，符合條件追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
# ==========================================
# 📅 區塊六：外資與投信連續買超 (日/週全景戰情室 - 全量解禁完全體)
# ==========================================
st.write("---")
st.markdown("<div id='section-wk'></div>", unsafe_allow_html=True)
st.header("📅 區塊3：連續買超戰情室")

# 在核心單日/單週大板塊下方，展示動態標籤說明文字
st.info("""
💡 **狀態動態評估依據（籌碼認養密度分級說明）：**
* 連買 **10以上天 / 週** 🔥 **波段認養** (長線鎖籌，趨勢保護力極強)
* 連買 **5 ~ 9 天 / 週** ⚡ **買盤點火** (資金流入，短期爆發動能，週連買有底氣)
* 連買 **1 ~ 4 天 / 週** 🆕 **試單觀察** (法人第一時間進場试單，週連買初步建倉)
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
    if not target_files:
        return pd.DataFrame(), None
        
    latest_file = sorted(target_files, key=extract_date_from_name, reverse=True)[0]
    date_str = extract_date_from_name(latest_file) 
    
    try:
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        df.columns = df.columns.astype(str).str.replace('\n', '').str.replace(' ', '').str.strip()
        
        col_id = [c for c in df.columns if '代號' in c or '股票' in c]
        col_name = [c for c in df.columns if '名稱' in c or '股票' in c]
        c_id = col_id[0] if col_id else df.columns[0]
        c_name = col_name[0] if len(col_name) > 0 else (col_id[0] if col_id else df.columns[1])
        
        target_key = exact_field_name.replace(' ', '')
        if target_key in df.columns:
            target_data_col = target_key
        else:
            matched_cols = [c for c in df.columns if '買賣' in c and strict_type in c]
            target_data_col = matched_cols[0] if matched_cols else df.columns[2]
            
        df[target_data_col] = pd.to_numeric(df[target_data_col], errors='coerce').fillna(0)
        
        # 🌟 核心修正：拿掉尾端的 .head(20)，只要是大於 0（正在買超狀態）的公司全數釋出！
        df_sorted = df[df[target_data_col] > 0].sort_values(by=target_data_col, ascending=False)
        
        if df_sorted.empty:
            return pd.DataFrame(), date_str
            
        output_df = pd.DataFrame()
        output_df["股票代號"] = df_sorted[c_id].astype(str).str.strip()
        output_df["股票名稱"] = df_sorted[c_name].astype(str).str.strip()
        
        def get_status_tag(val):
            if val >= 10:
                return "🔥 波段認養"
            elif val >= 5:
                return "⚡ 買盤點火"
            else:
                return "🆕 試單觀察"
                
        output_df["狀態動態"] = df_sorted[target_data_col].apply(get_status_tag)
        output_df[col_label] = df_sorted[target_data_col].astype(int)
        
        real_pct_trade = [c for c in df_sorted.columns if prefix_keyword in c and "佔成交" in c]
        real_pct_issue = [c for c in df_sorted.columns if prefix_keyword in c and "佔發行量" in c]
        
        if real_pct_trade:
            output_df["佔成交(%)"] = pd.to_numeric(df_sorted[real_pct_trade[0]], errors='coerce').fillna(0.0)
        else:
            output_df["佔成交(%)"] = 0.0
            
        if real_pct_issue:
            output_df["佔發行量(%)"] = pd.to_numeric(df_sorted[real_pct_issue[0]], errors='coerce').fillna(0.0)
        else:
            output_df["佔發行量(%)"] = 0.0
            
        # 名次序號從 1 開始順著實際資料量一路排下去
        output_df.index = range(1, len(output_df) + 1)
            
        return output_df, date_str

    except Exception as e:
        # 🌟 補上結構對齊的安全防護罩，根除 SyntaxError 錯誤
        return pd.DataFrame(), f"解讀失敗: {str(e)}"

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
st.subheader("⚡ 核心主力：最新單日連續買超")
c_day1, c_day2 = st.columns(2)

with c_day1:
    st.markdown(f"🌐 **外資最新日連買** *(最新檔案日期: {date_fo_day if date_fo_day else '無資料'})*")
    if not live_fo_day.empty:
        st.dataframe(live_fo_day, use_container_width=True)
    else:
        st.write("無資料")

with c_day2:
    st.markdown(f"🥦 **投信最新日連買** *(最新檔案日期: {date_it_day if date_it_day else '無資料'})*")
    if not live_it_day.empty:
        st.dataframe(live_it_day, use_container_width=True)
    else:
        st.write("無資料")

st.write(" ") 

st.subheader("📅 戰略波段：最新單週連續買超")
c_wk1, c_wk2 = st.columns(2)

with c_wk1:
    st.markdown(f"🌐 **外資最新週連買** *(最新檔案日期: {date_fo_wk if date_fo_wk else '無資料'})*")
    if not live_fo_wk.empty:
        st.dataframe(live_fo_wk, use_container_width=True)
    else:
        st.write("無資料")

with c_wk2:
    st.markdown(f"🥦 **投信最新週連買** *(最新檔案日期: {date_it_wk if date_it_wk else '無資料'})*")
    if not live_it_wk.empty:
        st.dataframe(live_it_wk, use_container_width=True)
    else:
        st.write("無資料")
# ==========================================
# 📊 【蜂蜜計數器】本站累計觀測人次統計
# ==========================================
st.write("---")
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
