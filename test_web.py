import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import re

# ==========================================
# 1. 網頁基本設定 & 頂部蜂蜜幸運祝福
# ==========================================
st.set_page_config(page_title="台股籌碼五大核心矩陣儀表板", layout="wide")

st.markdown("""
<div style='text-align: center; background-color: #FFFDF0; padding: 20px; border-radius: 15px; border: 2px dashed #FFB700;'>
    <h1 style='color: #DDA400; margin-bottom: 5px;'>🐝 祝阿東順利畢業 - 每天都是美好的一天 🍯</h1>
    <p style='color: #665220; font-size: 16px; font-weight: bold;'>🌾 論文衝刺必勝 ｜ 香臘滿滿 ｜ 加速起漲雷達 ლ(∘◕‵ƹ′◕ლ)</p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("📊 系統全數領域展開：法人持股比 ｜ 短線法人買佔成交量 ｜ 法人買佔發行量比對 (本站進行數據分析僅供參考而非推薦個股與飆股另請愛惜荷包小心騙騙)")

DATA_DIR = "./Goodinfo_Rankings"

def extract_date_from_name(filepath):
    filename = os.path.basename(filepath)
    date_match = re.search(r'(\d+)', filename)
    return date_match.group(1) if date_match else "00000000"
# ==========================================
# 🌌 注入極致黑看盤軟體專屬風格樣式 (全站深色化 + 表格優化)
# ==========================================
st.markdown(
    """
    <style>
    /* 1. 變更全站主背景色 */
    .stApp {
        background-color: #0A0D14 !important;
    }
    
    /* 2. 強制所有標題與內文變成明亮的灰白色 (解決黑底黑字問題) */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText {
        color: #E2E8F0 !important;
    }
    
    /* 3. 頂部「阿東順利畢業」高雅減震配色 (與黑底和諧共存) */
    .stAlert p {
        color: #FFD700 !important; /* 點綴高貴金屬黃 */
    }
    .stAlert {
        background-color: #151B26 !important;
        border: 1px solid #2E3A4E !important;
    }
    
    /* 4. 變更側邊欄目錄背景色與邊框 */
    [data-testid="stSidebar"] {
        background-color: #111622 !important;
        border-right: 1px solid #1E293B;
    }
    
    /* 5. 優化輸入框、按鈕等元件 */
    .stTextInput>div>div>input {
        background-color: #1A202C !important;
        color: #FFFFFF !important;
        border: 1px solid #4A5568 !important;
    }
    
    /* 6. 表格與數據網格深色化修正 (防止白色突兀刺眼) */
    div[data-testid="stDataFrame"] {
        background-color: #111622 !important;
        border: 1px solid #1E293B !important;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ==========================================
# 🏆 預留置頂空間：頂級選股池容器
# ==========================================
top_pool_container = st.container()

# ==========================================
# 🧠 AI 量化評語生成引擎 (土洋對作/換手升級版)
# ==========================================
def generate_stock_commentary(row):
    """
    根據選股池的綜合數據，自動生成一段人話評語
    """
    score = row.get('總分', 0)
    warns = str(row.get('法人賣出警示', ''))
    b5_trend = str(row.get('大股東動向', ''))
    
    # 判斷是否帶有賣出警示與高分
    has_warning = "⚠️" in warns
    high_score = score >= 3
    
    # 1. 矛盾訊號判定：土洋對作 / 主力強勢吃籌碼
    if has_warning and high_score:
        return f"⚔️ 【土洋對作 / 激烈換手】系統偵測到法人分歧 ({warns})，但該股依然獲得 {score} 分的高評估！這代表『一方的倒貨正被另一方(或大戶)強勢吃下』。籌碼換手後若能維持強勢(如大漲/漲停)，代表承接方實力極強，可沿短均線偏多操作，但需嚴設停損。"
        
    # 2. 致命風險判定：真倒貨、無買盤
    if has_warning and not high_score:
        return f"🚨 【風險警示】目前法人主力正在進行倒貨調節 ({warns})，且無強大買盤承接，籌碼結構面臨鬆動。建議暫避風頭，嚴控資金水位。"
    
    if "大減" in b5_trend:
        return "⚠️ 【大戶撤退】400張以上大戶出現明顯減碼跡象，主力籌碼渙散，建議先行觀望，等待籌碼沉澱。"

    # 3. 綜合分數常規判定
    if score >= 6:
        base_comment = "🔥 【強勢噴發】籌碼面極度優異！內外資法人與大戶同步共振做多，具備強大的波段上攻潛力。"
        if "大增" in b5_trend:
            base_comment += "特別是大股東籌碼大幅集中，是不可多得的強勢防守標的，建議積極關注。"
        return base_comment
        
    elif score >= 3:
        return "📈 【偏多佈局】主力籌碼持續進駐，法人買盤給予一定支撐。具備穩健的波段潛力，可逢低尋找技術面切入點。"
        
    elif score >= 1:
        return "🔄 【中性觀望】籌碼表現較為平淡，雖有零星買盤但缺乏明確的連續性方向。建議多看少做，等待更強的表態訊號。"
        
    else:
        return "❄️ 【弱勢整理】籌碼處於流失或無主力認養狀態，資金效率低。若無特殊題材發酵，短期內建議暫不考量。"
# ==========================================
# 🔍 個股籌碼快搜 (全區塊聯動掃描版 - 終極全景版)
# ==========================================
st.write("---")
st.markdown("<div id='section-search'></div>", unsafe_allow_html=True)
st.subheader("🔍 個股籌碼快搜 (全方位診斷)")
# ==========================================
# 📈 專業 K 線圖與技術分析引擎 (yfinance 終極暗黑專業版)
# ==========================================
def render_technical_chart(stock_id, timeframe="日線"):
    import yfinance as yf
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    import streamlit as st

    try:
        ticker_tw = f"{stock_id}.TW"
        ticker_two = f"{stock_id}.TWO"
        
        df = yf.download(ticker_tw, period="5y", progress=False)
        if df is None or df.empty:
            df = yf.download(ticker_two, period="5y", progress=False)
            
        if df is None or df.empty:
            st.warning(f"⚠️ 無法從 Yahoo Finance 取得 {stock_id} 的即時報價，請確認代號是否正確。")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.loc[:, ~df.columns.duplicated()]

        if df.index.tz is not None:
            df.index = df.index.tz_convert('Asia/Taipei')
        else:
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Taipei')

        daily_df = df.copy()

        if timeframe == "週線":
            daily_df = daily_df.resample('W-FRI').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        elif timeframe == "月線":
            daily_df = daily_df.resample('ME').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()

        ma_windows = [5, 10, 20, 60, 120, 240]
        for ma in ma_windows:
            daily_df[f'{ma}MA'] = daily_df['Close'].rolling(window=ma).mean()

        def get_latest_price(col):
            valid_data = daily_df[col].dropna()
            if not valid_data.empty:
                val = valid_data.iloc[-1]
                if isinstance(val, pd.Series): val = val.iloc[0]
                return f"{float(val):.2f}"
            return "-"

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.7, 0.3])

        up_color = 'rgb(240, 90, 90)'     
        down_color = 'rgb(80, 200, 120)'  

        open_p, high_p = daily_df['Open'].squeeze(), daily_df['High'].squeeze()
        low_p, close_p = daily_df['Low'].squeeze(), daily_df['Close'].squeeze()
        vol = daily_df['Volume'].squeeze()

        fig.add_trace(go.Candlestick(
            x=daily_df.index, open=open_p, high=high_p, low=low_p, close=close_p, name='K線',
            increasing=dict(line=dict(color=up_color, width=1.5), fillcolor=up_color),
            decreasing=dict(line=dict(color=down_color, width=1.5), fillcolor=down_color),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br><br>開：%{open:.2f}<br>高：%{high:.2f}<br>低：%{low:.2f}<br>收：%{close:.2f}<extra></extra>"
        ), row=1, col=1)

        colors = ['#FFCC00', '#CC66FF', '#00CCFF', '#33FF33', '#FF3333', '#FFFF33']
        for idx, ma in enumerate(ma_windows):
            latest_val = get_latest_price(f'{ma}MA')
            fig.add_trace(go.Scatter(
                x=daily_df.index, y=daily_df[f'{ma}MA'].squeeze(), mode='lines', 
                name=f'{ma}MA ({latest_val})', line=dict(color=colors[idx], width=1.3),
                hovertemplate=f"<b>{ma}MA</b>： %{{y:.2f}}<extra></extra>"
            ), row=1, col=1)

        vol_colors = [up_color if c >= o else down_color for c, o in zip(close_p, open_p)]
        fig.add_trace(go.Bar(
            x=daily_df.index, y=vol, name='成交量', marker_color=vol_colors,
            hovertemplate="<b>成交量</b>： %{y}<extra></extra>"
        ), row=2, col=1)

        fig.update_layout(
            title=dict(
                text=f'📊 {stock_id} 最新 {timeframe} 與成交量 (資料來源: Yahoo Finance)',
                y=0.96, x=0.01, xanchor='left', yanchor='top',
                font=dict(color='#FFFFFF', size=16)
            ),
            yaxis_title='股價 (TWD)',
            xaxis_rangeslider_visible=False,
            height=700,
            template='plotly_dark',       
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',  
            margin=dict(l=10, r=10, t=100, b=10), # 增加頂部間距至 100px 完美避開重疊
            hovermode='x unified',
            hoverlabel=dict(bgcolor="#1A202C", font_size=14, font_family="Arial", font_color="#FFFFFF"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.01,
                font=dict(color='#E2E8F0')
            )
        )
        
        # 強制指定 X 軸的顯示與統一全數字日期格式（徹底拔除英文月份標籤）
        fig.update_xaxes(hoverformat="%Y-%m-%d", tickformat="%Y-%m-%d", row=1, col=1)
        fig.update_xaxes(hoverformat="%Y-%m-%d", tickformat="%Y-%m-%d", row=2, col=1)
        
        if not daily_df.empty:
            latest_date = daily_df.index[-1] 
            start_date = latest_date - pd.Timedelta(days=140) 
            zoom_range = [start_date.strftime('%Y-%m-%d'), latest_date.strftime('%Y-%m-%d')]
            fig.update_xaxes(range=zoom_range, row=1, col=1)
            fig.update_xaxes(range=zoom_range, row=2, col=1)
        
        if timeframe == "日線":
            fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], row=1, col=1)
        
        st.plotly_chart(fig, use_container_width=True, key=f"kline_{stock_id}_{timeframe}")
        
    except Exception as e:
        st.error(f"❌ 繪製 K 線圖時發生錯誤: {str(e)}")
