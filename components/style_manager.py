# components/style_manager.py
import streamlit as st
import base64
import os
import random
import streamlit.components.v1 as components

def apply_global_theme(image_path="./image/派對盛宴邀請.png"):
    """合併原本的 load_global_css 與 set_background，統一管理所有視覺與拖曳引擎"""
    theme = st.session_state.get('theme', 'dark')
    opacity = st.session_state.get('bg_opacity', 88) / 100.0
    block_opacity = opacity * 0.7 
    
    # 1. 統一使用字典管理顏色與對應的城市圖片，告別落長的 if-else
    theme_settings = {
        'pink':   {'rgb': '139, 109, 98', 'img': './image/鐵風堡.png'},
        'green':  {'rgb': '0, 54, 16',    'img': './image/翡翠林鎮.png'},
        'purple': {'rgb': '87, 99, 158',  'img': './image/月下綠洲城.png'},
        'brown':  {'rgb': '161, 115, 0',  'img': './image/沙漠衛星都市.png'},
        'dark':   {'rgb': '15, 23, 42',   'img': image_path}
    }
    
    # 獲取當前設定，找不到就用 dark 預設
    current = theme_settings.get(theme, theme_settings['dark'])
    base_color = f"rgba({current['rgb']}, {opacity})"
    block_bg = f"rgba({current['rgb']}, {block_opacity})"
    actual_image = current['img']
    
    # 防呆：圖片不存在就用預設的
    if not os.path.exists(actual_image):
        actual_image = image_path

    # 2. 處理背景圖片轉換
    bg_image_css = ""
    try:
        with open(actual_image, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()
        # 成功讀取圖片：使用漸層濾鏡 + 圖片
        bg_image_css = f"""
            background-image: linear-gradient({base_color}, {base_color}), url(data:image/png;base64,{encoded_string});
            background-size: cover; background-position: center center; background-attachment: fixed;
        """
    except FileNotFoundError:
        # 找不到圖片的退路：至少顯示單色背景
        bg_image_css = f"background-color: {base_color} !important;"

    # 3. 組合所有 CSS (一次性渲染)
    global_css = f"""
    <style>
    /* 隱藏預設 UI */
    #MainMenu, footer, header, div[data-testid="stToolbar"] {{ visibility: hidden; }}
    .block-container {{ padding-top: 0rem; }}
    
    /* 懸浮視窗縮放與圖示特效 */
    .glass-panel, .glass-panel-b2, .glass-panel-b4, .glass-panel-b5, .npc-overlay, .settings-modal-active {{ resize: both !important; overflow: auto !important; }}
    img[src*="icon-card"], img[alt*="icon-card"] {{ cursor: pointer !important; transition: all 0.2s ease !important; }}
    img[src*="icon-card"]:hover, img[alt*="icon-card"]:hover {{ transform: scale(1.08) !important; filter: drop-shadow(0 0 8px rgba(0, 210, 255, 0.6)) !important; }}
    img[src*="icon-card"]:active, img[alt*="icon-card"]:active {{ transform: scale(0.95) !important; }}

    /* 應用背景與區塊毛玻璃 */
    .stApp {{ {bg_image_css} }}
    div[data-testid="stVerticalBlock"] > div[style*="border"] {{ background-color: {block_bg} !important; backdrop-filter: blur(4px); }}
    
    /* 字體、輸入框與按鈕顏色 */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText {{ color: #E2E8F0 !important; }}
    [data-testid="stAlert"] {{ background-color: transparent !important; border: 1px solid #2D3748 !important; }}
    [data-testid="stSidebar"] {{ background-color: rgba(17, 22, 34, 0.95) !important; border-right: 1px solid #1E293B; }}
    .stTextInput>div>div>input {{ background-color: #1A202C !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }}
    div[data-testid="stDataFrame"] {{ background-color: #111622 !important; border: 1px solid #1E293B !important; border-radius: 6px; }}
    .stButton > button, .stLinkButton > a {{ background-color: #1E293B !important; color: #94A3B8 !important; border: 1px solid #334155 !important; transition: all 0.2s ease-in-out; }}
    .stButton > button:hover, .stLinkButton > a:hover {{ border-color: #00D2FF !important; color: #00D2FF !important; box-shadow: 0 0 8px rgba(0, 210, 255, 0.2); }}
    </style>
    """
    st.markdown(global_css, unsafe_allow_html=True)

    # 4. 載入全域拖曳與點擊監聽引擎 (保留你原本的 JavaScript)
    drag_engine_js = """
    <script>
    (function() {
        if (window.parent.window.customDragDelegated) return;
        window.parent.window.customDragDelegated = true;
        const doc = window.parent.document;
        
        // --- 1. 一鍵收合邏輯 ---
        doc.addEventListener('click', (e) => {
            let isIconCard = false;
            let t = e.target;
            if (t.tagName === 'IMG' && ((t.src && t.src.includes('icon-card')) || (t.alt && t.alt.includes('icon-card')))) { isIconCard = true; } 
            else if (t.closest) {
                let parentImg = t.closest('div[data-testid="stImage"]')?.querySelector('img');
                if (parentImg && ((parentImg.src && parentImg.src.includes('icon-card')) || (parentImg.alt && parentImg.alt.includes('icon-card')))) { isIconCard = true; }
            }
            if (isIconCard) {
                e.preventDefault(); e.stopPropagation();
                let cb2 = doc.getElementById('min-b2-card'), cb3 = doc.getElementById('min-card'), cb4 = doc.getElementById('min-b4-card'), cb5 = doc.getElementById('min-b5-card');
                let anyOpen = (cb2 && !cb2.checked) || (cb3 && !cb3.checked) || (cb4 && !cb4.checked) || (cb5 && !cb5.checked);
                if (cb2) cb2.checked = anyOpen; if (cb3) cb3.checked = anyOpen; if (cb4) cb4.checked = anyOpen; if (cb5) cb5.checked = anyOpen;
            }
        }, true);

        // --- 2. 拖曳引擎 ---
        let isDragging = false, currentEl = null, startX, startY, initialX, initialY;
        const onDown = (e) => {
            let handle = e.target.closest('.header-bar, .header-bar-b2, .header-bar-b4, .header-bar-b5, .npc-drag-handle, .settings-drag-handle');
            if (!handle || e.target.closest('button, input, label, .action-btn, .action-btn-b2, .action-btn-b4, .action-btn-b5')) return;
            let el = handle.closest('.glass-panel, .glass-panel-b2, .glass-panel-b4, .glass-panel-b5, .npc-wrapper, .settings-modal-active');
            if (!el) el = handle.closest('div[data-testid="stVerticalBlock"].settings-modal-active');
            if (!el) return;
            
            isDragging = true; currentEl = el;
            let clientX = e.touches ? e.touches[0].clientX : e.clientX;
            let clientY = e.touches ? e.touches[0].clientY : e.clientY;
            startX = clientX; startY = clientY;
            let rect = el.getBoundingClientRect();
            
            el.style.transition = 'none';
            el.style.left = rect.left + 'px'; el.style.top = rect.top + 'px';
            el.style.right = 'auto'; el.style.bottom = 'auto'; el.style.transform = 'none'; el.style.margin = '0';
            initialX = rect.left; initialY = rect.top; handle.style.cursor = 'grabbing';
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
        
        doc.addEventListener('mousedown', onDown); doc.addEventListener('touchstart', onDown, {passive: false});
        doc.addEventListener('mousemove', onMove, {passive: false}); doc.addEventListener('touchmove', onMove, {passive: false});
        doc.addEventListener('mouseup', onUp); doc.addEventListener('touchend', onUp);
    })();
    </script>
    """
    components.html(drag_engine_js, height=0, width=0)

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
                    # 💡 修改1：字體加大至 13.5px (對齊B4)，並加入 flex-shrink: 0 確保數值區塊絕對不會被擠壓換行
                    info_html = f"<div style='display:flex; justify-content:flex-end; align-items:center; color:#F59E0B; font-weight:bold; font-size:13.5px; white-space:nowrap; flex-shrink:0;'><span style='width:48px; text-align:right;'>{v1:.1f}%</span><span style='color:#94A3B8; font-size:13.5px; margin:0 3px;'>/</span><span style='width:48px; text-align:right;'>{v2:.1f}%</span></div>"
                else:
                    s1, s2 = unify_status_text(row.get('狀態(千)', '')), unify_status_text(row.get('狀態(四)', ''))
                    # 💡 修改2：狀態文字加大至 11px (對齊B4)，同樣設定 flex-shrink: 0
                    info_html = f"<div style='display:flex; justify-content:flex-end; align-items:center; color:#F59E0B; font-size:11px; white-space:nowrap; flex-shrink:0;'><span style='width:48px; text-align:right;'>{s1}</span><span style='color:#94A3B8; font-size:11px; margin:0 3px;'>/</span><span style='width:48px; text-align:right;'>{s2}</span></div>"
                    
                html += (
                    f"<li style='display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; font-size:13.5px; line-height:1.4;'>"
                    # 💡 修改3：左側股票區塊捨棄 width:50%，改用 flex:1 自動吃掉剩餘空間，加上 margin-right 稍微拉近數值間距，避免文字跑到下一行
                    f"  <div style='display:flex; align-items:center; flex:1; overflow:hidden; margin-right:8px;'>"
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
<div class="close-btn" id="btn-close-list">✕</div>
<div class="npc-header">
<div class="npc-image"></div>
<div class="npc-title-box">
<div class="npc-name">籌碼導師</div>
<div class="npc-greet">「冒險者，選擇你想強化的能力吧！」</div>
</div>
</div>
<div class="course-list">
<div class="course-item active" id="btn-open-course-1">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 1. 宏觀經濟與景氣循環</div>
<div class="course-desc">學習解讀 GDP、CPI、利率與匯率等基本總體經濟指標，判斷目前大盤處於景氣擴張或衰退的哪個階段。</div>
</div>
<div class="course-item active" id="btn-open-course-2">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 2. 股市基本架構與名詞解析</div>
<div class="course-desc">認識台股交易規則、漲跌幅限制、各類委託單與基本盤面術語，建立進場前的基礎常識。</div>
</div>
<div class="course-item active" id="btn-open-course-3">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 3. 財報與基本面入門</div>
<div class="course-desc">學習閱讀三大財務報表（綜合損益表、資產負債表、現金流量表），學會挑選具備長期競爭力的公司。</div>
</div>
<div class="course-item active" id="btn-open-course-4">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 4. 量價關係與盤面解讀</div>
<div class="course-desc">對照成交量與股價漲跌的互動（如價漲量增、量價背離），判斷多空雙方的企圖心與買賣力道。</div>
</div>
<div class="course-item active" id="btn-open-course-5">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 5. 技術分析與指標應用</div>
<div class="course-desc">熟悉常用技術指標（如均線 MA、MACD、RSI、KDJ），掌握支撐壓力與趨勢轉折點。</div>
</div>
<div class="course-item active" id="btn-open-course-6">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 6. 籌碼面追蹤：法人與大戶結構</div>
<div class="course-desc">認識外資、投信、自營商、大戶持股與分點集中度，透過籌碼變化觀察資金可能正在集中或分散。</div>
</div>
<div class="course-item active" id="btn-open-course-7">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 7. 券資關係與融資融券分析</div>
<div class="course-desc">觀察融資餘額、融券張數與券資比變化，評估市場散戶情緒及潛在的「軋空」或「多殺多」力道。</div>
</div>
<div class="course-item active" id="btn-open-course-8">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 8. 產業趨勢與題材選股</div>
<div class="course-desc">掌握主流產業輪動脈絡（如半導體、AI 供應鏈、綠能等），在對的時間點佈局具備成長爆發力的賽道。</div>
</div>
<div class="course-item active" id="btn-open-course-9">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 9. 資金控管與風險管理</div>
<div class="course-desc">學習單筆投資部位配置、分批進場策略、停損停利機制，避免因情緒失控而遭受重大虧損。</div>
</div>
<div class="course-item active" id="btn-open-course-10">
<div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">Lv 10. 交易心理學與個人策略總結</div>
<div class="course-desc">克服貪婪與恐懼的心理障礙，並回測、修正並建立專屬於自己的穩定獲利交易系統。</div>
</div>
</div>
</div>"""
            
        elif current_view == 'detail_1':
            # =========================
            # 📖 第1課詳情 (宏觀經濟與景氣循環)
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: center; margin-bottom: 20px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 15px 0 8px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「冒險者注意！經濟並不是永遠上升，而是不斷『🟢 復甦 → 擴張 → 過熱 → 放緩 → 衰退』的循環。現在的市場環境，究竟該積極、觀望，還是提高風險意識？讓我們從總體經濟數據中找答案吧！」</div>
</div>
</div>
<div class="table-container">

<div class="section-title">📊 總體經濟關鍵指標解析</div>
<table class="pv-table">
<thead>
<tr><th width="15%">指標</th><th width="35%">主要觀察什麼</th><th width="50%">上升通常代表對市場的初步影響</th></tr>
</thead>
<tbody>
<tr><td><b>GDP</b></td><td style="text-align: left;">經濟成長速度</td><td style="text-align: left;">經濟活動增加 🟢 景氣可能擴張</td></tr>
<tr><td><b>CPI</b></td><td style="text-align: left;">物價與通膨</td><td style="text-align: left;">生活成本上升 🟠 可能增加升息壓力</td></tr>
<tr><td><b>利率</b></td><td style="text-align: left;">資金成本</td><td style="text-align: left;">借錢成本提高 🔴 股市估值可能承壓</td></tr>
<tr><td><b>匯率</b></td><td style="text-align: left;">貨幣強弱</td><td style="text-align: left;">資金與出口環境變化 🟡 需搭配產業判讀</td></tr>
</tbody>
</table>

<div class="section-title">📈 景氣循環階段與市場情緒</div>
<table class="pv-table">
<thead>
<tr><th width="15%">階段</th><th width="20%">經濟狀況</th><th width="40%">常見現象</th><th width="25%">市場情緒</th></tr>
</thead>
<tbody>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 復甦</td><td style="text-align: left;">經濟開始回暖</td><td style="text-align: left;">GDP改善、企業活動增加</td><td>信心逐漸恢復</td></tr>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 擴張</td><td style="text-align: left;">經濟持續成長</td><td style="text-align: left;">消費增加、企業獲利改善</td><td>市場偏樂觀</td></tr>
<tr><td style="color:#FB923C; font-weight:bold;">🟠 過熱</td><td style="text-align: left;">成長過快</td><td style="text-align: left;">通膨升高、可能升息</td><td>市場開始出現壓力</td></tr>
<tr><td style="color:#F87171; font-weight:bold;">🔴 放緩</td><td style="text-align: left;">成長開始下降</td><td style="text-align: left;">消費與企業活動減弱</td><td>市場提高警戒</td></tr>
<tr><td style="color:#EF4444; font-weight:bold;">🚨 衰退</td><td style="text-align: left;">經濟明顯收縮</td><td style="text-align: left;">GDP下降、失業可能增加</td><td>市場偏悲觀</td></tr>
</tbody>
</table>

<div class="section-title">⚡ 景氣循環核心狀態對照</div>
<table class="pv-table">
<thead>
<tr><th width="30%">景氣狀態</th><th width="40%">核心數據表現</th><th width="30%">市場含義</th></tr>
</thead>
<tbody>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 景氣復甦</td><td>GDP↑ / CPI→ / 利率低</td><td style="text-align: left;">景氣回升，初升段</td></tr>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 經濟擴張</td><td>GDP↑↑ / 企業活動↑ / 市場偏多</td><td style="text-align: left;">多頭主升段延續</td></tr>
<tr><td style="color:#FB923C; font-weight:bold;">🟠 景氣過熱</td><td>GDP↑ / CPI↑↑ / 利率↑</td><td style="text-align: left;">通膨升溫，注意緊縮</td></tr>
<tr><td style="color:#F87171; font-weight:bold;">🔴 經濟放緩</td><td>GDP↓ / 消費↓ / 企業成長減速</td><td style="text-align: left;">動能減弱，防守為主</td></tr>
<tr><td style="color:#EF4444; font-weight:bold;">🚨 經濟衰退</td><td>GDP↓↓ / 失業↑ / 市場風險升高</td><td style="text-align: left;">熊市風險，資金避險</td></tr>
</tbody>
</table>

</div>
</div>"""
        elif current_view == 'detail_2':
            # =========================
            # 📖 第2課詳情 (股市基本架構與名詞解析)
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 15px 0 8px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「冒險者，歡迎來到基礎訓練營！進入市場前，熟悉『盤面術語』與『市場角色』是最基本的要求。記住，台股是『紅漲綠跌』，搞懂這些名詞，未來的籌碼分析才會事半功倍喔！」</div>
</div>
</div>
<div class="table-container">

<div class="section-title">📖 盤面速讀與狀態判讀</div>
<table class="pv-table">
<thead>
<tr><th width="20%">名詞</th><th width="40%">簡單理解</th><th width="40%">新手要知道什麼</th></tr>
</thead>
<tbody>
<tr><td><b>💰 股價</b></td><td style="text-align: left;">市場目前願意成交的價格</td><td style="text-align: left;">股票價格會隨買賣需求變動</td></tr>
<tr><td><b>📦 成交量</b></td><td style="text-align: left;">有多少股票正在交易</td><td style="text-align: left;">代表市場參與程度</td></tr>
<tr><td><b style="color:#FF4C4C;">📈 漲幅</b></td><td style="text-align: left;">今天比昨天上漲多少</td><td style="text-align: left;">觀察市場強弱</td></tr>
<tr><td><b style="color:#00E676;">📉 跌幅</b></td><td style="text-align: left;">今天比昨天下跌多少</td><td style="text-align: left;">觀察市場賣壓</td></tr>
<tr><td><b style="color:#FF4C4C;">🔴 買方</b></td><td style="text-align: left;">想用目前價格買股票的人</td><td style="text-align: left;">買盤增加可能推升價格</td></tr>
<tr><td><b style="color:#00E676;">🟢 賣方</b></td><td style="text-align: left;">想賣出股票的人</td><td style="text-align: left;">賣壓增加可能壓低價格</td></tr>
</tbody>
</table>

<table class="pv-table">
<thead>
<tr><th width="25%">狀態</th><th width="40%">一眼判讀</th><th width="35%">初步理解</th></tr>
</thead>
<tbody>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 買盤積極</td><td>股價↑ / 成交量↑</td><td style="text-align: left;">市場買方積極</td></tr>
<tr><td style="color:#F87171; font-weight:bold;">🔴 賣壓增加</td><td>股價↓ / 成交量↑</td><td style="text-align: left;">市場賣方積極</td></tr>
<tr><td style="color:#FACC15; font-weight:bold;">🟡 市場觀望</td><td>股價→ / 成交量↓</td><td style="text-align: left;">市場交易意願降低</td></tr>
<tr><td style="color:#FB923C; font-weight:bold;">🟠 價格波動加劇</td><td>高低價差↑ / 成交量↑</td><td style="text-align: left;">多空雙方競爭激烈</td></tr>
</tbody>
</table>

<div class="section-title">🏷️ 盤面常見名詞</div>
<table class="pv-table">
<thead>
<tr><th width="20%">名詞</th><th width="40%">一眼理解</th><th width="40%">代表什麼</th></tr>
</thead>
<tbody>
<tr><td><b>開盤價</b></td><td style="text-align: left;">今天第一筆成交價</td><td style="text-align: left;">市場開盤的第一個價格</td></tr>
<tr><td><b>最高價</b></td><td style="text-align: left;">今天最高成交價格</td><td style="text-align: left;">多方今天推到哪裡</td></tr>
<tr><td><b>最低價</b></td><td style="text-align: left;">今天最低成交價格</td><td style="text-align: left;">空方今天壓到哪裡</td></tr>
<tr><td><b>收盤價</b></td><td style="text-align: left;">最後成交價格</td><td style="text-align: left;">當日市場最後結果</td></tr>
<tr><td><b>昨收價</b></td><td style="text-align: left;">昨天收盤價格</td><td style="text-align: left;">判斷今日漲跌的基準</td></tr>
<tr><td><b>成交量</b></td><td style="text-align: left;">今天交易多少張</td><td style="text-align: left;">市場熱度</td></tr>
<tr><td style="color:#00E676; font-weight:bold;">內盤</td><td style="text-align: left;">主動賣方成交</td><td style="text-align: left;">賣方較積極</td></tr>
<tr><td style="color:#FF4C4C; font-weight:bold;">外盤</td><td style="text-align: left;">主動買方成交</td><td style="text-align: left;">買方較積極</td></tr>
</tbody>
</table>

<div class="section-title">🎭 市場角色 (籌碼追蹤前置)</div>
<table class="pv-table">
<thead>
<tr><th width="30%">市場角色</th><th width="45%">他們是誰</th><th width="25%">深入章節</th></tr>
</thead>
<tbody>
<tr><td>👤 一般投資人</td><td style="text-align: left;">個人買賣股票</td><td>Lv 7</td></tr>
<tr><td style="color:#FACC15; font-weight:bold;">🌍 外資</td><td style="text-align: left;">海外資金與機構投資人</td><td>Lv 6</td></tr>
<tr><td style="color:#4ADE80; font-weight:bold;">🏦 投信</td><td style="text-align: left;">國內基金與資產管理資金</td><td>Lv 6</td></tr>
<tr><td style="color:#60A5FA; font-weight:bold;">⚙️ 自營商</td><td style="text-align: left;">證券商自有資金交易</td><td>Lv 6</td></tr>
<tr><td style="color:#bc13fe; font-weight:bold;">🦈 大型持有人</td><td style="text-align: left;">持有較大量股票的帳戶</td><td>Lv 6</td></tr>
<tr><td style="color:#FF4C4C; font-weight:bold;">💰 融資</td><td style="text-align: left;">投資人使用槓桿買股票的人</td><td>Lv 7</td></tr>
<tr><td style="color:#00e676; font-weight:bold;">📉 融券/借券</td><td style="text-align: left;">交易者進行放空相關交易者</td><td>Lv 7</td></tr>
</tbody>
</table>

</div>
</div>"""            
        elif current_view == 'detail_3':
            # =========================
            # 📖 第3課詳情 (財報與基本面入門)
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 15px 0 8px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「冒險者，想找出真正能長期幫你賺錢的金雞母嗎？財報就是公司的體檢表！學會看懂基本面，才不會被虛假的包裝騙了喔！」</div>
</div>
</div>
<div class="table-container">

<div class="section-title">📖 三大財務報表白話理解</div>
<table class="pv-table">
<thead>
<tr><th width="25%">財務報表</th><th width="35%">白話理解</th><th width="40%">主要看什麼</th></tr>
</thead>
<tbody>
<tr><td><b>📈 綜合損益表</b></td><td style="text-align: left;">公司這段時間賺多少</td><td style="text-align: left;">營收、毛利、營業利益、淨利</td></tr>
<tr><td><b>🏦 資產負債表</b></td><td style="text-align: left;">公司現在有多少家底</td><td style="text-align: left;">資產、負債、股東權益</td></tr>
<tr><td><b>💵 現金流量表</b></td><td style="text-align: left;">錢實際怎麼流動</td><td style="text-align: left;">營業、投資、籌資現金流</td></tr>
</tbody>
</table>

<div class="section-title">📊 關鍵指標一眼理解</div>
<table class="pv-table">
<thead>
<tr><th width="20%">指標</th><th width="40%">一眼理解</th><th width="40%">初步觀察</th></tr>
</thead>
<tbody>
<tr><td><b>💵 營收</b></td><td style="text-align: left;">生意做多大</td><td style="text-align: left;">是否持續成長</td></tr>
<tr><td><b>📈 EPS</b></td><td style="text-align: left;">每股賺多少錢</td><td style="text-align: left;">是否穩定成長</td></tr>
<tr><td><b>💎 毛利率</b></td><td style="text-align: left;">產品本身好不好賺</td><td style="text-align: left;">是否維持或提升</td></tr>
<tr><td><b>🏦 負債比</b></td><td style="text-align: left;">借了多少錢</td><td style="text-align: left;">是否過度依賴負債</td></tr>
<tr><td><b>💰 營業現金流</b></td><td style="text-align: left;">本業有沒有產生現金</td><td style="text-align: left;">是否長期穩定</td></tr>
</tbody>
</table>

<div class="section-title">🔍 基本面狀態一眼判讀</div>
<table class="pv-table">
<thead>
<tr><th width="25%">狀態</th><th width="40%">一眼判讀</th><th width="35%">初步解讀</th></tr>
</thead>
<tbody>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 穩定成長</td><td>營收↑ / EPS↑ / 現金流↑</td><td style="text-align: left;">公司營運與獲利同步改善</td></tr>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 獲利改善</td><td>營收→ / 毛利↑ / EPS↑</td><td style="text-align: left;">公司效率或產品組合改善</td></tr>
<tr><td style="color:#FACC15; font-weight:bold;">🟡 成長放緩</td><td>營收↑但增速↓ / EPS→</td><td style="text-align: left;">公司仍成長，但速度減慢</td></tr>
<tr><td style="color:#FB923C; font-weight:bold;">🟠 虛胖成長</td><td>營收↑ / EPS↓ / 現金流↓</td><td style="text-align: left;">生意變大，但獲利品質可能下降</td></tr>
<tr><td style="color:#F87171; font-weight:bold;">🔴 財務壓力</td><td>負債↑↑ / 現金流↓ / EPS↓</td><td style="text-align: left;">公司財務體質可能惡化</td></tr>
<tr><td style="color:#EF4444; font-weight:bold;">🚨 基本面惡化</td><td>營收↓ / EPS↓ / 現金流↓</td><td style="text-align: left;">核心營運同步轉弱</td></tr>
</tbody>
</table>

<div class="section-title">⚠️ 財報陷阱：不能只看表面</div>
<table class="pv-table">
<thead>
<tr><th width="25%">現象</th><th width="35%">不能只看什麼</th><th width="40%">還要看什麼</th></tr>
</thead>
<tbody>
<tr><td style="color:#FFD700; font-weight:bold;">營收大增</td><td style="text-align: left;">只看營收</td><td style="text-align: left;">EPS、毛利率</td></tr>
<tr><td style="color:#FFD700; font-weight:bold;">EPS 大增</td><td style="text-align: left;">單季獲利</td><td style="text-align: left;">是否為一次性收益</td></tr>
<tr><td style="color:#FFD700; font-weight:bold;">公司帳上很多錢</td><td style="text-align: left;">現金餘額</td><td style="text-align: left;">現金流來源與負債</td></tr>
</tbody>
</table>

</div>
</div>"""

        elif current_view == 'detail_4':
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
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 羅德</div>
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

        elif current_view == 'detail_5':
            # =========================
            # 📖 第5課詳情 (技術分析與指標應用)
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 20px 0 10px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
.info-box { background: rgba(0, 210, 255, 0.05); border: 1px solid rgba(0, 210, 255, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 15px; font-size: 14px; color: #CBD5E1; line-height: 1.6; }
.info-box span { color: #FFD700; font-weight: bold; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 羅德</div>
<div class="npc-text">「冒險者！技術指標可不是單純告訴你『買』或『賣』的魔法棒！它就像裝備上的屬性雷達，幫你從不同角度觀察市場的『方向、動能、熱度、節奏與波動』。來看看這張儀表板吧！」</div>
</div>
</div>
<div class="table-container">

<div class="info-box">
    <b>🧭 指標核心雷達：</b><br>
    📈 MA 看方向 ｜ ⚡ MACD 看動能 ｜ 🌡️ RSI 看熱度 ｜ 🎢 KDJ 看短線節奏 ｜ 📏 BBW 看波動
</div>

<div class="section-title">📊 綜合總表 ①：五大指標數值判讀</div>
<table class="pv-table">
<thead>
<tr><th width="15%">指標</th><th width="28%">🟢 偏多／轉強</th><th width="28%">🟡 中性／觀察</th><th width="29%">🔴 偏空／轉弱</th></tr>
</thead>
<tbody>
<tr><td><b>📈 MA</b></td><td style="text-align: left;">股價 > MA<br>均線向上、多頭排列</td><td style="text-align: left;">股價接近 MA<br>均線糾結</td><td style="text-align: left;">股價 < MA<br>均線向下、空頭排列</td></tr>
<tr><td><b>⚡ MACD</b></td><td style="text-align: left;">DIF > DEA<br>柱體增加、0軸上方較強</td><td style="text-align: left;">DIF 接近 DEA<br>柱體縮小</td><td style="text-align: left;">DIF < DEA<br>柱體減少、0軸下方較弱</td></tr>
<tr><td><b>🌡️ RSI</b></td><td style="text-align: left;">50～70 偏多<br>70↑ 偏熱</td><td style="text-align: left;">40～50 多空拉鋸</td><td style="text-align: left;">30～40 偏弱<br>30↓ 偏冷</td></tr>
<tr><td><b>🎢 KDJ</b></td><td style="text-align: left;">K、D > 50<br>低檔黃金交叉可觀察</td><td style="text-align: left;">20～80 一般震盪區</td><td style="text-align: left;">K、D < 50<br>高檔死亡交叉偏弱</td></tr>
<tr><td><b>📏 BBW</b></td><td style="text-align: left;">帶寬由低檔開始擴張<br>搭配向上突破</td><td style="text-align: left;">歷史 25～75% 百分位</td><td style="text-align: left;">單純收縮不代表偏空<br>0～10% 為極度收縮，需等待方向</td></tr>
</tbody>
</table>

<div class="info-box" style="border-color: rgba(255, 215, 0, 0.4); background: rgba(255, 215, 0, 0.05);">
    <b style="color: #FFD700;">📌 蘿西特別提醒：BBW (布林通道寬度)</b><br>
    BBW 最適合用「歷史百分位」判斷：<br>
    🔹 0～10%：極度收縮 ｜ 🔹 10～25%：收縮整理 ｜ 🔹 25～75%：正常波動 ｜ 🔹 75～90%：波動擴張 ｜ 🔹 90～100%：極度擴張<br>
    <br>
    它不像 RSI 單純分成多空，而是用來回答你：<b>「市場正在蓄力，還是行情正在爆發？」</b>
</div>

<div class="section-title">🎯 綜合總表 ②：多指標狀態判讀</div>
<table class="pv-table">
<thead>
<tr>
    <th width="14%">市場狀態</th>
    <th width="16%">MA 趨勢</th>
    <th width="20%">MACD 動能</th>
    <th width="20%">RSI／KDJ</th>
    <th width="15%">BBW 波動</th>
    <th width="15%">綜合解讀</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:#60A5FA; font-weight:bold;">🔵 蓄力整理</td>
    <td>均線糾結</td>
    <td>接近 0 軸</td>
    <td>RSI 40～60<br>KDJ 震盪</td>
    <td>↓↓ 極度收縮</td>
    <td>市場等待突破</td>
</tr>
<tr>
    <td style="color:#4ADE80; font-weight:bold;">🚀 向上突破</td>
    <td>股價突破均線或壓力</td>
    <td>DIF > DEA<br>動能↑</td>
    <td>RSI > 50<br>KDJ 偏多</td>
    <td>↑ 開始擴張</td>
    <td>多方可能轉強</td>
</tr>
<tr>
    <td style="color:#4ADE80; font-weight:bold;">🟢 多頭趨勢</td>
    <td>股價 > MA<br>均線向上</td>
    <td>0軸上 / 偏多</td>
    <td>RSI 50～70</td>
    <td>正常或持續擴張</td>
    <td>趨勢偏多</td>
</tr>
<tr>
    <td style="color:#FF7676; font-weight:bold;">🔥 強勢加速</td>
    <td>多頭排列</td>
    <td>柱體↑↑</td>
    <td>RSI 70↑<br>KDJ高檔</td>
    <td>↑↑ 快速擴張</td>
    <td>強勢但波動風險提高</td>
</tr>
<tr>
    <td style="color:#FACC15; font-weight:bold;">🟡 高檔過熱</td>
    <td>仍維持多頭</td>
    <td>動能開始縮小</td>
    <td>RSI > 70<br>KDJ > 80</td>
    <td>高檔擴張或開始收斂</td>
    <td>注意追高與轉弱</td>
</tr>
<tr>
    <td style="color:#FB923C; font-weight:bold;">🟠 趨勢轉弱</td>
    <td>跌破短均線</td>
    <td>柱體縮小<br>死亡交叉</td>
    <td>RSI 跌破 50</td>
    <td>波動可能收縮或轉向</td>
    <td>多方力道減弱</td>
</tr>
<tr>
    <td style="color:#F87171; font-weight:bold;">🔴 空頭趨勢</td>
    <td>股價 < MA<br>均線向下</td>
    <td>DIF < DEA<br>0軸下</td>
    <td>RSI < 40<br>KDJ 偏弱</td>
    <td>向下時可能擴張</td>
    <td>空方占優</td>
</tr>
<tr>
    <td style="color:#CBD5E1; font-weight:bold;">⚪ 盤整觀望</td>
    <td>均線糾結</td>
    <td>接近 0 軸</td>
    <td>RSI 40～60</td>
    <td>正常或收縮</td>
    <td>尚未形成明確方向</td>
</tr>
</tbody>
</table>

</div>
</div>"""

        elif current_view == 'detail_6':
            # =========================
            # 📖 第6課詳情 (籌碼面追蹤：法人與大戶結構)
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
background-image: url('app/static/npcroad.png'); 
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 15px 0 8px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 羅德</div>
<div class="npc-text">「冒險者！市場上真正能呼風喚雨的，往往是那些掌握龐大資金的『法人』與『大戶』。透過這張籌碼結構表，我們可以看穿『誰在買』、『籌碼是集中還是分散』，進而判斷買盤的延續性喔！」</div>
</div>
</div>
<div class="table-container">

<div class="section-title">📊 綜合總表 ①：法人、大戶與分點怎麼看？</div>
<table class="pv-table">
<thead>
<tr>
    <th width="18%">觀察對象</th>
    <th width="28%">主要看什麼</th>
    <th width="18%">🟢 偏多／集中</th>
    <th width="18%">🟡 觀察</th>
    <th width="18%">🔴 偏空／分散</th>
</tr>
</thead>
<tbody>
<tr>
    <td><b>🌍 外資</b></td>
    <td style="text-align: left;">連續買賣超、持股變化</td>
    <td style="color:#4ADE80; font-weight:bold;">連續買超／持股↑</td>
    <td style="color:#FACC15;">買賣互有</td>
    <td style="color:#F87171; font-weight:bold;">連續賣超／持股↓</td>
</tr>
<tr>
    <td><b>🏦 投信</b></td>
    <td style="text-align: left;">連續買賣超</td>
    <td style="color:#4ADE80; font-weight:bold;">連續買超</td>
    <td style="color:#FACC15;">間歇性買超</td>
    <td style="color:#F87171; font-weight:bold;">連續賣超</td>
</tr>
<tr>
    <td><b>⚙️ 自營商</b></td>
    <td style="text-align: left;">買賣超方向</td>
    <td style="color:#4ADE80; font-weight:bold;">持續買超</td>
    <td style="color:#FACC15;">方向反覆</td>
    <td style="color:#F87171; font-weight:bold;">持續賣超</td>
</tr>
<tr>
    <td><b>🦈 400 張以上</b></td>
    <td style="text-align: left;">中大型持有人變化</td>
    <td style="color:#4ADE80; font-weight:bold;">人數↓／持股↑</td>
    <td style="color:#FACC15;">變化不明顯</td>
    <td style="color:#F87171; font-weight:bold;">人數↑／持股↓</td>
</tr>
<tr>
    <td><b>🐋 1,000 張以上</b></td>
    <td style="text-align: left;">大型持有人集中度</td>
    <td style="color:#4ADE80; font-weight:bold;">持股↑／集中↑</td>
    <td style="color:#FACC15;">持平</td>
    <td style="color:#F87171; font-weight:bold;">持股↓／集中↓</td>
</tr>
<tr>
    <td><b>🔍 單一分點</b></td>
    <td style="text-align: left;">連續買超與成交占比</td>
    <td style="color:#4ADE80; font-weight:bold;">連續買超／集中度↑</td>
    <td style="color:#FACC15;">單日異常</td>
    <td style="color:#F87171; font-weight:bold;">連續賣超</td>
</tr>
<tr>
    <td><b>🏢 券商群聚</b></td>
    <td style="text-align: left;">同券商多分點方向</td>
    <td style="color:#4ADE80; font-weight:bold;">多分點同步買超</td>
    <td style="color:#FACC15;">分點分歧</td>
    <td style="color:#F87171; font-weight:bold;">多分點同步賣超</td>
</tr>
</tbody>
</table>

<div class="section-title">🏛️ 延伸觀察：內部人與董監持股</div>
<table class="pv-table">
<thead>
<tr>
    <th width="35%">項目</th>
    <th width="65%">觀察重點</th>
</tr>
</thead>
<tbody>
<tr>
    <td><b>🏛️ 董監持股比例</b></td>
    <td style="text-align: left;">公司內部人持股結構</td>
</tr>
<tr>
    <td><b>📈 董監持股變化</b></td>
    <td style="text-align: left;">是否增加或減少</td>
</tr>
<tr>
    <td><b>🔒 質押比例</b></td>
    <td style="text-align: left;">持股是否存在較高財務壓力</td>
</tr>
<tr>
    <td><b>👥 主要股東</b></td>
    <td style="text-align: left;">股權是否過度集中或出現重大變化</td>
</tr>
</tbody>
</table>

</div>
</div>"""

        elif current_view == 'detail_7':
            # =========================
            # 📖 第7課詳情 (券資關係與融資融券)
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
background-image: url('app/static/npcroad.png'); 
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
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「融資與融券的變化，往往暗示著主力與散戶的籌碼流動！觀察下方這張『券資關係與軋空狀態表』，小心別被『軋空』或『多殺多』掃出市場喔！」</div>
</div>
</div>
<div class="table-container">
<table class="pv-table">
<thead>
<tr><th width="20%">趨勢</th><th width="35%">狀態</th><th width="45%">市場含義</th></tr>
</thead>
<tbody>
<tr><td style="color:#60A5FA; font-weight:bold;">🔵 可能軋空</td><td>股價↑ / 融券↑ / 借券↑ / 融資→↓</td><td style="text-align: left;">空方部位仍高或持續增加，但股價開始走強，後續可能形成回補壓力</td></tr>
<tr><td style="color:#4ADE80; font-weight:bold;">🟢 正在軋空</td><td>股價↑↑ / 融券↓ / 借券↓ / 融資→↓</td><td style="text-align: left;">股價上漲同時空方部位下降，可能出現空方回補推升</td></tr>
<tr><td style="color:#FACC15; font-weight:bold;">🟡 軋空力道下降</td><td>股價↑→ / 融券↓幅縮小 / 借券↓幅縮小 / 融資↑</td><td style="text-align: left;">空方回補動能減弱，多方接棒力道需要觀察</td></tr>
<tr><td style="color:#FB923C; font-weight:bold;">🟠 融資追價</td><td>股價↑ / 融資↑↑ / 融券→↓ / 借券→↓</td><td style="text-align: left;">上漲主要伴隨融資增加，槓桿追價升溫</td></tr>
<tr><td style="color:#FACC15; font-weight:bold;">🟡 多空混戰</td><td>股價→ / 融資↑ / 融券↑ / 借券↑</td><td style="text-align: left;">多空雙方同步加碼，方向尚未明確</td></tr>
<tr><td style="color:#F87171; font-weight:bold;">🔴 空方壓力增加</td><td>股價↓ / 融券↑ / 借券↑↑ / 融資→↓</td><td style="text-align: left;">股價走弱且空方部位增加，空方壓力升高</td></tr>
<tr><td style="color:#EF4444; font-weight:bold;">🚨 多殺多風險</td><td>股價↓↓ / 融資↓↓ / 融券→↓ / 借券→↓</td><td style="text-align: left;">股價下跌導致融資退場，可能出現槓桿賣壓</td></tr>
</tbody>
</table>
</div>
</div>"""

        elif current_view == 'detail_8':
            # =========================
            # 📖 第8課詳情 (產業趨勢與題材)
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
background-image: url('app/static/npcroad.png'); 
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 20px 0 10px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
.info-box { background: rgba(0, 210, 255, 0.05); border: 1px solid rgba(0, 210, 255, 0.2); border-radius: 8px; padding: 15px; margin-bottom: 15px; font-size: 14px; color: #CBD5E1; line-height: 1.6; }
.info-box ul { margin: 8px 0 0 20px; padding: 0; }
.tree-container { background: rgba(0,0,0,0.3); border: 1px dashed rgba(0,210,255,0.4); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
.tree-row { display: flex; justify-content: center; gap: 30px; margin: 10px 0; }
.tree-node { background: rgba(0, 210, 255, 0.15); border: 1px solid #00D2FF; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; box-shadow: 0 0 10px rgba(0,210,255,0.2); }
.tree-arrow { color: #94A3B8; font-size: 18px; margin: 5px 0; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「冒險者，市場資金就像流水，哪裡有『題材』就往哪裡去！但別只盯著一檔股票，真正的強勢產業會引發『族群共振』。當上下游供應鏈同步轉強，才代表大部隊資金真的進場囉！」</div>
</div>
</div>
<div class="table-container">

<div class="info-box">
    <b style="color: #FFD700;">🎯 重點不是追逐熱門，而是問自己這四個問題：</b>
    <ul>
        <li>「市場現在在炒什麼？」</li>
        <li>「是單一股票上漲，還是整個族群開始 <b>共振</b>？」</li>
        <li>「這個題材有沒有實際產業基本面支撐？」</li>
        <li>「目前是剛起漲、持續發展，還是已經過熱？」</li>
    </ul>
</div>

<div class="section-title">🌊 資金輪動與題材階段解讀</div>
<table class="pv-table">
<thead>
<tr>
    <th width="20%">題材階段</th>
    <th width="25%">族群共振</th>
    <th width="55%">初步解讀</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:#60A5FA; font-weight:bold;">🌱 題材萌芽</td>
    <td>單點啟動</td>
    <td style="text-align: left;">少數公司開始受到關注，可能是早期題材，尚未擴散。</td>
</tr>
<tr>
    <td style="color:#4ADE80; font-weight:bold;">🚀 趨勢成長</td>
    <td>局部共振</td>
    <td style="text-align: left;">上下游開始陸續轉強，產業趨勢逐漸形成，資金慢慢流入。</td>
</tr>
<tr>
    <td style="color:#FACC15; font-weight:bold;">🧩 族群共振</td>
    <td>全產業擴散</td>
    <td style="text-align: left;">多家公司、不同環節同步走強，資金高度集中於該產業。</td>
</tr>
<tr>
    <td style="color:#FF7676; font-weight:bold;">🔥 市場主流</td>
    <td>強烈共振</td>
    <td style="text-align: left;">產業討論度極高、族群全面活躍，主流題材確立，但須注意追高風險。</td>
</tr>
<tr>
    <td style="color:#FB923C; font-weight:bold;">⚠️ 高檔過熱</td>
    <td>共振開始分歧</td>
    <td style="text-align: left;">多數股票已大幅上漲，強弱開始分明，注意資金輪動與獲利了結賣壓。</td>
</tr>
<tr>
    <td style="color:#94A3B8; font-weight:bold;">🌙 題材退燒</td>
    <td>共振消失</td>
    <td style="text-align: left;">強勢股減少、資金明顯撤離，產業可能進入中長期整理或退潮。</td>
</tr>
</tbody>
</table>

<div class="section-title">🧩 供應鏈結構範例 (以 AI 產業為例)</div>
<div class="tree-container">
    <div class="tree-row">
        <div class="tree-node" style="border-color: #FFD700; color: #FFD700;">🧠 AI 晶片</div>
    </div>
    <div class="tree-arrow">⬇️</div>
    <div class="tree-row">
        <div class="tree-node">🖥️ 伺服器組裝</div>
        <div class="tree-node">🔌 電源供應器</div>
    </div>
    <div class="tree-arrow">⬇️</div>
    <div class="tree-row">
        <div class="tree-node">❄️ 散熱模組</div>
        <div class="tree-node">🟩 伺服器 PCB</div>
        <div class="tree-node">🌐 網通設備</div>
    </div>
    <div style="margin-top: 15px; font-size: 13px; color: #94A3B8;">
        💡 觀察重點：如果只有晶片廠漲，是「單點啟動」；<br>如果連散熱、PCB、網通都一起大漲，就是強烈的「族群共振」！
    </div>
</div>

</div>
</div>"""

        elif current_view == 'detail_9':
            # =========================
            # 📖 第9課詳情 (資金控管與風險管理)
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
background-image: url('app/static/npcroad.png'); 
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 20px 0 10px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
.info-box { background: rgba(0, 210, 255, 0.05); border: 1px solid rgba(0, 210, 255, 0.2); border-radius: 8px; padding: 15px; margin-bottom: 15px; font-size: 14px; color: #CBD5E1; line-height: 1.6; }
.info-box ul { margin: 8px 0 8px 20px; padding: 0; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「冒險者！在市場裡活下來，比賺多少錢更重要！資金控管就是你的護城河與保命裝備。別總想著『重壓一把』，學會根據大盤環境調整資金比例，才能在股海裡安穩航行喔！」</div>
</div>
</div>
<div class="table-container">

<div class="info-box">
    <b style="color: #FFD700;">🛡️ 進場前，先問自己這三個靈魂拷問：</b>
    <ul>
        <li>「現在的大盤環境適合投入多少？」</li>
        <li>「我的資金應該保留多少？」</li>
        <li>「單一股票最多可以承擔多少風險？」</li>
    </ul>
    💡 <b>大原則：</b><br>
    🟢 大盤越明確 → 可以考慮提高配置<br>
    🟡 大盤越震盪 → 降低單筆部位、增加分批操作<br>
    🔴 大盤越弱 → 優先提高現金與風險控制
</div>

<div class="section-title">📉 大盤環境與資金配置思維</div>
<table class="pv-table">
<thead>
<tr>
    <th width="18%">大盤狀態</th>
    <th width="35%">市場特徵</th>
    <th width="32%">資金配置思維</th>
    <th width="15%">投入部位</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:#4ADE80; font-weight:bold;">🚀 多頭趨勢</td>
    <td style="text-align: left;">高低點持續墊高、趨勢明確</td>
    <td style="text-align: left;">可逐步提高市場參與度</td>
    <td style="color:#4ADE80; font-weight:bold;">🟢 較高</td>
</tr>
<tr>
    <td style="color:#60A5FA; font-weight:bold;">🟢 偏多震盪</td>
    <td style="text-align: left;">大方向偏多，但短線來回震盪</td>
    <td style="text-align: left;">保留部分現金、分批配置</td>
    <td style="color:#FACC15; font-weight:bold;">🟡 中高</td>
</tr>
<tr>
    <td style="color:#FACC15; font-weight:bold;">🟡 區間震盪</td>
    <td style="text-align: left;">上下來回、方向不明</td>
    <td style="text-align: left;">控制總曝險，避免重壓</td>
    <td style="color:#FACC15; font-weight:bold;">🟡 中低</td>
</tr>
<tr>
    <td style="color:#FB923C; font-weight:bold;">🟠 偏空震盪</td>
    <td style="text-align: left;">反彈後仍容易出現賣壓</td>
    <td style="text-align: left;">降低部位、提高現金比例</td>
    <td style="color:#FB923C; font-weight:bold;">🟠 低</td>
</tr>
<tr>
    <td style="color:#F87171; font-weight:bold;">🔴 空頭趨勢</td>
    <td style="text-align: left;">高低點持續下降</td>
    <td style="text-align: left;">優先控制風險</td>
    <td style="color:#F87171; font-weight:bold;">🔴 很低/觀望</td>
</tr>
</tbody>
</table>

<div class="section-title">⚔️ 實戰策略：投資狀態與風險重點</div>
<table class="pv-table">
<thead>
<tr>
    <th width="24%">投資狀態</th>
    <th width="14%">總資金配置</th>
    <th width="14%">單筆投入</th>
    <th width="20%">操作方式</th>
    <th width="28%">風險重點</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:#4ADE80; font-weight:bold; text-align:left;">🚀 大盤強＋個股強</td>
    <td>較高</td>
    <td>中～較高</td>
    <td>分批進場</td>
    <td style="text-align:left;">不因看好而一次滿倉</td>
</tr>
<tr>
    <td style="color:#60A5FA; font-weight:bold; text-align:left;">🟢 大盤偏多＋個股強</td>
    <td>中高</td>
    <td>中等</td>
    <td>分批建立部位</td>
    <td style="text-align:left;">注意市場突然轉弱</td>
</tr>
<tr>
    <td style="color:#FACC15; font-weight:bold; text-align:left;">🟡 大盤震盪＋個股強</td>
    <td>中低</td>
    <td>小～中</td>
    <td>分批或試單</td>
    <td style="text-align:left;">避免追高與重壓</td>
</tr>
<tr>
    <td style="color:#FB923C; font-weight:bold; text-align:left;">🟠 大盤弱＋個股逆勢強</td>
    <td>低</td>
    <td>小</td>
    <td>嚴格控制風險</td>
    <td style="text-align:left;">個股可能受大盤拖累</td>
</tr>
<tr>
    <td style="color:#F87171; font-weight:bold; text-align:left;">🔴 大盤弱＋個股弱</td>
    <td>很低</td>
    <td>極低或不投入</td>
    <td>觀望</td>
    <td style="text-align:left;">避免逆勢攤平</td>
</tr>
<tr>
    <td style="color:#bc13fe; font-weight:bold; text-align:left;">🚨 連續判斷錯誤</td>
    <td>降低</td>
    <td>明顯降低</td>
    <td>暫停或重新檢討</td>
    <td style="text-align:left;">防止情緒化交易</td>
</tr>
</tbody>
</table>

</div>
</div>"""

        elif current_view == 'detail_10':
            # =========================
            # 📖 第10課詳情 (交易心理學與個人策略)
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
background-image: url('app/static/npcroad.png'); 
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
.pv-table { width: 100%; border-collapse: collapse; font-size: 13.5px; text-align: center; margin-bottom: 15px; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 10px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.section-title { color: #00D2FF; font-size: 16px; font-weight: bold; margin: 20px 0 10px 0; border-left: 4px solid #00D2FF; padding-left: 8px; }
.info-box { background: rgba(255, 76, 76, 0.05); border: 1px solid rgba(255, 76, 76, 0.3); border-radius: 8px; padding: 15px; margin-bottom: 15px; font-size: 14px; color: #CBD5E1; line-height: 1.6; }
.path-container { background: rgba(0,0,0,0.3); border: 1px dashed rgba(0,210,255,0.4); border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 15px; line-height: 2.2; }
.path-step { background: rgba(0, 210, 255, 0.1); padding: 5px 10px; border-radius: 5px; font-weight: bold; color: #FFF; margin: 0 5px; display: inline-block; }
.tree-node { background: rgba(0, 210, 255, 0.15); border: 1px solid #00D2FF; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; box-shadow: 0 0 10px rgba(0,210,255,0.2); }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style>
<div class="npc-overlay">
<div class="top-actions">
<label class="action-btn back" id="btn-back-detail" title="回到籌碼導師選單">←</label>
<label class="action-btn close" id="btn-close-detail" title="關閉">✕</label>
</div>
<div class="detail-header">
<div class="npc-big-image"></div>
<div class="dialogue-box">
<div class="npc-name">籌碼導師 蘿西</div>
<div class="npc-text">「冒險者，恭喜你來到最後一關！技術再好，如果心態崩了也是白搭。真正成熟的投資者，不代表每天都要交易，而是知道『什麼時候值得出手』、『什麼時候該收手』。讓我們建立屬於你的交易系統吧！」</div>
</div>
</div>
<div class="table-container">

<div class="info-box">
    <b style="color: #FF4C4C;">⚠️ 致命陷阱：有時候我們不是輸給市場，而是「輸在太想賺」！</b><br>
    當市場出現 <b>📈趨勢不明 ＋ 📊籌碼混亂 ＋ 📉技術面震盪 ＋ 🌍大盤方向不明</b> 時，一直交易不代表你積極，而是你不願意等待。<br>
    過度追求高報酬容易導致：頻繁追逐熱門股 ➔ 提高槓桿 ➔ 放大單筆部位 ➔ 不願意承認錯誤 ➔ <b>最終導致大虧損！</b>
</div>

<div class="section-title">🧭 下單前的靈魂拷問</div>
<div class="path-container">
    <span class="path-step">😨 自己恐懼了嗎？</span> ➔ 
    <span class="path-step">🤑 自己太貪婪了？</span> ➔ 
    <span class="path-step">🌡️ 市場情緒如何？</span> ➔ 
    <span class="path-step">🇺🇸 VIX 升高？</span> ➔ 
    <span class="path-step">🇹🇼 TW VIX 異常？</span> ➔ 
    <span class="path-step">💰 需調整配置？</span> ➔ 
    <span class="path-step">🎯 符合交易規則？</span><br><br>
    <div class="tree-node" style="border-color: #FFD700; color: #FFD700; display: inline-block;">🐢 如果沒有，最好的策略就是「什麼都不做」，耐心等待。</div>
</div>

<div class="section-title">🌡️ 認識市場情緒指標</div>
<table class="pv-table">
<thead>
<tr>
    <th width="20%">指標名稱</th>
    <th width="35%">這是什麼？</th>
    <th width="45%">如何解讀？</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:#FFD700; font-weight:bold;">恐懼貪婪指數<br>(Fear & Greed)</td>
    <td style="text-align: left;">CNN編製的綜合情緒指標，滿分100。</td>
    <td style="text-align: left;">接近 0 (極度恐懼) 可能是相對低點；<br>接近 100 (極度貪婪) 代表市場過熱，隨時可能反轉。</td>
</tr>
<tr>
    <td style="color:#FF4C4C; font-weight:bold;">VIX 指數<br>(美股恐慌指數)</td>
    <td style="text-align: left;">標普500選擇權隱含波動率。</td>
    <td style="text-align: left;">常態在 15 左右。若突然狂飆 (如 >30)，代表市場預期未來將有劇烈波動，美股易見大跌。</td>
</tr>
<tr>
    <td style="color:#60A5FA; font-weight:bold;">TW VIX<br>(台指恐慌指數)</td>
    <td style="text-align: left;">台指選擇權隱含波動率。</td>
    <td style="text-align: left;">反映台灣散戶與法人的避險情緒，大盤急殺時會飆高，適合用來判斷短線是否過度恐慌。</td>
</tr>
</tbody>
</table>

<div class="section-title">🧠 常見心理陷阱與對策</div>
<table class="pv-table">
<thead>
<tr>
    <th width="20%">心理／行為</th>
    <th width="35%">常見想法</th>
    <th width="45%">更好的做法</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:#F87171; font-weight:bold;">😨 恐懼</td>
    <td>「再跌一點就完了...」</td>
    <td style="text-align: left;">回到進場前設定的停損規則，該砍就砍。</td>
</tr>
<tr>
    <td style="color:#4ADE80; font-weight:bold;">🤑 貪婪</td>
    <td>「應該還會再漲，繼續凹！」</td>
    <td style="text-align: left;">客觀評估趨勢與風險，不憑感覺，嚴守停利。</td>
</tr>
<tr>
    <td style="color:#FACC15; font-weight:bold;">🏃 FOMO</td>
    <td>「現在不買就錯過了！」</td>
    <td style="text-align: left;">寧可錯過，也不要做錯。等待符合進場條件。</td>
</tr>
<tr>
    <td style="color:#FB923C; font-weight:bold;">🎲 過度交易</td>
    <td>「今天一定要做點什麼才行...」</td>
    <td style="text-align: left;">沒有高勝率機會就不交易，休息也是策略。</td>
</tr>
<tr>
    <td style="color:#bc13fe; font-weight:bold;">🔥 報復性交易</td>
    <td>「可惡，我要趕快把虧的賺回來！」</td>
    <td style="text-align: left;">立刻離開螢幕，降低部位、暫停交易並檢討。</td>
</tr>
<tr>
    <td style="color:#94A3B8; font-weight:bold;">🐢 耐心等待</td>
    <td>「機會還沒出現...」</td>
    <td style="text-align: left;">保留滿手現金，心如止水，等待高品質的獵物。</td>
</tr>
</tbody>
</table>

<div class="section-title">🏰 建立你的專屬交易系統</div>
<table class="pv-table">
<thead>
<tr>
    <th width="20%">系統環節</th>
    <th width="35%">要回答的問題</th>
    <th width="45%">核心觀念</th>
</tr>
</thead>
<tbody>
<tr>
    <td><b>🌍 市場環境</b></td>
    <td>大盤是多頭、空頭還是震盪？</td>
    <td style="text-align: left;">不同市場使用不同策略。</td>
</tr>
<tr>
    <td><b>🔎 選股條件</b></td>
    <td>什麼樣的股票值得觀察？</td>
    <td style="text-align: left;">專注熟悉的領域，不必什麼股票都做。</td>
</tr>
<tr>
    <td><b>🎯 進場條件</b></td>
    <td>什麼情況才允許買進？</td>
    <td style="text-align: left;">耐心等待價格走入你的「打擊區」。</td>
</tr>
<tr>
    <td><b>💰 部位管理</b></td>
    <td>一次投入多少？</td>
    <td style="text-align: left;">嚴格控制總曝險與單筆承受風險。</td>
</tr>
<tr>
    <td><b>🛑 停損規則</b></td>
    <td>判斷錯了怎麼辦？</td>
    <td style="text-align: left;">小錯可以接受，大錯絕對要避免。</td>
</tr>
<tr>
    <td><b>📈 停利規則</b></td>
    <td>看對後如何處理？</td>
    <td style="text-align: left;">讓獲利有機會延續，不輕易被洗掉。</td>
</tr>
<tr>
    <td><b>🧘 等待機制</b></td>
    <td>沒有機會時怎麼辦？</td>
    <td style="text-align: left;">不動作本身就是一種最強的防守策略。</td>
</tr>
<tr>
    <td><b>📝 交易紀錄</b></td>
    <td>為什麼買、為什麼賣？</td>
    <td style="text-align: left;">讓經驗可以被量化與檢討。</td>
</tr>
<tr>
    <td><b>🔄 回測與修正</b></td>
    <td>長期結果是否符合預期？</td>
    <td style="text-align: left;">持續改善，尋找正期望值，而非追求完美。</td>
</tr>
</tbody>
</table>

</div>
</div>"""

        # 渲染畫面 (這行保留原本的)
        st.markdown(html_code, unsafe_allow_html=True)     
        
        # ==========================================
        # 🚀 終極效能升級版：使用 Callback (回呼) 完全移除 st.rerun()
        # ==========================================
        
        # 1. 定義狀態切換動作 (這會在按鈕被點擊的瞬間優先執行，不會產生閃爍)
        def close_npc_action():
            st.session_state['show_course_npc'] = False
            st.session_state['course_view'] = 'list'
            
        def switch_view_action(view_name):
            st.session_state['course_view'] = view_name

        # 2. 建立實體按鈕，並綁定對應的 Callback 動作
        cols = st.columns(12)
        with cols[0]:
            st.button("CloseNPC", key="npc_btn_close", on_click=close_npc_action)
        with cols[1]:
            st.button("OpenCourse1", key="npc_btn_c1", on_click=switch_view_action, args=('detail_1',))
        with cols[2]:
            st.button("OpenCourse2", key="npc_btn_c2", on_click=switch_view_action, args=('detail_2',))
        with cols[3]:
            st.button("OpenCourse3", key="npc_btn_c3", on_click=switch_view_action, args=('detail_3',))
        with cols[4]:
            st.button("OpenCourse4", key="npc_btn_c4", on_click=switch_view_action, args=('detail_4',))
        with cols[5]:
            st.button("OpenCourse5", key="npc_btn_c5", on_click=switch_view_action, args=('detail_5',))
        with cols[6]:
            st.button("OpenCourse6", key="npc_btn_c6", on_click=switch_view_action, args=('detail_6',))
        with cols[7]:
            st.button("OpenCourse7", key="npc_btn_c7", on_click=switch_view_action, args=('detail_7',))
        with cols[8]:
            st.button("OpenCourse8", key="npc_btn_c8", on_click=switch_view_action, args=('detail_8',))
        with cols[9]:
            st.button("OpenCourse9", key="npc_btn_c9", on_click=switch_view_action, args=('detail_9',))
        with cols[10]:
            st.button("OpenCourse10", key="npc_btn_c10", on_click=switch_view_action, args=('detail_10',))
        with cols[11]:
            st.button("BackToList", key="npc_btn_back", on_click=switch_view_action, args=('list',))
            
        # 3. 🎯 修正版的 JavaScript：精準對應英文名稱，確保完美隱藏與觸發
        bind_js = """<script>
        setInterval(() => {
            const doc = window.parent.document;
            if (!doc) return;

            // 尋找 Streamlit 生成的實體按鈕 (這裡已修正為對應你截圖中的英文名稱)
            const stBtns = Array.from(doc.querySelectorAll('button'));
            const btnClose = stBtns.find(b => b.textContent.includes('CloseNPC'));
            const btnOpen1 = stBtns.find(b => b.textContent.includes('OpenCourse1'));
            const btnOpen2 = stBtns.find(b => b.textContent.includes('OpenCourse2'));
            const btnOpen3 = stBtns.find(b => b.textContent.includes('OpenCourse3'));
            const btnOpen4 = stBtns.find(b => b.textContent.includes('OpenCourse4'));
            const btnOpen5 = stBtns.find(b => b.textContent.includes('OpenCourse5'));
            const btnOpen6 = stBtns.find(b => b.textContent.includes('OpenCourse6'));
            const btnOpen7 = stBtns.find(b => b.textContent.includes('OpenCourse7'));
            const btnOpen8 = stBtns.find(b => b.textContent.includes('OpenCourse8'));
            const btnOpen9 = stBtns.find(b => b.textContent.includes('OpenCourse9'));
            const btnOpen10 = stBtns.find(b => b.textContent.includes('OpenCourse10'));
            const btnBack = stBtns.find(b => b.textContent.includes('BackToList'));

            // 安全隱藏實體按鈕容器 (讓畫面上不再出現那一排醜醜的按鈕)
            [btnClose, btnOpen1, btnOpen2, btnOpen3, btnOpen4, btnOpen5, btnOpen6, btnOpen7, btnOpen8, btnOpen9, btnOpen10, btnBack].forEach(b => {
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
                if(uiEl && stBtn && !uiEl.dataset.hooked) {
                    uiEl.dataset.hooked = 'true'; 
                    uiEl.style.cursor = 'pointer'; 
                    uiEl.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        stBtn.click(); 
                    });
                }
            };

            // 進行所有按鈕的綁定 (對應 HTML 中的 id)
            bindEvent('btn-close-list', btnClose);
            bindEvent('btn-close-detail', btnClose);
            bindEvent('btn-back-detail', btnBack);
            bindEvent('btn-open-course-1', btnOpen1);
            bindEvent('btn-open-course-2', btnOpen2);
            bindEvent('btn-open-course-3', btnOpen3);
            bindEvent('btn-open-course-4', btnOpen4);
            bindEvent('btn-open-course-5', btnOpen5);
            bindEvent('btn-open-course-6', btnOpen6);
            bindEvent('btn-open-course-7', btnOpen7);
            bindEvent('btn-open-course-8', btnOpen8);
            bindEvent('btn-open-course-9', btnOpen9);
            bindEvent('btn-open-course-10', btnOpen10);

        }, 300);
        </script>"""

        components.html(bind_js, height=0, width=0)
