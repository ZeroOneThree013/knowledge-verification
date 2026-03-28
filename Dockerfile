# 使用 Python 3.10 完整版 (非 slim)，系統穩定性與相容性最高
FROM python:3.10

# 設定工作目錄
WORKDIR /app

# 建立 HuggingFace Spaces 要求的非 root 使用者 (UID 1000)
RUN useradd -m -u 1000 user && chown -R user /app

# 設定環境變數 (重要：為 PORT 設定預設值 7860)
ENV PORT=7860

# 安裝必要的系統編譯工具與依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有專案檔案 (包括補齊的 frontend 資料夾)
COPY . .

# 切換至非 root 使用者 (HuggingFace Spaces 要求)
USER user

# 曝露埠號
EXPOSE 7860

# 啟動指令 (使用 Gunicorn 並動態綁定 PORT)
CMD gunicorn app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
