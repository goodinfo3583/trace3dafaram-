# 📋 完美等比 8 欄位設計 (調整比例：縮小名稱與產業的間距，放大筆記空間)
        # 舊版: [1.2, 0.8, 1.2, 1.3, 2.5, 0.8, 0.7, 0.5]
        # 新版: [0.9, 0.7, 1.2, 1.2, 3.2, 0.7, 0.6, 0.5]
        col_ratios = [0.9, 0.7, 1.2, 1.2, 3.2, 0.7, 0.6, 0.5]
        
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(col_ratios)
        h1.markdown("<span style='color:#94a3b8; font-size:14px;'>標的名稱</span>", unsafe_allow_html=True)
        h2.markdown("<span style='color:#94a3b8; font-size:14px;'>產業別</span>", unsafe_allow_html=True)
        h3.markdown("<span style='color:#94a3b8; font-size:14px;'>最新價</span>", unsafe_allow_html=True)
        h4.markdown("<span style='color:#94a3b8; font-size:14px;'>成交量 (張)</span>", unsafe_allow_html=True)
        h5.markdown("<span style='color:#94a3b8; font-size:14px;'>專屬筆記 (Enter換行/點擊空白處存檔)</span>", unsafe_allow_html=True)
        h8.markdown("<span style='color:#94a3b8; font-size:13px;'>批次</span>", unsafe_allow_html=True)

        def save_note_callback(stock_key):
            watchlist[stock_key] = st.session_state[f"note_{stock_key}"]
            save_user_watchlist(username, watchlist)

        # 🎨 台股專屬紅綠顏色渲染器
        def fmt_color(val, is_pct=False, is_vol=False):
            color = "#FF4B4B" if val > 0 else ("#00E272" if val < 0 else "#94A3B8")
            sign = "+" if val > 0 else ""
            tail = "%" if is_pct else ""
            if is_vol: return f"<span style='color:{color}; font-size:12px;'>({sign}{val:.1f}%)</span>"
            return f"<span style='color:{color}; font-weight:bold;'>{sign}{val:.2f}{tail}</span>"

        for stock, note in list(watchlist.items()):
            
            # 取出代號
            pure_code = None
            stock_code_match = re.search(r'\d+', stock)
            if stock_code_match: pure_code = stock_code_match.group()

            # 動態尋找產業別
            industry_label = "未知"
            if pure_code and STOCK_DICT and pure_code in STOCK_DICT:
                industry_label = STOCK_DICT[pure_code].get("industry", "未知")

            # 抓取報價資料
            p_str, v_str = "<span style='color:#555;'>-</span>", "<span style='color:#555;'>-</span>"
            if pure_code and pure_code in market_data:
                d = market_data[pure_code]
                p_str = f"<span style='font-size:16px;'>{d['price']:.2f}</span><br>{fmt_color(d['price_pct'], True)}"
                v_str = f"<span style='font-size:15px;'>{d['vol']:,}</span><br>{fmt_color(d['vol_pct'], False, True)}"

            # 渲染各欄位 (套用新比例)
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(col_ratios)
            
            with c1:
                st.markdown(f"<div style='padding-top:8px; font-weight:bold; font-size:15px;'>{stock}</div>", unsafe_allow_html=True)
            with c2:
                # 拿掉多餘的 padding，讓標籤與名稱更緊湊
                st.markdown(f"<div style='padding-top:10px; font-size:12px; color:#38BDF8;'><span style='background-color:#1E293B; padding:2px 5px; border-radius:4px; border: 1px solid #0369a1;'>{industry_label}</span></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='padding-top:4px;'>{p_str}</div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='padding-top:4px;'>{v_str}</div>", unsafe_allow_html=True)
            with c5:
                # 🚀 核心改動：將 st.text_input 換成 st.text_area (多行便利貼)
                st.markdown("<div style='padding-top:2px;'>", unsafe_allow_html=True)
                st.text_area(
                    "筆記", 
                    value=note, 
                    key=f"note_{stock}", 
                    label_visibility="collapsed", 
                    placeholder="點此輸入筆記...", 
                    on_change=save_note_callback, 
                    args=(stock,),
                    height=68  # 設定一個舒適的預設高度 (約兩行字高)，使用者打滿會自動捲動
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with c6:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button(f"🔍 顯示", key=f"view_{stock}", use_container_width=True):
                    st.session_state["selected_watch_stock"] = stock
                    st.session_state["global_search_final"] = pure_code if pure_code else stock
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c7:
                st.markdown("<div style='padding-top:15px;'>", unsafe_allow_html=True)
                if st.button(f"移除", key=f"remove_{stock}", use_container_width=True):
                    del watchlist[stock]
                    save_user_watchlist(username, watchlist)
                    if st.session_state.get("selected_watch_stock") == stock:
                        st.session_state["selected_watch_stock"] = None
                        st.session_state["global_search_final"] = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c8:
                st.markdown("<div style='padding-top:22px; padding-left:5px;'>", unsafe_allow_html=True)
                st.checkbox("選取", key=f"chk_{stock}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color: #1E293B; margin: 5px 0;'>", unsafe_allow_html=True)
