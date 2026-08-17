# components/style_manager.py
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
    image_files = ["沙漠之城.png", "法人意向.png", "月影綠洲.png", "組合化學晶礦.png", "鐵風堡b.png"]
    
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

#跑馬燈懸浮卡片
#B2法人掃貨
def render_b2_top10_glass_card():
    """渲染 B2 法人掃貨 專屬懸浮玻璃卡片 (完美解決欄位擠壓問題)"""
    import pandas as pd
    import streamlit as st

    if 'df_blk2_1' not in st.session_state:
        return

    try:
        raw_df_21 = st.session_state.get('df_blk2_1', pd.DataFrame()) 
        raw_df_22 = st.session_state.get('df_blk2_2', pd.DataFrame()) 
        raw_df_23 = st.session_state.get('df_blk2_3', pd.DataFrame()) 
        raw_df_24 = st.session_state.get('df_blk2_4', pd.DataFrame()) 

        def get_top10_pure(df, target_col):
            if df is None or df.empty or target_col not in df.columns:
                return pd.DataFrame()
            df['股票代號'] = df['股票代號'].astype(str).str.strip()
            pure = df[(df['股票代號'].str.len() == 4) & (~df['股票代號'].str.startswith('00'))].copy()
            pure[target_col] = pd.to_numeric(pure[target_col], errors='coerce').fillna(0)
            pure = pure.sort_values(by=target_col, ascending=False).head(10)
            return pure

        def get_latest_col(df, keyword):
            if df.empty: return None, "未知"
            cols = [c for c in df.columns if keyword in c]
            if not cols: return None, "未知"
            latest = cols[0]
            date_str = latest.replace(keyword, "")
            return latest, date_str

        c21_col, d_21 = get_latest_col(raw_df_21, "成交比%")
        c22_col, d_22 = get_latest_col(raw_df_22, "成交比%")
        c23_col, d_23 = get_latest_col(raw_df_23, "發行數%")
        c24_col, d_24 = get_latest_col(raw_df_24, "發行數%")

        df_21 = get_top10_pure(raw_df_21, c21_col)
        df_22 = get_top10_pure(raw_df_22, c22_col)
        df_23 = get_top10_pure(raw_df_23, c23_col)
        df_24 = get_top10_pure(raw_df_24, c24_col)

        def make_list_html(df, val_col):
            if df.empty or val_col is None:
                return "<p style='font-size:14px; text-align:center; color:#94A3B8; margin-top:40px;'>目前無資料或尚未開盤</p>"
            
            html = "<ul style='padding-left: 0; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(df.to_dict('records')):
                val = row.get(val_col, 0)
                
                # --- 🎯 狀態文字精簡處理 ---
                raw_status = row.get('今日短動態', '')
                # 去除括號與後面的數字 (例如: "🔥 強延續 (1.89%)" -> "🔥 強延續")
                clean_status = raw_status.split('(')[0].strip()
                
                # 特殊處理：為了排版美觀，我們將狀態文字縮減為圖示+2個字
                if "轉賣反轉" in clean_status:
                    short_status = "🚨 轉賣"
                elif "今日突擊卡位" in clean_status:
                    short_status = "🆕 卡位"
                elif "持續加碼" in clean_status:
                    short_status = "🔥 加碼"
                elif "強延續" in clean_status:
                    short_status = "🔥 強攻"
                elif "劇烈倒貨" in clean_status:
                    short_status = "🚨 倒貨"
                elif "調節洗盤" in clean_status:
                    short_status = "📉 調節"
                elif "量縮持平" in clean_status or "持平" in clean_status:
                    short_status = "🔄 持平"
                elif "趨緩" in clean_status:
                    short_status = "⚠️ 趨緩"
                else:
                    # 如果都沒配對到，只取前三個字元(包含圖示)
                    short_status = clean_status[:3] if len(clean_status) > 3 else clean_status
                # -----------------------------

                # 採用 Flexbox 排版，保證不擠壓不換行
                html += (
                    f"<li style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; font-size: 14px; line-height: 1.4;'>"
                    f"  <div style='display: flex; align-items: center; width: 55%; overflow: hidden;'>"
                    f"      <b style='color:#FFF; width:22px; flex-shrink: 0;'>{i+1}.</b>"
                    f"      <span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['股票代號']}{row['股票名稱']}</span>"
                    f"  </div>"
                    f"  <div style='width: 25%; color:#FFD700; font-size: 12px; text-align: left; white-space:nowrap;'>{short_status}</div>"
                    f"  <div style='width: 20%; color:#FF4C4C; font-weight:bold; text-align: right;'>{val:.1f}%</div>"
                    f"</li>"
                )
            html += "</ul>"
            return html

        h_21 = make_list_html(df_21, c21_col)
        h_22 = make_list_html(df_22, c22_col)
        h_23 = make_list_html(df_23, c23_col)
        h_24 = make_list_html(df_24, c24_col)

        # HTML, CSS 頂格並單行化
        card_html = f"""
<input type="checkbox" id="close-b2-card" style="display:none;">
<input type="checkbox" id="min-b2-card" style="display:none;">
<style>
#close-b2-card:checked ~ #b2-top10-card {{ display: none !important; }}
#min-b2-card:checked ~ #b2-top10-card .carousel-wrapper-b2 {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-b2-card:checked ~ #b2-top10-card {{ padding-bottom: 8px; width: 220px; }}
#min-b2-card:checked ~ #b2-top10-card .min-icon-b2::after {{ content: '□'; font-size: 14px; }}
#min-b2-card:not(:checked) ~ #b2-top10-card .min-icon-b2::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
@keyframes slideInRightB2 {{ from {{ transform: translateX(120%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
.glass-panel-b2 {{ position: fixed; top: 56vh; right: 20px; width: 330px; background: rgba(30, 20, 20, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 76, 76, 0.35); border-radius: 12px; padding: 12px 16px; z-index: 999998; color: #E2E8F0; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); animation: slideInRightB2 0.8s cubic-bezier(0.25, 0.8, 0.25, 1); transition: all 0.3s ease; box-sizing: border-box; }}
.header-bar-b2 {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title-b2 {{ font-size: 14px; font-weight: bold; color: #FF7676; }}
.action-btns-b2 {{ display: flex; gap: 10px; align-items: center; }}
.action-btn-b2 {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; }}
.action-btn-b2:hover {{ color: #FF4C4C; }}
.panel-title-b2 {{ margin: 0 0 8px 0; font-size: 14.5px; font-weight: bold; color: #FF4C4C; display: flex; justify-content: space-between; align-items: flex-end; }}
.date-badge-b2 {{ font-size: 11.5px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper-b2 {{ position: relative; max-height: 270px; height: 270px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item-b2 {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitchB2 20s infinite; }}
.carousel-item-b2:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item-b2:nth-child(2) {{ animation-delay: 5s; }}
.carousel-item-b2:nth-child(3) {{ animation-delay: 10s; }}
.carousel-item-b2:nth-child(4) {{ animation-delay: 15s; }}
@keyframes fadeSwitchB2 {{ 0%, 22% {{ opacity: 1; z-index: 2; }} 25%, 97% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
</style>
<div class="glass-panel-b2" id="b2-top10-card">
<div class="header-bar-b2">
<span class="header-title-b2">🚀 法人暴力掃貨榜</span>
<div class="action-btns-b2">
<label for="min-b2-card" class="action-btn-b2 min-icon-b2" title="縮放"></label>
<label for="close-b2-card" class="action-btn-b2" title="關閉">✕</label>
</div>
</div>
<div class="carousel-wrapper-b2">
<div class="carousel-item-b2"><div class="panel-title-b2"><span>外資買超佔成交%</span><span class="date-badge-b2">📅 {d_21}</span></div>{h_21}</div>
<div class="carousel-item-b2"><div class="panel-title-b2"><span>投信買超佔成交%</span><span class="date-badge-b2">📅 {d_22}</span></div>{h_22}</div>
<div class="carousel-item-b2"><div class="panel-title-b2"><span>外資買超佔發行%</span><span class="date-badge-b2">📅 {d_23}</span></div>{h_23}</div>
<div class="carousel-item-b2"><div class="panel-title-b2"><span>投信買超佔發行%</span><span class="date-badge-b2">📅 {d_24}</span></div>{h_24}</div>
</div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
        
    except Exception as e:
        print(f"B2 Glass Card Error: {e}")
        pass

#B3法人連買
def render_top10_glass_card():
    """渲染右側懸浮玻璃卡片 (支援縮小、展開、關閉、10檔標的、4大榜單輪播、顯示基準日)"""
    import pandas as pd
    import streamlit as st

    if 'b3_data' not in st.session_state:
        return

    try:
        raw_fo_day_df, date_fo_day = st.session_state['b3_data']['fo_day']
        raw_it_day_df, date_it_day = st.session_state['b3_data']['it_day']
        raw_fo_wk_df, date_fo_wk = st.session_state['b3_data']['fo_wk']
        raw_it_wk_df, date_it_wk = st.session_state['b3_data']['it_wk']

        # 嚴格過濾：4 碼純股票（排除 00 開頭的 ETF）並取前 10 名
        def get_top10_pure_stocks(df):
            if df is None or df.empty:
                return pd.DataFrame()
            df['股票代號'] = df['股票代號'].astype(str).str.strip()
            pure_stocks = df[(df['股票代號'].str.len() == 4) & (~df['股票代號'].str.startswith('00'))].copy()
            return pure_stocks.head(10) 

        fo_day_df = get_top10_pure_stocks(raw_fo_day_df)
        it_day_df = get_top10_pure_stocks(raw_it_day_df)
        fo_wk_df = get_top10_pure_stocks(raw_fo_wk_df)
        it_wk_df = get_top10_pure_stocks(raw_it_wk_df)

        fmt_date = lambda d: d[-4:] if (d and d != "00000000") else "未知"
        d_fo_day = fmt_date(date_fo_day)
        d_it_day = fmt_date(date_it_day)
        d_fo_wk = fmt_date(date_fo_wk)
        d_it_wk = fmt_date(date_it_wk)

        def make_list_html(df, col_days, unit):
            if df is None or df.empty:
                return "<p style='font-size:14px; text-align:center; color:#94A3B8; margin-top:40px;'>目前無資料或尚未開盤</p>"
            
            html = "<ul style='padding-left: 5px; margin: 0; font-size: 14px; line-height: 1.5; list-style-type: none;'>"
            for i, row in enumerate(df.to_dict('records')):
                val = row.get(col_days, 0)
                status = row.get('狀態動態', '')
                html += (
                    f"<li>"
                    f"<b style='color:#FFF; display:inline-block; width:22px;'>{i+1}.</b>"
                    f"<span style='display:inline-block; width:95px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; vertical-align:bottom;'>{row['股票代號']}{row['股票名稱']}</span>"
                    f"<span style='color:#FFD700; font-size: 11.5px; margin: 0 4px;'>{status}</span>"
                    f"<span style='color:#00D2FF; float:right;'>{val}{unit}</span>"
                    f"</li>"
                )
            html += "</ul>"
            return html

        fo_day_html = make_list_html(fo_day_df, "最新連買天數", "天")
        it_day_html = make_list_html(it_day_df, "最新連買天數", "天")
        fo_wk_html = make_list_html(fo_wk_df, "最新連買週數", "週")
        it_wk_html = make_list_html(it_wk_df, "最新連買週數", "週")

        # HTML, CSS 頂格並單行化，防止 Markdown 渲染錯誤
        # 使用兩個隱藏的 checkbox 控制：一個負責關閉，一個負責縮小
        card_html = f"""
