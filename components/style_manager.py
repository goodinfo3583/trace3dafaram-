# components/style_manager.py
import streamlit as st
import pandas as pd
import base64
import os
import random
import streamlit.components.v1 as components

# ==========================================
# 💡 效能救星：全域快取 Base64 圖片編碼
# ==========================================
@st.cache_data(show_spinner=False)
def get_cached_base64_image(image_path):
    if not os.path.exists(image_path): return ""
    try:
        with open(image_path, "rb") as file:
            return f"data:image/{'gif' if image_path.lower().endswith('.gif') else 'png'};base64,{base64.b64encode(file.read()).decode()}"
    except Exception: return ""

def apply_global_theme(image_path="./image/派對盛宴邀請.png"):
    theme, opacity = st.session_state.get('theme', 'dark'), st.session_state.get('bg_opacity', 88) / 100.0
    theme_settings = {
        'pink': {'rgb': '139, 109, 98', 'img': './image/鐵風堡.png'},
        'green': {'rgb': '0, 54, 16', 'img': './image/翡翠林鎮.png'},
        'purple': {'rgb': '87, 99, 158', 'img': './image/月下綠洲城.png'},
        'brown': {'rgb': '161, 115, 0', 'img': './image/沙漠衛星都市.png'},
        'blue': {'rgb': '135, 206, 235', 'img': './image/漂浮之都藍晶港.png'},
        'dark': {'rgb': '15, 23, 42', 'img': image_path}
    }
    
    current = theme_settings.get(theme, theme_settings['dark'])
    base_color, block_bg, actual_image = f"rgba({current['rgb']}, {opacity})", f"rgba({current['rgb']}, {opacity * 0.7})", current['img'] if os.path.exists(current['img']) else image_path

    bg_b64 = get_cached_base64_image(actual_image)
    bg_image_css = f"background-image: linear-gradient({base_color}, {base_color}), url({bg_b64}); background-size: cover; background-position: center; background-attachment: fixed;" if bg_b64 else f"background-color: {base_color} !important;"

    st.markdown(f"""<style>
    #MainMenu, footer, header, div[data-testid="stToolbar"] {{ visibility: hidden; }}
    .block-container {{ padding-top: 0rem; }}
    .glass-panel, .glass-panel-b2, .glass-panel-b4, .glass-panel-b5, .npc-overlay, .settings-modal-active {{ resize: both !important; overflow: auto !important; }}
    div[data-testid="stElementContainer"]:has(#hidden-nav-anchor), div[data-testid="stElementContainer"]:has(#hidden-nav-anchor) ~ div[data-testid="stElementContainer"] {{ display: none !important; }}
    img[src*="icon-card"], img[alt*="icon-card"] {{ cursor: pointer !important; transition: all 0.2s ease !important; }}
    img[src*="icon-card"]:hover, img[alt*="icon-card"]:hover {{ transform: scale(1.08) !important; filter: drop-shadow(0 0 8px rgba(0, 210, 255, 0.6)) !important; }}
    img[src*="icon-card"]:active, img[alt*="icon-card"]:active {{ transform: scale(0.95) !important; }}
    .stApp {{ {bg_image_css} }}
    div[data-testid="stVerticalBlock"] > div[style*="border"] {{ background-color: {block_bg} !important; backdrop-filter: blur(4px); }}
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText {{ color: #E2E8F0 !important; }}
    [data-testid="stAlert"] {{ background-color: transparent !important; border: 1px solid #2D3748 !important; }}
    [data-testid="stSidebar"] {{ background-color: rgba(17, 22, 34, 0.95) !important; border-right: 1px solid #1E293B; }}
    .stTextInput>div>div>input {{ background-color: #1A202C !important; color: #FFFFFF !important; border: 1px solid #4A5568 !important; }}
    div[data-testid="stDataFrame"] {{ background-color: #111622 !important; border: 1px solid #1E293B !important; border-radius: 6px; }}
    .stButton > button, .stLinkButton > a {{ background-color: #1E293B !important; color: #94A3B8 !important; border: 1px solid #334155 !important; transition: all 0.2s ease-in-out; }}
    .stButton > button:hover, .stLinkButton > a:hover {{ border-color: #00D2FF !important; color: #00D2FF !important; box-shadow: 0 0 8px rgba(0, 210, 255, 0.2); }}
    </style>""", unsafe_allow_html=True)

    components.html("""<script>
    (function(){
        if(window.parent.window.customDragDelegated) return;
        window.parent.window.customDragDelegated = true;
        const doc = window.parent.document;
        
        doc.addEventListener('click', e => {
            let t = e.target;
            if((t.tagName==='IMG' && (t.src?.includes('icon-card') || t.alt?.includes('icon-card'))) || (t.closest('div[data-testid="stImage"]')?.querySelector('img')?.src?.includes('icon-card'))) {
                e.preventDefault(); e.stopPropagation();
                const ids = ['b2-card','card','b4-card','b5-card'], cbs = ids.map(id=>doc.getElementById(`close-${id}`)), mins = ids.map(id=>doc.getElementById(`min-${id}`));
                let open = false, min = false;
                for(let i=0; i<4; i++) { if(cbs[i] && mins[i]) { if(!cbs[i].checked && !mins[i].checked) open=true; if(!cbs[i].checked && mins[i].checked) min=true; } }
                let nMin = open, nClose = !open && min;
                mins.forEach(c => { if(c) c.checked = nMin; }); cbs.forEach(c => { if(c) c.checked = nClose; });
            }
        }, true);
        
        let d=false, el=null, sx, sy, ix, iy;
        const down = e => {
            let h = e.target.closest('.header-bar,.header-bar-b2,.header-bar-b4,.header-bar-b5,.npc-drag-handle,.settings-drag-handle');
            if(!h || e.target.closest('button,input,label,.action-btn,.action-btn-b2,.action-btn-b4,.action-btn-b5')) return;
            let c = h.closest('.glass-panel,.glass-panel-b2,.glass-panel-b4,.glass-panel-b5,.npc-wrapper,.settings-modal-active');
            if(!c) c = h.closest('div[data-testid="stVerticalBlock"].settings-modal-active');
            if(!c) return;
            d=true; el=c; let touch = e.touches ? e.touches[0] : e; sx=touch.clientX; sy=touch.clientY;
            let r = el.getBoundingClientRect(); el.style.transition='none'; el.style.left=r.left+'px'; el.style.top=r.top+'px'; el.style.right='auto'; el.style.bottom='auto'; el.style.transform='none'; el.style.margin='0'; ix=r.left; iy=r.top; h.style.cursor='grabbing';
        };
        const move = e => { if(!d || !el) return; e.preventDefault(); let t = e.touches ? e.touches[0] : e; el.style.left=(ix+(t.clientX-sx))+'px'; el.style.top=(iy+(t.clientY-sy))+'px'; };
        const up = () => { if(d && el){ el.style.transition=''; let h=el.querySelector('.header-bar,.header-bar-b2,.header-bar-b4,.header-bar-b5,.npc-drag-handle,.settings-drag-handle'); if(h) h.style.cursor='grab'; } d=false; el=null; };
        doc.addEventListener('mousedown', down); doc.addEventListener('touchstart', down, {passive:false});
        doc.addEventListener('mousemove', move, {passive:false}); doc.addEventListener('touchmove', move, {passive:false});
        doc.addEventListener('mouseup', up); doc.addEventListener('touchend', up);
    })();</script>""", height=0, width=0)


