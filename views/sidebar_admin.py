# views/sidebar_admin.py
import streamlit as st
import pandas as pd
import os
from views.b1_page import fetch_github_json_down

def render_global_admin_sidebar(DATA_DIR):
    # 建立專屬的歷史快照資料夾
    snapshot_dir = os.path.join(DATA_DIR, "history_snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    
    # 放置於側邊欄最底部
    with st.sidebar.expander("🛠️ 站長快照總管 (全站儲存)", expanded=False):
        admin_pw = st.text_input("解鎖全站快照功能", type="password", key="global_admin_pw_input")
        expected_pw = st.secrets["passwords"]["b1_admin"]
        
        if admin_pw == expected_pw:
            st.success("🔓 驗證成功！")
            snap_date = st.date_input("選擇這份資料的基準日(通常為今日)")
            
            if st.button("💾 一鍵儲存全站快照 (B1 + 全市場大表)", use_container_width=True, type="primary"):
                date_str = snap_date.strftime("%Y%m%d")
                
                with st.spinner("📦 正在將籌碼特徵封存至資料庫..."):
                    # --- 1. 處理 B1 正向數據 ---
                    json_dfs = st.session_state.get('b1_json_dfs', {})
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
                        save_path_up = os.path.join(DATA_DIR, f"{date_str}_JSON_History.csv")
                        snap_grouped_up.to_csv(save_path_up, index=False, encoding='utf-8-sig')
                        st.success(f"✅ B1 正向封存成功！({len(snap_grouped_up)} 檔)")

                    # --- 2. 處理 B1 負向數據 ---
                    current_down_dfs = fetch_github_json_down()
                    all_snap_down = []
                    for d in [5, 10, 20, 30]:
                        if d in current_down_dfs and not current_down_dfs[d].empty:
                            temp = current_down_dfs[d].copy()
                            temp['上榜區塊'] = f"{d}日衰退"
                            all_snap_down.append(temp)
                            
                    if all_snap_down:
                        snap_df_down = pd.concat(all_snap_down, ignore_index=True)
                        snap_grouped_down = snap_df_down.groupby(['股票代號', '股票名稱']).agg({
                            '法人持股': 'max', '上榜區塊': lambda x: ",".join(set(x)), '累積衰退': 'first'
                        }).reset_index()
                        save_path_down = os.path.join(DATA_DIR, f"{date_str}_Down_History.csv")
                        snap_grouped_down.to_csv(save_path_down, index=False, encoding='utf-8-sig')
                        st.success(f"✅ B1 負向封存成功！({len(snap_grouped_down)} 檔)")

                    # --- 3. 處理 B0~B8 全市場大表 ---
                    # 💡 雙重保險：如果 b8_master_dataframe 被清空，就去抓 debug_df
                    master_df = st.session_state.get('b8_master_dataframe')
                    if master_df is None or master_df.empty:
                        master_df = st.session_state.get('debug_df')
                    
                    if master_df is not None and not master_df.empty:
                        # ⚠️ 防呆機制：將所有欄位轉為字串或數字，避免 Parquet 遇到串列 (List) 格式報錯
                        for col in master_df.columns:
                            if master_df[col].dtype == object:
                                master_df[col] = master_df[col].astype(str)
                                
                        pq_path = os.path.join(snapshot_dir, f"Master_Snapshot_{date_str}.parquet")
                        pq_path = os.path.join(snapshot_dir, f"Master_Snapshot_{date_str}.parquet")
                        master_df.to_parquet(pq_path, index=False)
                        
                        csv_path = os.path.join(snapshot_dir, f"Master_Snapshot_{date_str}.csv")
                        master_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        
                        st.success(f"🚀 全市場特徵快照 (Parquet/CSV) 封存成功！({len(master_df)} 檔)")
                    else:
                        st.error("❌ 找不到全市場大表。請先至網頁點擊運算按鈕產生數據後，再來點擊儲存。")
                        
                    st.balloons()
        elif admin_pw != "":
            st.error("❌ 密碼錯誤")
