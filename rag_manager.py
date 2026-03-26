from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

class RAGManager:
    """提供切塊(Chunking)、向量化與儲存檢索(Retrieval)的核心功能"""
    def __init__(self, persist_directory="./vector_db"):
        # 預設使用 Google Gemini 的 Embedding 模型
        # 需要環境變數設定 GOOGLE_API_KEY
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.persist_directory = persist_directory
        self.db = None
        
    def process_and_store(self, text: str):
        """將爬取後的長文本進行切塊，並存入 Chroma 向量資料庫"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        
        import shutil
        
        # 清除舊的資料庫資料夾，確保每次處理新連結時不會混雜上一次(舊)的知識內容
        if os.path.exists(self.persist_directory):
            try:
                shutil.rmtree(self.persist_directory)
            except Exception as e:
                print(f"Warning: could not delete old vector db directory: {e}")
                
        self.db = None
        
        # 使用 Chroma 建立全新的本地知識庫
        self.db = Chroma.from_texts(
            texts=chunks, 
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        # 持久化儲存
        self.db.persist()
        return len(chunks)
        
    def retrieve(self, query: str, k: int = 4) -> str:
        """根據查詢語句檢索最相關的 k 個文本區塊"""
        if not self.db:
            # 嘗試讀取本地既有的資料庫
            if os.path.exists(self.persist_directory):
                self.db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            else:
                return "知識庫尚無資料，請先提供網址處理。"
                
        # 執行相似度搜尋
        docs = self.db.similarity_search(query, k=k)
        
        # 提取內文並串接返回
        return "\n\n".join([doc.page_content for doc in docs])
