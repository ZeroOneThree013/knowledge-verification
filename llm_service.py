from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import json
import re

class LLMService:
    """封裝對 LLM (Gemini) 的請求，負責萃取重點與生成測驗"""
    def __init__(self):
        # 使用 Gemini 模型進行生成，注意需要設定 GOOGLE_API_KEY
        self.llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.7)
        
    async def extract_teaching_points(self, context: str) -> str:
        """從 RAG 檢索內容中萃取重點知識"""
        prompt = PromptTemplate.from_template(
            "你是一個專業的知識萃取助理。請根據以下文本內容，萃取出最重要的 3 到 5 個關鍵概念，"
            "並以繁體中文字撰寫。為了前端卡片元件顯示，請使用 JSON 陣列格式輸出：\n\n"
            "文本：\n{context}\n\n"
            "輸出必需為純 JSON 陣列格式：\n"
            "[\n"
            "  {{\"title\": \"核心概念名稱\", \"description\": \"一句話簡述重點內容\", \"details\": \"深入解析此概念在文中的脈絡與意義（約50到100字）\", \"source_quote\": \"嚴格從上方『文本』中摘錄一段最相關的原文原話作為客觀佐證\"}}\n"
            "]"
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": context})
        return self._extract_json(response.content)

    async def generate_quiz(self, context: str, num_questions: int = 5) -> str:
        """根據文本生成指定題數的單選測驗題"""
        prompt = PromptTemplate.from_template(
            "你是一個專業的測驗出題老師。請根據以下文本內容，設計 {num} 題測驗題目，"
            "題型「全部必須為單選題」。所有內容必須為繁體中文。\n\n"
            "文本：\n{context}\n\n"
            "輸出必需為純 JSON 陣列格式：\n"
            "[\n"
            "  {{\"type\": \"radio\", \"question\": \"單選題幹...\", \"options\": [\"選項1\",\"選項2\",\"選項3\",\"選項4\"], \"answer\": \"正確選項內容\"}}\n"
            "]"
        )
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": context, "num": num_questions})
        return self._extract_json(response.content)
        
    def _extract_json(self, text: str) -> str:
        """清理 LLM 的回應，確保為乾淨的 JSON 格式字串"""
        text = text.strip()
        # 移除 markdown 中的 json 標記
        text = re.sub(r"^```json", "", text, flags=re.MULTILINE)
        text = re.sub(r"^```", "", text, flags=re.MULTILINE)
        return text.strip()
