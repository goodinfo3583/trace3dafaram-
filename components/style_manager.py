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
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 基礎介面顏色定義 (背景色由濾鏡透明度決定)
    if theme == 'pink': bg_color = f"rgba(237, 184, 242, {opacity})"
    elif theme == 'green': bg_color = f"rgba(10, 20, 15, {opacity})"
    elif theme == 'blue': bg_color = f"rgba(184, 236, 242, {opacity})"
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

    # 🚀 終極版全域拖曳引擎 (事件代理架構)：不論是 HTML 還是 Streamlit 容器，只要有標籤全部通殺！
    drag_engine_js = """
    <script>
    (function() {
        if (window.parent.window.customDragDelegated) return;
        window.parent.window.customDragDelegated = true;
        const doc = window.parent.document;
        
        let isDragging = false, currentEl = null, startX, startY, initialX, initialY;
        
        const onDown = (e) => {
            // 尋找被點擊的目標是否是標題把手
            let handle = e.target.closest('.header-bar, .header-bar-b2, .header-bar-b4, .header-bar-b5, .npc-drag-handle, .settings-drag-handle');
            if (!handle) return;
            
            // 排除按鈕與輸入框的誤觸
            if (e.target.closest('button, input, label, .action-btn, .action-btn-b2, .action-btn-b4, .action-btn-b5')) return;
            
            // 往上尋找要移動的實體視窗外框
            let el = handle.closest('.glass-panel, .glass-panel-b2, .glass-panel-b4, .glass-panel-b5, .npc-wrapper, .settings-modal-active');
            if (!el) {
                // 特別相容 Streamlit 容器
                el = handle.closest('div[data-testid="stVerticalBlock"].settings-modal-active');
            }
            if (!el) return;
            
            isDragging = true;
            currentEl = el;
            
            let clientX = e.touches ? e.touches[0].clientX : e.clientX;
            let clientY = e.touches ? e.touches[0].clientY : e.clientY;
            startX = clientX;
            startY = clientY;
            
            let rect = el.getBoundingClientRect();
            el.style.transition = 'none'; // 拖曳時關閉動畫，實現零延遲
            el.style.left = rect.left + 'px';
            el.style.top = rect.top + 'px';
            el.style.right = 'auto';
            el.style.bottom = 'auto';
            el.style.transform = 'none';
            el.style.margin = '0';
            
            initialX = rect.left;
            initialY = rect.top;
            
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
                currentEl.style.transition = ''; // 放開時恢復動畫
                let handle = currentEl.querySelector('.header-bar, .header-bar-b2, .header-bar-b4, .header-bar-b5, .npc-drag-handle, .settings-drag-handle');
                if(handle) handle.style.cursor = 'grab';
            }
            isDragging = false;
            currentEl = null;
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

def set_background(image_path="app/static/沙漠之城.png"):
    """網站主視覺背景設定引擎 (支援濾鏡與主題自動連動)"""
    theme = st.session_state.get('theme', 'dark')
    opacity = st.session_state.get('bg_opacity', 88) / 100.0
    block_opacity = opacity * 0.7 # 方塊背景比濾鏡稍透
    
    # 💡 自動連動背景圖片與對應顏色的濾鏡
    actual_image = image_path
    if theme == 'pink':
        overlay, block_bg = f"rgba(35, 15, 25, {opacity})", f"rgba(35, 15, 25, {block_opacity})"
        actual_image = "app/static/櫻花都市.png"
    elif theme == 'green':
        overlay, block_bg = f"rgba(15, 35, 20, {opacity})", f"rgba(15, 35, 20, {block_opacity})"
        actual_image = "app/static/翡翠林鎮.png"
    elif theme == 'blue':
        overlay, block_bg = f"rgba(15, 20, 40, {opacity})", f"rgba(15, 20, 40, {block_opacity})"
        actual_image = "app/static/天空城.png"
    else: # 預設 dark
        overlay, block_bg = f"rgba(15, 23, 42, {opacity})", f"rgba(15, 23, 42, {block_opacity})"
    
    # 圖片防呆：如果該主題的圖片還沒建立，就退回預設背景圖片
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

# ==========================================
# 📊 B2, B3, B4, B5 玻璃卡片 (保持原本邏輯與縮排)
# ==========================================
# (在此為節省長度，B2~B4 的代碼邏輯與上次更新完全相同，請直接保留您現有的 B2, B3, B4, B5 函數即可)
# 確保您的 B5 `make_resonance_html` 已經套用了 `justify-content:flex-start;` 的排版微調！


# ==========================================
# ⚙️ 設置中心 懸浮卡片 (上方 X，下方確認/取消)
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
            
            # 💡 頂部：標題 + 右側 X 按鈕
            col_title, col_x = st.columns([9, 1])
            with col_title:
                st.markdown("<h3 class='settings-drag-handle' style='color:#00D2FF; margin-top:0;' title='按住此處可拖曳視窗'>⚙️ 設置中心</h3>", unsafe_allow_html=True)
            with col_x:
                if st.button("✕", key="settings_btn_close_top"):
                    st.session_state['show_settings'] = False
                    st.rerun()

            st.markdown("<h4 style='color:#E2E8F0; font-size: 16px;'>🎨 外觀與濾鏡</h4>", unsafe_allow_html=True)
            current_theme = st.session_state.get('theme', 'dark')
            current_opacity = st.session_state.get('bg_opacity', 88)
            
            theme_options = ['dark', 'pink', 'green', 'blue']
            theme_choice = st.radio("選擇背景主題 (將同步切換圖片)：", options=theme_options, format_func=lambda x: {'dark': "🌙 專業暗黑", 'pink': "🌸 櫻花粉", 'green': "🌲 翡翠綠", 'blue': "🌌 天空藍"}[x], index=theme_options.index(current_theme) if current_theme in theme_options else 0, horizontal=True)
            
            # 💡 新增：濾鏡透明度滑桿
            opacity_val = st.slider("背景濾鏡透明度 (%)", min_value=0, max_value=100, value=current_opacity)
            
            st.markdown("---")
            st.markdown("<h4 style='color:#E2E8F0; font-size: 16px;'>⌨️ 快捷鍵配置 (點擊欄位後直接按下按鍵)</h4>", unsafe_allow_html=True)
            
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
            
            # 💡 底部：確認 與 取消 按鈕
            col_ok, col_cancel = st.columns(2)
            with col_ok:
                if st.button("💾 確認", use_container_width=True):
                    st.session_state['theme'] = theme_choice
                    st.session_state['bg_opacity'] = opacity_val
                    st.session_state['custom_hotkeys'] = {k.strip().lower(): v for v, k in new_hotkeys.items() if k.strip().lower()}
                    st.session_state['show_settings'] = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ 取消", use_container_width=True):
                    st.session_state['show_settings'] = False
                    st.rerun()
                    
        # JS 綁定設定視窗與快捷鍵捕捉
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
# 🎓 課程 NPC 懸浮對話框 (💡 已移除所有空白行與註解，徹底消滅 Markdown 破圖)
# ==========================================
def render_course_npc():
    import streamlit as st
    if st.session_state.get('show_course_npc', False):
        # 💡 將整個 HTML 包裝得極度緊湊，避免 Streamlit 遇到空行就當作純文字解析
        html_code = """<input type="checkbox" id="close-npc" style="display:none;"><input type="radio" name="course_tabs" id="tab-list" checked style="display:none;"><input type="radio" name="course_tabs" id="tab-detail-4" style="display:none;"><style>
