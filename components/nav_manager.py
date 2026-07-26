# components/nav_manager.py
import streamlit.components.v1 as components

# 💡 1. 這裡加上 is_logged_in=False 參數
def inject_custom_header(is_logged_in=False):
    """注入客製化懸浮頂部導航與隱藏側邊欄邏輯"""

    # 💡 只有登入 B6 鎖起來
    login_btn_text = "VIP中心💎" if is_logged_in else "登入🛠️"
    b6_text = "鉅額交易" if is_logged_in else "🔒鉅額交易"
    
    inject_js = """
    <script>
    const parentDoc = window.parent.document;

    if (!parentDoc.getElementById('custom-sticky-header')) {
        const style = parentDoc.createElement('style');
        style.innerHTML = `
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stToolbar"] { display: none !important; }
            [data-testid="collapsedControl"] { top: 70px !important; z-index: 1000000 !important; background-color: rgba(10, 13, 20, 0.8) !important; border-radius: 50%; }

            #custom-sticky-header { position: fixed; top: 0; left: 0; width: 100%; z-index: 999999; background: transparent !important; pointer-events: none; }
            .disclaimer-bar, .nav-btn-container { pointer-events: auto; }
            .disclaimer-bar { display: flex; align-items: center; background: transparent !important; padding: 0px 15px; border: none !important; }
            .disclaimer-item { position: relative; padding: 6px 15px; cursor: help; background: transparent !important; }
            .disclaimer-title { color: #64748B; font-size: 13px; font-weight: 500; text-decoration: none; text-shadow: 1px 1px 4px rgba(0,0,0,1), -1px -1px 4px rgba(0,0,0,1); }
            .disclaimer-item:hover .disclaimer-title { color: #FFD700; text-shadow: 0 0 8px rgba(255, 215, 0, 0.8); }
            
            .vip-login-btn { color: #FFD700 !important; font-weight: bold; text-shadow: 0 0 5px rgba(255, 215, 0, 0.5); transition: all 0.3s; }
            .vip-login-btn:hover { text-shadow: 0 0 12px rgba(255, 215, 0, 1); transform: scale(1.05); }

            .disclaimer-content { position: absolute; top: 100%; left: 0; width: 350px; max-width: 90vw; background-color: rgba(17, 22, 34, 0.95); border: 1px solid #1E293B; border-top: none; border-radius: 0 0 8px 8px; padding: 0px 15px; max-height: 0; opacity: 0; overflow: hidden; transition: all 0.3s; font-size: 12px; color: #94A3B8; line-height: 1.6; box-shadow: 0px 8px 20px rgba(0,0,0,0.8); }
            .disclaimer-item:hover .disclaimer-content { max-height: 400px; opacity: 1; padding: 12px 15px; }
            
            .nav-btn-container { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; padding: 8px 15px; background: transparent !important; gap: 6px; border: none !important; transition: all 0.3s ease-in-out; }
            .nav-text-link { text-decoration: none !important; color: #94A3B8 !important; font-size: 16px; font-weight: 600; padding: 4px 6px; transition: all 0.2s ease-in-out; text-shadow: 1px 1px 4px rgba(0,0,0,1), -1px -1px 4px rgba(0,0,0,1); cursor: pointer; display: flex; align-items: center; }
            .nav-text-link:hover { color: #FFD700 !important; text-shadow: 0 0 12px rgba(255, 215, 0, 0.8); transform: scale(1.08); }
            .nav-divider { color: #334155; font-size: 16px; user-select: none; }
            #custom-sidebar-toggle { color: #38BDF8 !important; }

            /* 🎨 自訂圖片圖示的 CSS 樣式 */
            .nav-icon { width: 22px; height: 22px; margin-right: 5px; border-radius: 4px; object-fit: cover; position: relative; top: -2px; left: 0px; transition: all 0.3s ease-in-out; }
            .nav-text-link:hover .nav-icon { filter: drop-shadow(0px 0px 6px rgba(255, 215, 0, 0.9)) brightness(1.15); }
            
            @media (max-width: 768px) { .nav-btn-container { padding: 5px 10px; } .nav-divider { display: none; } .nav-text-link { font-size: 14px; margin: 2px; } }
            .stApp { margin-top: 50px !important; }
        `;
        parentDoc.head.appendChild(style);

        const headerDiv = parentDoc.createElement('div');
        headerDiv.id = 'custom-sticky-header';
        
        // 💡 2. 這裡原本寫死的文字，換成了 __LOGIN_TEXT__ 與 __B6_TEXT__
        headerDiv.innerHTML = `
            <div class="disclaimer-bar">
                <div class="disclaimer-item"><span class="disclaimer-title">使用聲明</span><div class="disclaimer-content">本平台僅供教育研究與籌碼觀察，絕不構成任何實質投資建議、勸誘或要約。所有資料源自公開數據，受限於網路技術，可能有延遲或錯誤。</div></div>
                <div class="disclaimer-item"><span class="disclaimer-title">隱私政策</span><div class="disclaimer-content"><b>1. 蒐集目的與範圍：</b><br>本平台依個資法蒐集您的識別資料僅供維持系統安全與優化服務使用。<br><b>2. 資料利用：</b><br>您的資料絕不向第三方洩露。<br><b>3. 資料刪除：</b><br>您可透過「聯絡我們」請求刪除資料。<br><b>4. 政策修訂：</b><br>本站保留修改政策之權利，繼續使用即視為同意。</b></div></div>
                <div class="disclaimer-item"><a href="#" data-target="NavToContact" class="disclaimer-title internal-nav" style="cursor: pointer;">聯絡我們</a></div>
                <div class="disclaimer-item"><a href="#" data-target="登入專區" class="disclaimer-title internal-nav vip-login-btn" style="cursor: pointer; display: flex; align-items: center;">__LOGIN_TEXT__</a></div>
                <div style="flex-grow: 1;"></div>
                <div class="disclaimer-item" id="mobile-nav-toggle" title="收起選單" style="cursor: pointer; padding-right: 5px;"><span id="nav-toggle-icon" style="font-size: 18px; color: #38BDF8;">📜</span></div>
            </div>
            <div class="nav-btn-container" id="nav-btn-container">
                <a href="#" id="custom-sidebar-toggle" class="nav-text-link"><img src="app/static/iconarrow1.png" class="nav-icon" alt="icon">呼叫側邊欄</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToNews" class="nav-text-link internal-nav"><img src="app/static/magicbook2.png" class="nav-icon" alt="icon">市場消息</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToPool" class="nav-text-link internal-nav"><img src="app/static/magicbookfire2.png" class="nav-icon" alt="icon">觀察名單</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToB1" class="nav-text-link internal-nav"><img src="app/static/magicbookleaf.png" class="nav-icon" alt="icon">法人動向</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToB2" class="nav-text-link internal-nav"><img src="app/static/magicbookwind.png" class="nav-icon" alt="icon">法人掃貨</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToB3" class="nav-text-link internal-nav"><img src="app/static/magicbookwater.png" class="nav-icon" alt="icon">法人連買</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToB4" class="nav-text-link internal-nav"><img src="app/static/magicbookground.png" class="nav-icon" alt="icon">資券動向</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToB5" class="nav-text-link internal-nav"><img src="app/static/wirtleg.png" class="nav-icon" alt="icon">大腿動向</a><span class="nav-divider">|</span>
                <a href="#" data-target="NavToB6" class="nav-text-link internal-nav"><img src="app/static/magicbookfire.png" class="nav-icon" alt="icon">__B6_TEXT__</a>
            </div>
        `;
        parentDoc.body.insertBefore(headerDiv, parentDoc.body.firstChild);

        setTimeout(() => {
            const navLinks = parentDoc.querySelectorAll('.internal-nav');
            navLinks.forEach(link => {
                link.onclick = (e) => {
                    e.preventDefault(); 
                    const targetName = link.getAttribute('data-target');
                    const btns = Array.from(parentDoc.querySelectorAll('button'));
                    const targetBtn = btns.find(b => b.textContent.includes(targetName));
                    if (targetBtn) targetBtn.click();
                };
            });

            const menuToggle = parentDoc.getElementById('mobile-nav-toggle');
            const navContainer = parentDoc.getElementById('nav-btn-container');
            const iconSpan = parentDoc.getElementById('nav-toggle-icon');
            if (menuToggle && navContainer && iconSpan) {
                menuToggle.onclick = (e) => {
                    e.preventDefault();
                    if (navContainer.style.display === 'none') {
                        navContainer.style.display = 'flex';
                        menuToggle.title = "收起選單";
                        iconSpan.innerText = '📜';
                        iconSpan.style.color = '#38BDF8';
                    } else {
                        navContainer.style.display = 'none';
                        menuToggle.title = "展開選單";
                        iconSpan.innerText = '📙';
                        iconSpan.style.color = '#FFD700';
                    }
                };
            }

            const toggleBtn = parentDoc.getElementById('custom-sidebar-toggle');
            if (toggleBtn) {
                toggleBtn.onclick = (e) => {
                    e.preventDefault();
                    const expandBtn = parentDoc.querySelector('[data-testid="collapsedControl"]');
                    if (expandBtn) expandBtn.click();
                    else {
                        const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
                        if (sidebar) {
                            const closeBtn = sidebar.querySelector('button');
                            if (closeBtn) closeBtn.click();
                        }
                    }
                };
            }

            setInterval(() => {
                const allBtns = Array.from(parentDoc.querySelectorAll('button'));
                allBtns.forEach(b => {
                    if(b.textContent.includes('NavTo') || b.textContent.includes('登入專區')) { 
                        const wrapper = b.closest('div[data-testid="stElementContainer"]');
                        if (wrapper) wrapper.style.display = 'none';
                    }
                });
            }, 100);
        }, 500);
    }
    </script>
    """
    
    # 💡 3. 這裡執行替換，把真正的狀態文字塞進 JS 裡面
    inject_js = inject_js.replace("__LOGIN_TEXT__", login_btn_text)
    inject_js = inject_js.replace("__B6_TEXT__", b6_text)

    # 透過隱藏的 iframe 執行上述的 JavaScript 注入
    components.html(inject_js, height=0, width=0)

# ==========================================
# (下方隱形切換按鈕 def render_proxy_buttons(): 維持不變)


# 放在 components/nav_manager.py 的最下方
import streamlit as st

def render_proxy_buttons():
    """幕後無縫換頁引擎 (隱藏的切換按鈕)"""
    def change_page(page_name):
        st.query_params["page"] = page_name 

    with st.container():
        # 建立隱形按鈕，這裡的字串必須對應你 JS 裡面的 data-target
        st.button("NavToContact", on_click=change_page, args=("contact",))
        st.button("NavToNews", on_click=change_page, args=("news",))
        st.button("NavToPool", on_click=change_page, args=("pool",))
        st.button("NavToB1", on_click=change_page, args=("b1",))
        st.button("NavToB2", on_click=change_page, args=("b2",))
        st.button("NavToB3", on_click=change_page, args=("b3",))
        st.button("NavToB4", on_click=change_page, args=("b4",))
        st.button("NavToB5", on_click=change_page, args=("b5",))
        st.button("NavToB6", on_click=change_page, args=("b6",))
        st.button("登入專區", on_click=change_page, args=("login",))
