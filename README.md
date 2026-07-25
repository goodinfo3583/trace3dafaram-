最近開發了宅宅『股市派對』籌碼分析工具，整合了台灣市場的籌碼變化、籌碼分析、大戶(腿)動向與統計表格，一起成為千張大戶吧。歡迎教學研究參考與交流：https://3dafaram3583.streamlit.app/



專案架構

📁 專案根目錄/

│

├── 📄test\_web.py                   #  主程式 (Router \& 初始化)

│                                # 負責: 連線資料庫、讀取 Session、根據點擊把冒險者帶到對應的包廂(views)。

│

├── 📁 components/               #  裝潢與基礎設施 (UI 組件)

│   ├── 📄 nav\_manager.py        # 導航管家 (頂部 JS 導覽列、全站共用隱形按鈕)

│   └── 📄 style\_manager.py      # 視覺設計 (CSS 樣式、跑馬燈特效)

│

├── 📁 utils/                    #  工具箱 (純邏輯與資料處理)

│   └── 📄 data\_utils.py         # 讀取 CSV、清理代號、轉換格式等防呆小幫手

│

├── 📁 views/                    #  獨立頁面 (各個獨立的頁面專屬包廂邏輯)

│   ├── 📄 news\_page.py          # 市場消息

│   ├── 📄 contact\_page.py      #  聯絡我們 (寫入 G-Sheets)

│   ├── 📄 pool\_page.py          #  觀察名單 (大數據計分、樹狀圖、歷史回測)

│   ├── 📄 b1\_page.py            # 區塊 1 法人動向

│   └── 📄 b2\_page.py            # 區塊 2 ...

│

└── 📁 static/                   # 🖼️ 倉庫 (靜態資源)

&#x20;   └── 📄 75743.jpg             # 管家圖片等

