# views/sidebar_admin.py
import streamlit as st
import pandas as pd
import os
from views.b1_page import fetch_github_json_down

def render_global_admin_sidebar(DATA_DIR):
    # 建立專屬的歷史快照資料夾 (這是存在專案程式碼後台的資料夾)
    snapshot_dir = os.path.join(DATA_DIR, "history_snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    
    # 放置於側邊欄最底部
    with st.sidebar.expander("🛠️ 站長快照總管 (全站儲存)", expanded=False):
        admin_pw = st.text_input("解鎖全站快照功能", type="password", key="global_admin_pw_input")
        expected_pw = st.secrets["passwords"]["b1_admin"]
        
        if admin_pw == expected_pw:
            st.success("🔓 驗證成功！")
            snap_date = st.date_input("選擇這份資料的基準日(通常為今日)")
            date_str = snap_date.strftime("%Y%m%d")
            
            st.markdown("---")
            
            # ==========================================
            # 👁️ 記憶體監視器：讓你知道現在到底抓到什麼資料
            # ==========================================
            master_df = st.session_state.get('b8_master_dataframe')
            if master_df is None or master_df.empty:
                master_df = st.session_state.get('debug_df')
                
            if master_df is not None and not master_df.empty:
                st.info(f"📊 記憶體狀態：已捕捉大表 **{len(master_df)}** 檔")
                
                # 👇 新增這行：讓系統印出真實的硬碟絕對路徑
                st.caption(f"📁 後台預計存檔位置： `{os.path.abspath(snapshot_dir)}`")
            else:
                st.warning("⚠️ 記憶體尚未捕捉大表 (請先至回測頁面產生資料)")
                

            # ==========================================
            # 💾 動作一：寫入後台系統資料庫
            # ==========================================
            if st.button("💾 封存至系統資料庫 (供未來AI使用)", use_container_width=True, type="primary"):
                with st.spinner("📦 正在將籌碼特徵封存至後台資料夾..."):
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
                        st.success(f"✅ B1 正向封存至後台！({len(snap_grouped_up)} 檔)")

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
                        st.success(f"✅ B1 負向封存至後台！({len(snap_grouped_down)} 檔)")

                    # --- 3. 處理 B0~B8 全市場大表 ---
                    if master_df is not None and not master_df.empty:
                        # ⚠️ 防呆機制：將所有欄位轉為字串或數字，避免 Parquet 格式報錯
                        clean_master_df = master_df.copy()
                        for col in clean_master_df.columns:
                            if clean_master_df[col].dtype == object:
                                clean_master_df[col] = clean_master_df[col].astype(str)
                                
                        pq_path = os.path.join(snapshot_dir, f"Master_Snapshot_{date_str}.parquet")
                        clean_master_df.to_parquet(pq_path, index=False)
                        
                        csv_path = os.path.join(snapshot_dir, f"Master_Snapshot_{date_str}.csv")
                        clean_master_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        
                        st.success(f"🚀 全市場特徵大表 封存至後台！({len(clean_master_df)} 檔)")
                    
                    st.balloons()
            
            # ==========================================
            # 📥 動作二：實體下載區 (直接存到你的實體電腦 Downloads 資料夾)
            # ==========================================
            st.markdown("---")
            st.markdown("<div style='font-size:14px; font-weight:bold; color:#00E272;'>📥 手動下載至個人電腦 (雲端專用)</div>", unsafe_allow_html=True)
            
            if master_df is not None and not master_df.empty:
                col_down1, col_down2 = st.columns(2)
                
                with col_down1:
                    # 建立全市場大表的 CSV 下載按鈕
                    csv_buffer = master_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label=f"💾 下載 CSV ({len(master_df)}檔)",
                        data=csv_buffer,
                        file_name=f"Master_Snapshot_{date_str}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                with col_down2:
                    # 👇 新增：建立全市場大表的 Parquet 下載按鈕
                    import io
                    # 防呆：確保欄位為字串，避免 Parquet 轉換失敗
                    clean_master_df = master_df.copy()
                    for col in clean_master_df.columns:
                        if clean_master_df[col].dtype == object:
                            clean_master_df[col] = clean_master_df[col].astype(str)
                            
                    parquet_buffer = io.BytesIO()
                    clean_master_df.to_parquet(parquet_buffer, index=False)
                    st.download_button(
                        label=f"📦 下載 Parquet ({len(master_df)}檔)",
                        data=parquet_buffer.getvalue(),
                        file_name=f"Master_Snapshot_{date_str}.parquet",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
            else:
                st.write("*(尚未產生大表，無法下載)*")
