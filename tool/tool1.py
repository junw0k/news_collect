# tool/tool1.py
from __future__ import annotations

import logging

from fastmcp import FastMCP
from pydantic import BaseModel

from config import Settings
from resource.data_service import DataService

logger = logging.getLogger(__name__)

class CollectNewsInput(BaseModel):
    topic: str

class Article(BaseModel):
    title: str
    url: str
    text: str

class NewsCollectionResult(BaseModel):
    articles: list[Article]

def register_data_tools(mcp: FastMCP, settings: Settings) -> None:
    """뉴스 수집 관련 도구들을 MCP에 등록합니다."""
    service = DataService(settings)

    @mcp.tool()
    def collect_news(input: CollectNewsInput) -> NewsCollectionResult:
        """주어진 토픽에 대해 네이버 뉴스 기사 본문을 수집합니다."""
        article_models: list[Article] = []
        try:
            raw_articles = service.collect_articles(input.topic)
            article_models = [Article(**article) for article in raw_articles]
        except Exception as exc:
            logger.exception("기사 수집 또는 변환 실패", exc_info=exc)

        logger.info("총 %d건 기사 수집 완료", len(article_models))
        result = NewsCollectionResult(articles=article_models)
        logger.debug("Structured payload: %s", result.model_dump(mode="json"))
        return result
