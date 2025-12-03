# #src/mcp_server/tool.py
# from __future__ import annotations

# import json
# import logging
# import re
# import urllib.parse
# import urllib.request
# from typing import Dict, List

# import requests
# from bs4 import BeautifulSoup, Tag
# from fastmcp import FastMCP
# from pydantic import BaseModel

# from config import Settings

# logger = logging.getLogger(__name__)

# class Article(BaseModel):
#     text: str
#     title: str
#     url: str

# class NewsCollectionResult(BaseModel):
#     articles: list[Article]

# class NewsCollector:
#     """네이버 뉴스 검색 및 기사 본문 추출을 담당하는 헬퍼 클래스."""

#     def __init__(self, settings: Settings) -> None:
#         if not settings.client_id or not settings.client_secret:
#             raise RuntimeError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수를 설정하세요.")
#         self.settings = settings
#         self.session = requests.Session()
#         self.session.headers.update({"User-Agent": self.settings.user_agent})

#     def fetch_naver_news_items(
#         self,
#         topic: str,
#         display: int | None = None,
#         sort: str | None = None,
#     ) -> List[Dict[str, str]]:
#         """네이버 뉴스 검색 API를 호출해 제목과 URL 목록을 돌려준다."""
#         query = urllib.parse.quote(topic)
#         display = display or self.settings.default_display
#         sort = sort or self.settings.default_sort
#         url = f"{self.settings.search_url}?query={query}&display={display}&sort={sort}"

#         request = urllib.request.Request(url)
#         request.add_header("X-Naver-Client-Id", self.settings.client_id)
#         request.add_header("X-Naver-Client-Secret", self.settings.client_secret)

#         try:
#             with urllib.request.urlopen(request, timeout=self.settings.request_timeout) as response:
#                 if response.getcode() != 200:
#                     raise RuntimeError(f"API Error Code: {response.getcode()}")
#                 payload = json.loads(response.read().decode("utf-8"))
#         except Exception as exc:
#             raise RuntimeError(f"네이버 뉴스 검색 API 호출 실패: {exc}") from exc

#         results = []
#         for item in payload.get("items", []):
#             results.append(
#                 {
#                     "title": re.sub(r"<.*?>", "", item.get("title", "")),
#                     "url": item.get("originallink") or item.get("link") or "",
#                 }
#             )
#         return results

#     def fetch_article_text(self, url: str) -> str:
#         """기사 상세 페이지에서 본문만 추출한다."""
#         if not url:
#             return ""

#         try:
#             response = self.session.get(
#                 url,
#                 timeout=self.settings.request_timeout,
#                 allow_redirects=True,
#             )
#             response.raise_for_status()
#         except requests.RequestException:
#             return ""

#         # 일부 국내 언론사는 euc-kr 등을 사용하므로 추정 인코딩을 우선 적용한다.
#         if not response.encoding or response.encoding.lower() == "iso-8859-1":
#             response.encoding = response.apparent_encoding or "utf-8"

#         soup = BeautifulSoup(response.text, "html.parser")

#         noise_selectors = (
#             "script",
#             "style",
#             "noscript",
#             "iframe",
#             "svg",
#             "form",
#             "header",
#             "footer",
#             "nav",
#             "aside",
#             "[class*='ad']",
#             "[id*='ad']",
#             ".sns",
#             ".share",
#             ".copyright",
#             ".related",
#             ".recommend",
#             ".banner",
#         )
#         for selector in noise_selectors:
#             for tag in soup.select(selector):
#                 if isinstance(tag, Tag):
#                     tag.decompose()

#         candidates = (
#             "article",
#             "#newsct_article",
#             ".newsct_article",
#             "#dic_area",
#             ".article_body",
#             "#articeBody",
#             ".news_end",
#             ".article_content",
#             "#contents",
#             "#content",
#             ".content",
#             '.layout--bg','.view_cont','.cont_view',
#             '.article_view',
#             '.sec_body',
#         )
#         for selector in candidates:
#             element = soup.select_one(selector)
#             if element:
#                 text = re.sub(r"\s+", " ", element.get_text()).strip()
#                 if text and len(text) > 200:
#                     return text

#         return " "

#     def collect_articles(self, topic: str, display: int | None = None) -> List[Dict[str, str]]:
#         """주어진 토픽을 기준으로 기사 목록과 본문을 모두 수집한다."""
#         # 요청된 display 개수가 없으면 기본 5개로 설정 (기존 3개 -> 5개로 증가)
#         count = display
#         items = self.fetch_naver_news_items(topic, display=count)
#         articles: List[Dict[str, str]] = []
#         for item in items:
#             try:
#                 text = self.fetch_article_text(item["url"])
#                 # 본문이 비어있거나 너무 짧은 경우(공백 포함 50자 미만 등)는 제외
#                 if not text or len(text.strip()) < 50:
#                     continue
                
#                 articles.append(
#                     {
#                         "title": item["title"],
#                         "url": item["url"],
#                         "text": text,
#                     }
#                 )
#             except Exception:
#                 # 개별 기사 수집 실패 시 전체 프로세스를 중단하지 않고 건너뜀
#                 continue
                
#         return articles

