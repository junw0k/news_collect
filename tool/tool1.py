# tool/tool1.py
from __future__ import annotations

from typing import Annotated
import logging

from fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel

from config import Settings
from resource.data_service import DataService

logger = logging.getLogger(__name__)

class CollectNewsInput(BaseModel):
    topic: str

class NewsCollectionResult(BaseModel):
    articles: list[dict[str, str]]

def register_data_tools(mcp: FastMCP, settings: Settings) -> None:
    """뉴스 수집 관련 도구들을 MCP에 등록합니다."""
    service = DataService(settings)

    @mcp.tool()
    def collect_news(
        input: CollectNewsInput,
    ) -> Annotated[CallToolResult, NewsCollectionResult]:
        """주어진 토픽에 대해 네이버 뉴스 기사 본문을 수집합니다."""
        try:
            articles = service.collect_articles(input.topic)
        except Exception as exc:
            logger.error("기사 수집 실패: %s", exc)
            return CallToolResult(
                content=[TextContent(type="text", text="기사 수집 중오류가 발생했습니다.")],

                structuredContent=NewsCollectionResult(articles=[]).model_dump(),
            )

        logger.info("총 %d건 기사 수집 완료", len(articles))
        result = NewsCollectionResult(articles=articles)

        return CallToolResult(
            content=[TextContent(type="text", text=f"{len(articles)}건 기사 수집 완료")],
            structuredContent=result.model_dump(),
        )