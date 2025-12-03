# client.py
import asyncio
import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

def create_mcp_client() -> StdioServerParameters:
    """MCP 서버 실행 파라미터"""
    return StdioServerParameters(
        command="python", # 또는 "uv", "python3" 등 환경에 맞게
        args=["src/mcp_server/server.py"],
        env=os.environ.copy(),
    )

def prepare_summary_prompt_args(raw_args: Dict[str, Any], fallback_topic: str = None) -> Dict[str, Any]:
    """JSON 데이터를 문자열로 직렬화하여 프롬프트 인자로 전달"""
    pargs = dict(raw_args)
    if "topic" not in pargs and fallback_topic:
        pargs["topic"] = fallback_topic
    
    # articles 객체를 JSON 문자열로 변환 (한글 깨짐 방지)
    if "articles" in pargs:
        pargs["articles_blob"] = json.dumps(pargs["articles"], ensure_ascii=False, indent=2)
        del pargs["articles"]
        
    return pargs

async def main():
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    server_params = create_mcp_client()
    
    print("Gemini 뉴스 봇과 대화를 시작합니다. (종료: exit)\n")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 도구 목록 로드 및 변환
            mcp_tools = await session.list_tools()
            gemini_tools = [{"function_declarations": [
                {
                    "name": "get_prompt",
                    "description": "Get a prompt template.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "args": {"type": "OBJECT"}
                        },
                        "required": ["name", "args"]
                    }
                }
            ]}]
            
            # MCP 도구들을 Gemini 포맷으로 변환 추가
            for tool in mcp_tools.tools:
                gemini_tools[0]["function_declarations"].append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                })

            history = []
            last_topic = None
            
            system_instruction = (
                "You are a helpful assistant. Use 'collect_news' to find info. "
                "Then use 'get_prompt' with name='summarize_articles_prompt' to summarize it."
            )

            async def process_turn(user_input):
                nonlocal last_topic
                history.append(genai.types.Content(role="user", parts=[genai.types.Part(text=user_input)]))
                
                print("[System] Sending to Gemini...")
                response = await gemini_client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=history,
                    config=genai.types.GenerateContentConfig(
                        temperature=0,
                        system_instruction=system_instruction,
                        tools=gemini_tools
                    )
                )

                # 도구 호출 루프 (While loop for tool use)
                while response.function_calls:
                    print(f"[System] Tool calls: {len(response.function_calls)}")
                    history.append(response.candidates[0].content) # 모델의 요청 저장
                    
                    parts = []
                    for call in response.function_calls:
                        t_name = call.name
                        t_args = call.args
                        print(f"  -> Executing: {t_name}")
                        
                        try:
                            result_txt = ""
                            if t_name == "get_prompt":
                                args = prepare_summary_prompt_args(dict(t_args["args"]), last_topic)
                                res = await session.get_prompt(t_args["name"], args)
                                result_txt = res.messages[0].content.text
                            else:
                                if t_name == "collect_news":
                                    last_topic = t_args.get("topic")
                                res = await session.call_tool(t_name, dict(t_args))
                                result_txt = res.content[0].text

                            parts.append(genai.types.Part(
                                function_response=genai.types.FunctionResponse(
                                    name=t_name, response={"result": result_txt}
                                )
                            ))
                        except Exception as e:
                            parts.append(genai.types.Part(
                                function_response=genai.types.FunctionResponse(
                                    name=t_name, response={"error": str(e)}
                                )
                            ))
                    
                    # 결과 반환 및 재요청
                    history.append(genai.types.Content(role="user", parts=parts))
                    response = await gemini_client.aio.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=history,
                        config=genai.types.GenerateContentConfig(tools=gemini_tools)
                    )

                # 최종 응답 출력
                if response.text:
                    print(f"\nGemini> {response.text}\n")
                    history.append(response.candidates[0].content)

            # 메인 입력 루프
            while True:
                u_in = await asyncio.to_thread(input, "User> ")
                if u_in.lower() in ("exit", "quit"): break
                if not u_in.strip(): continue
                await process_turn(u_in)

if __name__ == "__main__":
    asyncio.run(main())