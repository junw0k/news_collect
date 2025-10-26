import os
import requests
import re
from typing import Optional
from bs4 import BeautifulSoup, Tag
from modelcontextprotocol.server.fastmcp import FastMCP # MCP 서버 SDK
from modelcontextprotocol.resource import resource # @resource 데코레이터 import

# ----------------------------------------------------------------------
# 환경 변수 로드
# ----------------------------------------------------------------------
# os.environ.get으로 환경 변수에서 값을 가져오고, 없으면 임시 값 ('YOUR_NAVER_ID')을 사용합니다.
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID', 'YOUR_NAVER_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', 'YOUR_NAVER_SECRET')

# 실제 네이버 뉴스 기사 URL의 기본 경로를 사용합니다. 
# (API 주소인 https://openapi.naver.com... 대신 실제 기사 주소를 사용)
NAVER_ARTICLE_BASE_URL = "https://n.news.naver.com/mnews/article/"

# ----------------------------------------------------------------------
# 1. MCP 서버 인스턴스 생성
# ----------------------------------------------------------------------
# FastMCP는 FastAPI 기반으로 서버를 초기화하며, 리소스를 노출합니다.
# mcp = FastMCP(
#     server_id="naver-news-extractor", 
#     server_name="Naver News Extractor"
# )


# ----------------------------------------------------------------------
# 2. 기사 본문 추출 핵심 로직 (동기 크롤러)
# ----------------------------------------------------------------------
def _crawl_article_by_url(url: str) -> str:
    """단일 URL에서 HTML을 가져와 본문을 추출하는 핵심 로직 (동기)"""
    try:
        # User-Agent 설정
        headers = {'User-Agent': 'Mozilla/5.0 (McpResourceBot)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 🚨 잡음 제거 (Node.js 코드와 동일)
        noise_selectors = [
            'script', 'style', 'noscript', 'iframe', 'svg', 'form', 'header', 
            'footer', 'nav', 'aside', '[class*="ad"]', '[id*="ad"]', '.sns', 
            '.share', '.copyright', '.related', '.recommend', '.banner'
        ]
        for selector in noise_selectors:
            for tag in soup.select(selector):
                if isinstance(tag, Tag):
                    tag.decompose()
        
        # 🚨 본문 후보 선택자 (Node.js 코드와 동일한 휴리스틱)
        candidates = [
            'article', '#newsct_article', '.newsct_article', '#dic_area', 
            '.article_body', '#articeBody', '.news_end', '.article_content', 
            '#contents', '#content', '.content',
        ]
        
        for sel in candidates:
            element = soup.select_one(sel)
            if element:
                text = re.sub(r'\s+', ' ', element.get_text()).strip()
                if text and len(text) > 200: # 200자 이상 휴리스틱
                    return text
        
        # 최종적으로 body 전체에서 추출 (Fallback)
        body_text = soup.body.get_text() if soup.body else ""
        return re.sub(r'\s+', ' ', body_text).strip()

    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return ""

# ----------------------------------------------------------------------
# 3. MCP Resource 정의
# ----------------------------------------------------------------------
@resource("news://naver/{news_id}/{company_code}")
def get_news_article(news_id: str, company_code: str = '001') -> str:
    """
    네이버 기사 ID와 언론사 코드를 기반으로 기사 본문 텍스트(컨텍스트)를 가져오는 MCP Resource.
    
    Args:
        news_id (str): 네이버 기사 고유 ID (예: 0001099688).
        company_code (str): 언론사 코드 (예: 001).
        
    Returns:
        str: 정제된 기사 본문 텍스트.
    """
    
    # 🚨 API 호출 대신, ID와 코드를 사용하여 실제 기사 URL을 구성합니다.
    # (Node.js 원본 코드의 크롤링 대상 URL 포맷)
    article_url = f"{NAVER_ARTICLE_BASE_URL}{company_code}/{news_id}" 

    # 동기 함수를 호출하여 본문 크롤링
    article_content = _crawl_article_by_url(article_url)
    
    if not article_content:
        # 본문을 찾지 못하거나 오류가 발생하면 빈 문자열 반환 
        return "" 
    
    return article_content


# ----------------------------------------------------------------------
# 4. 서버 실행
# ----------------------------------------------------------------------
# 이 코드는 uvicorn을 사용하여 MCP 서버를 구동합니다.
if __name__ == "__main__":
    import uvicorn
    # .env 파일에서 환경 변수를 로드하도록 설정 (python-dotenv 라이브러리 필요)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env 파일 로드 완료.")
    except ImportError:
        print("⚠️ python-dotenv 라이브러리가 없습니다. 환경 변수가 직접 설정되었는지 확인하세요.")

    print(f"🚀 Starting MCP Server: {mcp.server_name}")
    # uvicorn은 mcp.app (FastAPI 인스턴스)를 실행합니다.
    uvicorn.run(mcp.app, host="0.0.0.0", port=8000)