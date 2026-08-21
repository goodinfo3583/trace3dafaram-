# views/settings_page.py
import streamlit as st

def run():
    st.title("⚙️ 系統設定中心")
    st.markdown("---")
    
    # 1. 主題設定
    st.subheader("🎨 介面風格設定")
    current_theme = st.session_state.get('theme', 'dark')
    
    theme_choice = st.radio(
        "選擇您偏好的底色：", 
        options=['dark', 'light'], 
        format_func=lambda x: "🌙 專業暗黑模式 (預設)" if x == 'dark' else "☀️ 亮白模式",
        index=0 if current_theme == 'dark' else 1
    )
    
    # 2. 快捷鍵設定
    st.markdown("---")
    st.subheader("⌨️ 快捷鍵配置")
    st.info("您可自訂對應的按鍵 (例如 F1, F2, alt+q)。設定完成後請點擊儲存，設定才會生效。")
    
    # 讀取現有設定
    default_hotkeys = {
        "f1": "NavToB1", "f2": "NavToB2", "f3": "NavToB3", 
        "f4": "NavToB4", "f5": "NavToB5", "f6": "NavToB6", "f7": "NavToB7",
        "alt+l": "NavToWatchlist", "escape": "NavToSystem"
    }
    current_hotkeys = st.session_state.get('custom_hotkeys', default_hotkeys)
    
    # 將 target (NavToB1) 反轉為易讀的名稱對應表，供 UI 顯示
    target_names = {
        "NavToB1": "區塊1: 法人動向", "NavToB2": "區塊2: 法人掃貨",
        "NavToB3": "區塊3: 法人連買", "NavToB4": "區塊4: 資券動向",
        "NavToB5": "區塊5: 大腿動向", "NavToB6": "區塊6: 鉅額交易",
        "NavToB7": "區塊7: 董監動向", "NavToWatchlist": "建立名單",
        "NavToSystem": "系統首頁"
    }
    
    # 產生反向查找字典 (用 target 找目前的 key)
    reverse_map = {v: k for k, v in current_hotkeys.items()}
    
    col1, col2 = st.columns(2)
    new_hotkeys = {}
    
    with col1:
        new_hotkeys["NavToB1"] = st.text_input("法人動向快捷鍵", value=reverse_map.get("NavToB1", "f1"))
        new_hotkeys["NavToB2"] = st.text_input("法人掃貨快捷鍵", value=reverse_map.get("NavToB2", "f2"))
        new_hotkeys["NavToB3"] = st.text_input("法人連買快捷鍵", value=reverse_map.get("NavToB3", "f3"))
        new_hotkeys["NavToB4"] = st.text_input("資券動向快捷鍵", value=reverse_map.get("NavToB4", "f4"))
        new_hotkeys["NavToSystem"] = st.text_input("系統首頁快捷鍵", value=reverse_map.get("NavToSystem", "escape"))
        
    with col2:
        new_hotkeys["NavToB5"] = st.text_input("大腿動向快捷鍵", value=reverse_map.get("NavToB5", "f5"))
        new_hotkeys["NavToB6"] = st.text_input("鉅額交易快捷鍵", value=reverse_map.get("NavToB6", "f6"))
        new_hotkeys["NavToB7"] = st.text_input("董監動向快捷鍵", value=reverse_map.get("NavToB7", "f7"))
        new_hotkeys["NavToWatchlist"] = st.text_input("建立名單快捷鍵", value=reverse_map.get("NavToWatchlist", "alt+l"))
        
    if st.button("💾 儲存並套用設定"):
        # 處理主題
        st.session_state['theme'] = theme_choice
        
        # 處理快捷鍵：轉為 JS 需要的字典格式 (key -> target)
        final_hotkeys_dict = {}
        for target, key in new_hotkeys.items():
            clean_key = key.strip().lower()
            if clean_key:
                final_hotkeys_dict[clean_key] = target
                
        st.session_state['custom_hotkeys'] = final_hotkeys_dict
        st.success("設定已成功儲存！頁面將刷新以套用新設定。")
        st.rerun() # 立即重整頁面讓 CSS 與 JS 設定生效
