from __future__ import annotations

from fastmcp import FastMCP


def register_prompt_templates(mcp: FastMCP) -> None:
    """LLM이 활용할 프롬프트 템플릿을 MCP에 등록한다."""

    @mcp.prompt(title="News Summarizer & Comparator")
    def summarize_and_compare_news(articles_json: str) -> str:
        """
        수집된 기사 JSON을 LLM이 요약·비교할 수 있도록 지침을 반환한다.
        """
        instruction = (
            "아래는 특정 주제와 관련해 수집된 뉴스 기사 목록(JSON)입니다.\n\n"
            "1. 각 기사의 핵심 내용을 3줄 이내로 간결하게 요약하세요.\n"
            "2. 모든 기사를 비교하여 공통된 시각과 관점 차이를 최소 3가지 이상 분석하세요.\n\n"
            "수집된 기사 목록:\n"
        )
        return instruction + articles_json

    @mcp.prompt(title="Extract Key Entities")
    def extract_entities(text: str) -> str:
        """
        텍스트에서 주요 기업·인물·기술 용어를 추출하도록 지시한다.
        """
        return (
            "아래 텍스트에서 주요 '기업 이름', '인물 이름', '기술 용어'를 추출하여 "
            "JSON 형식의 파이썬 리스트(list[str])만 반환하세요. 다른 설명은 포함하지 마세요.\n\n"
            f"텍스트: {text}"
        )
