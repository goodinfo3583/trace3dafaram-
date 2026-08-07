#style_manager.py
import streamlit as st
import base64
import os
import random

def load_global_css():
    """載入全站共用的隱藏設定、縮排與暗黑護眼 CSS"""
    # 隱藏 Streamlit 預設選單與縮排
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        .block-container { padding-top: 0 rem; }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 網頁風格設計 (暗黑護眼化)
    dark_mode_css = """
        <style>
        .stApp { background-color: #0A0D14 !important; }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText { color: #E2E8F0 !important; }
        [data-testid="stAlert"] { background-color: transparent !important; border: 1px solid #2D3748 !important; }
        [data-testid="stSidebar"] { background-color: #111622 !important; border-right: 1px solid #1E293B; }
        .stTextInput>div>div>input { background-color: #1A202C !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }
        div[data-testid="stDataFrame"] { background-color: #111622 !important; border: 1px solid #1E293B !important; border-radius: 6px; }
        [data-testid="stSidebar"] a { color: #00D2FF !important; text-decoration: none !important; font-weight: 500 !important; letter-spacing: 0.5px; transition: all 0.3s ease; }
        [data-testid="stSidebar"] a:hover { color: #FFD700 !important; text-shadow: 0px 0px 8px rgba(255, 215, 0, 0.5); }
        .stButton > button, .stLinkButton > a {
            background-color: #1E293B !important; 
            color: #94A3B8 !important; 
            border: 1px solid #334155 !important;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover, .stLinkButton > a:hover {
            border-color: #00D2FF !important;
            color: #00D2FF !important;
            box-shadow: 0 0 8px rgba(0, 210, 255, 0.2);
        }
        </style>
    """
    st.markdown(dark_mode_css, unsafe_allow_html=True)

