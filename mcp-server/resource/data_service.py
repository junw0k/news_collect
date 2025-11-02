from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Dict, List

import requests
from bs4 import BeautifulSoup, Tag

from config import Settings


class DataService:
    """네이버 뉴스 검색 및 기사 본문 추출을 담당하는 서비스."""

    def __init__(self, settings: Settings) -> None:
        if not settings.client_id or not settings.client_secret:
            raise RuntimeError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수를 설정하세요.")
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.user_agent})

    def fetch_naver_news_items(
        self,
        topic: str,
        display: int | None = None,
        sort: str | None = None,
    ) -> List[Dict[str, str]]:
        """네이버 뉴스 검색 API를 호출해 제목과 URL 목록을 돌려준다."""
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
            results.append(
                {
                    "title": re.sub(r"<.*?>", "", item.get("title", "")),
                    "url": item.get("originallink") or item.get("link") or "",
                }
            )
        return results

    def fetch_article_text(self, url: str) -> str:
        """기사 상세 페이지에서 본문만 추출한다."""
        if not url:
            return ""

        try:
            response = self.session.get(
                url,
                timeout=self.settings.request_timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        noise_selectors = (
            "script",
            "style",
            "noscript",
            "iframe",
            "svg",
            "form",
            "header",
            "footer",
            "nav",
            "aside",
            "[class*='ad']",
            "[id*='ad']",
            ".sns",
            ".share",
            ".copyright",
            ".related",
            ".recommend",
            ".banner",
        )
        for selector in noise_selectors:
            for tag in soup.select(selector):
                if isinstance(tag, Tag):
                    tag.decompose()

        candidates = (
            "article",
            "#newsct_article",
            ".newsct_article",
            "#dic_area",
            ".article_body",
            "#articeBody",
            ".news_end",
            ".article_content",
            "#contents",
            "#content",
            ".content",
        )
        for selector in candidates:
            element = soup.select_one(selector)
            if element:
                text = re.sub(r"\s+", " ", element.get_text()).strip()
                if text and len(text) > 200:
                    return text

        return ""

    def collect_articles(self, topic: str, display: int | None = None) -> List[Dict[str, str]]:
        """주어진 토픽을 기준으로 기사 목록과 본문을 모두 수집한다."""
        items = self.fetch_naver_news_items(topic, display)
        articles: List[Dict[str, str]] = []
        for item in items:
            text = self.fetch_article_text(item["url"])
            articles.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "text": text,
                }
            )
        return articles