def render_fireflies():
    css, divs = "", ""
    for i in range(5):
        s, sx, sy, mx, my, d, dl, p = random.uniform(2,5), random.uniform(0,100), random.uniform(0,100), random.uniform(-20,20), random.uniform(-20,20), random.uniform(10,25), random.uniform(0,10), random.uniform(2,5)
        css += f".f-{i}{{position:absolute;width:{s}px;height:{s}px;left:{sx}vw;top:{sy}vh;background:#FFFFDF;border-radius:50%;box-shadow:0 0 {s*3}px {s}px rgba(255,215,0,0.6);animation:dr-{i} {d}s infinite ease-in-out {dl}s,fl-{i} {p}s infinite ease-in-out {dl}s;opacity:0;}} @keyframes dr-{i}{{0%,100%{{transform:translate(0px,0px);}}25%{{transform:translate({mx}vw,{my}vh);}}50%{{transform:translate({mx/2}vw,{my*1.5}vh);}}75%{{transform:translate({-mx}vw,{my/2}vh);}}}} @keyframes fl-{i}{{0%,100%{{opacity:0;}}50%{{opacity:{random.uniform(0.5,1.0)};}}}} "
        divs += f"<div class='f-{i}'></div>"
    st.markdown(f"<style>.ff-cnt{{position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:1000;overflow:hidden;}} {css}</style><div class='ff-cnt'>{divs}</div>", unsafe_allow_html=True)


def render_marquee():
    imgs, tags, css = ["沙漠之城.png", "法人意向.png", "月影綠洲.png", "組合化學晶礦.png", "鐵風堡b.png"], "", ""
    for i, img in enumerate(imgs):
        b64 = get_cached_base64_image(f"static/{img}")
        if b64: tags += f'<img class="sl s-{i}" src="{b64}">'; css += f".s-{i}{{animation-delay:{i*5}s;}}"
    st.markdown(f"""<style>.sl-cnt{{position:relative;width:800px;height:100px;margin:0 auto 10px;display:flex;justify-content:center;align-items:center;overflow:hidden;}} .sl{{position:absolute;height:100%;object-fit:contain;visibility:hidden;opacity:0;animation:cut {len(imgs)*5}s infinite;}} {css} @keyframes cut{{0%,{(1/len(imgs))*100-0.01:.2f}%{{visibility:visible;opacity:1;}} {(1/len(imgs))*100:.2f}%,100%{{visibility:hidden;opacity:0;}}}}</style><div class="sl-cnt">{tags}</div>""", unsafe_allow_html=True)

# ==========================================
# 🌟 共用卡片 CSS 模板產生器 (極限壓縮重複代碼)
# ==========================================
def get_card_css(id_suffix, top, left, border_color, border_radius, title_color, anim_name, z_index, bg_color):
    return f"""
    #close-{id_suffix}:checked ~ #{id_suffix}-card {{ display:none !important; }}
    #min-{id_suffix}:checked ~ #{id_suffix}-card .c-wrap {{ max-height:0; opacity:0; margin-top:0; }}
    #min-{id_suffix}:checked ~ #{id_suffix}-card {{ padding-bottom:8px; width:150px; height:auto; }}
    #min-{id_suffix}:checked ~ #{id_suffix}-card .min-i::after {{ content:'□'; font-size:14px; }}
    #min-{id_suffix}:not(:checked) ~ #{id_suffix}-card .min-i::after {{ content:'_'; font-size:14px; position:relative; top:-3px; }}
    #pause-{id_suffix}:checked ~ #{id_suffix}-card .c-item {{ animation-play-state:paused !important; }}
    #pause-{id_suffix}:checked ~ #{id_suffix}-card .ps-i::after {{ content:'▶'; font-size:11px; color:#FFD700; }}
    #pause-{id_suffix}:not(:checked) ~ #{id_suffix}-card .ps-i::after {{ content:'⏸'; font-size:11px; }}
    @keyframes sIn-{id_suffix} {{ from {{ transform:translateY(-50%); opacity:0; }} to {{ transform:translateY(0); opacity:1; }} }}
    .gp-{id_suffix} {{ position:fixed; top:{top}; left:{left}; width:15.5vw; min-width:220px; background:{bg_color}; backdrop-filter:blur(12px); border:1px solid {border_color}; border-radius:{border_radius}; padding:10px 12px; z-index:{z_index}; color:#E2E8F0; animation:sIn-{id_suffix} 0.8s cubic-bezier(0.25,0.8,0.25,1); transition:all 0.3s ease; box-sizing:border-box; }}
    @media(max-width:1200px) {{ .gp-{id_suffix} {{ position:relative; top:auto; left:auto; width:90%; max-width:350px; margin:10px auto; display:block; }} }}
    #{id_suffix}-card .h-bar {{ display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px; margin-bottom:8px; cursor:default; }}
    #{id_suffix}-card .h-title {{ font-size:13px; font-weight:bold; color:{title_color}; white-space:nowrap; }}
    #{id_suffix}-card .a-btns {{ display:flex; gap:8px; align-items:center; }}
    #{id_suffix}-card .a-btn {{ cursor:pointer; color:#94A3B8; font-weight:bold; transition:color 0.2s; user-select:none; display:flex; align-items:center; justify-content:center; }}
    #{id_suffix}-card .a-btn:hover {{ color:{title_color}; }}
    #{id_suffix}-card .p-title {{ margin:0 0 8px 0; font-size:12.5px; font-weight:bold; color:{title_color}; display:flex; justify-content:space-between; align-items:flex-end; }}
    #{id_suffix}-card .d-badge {{ font-size:10px; color:#94A3B8; font-weight:normal; }}
    #{id_suffix}-card .c-wrap {{ position:relative; height:285px; overflow:hidden; transition:all 0.3s ease; opacity:1; }}
    #{id_suffix}-card .c-item {{ position:absolute; top:0; left:0; width:100%; opacity:0; animation:fSw-{id_suffix} 20s infinite; }}
    #{id_suffix}-card .c-item:nth-child(1) {{ animation-delay:0s; }} #{id_suffix}-card .c-item:nth-child(2) {{ animation-delay:5s; }}
    #{id_suffix}-card .c-item:nth-child(3) {{ animation-delay:10s; }} #{id_suffix}-card .c-item:nth-child(4) {{ animation-delay:15s; }}
    @keyframes fSw-{id_suffix} {{ 0%,22%{{opacity:1;z-index:2;}} 25%,97%{{opacity:0;z-index:1;}} 100%{{opacity:1;z-index:2;}} }}
    """

