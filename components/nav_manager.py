# components/nav_manager.py
import streamlit.components.v1 as components

def inject_custom_header(is_logged_in=False):
    """注入客製化懸浮頂部導航與隱藏側邊欄邏輯"""
    login_btn_text = "登出" if is_logged_in else "登入"
    b6_text = "鉅額交易"
    
    inject_js = """
    <script>
    const parentDoc = window.parent.document;

    const oldHeader = parentDoc.getElementById('custom-sticky-header');
    if (oldHeader) oldHeader.remove();
    
    const oldStyle = parentDoc.getElementById('custom-nav-style');
    if (oldStyle) oldStyle.remove();

    const style = parentDoc.createElement('style');
    style.id = 'custom-nav-style'; 
    style.innerHTML = `
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="collapsedControl"] { top: 70px !important; z-index: 1000000 !important; background-color: rgba(10, 13, 20, 0.8) !important; border-radius: 50%; }

        #custom-sticky-header { position: fixed; top: 0; left: 0; width: 100%; z-index: 999999; background: transparent !important; pointer-events: none; }
        .disclaimer-bar, .nav-btn-container { pointer-events: auto; }
        .disclaimer-bar { display: flex; align-items: center; background: transparent !important; padding: 0px 15px; border: none !important; }
        
        /* ⚙️ 系統下拉選單樣式 */
        .system-menu { position: relative; padding: 6px 15px; cursor: pointer; background: transparent !important; }
        .system-menu-title { color: #64748B; font-size: 14px; font-weight: bold; display: flex; align-items: center; gap: 5px; transition: color 0.3s; text-shadow: 1px 1px 4px rgba(0,0,0,1); }
        .system-menu:hover .system-menu-title { color: #00D2FF; text-shadow: 0 0 8px rgba(0, 210, 255, 0.8); }
        
        .system-dropdown { position: absolute; top: 100%; left: 10px; width: 280px; background-color: rgba(17, 22, 34, 0.95); border: 1px solid #1E293B; border-top: none; border-radius: 0 0 8px 8px; padding: 0; max-height: 0; opacity: 0; overflow: hidden; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0px 8px 20px rgba(0,0,0,0.8); z-index: 1000; }
        .system-menu:hover .system-dropdown { max-height: 500px; opacity: 1; padding: 8px 0; }
        
        .dropdown-item { padding: 10px 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .dropdown-item:last-child { border-bottom: none; }
        
        .dropdown-title { color: #E2E8F0; font-size: 13px; font-weight: bold; margin-bottom: 4px; display: block; text-decoration: none; transition: color 0.2s; cursor: pointer; }
        .dropdown-text { font-size: 11px; color: #94A3B8; line-height: 1.5; margin: 0; }
        
        /* 懸停效果與按鈕特化 */
        .dropdown-item:hover { background-color: rgba(255,255,255,0.03); }
        .dropdown-item.actionable:hover .dropdown-title { color: #FFD700; }
        
        .vip-login-btn { color: #FFD700 !important; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 5px;}
        .vip-login-btn:hover { text-shadow: 0 0 10px rgba(255, 215, 0, 0.8); }

        .nav-btn-container { display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; padding: 8px 15px; background: transparent !important; gap: 6px; border: none !important; transition: all 0.3s ease-in-out; }
        .nav-text-link { text-decoration: none !important; color: #94A3B8 !important; font-size: 16px; font-weight: 600; padding: 4px 6px; transition: all 0.2s ease-in-out; text-shadow: 1px 1px 4px rgba(0,0,0,1), -1px -1px 4px rgba(0,0,0,1); cursor: pointer; display: flex; align-items: center; }
        .nav-text-link:hover { color: #FFD700 !important; text-shadow: 0 0 12px rgba(255, 215, 0, 0.8); transform: scale(1.08); }
        .nav-divider { color: #334155; font-size: 16px; user-select: none; }
        #custom-sidebar-toggle { color: #38BDF8 !important; }

        .nav-icon { width: 22px; height: 22px; margin-right: 5px; border-radius: 4px; object-fit: cover; position: relative; top: -2px; left: 0px; transition: all 0.3s ease-in-out; }
        .nav-text-link:hover .nav-icon { filter: drop-shadow(0px 0px 6px rgba(255, 215, 0, 0.9)) brightness(1.15); }
        
        .global-radar-toggle {
            display: flex; align-items: center; cursor: pointer; padding: 4px 10px; margin-right: 15px;
            background: rgba(15, 23, 42, 0.6); border: 1px solid #38BDF8; border-radius: 20px;
            transition: all 0.3s ease; backdrop-filter: blur(4px);
        }
        .global-radar-toggle:hover {
            background: rgba(56, 189, 248, 0.2); border-color: #FFD700; box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
        }
        .global-radar-toggle img { width: 18px; height: 18px; margin-right: 6px; border-radius: 50%; }
        .global-radar-toggle span { color: #38BDF8; font-size: 13px; font-weight: bold; transition: color 0.3s; }
        .global-radar-toggle:hover span { color: #FFD700; }

        @media (max-width: 768px) { .nav-btn-container { padding: 5px 10px; } .nav-divider { display: none; } .nav-text-link { font-size: 14px; margin: 2px; } .global-radar-toggle { display: flex; } }
        .stApp { margin-top: 50px !important; }
    `;
    parentDoc.head.appendChild(style);

    const headerDiv = parentDoc.createElement('div');
    headerDiv.id = 'custom-sticky-header';
    
    headerDiv.innerHTML = `
        <div class="disclaimer-bar">
            <!-- 💡 新增：系統下拉選單 -->
            <div class="system-menu">
                <div class="system-menu-title">⚙️ 系統</div>
                <div class="system-dropdown">
                    <div class="dropdown-item">
                        <span class="dropdown-title">📜 聲明</span>
                        <p class="dropdown-text">本平台僅供教育研究與籌碼觀察，絕不構成實質投資建議。資料源自公開數據，可能有延遲或錯誤。</p>
                    </div>
                    <div class="dropdown-item">
                        <span class="dropdown-title">🛡️ 隱私</span>
                        <p class="dropdown-text">依個資法蒐集識別資料僅供優化服務，絕不外流。可透過聯絡我們請求刪除資料。</p>
                    </div>
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToContact" class="dropdown-title internal-nav">📧 聯絡訊息</a>
                    </div>
                    <div class="dropdown-item actionable" style="text-align: center; border-bottom: none;">
                        <a href="#" data-target="登入" class="dropdown-title internal-nav vip-login-btn">🔐 __LOGIN_TEXT__</a>
                    </div>
                </div>
            </div>

            <div style="flex-grow: 1;"></div>
            
            <!-- 💡 修改：排行按鈕文字固定為「排行」 -->
            <div id="global-radar-btn" class="global-radar-toggle" title="開關排行卡片">
                <img src="app/static/17.png" alt="雷達總控">
                <span id="global-radar-text">排行</span>
            </div>

            <div class="disclaimer-item" id="mobile-nav-toggle" title="收起選單" style="cursor: pointer; padding-right: 5px;"><span id="nav-toggle-icon" style="font-size: 18px; color: #38BDF8;">📜</span></div>
        </div>
        
        <div class="nav-btn-container" id="nav-btn-container">
            <a href="#" id="custom-sidebar-toggle" class="nav-text-link"><img src="app/static/iconarrow1.png" class="nav-icon" alt="icon">側欄功能</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToNews" class="nav-text-link internal-nav"><img src="app/static/magicbook2.png" class="nav-icon" alt="icon">市場消息</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToPool" class="nav-text-link internal-nav"><img src="app/static/magicbookfire2.png" class="nav-icon" alt="icon">觀察名單</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToWatchlist" class="nav-text-link internal-nav"><img src="app/static/iconwathclist.png" class="nav-icon" alt="icon">建立名單</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB1" class="nav-text-link internal-nav"><img src="app/static/magicbookleaf.png" class="nav-icon" alt="icon">法人動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB2" class="nav-text-link internal-nav"><img src="app/static/magicbookwind.png" class="nav-icon" alt="icon">法人掃貨</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB3" class="nav-text-link internal-nav"><img src="app/static/magicbookwater.png" class="nav-icon" alt="icon">法人連買</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB4" class="nav-text-link internal-nav"><img src="app/static/magicbookground.png" class="nav-icon" alt="icon">資券動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB5" class="nav-text-link internal-nav"><img src="app/static/wirtleg.png" class="nav-icon" alt="icon">大腿動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB6" class="nav-text-link internal-nav"><img src="app/static/magicbookfire.png" class="nav-icon" alt="icon">__B6_TEXT__</a>
            <a href="#" data-target="NavToB7" class="nav-text-link internal-nav"><img src="app/static/35.png" class="nav-icon" alt="icon">董監動向</a><span class="nav-divider">|</span>
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

        const globalRadarBtn = parentDoc.getElementById('global-radar-btn');
        const globalRadarText = parentDoc.getElementById('global-radar-text');
        let isAllHidden = false; 

        if (globalRadarBtn) {
            globalRadarBtn.onclick = (e) => {
                e.preventDefault();
                const targetIds = ['close-b2-card', 'close-card', 'close-b4-card', 'close-b5-card'];
                isAllHidden = !isAllHidden;
                
                targetIds.forEach(id => {
                    const checkbox = parentDoc.getElementById(id);
                    if (checkbox) {
                        checkbox.checked = isAllHidden;
                    }
                });
                
                // 💡 修改：文字永遠維持「排行」，只透過顏色變化來暗示狀態
                if (isAllHidden) {
                    globalRadarText.style.color = '#64748B';  // 隱藏時變灰
                    globalRadarBtn.style.borderColor = '#64748B';
                } else {
                    globalRadarText.style.color = '#38BDF8';  // 開啟時恢復亮藍色
                    globalRadarBtn.style.borderColor = '#38BDF8';
                }
            };
        }

        setInterval(() => {
            const allBtns = Array.from(parentDoc.querySelectorAll('button'));
            allBtns.forEach(b => {
                if(b.textContent.includes('NavTo') || b.textContent.includes('登入')) { 
                    const wrapper = b.closest('div[data-testid="stElementContainer"]');
                    if (wrapper) wrapper.style.display = 'none';
                }
            });
        }, 100);
    }, 500);
    
    </script>
    """
    
    inject_js = inject_js.replace("__LOGIN_TEXT__", login_btn_text)
    inject_js = inject_js.replace("__B6_TEXT__", b6_text)

    components.html(inject_js, height=0, width=0)

# ==========================================
import streamlit as st

def render_proxy_buttons():
    def change_page(page_name):
        st.query_params["page"] = page_name 

    with st.container():
        st.button("NavToContact", on_click=change_page, args=("contact",))
        st.button("NavToNews", on_click=change_page, args=("news",))
        st.button("NavToPool", on_click=change_page, args=("pool",))
        st.button("NavToWatchlist", on_click=change_page, args=("watchlist",)) 
        st.button("NavToB1", on_click=change_page, args=("b1",))
        st.button("NavToB2", on_click=change_page, args=("b2",))
        st.button("NavToB3", on_click=change_page, args=("b3",))
        st.button("NavToB4", on_click=change_page, args=("b4",))
        st.button("NavToB5", on_click=change_page, args=("b5",))
        st.button("NavToB6", on_click=change_page, args=("b6",))
        st.button("NavToB7", on_click=change_page, args=("b7",))
        st.button("登入", on_click=change_page, args=("login",))