#===================================
#以上技術線圖
#===================================       

# 🛠️ 定義強韌的搜尋函式
def robust_search_engine(df, query):
    if df is None or df.empty:
        return pd.DataFrame()
        
    df = df.loc[:, ~df.columns.duplicated()].copy()
    query = str(query).strip()
    mask = pd.Series(False, index=df.index)
    
    if '股票代號' in df.columns:
        df['股票代號'] = df['股票代號'].astype(str).str.strip()
        mask = mask | (df['股票代號'] == query)
        
    if '股票名稱' in df.columns:
        df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
        mask = mask | df['股票名稱'].str.contains(query, na=False, case=False)
        
    return df[mask]

# 🎯 建立通用掃描與顯示工具 (全面去藍底、保持排版左右高度對稱)
def scan_and_display(title, session_key, query):
    if session_key not in st.session_state:
        st.write(f"⚪ **{title}**：尚未載入資料表")
        return
        
    df = st.session_state[session_key]
    if df is None or df.empty:
        st.write(f"⚪ **{title}**：該榜單無任何資料")
        return
        
    res = robust_search_engine(df, query)
    
    # 只要查有資料，就印出標題與表格；若無資料，改用無背景純文字以求對齊
    if not res.empty:
        st.write(f"**{title}**")
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.write(f"⚪ **{title}**：未進榜")

#==========================================
# 🎯 搜尋輸入框
#==========================================
search_query = st.text_input("請輸入想觀測的股票代號或名稱 (例如: 3231 或 緯創，未顯示任何資料代表你的標的可能太弱了)：", key="global_search_final")

if search_query:
    st.write(f"### 🎯 綜合診斷標的：{search_query}")

    # ==========================================
    # 📈 K 線圖按鈕與週期切換 (防呆中文過濾版)
    # ==========================================
    st.write("---")
    if 'show_kline' not in st.session_state:
        st.session_state.show_kline = False

    button_label = "❌ 關閉技術 K 線圖" if st.session_state.show_kline else "📊 載入最新技術 K 線圖"
    if st.button(button_label, use_container_width=True):
        st.session_state.show_kline = not st.session_state.show_kline
        st.rerun()

    if st.session_state.show_kline:
        import re
        # 嚴格要求輸入內容必須含有數字代碼
        stock_id_match = re.search(r'\d+', search_query)
        
        if stock_id_match:
            pure_stock_id = stock_id_match.group(0)
            selected_tf = st.radio("⏳ 選擇 K 線週期：", ["日線", "週線", "月線"], horizontal=True)
            with st.spinner(f"正在從 Yahoo Finance 擷取 {pure_stock_id} 的 {selected_tf} 資料..."):
                render_technical_chart(pure_stock_id, selected_tf)
        else:
            st.warning("⚠️ 技術 K 線圖目前僅支援「數字代號」查詢。請在上方輸入框加入股票代號 (例如: 2330)，再點選此按鈕。")

    # ==========================================
    # 🤖 呼叫 AI 量化評語
    # ==========================================
    st.write("---")
    if 'top_pool_df' in st.session_state:
        # 從計分總表中搜尋這檔股票
        ai_target = robust_search_engine(st.session_state['top_pool_df'], search_query)
        if not ai_target.empty:
            st.markdown("#### 🤖 系統綜合診斷評語")
            # 將找到的該筆資料 (row) 丟進我們寫好的 AI 引擎
            commentary = generate_stock_commentary(ai_target.iloc[0])
            st.info(f"**{commentary}**")
        else:
            # 如果這檔股票沒有在計分表裡 (代表它可能連基本條件都沒達到)
            st.markdown("#### 🤖 系統綜合診斷評語")
            st.info("❄️ 【弱勢整理】該標的未能進入綜合評分池，籌碼處於流失或無主力認養狀態。若無特殊題材發酵，短期內建議暫不考量。")

 
    # ==========================================
    # 👑 區塊 1：中長線三大法人持股
    # ==========================================
    st.write("#### 👑 區塊 1：短中長線三大法人持股變化")
    if 'my_final_df' in st.session_state:
        q_blk1 = robust_search_engine(st.session_state['my_final_df'], search_query)
        if not q_blk1.empty:
            st.dataframe(q_blk1.drop(columns=["秘密3日斜率"], errors='ignore'), use_container_width=True, hide_index=True)
            chart_cols = [c for c in q_blk1.columns if "持股%" in c]
            if chart_cols:
                target_cols = chart_cols[:30] 
                raw_vals = pd.to_numeric(q_blk1.iloc[0][target_cols].values, errors='coerce')
                t_ser = pd.Series(
                    raw_vals, index=[c.split(' ')[0] for c in target_cols]
                ).replace(0, None).dropna().iloc[::-1]
                
                if not t_ser.empty:
                    st.write(f"📈 **持股 {len(t_ser)}日波段真實軌跡 ({q_blk1.iloc[0].get('股票名稱', '標的')})**")
                    st.line_chart(t_ser, height=240)
                    st.write("🚀 **籌碼斜率 (與最新持股相比淨增減)**")
                    
                    def get_slope_ui(label, n_days):
                        if len(target_cols) >= n_days:
                            v_new = pd.to_numeric(q_blk1.iloc[0][target_cols[0]], errors='coerce')
                            v_old = pd.to_numeric(q_blk1.iloc[0][target_cols[n_days-1]], errors='coerce')
                            if pd.notna(v_new) and pd.notna(v_old) and v_old != 0 and v_new != 0:
                                diff = round(v_new - v_old, 2)
                                color = "red" if diff > 0 else "green" if diff < 0 else "black"
                                return f"<div style='text-align:left; padding:5px;'><div style='font-size:14px; color:gray;'>{label}</div><div style='font-size:22px; font-weight:bold; color:{color};'>{diff:+.2f} %</div></div>"
                        return f"<div style='text-align:left; padding:5px;'><div style='font-size:14px; color:gray;'>{label}</div><div style='font-size:16px; font-weight:normal; margin-top:5px;'>無對應資料</div></div>"

                    col1, col2, col3, col4 = st.columns(4)
                    col1.markdown(get_slope_ui("2日斜率", 2), unsafe_allow_html=True)
                    col2.markdown(get_slope_ui("3日斜率", 3), unsafe_allow_html=True)
                    col3.markdown(get_slope_ui("5日斜率", 5), unsafe_allow_html=True)
                    col4.markdown(get_slope_ui("20日斜率", 20), unsafe_allow_html=True)
                else:
                    st.info("⚪ 該標的有效數據過少，無法繪製波段圖表。")
        else:
            st.info("⚪ 區塊 1：未進榜 ")
    else:
        st.error("⚠️ 尚未載入區塊 1 資料。請確認上方區塊 1 已執行。")

    # ==========================================
    # 📊 區塊 2：動能與外資診斷
    # ==========================================
    st.write("---")
    st.write("#### 📊 區塊 2：法人買超診斷")
    c1, c2 = st.columns(2)
    with c1: scan_and_display("🔹 區塊 2-1 -外資5日淨買佔標的成交量", 'df_blk2_1', search_query)
    with c2: scan_and_display("🔹 區塊 2-2 -投信5日淨買佔標的成交量", 'df_blk2_2', search_query)
    c3, c4 = st.columns(2)
    with c3: scan_and_display("🔹 區塊 2-3 -外資5日淨買佔公司發行量", 'df_blk2_3', search_query)
    with c4: scan_and_display("🔹 區塊 2-4 -投信5日淨買佔公司發行量", 'df_blk2_4', search_query)

    # ==========================================
    # 📊 區塊 3：特定籌碼或大戶診斷 (4 榜全景)
    # ==========================================
    st.write("---")
    st.write("#### 📊 區塊 3：法人連買排名診斷")
    if 'df_blk3_main' in st.session_state:
        df_b3 = st.session_state['df_blk3_main']
        res_b3 = robust_search_engine(df_b3, search_query)
        
        display_id = res_b3.iloc[0]['股票代號'] if not res_b3.empty else search_query
        display_name = res_b3.iloc[0]['股票名稱'] if not res_b3.empty else "-"
        
        base_types = ['🌐 外資日連買', '🌐 外資週連買', '🏦 投信日連買', '🏦 投信週連買']
        display_list = []
        for b_type in base_types:
            match = res_b3[res_b3['連買類型'] == b_type] if not res_b3.empty else pd.DataFrame()
            if not match.empty: display_list.append(match.iloc[0].to_dict())
            else: display_list.append({'連買類型': b_type, '股票代號': display_id, '股票名稱': display_name, '狀態動態': '⚪ 未進榜', '連買週期數': '-'})
                
        final_b3_display = pd.DataFrame(display_list)
        st.write("**連續買超日數與連續買超週數 **")
        st.dataframe(final_b3_display, use_container_width=True, hide_index=True)
    else:
        st.info("⚪ 區塊 3：尚未載入資料表 (請確認上半部區塊已執行)")


    # ==========================================
    # 📊 區塊 4：籌碼變動排名診斷 (三榜全景 + 強制去小數點)
    # ==========================================
    st.write("---")
    st.write("#### 📊 區塊 4：券資有利排名")
    
    def render_b4_panorama(view_title, keys_and_labels, query):
        display_list = []
        display_id = query
        display_name = "-"
        
        for label, key in keys_and_labels:
            if key in st.session_state:
                res = robust_search_engine(st.session_state[key], query)
                if not res.empty:
                    display_id = res.iloc[0].get('股票代號', query)
                    display_name = res.iloc[0].get('股票名稱', '-')
                    break
                    
        for label, key in keys_and_labels:
            if key in st.session_state:
                res = robust_search_engine(st.session_state[key], query)
                if not res.empty:
                    row_data = res.iloc[0].to_dict()
                    new_row = {'榜單類型': label}
                    new_row.update(row_data)
                    display_list.append(new_row)
                else:
                    display_list.append({'榜單類型': label, '股票代號': display_id, '股票名稱': display_name, '進榜狀態': '⚪ 未進榜'})
            else:
                display_list.append({'榜單類型': label, '股票代號': display_id, '股票名稱': display_name, '進榜狀態': '⚠️ 尚未載入'})
                
        df_panorama = pd.DataFrame(display_list).fillna('-')
        
        front_cols = ['榜單類型', '股票代號', '股票名稱', '進榜狀態']
        data_cols = [c for c in df_panorama.columns if c not in front_cols]
        final_cols = [c for c in front_cols if c in df_panorama.columns] + data_cols
        
        # 🔥 【神級修正】：強制將以 '.0' 結尾的數值轉為整數字串 (消除 190.0 的現象)
        for c in final_cols:
            df_panorama[c] = df_panorama[c].apply(lambda x: str(x)[:-2] if str(x).endswith('.0') else x)
        
        st.markdown(f"##### {view_title}")
        st.dataframe(df_panorama[final_cols], use_container_width=True, hide_index=True)

    render_b4_panorama("📊 5日幅度變動排名", [('📉 融資減少', 'df_margin_pct'), ('📉 借券減少', 'df_short_pct'), ('📈 融券增加', 'df_margin_plus_pct')], search_query)
    st.write("") 
    render_b4_panorama("📊 5日張數變動排名", [('📉 融資減少', 'df_margin_vol'), ('📉 借券減少', 'df_short_vol'), ('📈 融券增加', 'df_margin_plus_vol')], search_query)

    # ==========================================
    # 💎 區塊 5：神秘金字塔大戶動向
    # ==========================================
    st.write("---")
    st.write("#### 💰 區塊 5：大股東動向")
    scan_and_display("400張以上大戶動向", 'df_blk5', search_query)

