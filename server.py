"""MCP 서버 엔트리포인트."""
#server.py
from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

from config import settings
from prompt.prompt import register_prompt_templates
from tool.tool1 import register_data_tools

def configure_logging() -> None:
    """MCP 권장 사항에 따라 stderr 로깅을 구성한다."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )


def create_server() -> FastMCP:
    """FastMCP 인스턴스를 생성하고 필요한 도구/프롬프트를 등록한다."""
    mcp = FastMCP(
        name="naver-news-collectmcp",
        instructions="네이버 뉴스 기사를 수집하고 분석하는 MCP 서버",
    )

    register_data_tools(mcp, settings)
    register_prompt_templates(mcp)

    return mcp


def main() -> None:
    """환경 변수를 로드하고 MCP 서버를 STDIO 모드로 기동한다."""
    configure_logging()
    load_dotenv()

    logger = logging.getLogger("mcp.server")
    if not settings.client_id or not settings.client_secret:
        logger.warning("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")

    mcp_server = create_server()
    logger.info("🚀 MCP Server starting in stdio mode")
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()


