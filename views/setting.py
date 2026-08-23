# views/setting.py
import streamlit as st
import streamlit.components.v1 as components

def render():
    # 💡 移除原本的懸浮 CSS (position: fixed, drag-handle)，改為乾淨的全螢幕排版
    st.markdown("<h2 style='color:#00D2FF; margin-top:10px;'>設置中心</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; font-size:14px;'>調整將會自動套用至系統頁面，完成後請點擊下方確認。</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<h4 style='color:#E2E8F0; font-size: 16px;'>外觀與濾鏡</h4>", unsafe_allow_html=True)
    current_theme = st.session_state.get('theme', 'dark')
    current_opacity = int(st.session_state.get('bg_opacity', 88))
    
    theme_options = ['dark', 'pink', 'green', 'purple','brown']
    theme_choice = st.radio(
        "選擇背景主題 (將同步切換圖片)：", 
        options=theme_options, 
        format_func=lambda x: {'dark': "暗黑(預設)", 'pink': "鋼鐵褐", 'green': "翡翠綠", 'purple': "月影紫", 'brown':"沙漠棕"}[x], 
        index=theme_options.index(current_theme) if current_theme in theme_options else 0, 
        horizontal=True
    )
    
    opacity_val = st.slider("背景濾鏡遮罩 (%)", min_value=0, max_value=100, value=current_opacity)
    
    st.markdown("---")
    st.markdown("<h4 style='color:#E2E8F0; font-size: 16px;'>快捷鍵配置 (點擊欄位後直接按下按鍵)</h4>", unsafe_allow_html=True)
    
    reverse_map = {v: k for k, v in st.session_state.get('custom_hotkeys', {"f1": "NavToB1", "f2": "NavToB2", "f3": "NavToB3", "f4": "NavToB4", "f5": "NavToB5", "f6": "NavToB6", "f7": "NavToB7", "alt+l": "NavToWatchlist", "escape": "登入"}).items()}
    
    col1, col2 = st.columns(2)
    new_hotkeys = {}
    with col1:
        new_hotkeys["NavToB1"] = st.text_input("法人動向", value=reverse_map.get("NavToB1", "F1"), key="kb1")
        new_hotkeys["NavToB2"] = st.text_input("法人掃貨", value=reverse_map.get("NavToB2", "F2"), key="kb2")
        new_hotkeys["NavToB3"] = st.text_input("法人連買", value=reverse_map.get("NavToB3", "F3"), key="kb3")
        new_hotkeys["NavToB4"] = st.text_input("資券動向", value=reverse_map.get("NavToB4", "F4"), key="kb4")
        new_hotkeys["NavToB5"] = st.text_input("大腿動向", value=reverse_map.get("NavToB5", "F6"), key="kb5")
    with col2:
        
        new_hotkeys["NavToB6"] = st.text_input("鉅額交易", value=reverse_map.get("NavToB6", "F7"), key="kb6")
        new_hotkeys["NavToB7"] = st.text_input("董監動向", value=reverse_map.get("NavToB7", "F8"), key="kb7")
        new_hotkeys["NavToWatchlist"] = st.text_input("建立名單", value=reverse_map.get("NavToWatchlist", "alt+l"), key="kb_wl")
        new_hotkeys["登入"] = st.text_input("登入", value=reverse_map.get("登入", "escape"), key="kb_login")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # -----------------------------
    # 底部：儲存與取消按鈕 (保留在當前頁面)
    # -----------------------------
    col_ok, col_cancel = st.columns([1, 1])
    with col_ok:
        if st.button("確認", use_container_width=True):
            # 寫入 session_state
            st.session_state['theme'] = theme_choice
            st.session_state['bg_opacity'] = opacity_val
            st.session_state['custom_hotkeys'] = {k.strip().lower(): v for v, k in new_hotkeys.items() if k.strip().lower()}
            
            # 使用 toast 顯示右下角輕量提示，不干擾畫面
            st.toast('設定已成功儲存！')
            
            # 重新執行一次以立即套用新主題與濾鏡
            st.rerun()
            
    with col_cancel:
        if st.button("取消", use_container_width=True):
            # 什麼都不做，直接 rerun 就會讀取原本存在 session_state 裡的設定值
            st.toast('已恢復為原本的設定。')
            st.rerun()
            
    # 💡 乾淨的 JS：不再需要尋找 modal 容器，直接綁定頁面上所有的 text input
    keybind_js = """
    <script>
    setTimeout(() => {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        inputs.forEach(input => {
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
            input.addEventListener('focus', function() { this.style.boxShadow = '0 0 10px #00D2FF'; });
            input.addEventListener('blur', function() { this.style.boxShadow = 'none'; });
        });
    }, 500);
    </script>
    """
    components.html(keybind_js, height=0, width=0)