def render_b2_top10_glass_card():
    if 'df_blk2_1' not in st.session_state: return
    try:
        def get_col(df): return next(((c, str(c)[:4]) for c in (df.columns if df is not None and not df.empty else []) if "成交比" in str(c) or "發行數" in str(c)), (None, "未知"))
        def get_t10(df, c): return df[(df['股票代號'].astype(str).str.strip().str.len() == 4) & (~df['股票代號'].astype(str).str.startswith('00'))].assign(**{c: pd.to_numeric(df[c].astype(str).str.replace(r'[,%]', '', regex=True), errors='coerce').fillna(0)}).sort_values(c, ascending=False).head(10) if df is not None and not df.empty and c else pd.DataFrame()
        
        c21, d21 = get_col(st.session_state.get('df_blk2_1')); c22, d22 = get_col(st.session_state.get('df_blk2_2')); c23, d23 = get_col(st.session_state.get('df_blk2_3')); c24, d24 = get_col(st.session_state.get('df_blk2_4'))
        d1, d2, d3, d4 = get_t10(st.session_state.get('df_blk2_1'), c21), get_t10(st.session_state.get('df_blk2_2'), c22), get_t10(st.session_state.get('df_blk2_3'), c23), get_t10(st.session_state.get('df_blk2_4'), c24)
        
        def m_html(df, c):
            if df.empty or not c: return "<p style='font-size:13.5px;text-align:center;color:#94A3B8;margin-top:40px;'>無資料</p>"
            return "<ul style='padding:0;margin:0;list-style:none;'>" + "".join([f"<li style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;font-size:13.5px;'><div style='display:flex;width:48%;overflow:hidden;'><b style='color:#FFF;width:22px;flex-shrink:0;'>{i+1}.</b><span style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{r['股票代號']}{r['股票名稱']}</span></div><div style='width:27%;color:#FFD700;font-size:11px;text-align:right;flex-shrink:0;'>{'🚨轉賣' if '轉賣反轉' in (cs:=str(r.get('今日短動態','')).split('(')[0]) else '🆕卡位' if '卡位' in cs else '🔥加碼' if '加碼' in cs else '🔥強攻' if '強延續' in cs else '🚨倒貨' if '倒貨' in cs else '📉調節' if '調節' in cs else '🔄持平' if '持平' in cs else '⚠️趨緩' if '趨緩' in cs else '⚪觀察' if not cs or cs=='nan' else cs[:3]}</div><div style='width:25%;color:#FF4C4C;font-weight:bold;text-align:right;flex-shrink:0;'>{float(r.get(c,0)):.1f}%</div></li>" for i, r in enumerate(df.to_dict('records'))]) + "</ul>"

        st.markdown(f"""
        <input type="checkbox" id="close-b2-card" style="display:none;"><input type="checkbox" id="min-b2-card" style="display:none;"><input type="checkbox" id="pause-b2-card" style="display:none;">
        <style>{get_card_css('b2', '85px', '84.5vw', 'rgba(255,76,76,0.35)', '0 12px 12px 0', '#FF7676', 'b2', '999998', 'rgba(30,20,20,0.88)')}</style>
        <div class="gp-b2" id="b2-card"><div class="h-bar"><span class="h-title"><img src="app/static/magicbookwind.png" style="width:18px;margin-right:6px;vertical-align:-3px;" onerror="this.style.display='none'">法人掃貨</span><div class="a-btns"><label for="pause-b2-card" class="a-btn ps-i"></label><label for="min-b2-card" class="a-btn min-i"></label><label for="close-b2-card" class="a-btn">✕</label></div></div><div class="c-wrap">
        <div class="c-item"><div class="p-title"><span>外資買超(成交%)</span><span class="d-badge">{d21}</span></div>{m_html(d1, c21)}</div><div class="c-item"><div class="p-title"><span>投信買超(成交%)</span><span class="d-badge">{d22}</span></div>{m_html(d2, c22)}</div><div class="c-item"><div class="p-title"><span>外資買超(發行%)</span><span class="d-badge">{d23}</span></div>{m_html(d3, c23)}</div><div class="c-item"><div class="p-title"><span>投信買超(發行%)</span><span class="d-badge">{d24}</span></div>{m_html(d4, c24)}</div></div></div>
        """, unsafe_allow_html=True)
    except: pass

def render_top10_glass_card():
    if 'b3_data' not in st.session_state: return
    try:
        def get_t10(df): return df[(df['股票代號'].astype(str).str.strip().str.len() == 4) & (~df['股票代號'].astype(str).str.startswith('00'))].head(10) if df is not None and not df.empty else pd.DataFrame()
        fd, it, fw, iw = get_t10(st.session_state['b3_data']['fo_day'][0]), get_t10(st.session_state['b3_data']['it_day'][0]), get_t10(st.session_state['b3_data']['fo_wk'][0]), get_t10(st.session_state['b3_data']['it_wk'][0])
        def fmt_d(d): return d[-4:] if (d and d != "00000000") else "未知"
        dfd, dit, dfw, diw = fmt_d(st.session_state['b3_data']['fo_day'][1]), fmt_d(st.session_state['b3_data']['it_day'][1]), fmt_d(st.session_state['b3_data']['fo_wk'][1]), fmt_d(st.session_state['b3_data']['it_wk'][1])
        
        def m_html(df, c, u): return "<p style='font-size:13.5px;text-align:center;color:#94A3B8;margin-top:40px;'>無資料</p>" if df.empty else "<ul style='padding:0;margin:0;list-style:none;'>" + "".join([f"<li style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:13.5px;'><div style='display:flex;width:55%;overflow:hidden;'><b style='color:#FFF;width:22px;flex-shrink:0;'>{i+1}.</b><span style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{r['股票代號']}{r['股票名稱']}</span></div><div style='width:45%;text-align:right;white-space:nowrap;'><span style='color:#FFD700;font-size:11px;margin-right:4px;'>{r.get('狀態動態','')}</span><span style='color:#00D2FF;font-weight:bold;'>{r.get(c,0)}{u}</span></div></li>" for i, r in enumerate(df.to_dict('records'))]) + "</ul>"

        st.markdown(f"""
        <input type="checkbox" id="close-b3-card" style="display:none;"><input type="checkbox" id="min-b3-card" style="display:none;"><input type="checkbox" id="pause-b3-card" style="display:none;">
        <style>{get_card_css('b3', '85px', '69vw', 'rgba(0,210,255,0.35)', '0', '#64748B', 'b3', '999999', 'rgba(15,23,42,0.88)')}</style>
        <div class="gp-b3" id="b3-card"><div class="h-bar"><span class="h-title"><img src="app/static/magicbookwater.png" style="width:18px;margin-right:6px;vertical-align:-3px;" onerror="this.style.display='none'">法人連買</span><div class="a-btns"><label for="pause-b3-card" class="a-btn ps-i"></label><label for="min-b3-card" class="a-btn min-i"></label><label for="close-b3-card" class="a-btn">✕</label></div></div><div class="c-wrap">
        <div class="c-item"><div class="p-title" style="color:#00D2FF;"><span>外資日連買</span><span class="d-badge">{dfd}</span></div>{m_html(fd, "最新連買天數", "天")}</div><div class="c-item"><div class="p-title" style="color:#00D2FF;"><span>投信日連買</span><span class="d-badge">{dit}</span></div>{m_html(it, "最新連買天數", "天")}</div><div class="c-item"><div class="p-title" style="color:#00D2FF;"><span>外資週連買</span><span class="d-badge">{dfw}</span></div>{m_html(fw, "最新連買週數", "週")}</div><div class="c-item"><div class="p-title" style="color:#00D2FF;"><span>投信週連買</span><span class="d-badge">{diw}</span></div>{m_html(iw, "最新連買週數", "週")}</div></div></div>
        """, unsafe_allow_html=True)
    except: pass

