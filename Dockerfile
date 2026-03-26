# 使用 Python 官方映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (ChromaDB 可能需要一些編譯工具)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案文件
COPY . .

# 曝露埠號 (Render/Zeabur 會自動覆蓋)
EXPOSE 8000

# 啟動指令 (使用 Gunicorn 提高穩定性)
# 注意：使用 uvicorn.workers.UvicornWorker 來處理 FastAPI
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