# ==========================================
# 🧭 側邊欄導航 (無感互動+視覺特效版)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("📊 大盤總體經濟指標")

c_btn1, c_btn2 = st.sidebar.columns(2)
with c_btn1:
    st.link_button("📈 恐懼貪婪", "https://www.wantgoo.com/global/macroeconomics/fearandgreed", use_container_width=True)
with c_btn2:
    st.link_button("⚠️ VIX 指數", "https://www.wantgoo.com/global/vix", use_container_width=True)


# 1. 戰情室快速導航
st.sidebar.markdown("---")
st.sidebar.header("📍 戰情室快速導航")
st.sidebar.markdown("[🏆 數據分析觀察名單](#section-top-pool)")
st.sidebar.markdown("[🔍 個股籌碼快搜 (診斷區)](#section-search)")
st.sidebar.markdown("[👑 區塊1：三大法人持股比追蹤](#section-1)")
st.sidebar.markdown("[🎯 區塊2-1：外資5日淨買佔成交量](#section-2-1)")
st.sidebar.markdown("[🎯 區塊2-2：投信5日淨買佔成交量](#section-2-2)")
st.sidebar.markdown("[🎯 區塊2-3：外資5日淨買佔發行量](#section-2-3)")
st.sidebar.markdown("[🎯 區塊2-4：投信5日淨買佔發行量](#section-2-4)")
st.sidebar.markdown("[📅 區塊3：法人連續買超](#section-3)")
st.sidebar.markdown("[🔄 區塊4-1：融資減少動向](#section-4-1)")
st.sidebar.markdown("[🔄 區塊4-2：借券賣出減少動向](#section-4-2)")
st.sidebar.markdown("[🔄 區塊4-3：融券增加動向](#section-4-3)")
st.sidebar.markdown("[💰 區塊5：大股東動向](#section-5)")
# ==========================================
# 🏠 核心五大區塊
# ==========================================

# ==========================================
# 🏠 區塊1：中長線 三大法人 持股比例 追蹤 (量化動態升級+暗黑專業版)
# ==========================================
st.write("---")
st.markdown("<div id='section-1'></div>", unsafe_allow_html=True)
st.header("👑 區塊1：三大法人短中長線持股比追蹤")

import re
import os
import glob
import pandas as pd
from collections import defaultdict

# 1. 解析引擎 (嚴格依賴分隔線)
def parse_special_txt(file_path, date_label):
    parsed_data = []
    target_col = f"{date_label}持股%"
    current_section = None
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line_str = line.strip()
                
                # 🛑 【絕對斷路器】：只要遇到分隔線，立刻清空狀態
                if line_str.startswith("---") or line_str.startswith("==="):
                    current_section = None
                    continue
                
                # 💡 【區塊開關】：讀到對應標題才開啟
                if "三大法人持股變化排名" in line_str or ("排名" in line_str and "日)" in line_str):
                    if "120日" in line_str: current_section = "120日"
                    elif "20日" in line_str: current_section = "20日"
                    elif "5日" in line_str: current_section = "5日"
                    elif "60日" in line_str: current_section = "60日"
                    continue
                
                # 抓取資料
                parts = line_str.split('\t')
                if current_section and len(parts) >= 5 and parts[0].isdigit():
                    try: holding_pct = float(parts[-2])
                    except ValueError: continue
                    
                    stock_str = parts[1].strip()  
                    m = re.match(r'^(\d+)(.*)', stock_str)
                    stock_id = m.group(1) if m else stock_str
                    stock_name = m.group(2).strip() if m else stock_str
                    
                    parsed_data.append({
                        '股票代號': stock_id,
                        '股票名稱': stock_name,
                        target_col: holding_pct,
                        '上榜區塊': current_section
                    })
    except Exception:
        pass
    return pd.DataFrame(parsed_data)

# 聚合相同標的的不同榜單標籤
def agg_sections_func(x):
    valid_x = set([s for s in x if pd.notna(s) and s != ""])
    order = ['5日', '20日', '60日', '120日']
    return ",".join([s for s in order if s in valid_x])

# ==========================================
# 🔄 多日歷史資料合併與邏輯運算
# ==========================================
txt_pattern = os.path.join(DATA_DIR, "*持股排名變化*.txt")
all_txt_files = glob.glob(txt_pattern)

date_files = defaultdict(list)
for f in all_txt_files:
    date_label = os.path.basename(f)[:8]
    if date_label.isdigit():
        date_files[date_label].append(f)

sorted_dates = sorted(date_files.keys(), reverse=True)

