import requests
from bs4 import BeautifulSoup
import re

def fetch_url_content(url: str) -> str:
    """
    抓取目標網頁的純文字內容。
    過濾掉 script、style 等干擾標籤，以利於後續 RAG 處理。
    """
    try:
        # 設定基本的 Header 偽裝成瀏覽器，避免被簡單阻擋
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除不需要的標籤
        for script in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            script.decompose()
            
        # 提取文字
        text = soup.get_text(separator=' ', strip=True)
        # 清除多餘的連續空白與換行
        text = re.sub(r'\s+', ' ', text)
        return text
    except Exception as e:
        raise Exception(f"網頁內容抓取失敗: {str(e)}")
