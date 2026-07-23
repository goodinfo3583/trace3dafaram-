import streamlit as st
import base64
import os
import random

#隱藏設定
def load_global_css():
    """載入全站共用的隱藏設定與基本 CSS"""
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        .block-container { padding-top: 0 rem; }
        .stApp { background-color: #0A0D14 !important; }
        /* 這裡貼上你原本「網頁風格設計」區塊的所有 CSS */
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def set_background(image_path):
    """網站主視覺背景設定引擎"""
    try:
        with open(image_path, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()
            
        css = f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.88)), url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
        }}
        /* 其餘背景 CSS */
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ 找不到背景圖片檔：{image_path}")

def render_fireflies():
    """頂級視覺魔法：純代碼動態螢火蟲/粒子引擎"""
    # 將你原本的 render_fireflies 函式完整貼到這裡
    pass

def render_marquee():
    """跑馬燈區塊渲染"""
    # 將你原本跑馬燈 (get_image_base64 與 marquee_code) 的邏輯放在這裡
    pass