if sorted_dates:
    final_df = None
    
    for i, date_label in enumerate(sorted_dates[:30]):
        is_latest = (i == 0)
        day_dfs = []
        
        for file_path in date_files[date_label]:
            df_part = parse_special_txt(file_path, date_label)
            if not df_part.empty:
                day_dfs.append(df_part)
                
        if not day_dfs: continue
            
        df_day_raw = pd.concat(day_dfs, ignore_index=True)
        target_col = f"{date_label}持股%"
        
        # 🔥 【邏輯重構】：歷史每一天的上榜榜單全部予以保留，以便比對「洗盤回歸」與「衝進榜單」
        df_day = df_day_raw.groupby(['股票代號', '股票名稱']).agg({
            target_col: 'max',  
            '上榜區塊': agg_sections_func
        }).reset_index()
        
        # 將上榜區塊重新命名以區分日期
        df_day = df_day.rename(columns={'上榜區塊': f"{date_label}_區塊"})
            
        if final_df is None: 
            final_df = df_day
        else: 
            final_df = pd.merge(final_df, df_day, on=['股票代號', '股票名稱'], how='outer')
            
    if final_df is not None and not final_df.empty:
        date_cols = sorted([c for c in final_df.columns if '持股%' in c], reverse=True)
        for c in date_cols:
            final_df[c] = pd.to_numeric(final_df[c], errors='coerce').fillna(0)
            
        # 今日上榜欄位標籤化
        def generate_tags(sections):
            if pd.isna(sections) or not sections: return ""
            sec_list = str(sections).split(',')
            tags = []
            if '5日' in sec_list: tags.append('🔴5日')
            if '20日' in sec_list: tags.append('🟡20日')
            if '60日' in sec_list: tags.append('🟢60日')
            if '120日' in sec_list: tags.append('🔵120日')
            return " ".join(tags)
            
        latest_sect_col = f"{sorted_dates[0]}_區塊"
        if latest_sect_col not in final_df.columns:
            final_df[latest_sect_col] = ""
            
        final_df['今日上榜'] = final_df[latest_sect_col].apply(generate_tags)
        final_df['上榜數量'] = final_df['今日上榜'].apply(lambda x: str(x).count('日'))
            
        # 🧠 量化動態判定邏輯核心 (洗盤回歸 與 衝進新榜單 整合版)
        def evaluate_trend(row):
            if len(date_cols) < 2: return "⚪ 資料不足"
            
            # 讀取今日與昨日的上榜區塊明細
            today_sec_str = str(row.get(f"{sorted_dates[0]}_區塊", ""))
            yesterday_sec_str = str(row.get(f"{sorted_dates[1]}_區塊", ""))
            
            today_list = [s for s in today_sec_str.split(',') if s]
            yesterday_list = [s for s in yesterday_sec_str.split(',') if s]
            
            v0, v1 = row[date_cols[0]], row[date_cols[1]]
            
            # 1. 🔍 【判定：洗盤回歸】 -> 今日重新上榜，但昨日完全不見，且更早之前曾經在榜內
            if v0 > 0 and v1 == 0:
                has_past_record = False
                for c in date_cols[2:]:
                    if row[c] > 0:
                        has_past_record = True
                        break
                if has_past_record:
                    return "🔄 洗盤回歸"
            
            # 2. 🚀 【判定：衝進新榜單】 -> 原本已有1~3個榜單，今日數量增加且有新成員
            if 1 <= len(yesterday_list) <= 3 and len(today_list) > len(yesterday_list):
                new_entries = [item for item in today_list if item not in yesterday_list]
                if new_entries:
                    mapped_labels = []
                    for item in new_entries:
                        if '5日' in item: mapped_labels.append('🔴5日')
                        elif '20日' in item: mapped_labels.append('🟡20日')
                        elif '60日' in item: mapped_labels.append('🟢60日')
                        elif '120日' in item: mapped_labels.append('🔵120日')
                    if mapped_labels:
                        return f"🚀 衝進{'、'.join(mapped_labels)}榜單"
            
            # 3. 常規趨勢判定
            diff1 = v0 - v1  
            if diff1 > 0:
                if len(date_cols) >= 3:
                    v2 = row[date_cols[2]]
                    if v1 != 0 and v2 != 0:
                        diff2 = v1 - v2
                        if diff2 > 0 and diff1 < diff2: return "⚠️ 趨緩"
                return "📈 上升"
            elif diff1 < 0: 
                return "📉 下降"
            else: 
                return "🔄 持平"
                
        final_df['最新動態'] = final_df.apply(evaluate_trend, axis=1)
        
        if date_cols:
            final_df = final_df.sort_values(by=['上榜數量', date_cols[0]], ascending=[False, False])
            
        color_ref = final_df.set_index('股票代號')['上榜數量'].to_dict()
        cols = ['股票代號', '股票名稱', '今日上榜', '最新動態'] + date_cols
        final_df = final_df[cols]
        
        # ==========================================
        # 🔧 UI 顯示與底色渲染 (移除過濾拉條，預設全開)
        # ==========================================
        show_etf = True
        show_bond = True
        
        is_bond = final_df['股票代號'].str.endswith('B')
        is_etf = (final_df['股票代號'].str.len() >= 5) & (~is_bond)
        is_stock = final_df['股票代號'].str.len() == 4
        
        mask = is_stock
        if show_etf: mask |= is_etf
        if show_bond: mask |= is_bond
            
        filtered_df = final_df[mask].copy()
        
        for c in date_cols:
            filtered_df[c] = filtered_df[c].apply(lambda x: f"{x:.2f}" if x != 0 else "-")
        filtered_df.index = range(1, len(filtered_df) + 1)
        
        # 🎨 暗黑專業版高亮色系設定 (調高透明度以適配黑底，不破壞原設計)
        def highlight_row(row):
            cnt = color_ref.get(row['股票代號'], 0)
            if cnt == 4: bg = 'background-color: rgba(240, 90, 90, 0.25)'     
            elif cnt == 3: bg = 'background-color: rgba(255, 165, 0, 0.25)'    
            elif cnt == 2: bg = 'background-color: rgba(80, 200, 120, 0.25)'    
            elif cnt == 1: bg = 'background-color: rgba(0, 127, 255, 0.25)'    
            else: bg = ''                                                   
            return [bg] * len(row)

        styled_df = filtered_df.style.apply(highlight_row, axis=1)
        
        st.info("**今日上榜說明：** 5/20/60/120日，代表法人持股變化數據分析後於5/20/60/120日前段班，多榜單共振籌碼集中度高，長線具備底氣。")
        st.success(f"已成功串聯 {len(date_cols)} 個交易日的持股數據 (今日上榜共振數量排序優先)")
        st.session_state['my_final_df'] = final_df
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("⚠️ 讀取到的檔案皆無效或無資料，請檢查 TXT 內容。")
else:
    st.write("⚠️ 目前暫無持股比例追蹤數據。")


# ==========================================
# 🎯 區塊2-1：外資 5 日買超 佔成交量比 追蹤 (穩定精確版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-1'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-1：外資 5 日買超佔標的成交量 追蹤")

import os
import glob
import pandas as pd

csv_pattern = os.path.join(DATA_DIR, "*外資買超佔成交比*.csv")
all_csv_files = glob.glob(csv_pattern)

if not all_csv_files:
    st.warning("⚠️ 找不到任何包含『外資買超佔成交比』的 CSV 檔案。")
else:
    all_csv_files.sort(reverse=True)
    target_files = all_csv_files[:14]
    base_df = None
    latest_day_today_data = {}

    for idx, f in enumerate(target_files):
        try:
            # 強制讀取並清洗所有欄位名稱 (移除空格、換行、BOM)
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 確保代號/名稱存在
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '代號', name_col: '名稱'})
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 自動偵測欄位 (包含關鍵字即可)
            col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
            
            # 存當日數據
            if idx == 0 and col_today:
                latest_day_today_data = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            # 合併歷史
            if col_5d:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}買佔比%"})
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
        except Exception:
            continue

    if base_df is not None:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 強健排序：依據最新日期數值排序
        latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}買佔比%"
        if latest_col_name in csv_display.columns:
            csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
            
        # 增加當日買佔比欄位處理
        csv_display['當日買佔比%'] = csv_display['股票代號'].map(latest_day_today_data).fillna(0)
            
        # 動態判定邏輯
        def evaluate_continuity(row):
            today = latest_day_today_data.get(row['股票代號'], 0)
            base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
            if pd.isna(today): return "⚪ 觀望"
            if today > 0: return "🔥 強延續" if today > base else "⚠️ 趨緩"
            elif today < 0: return "🚨 劇烈倒貨" if abs(today) > abs(base) else "📉 調節洗盤"
            return "🔄 持平"

        csv_display['今日短動態'] = csv_display.apply(evaluate_continuity, axis=1)
        
        # 動態說明對照表
        st.info("""
        **動態說明：** 🔥 強延續 (買盤加速) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (強烈賣出)
        """)
        
        # UI 與過濾
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="fo_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="fo_bond_v9")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 調整欄位順序
        cols = ["股票代號", "股票名稱", "今日短動態", "當日買佔比%"] + [c for c in csv_display.columns if "買佔比%" in c and c != "當日買佔比%"]
        csv_display = csv_display[cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
        
        # ==========================================================
        # 🔥 【重點新增】：將結果存入記憶體，供搜尋區塊讀取！
        # ==========================================================
        st.session_state['df_blk2_1'] = csv_display
        
    else:
        st.error("❌ 無法讀取外資買超數據，請檢查 CSV 欄位名稱是否包含『5日』與『成交』關鍵字。")

# ==========================================
# 🎯 區塊2-2：投信 5 日買超 佔成交量比 追蹤 (穩定修復版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-2'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-2：投信 5 日買超佔標的成交量 追蹤")

csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔成交比*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if not all_files_sitc:
    st.warning("⚠️ 找不到任何包含『投信買超佔成交比』的 CSV 檔案。")
else:
    all_files_sitc.sort(reverse=True)
    target_files = all_files_sitc[:14]
    base_df = None
    latest_day_today_data_sitc = {}

    for idx, f in enumerate(target_files):
        try:
            # 1. 強制讀取並清洗欄位 (移除空格、換行、BOM)
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\n", "").replace("\ufeff", "").strip() for c in df.columns]
            
            # 2. 確保代號/名稱欄位存在並清理
            id_col = next((c for c in df.columns if '代號' in c), df.columns[0])
            name_col = next((c for c in df.columns if '名稱' in c), df.columns[1])
            df = df.rename(columns={id_col: '代號', name_col: '名稱'})
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            # 3. 自動偵測關鍵欄位 (只要包含關鍵字即可)
            col_today = next((c for c in df.columns if '當日' in c and '買' in c and '成交' in c), None)
            col_5d = next((c for c in df.columns if '5日' in c and '買' in c and '成交' in c), None)
            
            if idx == 0 and col_today:
                latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}買佔比%"})
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
        except Exception:
            continue

    if base_df is not None:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        # 4. 強健排序
        latest_col_name = f"{extract_date_from_name(target_files[0])[-4:]}買佔比%"
        if latest_col_name in csv_display.columns:
            csv_display[latest_col_name] = pd.to_numeric(csv_display[latest_col_name].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_col_name, ascending=False)
            
        # 5. 增加當日數據並判定動態
        csv_display['當日買佔比%'] = csv_display['股票代號'].map(latest_day_today_data_sitc).fillna(0)
        
        def evaluate_continuity(row):
            today = latest_day_today_data_sitc.get(row['股票代號'], 0)
            base = pd.to_numeric(row.get(latest_col_name, 0), errors='coerce')
            if pd.isna(today): return "⚪ 觀望"
            if today > 0: return "🔥 強延續" if today > base else "⚠️ 趨緩"
            elif today < 0: return "🚨 劇烈倒貨" if abs(today) > abs(base) else "📉 調節洗盤"
            return "🔄 持平"

        csv_display['今日短動態'] = csv_display.apply(evaluate_continuity, axis=1)
        
        # 動態說明
        st.info("""
        **動態說明：** 🔥 強延續 (法人認養中) ⚠️ 趨緩 (買盤力道減弱) 🔄 持平 📉 調節洗盤 (微幅調節) 🚨 劇烈倒貨 (短線獲利了結)
        """)
        
        # 篩選邏輯
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_v9")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_v9")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        # 欄位順序調整
        cols = ["股票代號", "股票名稱", "今日短動態", "當日買佔比%"] + [c for c in csv_display.columns if "買佔比%" in c and c != "當日買佔比%"]
        csv_display = csv_display[cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
        
        # 🔥 【連動儲存】：存入對應的快搜抽屜
        st.session_state['df_blk2_2'] = csv_display
    else:
        st.error("❌ 無法讀取投信買超數據，請確認 CSV 檔案內含有『5日』與『成交』欄位。")

# ==========================================
# 🎯 區塊2-3：外資 5 日買超佔發行張數 追蹤 (穩定精確版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-3'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-3：外資 5 日買超佔公司發行張數 追蹤")
csv_pattern_fo = os.path.join(DATA_DIR, "*外資買超佔發行張數*.csv")
all_files_fo = glob.glob(csv_pattern_fo)

if not all_files_fo:
    st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
else:
    sorted_files = sorted(all_files_fo, key=extract_date_from_name, reverse=True)[:10]
    base_df = None
    date_labels = []
    latest_day_today_data_fo = {}

    for idx, f in enumerate(sorted_files):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
            
            if '代號' not in df.columns or '名稱' not in df.columns:
                continue
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            col_today = '當日買賣超佔發行張數'
            col_5d = '5日買賣超佔發行張數'
            
            if idx == 0 and col_today in df.columns:
                latest_day_today_data_fo = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d in df.columns:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}外資買發張數%"})
                
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            
            date_labels.append(d_label)
        except Exception:
            continue

    if base_df is not None and len(date_labels) > 0:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        latest_5d_col = f"{date_labels[0]}外資買發張數%"
        if latest_5d_col in csv_display.columns:
            csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
        
        def judge_today_alert_fo(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, 0)
            val_today = latest_day_today_data_fo.get(stock_id, 0)
            
            if val_5d == 0 or val_5d == "未進榜":
                return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
            
            if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
            elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
            return "🔄 今日量縮持平"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_fo, axis=1)
        
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="foreign_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="foreign_bond_final_v3")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        history_cols = [c for c in csv_display.columns if "外資買發張數%" in c]
        csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯 {len(date_labels)} 個交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
        
        # 🔥 【連動儲存】
        st.session_state['df_blk2_3'] = csv_display
    else:
        st.error("❌ 無法讀取外資數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")

