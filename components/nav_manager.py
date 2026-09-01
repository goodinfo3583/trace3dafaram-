# components/nav_manager.py
import streamlit.components.v1 as components
import streamlit as st
import json

def inject_custom_header(is_logged_in=False):
    """注入客製化懸浮頂部導航與隱藏側邊欄邏輯 (遊戲化UI版 + 動態快捷鍵 + 設定功能)"""
    login_btn_text = "登出" if is_logged_in else "登入"
    
    # 預設快捷鍵字典
    default_hotkeys = {
        "f1": "NavToB1", "f2": "NavToB2", "f3": "NavToB3", 
        "f4": "NavToB4", "f5": "NavToB5", "f6": "NavToB6", "f7": "NavToB7",
        "alt+l": "NavToWatchlist", "escape": "登入"
    }
    user_hotkeys = st.session_state.get('custom_hotkeys', default_hotkeys)
    hotkeys_json = json.dumps(user_hotkeys)
    
    inject_js = """
    <script>
    const parentWin = window.parent;
    const parentDoc = parentWin.document;

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
        
        .system-menu { position: relative; padding: 6px 8px; cursor: pointer; background: transparent !important; display: flex; align-items: center; justify-content: center; }
        .system-icon { width: 22px; height: 22px; object-fit: contain; filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .system-menu:hover .system-icon { filter: drop-shadow(0px 0px 8px rgba(0, 210, 255, 0.9)); transform: scale(1.15); }
        
        @keyframes periodicGlow {
            0%, 82% { filter: brightness(1) drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); transform: scale(1); }
            88% { filter: brightness(1.7) drop-shadow(0 0 12px rgba(56, 189, 248, 1)); transform: scale(1.2); }
            94% { filter: brightness(1) drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); transform: scale(1); }
            100% { filter: brightness(1) drop-shadow(1px 1px 2px rgba(0,0,0,0.8)); }
        }
        
        #custom-sidebar-toggle .system-icon { animation: periodicGlow 5s infinite ease-in-out; }
        #custom-sidebar-toggle:hover .system-icon { animation-play-state: paused; filter: brightness(1.2) drop-shadow(0px 0px 8px rgba(0, 210, 255, 0.9)); transform: scale(1.15); }

        .system-dropdown { position: absolute; top: 100%; left: 10px; width: 300px; background-color: rgba(17, 22, 34, 0.95); border: 1px solid rgba(255,255,255,0.1); border-top: none; border-radius: 0 0 8px 8px; padding: 0; max-height: 0; opacity: 0; overflow: hidden; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0px 8px 20px rgba(0,0,0,0.8); z-index: 1000010; backdrop-filter: blur(10px); }
        .system-menu:hover .system-dropdown { max-height: 800px; opacity: 1; padding: 8px 0; }
        
        .dropdown-item { padding: 10px 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .dropdown-item:last-child { border-bottom: none; }
        
        .dropdown-title { display: flex; align-items: center; gap: 8px; color: #E2E8F0; font-size: 13px; font-weight: bold; margin-bottom: 4px; text-decoration: none; transition: color 0.2s; cursor: pointer; }
        .menu-icon { width: 18px; height: 18px; object-fit: contain; }
        .dropdown-text { font-size: 11px; color: #94A3B8; line-height: 1.5; margin: 0; padding-left: 26px; }
        
        .dropdown-item:hover { background-color: rgba(255,255,255,0.05); }
        .dropdown-item.actionable:hover .dropdown-title { color: #FFD700; }
        
        .vip-login-btn { color: #FFD700 !important; font-size: 14px; justify-content: center; margin-top: 2px; }
        .vip-login-btn:hover { text-shadow: 0 0 10px rgba(255, 215, 0, 0.8); }

        .locked-item { opacity: 0.5; filter: grayscale(50%); cursor: not-allowed; }
        .locked-item:hover { background-color: transparent; opacity: 0.8; filter: grayscale(0%); }

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
            .global-radar-toggle { display: flex; margin-right: 5px; } 
        }
        .stApp { margin-top: 50px !important; }
        
        /* 贊助彈窗樣式 */
        .donate-modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.7); z-index: 1000050; justify-content: center; align-items: center;
            backdrop-filter: blur(5px); pointer-events: auto; opacity: 0; transition: opacity 0.3s ease;
        }
        .donate-modal-overlay.show { display: flex; opacity: 1; }
        .donate-modal-content {
            background: rgba(17, 22, 34, 0.95); border: 1px solid rgba(255, 215, 0, 0.4); border-radius: 12px;
            padding: 30px; text-align: center; max-width: 380px; width: 90%;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8), 0 0 20px rgba(255,215,0,0.15);
            transform: translateY(20px); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .donate-modal-overlay.show .donate-modal-content { transform: translateY(0); }
        .donate-btn-close {
            background: rgba(255, 215, 0, 0.1); border: 1px solid #FFD700; color: #FFD700; 
            padding: 8px 24px; border-radius: 6px; font-size: 14px; font-weight: bold; cursor: pointer; transition: 0.3s;
        }
        .donate-btn-close:hover { background: rgba(255, 215, 0, 0.3); box-shadow: 0 0 10px rgba(255,215,0,0.4); }
    `;
    parentDoc.head.appendChild(style);

    const headerDiv = parentDoc.createElement('div');
    headerDiv.id = 'custom-sticky-header';
    
    headerDiv.innerHTML = `
        <div class="disclaimer-bar">
            <!-- ⚙️ 系統設定 -->
            <div class="system-menu">
                <div class="system-menu-title" title="系統與聲明">
                    <img src="app/static/icon-system.png" class="system-icon" alt="系統">
                </div>
                
                <div class="system-dropdown">
                    <div class="dropdown-item actionable" style="text-align: center;">
                        <a href="#" data-target="__LOGIN_TEXT__" class="dropdown-title internal-nav vip-login-btn">
                            <img src="app/static/icon-login.png" class="menu-icon" alt="login"> __LOGIN_TEXT__ <span style="color:#64748b; font-size:10px;">(Esc)</span>
                        </a>
                    </div>
                    
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToSettings" class="dropdown-title internal-nav">
                            <img src="app/static/icon-system.png" class="menu-icon" alt="settings"> 設置
                        </a>
                        <p class="dropdown-text">自訂介面底色風格與專屬鍵盤快捷鍵。</p>
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
            
            <!-- 🎒 工具箱 / 擴充功能 -->
            <div class="system-menu">
                <div class="system-menu-title" title="韭菜盒子">
                    <img src="app/static/icon-toolbag.png" class="system-icon" alt="工具箱">
                </div>
                
                <div class="system-dropdown">
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToWatchlist" class="dropdown-title internal-nav">
                            <img src="app/static/icon-watchlist.png" class="menu-icon" alt="create"> 建立名單 <span style="color:#64748b; font-size:10px;">(Alt+L)</span>
                        </a>
                        <p class="dropdown-text">自訂與管理您的專屬觀察清單。</p>
                    </div>

                <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToWeightBacktest" class="dropdown-title internal-nav">
                            <img src="app/static/icon-podiumaward.png" class="menu-icon" alt="weight"> 權重與回測
                        </a>
                        <p class="dropdown-text">自訂計分籌碼權重與未來勝率回測模擬。</p>
                    </div>

                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToB0" class="dropdown-title internal-nav">
                            <img src="app/static/icon-stats.png" class="menu-icon" alt="b0"> 量價模型
                        </a>
                        <p class="dropdown-text">透視全市場資金動能與主力控盤狀態。</p>
                    </div>

                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToBroker" class="dropdown-title internal-nav">
                            <img src="app/static/icon-building.png" class="menu-icon" alt="broker"> 券商分點
                        </a>
                        <p class="dropdown-text">追蹤特定券商分點進出動向。</p>
                    </div>
                    
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToNews" class="dropdown-title internal-nav">
                            <img src="app/static/icon-coffee-time.png" class="menu-icon" alt="news"> 市場消息
                        </a>
                        <p class="dropdown-text">掌握最新市場動態與總經快訊。</p>
                    </div>
                    
                    <div class="dropdown-item actionable">
                        <a href="#" data-target="NavToCourses" class="dropdown-title internal-nav">
                            <img src="app/static/icon-malware-shield.png" class="menu-icon" alt="courses"> 課程
                        </a>
                        <p class="dropdown-text">增加最大智識，提升能力不求人。</p>
                    </div>                           
                    
                    <div class="dropdown-item actionable">
                        <a href="https://www.facebook.com/DOUBLEE04/?locale=zh_TW" target="_blank" class="dropdown-title" style="text-decoration: none;">
                            <img src="app/static/icon-malware-shield.png" class="menu-icon" alt="fb-group"> 靠北投顧 3.0 
                        </a>
                        <p class="dropdown-text">分享分析師真實績效，避免受話術白繳學費。</p>
                    </div>
                    
                    <div class="dropdown-item locked-item">
                        <span class="dropdown-title">
                            <img src="app/static/icon-podiumaward.png" class="menu-icon" alt="lock"> 主力追蹤 (開發中)
                        </span>
                        <p class="dropdown-text">深度解析主力籌碼囤積路徑。</p>
                    </div>
                    
                    <div class="dropdown-item locked-item" style="border-bottom: none;">
                        <span class="dropdown-title">
                            <img src="app/static/icon-chessknightalt.png" class="menu-icon" alt="game"> 命運酒館 (開發中)
                        </span>
                        <p class="dropdown-text">休息一下別殺進殺出占個卜，更多互動功能。</p>
                    </div>

                </div>
            </div>
            
            <div id="custom-sidebar-toggle" class="system-menu" title="搜尋與側欄功能">
                <img src="app/static/icon-search.png" class="system-icon" alt="搜尋">
            </div>

            <div style="flex-grow: 1;"></div>
            
            <!-- 💰 贊助收銀箱 (開發中) -->
            <div id="donate-btn" class="global-radar-toggle" style="margin-right: 5px;" title="支持開發 (建置中)">
                <img src="app/static/icon-donatebox.png" alt="支持開發">
            </div>

            <!-- 📡 雷達總控 -->
            <div id="global-radar-btn" class="global-radar-toggle" title="開關排行卡片">
                <img src="app/static/icon-card.png" alt="雷達總控" id="global-radar-img">
            </div>

            <div class="disclaimer-item" id="mobile-nav-toggle" title="收起選單" style="cursor: pointer; padding-right: 5px;"><span id="nav-toggle-icon" style="font-size: 18px; color: #38BDF8;">📜</span></div>
        </div>
        
        <!-- 💡 核心導覽列 -->
        <div class="nav-btn-container" id="nav-btn-container">
            <a href="#" data-target="NavToPool" class="nav-text-link internal-nav"><img src="app/static/magicbookfire2.png" class="nav-icon" alt="icon">觀察名單</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB1" class="nav-text-link internal-nav"><img src="app/static/magicbookleaf.png" class="nav-icon" alt="icon">法人動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB2" class="nav-text-link internal-nav"><img src="app/static/magicbookwind.png" class="nav-icon" alt="icon">法人掃貨</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB3" class="nav-text-link internal-nav"><img src="app/static/magicbookwater.png" class="nav-icon" alt="icon">法人連買</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB4" class="nav-text-link internal-nav"><img src="app/static/magicbookground.png" class="nav-icon" alt="icon">資券動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB5" class="nav-text-link internal-nav"><img src="app/static/wirtleg.png" class="nav-icon" alt="icon">大腿動向</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB6" class="nav-text-link internal-nav"><img src="app/static/magicbookfire.png" class="nav-icon" alt="icon">鉅額交易</a><span class="nav-divider">|</span>
            <a href="#" data-target="NavToB7" class="nav-text-link internal-nav"><img src="app/static/magicbookboss.png" class="nav-icon" alt="icon">董監動向</a>
        </div>
        
        <!-- 💰 贊助彈窗 HTML -->
        <div id="donate-modal-container" class="donate-modal-overlay">
            <div class="donate-modal-content">
                <img src="app/static/icon-donatebox.png" style="width: 70px; height: 70px; object-fit: contain; margin-bottom: 10px; filter: drop-shadow(0 0 15px rgba(255,215,0,0.6));">
                <h3 style="color: #FFD700; margin: 0 0 15px 0; font-size: 22px; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.8);">「等等！等等！」</h3>
                
                <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 16px; margin-bottom: 20px; text-align: left;">
                    <p style="color: #E2E8F0; font-size: 16px; margin: 0 0 8px 0; line-height: 1.5;">「我還沒準備好收銀箱！」</p>
                    <p style="color: #E2E8F0; font-size: 16px; margin: 0; line-height: 1.5;">「你現在把錢塞給我，我可能會不知道放哪裡。」</p>
                </div>
                
                <p style="color: #94A3B8; font-size: 13px; margin-bottom: 24px;">（ 功能正在準備中。下次再來看看，謝謝！ ）</p>
                <button id="close-donate-modal" class="donate-btn-close">我知道了</button>
            </div>
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
                const targetBtn = btns.find(b => b.textContent.trim() === targetName || b.textContent.includes(targetName));
                if (targetBtn) {
                    targetBtn.click();
                }
            };
        });

        // 🔥 動態快捷鍵引擎
        const hotkeysMap = JSON.parse(`__HOTKEYS_JSON__`);

        if (parentWin.customHotkeyHandler) {
            parentDoc.removeEventListener('keydown', parentWin.customHotkeyHandler);
        }

        parentWin.customHotkeyHandler = function(e) {
            const activeTag = parentDoc.activeElement ? parentDoc.activeElement.tagName.toLowerCase() : '';
            if (activeTag === 'input' || activeTag === 'textarea') return;

            // 💡 防呆機制：如果設置視窗開著，封鎖一般導航跳轉！並攔截 F1~F12 避免誤觸刷新/說明
            const isSettingsOpen = parentDoc.querySelector('.settings-overlay');
            if (isSettingsOpen) {
                if (e.key.toLowerCase().startsWith('f')) {
                    e.preventDefault();
                }
                return;
            }

            let combo = [];
            if (e.ctrlKey) combo.push('ctrl');
            if (e.altKey) combo.push('alt');
            if (e.shiftKey) combo.push('shift');
            combo.push(e.key.toLowerCase());
            let keyStr = combo.join('+');

            if (hotkeysMap[keyStr]) {
                e.preventDefault(); 
                const targetName = hotkeysMap[keyStr];
                const btns = Array.from(parentDoc.querySelectorAll('button'));
                const targetBtn = btns.find(b => b.textContent.trim() === targetName);
                if (targetBtn) targetBtn.click();
            }
        };
        
        parentDoc.addEventListener('keydown', parentWin.customHotkeyHandler);

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

        // 💰 贊助箱彈窗邏輯
        const donateBtn = parentDoc.getElementById('donate-btn');
        const donateModal = parentDoc.getElementById('donate-modal-container');
        const closeDonateBtn = parentDoc.getElementById('close-donate-modal');

        if (donateBtn && donateModal && closeDonateBtn) {
            donateBtn.onclick = (e) => {
                e.preventDefault();
                donateModal.classList.add('show');
            };
            
            closeDonateBtn.onclick = (e) => {
                e.preventDefault();
                donateModal.classList.remove('show');
            };
            
            // 點擊背景黑色區域也可關閉
            donateModal.onclick = (e) => {
                if(e.target === donateModal) {
                    donateModal.classList.remove('show');
                }
            };
        }

        setInterval(() => {
            const allBtns = Array.from(parentDoc.querySelectorAll('button'));
            allBtns.forEach(b => {
                const text = b.textContent.trim();
                if(text.includes('NavTo') || text === '登入' || text === '登出') { 
                    const wrapper = b.closest('div[data-testid="stElementContainer"]');
                    if (wrapper) wrapper.style.display = 'none';
                }
            });
        }, 3600);
    }, 500);
    </script>
    """
    
    inject_js = inject_js.replace("__LOGIN_TEXT__", login_btn_text)
    inject_js = inject_js.replace("__HOTKEYS_JSON__", hotkeys_json)
    components.html(inject_js, height=0, width=0)

