#prompt/prompt.py

# Prompts
# # Prompts are reusable templates that help LLMs interact with your server effectively:
# Prompt는 LLM이 원하는 방식으로 입력을 받도록 도와주는 서버 내장 명령 패턴 또는 템플릿입니다.

# 단순히 문자열이 아니라 파라미터화된 템플릿 함수 형태로 제공되며, LLM 클라이언트가 서버와 대화할 때 일관된 요청/출력을 보장합니다.

# 흔히 "코드리뷰 요청", "에러 진단", "맞춤형 환영 인사" 등 일상적인 언어지침/요청문을 재활용할 때 사용합니다.

# from mcp.server.fastmcp import FastMCP
# from mcp.server.fastmcp.prompts import base

# mcp = FastMCP(name="Prompt Example")


# @mcp.prompt(title="Code Review")
# def review_code(code: str) -> str:
#     return f"Please review this code:\n\n{code}"


# @mcp.prompt(title="Debug Assistant")
# def debug_error(error: str) -> list[base.Message]:
#     return [
#         base.UserMessage("I'm seeing this error:"),
#         base.UserMessage(error),
#         base.AssistantMessage("I'll help debug that. What have you tried so far?"),
#     ]


# tool/tool.py (또는 prompt/prompt.py)
import mcp
from mcp.server.fastmcp.prompts import base
from typing import List
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

import logging
logger = logging.getLogger(__name__)
# mcp = FastMCP(name="Prompt Example")

@mcp.prompt(title="News Summarizer & Comparator")
def summarize_and_compare_news(articles_json: str) -> str:
    """
    주어진 뉴스 기사 JSON 목록을 분석하여, 각 기사의 핵심 내용을 3줄로 요약하고, 
    이 기사들 간의 관점 차이(차이점/공통점)를 3가지 이상 비교하여 반환하도록 LLM에게 지시합니다.
    
    Args:
        articles_json (str): 수집된 뉴스 기사 목록(JSON 문자열).
    """
    instruction = (
        "아래는 주어진 주제에 대해 수집된 뉴스 기사 목록(JSON)입니다.\n\n"
        "1. 각 기사의 핵심 내용을 3줄 이내로 간결하게 요약하세요.\n"
        "2. 모든 기사를 비교하여 트렌드에 대한 공통된 시각과\n"
        "   기사들 간의 관점 차이(예: A 기사는 낙관적, B 기사는 규제 강조)를 3가지 이상 분석하여 서술하세요.\n\n"
        "수집된 기사 목록:\n"
    )
    return instruction + articles_json


@mcp.prompt(title="Extract Key Entities")
def extract_entities(text: str) -> str:
    """
    주어진 텍스트에서 언급된 주요 기업, 인물, 기술 용어(엔티티)를 추출하여 
    파이썬 리스트(list[str]) 형태로만 반환하도록 LLM에게 지시합니다.
    """
    return (
        "아래 텍스트에서 주요 '기업 이름', '인물 이름', '기술 용어'를 추출하여 "
        "오직 JSON 형식의 파이썬 리스트(list[str])로만 반환하세요. 다른 설명은 포함하지 마세요:\n\n"
        f"텍스트: {text}"
    )