# ==========================================
# 🎯 區塊2-4：投信 5 日買超佔發行張數 追蹤 (最終穩定版)
# ==========================================
st.write("---")
st.markdown("<div id='section-2-4'></div>", unsafe_allow_html=True)
st.header("🎯 區塊2-4：投信 5 日買超佔公司發行張數 追蹤")
csv_pattern_sitc = os.path.join(DATA_DIR, "*投信買超佔發行張數*.csv")
all_files_sitc = glob.glob(csv_pattern_sitc)

if not all_files_sitc:
    st.warning("⚠️ 找不到相關 CSV 檔案，請確認 DATA_DIR 路徑與檔名。")
else:
    sorted_files = sorted(all_files_sitc, key=extract_date_from_name, reverse=True)[:10]
    base_df = None
    date_labels = []
    latest_day_today_data_sitc = {}

    for idx, f in enumerate(sorted_files):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig')
            df.columns = [str(c).replace(" ", "").replace("\ufeff", "").strip() for c in df.columns]
            
            if '代號' not in df.columns or '名稱' not in df.columns:
                continue
            df['代號'] = df['代號'].astype(str).str.strip()
            df['名稱'] = df['名稱'].astype(str).str.strip()
            
            d_label = extract_date_from_name(f)[-4:]
            
            col_today = '當日買賣超佔發行張數'
            col_5d = '5日買賣超佔發行張數'
            
            if idx == 0 and col_today in df.columns:
                latest_day_today_data_sitc = dict(zip(df['代號'], pd.to_numeric(df[col_today], errors='coerce')))
            
            if col_5d in df.columns:
                df_s = df[['代號', '名稱', col_5d]].copy()
                df_s = df_s.rename(columns={col_5d: f"{d_label}投信買發張數%"})
                
                if base_df is None:
                    base_df = df_s
                else:
                    base_df = pd.merge(base_df, df_s, on=['代號', '名稱'], how='outer')
            
            date_labels.append(d_label)
        except Exception:
            continue

    if base_df is not None and len(date_labels) > 0:
        csv_display = base_df.fillna("未進榜").rename(columns={"代號": "股票代號", "名稱": "股票名稱"})
        
        latest_5d_col = f"{date_labels[0]}投信買發張數%"
        if latest_5d_col in csv_display.columns:
            csv_display[latest_5d_col] = pd.to_numeric(csv_display[latest_5d_col].replace("未進榜", 0), errors='coerce').fillna(0)
            csv_display = csv_display.sort_values(by=latest_5d_col, ascending=False)
        
        def judge_today_alert_sitc(row):
            stock_id = row['股票代號']
            val_5d = row.get(latest_5d_col, 0)
            val_today = latest_day_today_data_sitc.get(stock_id, 0)
            
            if val_5d == 0 or val_5d == "未進榜":
                return f"🆕 今日突擊卡位 ({val_today}%)" if val_today > 0 else "💤 籌碼沉澱中"
            
            if val_today < 0: return f"🚨 轉賣反轉 ({val_today}%)"
            elif val_today > 0: return f"🔥 持續加碼 ({val_today}%)"
            return "🔄 今日量縮持平"

        csv_display['今日短動態'] = csv_display.apply(judge_today_alert_sitc, axis=1)
        
        st.write("🔧 **自訂標的顯示過濾：**")
        c1, c2 = st.columns(2)
        show_etf = c1.checkbox("顯示 ETF", value=True, key="sitc_etf_final_v3")
        show_bond = c2.checkbox("顯示 債券/債券ETF", value=True, key="sitc_bond_final_v3")
        
        mask = (csv_display['股票代號'].str.len() == 4)
        if show_etf: mask |= ((csv_display['股票代號'].str.len() >= 5) & (~csv_display['股票代號'].str.endswith('B')))
        if show_bond: mask |= csv_display['股票代號'].str.endswith('B')
        csv_display = csv_display[mask]
        
        history_cols = [c for c in csv_display.columns if "投信買發張數%" in c]
        csv_display = csv_display[["股票代號", "股票名稱", "今日短動態"] + history_cols]
        csv_display.index = range(1, len(csv_display) + 1)
        
        st.success(f"📊 已成功串聯 {len(date_labels)} 個交易日，追蹤共 {len(csv_display)} 檔：")
        st.dataframe(csv_display, use_container_width=True)
        
        # 🔥 【連動儲存】
        st.session_state['df_blk2_4'] = csv_display
    else:
        st.error("❌ 無法讀取投信數據，請確保檔案內含『5日買賣超佔發行張數』欄位。")
# ==========================================
# 📅 區塊三：外資與投信連續買超 (日/週全景戰情室)
# ==========================================
st.write("---")
st.markdown("<div id='section-3'></div>", unsafe_allow_html=True)
st.header("📅 區塊3：連續買超")

st.info("""
狀態動態說明：🔥 波段認養: 連買 10以上天/週   ⚡ 買盤點火:連買 5 ~ 9 天/週   🆕 試單觀察:連買 1 ~ 4 天/週 """)

def read_live_ln_report(file_keyword, strict_type, exact_field_name, prefix_keyword, col_label):
    if strict_type == "日":
        search_pattern1 = os.path.join(DATA_DIR, f"*{file_keyword}*(日)*.csv")
        search_pattern2 = os.path.join(DATA_DIR, f"*{file_keyword}*日*.csv")
        target_files = glob.glob(search_pattern1) + glob.glob(search_pattern2)
        target_files = [f for f in target_files if "週" not in os.path.basename(f) and "周" not in os.path.basename(f) and "wk" not in os.path.basename(f).lower()]
    else:
        search_pattern1 = os.path.join(DATA_DIR, f"*{file_keyword}*(週)*.csv")
        search_pattern2 = os.path.join(DATA_DIR, f"*{file_keyword}*週*.csv")
        target_files = glob.glob(search_pattern1) + glob.glob(search_pattern2)
        
    target_files = list(set(target_files))
    if not target_files: return pd.DataFrame(), None
        
    latest_file = sorted(target_files, key=extract_date_from_name, reverse=True)[0]
    date_str = extract_date_from_name(latest_file) 
    
    try:
        # 強制指定 utf-8-sig 以解決中文亂碼，並清除欄位中的隱形字元
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        df.columns = df.columns.astype(str).str.replace('\n', '').str.replace(' ', '').str.replace('\ufeff', '').str.strip()
        
        # 動態查找欄位
        col_id = next((c for c in df.columns if '代號' in c), df.columns[0])
        col_name = next((c for c in df.columns if '名稱' in c), df.columns[1])
        
        target_key = exact_field_name.replace(' ', '')
        if target_key in df.columns:
            target_data_col = target_key
        else:
            matched_cols = [c for c in df.columns if '買賣' in c and strict_type in c]
            target_data_col = matched_cols[0] if matched_cols else df.columns[2]
            
        df[target_data_col] = pd.to_numeric(df[target_data_col], errors='coerce').fillna(0)
        df_sorted = df[df[target_data_col] > 0].sort_values(by=target_data_col, ascending=False)
        
        if df_sorted.empty: return pd.DataFrame(), date_str
            
        output_df = pd.DataFrame()
        output_df["股票代號"] = df_sorted[col_id].astype(str).str.strip()
        output_df["股票名稱"] = df_sorted[col_name].astype(str).str.strip()
        
        def get_status_tag(val):
            if val >= 10: return "🔥 波段認養"
            elif val >= 5: return "⚡ 買盤點火"
            else: return "🆕 試單觀察"
                
        output_df["狀態動態"] = df_sorted[target_data_col].apply(get_status_tag)
        output_df[col_label] = df_sorted[target_data_col].astype(int)
        
        real_pct_trade = [c for c in df_sorted.columns if prefix_keyword in c and "佔成交" in c]
        real_pct_issue = [c for c in df_sorted.columns if prefix_keyword in c and "佔發行量" in c]
        
        if real_pct_trade: output_df["佔成交(%)"] = pd.to_numeric(df_sorted[real_pct_trade[0]], errors='coerce').fillna(0.0)
        else: output_df["佔成交(%)"] = 0.0
            
        if real_pct_issue: output_df["佔發行量(%)"] = pd.to_numeric(df_sorted[real_pct_issue[0]], errors='coerce').fillna(0.0)
        else: output_df["佔發行量(%)"] = 0.0
            
        output_df.index = range(1, len(output_df) + 1)
        return output_df, date_str
    except Exception as e:
        return pd.DataFrame(), f"解讀失敗: {str(e)}"

# 執行排程與渲染 (與您原先邏輯相同)
live_fo_day, date_fo_day = read_live_ln_report("外資連續買超", "日", "外資連續買賣日數", "外資", "最新連買天數")
# ... (下方保持原本排程呼叫) ...

