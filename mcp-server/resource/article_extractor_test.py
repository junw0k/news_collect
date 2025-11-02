import os
import urllib.request
import urllib.parse
import json
import re
from typing import Dict, Any, Optional, List # ⬅️ List와 Dict, Optional 추가
from bs4 import BeautifulSoup, Tag
import requests

# 환경 변수에서 Client ID와 Secret을 가져옵니다. 
# (실제 실행 시 터미널에서 export 또는 .env 파일로 설정 필요)
#CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "YOUR_CLIENT_ID")
#CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
# 💡 만약 환경 변수가 아닌 파일 내의 임시 값으로 테스트하려면,
CLIENT_ID = 'CkaoiuDQTdAhLKTc0LqX'
CLIENT_SECRET = '7DqMOLcXMi'


def fetch_naver_news_items(topic: str, display: int = 3, sort: str = 'sim') -> Optional[Dict[str, Any]]:
    """
    네이버 뉴스 검색 API를 호출하여 검색 결과를 딕셔너리로 반환합니다.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: NAVER_CLIENT_ID or NAVER_CLIENT_SECRET not set.")
        return None

    # 1. API URL 및 검색어 설정
    encText = urllib.parse.quote(topic)
    # 🚨 뉴스 검색 API URL로 변경 (blog -> news)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&sort={sort}" 

    # 2. HTTP 요청 객체 생성 및 헤더 추가
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    try:
        # 3. API 호출 및 응답 처리
        with urllib.request.urlopen(request) as response:
            rescode = response.getcode()
            
            if rescode == 200:
                response_body = response.read()
                # 💡 JSON 형태로 디코딩하여 딕셔너리 반환
                return json.loads(response_body.decode('utf-8'))
            else:
                # HTTP 오류 코드 출력
                print(f"Error Code: {rescode}")
                # API 오류 응답 본문을 읽어 세부 정보 출력 시도
                error_body = response.read().decode('utf-8')
                print(f"Error Detail: {error_body}")
                return None
                
    except urllib.error.URLError as e:
        print(f"URL Error: Could not connect to API. {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# ====================================================================
# A. 크롤링 함수 (본문 추출)
# ====================================================================

def fetch_article_text(url: str) -> str:
    """
    주어진 URL에서 기사 본문을 추출합니다. (이전에 구현했던 크롤링 로직)
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (CollectorBot)'}
        # requests를 사용하여 동기 HTTP 요청
        response = requests.get(
            url, 
            headers=headers, 
            timeout=15.0, 
            allow_redirects=True
        )
        response.raise_for_status() 

    except requests.exceptions.RequestException as e:
        # print(f"[Collector] Request Error for {url}: {e}") # 디버그 출력
        return ""

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # 잡음 제거 (Script, Style, 광고, 공유 버튼 등)
    noise_selectors = [
        'script', 'style', 'noscript', 'iframe', 'svg', 'form', 'header', 
        'footer', 'nav', 'aside',
        '[class*="ad"]', '[id*="ad"]', '.sns', '.share', '.copyright', 
        '.related', '.recommend', '.banner'
    ]
    for selector in noise_selectors:
        for tag in soup.select(selector):
            if isinstance(tag, Tag):
                tag.decompose()

    # 본문 후보 선택자 (네이버 뉴스 페이지 구조에 맞춘 휴리스틱)
    candidates = [
        'article', '#newsct_article', '.newsct_article', 
        '#dic_area', '.article_body', '#articeBody', 
        '.news_end', '.article_content', '#contents', 
        '#content', '.content',
    ]

    for sel in candidates:
        element = soup.select_one(sel)
        if element:
            # 텍스트 추출 및 공백 정리
            text = re.sub(r'\s+', ' ', element.get_text()).strip()
            # 200자 이상일 경우 본문으로 인정
            if text and len(text) > 200:
                return text

    return "" # 본문을 찾지 못하거나 200자 미만일 경우 빈 문자열 반환

# ====================================================================
# B. API 호출 함수 (URL 수집)
# ====================================================================

def fetch_naver_news_items(topic: str, display: int = 3, sort: str = 'sim') -> List[Dict[str, str]]:
    """
    네이버 뉴스 검색 API를 호출하여 URL과 제목 목록을 반환합니다.
    """
    # (API 호출 로직은 이전 답변의 코드와 동일)
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: NAVER_CLIENT_ID or NAVER_CLIENT_SECRET not set.")
        return []

    encText = urllib.parse.quote(topic)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&sort={sort}" 

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    try:
        with urllib.request.urlopen(request) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                
                # 추출된 항목만 정리하여 반환
                return [
                    {
                        'title': re.sub(r'<b>|</b>', '', item.get('title', '')), # <b> 태그 제거
                        'url': item.get('originallink') or item.get('link')
                    }
                    for item in data.get('items', [])
                ]
            else:
                print(f"API Error Code: {response.getcode()}")
                return []
    except Exception as e:
        print(f"API Connection Error: {e}")
        return []

# ====================================================================
# C. 메인 실행 및 통합
# ====================================================================

if __name__ == '__main__':
    SEARCH_TOPIC = "인공지능 트렌드"
    
    print(f"1. 네이버 API로 '{SEARCH_TOPIC}' 관련 URL 5개 검색 중...")
    
    # 1. API 호출로 URL과 제목 목록 획득
    news_list = fetch_naver_news_items(SEARCH_TOPIC, display=3)

    if not news_list:
        print("검색 결과가 없거나 API 호출에 실패했습니다.")
    else:
        print(f"2. 검색된 {len(news_list)}개 기사의 본문을 크롤링 중...")
        
        # 2. 각 기사를 순회하며 본문 크롤링
        crawled_articles = []
        for i, item in enumerate(news_list):
            
            # 🚨 크롤링 함수 호출 🚨
            text = fetch_article_text(item['url']) 
            
            crawled_articles.append({
                'title': item['title'],
                'url': item['url'],
                'text': text
            })
            print(f"   -> {i+1}. '{item['title'][:20]}...' 본문 추출 완료 (길이: {len(text)})")

        # 3. 결과 출력
        print("\n" + "=" * 50)
        print(f"=== 최종 통합 결과 (주제: {SEARCH_TOPIC}) ===")
        print("=" * 50)
        
        for article in crawled_articles:
            print(f"\n[기사 제목]: {article['title']}")
            print(f"[URL]: {article['url']}")
            
            if article['text']:
                # 추출된 본문의 500자까지만 출력
                # body_preview 대신 전체 텍스트를 출력합니다.
                #body_preview = article['text'][:1000]
                #print(f"[본문 (500자 미리보기)]:\n{body_preview}...")
                print(f"[본문 (전체 내용)]:\n{article['text']}")
            else:
                print("[본문]: ❌ 크롤링 실패 또는 본문 200자 미만.")
        print("=" * 50)



