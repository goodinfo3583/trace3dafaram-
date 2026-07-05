import streamlit as st
import os
import base64
import random

def set_background(image_path):
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
            position: absolute;
            width: {size}px; height: {size}px;
            left: {start_x}vw; top: {start_y}vh;
            background: #FFFFDF; 
            border-radius: 50%;
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
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none; 
        z-index: 1000;        
        overflow: hidden;
    }}
    {''.join(css_rules)}
    </style>
    <div class="fireflies-container">
        {''.join(html_divs)}
    </div>
    """
    st.markdown(full_code, unsafe_allow_html=True)

def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        data = image_file.read()
        mime_type = "image/gif" if image_path.lower().endswith('.gif') else "image/png"
        encoded_string = base64.b64encode(data).decode()
    return f"data:{mime_type};base64,{encoded_string}"

def render_marquee():
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
            st.error(f"系統找不到這張圖片：{img_path}，請檢查檔名或大小寫！")

    marquee_code = f"""
    <style>
        .slideshow-container {{
            position: relative;
            width: 800px;
            height: 100px;
            margin: 0 auto 10px auto; 
            background-color: #0A0D14;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }}
        .slide {{
            position: absolute;
            height: 100%;
            object-fit: contain; 
            visibility: hidden; 
            opacity: 0;
            animation: cut {total_time}s infinite;
        }}
    {delay_css}
        @keyframes cut {{
            0%, {visible_percent - 0.01:.2f}%   {{ visibility: visible; opacity: 1; }} 
            {visible_percent:.2f}%, 100%        {{ visibility: hidden; opacity: 0; }}  
        }}
    </style>
    <div class="slideshow-container">
        {image_tags}
    </div>
    """
    st.markdown(marquee_code, unsafe_allow_html=True)

def setup_all_effects():
    """這是一鍵召喚所有視覺特效的按鈕"""
    # 1. 隱藏預設版面 & 調整留白
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        .block-container { padding-top: 0rem; }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 2. 建立圖片資料夾與設定背景
    IMAGE_DIR = "./image"
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    bg_path = os.path.join(IMAGE_DIR, "派對盛宴邀請.png")
    set_background(bg_path)

    # 3. 施放螢火蟲
    render_fireflies()

    # 4. 啟動跑馬燈
    render_marquee()