<input type="checkbox" id="close-card" style="display:none;">
<input type="checkbox" id="min-card" style="display:none;">
<style>
#close-card:checked ~ #b3-top10-card {{ display: none !important; }}
#min-card:checked ~ #b3-top10-card .carousel-wrapper {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-card:checked ~ #b3-top10-card {{ padding-bottom: 8px; width: 220px; }}
#min-card:checked ~ #b3-top10-card .min-icon::after {{ content: '□'; font-size: 14px; }}
#min-card:not(:checked) ~ #b3-top10-card .min-icon::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}

@keyframes slideInRight {{ from {{ transform: translateX(120%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
.glass-panel {{ position: fixed; top: 15vh; right: 20px; width: 330px; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(0, 210, 255, 0.35); border-radius: 12px; padding: 12px 16px; z-index: 999999; color: #E2E8F0; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); animation: slideInRight 0.8s cubic-bezier(0.25, 0.8, 0.25, 1); transition: all 0.3s ease; }}
.header-bar {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title {{ font-size: 14px; font-weight: bold; color: #64748B; }}
.action-btns {{ display: flex; gap: 10px; align-items: center; }}
.action-btn {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; }}
.action-btn:hover {{ color: #00D2FF; }}
.close-btn:hover {{ color: #FF4C4C; }}
.panel-title {{ margin: 0 0 8px 0; font-size: 14.5px; font-weight: bold; color: #00D2FF; display: flex; justify-content: space-between; align-items: flex-end; }}
.date-badge {{ font-size: 11.5px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper {{ position: relative; max-height: 310px; height: 310px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitch 20s infinite; }}
.carousel-item:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item:nth-child(2) {{ animation-delay: 5s; }}
.carousel-item:nth-child(3) {{ animation-delay: 10s; }}
.carousel-item:nth-child(4) {{ animation-delay: 15s; }}
@keyframes fadeSwitch {{ 0%, 22% {{ opacity: 1; z-index: 2; }} 25%, 97% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
</style>
<div class="glass-panel" id="b3-top10-card">
<div class="header-bar">
<span class="header-title">📊 籌碼強勢排行榜</span>
<div class="action-btns">
<label for="min-card" class="action-btn min-icon" title="縮放"></label>
<label for="close-card" class="action-btn close-btn" title="關閉">✕</label>
</div>
</div>
<div class="carousel-wrapper">
<div class="carousel-item"><div class="panel-title"><span>🌐 外資最新日連買</span><span class="date-badge">📅 {d_fo_day}</span></div>{fo_day_html}</div>
<div class="carousel-item"><div class="panel-title"><span>🏦 投信最新日連買</span><span class="date-badge">📅 {d_it_day}</span></div>{it_day_html}</div>
<div class="carousel-item"><div class="panel-title"><span>👑 外資最新週連買</span><span class="date-badge">📅 {d_fo_wk}</span></div>{fo_wk_html}</div>
<div class="carousel-item"><div class="panel-title"><span>🚀 投信最新週連買</span><span class="date-badge">📅 {d_it_wk}</span></div>{it_wk_html}</div>
</div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
        
    except Exception as e:
        print(f"Top 10 Glass Card Error: {e}")
        pass

#b4 資券玻璃卡片
def render_b4_top10_glass_card():
    """渲染 B4 資券動向 (軋空雷達/套牢名單) 專屬懸浮玻璃卡片"""
    import pandas as pd
    import streamlit as st

    # 檢查是否已有 B4 的雷達數據
    if 'b4_squeeze_radar' not in st.session_state or 'b4_risk_radar' not in st.session_state:
        return

    try:
        sq_data = st.session_state['b4_squeeze_radar']
        rk_data = st.session_state['b4_risk_radar']
        
        df_sq = sq_data['df']
        df_rk = rk_data['df']
        
        date_sq = sq_data['date'][-4:] if sq_data['date'] and len(sq_data['date']) >= 4 else "未知"
        date_rk = rk_data['date'][-4:] if rk_data['date'] and len(rk_data['date']) >= 4 else "未知"

        # 嚴格過濾：4 碼純股票（排除 00 開頭的 ETF）
        def get_pure_radar_stocks(df):
            if df is None or df.empty:
                return pd.DataFrame()
            df['代號'] = df['代號'].astype(str).str.strip()
            pure = df[(df['代號'].str.len() == 4) & (~df['代號'].str.startswith('00'))].copy()
            return pure

        # 取得純股票，並預留前 20 名
        pure_sq = get_pure_radar_stocks(df_sq).head(20)
        pure_rk = get_pure_radar_stocks(df_rk).head(20)

        # 產生 HTML 列表的通用函數
        # theme='sq' 為軋空(紅色系漲幅), theme='rk' 為套牢(綠色系跌幅)
        def make_radar_html(df, start_idx, theme):
            # 切片取 1~10 或 11~20
            sub_df = df.iloc[start_idx : start_idx+10]
            
            if sub_df.empty:
                return "<p style='font-size:14px; text-align:center; color:#94A3B8; margin-top:40px;'>該區間尚無雷達目標</p>"
            
            html = "<ul style='padding-left: 0; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(sub_df.to_dict('records')):
                # 判斷是軋空還是套牢
                status = row.get('軋空評估', '') if theme == 'sq' else row.get('套牢評估', '')
                pct = row.get('漲跌幅', 0.0)
                
                # 精簡狀態文字，確保只顯示圖示+2字 (例如: 💥 終極)
                short_status = status[:4] if len(status) > 4 else status
                
                # 顏色邏輯：軋空用紅/金，套牢用綠
                pct_color = "#FF4C4C" if theme == 'sq' else "#00e676"
                
                html += (
                    f"<li style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; font-size: 14px; line-height: 1.4;'>"
                    f"  <div style='display: flex; align-items: center; width: 55%; overflow: hidden;'>"
                    f"      <b style='color:#FFF; width:28px; flex-shrink: 0;'>{start_idx + i + 1}.</b>"
                    f"      <span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['代號']}{row['名稱']}</span>"
                    f"  </div>"
                    f"  <div style='width: 25%; color:#FFD700; font-size: 12px; text-align: left; white-space:nowrap;'>{short_status}</div>"
                    f"  <div style='width: 20%; color:{pct_color}; font-weight:bold; text-align: right;'>{pct}%</div>"
                    f"</li>"
                )
            html += "</ul>"
            return html

        # 分別產生 4 頁的 HTML
        h_sq_1_10 = make_radar_html(pure_sq, 0, 'sq')
        h_sq_11_20 = make_radar_html(pure_sq, 10, 'sq')
        h_rk_1_10 = make_radar_html(pure_rk, 0, 'rk')
        h_rk_11_20 = make_radar_html(pure_rk, 10, 'rk')

        # HTML, CSS 頂格單行化
        # 位置：放在左上角 (top: 15vh; left: 20px) 避免跟右邊的 B3, B2 打架
        # 特殊動畫與變色：前 10 秒是紫色調 (軋空)，後 10 秒變綠色調 (套牢)
        card_html = f"""
<input type="checkbox" id="close-b4-card" style="display:none;">
<input type="checkbox" id="min-b4-card" style="display:none;">
<style>
#close-b4-card:checked ~ #b4-top10-card {{ display: none !important; }}
#min-b4-card:checked ~ #b4-top10-card .carousel-wrapper-b4 {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-b4-card:checked ~ #b4-top10-card {{ padding-bottom: 8px; width: 220px; }}
#min-b4-card:checked ~ #b4-top10-card .min-icon-b4::after {{ content: '□'; font-size: 14px; }}
#min-b4-card:not(:checked) ~ #b4-top10-card .min-icon-b4::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
@keyframes slideInLeftB4 {{ from {{ transform: translateX(-120%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
@keyframes radarBreath {{ 
    0%, 49.9% {{ border-color: rgba(188, 19, 254, 0.4); box-shadow: 0 8px 32px 0 rgba(188, 19, 254, 0.15); }}
    50%, 100% {{ border-color: rgba(0, 230, 118, 0.4); box-shadow: 0 8px 32px 0 rgba(0, 230, 118, 0.1); }}
}}
.glass-panel-b4 {{ position: fixed; top: 15vh; left: 20px; width: 330px; background: rgba(20, 22, 35, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(188, 19, 254, 0.35); border-radius: 12px; padding: 12px 16px; z-index: 999997; color: #E2E8F0; animation: slideInLeftB4 0.8s cubic-bezier(0.25, 0.8, 0.25, 1), radarBreath 20s infinite; transition: all 0.3s ease; box-sizing: border-box; }}
.header-bar-b4 {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title-b4 {{ font-size: 14px; font-weight: bold; color: #E2E8F0; }}
.action-btns-b4 {{ display: flex; gap: 10px; align-items: center; }}
.action-btn-b4 {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; }}
.action-btn-b4:hover {{ color: #00D2FF; }}
.panel-title-b4 {{ margin: 0 0 8px 0; font-size: 14.5px; font-weight: bold; color: #bc13fe; display: flex; justify-content: space-between; align-items: flex-end; }}
.panel-title-b4.risk {{ color: #00e676; }}
.date-badge-b4 {{ font-size: 11.5px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper-b4 {{ position: relative; max-height: 270px; height: 270px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item-b4 {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitchB4 20s infinite; }}
.carousel-item-b4:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item-b4:nth-child(2) {{ animation-delay: 5s; }}
.carousel-item-b4:nth-child(3) {{ animation-delay: 10s; }}
.carousel-item-b4:nth-child(4) {{ animation-delay: 15s; }}
@keyframes fadeSwitchB4 {{ 0%, 22% {{ opacity: 1; z-index: 2; }} 25%, 97% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
</style>
<div class="glass-panel-b4" id="b4-top10-card">
<div class="header-bar-b4">
<span class="header-title-b4">📡 資券動向雙雷達</span>
<div class="action-btns-b4">
<label for="min-b4-card" class="action-btn-b4 min-icon-b4" title="縮放"></label>
<label for="close-b4-card" class="action-btn-b4" title="關閉">✕</label>
</div>
</div>
<div class="carousel-wrapper-b4">
<div class="carousel-item-b4"><div class="panel-title-b4"><span>🚀 可能軋空雷達 (1-10)</span><span class="date-badge-b4">📅 {date_sq}</span></div>{h_sq_1_10}</div>
<div class="carousel-item-b4"><div class="panel-title-b4"><span>🚀 可能軋空雷達 (11-20)</span><span class="date-badge-b4">📅 {date_sq}</span></div>{h_sq_11_20}</div>
<div class="carousel-item-b4"><div class="panel-title-b4 risk"><span>☠️ 短線套牢名單 (1-10)</span><span class="date-badge-b4">📅 {date_rk}</span></div>{h_rk_1_10}</div>
<div class="carousel-item-b4"><div class="panel-title-b4 risk"><span>☠️ 短線套牢名單 (11-20)</span><span class="date-badge-b4">📅 {date_rk}</span></div>{h_rk_11_20}</div>
</div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
        
    except Exception as e:
        print(f"B4 Glass Card Error: {e}")
        pass

#B5 大腿動向玻璃卡片
def render_b5_top10_glass_card():
    """渲染 B5 大腿動向 (長短線雙向共振) 專屬懸浮玻璃卡片 (修復排版與 Emoji 截斷)"""
    import pandas as pd
    import streamlit as st

    if 'b5_1000' not in st.session_state or 'b5_400' not in st.session_state:
        return

    try:
        df_1000 = st.session_state['b5_1000']
        df_400 = st.session_state['b5_400']
        
        if df_1000.empty or df_400.empty:
            return

        latest_col_1000 = next((c for c in df_1000.columns if c.startswith('▼') and '6周' not in c), None)
        latest_col_400 = next((c for c in df_400.columns if c.startswith('▼') and '6周' not in c), None)
        
        if not latest_col_1000 or not latest_col_400: return
        date_str = latest_col_1000.replace('▼', '') 

        def get_pure(df):
            df['股票代號'] = df['股票代號'].astype(str).str.strip()
            return df[(df['股票代號'].str.len() == 4) & (~df['股票代號'].str.startswith('00'))].copy()

        df_1k_pure = get_pure(df_1000)
        df_400_pure = get_pure(df_400)

        df_1k_sub = df_1k_pure[['股票代號', '股票名稱', '週動態', '▼6周增減', latest_col_1000]].copy()
        df_1k_sub = df_1k_sub.rename(columns={'▼6周增減': '6周(千)', latest_col_1000: '最新(千)', '週動態': '狀態(千)'})
        
        df_400_sub = df_400_pure[['股票代號', '週動態', '▼6周增減', latest_col_400]].copy()
        df_400_sub = df_400_sub.rename(columns={'▼6周增減': '6周(四)', latest_col_400: '最新(四)', '週動態': '狀態(四)'})

        sync_df = pd.merge(df_1k_sub, df_400_sub, on='股票代號', how='inner')
        
        for col in ['6周(千)', '最新(千)', '6周(四)', '最新(四)']:
            sync_df[f"{col}_val"] = pd.to_numeric(sync_df[col].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0)

        # --- 條件 1：長線 6 周雙引擎 ---
        cond_6w = (sync_df['6周(千)_val'] > 0) & (sync_df['6周(四)_val'] > 0)
        top10_6w = sync_df[cond_6w].sort_values(by='6周(千)_val', ascending=False).head(10)

        # --- 條件 2：短線最新週雙引擎 ---
        cond_latest = (sync_df['最新(千)_val'] > 0) & (sync_df['最新(四)_val'] > 0)
        top10_latest = sync_df[cond_latest].sort_values(by='最新(千)_val', ascending=False).head(10)

        # --- 🎯 狀態文字對齊引擎 (支援 9 階層對稱雷達) ---
        def unify_status_text(raw_status):
            """強迫將所有的狀態轉換為 (1圖示 + 2漢字) 的完美對齊格式"""
            s = str(raw_status)
            
            # 多方 (增)
            if "🚀" in s: return "🚀劇增"
            if "🔥" in s: return "🔥大增"
            if "📈" in s: return "📈小增"
            if "↗️" in s: return "↗️微增"
            
            # 持平
            if "🔄" in s: return "🔄持平"
            
            # 空方 (減)
            if "↘️" in s: return "↘️微減"
            if "📉" in s: return "📉小減"
            if "⚠️" in s: return "⚠️大減"
            if "🚨" in s: return "🚨劇減"
            
            return "⚪無字"

        def make_resonance_html(df, is_6w):
            if df.empty:
                return "<p style='font-size:14px; text-align:center; color:#94A3B8; margin-top:40px;'>本週尚無雙引擎共振標的</p>"
            
            html = "<ul style='padding-left: 0; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(df.to_dict('records')):
                if is_6w:
                    val_1 = row['6周(千)_val']
                    val_2 = row['6周(四)_val']
                    # 數字對齊：固定為 55px 寬度並靠右
                    info_html = (
                        f"<div style='display: flex; width: 45%; justify-content: flex-end; color:#F59E0B; font-weight:bold; font-size: 13px;'>"
                        f"  <span style='width: 55px; text-align: right;'>{val_1:.2f}%</span>"
                        f"  <span style='color:#94A3B8; font-size:11px; font-weight:normal; margin: 0 4px;'>/</span>"
                        f"  <span style='width: 55px; text-align: right;'>{val_2:.2f}%</span>"
                        f"</div>"
                    )
                else:
                    status_1 = unify_status_text(row.get('狀態(千)', ''))
                    status_2 = unify_status_text(row.get('狀態(四)', ''))
                    # 狀態文字對齊：固定寬度並置中/靠右
                    info_html = (
                        f"<div style='display: flex; width: 45%; justify-content: flex-end; color:#F59E0B; font-size: 12px;'>"
                        f"  <span style='width: 55px; text-align: right;'>{status_1}</span>"
                        f"  <span style='color:#94A3B8; font-size:11px; margin: 0 4px;'>/</span>"
                        f"  <span style='width: 55px; text-align: right;'>{status_2}</span>"
                        f"</div>"
                    )
                
                html += (
                    f"<li style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; font-size: 14px; line-height: 1.4;'>"
                    f"  <div style='display: flex; align-items: center; width: 55%; overflow: hidden;'>"
                    f"      <b style='color:#FFF; width:22px; flex-shrink: 0;'>{i+1}.</b>"
                    f"      <span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['股票代號']}{row['股票名稱']}</span>"
                    f"  </div>"
                    f"  {info_html}"
                    f"</li>"
                )
            html += "</ul>"
            return html

        h_6w = make_resonance_html(top10_6w, is_6w=True)
        h_latest = make_resonance_html(top10_latest, is_6w=False)

        # HTML, CSS 單行化
        card_html = f"""
<input type="checkbox" id="close-b5-card" style="display:none;">
<input type="checkbox" id="min-b5-card" style="display:none;">
<style>
#close-b5-card:checked ~ #b5-top10-card {{ display: none !important; }}
#min-b5-card:checked ~ #b5-top10-card .carousel-wrapper-b5 {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-b5-card:checked ~ #b5-top10-card {{ padding-bottom: 8px; width: 220px; }}
#min-b5-card:checked ~ #b5-top10-card .min-icon-b5::after {{ content: '□'; font-size: 14px; }}
#min-b5-card:not(:checked) ~ #b5-top10-card .min-icon-b5::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
@keyframes slideInLeftB5 {{ from {{ transform: translateX(-120%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
.glass-panel-b5 {{ position: fixed; top: 56vh; left: 20px; width: 330px; background: rgba(30, 25, 10, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 12px 16px; z-index: 999996; color: #E2E8F0; box-shadow: 0 8px 32px 0 rgba(245, 158, 11, 0.2); animation: slideInLeftB5 0.8s cubic-bezier(0.25, 0.8, 0.25, 1); transition: all 0.3s ease; box-sizing: border-box; }}
.header-bar-b5 {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title-b5 {{ font-size: 14px; font-weight: bold; color: #FCD34D; }}
.action-btns-b5 {{ display: flex; gap: 10px; align-items: center; }}
.action-btn-b5 {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; }}
.action-btn-b5:hover {{ color: #F59E0B; }}
.panel-title-b5 {{ margin: 0 0 12px 0; font-size: 13.5px; font-weight: bold; color: #F59E0B; display: flex; justify-content: space-between; align-items: flex-end; }}
.date-badge-b5 {{ font-size: 11px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper-b5 {{ position: relative; max-height: 270px; height: 270px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item-b5 {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitchB5 10s infinite; }}
.carousel-item-b5:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item-b5:nth-child(2) {{ animation-delay: 5s; }}
@keyframes fadeSwitchB5 {{ 0%, 45% {{ opacity: 1; z-index: 2; }} 50%, 95% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
</style>
<div class="glass-panel-b5" id="b5-top10-card">
<div class="header-bar-b5">
<span class="header-title-b5">🔥 大腿動向雙向共振</span>
<div class="action-btns-b5">
<label for="min-b5-card" class="action-btn-b5 min-icon-b5" title="縮放"></label>
<label for="close-b5-card" class="action-btn-b5" title="關閉">✕</label>
</div>
</div>
<div class="carousel-wrapper-b5">
<div class="carousel-item-b5">
    <div class="panel-title-b5"><span>📊 6周累積共振(1000張/400張)</span><span class="date-badge-b5">📅 {date_str}</span></div>
    {h_6w}
</div>
<div class="carousel-item-b5">
    <div class="panel-title-b5"><span>⚡ 週動能共振(1000張/400張)</span><span class="date-badge-b5">📅 {date_str}</span></div>
    {h_latest}
</div>
</div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
        
    except Exception as e:
        print(f"B5 Glass Card Error: {e}")
        pass
