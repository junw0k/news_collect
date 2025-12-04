# client/http_client.py
import asyncio
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai
from fastmcp import Client  # High-Level Client

# 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000/mcp")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

def prepare_summary_prompt_args(raw_args: Dict[str, Any], fallback_topic: str = None) -> Dict[str, Any]:
    pargs = dict(raw_args)
    if "topic" not in pargs and fallback_topic:
        pargs["topic"] = fallback_topic
    
    if "articles" in pargs:
        pargs["articles_blob"] = json.dumps(pargs["articles"], ensure_ascii=False, indent=2)
        del pargs["articles"]
    return pargs

async def main():
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    
    print(f"Gemini 뉴스 봇 시작 (Target: {SERVER_URL})")
    
    async with Client(SERVER_URL) as mcp_client:
        
        # [수정됨] FastMCP Client는 리스트를 바로 반환합니다.
        mcp_tools = await mcp_client.list_tools()
        
        # Gemini용 도구 스키마 변환
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

        # [수정됨] mcp_tools.tools -> mcp_tools 로 변경
        for tool in mcp_tools:
            gemini_tools[0]["function_declarations"].append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema # FastMCP 모델은 inputSchema 필드를 가짐
            })

        # --- 대화 루프 ---
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

            while response.function_calls:
                print(f"[System] Tool calls: {len(response.function_calls)}")
                history.append(response.candidates[0].content)
                
                parts = []
                for call in response.function_calls:
                    t_name = call.name
                    t_args = call.args
                    print(f"  -> Executing: {t_name}")
                    
                    try:
                        result_txt = ""
                        if t_name == "get_prompt":
                            args = prepare_summary_prompt_args(dict(t_args["args"]), last_topic)
                            res = await mcp_client.get_prompt(t_args["name"], args)
                            # FastMCP Client의 get_prompt 결과 처리
                            result_txt = res.messages[0].content.text
                        else:
                            if t_name == "collect_news":
                                last_topic = t_args.get("topic")
                            res = await mcp_client.call_tool(t_name, dict(t_args))
                            # FastMCP Client의 call_tool 결과 처리
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
                
                history.append(genai.types.Content(role="user", parts=parts))
                response = await gemini_client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=history,
                    config=genai.types.GenerateContentConfig(tools=gemini_tools)
                )

            if response.text:
                print(f"\nGemini> {response.text}\n")
                history.append(response.candidates[0].content)

        while True:
            try:
                u_in = await asyncio.to_thread(input, "User> ")
                if u_in.lower() in ("exit", "quit"): break
                if not u_in.strip(): continue
                await process_turn(u_in)
            except EOFError:
                break

if __name__ == "__main__":
    asyncio.run(main())