def render_b4_top10_glass_card():
    if 'b4_squeeze_radar' not in st.session_state or 'b4_risk_radar' not in st.session_state: return
    try:
        def get_t20(df): return df[(df['代號'].astype(str).str.strip().str.len() == 4) & (~df['代號'].astype(str).str.startswith('00'))].head(20) if df is not None and not df.empty else pd.DataFrame()
        sq, rk = get_t20(st.session_state['b4_squeeze_radar']['df']), get_t20(st.session_state['b4_risk_radar']['df'])
        dsq = st.session_state['b4_squeeze_radar']['date'][-4:] if len(st.session_state['b4_squeeze_radar']['date']) >= 4 else "未知"
        drk = st.session_state['b4_risk_radar']['date'][-4:] if len(st.session_state['b4_risk_radar']['date']) >= 4 else "未知"
        
        def m_html(df, st_idx, th): return "<p style='font-size:13.5px;text-align:center;color:#94A3B8;margin-top:40px;'>尚無目標</p>" if (s:=df.iloc[st_idx:st_idx+10]).empty else "<ul style='padding:0;margin:0;list-style:none;'>" + "".join([f"<li style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;font-size:13.5px;'><div style='display:flex;width:55%;overflow:hidden;'><b style='color:#FFF;width:22px;flex-shrink:0;'>{st_idx+i+1}.</b><span style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{r['代號']}{r['名稱']}</span></div><div style='width:25%;color:#FFD700;font-size:11px;text-align:left;flex-shrink:0;'>{(r.get('軋空評估' if th=='sq' else '套牢評估', ''))[:7]}</div><div style='width:20%;color:{'#FF4C4C' if th=='sq' else '#00e676'};font-weight:bold;text-align:right;flex-shrink:0;'>{float(r.get('漲跌幅',0)):.1f}%</div></li>" for i, r in enumerate(s.to_dict('records'))]) + "</ul>"

        st.markdown(f"""
        <input type="checkbox" id="close-b4-card" style="display:none;"><input type="checkbox" id="min-b4-card" style="display:none;"><input type="checkbox" id="pause-b4-card" style="display:none;">
        <style>{get_card_css('b4', '85px', '38vw', 'rgba(188,19,254,0.35)', '12px 0 0 12px', '#E2E8F0', 'b4', '999997', 'rgba(20,22,35,0.88)')}</style>
        <div class="gp-b4" id="b4-card"><div class="h-bar"><span class="h-title"><img src="app/static/magicbookground.png" style="width:18px;margin-right:6px;vertical-align:-3px;" onerror="this.style.display='none'">資券雷達</span><div class="a-btns"><label for="pause-b4-card" class="a-btn ps-i"></label><label for="min-b4-card" class="a-btn min-i"></label><label for="close-b4-card" class="a-btn">✕</label></div></div><div class="c-wrap">
        <div class="c-item"><div class="p-title" style="color:#bc13fe;"><span>軋空(1-10)</span><span class="d-badge">{dsq}</span></div>{m_html(sq, 0, 'sq')}</div><div class="c-item"><div class="p-title" style="color:#bc13fe;"><span>軋空(11-20)</span><span class="d-badge">{dsq}</span></div>{m_html(sq, 10, 'sq')}</div><div class="c-item"><div class="p-title" style="color:#00e676;"><span>套牢(1-10)</span><span class="d-badge">{drk}</span></div>{m_html(rk, 0, 'rk')}</div><div class="c-item"><div class="p-title" style="color:#00e676;"><span>套牢(11-20)</span><span class="d-badge">{drk}</span></div>{m_html(rk, 10, 'rk')}</div></div></div>
        """, unsafe_allow_html=True)
    except: pass

def render_b5_top10_glass_card():
    if 'b5_1000' not in st.session_state or 'b5_400' not in st.session_state: return
    try:
        d1, d4 = st.session_state['b5_1000'], st.session_state['b5_400']
        l1, l4 = next((c for c in d1.columns if c.startswith('▼') and '6周' not in c), None), next((c for c in d4.columns if c.startswith('▼') and '6周' not in c), None)
        if not l1 or not l4 or d1.empty or d4.empty: return
        
        s1 = d1[(d1['股票代號'].astype(str).str.strip().str.len() == 4) & (~d1['股票代號'].astype(str).str.startswith('00'))][['股票代號','股票名稱','週動態','▼6周增減',l1]].rename(columns={'▼6周增減':'6周(千)', l1:'最新(千)', '週動態':'狀態(千)'})
        s4 = d4[(d4['股票代號'].astype(str).str.strip().str.len() == 4) & (~d4['股票代號'].astype(str).str.startswith('00'))][['股票代號','週動態','▼6周增減',l4]].rename(columns={'▼6周增減':'6周(四)', l4:'最新(四)', '週動態':'狀態(四)'})
        sy = pd.merge(s1, s4, on='股票代號', how='inner')
        for c in ['6周(千)','最新(千)','6周(四)','最新(四)']: sy[f"{c}_v"] = pd.to_numeric(sy[c].astype(str).str.replace(r'[+%]', '', regex=True), errors='coerce').fillna(0)
        t6 = sy[(sy['6周(千)_v']>0)&(sy['6周(四)_v']>0)].sort_values('6周(千)_v', ascending=False).head(10)
        tl = sy[(sy['最新(千)_v']>0)&(sy['最新(四)_v']>0)].sort_values('最新(千)_v', ascending=False).head(10)
        
        def u_txt(s): s=str(s); return "🚀劇增" if "🚀" in s else "🔥大增" if "🔥" in s else "📈小增" if "📈" in s else "↗️微增" if "↗️" in s else "🔄持平" if "🔄" in s else "↘️微減" if "↘️" in s else "📉小減" if "📉" in s else "⚠️大減" if "⚠️" in s else "🚨劇減" if "🚨" in s else "⚪無字"
        def m_html(df, i6): return "<p style='font-size:13.5px;text-align:center;color:#94A3B8;margin-top:40px;'>尚無共振</p>" if df.empty else "<ul style='padding:0;margin:0;list-style:none;'>" + "".join([f"<li style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;font-size:13.5px;'><div style='display:flex;align-items:center;flex:1;overflow:hidden;margin-right:8px;'><b style='color:#FFF;width:22px;flex-shrink:0;'>{i+1}.</b><span style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{r['股票代號']}{r['股票名稱']}</span></div><div style='display:flex;justify-content:flex-end;align-items:center;color:#F59E0B;font-weight:{'bold' if i6 else 'normal'};font-size:{'13.5' if i6 else '11'}px;flex-shrink:0;'><span style='width:48px;text-align:right;'>{f'{r['6周(千)_v']:.1f}%' if i6 else u_txt(r.get('狀態(千)'))}</span><span style='color:#94A3B8;margin:0 3px;'>/</span><span style='width:48px;text-align:right;'>{f'{r['6周(四)_v']:.1f}%' if i6 else u_txt(r.get('狀態(四)'))}</span></div></li>" for i, r in enumerate(df.to_dict('records'))]) + "</ul>"

        st.markdown(f"""
        <input type="checkbox" id="close-b5-card" style="display:none;"><input type="checkbox" id="min-b5-card" style="display:none;"><input type="checkbox" id="pause-b5-card" style="display:none;">
        <style>{get_card_css('b5', '85px', '53.5vw', 'rgba(245,158,11,0.4)', '0', '#FCD34D', 'b5', '999996', 'rgba(30,25,10,0.88)')}</style>
        <div class="gp-b5" id="b5-card"><div class="h-bar"><span class="h-title"><img src="app/static/wirtleg.png" style="width:18px;margin-right:6px;vertical-align:-3px;" onerror="this.style.display='none'">大腿共振</span><div class="a-btns"><label for="pause-b5-card" class="a-btn ps-i"></label><label for="min-b5-card" class="a-btn min-i"></label><label for="close-b5-card" class="a-btn">✕</label></div></div><div class="c-wrap" style="animation:fSw-b5 10s infinite;"><style>#b5-card .c-item {{ animation:fSw-b5 10s infinite; }} #b5-card .c-item:nth-child(2) {{ animation-delay:5s; }} @keyframes fSw-b5 {{ 0%,45%{{opacity:1;z-index:2;}} 50%,95%{{opacity:0;z-index:1;}} 100%{{opacity:1;z-index:2;}} }}</style>
        <div class="c-item"><div class="p-title" style="color:#F59E0B;"><span>6周累積(1000/400)</span><span class="d-badge">{l1[1:]}</span></div>{m_html(t6, True)}</div><div class="c-item"><div class="p-title" style="color:#F59E0B;"><span>本週動能(1000/400)</span><span class="d-badge">{l1[1:]}</span></div>{m_html(tl, False)}</div></div></div>
        """, unsafe_allow_html=True)
    except: pass


