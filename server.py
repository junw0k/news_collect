# server.py
import uvicorn
import os
# 환경 변수 로드 (필요하다면)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP

# 1. MCP 인스턴스 생성 (단 한 번)
mcp_app = FastMCP(
    server_id="unified-news-collector",
    server_name="Unified News Collector for LLM Context",
    # 기타 설정...
)

# 2. 각 기능 파일들을 import (여기서 기능이 mcp_app에 등록됨)
#  주의: 파일들을 import하면 그 파일 내부의 @mcp.resource/@mcp.tool/@mcp.prompt 데코레이터가 실행됩니다.

from .resource.article_extractor import * # Resource 기능 등록
from .tool.tool import * # Tool 기능 등록
from .prompt.prompt import * # Prompt 기능 등록

#  위 import를 정상적으로 처리하기 위해, 
# 각 파일 내부에서는 mcp 인스턴스를 공유하거나, 
# import 시 등록되도록 구조를 맞춰야 합니다. (아래 3번 항목 참고)


# 3. 서버 구동
if __name__ == "__main__":
    print(" Starting MCP Unified Server...")
    # uvicorn.run()은 mcp_app 인스턴스에 의해 생성된 ASGI 애플리케이션을 실행합니다.
    uvicorn.run(mcp_app.app, host="0.0.0.0", port=8000)