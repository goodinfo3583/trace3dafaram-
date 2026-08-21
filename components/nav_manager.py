# components/nav_manager.py
import streamlit.components.v1 as components
import streamlit as st
import json

def inject_custom_header(is_logged_in=False):
    """注入客製化懸浮頂部導航與隱藏側邊欄邏輯 (支援動態快捷鍵與黑白主題)"""
    login_btn_text = "登出" if is_logged_in else "登入"
    b6_text = "鉅額交易"
    
    # 預設快捷鍵字典 (全部轉小寫以利 JS 判斷)
    default_hotkeys = {
        "f1": "NavToB1", "f2": "NavToB2", "f3": "NavToB3", 
        "f4": "NavToB4", "f5": "NavToB5", "f6": "NavToB6", "f7": "NavToB7",
        "alt+l": "NavToWatchlist", "escape": "NavToSystem"
    }
    # 若 Session 中有自訂快捷鍵則覆蓋，否則使用預設
    user_hotkeys = st.session_state.get('custom_hotkeys', default_hotkeys)
    hotkeys_json = json.dumps(user_hotkeys)
    
    inject_js = """
    <script>
    const parentWin = window.parent;
    const parentDoc = parentWin.document;

    // 清除舊的 Header 與 Style
    const oldHeader = parentDoc.getElementById('custom-sticky-header');
    if (oldHeader) oldHeader.remove();
    
    const oldStyle = parentDoc.getElementById('custom-nav-style');
    if (oldStyle) oldStyle.remove();

    /* ...(這裡保留你原本的 CSS style 樣式設定，請將原本 style.innerHTML = `...` 內的 CSS 貼回這裡) ... */
    
    // 【修改點1】這裡為了節省版面，假設你已經貼上原本的完整 CSS
    const style = parentDoc.createElement('style');
    style.id = 'custom-nav-style'; 
    style.innerHTML = `
        /* 💡 為了維持完整性，請將你原有的 nav CSS 全部貼回這裡 */
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        /* ... 其他省略 ... */
    `;
    parentDoc.head.appendChild(style);

    const headerDiv = parentDoc.createElement('div');
    headerDiv.id = 'custom-sticky-header';
    
    headerDiv.innerHTML = `
        <!-- 【修改點2】在系統下拉選單中，加入"設定"按鈕 -->
        <div class="disclaimer-bar">
            <div class="system-menu">
                <div class="system-menu-title" title="系統與聲明">
                    <img src="app/static/icon-system.png" class="system-icon" alt="系統">
                </div>
                <div class="system-dropdown">
                    <div class="dropdown-item actionable" style="text-align: center;">
                        <a href="#" data-target="__LOGIN_TEXT__" class="dropdown-title internal-nav vip-login-btn">
                            <img src="app/static/icon-login.png" class="menu-icon" alt="login"> __LOGIN_TEXT__
                        </a>
                    </div>
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToSystem" class="dropdown-title internal-nav">
                            <img src="app/static/icon-system.png" class="menu-icon" alt="system"> 系統首頁 <span style="color:#64748b; font-size:10px;">(Esc)</span>
                        </a>
                    </div>
                    <!-- 新增的設定按鈕 -->
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToSettings" class="dropdown-title internal-nav">
                            <img src="app/static/icon-system.png" class="menu-icon" alt="settings"> ⚙️ 系統設定
                        </a>
                        <p class="dropdown-text">自訂介面風格與專屬鍵盤快捷鍵。</p>
                    </div>
                    <!-- 聯絡我們與其他按鈕保留... -->
                </div>
            </div>
            <!-- 工具箱按鈕與其他介面保留... -->
        </div>
    `;
    // 礙於字數，這裡省略你原本的 HTML，請記得把下拉選單更新進去
    parentDoc.body.insertBefore(headerDiv, parentDoc.body.firstChild);

    setTimeout(() => {
        // 點擊綁定
        const navLinks = parentDoc.querySelectorAll('.internal-nav');
        navLinks.forEach(link => {
            link.onclick = (e) => {
                e.preventDefault(); 
                const targetName = link.getAttribute('data-target');
                const btns = Array.from(parentDoc.querySelectorAll('button'));
                const targetBtn = btns.find(b => b.textContent.trim() === targetName || b.textContent.includes(targetName));
                if (targetBtn) targetBtn.click();
            };
        });

        // ==========================================
        // 【修改點3】全新強化的動態快捷鍵引擎
        // ==========================================
        const hotkeysMap = JSON.parse(`__HOTKEYS_JSON__`);

        // 避免重複綁定：先移除舊的監聽器
        if (parentWin.customHotkeyHandler) {
            parentDoc.removeEventListener('keydown', parentWin.customHotkeyHandler);
        }

        // 建立新的監聽器
        parentWin.customHotkeyHandler = function(e) {
            // 焦點在輸入框時不觸發
            const activeTag = parentDoc.activeElement ? parentDoc.activeElement.tagName.toLowerCase() : '';
            if (activeTag === 'input' || activeTag === 'textarea') return;

            // 組合使用者按下的按鍵字串 (例如: alt+l, f1, escape)
            let combo = [];
            if (e.ctrlKey) combo.push('ctrl');
            if (e.altKey) combo.push('alt');
            if (e.shiftKey) combo.push('shift');
            combo.push(e.key.toLowerCase());
            let keyStr = combo.join('+');

            // 如果字典裡有這個快捷鍵
            if (hotkeysMap[keyStr]) {
                e.preventDefault(); // 🔥 攔截瀏覽器預設行為 (例如 F1不會跳出說明, F3不會跳出搜尋)
                const targetName = hotkeysMap[keyStr];
                const btns = Array.from(parentDoc.querySelectorAll('button'));
                const targetBtn = btns.find(b => b.textContent.trim() === targetName);
                if (targetBtn) {
                    targetBtn.click();
                }
            }
        };
        
        parentDoc.addEventListener('keydown', parentWin.customHotkeyHandler);

        // ... 保留隱藏原生按鈕等邏輯 ...
    }, 500);
    </script>
    """
    
    inject_js = inject_js.replace("__LOGIN_TEXT__", login_btn_text)
    inject_js = inject_js.replace("__B6_TEXT__", b6_text)
    inject_js = inject_js.replace("__HOTKEYS_JSON__", hotkeys_json)
    
    components.html(inject_js, height=0, width=0)

# Python 隱藏按鈕對應區
def render_proxy_buttons():
    def change_page(page_name):
        st.query_params["page"] = page_name 

    def handle_logout():
        st.session_state.clear()
        st.query_params["page"] = "home"

    with st.container():
        st.button("NavToSettings", on_click=change_page, args=("settings",)) # 🔥新增設定頁面路由
        # ... 保留其他 NavTo按鈕 ...
        st.button("登入", on_click=change_page, args=("login",))
        st.button("登出", on_click=handle_logout)