# ========================================================
# 🚀 執行排程
# ========================================================
live_fo_day, date_fo_day = read_live_ln_report("外資連續買超", "日", "外資連續買賣日數", "外資", "最新連買天數")
if live_fo_day.empty and date_fo_day is None: 
    live_fo_day, date_fo_day = read_live_ln_report("外資連買", "日", "外資連續買賣日數", "外資", "最新連買天數")

live_it_day, date_it_day = read_live_ln_report("投信連續買超", "日", "投信連續買賣日數", "投信", "最新連買天數")
if live_it_day.empty and date_it_day is None:
    live_it_day, date_it_day = read_live_ln_report("投信連買", "日", "投信連續買賣日數", "投信", "最新連買天數")
if live_it_day.empty:
    live_it_day, date_it_day = read_live_ln_report("外資連續買超", "日", "投信連續買賣日數", "投信", "最新連買天數")
    if live_it_day.empty:
        live_it_day, date_it_day = read_live_ln_report("外資連買", "日", "投信連續買賣日數", "投信", "最新連買天數")

live_fo_wk, date_fo_wk = read_live_ln_report("外資連續買超", "週", "外資連續買賣週數", "外資", "最新連買週數")
if live_fo_wk.empty and date_fo_wk is None:
    live_fo_wk, date_fo_wk = read_live_ln_report("外資連買", "週", "外資連續買賣週數", "外資", "最新連買週數")

live_it_wk, date_it_wk = read_live_ln_report("投信連續買超", "週", "投信連續買賣週數", "投信", "最新連買週數")
if live_it_wk.empty and date_it_wk is None:
    live_it_wk, date_it_wk = read_live_ln_report("投信連買", "週", "投信連續買賣週數", "投信", "最新連買週數")
if live_it_wk.empty:
    live_it_wk, date_it_wk = read_live_ln_report("外資連續買超", "週", "投信連續買賣週數", "投信", "最新連買週數")
    if live_it_wk.empty:
        live_it_wk, date_it_wk = read_live_ln_report("外資連買", "週", "投信連續買賣週數", "投信", "最新連買週數")

# ========================================================
# 🖼️ 視覺介面渲染 (左外資、右投信)
# ========================================================
st.subheader("⚡ 最新單日連續買超")
c_day1, c_day2 = st.columns(2)

with c_day1:
    st.markdown(f"🌐 **外資最新日連買** *(最新檔案日期: {date_fo_day if date_fo_day else '無資料'})*")
    if not live_fo_day.empty:
        st.dataframe(live_fo_day, use_container_width=True)
    else:
        st.write("無資料")

with c_day2:
    st.markdown(f"🏦 **投信最新日連買** *(最新檔案日期: {date_it_day if date_it_day else '無資料'})*")
    if not live_it_day.empty:
        st.dataframe(live_it_day, use_container_width=True)
    else:
        st.write("無資料")

st.write(" ") 

st.subheader("📅 最新單週連續波段買超")
c_wk1, c_wk2 = st.columns(2)

with c_wk1:
    st.markdown(f"🌐 **外資最新週連買** *(最新檔案日期: {date_fo_wk if date_fo_wk else '無資料'})*")
    if not live_fo_wk.empty:
        st.dataframe(live_fo_wk, use_container_width=True)
    else:
        st.write("無資料")

with c_wk2:
    st.markdown(f"🏦 **投信最新週連買** *(最新檔案日期: {date_it_wk if date_it_wk else '無資料'})*")
    if not live_it_wk.empty:
        st.dataframe(live_it_wk, use_container_width=True)
    else:
        st.write("無資料")

