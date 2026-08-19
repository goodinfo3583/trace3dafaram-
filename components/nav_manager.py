# components/nav_manager.py
import streamlit.components.v1 as components

def inject_custom_header(is_logged_in=False):
    """注入客製化懸浮頂部導航與隱藏側邊欄邏輯 (遊戲化UI版)"""
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

        #custom-sticky-header { position: fixed; top: 0; left: 0; width: 100%; z-index: 1000005; background: transparent !important; pointer-events: none; }
        
        .disclaimer-bar, .nav-btn-container { pointer-events: auto; }
        .disclaimer-bar { display: flex; align-items: center; background: transparent !important; padding: 0px 15px; border: none !important; gap: 4px; }
        
        /* ⚙️ 頂部圖示共通樣式 */
        .system-menu { position: relative; padding: 6px 8px; cursor: pointer; background: transparent !important; display: flex; align-items: center; justify-content: center; }
        .system-icon { width: 22px; height: 22px; object-fit: contain; filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .system-menu:hover .system-icon { filter: drop-shadow(0px 0px 8px rgba(0, 210, 255, 0.9)); transform: scale(1.15); }
        
        /* 🌟 定時反光特效 */
        @keyframes periodicGlow {
            0%, 82% { filter: brightness(1) drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); transform: scale(1); }
            88% { filter: brightness(1.7) drop-shadow(0 0 12px rgba(56, 189, 248, 1)); transform: scale(1.2); }
            94% { filter: brightness(1) drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); transform: scale(1); }
            100% { filter: brightness(1) drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); }
        }
        
        #custom-sidebar-toggle .system-icon { animation: periodicGlow 5s infinite ease-in-out; }
        #custom-sidebar-toggle:hover .system-icon { animation-play-state: paused; filter: brightness(1.2) drop-shadow(0px 0px 8px rgba(0, 210, 255, 0.9)); transform: scale(1.15); }

        /* 🎁 贊助按鈕特別特效 (微微上下浮動) */
        @keyframes floatDonate {
            0%, 100% { transform: translateY(0); filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.4)); }
            50% { transform: translateY(-2px); filter: drop-shadow(0 0 10px rgba(255, 215, 0, 0.8)); }
        }
        #donate-btn .system-icon { animation: floatDonate 3s infinite ease-in-out; }
        #donate-btn:hover .system-icon { animation-play-state: paused; transform: scale(1.2); }

        /* 綠色補血特效動畫 */
        @keyframes healFlash {
            0% { opacity: 0; }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 0; transform: scale(1.5); }
        }

        /* 下拉選單 */
        .system-dropdown { position: absolute; top: 100%; left: 10px; width: 280px; background-color: rgba(17, 22, 34, 0.95); border: 1px solid rgba(255,255,255,0.1); border-top: none; border-radius: 0 0 8px 8px; padding: 0; max-height: 0; opacity: 0; overflow: hidden; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0px 8px 20px rgba(0,0,0,0.8); z-index: 1000010; backdrop-filter: blur(10px); }
        .system-menu:hover .system-dropdown { max-height: 600px; opacity: 1; padding: 8px 0; }
        
        .dropdown-item { padding: 10px 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .dropdown-item:last-child { border-bottom: none; }
        
        .dropdown-title { display: flex; align-items: center; gap: 8px; color: #E2E8F0; font-size: 13px; font-weight: bold; margin-bottom: 4px; text-decoration: none; transition: color 0.2s; cursor: pointer; }
        .menu-icon { width: 18px; height: 18px; object-fit: contain; }
        .dropdown-text { font-size: 11px; color: #94A3B8; line-height: 1.5; margin: 0; padding-left: 26px; }
        
        .dropdown-item:hover { background-color: rgba(255,255,255,0.05); }
        .dropdown-item.actionable:hover .dropdown-title { color: #FFD700; }
        
        .vip-login-btn { color: #FFD700 !important; font-size: 14px; justify-content: center; margin-top: 2px; }
        .vip-login-btn:hover { text-shadow: 0 0 10px rgba(255, 215, 0, 0.8); }
        
        /* 登出狀態按鈕樣式 (紅色警示) */
        .vip-logout-btn { color: #FF4C4C !important; font-size: 14px; justify-content: center; margin-top: 2px;}
        .vip-logout-btn:hover { text-shadow: 0 0 10px rgba(255, 76, 76, 0.8); }

        .locked-item { opacity: 0.5; filter: grayscale(50%); cursor: not-allowed; }
        .locked-item:hover { background-color: transparent; opacity: 0.8; filter: grayscale(0%); }

        /* 💎 導覽列 */
        .nav-btn-container { 
            display: flex; flex-wrap: wrap; justify-content: flex-end; align-items: center; 
            padding: 8px 15px; gap: 6px; 
            background: rgba(255, 255, 255, 0.06) !important; 
            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important; border-top: none !important; border-right: none !important;
            border-radius: 0 0 0 16px;
            box-shadow: -4px 4px 15px rgba(0,0,0,0.3);
            transition: all 0.3s ease-in-out; 
            width: fit-content; margin-left: auto;
        }
        
        .nav-text-link { 
            position: relative; overflow: hidden;
            text-decoration: none !important; color: #CBD5E1 !important; font-size: 15px; font-weight: 600; 
            padding: 6px 12px; border-radius: 6px; transition: all 0.3s ease-in-out; 
            text-shadow: 1px 1px 3px rgba(0,0,0,0.8); cursor: pointer; display: flex; align-items: center; 
            border: 1px solid transparent;
        }
        
        .nav-text-link::before {
            content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            transform: skewX(-20deg); transition: none;
        }
        
        .nav-text-link:hover { 
            color: #FFD700 !important; text-shadow: 0 0 10px rgba(255, 215, 0, 0.8); 
            background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 215, 0, 0.3);
            transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        
        .nav-text-link:hover::before { animation: sweepLight 0.6s ease-out; }
        @keyframes sweepLight { 0% { left: -100%; } 100% { left: 200%; } }
        
        .nav-divider { color: rgba(255, 255, 255, 0.15); font-size: 14px; user-select: none; margin: 0 2px; }

        .nav-icon { width: 20px; height: 20px; margin-right: 6px; object-fit: contain; transition: all 0.3s ease-in-out; }
        .nav-text-link:hover .nav-icon { filter: drop-shadow(0px 0px 6px rgba(255, 215, 0, 0.9)) brightness(1.2); }
        
        @keyframes floatAndPulse {
            0% { transform: translateY(0px) scale(1); filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.4)); }
            50% { transform: translateY(-3px) scale(1.05); filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.9)); }
            100% { transform: translateY(0px) scale(1); filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.4)); }
        }

        .global-radar-toggle {
            display: flex; align-items: center; justify-content: center; cursor: pointer; 
            margin-right: 15px; background: transparent; border: none; padding: 6px 10px;
        }
        .global-radar-toggle img { width: 22px; height: 22px; object-fit: contain; transition: all 0.4s ease; animation: floatAndPulse 3s infinite ease-in-out; }
        .global-radar-toggle:hover img { transform: scale(1.15); filter: drop-shadow(0 0 15px rgba(255, 215, 0, 1)); animation-play-state: paused; }
        .global-radar-toggle img.is-hidden { animation: none; opacity: 0.3; filter: grayscale(100%); transform: scale(0.9); }

        .force-hide { display: none !important; }

        @media (max-width: 768px) { 
            .nav-btn-container { 
                width: 96%; margin: 10px auto; 
                display: grid !important; grid-template-columns: repeat(2, 1fr); gap: 12px;
                padding: 20px 15px; background: rgba(15, 20, 30, 0.92) !important;
                border-radius: 12px; border: 1px solid rgba(255,255,255,0.1) !important;
            } 
            .nav-btn-container.force-hide { display: none !important; }
            .nav-divider { display: none; } 
            .nav-text-link { 
                flex-direction: column; justify-content: center; padding: 16px 10px; margin: 0;
                background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); 
                border-radius: 12px; font-size: 14px !important; text-align: center;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.2);
            } 
            .nav-text-link:active { transform: scale(0.95); background: rgba(255,215,0,0.1); }
            .nav-icon { margin: 0 0 8px 0; width: 28px; height: 28px; }
            .global-radar-toggle { display: flex; } 
        }
        .stApp { margin-top: 50px !important; }
    `;
    parentDoc.head.appendChild(style);

    const headerDiv = parentDoc.createElement('div');
    headerDiv.id = 'custom-sticky-header';
    
    // 動態生成類別與圖示
    const login_class = is_logged_in ? "vip-logout-btn" : "vip-login-btn";
    const login_icon = is_logged_in ? "app/static/icon-logout.png" : "app/static/icon-login.png";
    const login_action = is_logged_in ? "登出" : "登入";

    headerDiv.innerHTML = `
        <div class="disclaimer-bar">
            
            <!-- ⚙️ 系統設定 -->
            <div class="system-menu">
                <div class="system-menu-title" title="系統與聲明">
                    <img src="app/static/icon-system.png" class="system-icon" alt="系統">
                </div>
                
                <div class="system-dropdown">
                    <div class="dropdown-item actionable" style="text-align: center;">
                        <!-- 💡 登入/登出按鈕 -->
                        <a href="#" data-target="${login_action}" class="dropdown-title internal-nav ${login_class}">
                            <img src="${login_icon}" class="menu-icon" alt="login"> ${login_action}
                        </a>
                    </div>
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToContact" class="dropdown-title internal-nav">
                            <img src="app/static/icon-contact.png" class="menu-icon" alt="contact"> 聯絡我們
                        </a>
                        <p class="dropdown-text">有任何問題或合作提案，歡迎發送訊息與我們聯繫。</p>
                    </div>
                    <div class="dropdown-item">
                        <span class="dropdown-title"><img src="app/static/icon-agree.png" class="menu-icon" alt="disclaimer"> 平台聲明</span>
                        <p class="dropdown-text">本平台僅供教育研究與籌碼觀察，絕不構成實質投資建議。</p>
                    </div>
                    <div class="dropdown-item" style="border-bottom: none;">
                        <span class="dropdown-title"><img src="app/static/icon-agree.png" class="menu-icon" alt="privacy"> 隱私政策</span>
                        <p class="dropdown-text">依個資法蒐集識別資料僅供優化服務，絕不外流。</p>
                    </div>
                </div>
            </div>

            <!-- 🎒 工具箱 -->
            <div class="system-menu">
                <div class="system-menu-title" title="工具與擴充模組">
                    <img src="app/static/icon-toolbox.png" class="system-icon" alt="工具箱">
                </div>
                
                <div class="system-dropdown">
                    <!-- 🧪 精神回復藥水 -->
                    <div class="dropdown-item actionable" style="border-bottom: 2px solid rgba(74, 222, 128, 0.3);">
                        <a href="#" id="potion-trigger" class="dropdown-title internal-nav" style="color: #4ADE80;">
                            <img src="app/static/icon-potion.png" class="menu-icon" alt="potion"> 精神回復藥水
                        </a>
                        <p class="dropdown-text">清除思緒雜訊，重置儀表板並恢復冷靜視角。</p>
                    </div>

                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToNews" class="dropdown-title internal-nav">
                            <img src="app/static/magicbook2.png" class="menu-icon" alt="news"> 市場消息
                        </a>
                        <p class="dropdown-text">掌握最新市場動態與總經快訊。</p>
                    </div>
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToWatchlist" class="dropdown-title internal-nav">
                            <img src="app/static/icon-watchlist.png" class="menu-icon" alt="create"> 建立名單
                        </a>
                        <p class="dropdown-text">自訂與管理您的專屬觀察清單。</p>
                    </div>
                    
                    <div class="dropdown-item locked-item">
                        <span class="dropdown-title">
                            <img src="app/static/icon-podiumaward.png" class="menu-icon" alt="lock"> 權重與回測 (未解鎖)
                        </span>
                        <p class="dropdown-text">自訂計分籌碼權重與未來勝率回測模擬。</p>
                    </div>
                    <div class="dropdown-item locked-item" style="border-bottom: none;">
                        <span class="dropdown-title">
                            <img src="app/static/icon-chessknightalt.png" class="menu-icon" alt="game"> 命運酒館 (開發中)
                        </span>
                        <p class="dropdown-text">休息一下別殺進殺出，占個卜或追蹤主力。</p>
                    </div>
                </div>
            </div>

            <div id="custom-sidebar-toggle" class="system-menu" title="搜尋與側欄功能">
                <img src="app/static/icon-search.png" class="system-icon" alt="搜尋">
            </div>

            <!-- 🎁 贊助開發按鈕 -->
            <div id="donate-btn" class="system-menu" title="贊助開發">
                <a href="#" data-target="NavToDonate" class="internal-nav" style="display:flex;">
                    <img src="app/static/icon-donatebox.png" class="system-icon" alt="贊助">
                </a>
            </div>

            <div style="flex-grow: 1;"></div>
            
            <div id="global-radar-btn" class="global-radar-toggle" title="開關排行卡片">
                <img src="app/static/icon-card.png" alt="雷達總控" id="global-radar-img">
            </div>

            <div class="disclaimer-item" id="mobile-nav-toggle" title="收起選單" style="cursor: pointer; padding-right: 5px;"><span id="nav-toggle-icon" style="font-size: 18px; color: #38BDF8;">📜</span></div>
        </div>
        
        <div class="nav-btn-container" id="nav-btn-container">
            <a href="#" data-target="NavToPool" class="nav-text-link internal-nav"><img src="app/static/magicbookfire2.png" class="nav-icon" alt="icon">觀察名單</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB1" class="nav-text-link internal-nav"><img src="app/static/magicbookleaf.png" class="nav-icon" alt="icon">法人動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB2" class="nav-text-link internal-nav"><img src="app/static/magicbookwind.png" class="nav-icon" alt="icon">法人掃貨</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB3" class="nav-text-link internal-nav"><img src="app/static/magicbookwater.png" class="nav-icon" alt="icon">法人連買</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB4" class="nav-text-link internal-nav"><img src="app/static/magicbookground.png" class="nav-icon" alt="icon">資券動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB5" class="nav-text-link internal-nav"><img src="app/static/wirtleg.png" class="nav-icon" alt="icon">大腿動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB6" class="nav-text-link internal-nav"><img src="app/static/magicbookfire.png" class="nav-icon" alt="icon">__B6_TEXT__</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB7" class="nav-text-link internal-nav"><img src="app/static/35.png" class="nav-icon" alt="icon">董監動向</a>
        </div>
    `;
    parentDoc.body.insertBefore(headerDiv, parentDoc.body.firstChild);

    setTimeout(() => {
        // 綁定所有帶有 data-target 的內部導航
        const navLinks = parentDoc.querySelectorAll('.internal-nav');
        navLinks.forEach(link => {
            link.onclick = (e) => {
                e.preventDefault(); 
                const targetName = link.getAttribute('data-target');
                if (!targetName) return;

                // 找尋 Streamlit 產生的真實 button
                const btns = Array.from(parentDoc.querySelectorAll('button'));
                let targetBtn = btns.find(b => b.textContent.includes(targetName));
                
                // 如果是贊助，暫時導向 Contact
                if(targetName === 'NavToDonate' && !targetBtn) {
                    targetBtn = btns.find(b => b.textContent.includes('NavToContact'));
                }

                if (targetBtn) {
                    targetBtn.click();
                    
                    // 💡 如果是登出動作，我們幫它手動重整畫面，清除暫存感
                    if (targetName === "登出") {
                        setTimeout(() => {
                            window.location.reload();
                        }, 500);
                    }
                }
            };
        });

        // 🧪 藥水特效邏輯
        const potionTrigger = parentDoc.getElementById('potion-trigger');
        if (potionTrigger) {
            potionTrigger.onclick = (e) => {
                e.preventDefault();
                const overlay = parentDoc.createElement('div');
                overlay.style.position = 'fixed';
                overlay.style.top = '0'; overlay.style.left = '0';
                overlay.style.width = '100%'; overlay.style.height = '100%';
                overlay.style.background = 'radial-gradient(circle, rgba(74, 222, 128, 0.3) 0%, transparent 70%)';
                overlay.style.pointerEvents = 'none';
                overlay.style.zIndex = '9999999';
                overlay.style.animation = 'healFlash 0.8s ease-out';
                parentDoc.body.appendChild(overlay);
                
                setTimeout(() => { 
                    overlay.remove(); 
                    window.location.reload();
                }, 800);
            };
        }

        const menuToggle = parentDoc.getElementById('mobile-nav-toggle');
        const navContainer = parentDoc.getElementById('nav-btn-container');
        const iconSpan = parentDoc.getElementById('nav-toggle-icon');
        let isNavOpen = true; 
        
        if (window.innerWidth <= 768 && navContainer && iconSpan) {
            isNavOpen = false;
            navContainer.classList.add('force-hide');
            iconSpan.innerText = '📙';
            iconSpan.style.color = '#FFD700';
        }

        if (menuToggle && navContainer && iconSpan) {
            menuToggle.onclick = (e) => {
                e.preventDefault();
                isNavOpen = !isNavOpen; 
                
                if (isNavOpen) {
                    navContainer.classList.remove('force-hide'); 
                    menuToggle.title = "收起選單";
                    iconSpan.innerText = '📜';
                    iconSpan.style.color = '#38BDF8';
                } else {
                    navContainer.classList.add('force-hide'); 
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
        const globalRadarImg = parentDoc.getElementById('global-radar-img');
        let isAllHidden = false; 

        if (globalRadarBtn) {
            globalRadarBtn.onclick = (e) => {
                e.preventDefault();
                const targetIds = ['close-b2-card', 'close-card', 'close-b4-card', 'close-b5-card'];
                isAllHidden = !isAllHidden;
                
                targetIds.forEach(id => {
                    const checkbox = parentDoc.getElementById(id);
                    if (checkbox) { checkbox.checked = isAllHidden; }
                });
                
                if (isAllHidden) { globalRadarImg.classList.add('is-hidden'); } 
                else { globalRadarImg.classList.remove('is-hidden'); }
            };
        }

        // 隱藏原始的 Streamlit Buttons
        setInterval(() => {
            const allBtns = Array.from(parentDoc.querySelectorAll('button'));
            allBtns.forEach(b => {
                if(b.textContent.includes('NavTo') || b.textContent === '登入' || b.textContent === '登出') { 
                    const wrapper = b.closest('div[data-testid="stElementContainer"]');
                    if (wrapper) wrapper.style.display = 'none';
                }
            });
        }, 100);
    }, 500);
    </script>
    """
    
    inject_js = inject_js.replace("__B6_TEXT__", b6_text)
    components.html(inject_js, height=0, width=0)

# ==========================================
import streamlit as st
def render_proxy_buttons():
    def change_page(page_name):
        st.query_params["page"] = page_name 

    # 處理登出：清空狀態並導回首頁 (前端 JS 會自動重整畫面)
    def handle_logout():
        st.session_state.clear()
        st.query_params["page"] = "home"

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
        
        # 登入與登出 Proxy Buttons
        st.button("登入", on_click=change_page, args=("login",))
        st.button("登出", on_click=handle_logout)
