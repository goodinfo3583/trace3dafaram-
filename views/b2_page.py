# views/b2_page.py
import streamlit as st
import pandas as pd
import os
import glob
import re

def extract_date_from_name(filename):
    """從檔名萃取 8 碼日期 (202XXXXX)"""
    match = re.search(r'(202\d{5})', str(filename))
    return match.group(1) if match else "00000000"

# ==========================================
# ⚙️ 後台資料引擎 (Data Engine)：專責運算並寫入 Session
# ==========================================
def sync_b2_data(DATA_DIR):
    """只在背景讀取 B2 資料並寫入 session_state，絕對不繪製任何 UI，確保極速運作"""
    
    # --- 2-1：外資 5 日買超 ---
    files_21 = sorted(glob.glob(os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")), reverse=True)[:10]
    if files_21:
        base_df = None
        today_data = {}
        for idx, f in enumerate(files_21):
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
                id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
                name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
                df = df.rename(columns={id_col: '代號', name_col: '名稱'})
                df['代號'] = df['代號'].astype(str).str.strip()
                df['名稱'] = df['名稱'].astype(str).str.strip()
                
                d_label = extract_date_from_name(f)[-4:]
                col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
                col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
                
                if idx == 0 and col_today:
                    today_data = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
                if col_5d:
                    df_s = df[['代號', '名稱', col_5d]].copy().rename(columns={col_5d: f"{d_label}成交比%"})
                    base_df = df_s if base_df is None else pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            except: continue

        if base_df is not None:
            csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
            latest_col = f"{extract_date_from_name(files_21[0])[-4:]}成交比%"
            if latest_col in csv_display.columns:
                csv_display[latest_col] = pd.to_numeric(csv_display[latest_col].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_col, ascending=False)
                
                def eval_cont(row):
                    today = today_data.get(row['股票代號'], 0)
                    base = pd.to_numeric(row.get(latest_col, 0), errors='coerce')
                    val_str = "(無資料)" if pd.isna(today) else f"({today}%)"
                    if pd.isna(today): return f"⚪ 觀望 {val_str}"
                    if today > 0: return f"{'🔥 強延續' if today > base else '⚠️ 趨緩'} {val_str}"
                    elif today < 0: return f"{'🚨 劇烈倒貨' if abs(today) > abs(base) else '📉 調節洗盤'} {val_str}"
                    return f"🔄 持平 {val_str}"
                
                csv_display['今日短動態'] = csv_display.apply(eval_cont, axis=1)
                cols = ["股票代號", "股票名稱", "今日短動態"] + [c for c in csv_display.columns if "成交比%" in c]
                # 💡 修正 Bug：將「未過濾的完整資料」存入，確保觀察名單能讀到所有標的
                st.session_state['df_blk2_1'] = csv_display[cols].copy()

    # --- 2-2：投信 5 日買超 ---
    files_22 = sorted(glob.glob(os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")), reverse=True)[:10]
    if files_22:
        base_df = None
        today_data = {}
        for idx, f in enumerate(files_22):
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
                df = df.rename(columns={next((c for c in df.columns if '代號' in c), df.columns[0]): '代號', next((c for c in df.columns if '名稱' in c), df.columns[1]): '名稱'})
                df['代號'] = df['代號'].astype(str).str.strip()
                df['名稱'] = df['名稱'].astype(str).str.strip()
                d_label = extract_date_from_name(f)[-4:]
                col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
                col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
                
                if idx == 0 and col_today: today_data = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
                if col_5d:
                    df_s = df[['代號', '名稱', col_5d]].copy().rename(columns={col_5d: f"{d_label}成交比%"})
                    base_df = df_s if base_df is None else pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            except: continue

        if base_df is not None:
            csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
            latest_col = f"{extract_date_from_name(files_22[0])[-4:]}成交比%"
            if latest_col in csv_display.columns:
                csv_display[latest_col] = pd.to_numeric(csv_display[latest_col].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_col, ascending=False)
                def eval_cont(row):
                    today = today_data.get(row['股票代號'], 0)
                    base = pd.to_numeric(row.get(latest_col, 0), errors='coerce')
                    val_str = "(無資料)" if pd.isna(today) else f"({today}%)"
                    if pd.isna(today): return f"⚪ 觀望 {val_str}"
                    if today > 0: return f"{'🔥 強延續' if today > base else '⚠️ 趨緩'} {val_str}"
                    elif today < 0: return f"{'🚨 劇烈倒貨' if abs(today) > abs(base) else '📉 調節洗盤'} {val_str}"
                    return f"🔄 持平 {val_str}"
                csv_display['今日短動態'] = csv_display.apply(eval_cont, axis=1)
                cols = ["股票代號", "股票名稱", "今日短動態"] + [c for c in csv_display.columns if "成交比%" in c]
                st.session_state['df_blk2_2'] = csv_display[cols].copy()

    # --- 2-3：外資 5 日買超佔發行 ---
    files_23 = sorted(glob.glob(os.path.join(DATA_DIR, "*外資買超佔發行張數*.csv")), key=extract_date_from_name, reverse=True)[:10]
    if files_23:
        base_df = None
        date_labels = []
        today_data = {}
        for idx, f in enumerate(files_23):
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
                if '代號' not in df.columns or '名稱' not in df.columns: continue
                df['代號'], df['名稱'] = df['代號'].astype(str).str.strip(), df['名稱'].astype(str).str.strip()
                d_label = extract_date_from_name(f)[-4:]
                
                if idx == 0 and '當日買賣超佔發行張數' in df.columns:
                    today_data = dict(zip(df['代號'], pd.to_numeric(df['當日買賣超佔發行張數'], errors='coerce')))
                if '5日買賣超佔發行張數' in df.columns:
                    df_s = df[['代號', '名稱', '5日買賣超佔發行張數']].copy().rename(columns={'5日買賣超佔發行張數': f"{d_label}發行數%"})
                    base_df = df_s if base_df is None else pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
                date_labels.append(d_label)
            except: continue

        if base_df is not None and date_labels:
            csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
            latest_col = f"{date_labels[0]}發行數%"
            if latest_col in csv_display.columns:
                csv_display[latest_col] = pd.to_numeric(csv_display[latest_col].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_col, ascending=False)
                def judge_alert(row):
                    val_5d, val_today = row.get(latest_col, 0), today_data.get(row['股票代號'], 0)
                    if val_5d == 0 or val_5d == "未進榜": return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
                    if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
                    elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
                    return "🔄 今日量縮持平"
                csv_display['今日短動態'] = csv_display.apply(judge_alert, axis=1)
                history_cols = [c for c in csv_display.columns if "發行數%" in c]
                st.session_state['df_blk2_3'] = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols].copy()

    # --- 2-4：投信 5 日買超佔發行 ---
    files_24 = sorted(glob.glob(os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")), key=extract_date_from_name, reverse=True)[:10]
    if files_24:
        base_df = None
        date_labels = []
        today_data = {}
        for idx, f in enumerate(files_24):
            try:
                df = pd.read_csv(f, encoding='utf-8-sig')
                df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
                if '代號' not in df.columns or '名稱' not in df.columns: continue
                df['代號'], df['名稱'] = df['代號'].astype(str).str.strip(), df['名稱'].astype(str).str.strip()
                d_label = extract_date_from_name(f)[-4:]
                
                if idx == 0 and '當日買賣超佔發行張數' in df.columns:
                    today_data = dict(zip(df['代號'], pd.to_numeric(df['當日買賣超佔發行張數'], errors='coerce')))
                if '5日買賣超佔發行張數' in df.columns:
                    df_s = df[['代號', '名稱', '5日買賣超佔發行張數']].copy().rename(columns={'5日買賣超佔發行張數': f"{d_label}發行數%"})
                    base_df = df_s if base_df is None else pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
                date_labels.append(d_label)
            except: continue

        if base_df is not None and date_labels:
            csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
            latest_col = f"{date_labels[0]}發行數%"
            if latest_col in csv_display.columns:
                csv_display[latest_col] = pd.to_numeric(csv_display[latest_col].replace("未進榜", 0), errors='coerce').fillna(0)
                csv_display = csv_display.sort_values(by=latest_col, ascending=False)
                def judge_alert(row):
                    val_5d, val_today = row.get(latest_col, 0), today_data.get(row['股票代號'], 0)
                    if val_5d == 0 or val_5d == "未進榜": return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
                    if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
                    elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
                    return "🔄 今日量縮持平"
                csv_display['今日短動態'] = csv_display.apply(judge_alert, axis=1)
                history_cols = [c for c in csv_display.columns if "發行數%" in c]
                st.session_state['df_blk2_4'] = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols].copy()

# ==========================================
# 🖼️ 前台畫面渲染 (Views)：負責畫圖與 Checkbox
# ==========================================
def show_b2_page(DATA_DIR):
    """B2 專屬頁面 UI 渲染"""
    # 確保記憶體裡有資料 (如果還沒存過，就當場算一次)
    if 'df_blk2_1' not in st.session_state:
        sync_b2_data(DATA_DIR)

    # 2-1 渲染
    st.write("---")
    st.markdown("<div id='section-2-1'></div>", unsafe_allow_html=True)
    st.header("法人掃貨：外資 5 日 買超佔標的成交量")
    
    df_21 = st.session_state.get('df_blk2_1')
    if df_21 is not None and not df_21.empty:
        st.info("動態 🔥 強延續 (買盤加速) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (強烈賣出)")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="fo_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="fo_bond_v9")
        
        mask = (df_21['股票代號'].str.len() == 4)
        if show_etf: mask |= ((df_21['股票代號'].str.len() >= 5) & (~df_21['股票代號'].str.endswith('B')))
        if show_bond: mask |= df_21['股票代號'].str.endswith('B')
        
        display_df = df_21[mask].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("⚠️ 記憶體中無 2-1 數據。")

    # 2-2 渲染
    st.write("---")
    st.markdown("<div id='section-2-2'></div>", unsafe_allow_html=True)
    st.header("法人掃貨：投信 5 日 買超佔標的成交量")
    
    df_22 = st.session_state.get('df_blk2_2')
    if df_22 is not None and not df_22.empty:
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_v9")
        
        mask = (df_22['股票代號'].str.len() == 4)
        if show_etf: mask |= ((df_22['股票代號'].str.len() >= 5) & (~df_22['股票代號'].str.endswith('B')))
        if show_bond: mask |= df_22['股票代號'].str.endswith('B')
        
        display_df = df_22[mask].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("⚠️ 記憶體中無 2-2 數據。")

    # 2-3 渲染
    st.write("---")
    st.markdown("<div id='section-2-3'></div>", unsafe_allow_html=True)
    st.header("法人掃貨：外資 5 日 買超佔公司發行張數")
    
    df_23 = st.session_state.get('df_blk2_3')
    if df_23 is not None and not df_23.empty:
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="foreign_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="foreign_bond_final_v3")
        
        mask = (df_23['股票代號'].str.len() == 4)
        if show_etf: mask |= ((df_23['股票代號'].str.len() >= 5) & (~df_23['股票代號'].str.endswith('B')))
        if show_bond: mask |= df_23['股票代號'].str.endswith('B')
        
        display_df = df_23[mask].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("⚠️ 記憶體中無 2-3 數據。")

    # 2-4 渲染
    st.write("---")
    st.markdown("<div id='section-2-4'></div>", unsafe_allow_html=True)
    st.header("法人掃貨：投信 5 日 買超佔公司發行張數")
    
    df_24 = st.session_state.get('df_blk2_4')
    if df_24 is not None and not df_24.empty:
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_final_v3")
        
        mask = (df_24['股票代號'].str.len() == 4)
        if show_etf: mask |= ((df_24['股票代號'].str.len() >= 5) & (~df_24['股票代號'].str.endswith('B')))
        if show_bond: mask |= df_24['股票代號'].str.endswith('B')
        
        display_df = df_24[mask].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("⚠️ 記憶體中無 2-4 數據。")