# ==========================================
# 🎓 課程 NPC 懸浮對話框
# ==========================================
@st.fragment
def render_course_npc():
    if not st.session_state.get('show_course_npc', False): return
    vw = st.session_state.setdefault('course_view', 'list')

    css = """<style>.npc-overlay{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:90vw;max-width:800px;height:85vh;max-height:900px;background:rgba(15,23,42,0.98);border:2px solid #00D2FF;border-radius:12px;z-index:9999999;display:flex;flex-direction:column;padding:25px;box-shadow:0 8px 30px rgba(0,210,255,0.4);color:white;animation:fIn 0.3s cubic-bezier(0.175,0.885,0.32,1.1);box-sizing:border-box;} @keyframes fIn{from{transform:translate(-50%,-45%) scale(0.9);opacity:0;}to{transform:translate(-50%,-50%) scale(1);opacity:1;}} .top-actions{position:absolute;top:15px;right:20px;display:flex;gap:12px;z-index:10;} .action-btn{cursor:pointer;color:#94A3B8;font-size:20px;font-weight:bold;transition:0.2s;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5);width:32px;height:32px;border-radius:50%;border:1px solid rgba(255,255,255,0.1);} .action-btn:hover{background:rgba(0,210,255,0.3);color:#FFF;transform:scale(1.1);border-color:#00D2FF;} .action-btn.close:hover{background:rgba(255,76,76,0.8);border-color:#FF4C4C;} .detail-header,.npc-header{display:flex;align-items:flex-end;margin-bottom:15px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:15px;gap:20px;} .npc-big-image{width:140px;height:160px;background-size:contain;background-repeat:no-repeat;background-position:bottom;filter:drop-shadow(0 0 10px rgba(0,210,255,0.6));flex-shrink:0;} .dialogue-box{flex:1;background:rgba(0,210,255,0.08);border:1px solid rgba(0,210,255,0.3);border-radius:12px;padding:18px;position:relative;margin-bottom:10px;} .dialogue-box::before{content:'';position:absolute;left:-14px;bottom:30px;border-width:12px 14px 12px 0;border-style:solid;border-color:transparent rgba(0,210,255,0.3) transparent transparent;} .npc-name{color:#00D2FF;font-weight:bold;font-size:20px;margin-bottom:8px;} .npc-text{font-size:15px;color:#E2E8F0;line-height:1.6;} .table-container,.course-list{flex:1;overflow-y:auto;padding-right:10px;overflow-x:hidden;} .table-container::-webkit-scrollbar,.course-list::-webkit-scrollbar{width:6px;} .table-container::-webkit-scrollbar-thumb,.course-list::-webkit-scrollbar-thumb{background:rgba(0,210,255,0.4);border-radius:3px;} .pv-table{width:100%;border-collapse:collapse;font-size:14px;text-align:center;margin-bottom:15px;} .pv-table th{background:rgba(0,210,255,0.15);color:#00D2FF;padding:10px;border-bottom:2px solid #00D2FF;font-weight:bold;} .pv-table td{padding:10px;border-bottom:1px solid rgba(255,255,255,0.08);color:#CBD5E1;} .pv-table tr:hover td{background:rgba(255,255,255,0.05);color:#FFF;} .section-title{color:#00D2FF;font-size:16px;font-weight:bold;margin:15px 0 8px 0;border-left:4px solid #00D2FF;padding-left:8px;} .course-item{margin-bottom:15px;padding:15px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;transition:0.2s;cursor:pointer;} .course-item:hover{background:rgba(0,210,255,0.1);border-color:#00D2FF;transform:translateY(-2px);box-shadow:0 4px 15px rgba(0,210,255,0.2);} .course-title{color:#FFD700;font-weight:bold;font-size:16px;margin-bottom:8px;display:flex;align-items:center;} .course-icon{width:24px;height:24px;object-fit:contain;margin-right:8px;filter:drop-shadow(0 0 5px rgba(0,210,255,0.8));transition:0.3s;} .course-desc{font-size:13.5px;color:#CBD5E1;line-height:1.5;} .info-box{background:rgba(0,210,255,0.05);border:1px solid rgba(0,210,255,0.2);border-radius:8px;padding:12px;margin-bottom:15px;font-size:14px;color:#CBD5E1;line-height:1.6;} .trend-up{color:#FF4C4C;font-weight:bold;} .trend-down{color:#00E676;font-weight:bold;} .trend-flat{color:#FFD700;font-weight:bold;} @media(max-width:768px){.npc-overlay{width:95vw;height:90vh;padding:15px;} .detail-header{flex-direction:column;align-items:center;text-align:center;gap:10px;padding-bottom:10px;} .npc-big-image{width:90px;height:100px;} .dialogue-box{width:100%;padding:12px;} .dialogue-box::before{display:none;} .pv-table{font-size:12px;} .pv-table th,.pv-table td{padding:6px 4px;} .top-actions{top:8px;right:8px;gap:8px;} .action-btn{width:28px;height:28px;font-size:16px;} .npc-name{font-size:18px;} .npc-text{font-size:14px;} .section-title{font-size:15px;} .info-box{font-size:13px;padding:10px;}}</style>"""

    if vw == 'list':
        c_list = [("Lv 1. 宏觀經濟與景氣循環", "學習解讀 GDP、CPI、利率與匯率等基本指標，判斷大盤景氣階段。"),("Lv 2. 股市基本架構與名詞解析", "認識台股交易規則、各類委託單與基本盤面術語。"),("Lv 3. 財報與基本面入門", "學習閱讀三大財務報表，挑選具備長期競爭力的公司。"),("Lv 4. 量價關係與盤面解讀", "對照成交量與股價互動，判斷多空雙方的企圖心與買賣力道。"),("Lv 5. 技術分析與指標應用", "熟悉常用技術指標(MA, MACD, RSI, KDJ, BBW)，掌握趨勢轉折。"),("Lv 6. 籌碼面追蹤：法人與大戶結構", "認識外資、投信、自營商大戶持股，觀察資金集中或分散。"),("Lv 7. 券資關係與融資融券分析", "觀察融資餘額與券資比，評估市場潛在「軋空」或「多殺多」。"),("Lv 8. 產業趨勢與題材選股", "掌握主流產業輪動脈絡，佈局具備成長爆發力的賽道。"),("Lv 9. 資金控管與風險管理", "學習部位配置、分批進場與停損機制，避免重大虧損。"),("Lv 10. 交易心理學與個人策略總結", "克服貪婪與恐懼，建立專屬於自己的穩定獲利交易系統。")]
        h_items = "".join([f'<div class="course-item" id="btn-open-course-{i+1}"><div class="course-title"><img src="app/static/icon-course1.png" class="course-icon">{t}</div><div class="course-desc">{d}</div></div>' for i, (t, d) in enumerate(c_list)])
        st.markdown(f"""{css}<div class="npc-overlay"><div class="top-actions"><label class="action-btn close" id="btn-close-list" title="關閉">✕</label></div><div class="npc-header"><div class="npc-big-image" style="background-image: url('app/static/npcnatzu.png');"></div><div class="dialogue-box"><div class="npc-name">籌碼導師</div><div class="npc-text">「冒險者，選擇你想強化的能力吧！」</div></div></div><div class="course-list">{h_items}</div></div>""", unsafe_allow_html=True)
    else:
        d = {'detail_1': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「冒險者注意！經濟並不是永遠上升，而是不斷『🟢 復甦 → 擴張 → 過熱 → 放緩 → 衰退』的循環。現在的市場環境，究竟該積極、觀望，還是提高風險意識？讓我們從總體經濟數據中找答案吧！」', 'html': '<div class="section-title">📊 總體經濟關鍵指標解析</div><table class="pv-table"><thead><tr><th width="15%">指標</th><th width="35%">主要觀察什麼</th><th width="50%">上升通常代表對市場的影響</th></tr></thead><tbody><tr><td><b>GDP</b></td><td style="text-align:left;">經濟成長速度</td><td style="text-align:left;">經濟活動增加 🟢 景氣可能擴張</td></tr><tr><td><b>CPI</b></td><td style="text-align:left;">物價與通膨</td><td style="text-align:left;">生活成本上升 🟠 可能增加升息壓力</td></tr><tr><td><b>利率</b></td><td style="text-align:left;">資金成本</td><td style="text-align:left;">借錢成本提高 🔴 股市估值可能承壓</td></tr><tr><td><b>匯率</b></td><td style="text-align:left;">貨幣強弱</td><td style="text-align:left;">資金與出口環境變化 🟡 需搭配產業判讀</td></tr></tbody></table><div class="section-title">⚡ 景氣循環核心狀態對照</div><table class="pv-table"><thead><tr><th width="30%">景氣狀態</th><th width="40%">核心數據表現</th><th width="30%">市場含義</th></tr></thead><tbody><tr><td style="color:#4ADE80; font-weight:bold;">🟢 景氣復甦</td><td>GDP↑ / CPI→ / 利率低</td><td style="text-align:left;">景氣回升，初升段</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🟢 經濟擴張</td><td>GDP↑↑ / 企業活動↑</td><td style="text-align:left;">多頭主升段延續</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🟠 景氣過熱</td><td>GDP↑ / CPI↑↑ / 利率↑</td><td style="text-align:left;">通膨升溫，注意緊縮</td></tr><tr><td style="color:#F87171; font-weight:bold;">🔴 經濟放緩</td><td>GDP↓ / 消費↓</td><td style="text-align:left;">動能減弱，防守為主</td></tr><tr><td style="color:#EF4444; font-weight:bold;">🚨 經濟衰退</td><td>GDP↓↓ / 失業↑</td><td style="text-align:left;">熊市風險，資金避險</td></tr></tbody></table>'},
             'detail_2': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「冒險者，歡迎來到基礎訓練營！進入市場前，熟悉『盤面術語』與『市場角色』是最基本的要求。記住，台股是『紅漲綠跌』，搞懂這些名詞，未來的籌碼分析才會事半功倍喔！」', 'html': '<div class="section-title">📖 盤面速讀與狀態判讀</div><table class="pv-table"><thead><tr><th width="25%">狀態</th><th width="40%">一眼判讀</th><th width="35%">初步理解</th></tr></thead><tbody><tr><td style="color:#4ADE80; font-weight:bold;">🟢 買盤積極</td><td>股價↑ / 成交量↑</td><td style="text-align:left;">市場買方積極</td></tr><tr><td style="color:#F87171; font-weight:bold;">🔴 賣壓增加</td><td>股價↓ / 成交量↑</td><td style="text-align:left;">市場賣方積極</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🟡 市場觀望</td><td>股價→ / 成交量↓</td><td style="text-align:left;">市場交易意願降低</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🟠 波動加劇</td><td>高低價差↑ / 成交量↑</td><td style="text-align:left;">多空雙方競爭激烈</td></tr></tbody></table><div class="section-title">🏷️ 盤面常見名詞</div><table class="pv-table"><thead><tr><th width="20%">名詞</th><th width="40%">一眼理解</th><th width="40%">代表什麼</th></tr></thead><tbody><tr><td><b>開盤價</b></td><td style="text-align:left;">今天第一筆成交價</td><td style="text-align:left;">市場開盤的第一個價格</td></tr><tr><td><b>收盤價</b></td><td style="text-align:left;">最後成交價格</td><td style="text-align:left;">當日市場最後結果</td></tr><tr><td style="color:#00E676; font-weight:bold;">內盤</td><td style="text-align:left;">主動賣方成交</td><td style="text-align:left;">賣方較積極</td></tr><tr><td style="color:#FF4C4C; font-weight:bold;">外盤</td><td style="text-align:left;">主動買方成交</td><td style="text-align:left;">買方較積極</td></tr></tbody></table>'},
             'detail_3': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「冒險者，想找出真正能長期幫你賺錢的金雞母嗎？財報就是公司的體檢表！學會看懂基本面，才不會被虛假的包裝騙了喔！」', 'html': '<div class="section-title">📖 三大財務報表白話理解</div><table class="pv-table"><thead><tr><th width="25%">財務報表</th><th width="35%">白話理解</th><th width="40%">主要看什麼</th></tr></thead><tbody><tr><td><b>📈 綜合損益表</b></td><td style="text-align:left;">公司這段時間賺多少</td><td style="text-align:left;">營收、毛利、營業利益、淨利</td></tr><tr><td><b>🏦 資產負債表</b></td><td style="text-align:left;">公司現在有多少家底</td><td style="text-align:left;">資產、負債、股東權益</td></tr><tr><td><b>💵 現金流量表</b></td><td style="text-align:left;">錢實際怎麼流動</td><td style="text-align:left;">營業、投資、籌資現金流</td></tr></tbody></table><div class="section-title">🔍 基本面狀態一眼判讀</div><table class="pv-table"><thead><tr><th width="25%">狀態</th><th width="40%">一眼判讀</th><th width="35%">初步解讀</th></tr></thead><tbody><tr><td style="color:#4ADE80; font-weight:bold;">🟢 穩定成長</td><td>營收↑ / EPS↑ / 現金流↑</td><td style="text-align:left;">公司營運與獲利同步改善</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🟢 獲利改善</td><td>營收→ / 毛利↑ / EPS↑</td><td style="text-align:left;">公司效率或產品組合改善</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🟡 成長放緩</td><td>營收↑但增速↓ / EPS→</td><td style="text-align:left;">公司仍成長，但速度減慢</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🟠 虛胖成長</td><td>營收↑ / EPS↓ / 現金流↓</td><td style="text-align:left;">生意變大，但獲利品質可能下降</td></tr><tr><td style="color:#EF4444; font-weight:bold;">🚨 基本面惡化</td><td>營收↓ / EPS↓ / 現金流↓</td><td style="text-align:left;">核心營運同步轉弱</td></tr></tbody></table>'},
             'detail_4': {'npc': '羅德', 'img': 'npcroad.png', 'text': '「量價關係是市場最真實的足跡！仔細看這張表，當『量』與『價』出現背離時，就是趨勢即將反轉的危險警訊喔！」', 'html': '<table class="pv-table" style="margin-top:10px;"><thead><tr><th width="15%">趨勢</th><th width="20%">狀態</th><th width="65%">市場含義</th></tr></thead><tbody><tr><td class="trend-up">上漲</td><td>價升量縮</td><td style="text-align:left;">量價背離，下方有承接，短期回調，後續拉高</td></tr><tr><td class="trend-up">上漲</td><td>放量滯漲</td><td style="text-align:left;">趨勢高位，拋壓增大，即將見頂反轉，減倉清倉</td></tr><tr><td class="trend-up">上漲</td><td>縮量大漲</td><td style="text-align:left;">趨勢中途，縮量加速，鎖倉高控盤，延續上漲</td></tr><tr><td class="trend-up">上漲</td><td>放量大漲</td><td style="text-align:left;">價漲量增，量價齊升，多方吸籌，持續看漲</td></tr><tr><td class="trend-down">下跌</td><td>縮量小跌</td><td style="text-align:left;">主力洗盤，拋壓減弱，止跌位置，擇機進場</td></tr><tr><td class="trend-down">下跌</td><td>放量小跌</td><td style="text-align:left;">見底信號，買方增強，越跌越買，反轉新倉</td></tr><tr><td class="trend-down">下跌</td><td>縮量大跌</td><td style="text-align:left;">一致看空，無人接盤，下跌中繼，加速下跌</td></tr><tr><td class="trend-down">下跌</td><td>放量大跌</td><td style="text-align:left;">跟風砸盤，大量賣出，高位出貨，持續下跌</td></tr></tbody></table>'},
             'detail_5': {'npc': '羅德', 'img': 'npcroad.png', 'text': '「冒險者！技術指標可不是單純告訴你『買』或『賣』的魔法棒！它幫你從不同角度觀察市場的方向、動能與熱度。來看看這張儀表板吧！」', 'html': '<div class="info-box"><b>🧭 指標核心雷達：</b><br>📈 MA 看方向 ｜ ⚡ MACD 看動能 ｜ 🌡️ RSI 看熱度 ｜ 🎢 KDJ 看短線節奏 ｜ 📏 BBW 看波動</div><div class="section-title">📊 綜合總表：多指標狀態判讀</div><table class="pv-table"><thead><tr><th width="18%">市場狀態</th><th width="20%">MA 趨勢</th><th width="22%">MACD 動能</th><th width="20%">RSI／KDJ</th><th width="20%">BBW 波動</th></tr></thead><tbody><tr><td style="color:#60A5FA; font-weight:bold;">🔵 蓄力整理</td><td>均線糾結</td><td>接近 0 軸</td><td>RSI 40～60</td><td>↓↓ 極度收縮</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🚀 向上突破</td><td>突破均線</td><td>DIF > DEA</td><td>RSI > 50</td><td>↑ 開始擴張</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🟢 多頭趨勢</td><td>股價 > MA</td><td>0軸上/偏多</td><td>RSI 50～70</td><td>正常或擴張</td></tr><tr><td style="color:#FF7676; font-weight:bold;">🔥 強勢加速</td><td>多頭排列</td><td>柱體↑↑</td><td>RSI 70↑</td><td>↑↑ 快速擴張</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🟡 高檔過熱</td><td>維持多頭</td><td>動能縮小</td><td>RSI > 70</td><td>高檔擴張或收斂</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🟠 趨勢轉弱</td><td>跌破短均</td><td>死亡交叉</td><td>RSI 跌破50</td><td>可能收縮或轉向</td></tr><tr><td style="color:#F87171; font-weight:bold;">🔴 空頭趨勢</td><td>股價 < MA</td><td>DIF < DEA</td><td>RSI < 40</td><td>向下擴張</td></tr></tbody></table>'},
             'detail_6': {'npc': '羅德', 'img': 'npcroad.png', 'text': '「冒險者！市場上真正能呼風喚雨的，往往是那些掌握龐大資金的『法人』與『大戶』。透過這張籌碼結構表，我們可以看穿誰在買，進而判斷買盤的延續性喔！」', 'html': '<div class="section-title">📊 法人、大戶與分點怎麼看？</div><table class="pv-table"><thead><tr><th width="20%">觀察對象</th><th width="25%">主要看什麼</th><th width="25%">🟢 偏多／集中</th><th width="30%">🔴 偏空／分散</th></tr></thead><tbody><tr><td><b>🌍 外資</b></td><td style="text-align:left;">連續買賣超</td><td style="color:#4ADE80; font-weight:bold;">連續買超／持股↑</td><td style="color:#F87171; font-weight:bold;">連續賣超／持股↓</td></tr><tr><td><b>🏦 投信</b></td><td style="text-align:left;">連續買賣超</td><td style="color:#4ADE80; font-weight:bold;">連續買超</td><td style="color:#F87171; font-weight:bold;">連續賣超</td></tr><tr><td><b>⚙️ 自營商</b></td><td style="text-align:left;">買賣超方向</td><td style="color:#4ADE80; font-weight:bold;">持續買超</td><td style="color:#F87171; font-weight:bold;">持續賣超</td></tr><tr><td><b>🦈 400 張</b></td><td style="text-align:left;">中大型持有人</td><td style="color:#4ADE80; font-weight:bold;">人數↓／持股↑</td><td style="color:#F87171; font-weight:bold;">人數↑／持股↓</td></tr><tr><td><b>🐋 1000 張</b></td><td style="text-align:left;">大型持有人</td><td style="color:#4ADE80; font-weight:bold;">持股↑／集中↑</td><td style="color:#F87171; font-weight:bold;">持股↓／集中↓</td></tr><tr><td><b>🔍 單一分點</b></td><td style="text-align:left;">連續買超占比</td><td style="color:#4ADE80; font-weight:bold;">連續買超／集中↑</td><td style="color:#F87171; font-weight:bold;">連續賣超</td></tr></tbody></table>'},
             'detail_7': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「融資與融券的變化，往往暗示著主力與散戶的籌碼流動！觀察下方這張『券資關係與軋空狀態表』，小心別被『軋空』或『多殺多』掃出市場喔！」', 'html': '<table class="pv-table" style="margin-top:10px;"><thead><tr><th width="20%">趨勢</th><th width="35%">狀態</th><th width="45%">市場含義</th></tr></thead><tbody><tr><td style="color:#60A5FA; font-weight:bold;">🔵 可能軋空</td><td>股價↑ / 融券↑ / 借券↑ / 融資→↓</td><td style="text-align:left;">空方部位高，股價走強，後續可能回補</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🟢 正在軋空</td><td>股價↑↑ / 融券↓ / 借券↓ / 融資→↓</td><td style="text-align:left;">股價上漲同時空方下降，空方回補推升</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🟡 軋空下降</td><td>股價↑→ / 券降幅縮 / 資↑</td><td style="text-align:left;">空方回補減弱，多方接棒力道需觀察</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🟠 融資追價</td><td>股價↑ / 融資↑↑ / 券→↓</td><td style="text-align:left;">上漲伴隨融資增加，槓桿追價升溫</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🟡 多空混戰</td><td>股價→ / 融資↑ / 融券↑</td><td style="text-align:left;">多空雙方同步加碼，方向尚未明確</td></tr><tr><td style="color:#F87171; font-weight:bold;">🔴 空方增加</td><td>股價↓ / 融券↑ / 借券↑↑</td><td style="text-align:left;">股價弱且空單增，空方壓力升高</td></tr><tr><td style="color:#EF4444; font-weight:bold;">🚨 多殺多</td><td>股價↓↓ / 融資↓↓ / 券→↓</td><td style="text-align:left;">股價跌導致融資退場，出現槓桿賣壓</td></tr></tbody></table>'},
             'detail_8': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「冒險者，市場資金就像流水，哪裡有『題材』就往哪裡去！真正的強勢產業會引發『族群共振』。當上下游供應鏈同步轉強，才代表大部隊進場囉！」', 'html': '<div class="info-box"><b style="color: #FFD700;">🎯 重點不是追熱門，而是問自己：</b><br>市場炒什麼？是單檔漲還是族群共振？有無基本面支撐？是剛起漲還是過熱？</div><div class="section-title">🌊 資金輪動與題材階段解讀</div><table class="pv-table"><thead><tr><th width="20%">題材階段</th><th width="25%">族群共振</th><th width="55%">初步解讀</th></tr></thead><tbody><tr><td style="color:#60A5FA; font-weight:bold;">🌱 題材萌芽</td><td>單點啟動</td><td style="text-align:left;">少數公司受關注，尚未擴散。</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🚀 趨勢成長</td><td>局部共振</td><td style="text-align:left;">上下游陸續轉強，資金慢慢流入。</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🧩 族群共振</td><td>全產業擴散</td><td style="text-align:left;">多家公司同步走強，資金高度集中。</td></tr><tr><td style="color:#FF7676; font-weight:bold;">🔥 市場主流</td><td>強烈共振</td><td style="text-align:left;">討論度極高，主流確立，注意追高風險。</td></tr><tr><td style="color:#FB923C; font-weight:bold;">⚠️ 高檔過熱</td><td>共振分歧</td><td style="text-align:left;">強弱分明，注意資金輪動與獲利了結。</td></tr><tr><td style="color:#94A3B8; font-weight:bold;">🌙 題材退燒</td><td>共振消失</td><td style="text-align:left;">強勢股減少、資金撤離。</td></tr></tbody></table>'},
             'detail_9': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「冒險者！資金控管就是你的護城河。別總想著『重壓一把』，學會根據大盤環境調整資金比例，才能在股海裡安穩航行喔！」', 'html': '<div class="info-box"><b style="color: #FFD700;">🛡️ 大原則：</b> 🟢 大盤越明確 → 提高配置 ｜ 🟡 大盤越震盪 → 分批操作 ｜ 🔴 大盤越弱 → 提高現金</div><div class="section-title">📉 大盤環境與資金配置思維</div><table class="pv-table"><thead><tr><th width="24%">大盤狀態</th><th width="35%">資金配置思維</th><th width="41%">實戰操作方式</th></tr></thead><tbody><tr><td style="color:#4ADE80; font-weight:bold;">🚀 多頭趨勢</td><td style="text-align:left;">逐步提高參與度 (較高)</td><td style="text-align:left;">分批進場，不一次滿倉</td></tr><tr><td style="color:#60A5FA; font-weight:bold;">🟢 偏多震盪</td><td style="text-align:left;">保留部分現金 (中高)</td><td style="text-align:left;">分批建立部位，注意轉弱</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🟡 區間震盪</td><td style="text-align:left;">控制總曝險 (中低)</td><td style="text-align:left;">避免追高，分批試單</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🟠 偏空震盪</td><td style="text-align:left;">提高現金比例 (低)</td><td style="text-align:left;">嚴控風險，防個股受拖累</td></tr><tr><td style="color:#F87171; font-weight:bold;">🔴 空頭趨勢</td><td style="text-align:left;">優先控制風險 (觀望)</td><td style="text-align:left;">極低或不投入，避免攤平</td></tr><tr><td style="color:#bc13fe; font-weight:bold;">🚨 連續看錯</td><td style="text-align:left;">暫停或明顯降低部位</td><td style="text-align:left;">防情緒化交易，檢討策略</td></tr></tbody></table>'},
             'detail_10': {'npc': '蘿西', 'img': 'npcroxy.png', 'text': '「恭喜你來到最後一關！技術再好，心態崩了也是白搭。真正成熟的投資者知道『何時該收手』。讓我們建立屬於你的交易系統吧！」', 'html': '<div class="info-box" style="border-color:rgba(255,76,76,0.3); background:rgba(255,76,76,0.05);"><b style="color: #FF4C4C;">⚠️ 致命陷阱：輸在太想賺！</b><br>一直交易不代表積極，而是不願等待。過度追求易導致：追高➔ 放大部位➔ 不願停損➔ <b>大虧損！</b></div><div class="section-title">🧠 常見心理陷阱與對策</div><table class="pv-table"><thead><tr><th width="20%">心理陷阱</th><th width="35%">常見想法</th><th width="45%">更好的做法</th></tr></thead><tbody><tr><td style="color:#F87171; font-weight:bold;">😨 恐懼</td><td>「再跌一點就完了...」</td><td style="text-align:left;">嚴守停損，該砍就砍。</td></tr><tr><td style="color:#4ADE80; font-weight:bold;">🤑 貪婪</td><td>「應該還會漲，繼續凹！」</td><td style="text-align:left;">不憑感覺，嚴守停利點。</td></tr><tr><td style="color:#FACC15; font-weight:bold;">🏃 FOMO</td><td>「現在不買就錯過了！」</td><td style="text-align:left;">寧可錯過也不做錯，等待條件。</td></tr><tr><td style="color:#FB923C; font-weight:bold;">🎲 過度交易</td><td>「今天一定要做點什麼...」</td><td style="text-align:left;">無高勝率不交易，休息是策略。</td></tr><tr><td style="color:#bc13fe; font-weight:bold;">🔥 報復交易</td><td>「我要把虧的賺回來！」</td><td style="text-align:left;">關閉螢幕，暫停交易並檢討。</td></tr></tbody></table><div class="section-title">🏰 建立專屬交易系統</div><table class="pv-table"><thead><tr><th width="25%">系統環節</th><th width="75%">核心觀念</th></tr></thead><tbody><tr><td><b>🔎 選股條件</b></td><td style="text-align:left;">專注熟悉領域，不必什麼都做。</td></tr><tr><td><b>🎯 進場/部位</b></td><td style="text-align:left;">耐心等進打擊區，嚴控單筆承受風險。</td></tr><tr><td><b>🛑 停損停利</b></td><td style="text-align:left;">小錯可接受，大錯絕對避免；讓獲利延續。</td></tr><tr><td><b>🧘 等待機制</b></td><td style="text-align:left;">沒機會時不動作，這就是最強防守策略。</td></tr></tbody></table>'}
            }.get(vw, {})
        st.markdown(f"""{css}<div class="npc-overlay"><div class="top-actions"><label class="action-btn back" id="btn-back-detail" title="回到選單">←</label><label class="action-btn close" id="btn-close-detail" title="關閉">✕</label></div><div class="detail-header"><div class="npc-big-image" style="background-image: url('app/static/{d.get('img','')}');"></div><div class="dialogue-box"><div class="npc-name">籌碼導師 {d.get('npc','')}</div><div class="npc-text">{d.get('text','')}</div></div></div><div class="table-container">{d.get('html','')}</div></div>""", unsafe_allow_html=True)
    
    with st.empty().container():
        cols = st.columns(12)
        cols[0].button("CloseNPC", key="npc_c", on_click=lambda: st.session_state.update({'show_course_npc': False, 'course_view': 'list'}))
        for i in range(1, 11): cols[i].button(f"OpenCourse{i}", key=f"npc_c{i}", on_click=lambda v=f"detail_{i}": st.session_state.update({'course_view': v}))
        cols[11].button("BackToList", key="npc_b", on_click=lambda: st.session_state.update({'course_view': 'list'}))

    components.html("""<script>setInterval(()=>{const d=window.parent.document;if(!d)return;const bs=Array.from(d.querySelectorAll('button'));const map={ 'btn-close-list':'CloseNPC','btn-close-detail':'CloseNPC','btn-back-detail':'BackToList','btn-open-course-1':'OpenCourse1','btn-open-course-2':'OpenCourse2','btn-open-course-3':'OpenCourse3','btn-open-course-4':'OpenCourse4','btn-open-course-5':'OpenCourse5','btn-open-course-6':'OpenCourse6','btn-open-course-7':'OpenCourse7','btn-open-course-8':'OpenCourse8','btn-open-course-9':'OpenCourse9','btn-open-course-10':'OpenCourse10'};Object.entries(map).forEach(([id,txt])=>{const tb=bs.find(b=>b.textContent.includes(txt));if(tb){const c=tb.closest('div[data-testid="stElementContainer"]');if(c){c.style.position='fixed';c.style.top='-9999px';c.style.left='-9999px';}const el=d.getElementById(id);if(el){el.style.cursor='pointer';el.onclick=e=>{e.preventDefault();e.stopPropagation();tb.click();};}}});}, 15);</script>""", height=0, width=0)
