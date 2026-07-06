import streamlit as st
import pandas as pd
import os
import glob
import re
import datetime
import html
import plotly.express as px
import data_engine # 引入我們剛剛搬運的強大數據引擎

# 確保讀取全域的股票字典 (產業判定會用到)
if 'STOCK_DICT' not in globals():
    try:
        from data_engine import load_stock_dict
        STOCK_DICT = load_stock_dict()
    except:
        STOCK_DICT = {}

st.set_page_config(page_title="法人動向追蹤", page_icon="👑", layout="wide")

# ==========================================
# 🚀 資料讀取與快取綁定
# ==========================================
with st.spinner("🚀 正在從 GitHub 與本地資料庫編譯法人歷史軌跡母表..."):
    json_dfs, latest_all_df = data_engine.fetch_github_json_all()
    final_df, sorted_dates, date_cols, color_ref = data_engine.build_block1_master_df()
    
    # 存入 session_state 給側邊欄戰情室使用！
    st.session_state['my_final_df'] = final_df

# ==========================================
# 🏠 畫面渲染開始
# ==========================================
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)

if sorted_dates:
    latest_d = sorted_dates[0]
    fmt_date = f"{latest_d[:4]}/{latest_d[4:6]}/{latest_d[6:]}"
    st.markdown(
        f"<h2 style='margin-bottom: 0px;'>👑 法人動向：三大法人短中長線持股比追蹤 "
        f"<span style='color:#00D2FF; font-size:16px; font-weight:500; margin-left:12px;'>基準日：{fmt_date}</span></h2>", 
        unsafe_allow_html=True
    )
else:
    st.markdown("<h2 style='margin-bottom: 0px;'>👑 法人動向：三大法人短中長線持股比追蹤</h2>", unsafe_allow_html=True)

# ------------------------------------------
# 💾 站長專屬：JSON 200名快照存檔區
# ------------------------------------------
DATA_DIR = "./Goodinfo_Rankings"
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
    st.link_button("📊 台股法人籌碼追蹤(50名) GitHub Repo", "https://goodinfo3583.github.io/DDong_tw-institutional-stocker/", use_container_width=True)

with c_btn2:
    try: exp_container = st.popover(f"🛠 站長快照 ({status_text})", use_container_width=True)
    except AttributeError: exp_container = st.expander(f"🛠 站長：下載 200名快照 ({status_text})", expanded=False)
        
    with exp_container:
        if is_updated_today: st.success(f"✅ **今日已更新！** 資料夾中最新快照為 `{local_latest_date}`。")
        else: st.warning(f"⚠️ **今日尚未更新！** 資料夾中最新快照停留在 `{local_latest_date}`，請記得下載！")
            
        admin_pw = st.text_input("請輸入站長密碼以解鎖功能", type="password", key="admin_pw_input")
        if admin_pw == "DDong888": 
            st.success("🔓 驗證成功！請執行快照封存。")
            
            if st.button("🔄 站長專屬：強制抓取 GitHub 最新數據", use_container_width=True):
                data_engine.fetch_github_json_all.clear() # 👉 自動呼叫引擎層的清除快取
                st.rerun()                     
            
            snap_date = st.date_input("選擇這份資料的實際基準日")
            st.write("")
            if st.button("💾 將 GitHub 200名數據封存為 CSV", use_container_width=True):
                date_str = snap_date.strftime("%Y%m%d")
                save_path = os.path.join(DATA_DIR, f"{date_str}_JSON_History.csv")
                all_snap_data = []
                for d in [5, 20, 60, 120]:
                    if d in json_dfs and not json_dfs[d].empty:
                        temp = json_dfs[d][['股票代號', '股票名稱', '法人持股']].copy()
                        temp['上榜區塊'] = f"{d}日"
                        all_snap_data.append(temp)
                
                if all_snap_data:
                    snap_df = pd.concat(all_snap_data, ignore_index=True)
                    snap_grouped = snap_df.groupby(['股票代號', '股票名稱']).agg({
                        '法人持股': 'max', '上榜區塊': lambda x: ",".join(set(x))
                    }).reset_index()
                    csv_data = snap_grouped.to_csv(index=False).encode('utf-8-sig')
                    snap_grouped.to_csv(save_path, index=False, encoding='utf-8-sig')
                    
                    data_engine.build_block1_master_df.clear() # 👉 呼叫引擎層清空母表快取
                    st.success(f"✅ 成功生成 {len(snap_grouped)} 檔股票的歷史快照！")
                    st.download_button(
                        label="📥 點我下載快照 CSV 檔案", data=csv_data, file_name=f"{date_str}_JSON_History.csv",
                        mime="text/csv", type="primary", use_container_width=True
                    )
                else: st.error("❌ 尚未獲取到 GitHub 數據，封存失敗。")
        elif admin_pw != "": st.error("❌ 密碼錯誤，無法使用此功能。")

# ==========================================
# 🔧 UI 數據渲染 (四大榜單完美還原期程排序)
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
# 📊 繪圖區塊 ：產業聚落與資金輪動板塊 (Treemap)
# ==========================================
st.write("---")
st.markdown("### 🧩 資金聚落板塊：三大法人進榜產業分佈")
st.caption("透過區塊面積大小，觀察法人資金集中攻擊哪些產業。")

