# 도구	모델 제어	LLM에 노출되어 
# 작업을 수행하는 기능	API 호출, 데이터 업데이트
# tool 응답받은것을 description 이쁘게 만들면 된느건가?
#tool/tool.py

# from typing import Annotated
# from pydantic import BaseModel
# from mcp.server.fastmcp import FastMCP
# from mcp.types import CallToolResult, TextContent


# from pydantic import BaseModel
# from typing import List
# from mcp.server.fastmcp import FastMCP
# from mcp.types import CallToolResult, TextContent
# from typing import Annotated
# from article_extractor import fetch_naver_news_items
# from article_extractor import fetch_article_text

# from 

# import mcp
# import logging
# logger = logging.getLogger(__name__)



# # 💡 1. 입력 모델: 검색 주제(topic)만 필요
# class CollectNewsInput(BaseModel):
#     """뉴스 기사를 검색하고 수집하기 위한 입력 파라미터."""
#     topic: str
    
# # 💡 2. 출력 모델: 수집된 기사 목록 구조 정의
# class Article(BaseModel):
#     """수집된 단일 뉴스 기사의 구조."""
#     title: str
#     url: str
#     text: str # 전체 본문 내용

# # 💡 3. 최종 출력 모델: 기사 목록을 담는 리스트
# class NewsCollectionResult(BaseModel):
#     """검색 결과로 수집된 기사 목록."""
#     articles: List[Article]



# # mcp = FastMCP("NewsCollectorToolService")

# @mcp.tool()
# def collect_news_articles(
#     # Pydantic 모델을 사용하여 입력 파라미터를 명확히 정의
#     input: CollectNewsInput
# ) -> Annotated[CallToolResult, NewsCollectionResult]:
#     """
#     주어진 주제에 대한 최신 뉴스 기사를 네이버에서 검색하고,
#     각 기사의 본문 내용을 추출하여 목록으로 반환합니다. 
#     (LLM에게 최신 컨텍스트를 제공하는 데 유용합니다.)
#     """
    
#     # 1. 네이버 API 호출 (최대 3건 등)
#     news_list = fetch_naver_news_items(input.topic, display=3)
    
#     crawled_articles = []
#     for item in news_list:
#         # 2. 각 URL을 순회하며 본문 크롤링
#         text = fetch_article_text(item['url'])
        
#         # 3. Article 모델에 맞게 데이터 정리
#         crawled_articles.append(Article(
#             title=item['title'], 
#             url=item['url'], 
#             text=text
#         ))

#     # 4. 최종 출력 모델(NewsCollectionResult)에 데이터 담기
#     result_data = NewsCollectionResult(articles=crawled_articles)

#     # 5. CallToolResult로 래핑하여 반환
#     return CallToolResult(
#         # LLM에게 읽힐 내용 (선택 사항, 주로 JSON 데이터가 전달됨)
#         content=[TextContent(type="text", text=f"총 {len(crawled_articles)}건의 기사 정보를 수집했습니다.")],
#         # 💡 Pydantic 모델을 통해 검증될 최종 데이터 (Structured Output)
#         structuredContent=result_data.model_dump(),
#     )


# class ValidationModel(BaseModel):
#     """Model for validating structured output."""

#     status: str
#     data: dict[str, int]


# @mcp.tool()
# def advanced_tool() -> CallToolResult:
#     """Return CallToolResult directly for full control including _meta field."""
#     return CallToolResult(
#         content=[TextContent(type="text", text="Response visible to the model")],
#         _meta={"hidden": "data for client applications only"},
#     )


# @mcp.tool()
# def validated_tool() -> Annotated[CallToolResult, ValidationModel]:
#     """Return CallToolResult with structured output validation."""
#     return CallToolResult(
#         content=[TextContent(type="text", text="Validated response")],
#         structuredContent={"status": "success", "data": {"result": 42}},
#         _meta={"internal": "metadata"},
#     )


# @mcp.tool()
# def empty_result_tool() -> CallToolResult:
#     """For empty results, return CallToolResult with empty content."""
#     return CallToolResult(content=[])