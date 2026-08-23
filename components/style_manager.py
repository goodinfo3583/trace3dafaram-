# components/style_manager.py
import streamlit as st
import base64
import os
import random
import streamlit.components.v1 as components

def load_global_css():
    """載入全站共用的隱藏設定、縮排與動態主題 (深色濾鏡護眼版) CSS，以及全域拖曳引擎"""
    theme = st.session_state.get('theme', 'dark')
    opacity = st.session_state.get('bg_opacity', 88) / 100.0
    
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        .block-container { padding-top: 0rem; }
        
        /* 啟用所有懸浮視窗的縮放功能 (右下角可拉伸) */
        .glass-panel, .glass-panel-b2, .glass-panel-b4, .glass-panel-b5, .npc-overlay, .settings-modal-active {
            resize: both !important; 
            overflow: auto !important; 
        }

        /* 💡 賦予 icon-card.png 真實按鈕的回饋手感 (發光、縮放) */
        img[src*="icon-card"], img[alt*="icon-card"] {
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        img[src*="icon-card"]:hover, img[alt*="icon-card"]:hover {
            transform: scale(1.08) !important;
            filter: drop-shadow(0 0 8px rgba(0, 210, 255, 0.6)) !important;
        }
        img[src*="icon-card"]:active, img[alt*="icon-card"]:active {
            transform: scale(0.95) !important;
        }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    if theme == 'pink': bg_color = f"rgba(139, 109, 98, {opacity})"
    elif theme == 'green': bg_color = f"rgba(75, 159, 113, {opacity})"
    elif theme == 'purple': bg_color = f"rgba(87, 99, 158, {opacity})"
    elif theme == 'brown': bg_color = f"rgba(238, 226, 188, {opacity})"
    
    else: bg_color = f"rgba(10, 13, 20, {opacity})"

    theme_css = f"""
        <style>
        .stApp {{ background-color: {bg_color} !important; }}
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText {{ color: #E2E8F0 !important; }}
        [data-testid="stAlert"] {{ background-color: transparent !important; border: 1px solid #2D3748 !important; }}
        [data-testid="stSidebar"] {{ background-color: rgba(17, 22, 34, 0.95) !important; border-right: 1px solid #1E293B; }}
        .stTextInput>div>div>input {{ background-color: #1A202C !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }}
        div[data-testid="stDataFrame"] {{ background-color: #111622 !important; border: 1px solid #1E293B !important; border-radius: 6px; }}
        
        .stButton > button, .stLinkButton > a {{
            background-color: #1E293B !important; 
            color: #94A3B8 !important; 
            border: 1px solid #334155 !important;
            transition: all 0.2s ease-in-out;
        }}
        .stButton > button:hover, .stLinkButton > a:hover {{
            border-color: #00D2FF !important;
            color: #00D2FF !important;
            box-shadow: 0 0 8px rgba(0, 210, 255, 0.2);
        }}
        </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

    drag_engine_js = """
    <script>
    (function() {
        if (window.parent.window.customDragDelegated) return;
        window.parent.window.customDragDelegated = true;
        const doc = window.parent.document;
        
        // ==========================================
        // 💡 1. 強制監聽點擊事件：一鍵收合 4 張玻璃卡片
        // ==========================================
        doc.addEventListener('click', (e) => {
            let isIconCard = false;
            let t = e.target;
            
            // 檢查是否直接點到圖片，且 src 或 alt 包含 icon-card (防止 Streamlit 將檔名 hash 導致找不到)
            if (t.tagName === 'IMG' && ((t.src && t.src.includes('icon-card')) || (t.alt && t.alt.includes('icon-card')))) {
                isIconCard = true;
            } 
            // 檢查是否點到 Streamlit 包裝的 div 容器
            else if (t.closest) {
                let parentImg = t.closest('div[data-testid="stImage"]')?.querySelector('img');
                if (parentImg && ((parentImg.src && parentImg.src.includes('icon-card')) || (parentImg.alt && parentImg.alt.includes('icon-card')))) {
                    isIconCard = true;
                }
            }

            if (isIconCard) {
                e.preventDefault();   // 攔截預設行為
                e.stopPropagation();  // 阻止事件冒泡，防止 Streamlit 的燈箱彈出
                
                let cb2 = doc.getElementById('min-b2-card');
                let cb3 = doc.getElementById('min-card');
                let cb4 = doc.getElementById('min-b4-card');
                let cb5 = doc.getElementById('min-b5-card');

                // 判斷當前狀態：只要有一張沒縮小，按下去就全部縮小；如果全部都縮小了，按下去就全部展開
                let anyOpen = false;
                if (cb2 && !cb2.checked) anyOpen = true;
                if (cb3 && !cb3.checked) anyOpen = true;
                if (cb4 && !cb4.checked) anyOpen = true;
                if (cb5 && !cb5.checked) anyOpen = true;

                if (cb2) cb2.checked = anyOpen;
                if (cb3) cb3.checked = anyOpen;
                if (cb4) cb4.checked = anyOpen;
                if (cb5) cb5.checked = anyOpen;
            }
        }, true); // 💡 使用 true 開啟 Capture Phase，搶在 React 之前攔截點擊

        // ==========================================
        // 💡 2. 全域拖曳引擎
        // ==========================================
        let isDragging = false, currentEl = null, startX, startY, initialX, initialY;
        const onDown = (e) => {
            let handle = e.target.closest('.header-bar, .header-bar-b2, .header-bar-b4, .header-bar-b5, .npc-drag-handle, .settings-drag-handle');
            if (!handle) return;
            if (e.target.closest('button, input, label, .action-btn, .action-btn-b2, .action-btn-b4, .action-btn-b5')) return;
            
            let el = handle.closest('.glass-panel, .glass-panel-b2, .glass-panel-b4, .glass-panel-b5, .npc-wrapper, .settings-modal-active');
            if (!el) el = handle.closest('div[data-testid="stVerticalBlock"].settings-modal-active');
            if (!el) return;
            
            isDragging = true;
            currentEl = el;
            let clientX = e.touches ? e.touches[0].clientX : e.clientX;
            let clientY = e.touches ? e.touches[0].clientY : e.clientY;
            startX = clientX; startY = clientY;
            
            let rect = el.getBoundingClientRect();
            el.style.transition = 'none';
            el.style.left = rect.left + 'px';
            el.style.top = rect.top + 'px';
            el.style.right = 'auto';
            el.style.bottom = 'auto';
            el.style.transform = 'none';
            el.style.margin = '0';
            
            initialX = rect.left; initialY = rect.top;
            handle.style.cursor = 'grabbing';
        };
        const onMove = (e) => {
            if (!isDragging || !currentEl) return;
            e.preventDefault(); 
            let clientX = e.touches ? e.touches[0].clientX : e.clientX;
            let clientY = e.touches ? e.touches[0].clientY : e.clientY;
            currentEl.style.left = (initialX + (clientX - startX)) + 'px';
            currentEl.style.top = (initialY + (clientY - startY)) + 'px';
        };
        const onUp = () => {
            if (isDragging && currentEl) {
                currentEl.style.transition = '';
                let handle = currentEl.querySelector('.header-bar, .header-bar-b2, .header-bar-b4, .header-bar-b5, .npc-drag-handle, .settings-drag-handle');
                if(handle) handle.style.cursor = 'grab';
            }
            isDragging = false; currentEl = null;
        };
        
        doc.addEventListener('mousedown', onDown);
        doc.addEventListener('touchstart', onDown, {passive: false});
        doc.addEventListener('mousemove', onMove, {passive: false});
        doc.addEventListener('touchmove', onMove, {passive: false});
        doc.addEventListener('mouseup', onUp);
        doc.addEventListener('touchend', onUp);
    })();
    </script>
    """
    components.html(drag_engine_js, height=0, width=0)

def set_background(image_path="./image/派對盛宴邀請.png"):
    theme = st.session_state.get('theme', 'dark')
    opacity = st.session_state.get('bg_opacity', 88) / 100.0
    block_opacity = opacity * 0.7 
    
    actual_image = image_path
    if theme == 'pink':
        overlay, block_bg = f"rgba(139, 109, 98, {opacity})", f"rgba(139, 109, 98, {block_opacity})"
        actual_image = "./static/鐵風堡.png"
    elif theme == 'green':
        overlay, block_bg = f"rgba(75, 159, 113, {opacity})", f"rgba(75, 159, 113, {block_opacity})"
        actual_image = "./static/翡翠林鎮.png"
    elif theme == 'purple':
        overlay, block_bg = f"rgba(87, 99, 158, {opacity})", f"rgba(87, 99, 158, {block_opacity})"
        actual_image = "./static/月下綠洲城.png"
    elif theme == 'brown':
        overlay, block_bg = f"rgba(238, 226, 188, {opacity})", f"rgba(238, 226, 188, {block_opacity})"
        actual_image = "./static/沙漠之都.png"
        
    else: 
        overlay, block_bg = f"rgba(15, 23, 42, {opacity})", f"rgba(15, 23, 42, {block_opacity})"
    
    if not os.path.exists(actual_image):
        actual_image = image_path
    
    try:
        with open(actual_image, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()

        css = f"""
        <style>
        .stApp {{
            background-image: linear-gradient({overlay}, {overlay}), url(data:image/png;base64,{encoded_string});
            background-size: cover; background-position: center center; background-attachment: fixed;
        }}
        div[data-testid="stVerticalBlock"] > div[style*="border"] {{
            background-color: {block_bg} !important; backdrop-filter: blur(4px); 
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError: pass

def render_fireflies():
    num_fireflies = 5 
    css_rules, html_divs = [], []
    for i in range(num_fireflies):
        size = random.uniform(2, 5)          
        start_x, start_y = random.uniform(0, 100), random.uniform(0, 100)     
        move_x, move_y = random.uniform(-20, 20), random.uniform(-20, 20)     
        duration, delay, pulse_dur = random.uniform(10, 25), random.uniform(0, 10), random.uniform(2, 5)     
        
        css_rules.append(f"""
        .firefly-{i} {{ position: absolute; width: {size}px; height: {size}px; left: {start_x}vw; top: {start_y}vh; background: #FFFFDF; border-radius: 50%; box-shadow: 0 0 {size*3}px {size}px rgba(255, 215, 0, 0.6); animation: drift-{i} {duration}s infinite ease-in-out {delay}s, flash-{i} {pulse_dur}s infinite ease-in-out {delay}s; opacity: 0; }}
        @keyframes drift-{i} {{ 0% {{ transform: translate(0px, 0px); }} 25% {{ transform: translate({move_x}vw, {move_y}vh); }} 50% {{ transform: translate({move_x/2}vw, {move_y*1.5}vh); }} 75% {{ transform: translate({-move_x}vw, {move_y/2}vh); }} 100% {{ transform: translate(0px, 0px); }} }}
        @keyframes flash-{i} {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: {random.uniform(0.5, 1.0)}; }} }}
        """)
        html_divs.append(f"<div class='firefly-{i}'></div>")
    
    st.markdown(f"<style>.fireflies-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 1000; overflow: hidden; }} {''.join(css_rules)}</style><div class='fireflies-container'>{''.join(html_divs)}</div>", unsafe_allow_html=True)

def render_marquee():
    def get_image_base64(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            mime_type = "image/gif" if image_path.lower().endswith('.gif') else "image/png"
        return f"data:{mime_type};base64,{encoded_string}"

    image_folder, image_files = "static", ["沙漠之城.png", "法人意向.png", "月影綠洲.png", "組合化學晶礦.png", "鐵風堡b.png"]
    total_images, time_per_slide = len(image_files), 5  
    total_time, visible_percent = total_images * time_per_slide, (1 / total_images) * 100 

    image_tags, delay_css = "", ""
    for i, img_name in enumerate(image_files):
        img_path = os.path.join(image_folder, img_name)
        if os.path.exists(img_path):
            image_tags += f'<img class="slide slide-{i}" src="{get_image_base64(img_path)}">'
            delay_css += f"    .slide-{i} {{ animation-delay: {i * time_per_slide}s; }}\n"
        else: st.error(f"系統找不到圖片：{img_path}")

    st.markdown(f"""
    <style>
        .slideshow-container {{ position: relative; width: 800px; height: 100px; margin: 0 auto 10px auto; background-color: transparent; display: flex; justify-content: center; align-items: center; overflow: hidden; }}
        .slide {{ position: absolute; height: 100%; object-fit: contain; visibility: hidden; opacity: 0; animation: cut {total_time}s infinite; }}
        {delay_css}
        @keyframes cut {{ 0%, {visible_percent - 0.01:.2f}% {{ visibility: visible; opacity: 1; }} {visible_percent:.2f}%, 100% {{ visibility: hidden; opacity: 0; }} }}
    </style>
    <div class="slideshow-container">{image_tags}</div>
    """, unsafe_allow_html=True)

#跑馬燈懸浮卡片
#B2法人掃貨
def render_b2_top10_glass_card():
    import pandas as pd
    import streamlit as st
    if 'df_blk2_1' not in st.session_state: return
    try:
        raw_df_21 = st.session_state.get('df_blk2_1', pd.DataFrame()) 
        raw_df_22 = st.session_state.get('df_blk2_2', pd.DataFrame()) 
        raw_df_23 = st.session_state.get('df_blk2_3', pd.DataFrame()) 
        raw_df_24 = st.session_state.get('df_blk2_4', pd.DataFrame()) 
        def get_top10(df, target_col):
            if df is None or df.empty or target_col not in df.columns: return pd.DataFrame()
            df['股票代號'] = df['股票代號'].astype(str).str.strip()
            pure = df[(df['股票代號'].str.len() == 4) & (~df['股票代號'].str.startswith('00'))].copy()
            pure[target_col] = pd.to_numeric(pure[target_col], errors='coerce').fillna(0)
            return pure.sort_values(by=target_col, ascending=False).head(10)
        def get_col(df, kw):
            cols = [c for c in df.columns if kw in c]
            if not cols: return None, "未知"
            return cols[0], cols[0].replace(kw, "")
        c21, d21 = get_col(raw_df_21, "成交比%")
        c22, d22 = get_col(raw_df_22, "成交比%")
        c23, d23 = get_col(raw_df_23, "發行數%")
        c24, d24 = get_col(raw_df_24, "發行數%")
        df_21, df_22 = get_top10(raw_df_21, c21), get_top10(raw_df_22, c22)
        df_23, df_24 = get_top10(raw_df_23, c23), get_top10(raw_df_24, c24)
        def make_list_html(df, val_col):
            if df.empty or val_col is None: return "<p style='font-size:13.5px; text-align:center; color:#94A3B8; margin-top:40px;'>無資料</p>"
            html = "<ul style='padding-left: 0; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(df.to_dict('records')):
                val = row.get(val_col, 0)
                cs = row.get('今日短動態', '').split('(')[0].strip()             
                if "轉賣反轉" in cs: short_status = "🚨轉賣"
                elif "卡位" in cs: short_status = "🆕卡位"
                elif "加碼" in cs: short_status = "🔥加碼"
                elif "強延續" in cs: short_status = "🔥強攻"
                elif "倒貨" in cs: short_status = "🚨倒貨"
                elif "調節" in cs: short_status = "📉調節"
                elif "持平" in cs: short_status = "🔄持平"
                elif "趨緩" in cs: short_status = "⚠️趨緩"
                else: short_status = cs[:3]
                html += (
                    f"<li style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 13.5px; line-height: 1.4;'>"
                    f"  <div style='display: flex; align-items: center; width: 50%; overflow: hidden;'>"
                    f"      <b style='color:#FFF; width:22px; flex-shrink: 0;'>{i+1}.</b>"
                    f"      <span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['股票代號']}{row['股票名稱']}</span>"
                    f"  </div>"
                    f"  <div style='width: 25%; color:#FFD700; font-size: 11px; text-align: right; white-space:nowrap;'>{short_status}</div>"
                    f"  <div style='width: 25%; color:#FF4C4C; font-weight:bold; text-align: right;'>{val:.1f}%</div>"
                    f"</li>"
                )
            html += "</ul>"
            return html
        h_21, h_22 = make_list_html(df_21, c21), make_list_html(df_22, c22)
        h_23, h_24 = make_list_html(df_23, c23), make_list_html(df_24, c24)
        card_html = f"""
<input type="checkbox" id="close-b2-card" style="display:none;">
<input type="checkbox" id="min-b2-card" style="display:none;">
<input type="checkbox" id="pause-b2-card" style="display:none;">
<style>
#close-b2-card:checked ~ #b2-top10-card {{ display: none !important; }}
#min-b2-card:checked ~ #b2-top10-card .carousel-wrapper-b2 {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-b2-card:checked ~ #b2-top10-card {{ padding-bottom: 8px; width: 150px; height: auto; }}
#min-b2-card:checked ~ #b2-top10-card .min-icon-b2::after {{ content: '□'; font-size: 14px; }}
#min-b2-card:not(:checked) ~ #b2-top10-card .min-icon-b2::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
#pause-b2-card:checked ~ #b2-top10-card .carousel-item-b2 {{ animation-play-state: paused !important; }}
#pause-b2-card:checked ~ #b2-top10-card .pause-icon-b2::after {{ content: '▶'; font-size: 11px; color: #FFD700; }}
#pause-b2-card:not(:checked) ~ #b2-top10-card .pause-icon-b2::after {{ content: '⏸'; font-size: 11px; }}
@keyframes slideInDownB2 {{ from {{ transform: translateY(-50%); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
/* 💡 將 top: 75px 改為 top: 100px */
.glass-panel-b2 {{position: fixed; top: 85px; left: 84.5vw; width: 15.5vw; min-width: 220px; background: rgba(30, 20, 20, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 76, 76, 0.35); border-radius: 0 12px 12px 0; padding: 10px 12px; z-index: 999998; color: #E2E8F0; animation: slideInDownB2 0.9s cubic-bezier(0.25, 0.8, 0.25, 1); transition: all 0.3s ease; box-sizing: border-box; }}
.header-bar-b2 {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title-b2 {{ font-size: 13px; font-weight: bold; color: #FF7676; white-space:nowrap; }}
.action-btns-b2 {{ display: flex; gap: 8px; align-items: center; }}
.action-btn-b2 {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; display: flex; align-items: center; justify-content: center; }}
.action-btn-b2:hover {{ color: #FF4C4C; }}
.panel-title-b2 {{ margin: 0 0 8px 0; font-size: 12.5px; font-weight: bold; color: #FF4C4C; display: flex; justify-content: space-between; align-items: flex-end; }}
.date-badge-b2 {{ font-size: 10px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper-b2 {{ position: relative; max-height: 285px; height: 285px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item-b2 {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitchB2 20s infinite; }}
.carousel-item-b2:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item-b2:nth-child(2) {{ animation-delay: 5s; }}
.carousel-item-b2:nth-child(3) {{ animation-delay: 10s; }}
.carousel-item-b2:nth-child(4) {{ animation-delay: 15s; }}
@keyframes fadeSwitchB2 {{ 0%, 22% {{ opacity: 1; z-index: 2; }} 25%, 97% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
@media (max-width: 1200px) {{ .glass-panel-b2 {{ position: relative; top: auto; left: auto; width: 90%; max-width: 350px; margin: 10px auto; display: block; }} }}
</style>
<div class="glass-panel-b2" id="b2-top10-card">
<div class="header-bar-b2"><span class="header-title-b2"><img src="app/static/magicbookwind.png" style="width:18px; margin-right:6px; vertical-align:-3px;" onerror="this.style.display='none'">法人掃貨</span>
<div class="action-btns-b2">
<label for="pause-b2-card" class="action-btn-b2 pause-icon-b2" title="暫停/播放輪播"></label>
<label for="min-b2-card" class="action-btn-b2 min-icon-b2" title="縮放"></label>
<label for="close-b2-card" class="action-btn-b2" title="關閉">✕</label>
</div></div>
<div class="carousel-wrapper-b2">
<div class="carousel-item-b2"><div class="panel-title-b2"><span>外資買超(成交%)</span><span class="date-badge-b2">{d21}</span></div>{h_21}</div>
<div class="carousel-item-b2"><div class="panel-title-b2"><span>投信買超(成交%)</span><span class="date-badge-b2">{d22}</span></div>{h_22}</div>
<div class="carousel-item-b2"><div class="panel-title-b2"><span>外資買超(發行%)</span><span class="date-badge-b2">{d23}</span></div>{h_23}</div>
<div class="carousel-item-b2"><div class="panel-title-b2"><span>投信買超(發行%)</span><span class="date-badge-b2">{d24}</span></div>{h_24}</div>
</div></div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
    except Exception as e: pass

#B3法人連買
def render_top10_glass_card():
    import pandas as pd
    import streamlit as st
    if 'b3_data' not in st.session_state: return
    try:
        raw_fo_day_df, date_fo_day = st.session_state['b3_data']['fo_day']
        raw_it_day_df, date_it_day = st.session_state['b3_data']['it_day']
        raw_fo_wk_df, date_fo_wk = st.session_state['b3_data']['fo_wk']
        raw_it_wk_df, date_it_wk = st.session_state['b3_data']['it_wk']

        def get_top10(df):
            if df is None or df.empty: return pd.DataFrame()
            df['股票代號'] = df['股票代號'].astype(str).str.strip()
            return df[(df['股票代號'].str.len() == 4) & (~df['股票代號'].str.startswith('00'))].head(10) 
        fo_day_df, it_day_df = get_top10(raw_fo_day_df), get_top10(raw_it_day_df)
        fo_wk_df, it_wk_df = get_top10(raw_fo_wk_df), get_top10(raw_it_wk_df)

        fmt_d = lambda d: d[-4:] if (d and d != "00000000") else "未知"
        d_fo_day, d_it_day, d_fo_wk, d_it_wk = fmt_d(date_fo_day), fmt_d(date_it_day), fmt_d(date_fo_wk), fmt_d(date_it_wk)

        def make_list_html(df, col_days, unit):
            if df is None or df.empty: return "<p style='font-size:13.5px; text-align:center; color:#94A3B8; margin-top:40px;'>無資料</p>"
            html = "<ul style='padding-left: 0px; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(df.to_dict('records')):
                val, status = row.get(col_days, 0), row.get('狀態動態', '')
                html += (
                    f"<li style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; font-size: 13.5px; line-height: 1.4;'>"
                    f"<div style='display:flex; width:55%; overflow:hidden;'>"
                    f"<b style='color:#FFF; display:inline-block; width:22px; flex-shrink:0;'>{i+1}.</b>"
                    f"<span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['股票代號']}{row['股票名稱']}</span>"
                    f"</div>"
                    f"<div style='width:45%; text-align:right; white-space:nowrap;'>"
                    f"<span style='color:#FFD700; font-size: 11px; margin-right:4px;'>{status}</span>"
                    f"<span style='color:#00D2FF; font-weight:bold;'>{val}{unit}</span>"
                    f"</div></li>"
                )
            html += "</ul>"
            return html

        fo_day_html, it_day_html = make_list_html(fo_day_df, "最新連買天數", "天"), make_list_html(it_day_df, "最新連買天數", "天")
        fo_wk_html, it_wk_html = make_list_html(fo_wk_df, "最新連買週數", "週"), make_list_html(it_wk_df, "最新連買週數", "週")
        card_html = f"""
<input type="checkbox" id="close-card" style="display:none;">
<input type="checkbox" id="min-card" style="display:none;">
<input type="checkbox" id="pause-card" style="display:none;">
<style>
#close-card:checked ~ #b3-top10-card {{ display: none !important; }}
#min-card:checked ~ #b3-top10-card .carousel-wrapper {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-card:checked ~ #b3-top10-card {{ padding-bottom: 8px; width: 150px; height: auto; }}
#min-card:checked ~ #b3-top10-card .min-icon::after {{ content: '□'; font-size: 14px; }}
#min-card:not(:checked) ~ #b3-top10-card .min-icon::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
#pause-card:checked ~ #b3-top10-card .carousel-item {{ animation-play-state: paused !important; }}
#pause-card:checked ~ #b3-top10-card .pause-icon::after {{ content: '▶'; font-size: 11px; color: #FFD700; }}
#pause-card:not(:checked) ~ #b3-top10-card .pause-icon::after {{ content: '⏸'; font-size: 11px; }}
@keyframes slideInDownB3 {{ from {{ transform: translateY(-50%); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
/* 💡 將 top: 75px 改為 top: 100px */
.glass-panel {{position: fixed; top: 85px; left: 69vw; width: 15.5vw; min-width: 220px; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(0, 210, 255, 0.35); border-right: none; border-radius: 0; padding: 10px 12px; z-index: 999999; color: #E2E8F0; animation: slideInDownB3 0.8s cubic-bezier(0.25, 0.8, 0.25, 1); transition: all 0.3s ease; box-sizing: border-box;}}
.header-bar {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title {{ font-size: 13px; font-weight: bold; color: #64748B; white-space:nowrap; }}
.action-btns {{ display: flex; gap: 8px; align-items: center; }}
.action-btn {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; display: flex; align-items: center; justify-content: center; }}
.action-btn:hover {{ color: #00D2FF; }}
.close-btn:hover {{ color: #FF4C4C; }}
.panel-title {{ margin: 0 0 8px 0; font-size: 12.5px; font-weight: bold; color: #00D2FF; display: flex; justify-content: space-between; align-items: flex-end; }}
.date-badge {{ font-size: 10px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper {{ position: relative; max-height: 285px; height: 285px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitch 20s infinite; }}
.carousel-item:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item:nth-child(2) {{ animation-delay: 5s; }}
.carousel-item:nth-child(3) {{ animation-delay: 10s; }}
.carousel-item:nth-child(4) {{ animation-delay: 15s; }}
@keyframes fadeSwitch {{ 0%, 22% {{ opacity: 1; z-index: 2; }} 25%, 97% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
@media (max-width: 1200px) {{ .glass-panel {{ position: relative; top: auto; left: auto; width: 90%; max-width: 350px; margin: 10px auto; display: block; }} }}
</style>
<div class="glass-panel" id="b3-top10-card">
<div class="header-bar"><span class="header-title"><img src="app/static/magicbookwater.png" style="width:18px; margin-right:6px; vertical-align:-3px;" onerror="this.style.display='none'"> 法人連買</span>
<div class="action-btns">
<label for="pause-card" class="action-btn pause-icon" title="暫停/播放輪播"></label>
<label for="min-card" class="action-btn min-icon" title="縮放"></label>
<label for="close-card" class="action-btn close-btn" title="關閉">✕</label>
</div></div>
<div class="carousel-wrapper">
<div class="carousel-item"><div class="panel-title"><span>🌐 外資日連買</span><span class="date-badge">{d_fo_day}</span></div>{fo_day_html}</div>
<div class="carousel-item"><div class="panel-title"><span>🏦 投信日連買</span><span class="date-badge">{d_it_day}</span></div>{it_day_html}</div>
<div class="carousel-item"><div class="panel-title"><span>👑 外資週連買</span><span class="date-badge">{d_fo_wk}</span></div>{fo_wk_html}</div>
<div class="carousel-item"><div class="panel-title"><span>🚀 投信週連買</span><span class="date-badge">{d_it_wk}</span></div>{it_wk_html}</div>
</div></div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
    except Exception as e: pass  

#b4 資券玻璃卡片
def render_b4_top10_glass_card():
    import pandas as pd
    import streamlit as st
    if 'b4_squeeze_radar' not in st.session_state or 'b4_risk_radar' not in st.session_state: return
    try:
        sq_data, rk_data = st.session_state['b4_squeeze_radar'], st.session_state['b4_risk_radar']
        df_sq, df_rk = sq_data['df'], rk_data['df']
        date_sq = sq_data['date'][-4:] if sq_data['date'] and len(sq_data['date']) >= 4 else "未知"
        date_rk = rk_data['date'][-4:] if rk_data['date'] and len(rk_data['date']) >= 4 else "未知"
        def get_pure_radar_stocks(df):
            if df is None or df.empty: return pd.DataFrame()
            df['代號'] = df['代號'].astype(str).str.strip()
            return df[(df['代號'].str.len() == 4) & (~df['代號'].str.startswith('00'))].copy()
        pure_sq, pure_rk = get_pure_radar_stocks(df_sq).head(20), get_pure_radar_stocks(df_rk).head(20)
        def make_radar_html(df, start_idx, theme):
            sub_df = df.iloc[start_idx : start_idx+10]
            if sub_df.empty: return "<p style='font-size:13.5px; text-align:center; color:#94A3B8; margin-top:40px;'>尚無目標</p>"
            html = "<ul style='padding-left: 0; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(sub_df.to_dict('records')):
                status = row.get('軋空評估', '') if theme == 'sq' else row.get('套牢評估', '')
                pct = row.get('漲跌幅', 0.0)
                short_status = status[:7] if len(status) > 7 else status
                pct_color = "#FF4C4C" if theme == 'sq' else "#00e676"               
                html += (
                    f"<li style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 13.5px; line-height: 1.4;'>"
                    f"  <div style='display: flex; align-items: center; width: 55%; overflow: hidden;'>"
                    f"      <b style='color:#FFF; width:22px; flex-shrink: 0;'>{start_idx + i + 1}.</b>"
                    f"      <span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['代號']}{row['名稱']}</span>"
                    f"  </div>"
                    f"  <div style='width: 25%; color:#FFD700; font-size: 11px; text-align: left; white-space:nowrap;'>{short_status}</div>"
                    f"  <div style='width: 20%; color:{pct_color}; font-weight:bold; text-align: right;'>{pct}%</div>"
                    f"</li>"
                )
            html += "</ul>"
            return html
        h_sq_1_10, h_sq_11_20 = make_radar_html(pure_sq, 0, 'sq'), make_radar_html(pure_sq, 10, 'sq')
        h_rk_1_10, h_rk_11_20 = make_radar_html(pure_rk, 0, 'rk'), make_radar_html(pure_rk, 10, 'rk')

        card_html = f"""
<input type="checkbox" id="close-b4-card" style="display:none;">
<input type="checkbox" id="min-b4-card" style="display:none;">
<input type="checkbox" id="pause-b4-card" style="display:none;">
<style>
#close-b4-card:checked ~ #b4-top10-card {{ display: none !important; }}
#min-b4-card:checked ~ #b4-top10-card .carousel-wrapper-b4 {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-b4-card:checked ~ #b4-top10-card {{ padding-bottom: 8px; width: 150px; height: auto; }}
#min-b4-card:checked ~ #b4-top10-card .min-icon-b4::after {{ content: '□'; font-size: 14px; }}
#min-b4-card:not(:checked) ~ #b4-top10-card .min-icon-b4::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
#pause-b4-card:checked ~ #b4-top10-card .carousel-item-b4 {{ animation-play-state: paused !important; }}
#pause-b4-card:checked ~ #b4-top10-card .pause-icon-b4::after {{ content: '▶'; font-size: 11px; color: #FFD700; }}
#pause-b4-card:not(:checked) ~ #b4-top10-card .pause-icon-b4::after {{ content: '⏸'; font-size: 11px; }}
@keyframes slideInDownB4 {{ from {{ transform: translateY(-50%); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
@keyframes radarBreath {{ 0%, 49.9% {{ border-color: rgba(188, 19, 254, 0.4); box-shadow: 0 4px 15px rgba(188, 19, 254, 0.15); }} 50%, 100% {{ border-color: rgba(0, 230, 118, 0.4); box-shadow: 0 4px 15px rgba(0, 230, 118, 0.1); }} }}
/* 💡 將 top: 75px 改為 top: 100px */
.glass-panel-b4 {{ position: fixed; top: 85px; left: 38vw; width: 15.5vw; min-width: 220px; background: rgba(20, 22, 35, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(188, 19, 254, 0.35); border-right: none; border-radius: 12px 0 0 12px; padding: 10px 12px; z-index: 999997; color: #E2E8F0;animation: slideInDownB4 0.6s cubic-bezier(0.25, 0.8, 0.25, 1);     transition: all 0.3s ease; box-sizing: border-box; }}
.header-bar-b4 {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title-b4 {{ font-size: 13px; font-weight: bold; color: #E2E8F0; white-space:nowrap; }}
.action-btns-b4 {{ display: flex; gap: 8px; align-items: center; }}
.action-btn-b4 {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; display: flex; align-items: center; justify-content: center; }}
.action-btn-b4:hover {{ color: #00D2FF; }}
.panel-title-b4 {{ margin: 0 0 8px 0; font-size: 12.5px; font-weight: bold; color: #bc13fe; display: flex; justify-content: space-between; align-items: flex-end; }}
.panel-title-b4.risk {{ color: #00e676; }}
.date-badge-b4 {{ font-size: 10px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper-b4 {{ position: relative; max-height: 285px; height: 285px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item-b4 {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitchB4 20s infinite; }}
.carousel-item-b4:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item-b4:nth-child(2) {{ animation-delay: 5s; }}
.carousel-item-b4:nth-child(3) {{ animation-delay: 10s; }}
.carousel-item-b4:nth-child(4) {{ animation-delay: 15s; }}
@keyframes fadeSwitchB4 {{ 0%, 22% {{ opacity: 1; z-index: 2; }} 25%, 97% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
@media (max-width: 1200px) {{ .glass-panel-b4 {{ position: relative; top: auto; left: auto; width: 90%; max-width: 350px; margin: 10px auto; display: block; }} }}
</style>
<div class="glass-panel-b4" id="b4-top10-card">
<div class="header-bar-b4"><span class="header-title-b4"><img src="app/static/magicbookground.png" style="width:18px; margin-right:6px; vertical-align:-3px;" onerror="this.style.display='none'">資券雷達</span>
<div class="action-btns-b4">
<label for="pause-b4-card" class="action-btn-b4 pause-icon-b4" title="暫停/播放輪播"></label>
<label for="min-b4-card" class="action-btn-b4 min-icon-b4" title="縮放"></label>
<label for="close-b4-card" class="action-btn-b4" title="關閉">✕</label>
</div></div>
<div class="carousel-wrapper-b4">
<div class="carousel-item-b4"><div class="panel-title-b4"><span>🚀 軋空(1-10)</span><span class="date-badge-b4">{date_sq}</span></div>{h_sq_1_10}</div>
<div class="carousel-item-b4"><div class="panel-title-b4"><span>🚀 軋空(11-20)</span><span class="date-badge-b4">{date_sq}</span></div>{h_sq_11_20}</div>
<div class="carousel-item-b4"><div class="panel-title-b4 risk"><span>☠ 套牢(1-10)</span><span class="date-badge-b4">{date_rk}</span></div>{h_rk_1_10}</div>
<div class="carousel-item-b4"><div class="panel-title-b4 risk"><span>☠ 套牢(11-20)</span><span class="date-badge-b4">{date_rk}</span></div>{h_rk_11_20}</div>
</div></div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
    except Exception as e: pass  

#B5 大腿動向玻璃卡片
def render_b5_top10_glass_card():
    import pandas as pd
    import streamlit as st
    if 'b5_1000' not in st.session_state or 'b5_400' not in st.session_state: return
    try:
        df_1000, df_400 = st.session_state['b5_1000'], st.session_state['b5_400']
        if df_1000.empty or df_400.empty: return
        latest_col_1000 = next((c for c in df_1000.columns if c.startswith('▼') and '6周' not in c), None)
        latest_col_400 = next((c for c in df_400.columns if c.startswith('▼') and '6周' not in c), None)
        if not latest_col_1000 or not latest_col_400: return
        date_str = latest_col_1000.replace('▼', '') 

        def get_pure(df):
            df['股票代號'] = df['股票代號'].astype(str).str.strip()
            return df[(df['股票代號'].str.len() == 4) & (~df['股票代號'].str.startswith('00'))].copy()
        df_1k_sub = get_pure(df_1000)[['股票代號', '股票名稱', '週動態', '▼6周增減', latest_col_1000]].copy()
        df_1k_sub = df_1k_sub.rename(columns={'▼6周增減': '6周(千)', latest_col_1000: '最新(千)', '週動態': '狀態(千)'})
        df_400_sub = get_pure(df_400)[['股票代號', '週動態', '▼6周增減', latest_col_400]].copy()
        df_400_sub = df_400_sub.rename(columns={'▼6周增減': '6周(四)', latest_col_400: '最新(四)', '週動態': '狀態(四)'})

        sync_df = pd.merge(df_1k_sub, df_400_sub, on='股票代號', how='inner')
        for col in ['6周(千)', '最新(千)', '6周(四)', '最新(四)']:
            sync_df[f"{col}_val"] = pd.to_numeric(sync_df[col].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False), errors='coerce').fillna(0)
        cond_6w = (sync_df['6周(千)_val'] > 0) & (sync_df['6周(四)_val'] > 0)
        top10_6w = sync_df[cond_6w].sort_values(by='6周(千)_val', ascending=False).head(10)
        cond_latest = (sync_df['最新(千)_val'] > 0) & (sync_df['最新(四)_val'] > 0)
        top10_latest = sync_df[cond_latest].sort_values(by='最新(千)_val', ascending=False).head(10)

        def unify_status_text(s):
            s = str(s)
            if "🚀" in s: return "🚀劇增"
            if "🔥" in s: return "🔥大增"
            if "📈" in s: return "📈小增"
            if "↗️" in s: return "↗️微增"
            if "🔄" in s: return "🔄持平"
            if "↘️" in s: return "↘️微減"
            if "📉" in s: return "📉小減"
            if "⚠️" in s: return "⚠️大減"
            if "🚨" in s: return "🚨劇減"
            return "⚪無字"
        def make_resonance_html(df, is_6w):
            if df.empty: return "<p style='font-size:13.5px; text-align:center; color:#94A3B8; margin-top:40px;'>尚無共振標的</p>"
            html = "<ul style='padding-left: 0; margin: 0; list-style-type: none;'>"
            for i, row in enumerate(df.to_dict('records')):
                if is_6w:
                    v1, v2 = row['6周(千)_val'], row['6周(四)_val']
                    info_html = f"<div style='display:flex; width:50%; justify-content:flex-end; color:#F59E0B; font-weight:bold; font-size:11px;'><span style='width:45px; text-align:right;'>{v1:.1f}%</span><span style='color:#94A3B8; font-size:12px; margin:0 2px;'>/</span><span style='width:40px; text-align:right;'>{v2:.1f}%</span></div>"
                else:
                    s1, s2 = unify_status_text(row.get('狀態(千)', '')), unify_status_text(row.get('狀態(四)', ''))
                    info_html = f"<div style='display:flex; width:50%; justify-content:flex-end; color:#F59E0B; font-size:10px;'><span style='width:40px; text-align:right;'>{s1}</span><span style='color:#94A3B8; font-size:12px; margin:0 2px;'>/</span><span style='width:40px; text-align:right;'>{s2}</span></div>"
                    
                html += (
                    f"<li style='display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; font-size:13.5px; line-height:1.4;'>"
                    f"  <div style='display:flex; align-items:center; width:50%; overflow:hidden;'>"
                    f"      <b style='color:#FFF; width:22px; flex-shrink:0;'>{i+1}.</b>"
                    f"      <span style='white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{row['股票代號']}{row['股票名稱']}</span>"
                    f"  </div>{info_html}</li>"
                )
            html += "</ul>"
            return html

        h_6w, h_latest = make_resonance_html(top10_6w, True), make_resonance_html(top10_latest, False)
        card_html = f"""
<input type="checkbox" id="close-b5-card" style="display:none;">
<input type="checkbox" id="min-b5-card" style="display:none;">
<input type="checkbox" id="pause-b5-card" style="display:none;">
<style>
#close-b5-card:checked ~ #b5-top10-card {{ display: none !important; }}
#min-b5-card:checked ~ #b5-top10-card .carousel-wrapper-b5 {{ max-height: 0; opacity: 0; margin-top: 0; }}
#min-b5-card:checked ~ #b5-top10-card {{ padding-bottom: 8px; width: 150px; height: auto; }}
#min-b5-card:checked ~ #b5-top10-card .min-icon-b5::after {{ content: '□'; font-size: 14px; }}
#min-b5-card:not(:checked) ~ #b5-top10-card .min-icon-b5::after {{ content: '_'; font-size: 14px; position: relative; top: -3px; }}
#pause-b5-card:checked ~ #b5-top10-card .carousel-item-b5 {{ animation-play-state: paused !important; }}
#pause-b5-card:checked ~ #b5-top10-card .pause-icon-b5::after {{ content: '▶'; font-size: 11px; color: #FFD700; }}
#pause-b5-card:not(:checked) ~ #b5-top10-card .pause-icon-b5::after {{ content: '⏸'; font-size: 11px; }}
@keyframes slideInDownB5 {{ from {{ transform: translateY(-50%); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
/* 💡 將 top: 75px 改為 top: 100px */
.glass-panel-b5 {{position: fixed; top: 85px; left: 53.5vw; width: 15.5vw; min-width: 220px; background: rgba(30, 25, 10, 0.88); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(245, 158, 11, 0.4); border-right: none; border-radius: 0; padding: 10px 12px; z-index: 999996; color: #E2E8F0; animation: slideInDownB5 0.7s cubic-bezier(0.25, 0.8, 0.25, 1); transition: all 0.3s ease; box-sizing: border-box;}}
.header-bar-b5 {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; margin-bottom: 8px; cursor: default; }}
.header-title-b5 {{ font-size: 13px; font-weight: bold; color: #FCD34D; white-space:nowrap; }}
.action-btns-b5 {{ display: flex; gap: 8px; align-items: center; }}
.action-btn-b5 {{ cursor: pointer; color: #94A3B8; font-weight: bold; transition: color 0.2s; user-select: none; display: flex; align-items: center; justify-content: center; }}
.action-btn-b5:hover {{ color: #F59E0B; }}
.panel-title-b5 {{ margin: 0 0 8px 0; font-size: 12.5px; font-weight: bold; color: #F59E0B; display: flex; justify-content: space-between; align-items: flex-end; }}
.date-badge-b5 {{ font-size: 10px; color: #94A3B8; font-weight: normal; }}
.carousel-wrapper-b5 {{ position: relative; max-height: 285px; height: 285px; overflow: hidden; transition: all 0.3s ease; opacity: 1; }}
.carousel-item-b5 {{ position: absolute; top: 0; left: 0; width: 100%; opacity: 0; animation: fadeSwitchB5 10s infinite; }}
.carousel-item-b5:nth-child(1) {{ animation-delay: 0s; }}
.carousel-item-b5:nth-child(2) {{ animation-delay: 5s; }}
@keyframes fadeSwitchB5 {{ 0%, 45% {{ opacity: 1; z-index: 2; }} 50%, 95% {{ opacity: 0; z-index: 1; }} 100% {{ opacity: 1; z-index: 2; }} }}
@media (max-width: 1200px) {{ .glass-panel-b5 {{ position: relative; top: auto; left: auto; width: 90%; max-width: 350px; margin: 10px auto; display: block; }} }}
</style>
<div class="glass-panel-b5" id="b5-top10-card">
<div class="header-bar-b5"><span class="header-title-b5"><img src="app/static/wirtleg.png" style="width:18px; margin-right:6px; vertical-align:-3px;" onerror="this.style.display='none'">大腿共振</span>
<div class="action-btns-b5">
<label for="pause-b5-card" class="action-btn-b5 pause-icon-b5" title="暫停/播放輪播"></label>
<label for="min-b5-card" class="action-btn-b5 min-icon-b5" title="縮放"></label>
<label for="close-b5-card" class="action-btn-b5" title="關閉">✕</label>
</div></div>
<div class="carousel-wrapper-b5">
<div class="carousel-item-b5"><div class="panel-title-b5"><span>📊 6周累積(1000/400)</span><span class="date-badge-b5">{date_str}</span></div>{h_6w}</div>
<div class="carousel-item-b5"><div class="panel-title-b5"><span>⚡ 週動能(1000/400)</span><span class="date-badge-b5">{date_str}</span></div>{h_latest}</div>
</div></div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
    except Exception as e: pass

# ==========================================
# 設置中心 懸浮卡片
# ==========================================
def render_settings_modal():
    import streamlit as st
    if st.session_state.get('show_settings', False):
        settings_css = """
        <style>
        .settings-modal-active {
            position: fixed !important; 
            top: 15% !important; left: 50% !important; transform: translateX(-50%) !important;
            background: rgba(15, 23, 42, 0.98) !important; 
            border: 2px solid #00D2FF !important; border-radius: 12px !important; 
            padding: 20px 25px !important; z-index: 9999999 !important;
            width: 90% !important; max-width: 650px !important; box-shadow: 0 8px 30px rgba(0, 210, 255, 0.4) !important;
            max-height: 85vh !important; overflow-y: auto !important;
        }
        .settings-drag-handle { cursor: grab; }
        .settings-drag-handle:active { cursor: grabbing; }
        </style>
        """
        st.markdown(settings_css, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="setting-anchor"></div>', unsafe_allow_html=True)
            col_title, col_x = st.columns([9, 1])
            with col_title:
                st.markdown("<h3 class='settings-drag-handle' style='color:#00D2FF; margin-top:0;' title='按住此處可拖曳視窗'>設置中心</h3>", unsafe_allow_html=True)
            with col_x:
                if st.button("✕", key="settings_btn_close_top"):
                    st.session_state['show_settings'] = False
                    st.rerun()

            st.markdown("<h4 style='color:#E2E8F0; font-size: 16px;'>外觀與濾鏡</h4>", unsafe_allow_html=True)
            current_theme = st.session_state.get('theme', 'dark')
            current_opacity = st.session_state.get('bg_opacity', 88)
            
            theme_options = ['dark', 'pink', 'green', 'purple','brown']
            theme_choice = st.radio("選擇背景主題 (將同步切換圖片)：", options=theme_options, format_func=lambda x: {'dark': "暗黑(預設)", 'pink': "鋼鐵褐", 'green': "翡翠綠", 'purple': "月影紫", 'brown':"沙漠棕"}[x], index=theme_options.index(current_theme) if current_theme in theme_options else 0, horizontal=True)
            
            opacity_val = st.slider("背景濾鏡透明度 (%)", min_value=0, max_value=100, value=current_opacity)
            
            st.markdown("---")
            st.markdown("<h4 style='color:#E2E8F0; font-size: 16px;'>快捷鍵配置 (點擊欄位後直接按下按鍵)</h4>", unsafe_allow_html=True)
            
            reverse_map = {v: k for k, v in st.session_state.get('custom_hotkeys', {"f1": "NavToB1", "f2": "NavToB2", "f3": "NavToB3", "f4": "NavToB4", "f5": "NavToB5", "f6": "NavToB6", "f7": "NavToB7", "alt+l": "NavToWatchlist", "escape": "登入"}).items()}
            
            col1, col2 = st.columns(2)
            new_hotkeys = {}
            with col1:
                new_hotkeys["NavToB1"] = st.text_input("法人動向", value=reverse_map.get("NavToB1", "f1"), key="kb1")
                new_hotkeys["NavToB2"] = st.text_input("法人掃貨", value=reverse_map.get("NavToB2", "f2"), key="kb2")
                new_hotkeys["NavToB3"] = st.text_input("法人連買", value=reverse_map.get("NavToB3", "f3"), key="kb3")
                new_hotkeys["NavToB4"] = st.text_input("資券動向", value=reverse_map.get("NavToB4", "f4"), key="kb4")
                new_hotkeys["NavToB6"] = st.text_input("鉅額交易", value=reverse_map.get("NavToB6", "f6"), key="kb6")
            with col2:
                new_hotkeys["NavToB5"] = st.text_input("大腿動向", value=reverse_map.get("NavToB5", "f5"), key="kb5")
                new_hotkeys["NavToB7"] = st.text_input("董監動向", value=reverse_map.get("NavToB7", "f7"), key="kb7")
                new_hotkeys["NavToWatchlist"] = st.text_input("建立名單", value=reverse_map.get("NavToWatchlist", "alt+l"), key="kb_wl")
                new_hotkeys["登入"] = st.text_input("登入", value=reverse_map.get("登入", "escape"), key="kb_login")

            st.markdown("<br>", unsafe_allow_html=True)
            
            col_ok, col_cancel = st.columns(2)
            with col_ok:
                if st.button("確認", use_container_width=True):
                    st.session_state['theme'] = theme_choice
                    st.session_state['bg_opacity'] = opacity_val
                    st.session_state['custom_hotkeys'] = {k.strip().lower(): v for v, k in new_hotkeys.items() if k.strip().lower()}
                    st.session_state['show_settings'] = False
                    st.rerun()
            with col_cancel:
                if st.button("取消", use_container_width=True):
                    st.session_state['show_settings'] = False
                    st.rerun()
                    
        keybind_js = """
        <script>
        setTimeout(() => {
            const container = window.parent.document.querySelector('.setting-anchor').closest('div[data-testid="stVerticalBlock"]');
            if (container && !container.classList.contains('settings-modal-active')) {
                container.classList.add('settings-modal-active');
            }
            container.querySelectorAll('input[type="text"]').forEach(input => {
                if(input.dataset.keybound) return;
                input.dataset.keybound = "true";
                input.addEventListener('keydown', function(e) {
                    e.preventDefault(); e.stopPropagation();
                    let combo = [];
                    if (e.ctrlKey) combo.push('ctrl'); if (e.altKey) combo.push('alt'); if (e.shiftKey) combo.push('shift');
                    let keyName = e.key.toLowerCase();
                    if (['control', 'alt', 'shift', 'meta', 'process'].includes(keyName)) return; 
                    if (keyName === ' ') keyName = 'space';
                    combo.push(keyName);
                    let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    nativeInputValueSetter.call(this, combo.join('+'));
                    this.dispatchEvent(new Event('input', { bubbles: true}));
                });
                input.addEventListener('focus', function() { this.style.boxShadow = '0 0 10px #FFD700'; });
                input.addEventListener('blur', function() { this.style.boxShadow = 'none'; });
            });
        }, 500);
        </script>
        """
        import streamlit.components.v1 as components
        components.html(keybind_js, height=0, width=0)

# ==========================================
# 🎓 課程 NPC 懸浮對話框
# ==========================================
def render_course_npc():
    import streamlit as st
    import streamlit.components.v1 as components  
    if st.session_state.get('show_course_npc', False):      
        if 'course_view' not in st.session_state:
            st.session_state['course_view'] = 'list'          
        current_view = st.session_state['course_view']        
        if current_view == 'list':
            # =========================
            # 📜 課程列表 (List View)
            # =========================
            html_code = """<style>
.npc-overlay {
position: fixed; bottom: 30px; right: 30px;
width: 650px; height: 75vh; max-height: 800px;
background: rgba(15, 23, 42, 0.96);
border: 2px solid #00D2FF; border-radius: 12px;
z-index: 9999999; display: flex; flex-direction: column;
padding: 25px; box-shadow: 0 8px 30px rgba(0, 210, 255, 0.3);
color: white; animation: slideUpNPC 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.npc-header { display: flex; align-items: flex-end; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; }
.npc-image {
width: 90px; height: 90px;
background-image: url('app/static/npcnatzu.png'); 
background-size: contain; background-repeat: no-repeat; background-position: bottom;
margin-right: 20px; filter: drop-shadow(0 0 5px rgba(0,210,255,0.5));
}
.npc-title-box { flex: 1; }
.npc-name { color: #00D2FF; font-weight: bold; font-size: 22px; margin-bottom: 6px; }
.npc-greet { font-size: 15px; color: #94A3B8; }
.course-list { flex: 1; overflow-y: auto; padding-right: 15px; }
.course-list::-webkit-scrollbar { width: 8px; }
.course-list::-webkit-scrollbar-thumb { background: rgba(0, 210, 255, 0.4); border-radius: 4px; }
.course-item { margin-bottom: 18px; padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; transition: 0.2s; }
.course-item.locked { cursor: not-allowed; background: rgba(0,0,0,0.2); }
.course-item.active { cursor: pointer; border-color: rgba(0, 210, 255, 0.4); }
.course-item.active:hover { background: rgba(0, 210, 255, 0.1); border-color: #00D2FF; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,210,255,0.2); }
.course-icon { width: 24px; height: 24px; object-fit: contain; margin-right: 8px; filter: drop-shadow(0 0 5px rgba(0,210,255,0.8)); transition: 0.3s; }
.course-item.locked .course-icon { filter: grayscale(100%) opacity(0.4); }
.course-item.active:hover .course-icon { filter: drop-shadow(0 0 10px #FFD700); transform: scale(1.1); }
.course-title { font-weight: bold; font-size: 16px; margin-bottom: 8px; display: flex; align-items: center; }
.course-item.locked .course-title { color: #64748B; }
.course-item.active .course-title { color: #FFD700; }
.course-desc { font-size: 14px; color: #CBD5E1; line-height: 1.6; }
.close-btn { position: absolute; top: 15px; right: 20px; cursor: pointer; color: #94A3B8; font-size: 24px; transition: 0.2s; z-index: 10; font-weight: bold; }
.close-btn:hover { color: #FF4C4C; transform: scale(1.1); }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<!-- 💡 放棄 onclick，改用 id 讓外部 JS 尋找並綁定事件 -->
<div class="close-btn" id="btn-close-list">✕</div>
<div class="npc-header">
<div class="npc-image"></div>
<div class="npc-title-box">
<div class="npc-name">籌碼導師</div>
<div class="npc-greet">「冒險者，選擇你想強化的能力吧！」</div>
</div>
</div>
<div class="course-list">
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 1. 宏觀經濟與景氣循環 (未開放)</div>
<div class="course-desc">學習解讀 GDP、CPI、利率與匯率等基本總體經濟指標，判斷目前大盤處於景氣擴張或衰退的哪個階段。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 2. 股市基本架構與名詞解析 (未開放)</div>
<div class="course-desc">認識台股交易規則、漲跌幅限制、各類委託單與基本盤面術語，建立進場前的基礎常識。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 3. 財報與基本面入門 (未開放)</div>
<div class="course-desc">學習閱讀三大財務報表（綜合損益表、資產負債表、現金流量表），學會挑選具備長期競爭力的公司。</div>
</div>

<!-- 💡 放棄 onclick，改用 id="btn-open-course-4" -->
<div class="course-item active" id="btn-open-course-4">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 4. 量價關係與盤面解讀 (點擊進入)</div>
<div class="course-desc">對照成交量與股價漲跌的互動（如價漲量增、量價背離），判斷多空雙方的企圖心與買賣力道。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 5. 技術分析與指標應用 (未開放)</div>
<div class="course-desc">熟悉常用技術指標（如均線 MA、MACD、RSI、KDJ），掌握支撐壓力與趨勢轉折點。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 6. 籌碼面追蹤：法人與大戶結構 (未開放)</div>
<div class="course-desc">分析外資、投信、自營商動向及大戶持股比例，透過資金流向尋找主力默默佈局的標的。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 7. 券資關係與融資融券分析 (未開放)</div>
<div class="course-desc">觀察融資餘額、融券張數與券資比變化，評估市場散戶情緒及潛在的「軋空」或「多殺多」力道。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 8. 產業趨勢與題材選股 (未開放)</div>
<div class="course-desc">掌握主流產業輪動脈絡（如半導體、AI 供應鏈、綠能等），在對的時間點佈局具備成長爆發力的賽道。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 9. 資金控管與風險管理 (未開放)</div>
<div class="course-desc">學習單筆投資部位配置、分批進場策略、停損停利機制，避免因情緒失控而遭受重大虧損。</div>
</div>
<div class="course-item locked">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon"> 10. 交易心理學與個人策略總結 (未開放)</div>
<div class="course-desc">克服貪婪與恐懼的心理障礙，並回測、修正並建立專屬於自己的穩定獲利交易系統。</div>
</div>
</div>
</div>"""
        else:
            # =========================
            # 📖 第4課詳情 (Detail View)
            # =========================
            html_code = """<style>
.npc-overlay {
position: fixed; bottom: 30px; right: 30px;
width: 800px; height: 85vh; max-height: 900px;
background: rgba(15, 23, 42, 0.98);
border: 2px solid #00D2FF; border-radius: 12px;
z-index: 9999999; display: flex; flex-direction: column;
padding: 25px; box-shadow: 0 8px 30px rgba(0, 210, 255, 0.4);
color: white; animation: slideUpNPC 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.top-actions { position: absolute; top: 15px; right: 20px; display: flex; gap: 12px; z-index: 10; }
.action-btn { cursor: pointer; color: #94A3B8; font-size: 20px; font-weight:bold; transition: 0.2s; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); width: 32px; height: 32px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.1); }
.action-btn:hover { background: rgba(0,210,255,0.3); color: #FFF; transform: scale(1.1); border-color: #00D2FF; }
.action-btn.close:hover { background: rgba(255,76,76,0.8); border-color: #FF4C4C; }
.detail-header { display: flex; align-items: flex-end; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; gap: 20px; }
.npc-big-image {
width: 160px; height: 180px;
background-image: url('app/static/npcroxy.png'); 
background-size: contain; background-repeat: no-repeat; background-position: bottom;
filter: drop-shadow(0 0 10px rgba(0,210,255,0.6)); flex-shrink: 0;
}
.dialogue-box {
flex: 1; background: rgba(0, 210, 255, 0.08); border: 1px solid rgba(0, 210, 255, 0.3);
border-radius: 12px; padding: 18px; position: relative; margin-bottom: 10px;
}
.dialogue-box::before {
content: ''; position: absolute; left: -14px; bottom: 30px;
border-width: 12px 14px 12px 0; border-style: solid; border-color: transparent rgba(0, 210, 255, 0.3) transparent transparent;
}
.npc-name { color: #00D2FF; font-weight: bold; font-size: 20px; margin-bottom: 8px; }
.npc-text { font-size: 15px; color: #E2E8F0; line-height: 1.6; }
.table-container { flex: 1; overflow-y: auto; padding-right: 10px; }
.table-container::-webkit-scrollbar { width: 8px; }
.table-container::-webkit-scrollbar-thumb { background: rgba(0, 210, 255, 0.4); border-radius: 4px; }
.pv-table { width: 100%; border-collapse: collapse; font-size: 15px; text-align: center; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 12px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.trend-up { color: #FF4C4C; font-weight: bold; }
.trend-down { color: #00E676; font-weight: bold; }
.trend-flat { color: #FFD700; font-weight: bold; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<!-- 💡 同樣放棄 onclick，賦予專屬 ID -->

<label class="action-btn close"
       id="btn-close-detail"
       title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「量價關係是市場最真實的足跡！仔細看這張表，當『量』與『價』出現背離時，就是趨勢即將反轉的危險警訊喔！」</div>
</div>
</div>
<div class="table-container">
<table class="pv-table">
<thead>
<tr><th width="15%">趨勢</th><th width="20%">狀態</th><th width="65%">市場含義</th></tr>
</thead>
<tbody>
<tr><td class="trend-up">上漲</td><td>價升量縮</td><td style="text-align: left;">量價背離，下方有承接，短期回調，後續拉高</td></tr>
<tr><td class="trend-up">上漲</td><td>放量滯漲</td><td style="text-align: left;">趨勢高位，拋壓增大，即將見頂反轉，減倉清倉</td></tr>
<tr><td class="trend-up">上漲</td><td>縮量大漲</td><td style="text-align: left;">趨勢中途，縮量加速，鎖倉高控盤，延續上漲</td></tr>
<tr><td class="trend-up">上漲</td><td>放量大漲</td><td style="text-align: left;">價漲量增，量價齊升，多方吸籌，持續看漲</td></tr>
<tr><td class="trend-down">下跌</td><td>縮量小跌</td><td style="text-align: left;">主力洗盤，拋壓減弱，止跌位置，擇機進場</td></tr>
<tr><td class="trend-down">下跌</td><td>放量小跌</td><td style="text-align: left;">見底信號，買方增強，越跌越買，反轉新倉</td></tr>
<tr><td class="trend-down">下跌</td><td>縮量大跌</td><td style="text-align: left;">一致看空，無人接盤，下跌中繼，加速下跌</td></tr>
<tr><td class="trend-down">下跌</td><td>放量大跌</td><td style="text-align: left;">跟風砸盤，大量賣出，高位出貨，持續下跌</td></tr>
<tr><td class="trend-flat">平量</td><td>平量滯漲</td><td style="text-align: left;">拋壓增大，越漲越難，高位見頂</td></tr>
<tr><td class="trend-flat">平量</td><td>平量大漲</td><td style="text-align: left;">一致看漲，沒有拋壓，鎖倉高控盤，加速上漲</td></tr>
<tr><td class="trend-flat">平量</td><td>平量價縮</td><td style="text-align: left;">下跌中繼，弱反彈信號，逢高減倉</td></tr>
<tr><td class="trend-flat">平量</td><td>平量大跌</td><td style="text-align: left;">一致看空，沒有承接，下跌中繼，加速下跌</td></tr>
</tbody>
</table>
</div>
</div>"""
        # 渲染畫面
        st.markdown(html_code, unsafe_allow_html=True)     
        # =========================
        # 🔗 核心隱藏按鈕 (真實操控狀態的樞紐)
        # =========================
        if st.button("CloseNPC"):
            st.session_state['show_course_npc'] = False
            st.session_state['course_view'] = 'list'
            st.rerun()
            
        if st.button("OpenCourse4"):
            st.session_state['course_view'] = 'detail'
            st.rerun()
            
        if st.button("BackToList"):
            st.session_state['course_view'] = 'list'
            st.rerun()
            
        # 💡 JS 強制綁定與隱形引擎：這段腳本會去尋找上面那三顆真實的 Streamlit 按鈕，把他們藏到畫面之外 (避免破壞 UI)
        # 然後主動捕捉帶有我們 ID (如 btn-close-list) 的 HTML 元素，並注入點擊事件！
        bind_js = """<script>
setInterval(() => {
    const doc = window.parent.document;
    if (!doc) return;
    
    // 尋找 Streamlit 生成的實體按鈕
    const stBtns = Array.from(doc.querySelectorAll('button'));
    const btnClose = stBtns.find(b => b.textContent.includes('CloseNPC'));
    const btnOpen4 = stBtns.find(b => b.textContent.includes('OpenCourse4'));
    const btnBack = stBtns.find(b => b.textContent.includes('BackToList'));
    // 安全隱藏實體按鈕 (將他們趕出畫面外，保證 React 能捕捉點擊)
    [btnClose, btnOpen4, btnBack].forEach(b => {
        if(b) {
            const container = b.closest('div[data-testid="stElementContainer"]');
            if(container) {
                container.style.position = 'fixed';
                container.style.top = '-9999px';
                container.style.left = '-9999px';
            }
        }
    });

    // 建立事件綁定工廠
    const bindEvent = (uiId, stBtn) => {
        const uiEl = doc.getElementById(uiId);
        // 若找到該 UI 元素且尚未被綁定過
        if(uiEl && !uiEl.dataset.hooked) {
            uiEl.dataset.hooked = 'true'; // 標記為已綁定
            uiEl.style.cursor = 'pointer'; 
            uiEl.addEventListener('click', (e) => {
                e.preventDefault();
                if(stBtn) stBtn.click(); // 點擊時，觸發被隱藏的 Streamlit 按鈕
            });
        }
    };
    // 替我們的自訂 UI 注入對應的點擊事件
    bindEvent('btn-close-list', btnClose);
    bindEvent('btn-open-course-4', btnOpen4);
    bindEvent('btn-back-detail', btnBack);
    bindEvent('btn-close-detail', btnClose);
}, 300); // 每 300 毫秒掃描一次，保證絕對綁定成功
</script>"""
        components.html(bind_js, height=0, width=0) 