df_b1_master = st.session_state.get('my_final_df', pd.DataFrame())

if not df_b1_master.empty and 'STOCK_DICT' in globals() and STOCK_DICT:
    st.write("") 
    c_opt, c_search = st.columns([2.5, 1.5])
    with c_opt:
        top_n_option = st.radio("設定觀測範圍：", ["顯示前 50 名", "顯示前 200 名"], horizontal=True)
        top_n = 50 if "50" in top_n_option else 200
        
    with c_search:
        treemap_search = st.text_input("🔍 板塊內標的搜尋", placeholder="輸入代號/名稱以聚焦...", label_visibility="visible")

    tab_5, tab_20, tab_60, tab_120, tab_all = st.tabs(["🔴 5日排行", "🟡 20日排行", "🟢 60日排行", "🔵 120日排行", "🌟 綜合熱力池"])

    def render_period_treemap(period_days):
        if period_days == "all":
            has_tag = df_b1_master['今日上榜'].astype(str).str.strip() != ""
            period_df = df_b1_master[has_tag].copy()
            
            if period_df.empty:
                st.info("⚪ 今日尚無任何標的上榜。")
                return
            
            period_df['熱力數值'] = pd.to_numeric(
                period_df['△'].astype(str).str.replace('+', '').str.replace('%', ''), 
                errors='coerce'
            ).fillna(0.0)
            
            period_df = period_df.nlargest(top_n, '熱力數值').copy()
            period_df['綜合△排名'] = period_df['熱力數值'].rank(ascending=False, method='min')
            rank_col = '綜合△排名'
            title_name = "🌟 綜合上榜熱力池"
            
        else:
            rank_col = f"{period_days}日排名"
            if rank_col not in df_b1_master.columns:
                st.info(f"⚪ 尚無 {period_days} 日排行資料。")
                return

            period_df = df_b1_master[df_b1_master[rank_col] > 0].nsmallest(top_n, rank_col).copy()

            if period_df.empty:
                st.info(f"⚪ {period_days} 日排行無符合資料。")
                return
            
            period_df['熱力數值'] = pd.to_numeric(
                period_df['△'].astype(str).str.replace('+', '').str.replace('%', ''), 
                errors='coerce'
            ).fillna(0.0)
            title_name = f"🏆 {period_days}日資金聚落"

        period_df['產業別'] = period_df['股票代號'].astype(str).apply(
            lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他")
        )
        period_df['產業別'] = period_df['產業別'].replace('', 'ETF / 債券 / 其他')
        period_df = period_df[period_df['產業別'] != 'ETF / 債券 / 其他']

        if period_df.empty:
            st.info("⚪ 剔除 ETF/債券 後無一般產業資料。")
            return

        if treemap_search:
            query = treemap_search.strip()
            period_df = period_df[
                period_df['股票代號'].astype(str).str.contains(query, case=False, na=False) | 
                period_df['股票名稱'].astype(str).str.contains(query, case=False, na=False)
            ]
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

        date_cols = sorted([c for c in period_df.columns if '持股%' in c], reverse=True)[:7]
        hover_columns = ['股票代號', '今日上榜', '最新動態', '單日△_格式化', rank_col] + date_cols

        custom_continuous_scale = [
            [0.0, "rgba(0, 230, 118, 0.85)"],  
            [0.5, "rgba(30, 41, 59, 0.95)"],   
            [1.0, "rgba(255, 75, 75, 0.85)"]   
        ]

        fig = px.treemap(
            period_df,
            path=[px.Constant(title_name), '產業別', '顯示名稱'],
            values='計數',                      
            color='熱力數值',                    
            color_continuous_scale=custom_continuous_scale, 
            color_continuous_midpoint=0,        
            hover_data=hover_columns
        )
        fig.update_coloraxes(showscale=False)

        rank_hover_label = "綜合△排行" if period_days == "all" else f"{period_days}日排行"
        hover_template = (
            '<b>%{label}</b><br>'
            '股票代號: %{customdata[0]}<br>'
            '今日上榜: %{customdata[1]}<br>'
            '最新動態: %{customdata[2]}<br>'
            '單日△: <b>%{customdata[3]}</b><br>'
            f'{rank_hover_label}: <b>第 %{{customdata[4]}} 名</b><br>' 
            '----------------<br>'
        )
        for i, col in enumerate(date_cols):
            clean_date = col.replace("持股%", "") 
            hover_template += f'{clean_date} 持股比: %{{customdata[{5+i}]}}%<br>'
        hover_template += '<extra></extra>'

        fig.update_traces(
            textinfo="label", 
            textfont=dict(color="white", size=14),
            marker=dict(line=dict(color='#0B0F19', width=2), pad=dict(t=35, l=10, r=10, b=10)),
            hovertemplate=hover_template
        )
        
        fig.update_layout(margin=dict(t=30, l=0, r=0, b=0), height=650, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="sans-serif"))
        st.plotly_chart(fig, use_container_width=True)

    with tab_5: render_period_treemap(5)
    with tab_20: render_period_treemap(20)
    with tab_60: render_period_treemap(60)
    with tab_120: render_period_treemap(120)
    with tab_all: render_period_treemap("all")

    # ==========================================
    # 🗑️ ETF 與債券懸停與變色模塊 
    # ==========================================
    is_etf = df_b1_master['股票代號'].astype(str).apply(
        lambda sid: STOCK_DICT.get(sid, {}).get("industry", "ETF / 債券 / 其他") in ["ETF / 債券 / 其他", ""]
    )
    on_list = df_b1_master['今日上榜'].astype(str).str.strip() != ""
    excluded_etfs = df_b1_master[is_etf & on_list].sort_values(by='股票代號')
    
    if not excluded_etfs.empty:
        st.write("")
        st.markdown("##### 🗑️ 本次已剔除的非一般產業 (ETF / 債券 / 指數)")
        st.caption("這些標的雖有強大法人資金進駐上榜，但已從上方產業聚落中剔除。**游標懸停於標籤可查看詳細 7 日明細。**")
        
        tags_html = ""
        date_cols_master = sorted([c for c in df_b1_master.columns if '持股%' in c], reverse=True)[:7]
        
        for _, r in excluded_etfs.iterrows():
            name = html.escape(str(r.get('股票名稱', '')), quote=True)
            sid = html.escape(str(r.get('股票代號', '')), quote=True)
            tag = html.escape(str(r.get('今日上榜', '無')), quote=True)
            dyn = html.escape(str(r.get('最新動態', '-')), quote=True)
            delta = r.get('△', 0.0)
            
            try: d_val = float(str(delta).replace('+', '').replace('%', ''))
            except: d_val = 0.0
                
            if d_val > 0:
                bg_color, border_color, text_color, d_str = "rgba(255, 75, 75, 0.15)", "rgba(255, 75, 75, 0.4)", "#FF4B4B", f"+{d_val:.2f}"
            elif d_val < 0:
                bg_color, border_color, text_color, d_str = "rgba(0, 230, 118, 0.15)", "rgba(0, 230, 118, 0.4)", "#00E676", f"{d_val:.2f}"
            else:
                bg_color, border_color, text_color, d_str = "rgba(30, 41, 59, 0.6)", "#334155", "#94A3B8", "0.00"
                
            tooltip_text = f"【{name}】&#10;股票代號: {sid}&#10;今日上榜: {tag}&#10;最新動態: {dyn}&#10;單日△: {d_str}&#10;----------------&#10;"
            for col in date_cols_master:
                clean_date = col.replace("持股%", "") 
                val = r.get(col, "0.00")
                tooltip_text += f"{clean_date} 持股比: {val}%&#10;"
            
            tags_html += f"<div title=\"{tooltip_text}\" style=\"background-color: {bg_color}; color: #E2E8F0; border: 1px solid {border_color}; padding: 6px 14px; border-radius: 20px; margin: 5px; display: inline-flex; align-items: center; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); cursor: help; transition: transform 0.2s;\">{name} ({sid}) <span style='color: {text_color}; font-weight: bold; margin-left: 8px;'>△ {d_str}</span></div>"
        
        st.markdown(f"<div style='margin-top: 5px; line-height: 2.4;'>{tags_html}</div>", unsafe_allow_html=True)

