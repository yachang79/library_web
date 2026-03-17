# 圖書館借閱系統

以 Flask + SQLite 建置的輕量級圖書館借閱管理系統，支援會員管理、圖書管理與借閱記錄，可部署於 [Render](https://render.com) 平台。

## Demo

**線上展示：** [https://library-web-8vte.onrender.com](https://library-web-8vte.onrender.com)

## 功能特色

| 模組 | 功能 |
|------|------|
| 首頁總覽 | 會員數、館藏數、借出數統計；最近借閱記錄 |
| 會員管理 | 新增 / 編輯 / 刪除會員，支援姓名、編號、電話搜尋 |
| 圖書管理 | 新增 / 編輯 / 刪除書籍，顯示借閱狀態，支援關鍵字搜尋 |
| 借閱服務 | 借閱登記、歸還登記，借出中 / 已歸還篩選 |

## 技術棧

- **後端**：Python 3.11 / Flask 3.x
- **資料庫**：SQLite（WAL mode）
- **前端**：Bootstrap 5.3 + Bootstrap Icons
- **部署**：Gunicorn / Render

## 本地開發

```bash
# 1. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. 安裝相依套件
pip install -r requirements.txt

# 3. 設定環境變數（選用）
export SECRET_KEY=your-secret-key

# 4. 啟動開發伺服器
python app.py
```

開啟瀏覽器前往 `http://localhost:5000`

## 部署至 Render

1. Fork 或 push 此專案至 GitHub
2. 在 Render 建立新的 **Web Service**，連結 GitHub repo
3. Render 會自動讀取 `render.yaml` 完成設定
4. 在 Render 環境變數中設定 `SECRET_KEY`

> **注意**：Render 免費方案的磁碟不支援持久化，SQLite 資料庫於每次重新部署後會重置。正式環境請改用 PostgreSQL。

## 專案結構

```
library_web/
├── app.py              # 主應用程式（路由 & 資料庫邏輯）
├── requirements.txt    # Python 相依套件
├── Procfile            # Gunicorn 啟動指令
├── render.yaml         # Render 部署設定
└── templates/
    ├── base.html           # 共用版型（側邊欄、Flash 訊息）
    ├── index.html          # 首頁總覽
    ├── members/
    │   ├── list.html       # 會員列表
    │   └── form.html       # 新增 / 編輯會員
    ├── books/
    │   ├── list.html       # 圖書列表
    │   └── form.html       # 新增 / 編輯圖書
    └── borrowings/
        ├── list.html       # 借閱記錄列表
        └── form.html       # 新增借閱
```

## 環境變數

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `SECRET_KEY` | Flask session 加密金鑰 | `library_secret_key_2024`（僅開發用） |

## License

MIT

---

> Vibe coding by Claude Code + OpenAI Codex
> [github.com/yachang79/library_web](https://github.com/yachang79/library_web)