def set_background(image_path):
    """網站主視覺背景設定引擎"""
    try:
        with open(image_path, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()
            
        css = f"""
        <style>
        .stApp {{
            background-image: 
                linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.88)), 
                url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
        }}
        div[data-testid="stVerticalBlock"] > div[style*="border"] {{
            background-color: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(4px); 
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ 找不到背景圖片檔：{image_path}，請確認檔名與路徑是否完全正確。")

def render_fireflies():
    """純代碼動態螢火蟲引擎"""
    num_fireflies = 5 
    css_rules = []
    html_divs = []
    
    for i in range(num_fireflies):
        size = random.uniform(2, 5)          
        start_x = random.uniform(0, 100)     
        start_y = random.uniform(0, 100)     
        move_x = random.uniform(-20, 20)     
        move_y = random.uniform(-20, 20)     
        duration = random.uniform(10, 25)    
        delay = random.uniform(0, 10)        
        pulse_dur = random.uniform(2, 5)     
        
        css_rules.append(f"""
        .firefly-{i} {{
            position: absolute; width: {size}px; height: {size}px;
            left: {start_x}vw; top: {start_y}vh; background: #FFFFDF; border-radius: 50%;
            box-shadow: 0 0 {size*3}px {size}px rgba(255, 215, 0, 0.6);
            animation: drift-{i} {duration}s infinite ease-in-out {delay}s, flash-{i} {pulse_dur}s infinite ease-in-out {delay}s;
            opacity: 0;
        }}
        @keyframes drift-{i} {{
            0% {{ transform: translate(0px, 0px); }}
            25% {{ transform: translate({move_x}vw, {move_y}vh); }}
            50% {{ transform: translate({move_x/2}vw, {move_y*1.5}vh); }}
            75% {{ transform: translate({-move_x}vw, {move_y/2}vh); }}
            100% {{ transform: translate(0px, 0px); }}
        }}
        @keyframes flash-{i} {{
            0%, 100% {{ opacity: 0; }}
            50% {{ opacity: {random.uniform(0.5, 1.0)}; }}
        }}
        """)
        html_divs.append(f"<div class='firefly-{i}'></div>")
    
    full_code = f"""
    <style>
    .fireflies-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none; z-index: 1000; overflow: hidden;
    }}
    {''.join(css_rules)}
    </style>
    <div class="fireflies-container">{''.join(html_divs)}</div>
    """
    st.markdown(full_code, unsafe_allow_html=True)

def render_marquee():
    """跑馬燈區塊渲染"""
    def get_image_base64(image_path):
        with open(image_path, "rb") as image_file:
            data = image_file.read()
            mime_type = "image/gif" if image_path.lower().endswith('.gif') else "image/png"
            encoded_string = base64.b64encode(data).decode()
        return f"data:{mime_type};base64,{encoded_string}"

    image_folder = "static" 
    image_files = ["沙漠之城.png", "法人意向.png", "組合畫家.png", "組合化學晶礦.png", "鐵風堡b.png"]
    
    total_images = len(image_files)
    time_per_slide = 5  
    total_time = total_images * time_per_slide
    visible_percent = (1 / total_images) * 100 

    image_tags = ""
    delay_css = ""
    for i, img_name in enumerate(image_files):
        img_path = os.path.join(image_folder, img_name)
        if os.path.exists(img_path):
            b64 = get_image_base64(img_path)
            image_tags += f'<img class="slide slide-{i}" src="{b64}">'
            delay_css += f"    .slide-{i} {{ animation-delay: {i * time_per_slide}s; }}\n"
        else:
            st.error(f"系統找不到這張圖片：{img_path}")

    marquee_code = f"""
    <style>
        .slideshow-container {{
            position: relative; width: 800px; height: 100px;
            margin: 0 auto 10px auto; background-color: #0A0D14;
            display: flex; justify-content: center; align-items: center; overflow: hidden;
        }}
        .slide {{
            position: absolute; height: 100%; object-fit: contain; 
            visibility: hidden; opacity: 0; animation: cut {total_time}s infinite; 
        }}
    {delay_css}
        @keyframes cut {{
            0%, {visible_percent - 0.01:.2f}%   {{ visibility: visible; opacity: 1; }} 
            {visible_percent:.2f}%, 100%        {{ visibility: hidden; opacity: 0; }}  
        }}
    </style>
    <div class="slideshow-container">{image_tags}</div>
    """
    st.markdown(marquee_code, unsafe_allow_html=True)
    
def render_top5_glass_card():
    """渲染右側懸浮玻璃卡片 (可手動關閉，自動輪播外資/投信前5名)"""
    
    # 檢查 session_state 是否已有 b3_data 
    # (必須確保主程式或背景已跑過 sync_b3_data)
    if 'b3_data' not in st.session_state:
        return

    try:
        fo_day_df, _ = st.session_state['b3_data']['fo_day']
        it_day_df, _ = st.session_state['b3_data']['it_day']

        # 產生 Top 5 列表 HTML 的小幫手函數 (使用 to_dict 避免中文欄位讀取問題)
        def make_list_html(df, col_days):
            if df is None or df.empty:
                return "<p style='font-size:14px; text-align:center; color:#94A3B8;'>目前無資料或尚未開盤</p>"
            
            html = "<ul style='padding-left: 10px; margin: 0; font-size: 15px; line-height: 1.8; list-style-type: none;'>"
            for i, row in enumerate(df.head(5).to_dict('records')):
                html += (
                    f"<li>"
                    f"<b style='color:#FFF;'>{i+1}.</b> {row['股票代號']}{row['股票名稱']} "
                    f"<span style='color:#FFD700;'>{row['狀態動態']}</span> "
                    f"<span style='color:#00D2FF;'>{row[col_days]}天</span>"
                    f"</li>"
                )
            html += "</ul>"
            return html

        fo_html = make_list_html(fo_day_df, "最新連買天數")
        it_html = make_list_html(it_day_df, "最新連買天數")

        # HTML & CSS (加入背景模糊 Glassmorphism 與 JS 點擊隱藏)
        card_html = f"""
        <style>
        @keyframes slideInRight {{
            from {{ transform: translateX(120%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        .glass-panel {{
            position: fixed;
            top: 20vh; /* 距離頂部高度，可自行微調 */
            right: 20px; /* 靠右對齊 */
            width: 290px;
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 210, 255, 0.3);
            border-radius: 12px;
            padding: 18px 20px;
            z-index: 999999;
            color: #E2E8F0;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            animation: slideInRight 0.8s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}
        .close-btn {{
            position: absolute;
            top: 8px;
            right: 12px;
            cursor: pointer;
            color: #94A3B8;
            font-weight: bold;
            font-size: 16px;
            transition: color 0.3s;
        }}
        .close-btn:hover {{
            color: #FF4C4C; /* 滑鼠移過去變紅色 */
        }}
        .panel-title {{
            margin-top: 0;
            font-size: 17px;
            font-weight: bold;
            color: #00D2FF;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        /* 輪播動畫設定 (10秒一輪，各停5秒，利用透明度切換) */
        .carousel-wrapper {{
            position: relative;
            height: 180px; 
            overflow: hidden;
        }}
        .carousel-item {{
            position: absolute;
            top: 0; left: 0; width: 100%;
            opacity: 0;
            animation: fadeSwitch 10s infinite;
        }}
        .carousel-item:nth-child(2) {{
            animation-delay: 5s; /* 投信延遲5秒出現 */
        }}
        @keyframes fadeSwitch {{
            0%, 45% {{ opacity: 1; z-index: 2; }}
            50%, 95% {{ opacity: 0; z-index: 1; }}
            100% {{ opacity: 1; z-index: 2; }}
        }}
        </style>

        <div class="glass-panel" id="b3-top5-card">
            <!-- 點擊 X 就隱藏整個 div -->
            <span class="close-btn" onclick="document.getElementById('b3-top5-card').style.display='none'">✕</span>
            
            <div class="carousel-wrapper">
                <div class="carousel-item">
                    <div class="panel-title">🌐 外資最新日連買 TOP 5</div>
                    {fo_html}
                </div>
                <div class="carousel-item">
                    <div class="panel-title">🏦 投信最新日連買 TOP 5</div>
                    {it_html}
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    except Exception as e:
        # 若發生 KeyError 或欄位變動，靜默錯誤不影響主畫面
        pass