# ==========================================
# 🛠️ 必備函數：強硬讀取法 (解決 Big5/UTF-8 亂碼)
# ==========================================
def robust_read_csv(file_path):
    # 強制嘗試台灣常見編碼 (cp950 為 Big5)
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            # 簡單檢查：如果出現了亂碼常見字元，就換下一個編碼
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    # 真的都不行就強制讀取並忽略錯誤
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# ==========================================
# 🛠️ 必備函數：強硬讀取法
# ==========================================
def robust_read_csv(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')

# ==========================================
# 🛠️ 必備函數：強硬讀取法
# ==========================================
def robust_read_csv(file_path):
    for encoding in ['cp950', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if not df.empty and len(df.columns) > 1 and '撖' in str(df.iloc[0, 1]): 
                continue
            return df
        except:
            continue
    return pd.read_csv(file_path, encoding='cp950', errors='ignore')
# ========================================================
# 🖼️ 視覺介面渲染 (左外資、右投信)搜尋功能用
# ==========================================
# ...（以上維持您原本的4個 columns 視覺程式碼）...

# 🔥 【重點新增】：將區塊 3 的日、週連買共 4 張資料表清洗、標記並整合
b3_combined_list = []

if 'live_fo_day' in locals() and not live_fo_day.empty:
    df_tmp = live_fo_day.copy()
    df_tmp['連買類型'] = '🌐 外資日連買'
    df_tmp = df_tmp.rename(columns={'最新連買天數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if 'live_it_day' in locals() and not live_it_day.empty:
    df_tmp = live_it_day.copy()
    df_tmp['連買類型'] = '🏦 投信日連買'
    df_tmp = df_tmp.rename(columns={'最新連買天數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if 'live_fo_wk' in locals() and not live_fo_wk.empty:
    df_tmp = live_fo_wk.copy()
    df_tmp['連買類型'] = '🌐 外資週連買'
    df_tmp = df_tmp.rename(columns={'最新連買週數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if 'live_it_wk' in locals() and not live_it_wk.empty:
    df_tmp = live_it_wk.copy()
    df_tmp['連買類型'] = '🏦 投信週連買'
    df_tmp = df_tmp.rename(columns={'最新連買週數': '連買週期數'})
    b3_combined_list.append(df_tmp)

if b3_combined_list:
    df_b3 = pd.concat(b3_combined_list, ignore_index=True)
    # 💡 【修改點】：重新排列欄位，將「連買類型」移至最前面
    df_b3 = df_b3[['連買類型', '股票代號', '股票名稱', '狀態動態', '連買週期數']]
    st.session_state['df_blk3_main'] = df_b3
else:
    st.session_state['df_blk3_main'] = pd.DataFrame(columns=['連買類型', '股票代號', '股票名稱', '狀態動態', '連買週期數'])

# ==========券資比資料請一起搬遷============
# ==========================================
# 📅 區塊 4 綜合區：融資與借券動向 (5日累計)
# ==========================================

# 🛠️ 【不可省略】讀取函數
def get_specific_margin_data(keyword):
    found_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        if '.git' in root or 'venv' in root: continue
        for file in files:
            if file.lower().endswith(".csv") and keyword in file:
                found_files.append(os.path.join(root, file))
    
    if not found_files:
        return pd.DataFrame(), f"找不到包含『{keyword}』的檔案"
    
    latest_file = sorted(found_files, key=lambda x: os.path.basename(x), reverse=True)[0]
    file_name = os.path.basename(latest_file)
    
    try:
        df = robust_read_csv(latest_file)
        if df.empty:
            return pd.DataFrame(), f"讀取成功但內容為空: {file_name}"
        
        df.columns = df.columns.astype(str).str.replace('\ufeff', '').str.strip()
        
        for col in df.columns:
            if "幅度" in col or "張數" in col or "%" in col or "％" in col:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.replace('%', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df, file_name
    except Exception as e:
        return pd.DataFrame(), f"讀取崩潰 ({file_name}): {str(e)}"

# 🛠️ 【不可省略】欄位清理與過濾函數 (修正欄位名稱，讓搜尋引擎認得)
def process_margin_df(df, type_name, flag_etf, flag_bond):
    if df.empty: return df
    df = df.copy()
    
    cols_to_drop = [c for c in df.columns if "更新" in str(c) and "日期" in str(c)]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        
    target_idx = -1
    if type_name == "幅度":
        for i, col in enumerate(df.columns):
            if "3個月" in str(col) and ("%" in str(col) or "％" in str(col)):
                target_idx = i
                break
    else: 
        for i, col in enumerate(df.columns):
            if "3個月" in str(col) and "張數" in str(col):
                target_idx = i
                break
                
    if target_idx != -1:
        df = df.iloc[:, :target_idx+1]
        
    col_name = next((c for c in df.columns if '名稱' in c), None)
    col_id = next((c for c in df.columns if '代號' in c), None)
    
    if col_name and col_id:
        # 🔥 【終極修正】：強迫改名為 '股票代號' 與 '股票名稱'，搜尋引擎才找得到！
        df = df.rename(columns={col_id: '股票代號', col_name: '股票名稱'})
        
        df['股票代號'] = df['股票代號'].astype(str).str.strip()
        df['股票名稱'] = df['股票名稱'].astype(str).str.strip()
        
        mask_bond = df['股票名稱'].str.contains('債', na=False) | df['股票代號'].str.endswith('B', na=False)
        mask_etf = df['股票代號'].str.startswith('00', na=False)
        
        if not flag_bond: df = df[~mask_bond]
        if not flag_etf: df = df[~(mask_etf & ~mask_bond)] 

    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

# ==========================================
# 📅 區塊 4-1：融資減少動向
# ==========================================
st.write("---")
st.markdown("<div id='section-4-1'></div>", unsafe_allow_html=True)
st.header("📅 區塊 4-1：融資減少動向")

st.write("🔧 **自訂標的顯示過濾：**")
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1: show_etf_41 = st.checkbox("顯示 ETF", value=True, key="margin_show_etf")
with f_col2: show_bond_41 = st.checkbox("顯示債券/債券ETF", value=True, key="margin_show_bond")
st.write("") 

c1, c2 = st.columns(2)

with c1:
    st.subheader("📉 融資減少比例排名")
    df_pct, msg_pct = get_specific_margin_data("融資減少幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度", show_etf_41, show_bond_41)
    
    if not df_pct_clean.empty:
        # 👈 核心修改：只過濾出 8 碼日期字串
        date_str = re.search(r'\d{8}', msg_pct).group(0) if re.search(r'\d{8}', msg_pct) else "未知"
        st.write(f" **最新檔案日期: {date_str}**")
        st.dataframe(df_pct_clean, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 無相符資料")

with c2:
    st.subheader("📉 融資減少張數排名")
    df_vol, msg_vol = get_specific_margin_data("融資減少張數")
    df_vol_clean = process_margin_df(df_vol, "張數", show_etf_41, show_bond_41)
    
    if not df_vol_clean.empty:
        date_str = re.search(r'\d{8}', msg_vol).group(0) if re.search(r'\d{8}', msg_vol) else "未知"
        st.write(f" **最新檔案日期: {date_str}**")
        st.dataframe(df_vol_clean, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 無相符資料")

st.session_state['df_margin_pct'] = df_pct_clean
st.session_state['df_margin_vol'] = df_vol_clean

# ==========================================
# 📅 區塊 4-2：借券賣出減少動向
# ==========================================
st.write("---")
st.markdown("<div id='section-4-2'></div>", unsafe_allow_html=True)
st.header("📅 區塊 4-2：借券賣出減少動向")

st.write("🔧 **自訂標的顯示過濾：**")
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1: show_etf_42 = st.checkbox("顯示 ETF", value=True, key="stock_show_etf_42")
with f_col2: show_bond_42 = st.checkbox("顯示債券/債券ETF", value=True, key="stock_show_bond_42")
st.write("") 

c1, c2 = st.columns(2)

with c1:
    st.subheader("📉 借券賣出減少比例排名")
    df_pct, msg_pct = get_specific_margin_data("借券賣出減少幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度", show_etf_42, show_bond_42)
    
    if not df_pct_clean.empty:
        # 👈 核心修改：只過濾出 8 碼日期字串
        date_str = re.search(r'\d{8}', msg_pct).group(0) if re.search(r'\d{8}', msg_pct) else "未知"
        st.write(f" **最新檔案日期: {date_str}**")
        st.dataframe(df_pct_clean, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 無相符資料")

with c2:
    st.subheader("📉 借券賣出減少張數排名")
    df_vol, msg_vol = get_specific_margin_data("借券賣出減少張數")
    df_vol_clean = process_margin_df(df_vol, "張數", show_etf_42, show_bond_42)
    
    if not df_vol_clean.empty:
        date_str = re.search(r'\d{8}', msg_vol).group(0) if re.search(r'\d{8}', msg_vol) else "未知"
        st.write(f" **最新檔案日期: {date_str}**")
        st.dataframe(df_vol_clean, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 無相符資料")

st.session_state['df_short_pct'] = df_pct_clean
st.session_state['df_short_vol'] = df_vol_clean

# ==========================================
# 📅 區塊 4-3：融券增加動向
# ==========================================
st.write("---")
st.markdown("<div id='section-4-3'></div>", unsafe_allow_html=True)
st.header("📅 區塊 4-3：融券增加動向 (5日累計)")

st.write("🔧 **自訂標的顯示過濾：**")
f_col1, f_col2, _ = st.columns([1, 1, 2])
with f_col1: show_etf_43 = st.checkbox("顯示 ETF", value=True, key="stock_show_etf_43")
with f_col2: show_bond_43 = st.checkbox("顯示債券/債券ETF", value=True, key="stock_show_bond_43")
st.write("") 

c1, c2 = st.columns(2)

with c1:
    st.subheader("📈 融券增加比例排名")
    df_pct, msg_pct = get_specific_margin_data("融券增加幅度")
    df_pct_clean = process_margin_df(df_pct, "幅度", show_etf_43, show_bond_43)
    
    if not df_pct_clean.empty:
        # 👈 核心修改：只過濾出 8 碼日期字串
        date_str = re.search(r'\d{8}', msg_pct).group(0) if re.search(r'\d{8}', msg_pct) else "未知"
        st.write(f" **最新檔案日期: {date_str}**")
        st.dataframe(df_pct_clean, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 無相符資料")

with c2:
    st.subheader("📈 融券增加張數排名")
    df_vol, msg_vol = get_specific_margin_data("融券增加張數")
    df_vol_clean = process_margin_df(df_vol, "張數", show_etf_43, show_bond_43)
    
    if not df_vol_clean.empty:
        date_str = re.search(r'\d{8}', msg_vol).group(0) if re.search(r'\d{8}', msg_vol) else "未知"
        st.write(f" **最新檔案日期: {date_str}**")
        st.dataframe(df_vol_clean, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 無相符資料")

st.session_state['df_margin_plus_pct'] = df_pct_clean
st.session_state['df_margin_plus_vol'] = df_vol_clean
# ==========券資比資料請一起搬遷============

# ==========================================
# 💰 區塊 5：大股東動向 (日期去重與去西元修復版)
# ==========================================
st.write("---")
st.markdown("<div id='section-5'></div>", unsafe_allow_html=True)
st.header("💰 區塊 5：大股東動向")

import re

csv_pattern_b5 = os.path.join(DATA_DIR, "*神秘金字塔 - 股權類股排行(5日之400張以上股東排行)*.csv")
all_files_b5 = glob.glob(csv_pattern_b5)

if not all_files_b5:
    st.warning("⚠️ 找不到相關 CSV 檔案。")
else:
    # 依照檔名排序，確保最新的檔案在最前面
    all_files_b5 = sorted(all_files_b5, key=os.path.basename, reverse=True)
    
    master_df = None
    all_date_cols = set()

    # 1. 遍歷所有檔案並合併
    for idx, file in enumerate(all_files_b5):
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            df.columns = [str(c).strip() for c in df.columns]
            
            # 🔥 【核心修復 1】：即時偵測並刪除欄位名稱開頭的 "2026"
            standardized_cols = []
            for c in df.columns:
                if re.match(r'^2026\d{4}$', c):  # 如果是 2026XXXX 格式
                    standardized_cols.append(c[-4:])  # 只取後方 4 碼 XXXX
                else:
                    standardized_cols.append(c)
            df.columns = standardized_cols
            
            # 🔥 【核心修復 2】：刪除單檔內部可能重複的相同日期欄位
            df = df.loc[:, ~df.columns.duplicated()]
            
            # 分離代號與名稱
            if '股票代號/名稱' in df.columns:
                df['股票代號'] = df['股票代號/名稱'].astype(str).str.extract(r'(\d+)')
                df['股票名稱'] = df['股票代號/名稱'].astype(str).str.replace(r'^\d+', '', regex=True)
            
            if '股票代號' not in df.columns:
                continue
                
            # 抓取已被標準化為 4 碼的日期欄位
            date_cols = [c for c in df.columns if re.match(r'^\d{4}$', c)]
            all_date_cols.update(date_cols)
            
            # 決定保留的欄位
            cols_to_keep = ['股票代號', '股票名稱'] + date_cols
            
            # 只有在讀取最新檔案 (idx == 0) 時，才把「上週持有%」抓進來
            if idx == 0 and '上週持有%' in df.columns:
                cols_to_keep.append('上週持有%')
            
            cols_to_keep = [c for c in cols_to_keep if c in df.columns]
            temp_df = df[cols_to_keep].copy()
            
            # 設定索引進行智慧拼接
            temp_df = temp_df.set_index(['股票代號', '股票名稱'])
            
            if master_df is None:
                master_df = temp_df
            else:
                # 智慧拼接歷史資料
                master_df = master_df.combine_first(temp_df)
        except Exception:
            continue

    if master_df is not None:
        master_df = master_df.reset_index()
        
        # 2. 排序日期欄位 (皆已轉為4碼，可直接降冪排序，越新越前面)
        sorted_dates = sorted(list(all_date_cols), reverse=True)
        
        # 3. 計算週動態
        if len(sorted_dates) >= 2:
            newest, prev = sorted_dates[0], sorted_dates[1]
            master_df[newest] = pd.to_numeric(master_df[newest], errors='coerce')
            master_df[prev] = pd.to_numeric(master_df[prev], errors='coerce')
            
            def get_trend(row):
                v1, v2 = row.get(newest), row.get(prev)
                if pd.isna(v1) or pd.isna(v2): return "無資料"
                diff = v1 - v2
                if diff >= 1.5: return "🔥 大增"
                if diff >= 0.5: return "📈 增"
                if diff > 0: return "↗️ 微增"
                if diff == 0: return "🔄 持平"
                if diff > -0.5: return "↘️ 微減"
                if diff > -1.5: return "📉 減"
                return "🚨 大減"
            
            master_df['週動態'] = master_df.apply(get_trend, axis=1)
        else:
            master_df['週動態'] = "無資料"

        # 4. 整理最終欄位順序：代號、名稱、週動態、上週持有%、所有日期(新到舊)
        final_cols = ['股票代號', '股票名稱', '週動態']
        if '上週持有%' in master_df.columns:
            final_cols.append('上週持有%')
        final_cols.extend(sorted_dates)
        
        final_df = master_df[[c for c in final_cols if c in master_df.columns]].copy()
        
        # 5. 排序表單：以最新日期做為置頂降冪排序依據
        if sorted_dates:
            final_df = final_df.sort_values(by=sorted_dates[0], ascending=False)
        
        # 6. 清理小數點與空值 (安全去除 .0 尾數)
        def clean_decimals(val):
            if pd.isna(val): return "無資料"
            s = str(val).strip()
            if s.endswith('.0'): return s[:-2]
            return s
            
        for col in sorted_dates:
            final_df[col] = final_df[col].apply(clean_decimals)
        if '上週持有%' in final_df.columns:
            final_df['上週持有%'] = final_df['上週持有%'].apply(clean_decimals)
            
        final_df = final_df.fillna("無資料")
        
        st.success(f"已成功串連 {len(final_df)} 筆股東數據")
        st.dataframe(final_df, use_container_width=True, hide_index=True)
        
        # 將最終結果同步存入記憶體，供搜尋區塊聯動掃描
        st.session_state['df_blk5'] = final_df
    else:
        st.error("無法合併資料。")

# ==========================================
# 🏆 頂級選股池核心引擎 (精確量化權重 + 欄位美化版)
# ==========================================
with top_pool_container:
    st.write("---")
    st.markdown("<div id='section-top-pool'></div>", unsafe_allow_html=True)
    st.header("🏆 數據分析觀察名單 (全區塊綜合評比)")
    st.info("💡 **權重評分**：法人持股上榜搭配其他數據分析積分。")

    if 'my_final_df' not in st.session_state or st.session_state['my_final_df'].empty:
        st.warning("⚠️ 尚未載入區塊 1 資料，無法進行選股池評比。")
    else:
        df_b1 = st.session_state['my_final_df'].copy()
        
        # 尋找區塊 1 的動態欄位與今日上榜欄位
        dyn_col = next((c for c in df_b1.columns if '動態' in c or '動能' in c), None)
        rank_col = next((c for c in df_b1.columns if '今日上榜' in c or '上榜' in c), None)
        
        if dyn_col:
            mask = df_b1[dyn_col].astype(str).str.contains('趨緩|上升|升|持平|加碼', na=False)
            pool_df = df_b1[mask].copy()
        else:
            pool_df = df_b1.copy()
            
        if pool_df.empty:
            st.warning("⚪ 目前區塊 1 中沒有符合「趨緩、上升、持平」動能的標的。")
        else:
            # 3. 讀取賣出警示名單 (外資/投信倒貨)
            fo_sell_ids, it_sell_ids = set(), set()
            try:
                fo_sell_files = glob.glob(os.path.join(DATA_DIR, "*外資賣出佔成交比*3日*.csv"))
                if not fo_sell_files: fo_sell_files = glob.glob(os.path.join(DATA_DIR, "*外資賣出佔成交比*.csv"))
                if fo_sell_files:
                    df_fs = robust_read_csv(sorted(fo_sell_files, reverse=True)[0])
                    id_c = next((c for c in df_fs.columns if '代號' in c), None)
                    if id_c: fo_sell_ids = set(df_fs[id_c].astype(str).str.replace(r'\D', '', regex=True))
                
                it_sell_files = glob.glob(os.path.join(DATA_DIR, "*投信賣出佔成交比*5日*.csv"))
                if not it_sell_files: it_sell_files = glob.glob(os.path.join(DATA_DIR, "*投信賣出佔成交比*.csv"))
                if it_sell_files:
                    df_is = robust_read_csv(sorted(it_sell_files, reverse=True)[0])
                    id_c = next((c for c in df_is.columns if '代號' in c), None)
                    if id_c: it_sell_ids = set(df_is[id_c].astype(str).str.replace(r'\D', '', regex=True))
            except: pass

            def get_df_safe(key): return st.session_state.get(key, pd.DataFrame())

            df_b2_1, df_b2_2 = get_df_safe('df_blk2_1'), get_df_safe('df_blk2_2')
            df_b2_3, df_b2_4 = get_df_safe('df_blk2_3'), get_df_safe('df_blk2_4')
            df_b3 = get_df_safe('df_blk3_main')
            
            s_b4_mar_pct, s_b4_mar_vol = set(get_df_safe('df_margin_pct').get('股票代號', [])), set(get_df_safe('df_margin_vol').get('股票代號', []))
            s_b4_sho_pct, s_b4_sho_vol = set(get_df_safe('df_short_pct').get('股票代號', [])), set(get_df_safe('df_short_vol').get('股票代號', []))
            s_b4_mp_pct, s_b4_mp_vol = set(get_df_safe('df_margin_plus_pct').get('股票代號', [])), set(get_df_safe('df_margin_plus_vol').get('股票代號', []))
            
            df_b5 = get_df_safe('df_blk5')

            def check_b2_strict(df, sid, bad_keywords):
                if df.empty or sid not in df['股票代號'].values: return False
                dyn = str(df[df['股票代號'] == sid].iloc[0].get('今日短動態', ''))
                if any(bad in dyn for bad in bad_keywords): return False
                return True

            bad_b2_vol = ['持平', '調節洗盤', '劇烈倒貨', '觀望']
            bad_b2_iss = ['轉賣反轉', '籌碼沉澱中', '今日量縮持平']

            def get_b3_score(df, sid, type_keyword):
                if df.empty: return 0, ""
                match = df[(df['股票代號'] == sid) & (df['連買類型'].str.contains(type_keyword))]
                if match.empty: return 0, ""
                days = pd.to_numeric(match.iloc[0].get('連買週期數', 0), errors='coerce')
                if pd.isna(days) or days == 0: return 0, ""
                if '日' in type_keyword:
                    if days >= 10: return 1.0, f"✔️({days}日)"
                    elif days >= 5: return 0.8, f"✔️({days}日)"
                    else: return 0.5, f"✔️({days}日)"
                else:
                    if days >= 10: return 2.0, f"✔️({days}週)"
                    elif days >= 5: return 1.5, f"✔️({days}週)"
                    else: return 1.0, f"✔️({days}週)"

            # 5. 計分迴圈
            results = []
            for _, row in pool_df.iterrows():
                sid = str(row['股票代號']).strip()
                sname = str(row.get('股票名稱', '')).strip()
                b1_dyn = str(row.get(dyn_col, '')) if dyn_col else '-'
                b1_rank = str(row.get(rank_col, '-')) if rank_col else '-'
                score = 0.0
                
                r_b2_1 = "✔️" if check_b2_strict(df_b2_1, sid, bad_b2_vol) else ""; score += 1 if r_b2_1 else 0
                r_b2_2 = "✔️" if check_b2_strict(df_b2_2, sid, bad_b2_vol) else ""; score += 1 if r_b2_2 else 0
                r_b2_3 = "✔️" if check_b2_strict(df_b2_3, sid, bad_b2_iss) else ""; score += 1 if r_b2_3 else 0
                r_b2_4 = "✔️" if check_b2_strict(df_b2_4, sid, bad_b2_iss) else ""; score += 1 if r_b2_4 else 0
                
                s_fd, r_b3_fd = get_b3_score(df_b3, sid, '外資日'); score += s_fd
                s_fw, r_b3_fw = get_b3_score(df_b3, sid, '外資週'); score += s_fw
                s_id, r_b3_id = get_b3_score(df_b3, sid, '投信日'); score += s_id
                s_iw, r_b3_iw = get_b3_score(df_b3, sid, '投信週'); score += s_iw
                
                r_b4_mar = ""; 
                if sid in s_b4_mar_pct: r_b4_mar += "✔️(幅)"; score += 1
                if sid in s_b4_mar_vol: r_b4_mar += "✔️(量)"; score += 0.5
                
                r_b4_sho = ""; 
                if sid in s_b4_sho_pct: r_b4_sho += "✔️(幅)"; score += 1
                if sid in s_b4_sho_vol: r_b4_sho += "✔️(量)"; score += 0.5
                
                r_b4_mp = ""; 
                if sid in s_b4_mp_pct: r_b4_mp += "✔️(幅)"; score += 1
                if sid in s_b4_mp_vol: r_b4_mp += "✔️(量)"; score += 0.5
                
                r_b5 = ""
                if not df_b5.empty and sid in df_b5['股票代號'].values:
                    trend = str(df_b5[df_b5['股票代號'] == sid].iloc[0].get('週動態', ''))
                    if '大增' in trend or ('增' in trend and '微' not in trend): score += 2; r_b5 = "🔥大增(+2)"
                    elif '微增' in trend: score += 1; r_b5 = "↗️微增(+1)"
                    elif '大減' in trend: score -= 1; r_b5 = "🚨大減(-1)"
                    elif '減' in trend and '微' in trend: score -= 0.5; r_b5 = "↘️微減(-0.5)"
                    elif '減' in trend: score -= 0.5; r_b5 = "📉減(-0.5)"
                    else: r_b5 = trend
                
                # 🔥 【精簡文字修復】：防止表格寬度被卡到
                is_fo_sell = sid in fo_sell_ids
                is_it_sell = sid in it_sell_ids
                if is_fo_sell and is_it_sell: r_warn = "🚨外投雙倒"
                elif is_fo_sell: r_warn = "⚠️外資倒"
                elif is_it_sell: r_warn = "⚠️投信倒"
                else: r_warn = "-"

                results.append({
                    '總分': score,
                    '股票代號': sid,
                    '股票名稱': sname,
                    'B1動態': b1_dyn,
                    '今日上榜欄位': b1_rank,  # 👈 新增區塊 1 訊號
                    '外買佔比': r_b2_1, '投買佔比': r_b2_2, '外佔發行': r_b2_3, '投佔發行': r_b2_4,
                    '外日連': r_b3_fd, '外週連': r_b3_fw, '投日連': r_b3_id, '投週連': r_b3_iw,
                    '資減': r_b4_mar, '借減': r_b4_sho, '券增': r_b4_mp,
                    '大股東動向': r_b5, '法人賣出警示': r_warn
                })
                
            res_df = pd.DataFrame(results)
            res_df = res_df.sort_values(by='總分', ascending=False).reset_index(drop=True)
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            st.success(f"🎯 頂級選股池掃描完成！共過濾出 {len(res_df)} 檔潛力標的。")
            st.session_state['top_pool_df'] = res_df

# ==========================================
# 📊 【蜂蜜計數器】本站累計觀測人次統計
# ==========================================
st.write("---")

# 🌟 新增防護罩：如果伺服器上沒有這個資料夾，就自動建立一個，避免當機
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

counter_file = os.path.join(DATA_DIR, "counter.txt")
if not os.path.exists(counter_file):
    with open(counter_file, "w") as f: f.write("1")
    count = 1
else:
    with open(counter_file, "r") as f:
        try: count = int(f.read().strip()) + 1
        except: count = 1
    with open(counter_file, "w") as f: f.write(str(count))

st.markdown(f"<p style='text-align: center; font-size: 16px; color: #DDA400; font-weight: bold;'>🐝 🍯 迷途不回家的小蜜蜂： {count} 隻 ｜ 祝阿東甜美收尾，順利通關畢業！ 🍯 🐝</p>", unsafe_allow_html=True)
