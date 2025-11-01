# server.py (최종 통합 및 리팩토링된 MCP 서버 파일)
import sys
import logging
from fastmcp import FastMCP  # FastMCP는 FastAPI 인스턴스를 제공합니다.
from dotenv import load_dotenv  # 환경 변수 로드

from config import settings


# ----------------------------------------------------------------------
# 1. 로깅 시스템 초기 설정 (MCP 베스트 프랙티스)
# ----------------------------------------------------------------------
# 💡 로깅 출력을 표준 에러(stderr)로 지정하여, stdout 통신을 방해하지 않도록 합니다.
logging.basicConfig(
    level=logging.INFO, # 기본 INFO 레벨 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr # 🚨 MCP 규정에 따라 로그를 stderr로 보냅니다.
)
# 이 시점 이전에 출력된 print()나 logging 호출은 제거되었습니다.


# ----------------------------------------------------------------------
# 2. 환경 변수 로드 및 중앙 인스턴스 생성
# ----------------------------------------------------------------------
try:
    load_dotenv()
    # print("env 파일 로드 완료.") # 🚨 print() 제거 (logging으로 대체)
except ImportError:
    pass

# 2.1. 중앙 MCP 인스턴스 생성 (단 한 번)
mcp = FastMCP("mcp-naver-news")
# logger를 mcp 객체 생성 후에 정의하여 사용할 수 있도록 합니다.
logger = logging.getLogger("mcp.server.main")


# 🚨 2.2. 중앙 인스턴스 공유 설정 (모든 기능 파일이 이 객체를 참조하도록 준비)
# sys.modules를 통해 현재 모듈의 'mcp' 객체를 다른 파일이 import 할 수 있도록 합니다.
current_module = sys.modules[__name__]
setattr(current_module, 'mcp', mcp)


# ----------------------------------------------------------------------
# 3. 기능 파일들을 import하여 기능 등록 완료
# ----------------------------------------------------------------------
# 💡 이 import 문들이 실행되면서 각 파일 내의 @mcp.resource, @mcp.tool 등이 실행되어
# 위의 중앙 'mcp' 인스턴스에 기능이 자동으로 등록됩니다.
import resource.article_extractor  # 기존 리소스 등록
import tool.tool1  # DataService 기반 뉴스 수집 툴
import prompt.prompt  # LLM 프롬프트 템플릿

logger.info("✅ 모든 MCP 기능(Resource, Tool, Prompt) 등록 완료.")


# ----------------------------------------------------------------------
# 4. 서버 구동
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if not settings.client_id or not settings.client_secret:
        logger.error("🚨 NAVER_CLIENT_ID/SECRET 환경 변수가 설정되지 않았습니다. 테스트가 실패할 수 있습니다.")
    logger.info(f"🚀 Starting MCP Server: ")
    # mcp.app은 FastMCP 인스턴스에서 노출하는 FastAPI 앱입니다.
    mcp.run(transport="stdio")
