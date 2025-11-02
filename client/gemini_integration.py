from __future__ import annotations

import asyncio
import os
from typing import Optional

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from google import genai

load_dotenv()

# MCP 서버 접속 정보 (.env 우선, 없으면 로컬 HTTP 기본값 사용)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")

# Gemini API 키는 필수
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY 환경 변수가 필요합니다.")


def create_mcp_client() -> Client:
    """MCP HTTP 엔드포인트에 연결하는 클라이언트를 생성한다."""
    auth: Optional[BearerAuth] = None
    if MCP_ACCESS_TOKEN:
        auth = BearerAuth(MCP_ACCESS_TOKEN)
    return Client(MCP_SERVER_URL, auth=auth)


async def ask_gemini(prompt: str) -> str:
    """Gemini에 MCP 도구 사용을 지시하고 응답 텍스트를 반환한다."""
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    mcp_client = create_mcp_client()

    async with mcp_client:
        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0,
                tools=[mcp_client.session],
            ),
        )
    return response.text


async def main() -> None:
    """터미널에서 대화형으로 Gemini + MCP 도구 사용을 수행한다."""
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    mcp_client = create_mcp_client()
    history: list[genai.types.Content] = []

    print("Gemini와 대화를 시작합니다. 대화를 종료하려면 'exit' 또는 'quit'을 입력하세요.\n")

    async with mcp_client:
        while True:
            user_input = await asyncio.to_thread(input, "사용자> ")
            stripped = user_input.strip()
            if stripped.lower() in {"exit", "quit"}:
                print("대화를 종료합니다.")
                break
            if not stripped:
                continue

            history.append(
                genai.types.Content(
                    role="user",
                    parts=[genai.types.Part(text=stripped)],
                )
            )

            response = await gemini_client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=history,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[mcp_client.session],
                ),
            )

            assistant_text = (response.text or "").strip()
            if not assistant_text:
                assistant_text = "[응답 텍스트가 비어 있습니다. response.candidates를 확인하세요.]"

            history.append(
                genai.types.Content(
                    role="model",
                    parts=[genai.types.Part(text=assistant_text)],
                )
            )

            print(f"Gemini> {assistant_text}\n")


if __name__ == "__main__":
    asyncio.run(main())
