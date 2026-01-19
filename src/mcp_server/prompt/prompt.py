
from __future__ import annotations

import asyncio
from fastmcp import FastMCP
from fastmcp.prompts.prompt import PromptMessage, TextContent


def register_prompt_templates(mcp: FastMCP) -> None:
    """LLM이 활용할 프롬프트 템플릿을 MCP에 등록한다."""

    # 1. 뉴스 수집 요청 변환 (변경 없음)
    @mcp.prompt
    def news_query_prompt(query: str) -> PromptMessage:
        text = (
            "사용자가 다음 주제에 대해 최신 뉴스를 원하고 있습니다.\n"
            f"주제: {query}\n\n"
            "이 주제와 관련된 네이버 뉴스 기사를 수집하기 위해 "
            "'collect_news' MCP 도구를 호출해야 합니다.\n"
            "적절한 검색 키워드를 생성해 주세요."
        )
        return PromptMessage(role="user", content=TextContent(type="text", text=text))

    # 2. [중요 수정] JSON 데이터를 위한 요약 프롬프트
    @mcp.prompt
    def summarize_articles_prompt(topic: str, articles_blob: str) -> PromptMessage:
        """
        JSON 형태(기사 리스트)로 전달된 뉴스 기사들을 요약한다.
        """
        text = (
            f"주제 '{topic}'과 관련된 뉴스 기사 데이터가 아래에 JSON 형식으로 제공됩니다.\n"
            "제공된 JSON 데이터를 분석하여 다음 지침에 따라 요약하세요.\n\n"
            "요약 작성 지침:\n"
            "1) 각 기사의 'text'(본문) 내용을 바탕으로 5줄 이내로 핵심 요약\n"
            "2) 각 요약 끝에 '출처: <url>' 형식으로 링크 명시 ('url' 필드 활용)\n"
            "3) 모든 기사를 분석한 뒤, 공통 시사점이 있다면 마지막에 한 줄로 정리\n\n"
            "기사 데이터(JSON):\n"
            f"{articles_blob}"
        )
        return PromptMessage(role="user", content=TextContent(type="text", text=text))

    # 3. 트렌드 분석 (변경 없음 - 필요시 JSON으로 변경 권장)
    @mcp.prompt
    def analyze_trends_prompt(topic: str, articles: list[str]) -> PromptMessage:
        joined = "\n\n--- 기사 ---\n\n".join(articles)
        text = (
            f"다음은 '{topic}'과 관련된 뉴스 기사들입니다.\n"
            "기사들을 기반으로 다음 항목을 분석해 주세요:\n"
            "1) 핵심 이슈 정리\n"
            "2) 업계/사회 반응\n"
            "3) 미래 전망\n"
            "4) 잠재적 리스크\n\n"
            "**분석에 인용된 기사의 출처 링크(URL)를 포함해 주세요.**\n\n"
            f"{joined}"
        )
        return PromptMessage(role="user", content=TextContent(type="text", text=text))

    # 4. 카테고리 분류 (변경 없음)
    @mcp.prompt
    def classify_category_prompt(article: str) -> PromptMessage:
        text = (
            "다음 기사를 보고 카테고리를 한 가지 선택하세요.\n"
            "카테고리 후보: 정치, 경제, 사회, 국제, IT/과학, 문화, 스포츠\n\n"
            f"기사 내용:\n{article}\n"
        )
        return PromptMessage(role="user", content=TextContent(type="text", text=text))

    # 5. 키워드 추출 (변경 없음)
    @mcp.prompt
    def extract_keywords_prompt(article: str) -> PromptMessage:
        text = (
            "다음 기사에서 핵심 키워드 5개를 추출하고 중요도 순으로 정렬해 주세요.\n\n"
            f"{article}"
        )
        return PromptMessage(role="user", content=TextContent(type="text", text=text))

    # 6. 비동기 예시 (변경 없음)
    @mcp.prompt
    async def async_news_prompt(topic: str) -> str:
        await asyncio.sleep(0)
        return f"'{topic}'에 대해 추가 정보가 필요하다면 collect_news 도구를 호출하세요."