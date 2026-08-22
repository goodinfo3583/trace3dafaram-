#test_web.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import glob
import re
import datetime
import requests  
import pytz  
import math
import streamlit.components.v1 as components
import plotly.express as px
from components import style_manager
from components import nav_manager
# 定義修改路徑呼叫工具函式
from utils.data_utils import (
    STOCK_DICT, extract_date_from_name, robust_read_csv, get_latest_csv, get_prev_csv, get_diff_ui
)
# 頁面模組或新增其他頁面模組
from views.login_page import show_login_page
from views.news_page import show_news_page
from views.contact_page import show_contact_page
from views.pool_page import show_pool_page
from views.sidebar import render_sidebar_war_room
from views.b1_page import show_b1_page, sync_b1_data
from views.b2_page import show_b2_page, sync_b2_data
from views.b3_page import show_b3_page, sync_b3_data
from views.b4_page import show_b4_page, sync_b4_data
from views.b5_page import show_b5_page, sync_b5_data
from views.b6_page import show_b6_page, sync_b6_data
from views.b7_page import show_b7_page, sync_b7_data
from views.watchlist_page import show_watchlist_page
# ==========================================
# 1. 網頁基本設定 & 目錄路徑初始化
# ==========================================
st.set_page_config(page_title="股市派對", layout="wide")
# 集中所有路徑變數
DATA_DIR = "./data"
SCORE_HISTORY_DIR = os.path.join(DATA_DIR, "ScoreHistory")
MARKET_HISTORY_DIR = os.path.join(DATA_DIR, "MarketHistory")
BLOCK_HISTORY_DIR = os.path.join(DATA_DIR, "BlockHistory")

# 隱形急救引擎 (置於程式最頂端，不要刪除)
# 加上 exist_ok=True，徹底消滅 FileExistsError
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SCORE_HISTORY_DIR, exist_ok=True)
os.makedirs(MARKET_HISTORY_DIR, exist_ok=True)
os.makedirs(BLOCK_HISTORY_DIR, exist_ok=True)

# ✨ 修改 ：在載入畫面之前，確保 B3 數據已經存在記憶體中供卡片/跑馬燈使用
if 'df_blk2_1' not in st.session_state:
    sync_b2_data(DATA_DIR)
if 'b3_data' not in st.session_state:
    sync_b3_data(DATA_DIR)
if 'b4_squeeze_radar' not in st.session_state:
    sync_b4_data(DATA_DIR)
if 'b5_1000' not in st.session_state:
    sync_b5_data(DATA_DIR)
# 呼叫渲染視覺元件 components
style_manager.load_global_css()
style_manager.set_background("./image/派對盛宴邀請.png")
style_manager.render_fireflies()
style_manager.render_marquee() # 呼叫頂層圖片跑馬燈與懸浮玻璃卡片
try:
    # 呼叫 B3 法人連買卡片 (藍色光暈，右上方)
    style_manager.render_top10_glass_card() 
    # 呼叫 B2 法人掃貨卡片 (紅色光暈，右下方)
    style_manager.render_b2_top10_glass_card()
    # 呼叫 B4 軋空/套牢雷達卡片 (左上方)
    style_manager.render_b4_top10_glass_card()
    # 呼叫 B5 大腿雙向共振卡片 (左下方)
    style_manager.render_b5_top10_glass_card()
    # 呼叫 系統設定 懸浮卡片 (置中全螢幕遮罩)
    style_manager.render_settings_modal()
    # 呼叫 課程NPC 懸浮卡片 (右下方)
    style_manager.render_course_npc()   
except AttributeError as e:
    # 避免尚未存檔完成時當機
    print(f"UI 渲染警告: {e}")
    pass

# 注入客製化頂部導覽列
# nav_manager.inject_custom_header()
is_logged_in = st.session_state.get("logged_in", False)
nav_manager.inject_custom_header(is_logged_in)
# ==========================================
# 2. 啟動 Google Sheets 連線與目錄初始化
# ==========================================
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TxHDahg8ul6lmUtDN-7X75cBXbkU0jaZ3M9zg6exBgU"



# 定義路徑
backup_df_path = os.path.join(DATA_DIR, "sidebar_twse_df_backup.csv")
backup_margin_path = os.path.join(DATA_DIR, "sidebar_margin_backup.csv")

# 補法人備援
if not os.path.exists(backup_df_path):
    pd.DataFrame({
        '單位名稱': ['合計'], '買賣差額': ['102770738307']}).to_csv(backup_df_path, index=False, encoding='utf-8-sig')
# 補融資備援
if not os.path.exists(backup_margin_path):
    pd.DataFrame([{"today_bal": 556359646.0, "prev_bal": 535025764.0}]).to_csv(backup_margin_path, index=False, encoding='utf-8-sig')

# ==========================================
# 3. 網頁首頁路由控制中心 (極速切換引擎)-首頁設定
# ==========================================
current_page = st.query_params.get("page", "b1")

# 頁面渲染分流 (路由中心)
if current_page == "all":
    # 在觀察名單按下「全市場掃描」後觸發的背景引擎
    with st.spinner("🚀 背景全市場數據高速運算中..."):
        sync_b1_data(DATA_DIR)
        sync_b2_data(DATA_DIR)           # 在背景後台算好 b2
        sync_b3_data(DATA_DIR)
        sync_b4_data(DATA_DIR)
        sync_b5_data(DATA_DIR)
        sync_b6_data(DATA_DIR)
        sync_b7_data(DATA_DIR)
        # 算完後，把使用者自動傳送回觀察名單
        # 新增其他計分頁面b7,b8...
        st.session_state.current_page = "pool"
        st.query_params["page"] = "pool"
        st.rerun()
# 頁面渲染分流
if current_page == "news":
    show_news_page()
elif current_page == "login":
    from views.login_page import show_login_page # 將您在 test_web.py 開頭宣告的 conn 和 SHEET_URL 傳進去     
    show_login_page(conn, SHEET_URL)
elif current_page == "contact":
    show_contact_page(conn, SHEET_URL)
elif current_page == "pool":
    show_pool_page(conn, SHEET_URL, DATA_DIR, STOCK_DICT)
elif current_page == "b1":
    show_b1_page(DATA_DIR, STOCK_DICT)
elif current_page == "b2":
    show_b2_page(DATA_DIR)
elif current_page == "b3":
    show_b3_page(DATA_DIR)
elif current_page == "b4":
    show_b4_page(DATA_DIR)
elif current_page == "b5":
    show_b5_page(DATA_DIR, STOCK_DICT) 
elif current_page == "b6":
    show_b6_page(DATA_DIR)
elif current_page == "b7":
    show_b7_page(DATA_DIR, STOCK_DICT)
elif current_page == "watchlist":                    # 👈 新增
    show_watchlist_page(STOCK_DICT, conn, SHEET_URL) # 👈 新增
# 渲染側邊欄
with st.sidebar:
    render_sidebar_war_room(STOCK_DICT, DATA_DIR)

# ==========================================
# 🏠 核心五大 區塊1-5原始碼位置
# ==========================================
# ==========================================
# 🎭 幕後無縫換頁引擎 (放在最後)
# ==========================================
# 如果程式順利走到這裡(沒有被上面的 st.stop 攔截)，就渲染按鈕
nav_manager.render_proxy_buttons()
