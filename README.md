# 知識驗證系統

將任意網頁文章轉換為互動式學習材料——自動生成教學卡片與測驗題，並支援匯出學習紀錄。

**線上體驗：** https://s920819-knowledge-verify.hf.space

---

## 功能

- **網址解析**：輸入任意文章網址，系統自動爬取內文並建立向量知識庫（RAG）
- **教學卡片**：由 Gemini AI 從文章中萃取 3–5 個核心概念，以卡片形式呈現
- **精熟測驗**：自動生成單選題測驗，即時評分
- **匯出紀錄**：將作答結果與解答匯出為 Markdown 檔案，並可寄送至 Email

---

## 技術架構

| 層級 | 技術 |
|------|------|
| 後端 | Python · FastAPI · Gunicorn |
| AI / RAG | LangChain · Google Gemini 2.5 Flash · ChromaDB |
| 前端 | 原生 HTML / CSS / JavaScript |
| 部署 | Docker · HuggingFace Spaces · Zeabur |

---

## 本地端執行

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製下列內容建立 `.env` 檔案（此檔案已被 `.gitignore` 排除，不會上傳）：

```env
GOOGLE_API_KEY=你的_Google_API_Key
GMAIL_APP_PASSWORD=你的_Gmail_應用程式密碼（16碼）
PORT=8000
```

- `GOOGLE_API_KEY`：在 [Google AI Studio](https://aistudio.google.com/apikey) 取得
- `GMAIL_APP_PASSWORD`：在 [Google 帳號 > 應用程式密碼](https://myaccount.google.com/apppasswords) 取得（需開啟兩步驟驗證）

### 3. 啟動伺服器

```bash
python app.py
```

開啟瀏覽器前往 `http://localhost:8000`

---

## 部署

### HuggingFace Spaces（Docker）

1. 建立一個 **Docker** 類型的 Space
2. 在 Space 的 **Settings > Variables and secrets** 中加入：
   - `GOOGLE_API_KEY`
   - `GMAIL_APP_PASSWORD`
3. 將此 repo 推送至 Space

### Zeabur

`zeabur.json` 已預先設定，直接匯入專案即可部署。記得在 Zeabur 後台設定上述兩個環境變數。

---

## 專案結構

```
├── app.py            # FastAPI 主應用程式，定義所有 API 路由
├── rag_manager.py    # RAG 核心：文字切塊、向量化、相似度檢索
├── llm_service.py    # LLM 服務：呼叫 Gemini 生成教學卡片與測驗
├── crawler.py        # 網頁爬蟲：抓取指定網址的純文字內容
├── frontend/         # 靜態前端頁面
│   ├── index.html    # 首頁（輸入網址）
│   ├── teaching.html # 教學卡片頁
│   ├── quiz.html     # 測驗頁
│   └── history.html  # 學習紀錄頁
├── Dockerfile        # 容器化設定（相容 HuggingFace Spaces）
├── requirements.txt  # Python 依賴清單
└── zeabur.json       # Zeabur 部署設定
```
