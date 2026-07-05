import streamlit as st
import requests
import time
import math
import left_panel
# ==========================================
# 1. 網頁基本設定 & 召喚視覺魔法
# ==========================================
# 為這個分頁設定專屬的標題
st.set_page_config(page_title="市場消息 | 股市派對", layout="wide")

# 🌟 一鍵套用您在 ui.py 寫好的背景、螢火蟲與跑馬燈！
import ui
ui.setup_all_effects()

# ==========================================
# 2. 背景快取引擎：負責去 GitHub 搬運多天份的資料
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_historical_news(days_to_load=3):
    base_url = "https://raw.githubusercontent.com/voidful/tw_news_stocker/main/docs/data"
    cache_buster = int(time.time() / 600) 
    index_url = f"{base_url}/news_index.json?t={cache_buster}"
    
    all_news = []
    
    try:
        index_res = requests.get(index_url)
        index_res.raise_for_status()
        news_dates = index_res.json()
        
        news_dates.sort(reverse=True)
        target_dates = news_dates[:days_to_load]
        
        for date in target_dates:
            data_url = f"{base_url}/news/{date}.json?t={cache_buster}"
            res = requests.get(data_url)
            if res.status_code == 200:
                day_data = res.json()
                all_news.extend(day_data)
                
        return all_news, target_dates
    except Exception as e:
        return [], []

# ==========================================
# 3. 📰 定義：市場消息主畫面分頁
# ==========================================
def show_news_page():
    st.title("市場消息")
    
    # 頂部控制面板
    col1, col2 = st.columns([1, 2])
    with col1:
        days_option = st.selectbox("載入歷史天數", [1, 3, 7, 14, 30, 90, 180, 365], index=0)
    with col2:
        search_query = st.text_input("🔍 搜尋市場新聞標題、關鍵字或股票代號...")
        
    st.markdown("---")
    
    # 呼叫快取引擎取得資料
    with st.spinner(f"正在從資料庫撈取近 {days_option} 天的新聞 (若選擇 365 天，首次載入約需 30 秒，請稍候)..."):
        news_data, loaded_dates = fetch_historical_news(days_option)
        
    if not news_data:
        st.error("無法取得新聞資料，請檢查網路連線。")
        return

    date_range_str = f"{loaded_dates[-1]} ~ {loaded_dates[0]}" if len(loaded_dates) > 1 else loaded_dates[0]
    
    # ==========================================
    # 🎨 注入 CSS 樣式
    # ==========================================
    glass_css = """
    <style>
    .glass-card {
        background: rgba(255, 255, 255, 0.15); 
        backdrop-filter: blur(10px);          
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08); 
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);   
        transition: all 0.2s ease-in-out;
    }
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.09);     
        transform: translateY(-2px);
    }
    .news-title {
        font-size: 16px; 
        font-weight: 400;
        color: #E0E0E0;  
        text-decoration: none;
        line-height: 1.4;
        display: block;
        margin-bottom: 8px;
    }
    .news-title:hover {
        color:  #FFE153;  
    }
    .news-info {
        font-size: 13px;
        color: #94A3B8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .code-tag {
        background: rgba(59, 130, 246, 0.15); 
        color: #60A5FA;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        margin-left: 5px;
        font-weight: 600;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    </style>
    """
    st.markdown(glass_css, unsafe_allow_html=True)
    
    # 執行全域過濾與排序
    try:
        sorted_news = sorted(news_data, key=lambda x: x.get("ts", ""), reverse=True)
    except:
        sorted_news = news_data

    filtered_news = []
    for news in sorted_news:
        title = news.get("title", "")
        codes = news.get("codes", [])
        
        if search_query:
            q = search_query.lower()
            match_title = q in title.lower()
            match_code = any(q in str(c).lower() for c in codes)
            if not (match_title or match_code):
                continue 
                
        filtered_news.append(news)

    total_items = len(filtered_news)
    
    if total_items == 0:
        st.warning(f"找不到包含「{search_query}」的新聞，建議增加上方的「載入歷史天數」再試一次！")
        return

    # 分頁系統 (Pagination)
    ITEMS_PER_PAGE = 50
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE) 
    
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p2:
        current_page = st.number_input(
            f"📄 選擇頁數 (共 {total_pages} 頁)", 
            min_value=1, 
            max_value=total_pages, 
            value=1, 
            step=1
        )
        
    start_item = (current_page - 1) * ITEMS_PER_PAGE + 1
    end_item = min(current_page * ITEMS_PER_PAGE, total_items)
    st.caption(f"<div style='text-align: center; color: #94A3B8; margin-bottom: 20px;'>共 {total_items} 則新聞，目前顯示第 {start_item} 到 {end_item} 則，千萬不要僅憑新聞操作買賣</div>", unsafe_allow_html=True)

    # 渲染卡片
    start_idx = (current_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    display_news = filtered_news[start_idx:end_idx] 

    for news in display_news:
        title = news.get("title", "")
        codes = news.get("codes", [])
        
        codes_html = ""
        if codes:
            codes_html = "".join([f"<span class='code-tag'>{c}</span>" for c in codes])
        
        link = news.get('link', '#')
        host = news.get('source_host', '未知')
        
        ts = news.get('ts', '')
        if "T" in ts:
            ts = ts.split("T")[0] + " " + ts.split("T")[1][:5]
        
        card_html = f"""
        <div class="glass-card">
            <a href="{link}" target="_blank" class="news-title">{title}</a>
            <div class="news-info">
                <span>來源: {host} &nbsp;|&nbsp; 時間: {ts}</span>
                <div>{codes_html}</div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)        

# ==========================================
# 4. 🚀 啟動畫面！ (直接呼叫，不需 if 判斷)
# ==========================================
show_news_page()