#close-npc:checked ~ .npc-wrapper { display: none !important; }
#tab-list:checked ~ .npc-wrapper .view-list { display: flex; }
#tab-list:not(:checked) ~ .npc-wrapper .view-list { display: none; }
#tab-detail-4:checked ~ .npc-wrapper .view-detail { display: flex; }
#tab-detail-4:not(:checked) ~ .npc-wrapper .view-detail { display: none; }
.npc-wrapper { position: fixed; bottom: 30px; right: 30px; z-index: 9999999; }
.npc-overlay { width: 650px; height: 75vh; max-height: 800px; background: rgba(15, 23, 42, 0.96); border: 2px solid #00D2FF; border-radius: 12px; display: flex; flex-direction: column; padding: 25px; box-shadow: 0 8px 30px rgba(0, 210, 255, 0.3); color: white; animation: slideUpNPC 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.npc-overlay.wide { width: 800px; height: 85vh; max-height: 900px; }
.npc-drag-handle { display: flex; align-items: flex-end; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; cursor: grab; }
.npc-drag-handle:active { cursor: grabbing; }
.npc-image { width: 90px; height: 90px; background-image: url('app/static/npcnatzu.png'); background-size: contain; background-repeat: no-repeat; background-position: bottom; margin-right: 20px; filter: drop-shadow(0 0 5px rgba(0,210,255,0.5)); pointer-events: none; }
.npc-big-image { width: 160px; height: 180px; background-image: url('app/static/npcroxy.png'); background-size: contain; background-repeat: no-repeat; background-position: bottom; filter: drop-shadow(0 0 10px rgba(0,210,255,0.6)); flex-shrink: 0; pointer-events: none; }
.npc-title-box { flex: 1; pointer-events: none; }
.npc-name { color: #00D2FF; font-weight: bold; font-size: 22px; margin-bottom: 6px; }
.npc-greet { font-size: 15px; color: #94A3B8; }
.course-list, .table-container { flex: 1; overflow-y: auto; padding-right: 15px; }
.course-list::-webkit-scrollbar, .table-container::-webkit-scrollbar { width: 8px; }
.course-list::-webkit-scrollbar-thumb, .table-container::-webkit-scrollbar-thumb { background: rgba(0, 210, 255, 0.4); border-radius: 4px; }
.course-item { margin-bottom: 18px; padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; transition: 0.2s; display: block; }
.course-item.locked { cursor: not-allowed; background: rgba(0,0,0,0.2); }
.course-item.active { cursor: pointer; border-color: rgba(0, 210, 255, 0.4); }
.course-item.active:hover { background: rgba(0, 210, 255, 0.1); border-color: #00D2FF; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,210,255,0.2); }
.course-icon { width: 24px; height: 24px; object-fit: contain; margin-right: 8px; filter: drop-shadow(0 0 5px rgba(0,210,255,0.8)); transition: 0.3s; vertical-align: middle; }
.course-item.locked .course-icon { filter: grayscale(100%) opacity(0.4); }
.course-item.active:hover .course-icon { filter: drop-shadow(0 0 10px #FFD700); transform: scale(1.1); }
.course-title { font-weight: bold; font-size: 16px; margin-bottom: 8px; }
.course-item.locked .course-title { color: #64748B; }
.course-item.active .course-title { color: #FFD700; }
.course-desc { font-size: 14px; color: #CBD5E1; line-height: 1.6; }
.close-btn { position: absolute; top: 15px; right: 20px; cursor: pointer; color: #94A3B8; font-size: 24px; transition: 0.2s; z-index: 10; font-weight: bold; }
.close-btn:hover { color: #FF4C4C; transform: scale(1.1); }
.top-actions { position: absolute; top: 15px; right: 20px; display: flex; gap: 12px; z-index: 10; }
.action-btn { cursor: pointer; color: #94A3B8; font-size: 20px; font-weight:bold; transition: 0.2s; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); width: 32px; height: 32px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.1); }
.action-btn:hover { background: rgba(0,210,255,0.3); color: #FFF; transform: scale(1.1); border-color: #00D2FF; }
.action-btn.close:hover { background: rgba(255,76,76,0.8); border-color: #FF4C4C; }
.dialogue-box { flex: 1; background: rgba(0, 210, 255, 0.08); border: 1px solid rgba(0, 210, 255, 0.3); border-radius: 12px; padding: 18px; position: relative; margin-bottom: 10px; pointer-events: none; }
.dialogue-box::before { content: ''; position: absolute; left: -14px; bottom: 30px; border-width: 12px 14px 12px 0; border-style: solid; border-color: transparent rgba(0, 210, 255, 0.3) transparent transparent; }
.npc-text { font-size: 15px; color: #E2E8F0; line-height: 1.6; }
.pv-table { width: 100%; border-collapse: collapse; font-size: 15px; text-align: center; }
.pv-table th { background: rgba(0, 210, 255, 0.15); color: #00D2FF; padding: 12px; border-bottom: 2px solid #00D2FF; font-weight: bold; }
.pv-table td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); color: #CBD5E1; }
.pv-table tr:hover td { background: rgba(255,255,255,0.05); color: #FFF; }
.trend-up { color: #FF4C4C; font-weight: bold; }
.trend-down { color: #00E676; font-weight: bold; }
.trend-flat { color: #FFD700; font-weight: bold; }
@keyframes slideUpNPC { from { transform: translateY(100px) scale(0.8); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
</style><div class="npc-wrapper"><div class="npc-overlay view-list"><label for="close-npc" class="close-btn" title="關閉">✕</label><div class="npc-drag-handle" title="按住此處可拖曳視窗"><div class="npc-image"></div><div class="npc-title-box"><div class="npc-name">籌碼導師</div><div class="npc-greet">「冒險者，選擇你想強化的能力吧！」</div></div></div><div class="course-list"><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 1. 宏觀經濟與景氣循環 (未開放)</div><div class="course-desc">學習解讀 GDP、CPI、利率與匯率等基本總體經濟指標，判斷目前大盤處於景氣擴張或衰退的哪個階段。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 2. 股市基本架構與名詞解析 (未開放)</div><div class="course-desc">認識台股交易規則、漲跌幅限制、各類委託單與基本盤面術語，建立進場前的基礎常識。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 3. 財報與基本面入門 (未開放)</div><div class="course-desc">學習閱讀三大財務報表（綜合損益表、資產負債表、現金流量表），學會挑選具備長期競爭力的公司。</div></div><label for="tab-detail-4" class="course-item active"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 4. 量價關係與盤面解讀 (點擊進入)</div><div class="course-desc">對照成交量與股價漲跌的互動（如價漲量增、量價背離），判斷多空雙方的企圖心與買賣力道。</div></label><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 5. 技術分析與指標應用 (未開放)</div><div class="course-desc">熟悉常用技術指標（如均線 MA、MACD、RSI、KDJ），掌握支撐壓力與趨勢轉折點。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 6. 籌碼面追蹤：法人與大戶結構 (未開放)</div><div class="course-desc">分析外資、投信、自營商動向及大戶持股比例，透過資金流向尋找主力默默佈局的標的。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 7. 券資關係與融資融券分析 (未開放)</div><div class="course-desc">觀察融資餘額、融券張數與券資比變化，評估市場散戶情緒及潛在的「軋空」或「多殺多」力道。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 8. 產業趨勢與題材選股 (未開放)</div><div class="course-desc">掌握主流產業輪動脈絡（如半導體、AI 供應鏈、綠能等），在對的時間點佈局具備成長爆發力的賽道。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 9. 資金控管與風險管理 (未開放)</div><div class="course-desc">學習單筆投資部位配置、分批進場策略、停損停利機制，避免因情緒失控而遭受重大虧損。</div></div><div class="course-item locked"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon" onerror="this.style.display='none'"> 10. 交易心理學與個人策略總結 (未開放)</div><div class="course-desc">克服貪婪與恐懼的心理障礙，並回測、修正並建立專屬於自己的穩定獲利交易系統。</div></div></div></div><div class="npc-overlay wide view-detail"><div class="top-actions"><label for="tab-list" class="action-btn" title="返回列表">↩</label><label for="close-npc" class="action-btn close" title="關閉">✕</label></div><div class="npc-drag-handle" style="gap:20px;" title="按住此處可拖曳視窗"><div class="npc-big-image"></div><div class="dialogue-box"><div class="npc-name">籌碼導師 蘿西</div><div class="npc-text">「量價關係是市場最真實的足跡！仔細看這張表，當『量』與『價』出現背離時，就是趨勢即將反轉的危險警訊喔！」</div></div></div><div class="table-container"><table class="pv-table"><thead><tr><th width="15%">趨勢</th><th width="20%">狀態</th><th width="65%">市場含義</th></tr></thead><tbody><tr><td class="trend-up">上漲</td><td>價升量縮</td><td style="text-align: left;">量價背離，下方有承接，短期回調，後續拉高</td></tr><tr><td class="trend-up">上漲</td><td>放量滯漲</td><td style="text-align: left;">趨勢高位，拋壓增大，即將見頂反轉，減倉清倉</td></tr><tr><td class="trend-up">上漲</td><td>縮量大漲</td><td style="text-align: left;">趨勢中途，縮量加速，鎖倉高控盤，延續上漲</td></tr><tr><td class="trend-up">上漲</td><td>放量大漲</td><td style="text-align: left;">價漲量增，量價齊升，多方吸籌，持續看漲</td></tr><tr><td class="trend-down">下跌</td><td>縮量小跌</td><td style="text-align: left;">主力洗盤，拋壓減弱，止跌位置，擇機進場</td></tr><tr><td class="trend-down">下跌</td><td>放量小跌</td><td style="text-align: left;">見底信號，買方增強，越跌越買，反轉新倉</td></tr><tr><td class="trend-down">下跌</td><td>縮量大跌</td><td style="text-align: left;">一致看空，無人接盤，下跌中繼，加速下跌</td></tr><tr><td class="trend-down">下跌</td><td>放量大跌</td><td style="text-align: left;">跟風砸盤，大量賣出，高位出貨，持續下跌</td></tr><tr><td class="trend-flat">平量</td><td>平量滯漲</td><td style="text-align: left;">拋壓增大，越漲越難，高位見頂</td></tr><tr><td class="trend-flat">平量</td><td>平量大漲</td><td style="text-align: left;">一致看漲，沒有拋壓，鎖倉高控盤，加速上漲</td></tr><tr><td class="trend-flat">平量</td><td>平量價縮</td><td style="text-align: left;">下跌中繼，弱反彈信號，逢高減倉</td></tr><tr><td class="trend-flat">平量</td><td>平量大跌</td><td style="text-align: left;">一致看空，沒有承接，下跌中繼，加速下跌</td></tr></tbody></table></div></div></div>"""
        st.markdown(html_code, unsafe_allow_html=True)