# def register_data_tools(mcp: FastMCP, settings: Settings) -> None:
#     """뉴스 수집 관련 도구들을 MCP에 등록합니다."""
#     collector = NewsCollector(settings)

#     @mcp.tool(
#             name="collect_news",
#             description="Collect news"
#     )
#     def collect_news(topic: str) -> NewsCollectionResult:
#         """주어진 토픽에 대해 네이버 뉴스 기사 본문을 수집합니다."""
#         try:
#             raw_articles = collector.collect_articles(topic)
#             article_models = [Article(**article) for article in raw_articles]
#         except Exception as exc:
#             logger.exception("기사 수집 또는 변환 실패", exc_info=exc)
#             article_models = []

#         logger.info("총 %d건 기사 수집 완료", len(article_models))
#         result = NewsCollectionResult(articles=article_models)
#         logger.debug("Structured payload: %s", result.model_dump(mode="json"))
#         return result


from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Dict, List

import requests
from bs4 import BeautifulSoup, Tag
from fastmcp import FastMCP
from pydantic import BaseModel

from config import Settings

logger = logging.getLogger(__name__)

class Article(BaseModel):
    text: str
    title: str
    url: str

class NewsCollectionResult(BaseModel):
    articles: list[Article]

class NewsCollector:
    """네이버 뉴스 검색 및 기사 본문 추출을 담당하는 헬퍼 클래스."""

    def __init__(self, settings: Settings) -> None:
        if not settings.client_id or not settings.client_secret:
            raise RuntimeError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수를 설정하세요.")
        self.settings = settings
        self.session = requests.Session()
        # [강화] 헤더 추가 (차단 방지)
        self.session.headers.update({
            "User-Agent": self.settings.user_agent,
            "Referer": "https://news.naver.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

    def fetch_naver_news_items(self, topic: str, display: int | None = None, sort: str | None = None) -> List[Dict[str, str]]:
        """네이버 뉴스 검색 API 호출"""
        query = urllib.parse.quote(topic)
        display = display or self.settings.default_display
        sort = sort or self.settings.default_sort
        url = f"{self.settings.search_url}?query={query}&display={display}&sort={sort}"

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", self.settings.client_id)
        request.add_header("X-Naver-Client-Secret", self.settings.client_secret)

        try:
            with urllib.request.urlopen(request, timeout=self.settings.request_timeout) as response:
                if response.getcode() != 200:
                    raise RuntimeError(f"API Error Code: {response.getcode()}")
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"네이버 뉴스 검색 API 호출 실패: {exc}") from exc

        results = []
        for item in payload.get("items", []):
            results.append({
                "title": re.sub(r"<.*?>|&quot;", "", item.get("title", "")), # HTML 엔티티 제거 강화
                "url": item.get("originallink") or item.get("link") or "",
            })
        return results

    def fetch_article_text(self, url: str) -> str:
        """기사 상세 페이지 본문 추출"""
        if not url: return ""

        try:
            response = self.session.get(url, timeout=self.settings.request_timeout, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException:
            return ""

        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"

        soup = BeautifulSoup(response.text, "html.parser")

        noise_selectors = (
            "script", "style", "noscript", "iframe", "svg", "form",
            "header", "footer", "nav", "aside", "button",
            "[class*='ad']", "[id*='ad']", ".sns", ".share", ".copyright", 
            ".related", ".recommend", ".banner", ".byline", ".reporter_area",
            ".img_desc"
        )
        for selector in noise_selectors:
            for tag in soup.select(selector):
                tag.decompose()

        candidates = (
            "#newsct_article", "#dic_area", "#articeBody", "#newsEndContents", # 스포츠 뉴스 추가
            ".newsct_article", ".article_body", ".view_cont", "article"
        )
        
        for selector in candidates:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(" ", strip=True)
                # [중요 수정] 200자 -> 50자로 완화 (짧은 기사 허용)
                if text and len(text) > 50:
                    return text
        return ""

    def collect_articles(self, topic: str, display: int | None = None) -> List[Dict[str, str]]:
        count = display or 5 # 기본값 5개로 증가
        items = self.fetch_naver_news_items(topic, display=count)
        articles: List[Dict[str, str]] = []
        
        for item in items:
            try:
                text = self.fetch_article_text(item["url"])
                # [필터링] 공백 포함 50자 미만 제외
                if not text or len(text.strip()) < 50:
                    continue
                
                articles.append({
                    "title": item["title"],
                    "url": item["url"],
                    "text": text,
                })
            except Exception:
                continue
        return articles

def register_data_tools(mcp: FastMCP, settings: Settings) -> None:
    """도구 등록"""
    collector = NewsCollector(settings)

    @mcp.tool(name="collect_news", description="주제에 대한 최신 뉴스 기사를 검색하고 본문을 수집합니다.")
    def collect_news(topic: str) -> NewsCollectionResult:
        try:
            raw_articles = collector.collect_articles(topic)
            # 최대 3개까지만 전달하여 토큰 절약 (선택 사항)
            article_models = [Article(**article) for article in raw_articles[:3]]
        except Exception as exc:
            logger.exception("기사 수집 실패", exc_info=exc)
            article_models = []

        logger.info("총 %d건 유효 기사 수집 완료", len(article_models))
        result = NewsCollectionResult(articles=article_models)
        return result