#所有的隱藏按鈕魔法斗篷
def render_proxy_buttons():
    def change_page(page_name):
        st.query_params["page"] = page_name 
        
    def toggle_course_npc():
        st.session_state['show_course_npc'] = not st.session_state.get('show_course_npc', False)
        
    def handle_logout():
        st.session_state.clear()
        st.query_params["page"] = "b1" # 登出後預設回首頁
        
    with st.container():
        # ==========================================
        # 🚀 CSS 隱形斗篷魔法 (終結 0.5 秒閃爍問題)
        # 只要放在這個 container 裡，並且排在 anchor 後面的元素，出生瞬間就會隱形！
        # ==========================================
        st.markdown("""
            <style>
            div[data-testid="stElementContainer"]:has(#hidden-nav-anchor) ~ div[data-testid="stElementContainer"] {
                display: none !important;
            }
            </style>
            <div id="hidden-nav-anchor"></div>
        """, unsafe_allow_html=True)
        
        # 下方的按鈕功能完全保留你的設定，但畫面再也不會閃爍了！
        st.button("登入", on_click=change_page, args=("login",))
        st.button("登出", on_click=handle_logout)
        st.button("NavToContact", on_click=change_page, args=("contact",))
        st.button("NavToCourses", on_click=toggle_course_npc)
        st.button("NavToNews", on_click=change_page, args=("news",))
        st.button("NavToPool", on_click=change_page, args=("pool",))
        st.button("NavToB0", on_click=change_page, args=("b0",))
        st.button("NavToB1", on_click=change_page, args=("b1",))
        st.button("NavToB2", on_click=change_page, args=("b2",))
        st.button("NavToB3", on_click=change_page, args=("b3",))
        st.button("NavToB4", on_click=change_page, args=("b4",))
        st.button("NavToB5", on_click=change_page, args=("b5",))
        st.button("NavToB6", on_click=change_page, args=("b6",))
        st.button("NavToB7", on_click=change_page, args=("b7",))
        st.button("NavToBroker", on_click=change_page, args=("broker",))
        st.button("NavToSettings", on_click=change_page, args=("setting",))
        st.button("NavToWatchlist", on_click=change_page, args=("watchlist",))
        st.button("NavToWeightBacktest", on_click=change_page, args=("weight_backtest",)) 
    

