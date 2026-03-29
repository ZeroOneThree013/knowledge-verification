from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from crawler import fetch_url_content
import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from rag_manager import RAGManager
from llm_service import LLMService

app = FastAPI(title="知識驗證 Backend API", description="將網頁轉換為 RAG 知識庫，並生成教學卡片與測驗", version="1.0.0")

# 設定 CORS 以允許前端從不同 domain/port 連接 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_manager = RAGManager()
llm_service = LLMService()

class URLRequest(BaseModel):
    url: str

class ExportRequest(BaseModel):
    email: str
    quiz_data: list
    score: int
    total: int

@app.post("/api/process_url")
async def process_url(req: URLRequest):
    """
    接收來自【首頁】的網址，抓取內文並建立 RAG 向量知識庫。
    """
    try:
        # 第一步：網頁純文字抓取
        text_content = fetch_url_content(req.url)
        if len(text_content) < 50:
             raise Exception("抓取到的內文過少，網站可能使用了動態渲染(SPA)防護或無有效文字。")
             
        # 第二步：文字切塊與向量化存庫
        chunk_count = rag_manager.process_and_store(text_content)
        
        return {
            "status": "success", 
            "message": f"成功處理網頁，知識已寫入資料庫！共切分為 {chunk_count} 個文本區塊。"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"網址處理失敗: {str(e)}")

@app.get("/api/teaching_content")
async def get_teaching_content():
    """
    為【教學分頁】提供資料。從知識庫檢索廣泛脈絡，經由 LLM 萃取成卡片內容。
    """
    try:
        # 檢索廣泛的主題相關區塊
        context = rag_manager.retrieve("這篇文章核心概念、重點與架構是什麼？", k=5)
        
        # 叫用 LLM 以 JSON 格式輸出萃取結果
        content_json_str = llm_service.extract_teaching_points(context)
        return {"status": "success", "data": content_json_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成教學內容失敗: {str(e)}")

@app.get("/api/quiz")
async def get_quiz(num: int = 5):
    """
    為【測驗分頁】提供資料。從知識庫檢索並隨機生成指定題數的單選測驗題。
    """
    try:
        # 檢索文章中的具體細節與知識點來出題
        context = rag_manager.retrieve("文章中的具體細節、專有名詞解釋、以及需要思考的問題是什麼？", k=6)
        
        quiz_json_str = llm_service.generate_quiz(context, num_questions=num)
        return {"status": "success", "data": quiz_json_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"測驗生成失敗: {str(e)}")

@app.post("/api/export_record")
async def export_record(req: ExportRequest):
    """將學習紀錄匯出成 MD，並寄送 Email (若無 SMTP 設定則回傳給前端下載)"""
    try:
        md_content = f"# 🎓 知識驗證學習紀錄\n\n"
        md_content += f"- **學習者帳號**: {req.email}\n"
        md_content += f"- **精熟度測驗得分**: {req.score} / {req.total}\n\n"
        md_content += "---\n\n## 📝 題目與解答回顧\n\n"
        
        for i, q in enumerate(req.quiz_data):
            md_content += f"### Q{i+1}: {q.get('question')}\n\n"
            ans = q.get('answer', '')
            md_content += f"> **💡 正確解答**: {ans}\n\n"
            
        # 嘗試使用 SMTP 寄信
        # 寄件帳號為使用者登入的信箱，密碼從環境變數 GMAIL_APP_PASSWORD 讀取
        sender_email = req.email
        sender_password = os.environ.get("GMAIL_APP_PASSWORD", "")
        email_sent = False
        smtp_error_msg = ""
        
        if sender_email and sender_password:
            try:
                msg = MIMEMultipart()
                msg['Subject'] = "【The Digital Archivist】您的知識驗證學習紀錄"
                msg['From'] = f"The Digital Archivist <{sender_email}>"
                msg['To'] = req.email
                
                body = "您好！感謝您使用本系統進行學習，附件是您剛剛完成的學習紀錄與全數解答，請查收。"
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # 將 MD 內容作為附件
                filename = f"learning_record_{req.email.split('@')[0]}.md"
                part = MIMEApplication(md_content.encode('utf-8'))
                part.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(part)
                
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    # 使用使用者的信箱與 16 碼應用程式密碼登入
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                
                email_sent = True
            except Exception as e:
                smtp_error_msg = str(e)
                print(f"寄信失敗: {e}")
                
        if email_sent:
            return {
                "status": "success", 
                "message": f"大成功！🎉 這份學習紀錄已透過 Gmail 以您的名義成功寄達信箱：{req.email}",
                "markdown": md_content # 保留備用下載機制
            }
        else:
            return {
                "status": "success", 
                "message": f"雖然產生了 Markdown，但寄信失敗：可能是您前台 Sign In 登入的信箱與產生密碼的 Google 帳號不同！\n\nGmail 系統報錯：{smtp_error_msg}\n\n已啟動備取方案：直接透過瀏覽器下載檔案給您。",
                "markdown": md_content
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 強制關閉靜態檔案快取機制
class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers) -> bool:
        return False
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/", NoCacheStaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # 從環境變數讀取 PORT，若無則預設為 8000
    port = int(os.environ.get("PORT", 8000))
    # 監聽 0.0.0.0 以便從容器外連線
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