else:
    st.info("⚪ 尚無全市場大數據或找不到產業字典，請確認背景掃描引擎已啟動。")

# ==========================================
# 🕵️‍♂️ 雙引擎籌碼歷史軌跡 (內資推估 vs 外資大腿)
# ==========================================
st.write("---")
try:
    df_foreign = data_engine.load_foreign_ratio_data(DATA_DIR)
except AttributeError:
    st.warning("⚠️ 在 data_engine.py 中尚未定義 load_foreign_ratio_data。請確認您的外資引擎是否已搬運。")
    df_foreign = pd.DataFrame()

if not df_foreign.empty and final_df is not None and not final_df.empty:
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
            
            dom_display_cols = []
            for_display_cols = []
            
            for d in common_dates:
                tot_col = f'{d}持股%'
                for_col = f'外資持股_{d}'
                dom_col = f'內資_{d[-4:]}' 
                for_out_col = f'外資_{d[-4:]}'
                
                tot_val = df_calc[tot_col].apply(clean_pct)
                for_val = df_calc[for_col].apply(clean_pct)
                
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
                latest_dom_col = f'內資_{common_dates[0][-4:]}_raw'
                df_dom_sorted = df_calc.sort_values(by=latest_dom_col, ascending=False).head(40)
                st.dataframe(df_dom_sorted[base_cols + dom_display_cols], use_container_width=True, hide_index=True)
                
            with tab_for:
                st.markdown("##### 🔍 尋找「外資大腿」長線階梯建倉股")
                latest_for_col = f'外資_{common_dates[0][-4:]}_raw'
                df_for_sorted = df_calc.sort_values(by=latest_for_col, ascending=False).head(40)
                st.dataframe(df_for_sorted[base_cols + for_display_cols], use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ 找不到主表與外資表的共通日期，請確認資料是否已同步。")
