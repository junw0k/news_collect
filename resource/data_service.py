# services/data_service.py
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Dict, List
import requests
from bs4 import BeautifulSoup, Tag

from config import settings

class DataService:
    """네이버 뉴스 API 검색과 기사 본문 크롤링을 담당하는 서비스입
니다."""

    def __init__(self) -> None:
        # API 호출에 필요한 인증값이 없는 경우를 대비해 비어 있으면 바로 확인합니다.
        if not settings.client_id or not settings.client_secret:
            raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET환경 변수 설정이 필요합니다.")

    def fetch_naver_news_items(self, topic: str, display: int | None = None, sort: str | 
                               None = None) -> List[Dict[str, str]]:
        """네이버 뉴스 검색 API를 호출해 제목/URL 목록을 반환합니다."""
        query = urllib.parse.quote(topic)
        display = display or settings.default_display
        sort = sort or settings.default_sort
        url = f"{settings.search_url}?query={query}&display={display}&sort={sort}"

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", settings.client_id)
        request.add_header("X-Naver-Client-Secret",settings.client_secret)

        try:
            with urllib.request.urlopen(request, timeout=settings.request_timeout) as response:
                if response.getcode() != 200:
                    raise RuntimeError(f"API Error Code: {response.getcode()}")

                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"네이버 뉴스 검색 API 호출 실패: {exc}") from exc

        # API 응답에서 필요한 필드만 추려서 반환합니다.
        results = []
        for item in payload.get("items", []):
            results.append(
                {
                    "title": re.sub(r"<.*?>", "", item.get("title","")),#<b> 태그 제거
                    "url": item.get("originallink") or item.get("link") or "",
                }
            )
        return results

    def fetch_article_text(self, url: str) -> str:
        """기사 상세 페이지에서 본문만 추출합니다."""
        if not url:
            return ""

        try:
            response = requests.get(
                url,
                headers={"User-Agent": settings.user_agent},
                timeout=settings.request_timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException:
            return ""

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 광고/공유 버튼 등 불필요한 요소를 제거합니다.
        noise_selectors = (
            "script", "style", "noscript", "iframe", "svg", "form",
            "header", "footer", "nav", "aside",
            "[class*='ad']", "[id*='ad']", ".sns", ".share",
            ".copyright", ".related", ".recommend", ".banner",
        )
        for selector in noise_selectors:
            for tag in soup.select(selector):
                if isinstance(tag, Tag):
                    tag.decompose()

        # 네이버 기사 본문에 자주 사용되는 선택자를 순회하며 텍스트를 찾습니다.
        candidates = (
            "article", "#newsct_article", ".newsct_article",
            "#dic_area", ".article_body", "#articeBody",
            ".news_end", ".article_content", "#contents",
            "#content", ".content",
        )
        for selector in candidates:
            element = soup.select_one(selector)
            if element:
                text = re.sub(r"\s+", " ", element.get_text()).strip()
                if text and len(text) > 200:  # 충분한 길이의 본문 만을 인정.
                    return text

        return ""
# 싱글톤처럼 바로 가져다 쓸 수 있도록 인스턴스를 만들어 둡니다.

data_service = DataService()