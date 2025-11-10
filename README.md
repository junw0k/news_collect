# Naver News MCP

FastMCP 서버가 네이버 뉴스 검색 API와 직접 통신해 기사 본문을 수집하고, Gemini 등 MCP 호환 LLM이 해당 도구와 프롬프트를 활용해 요약·분석하도록 돕는 프로젝트입니다.


## 필요 조건
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker / Docker Compose (선택)
- Naver Developers Open API 계정 (뉴스 검색)
- Google AI Studio 계정 및 `GEMINI_API_KEY`

## 환경 변수 (.env 예시)
`.env` 파일을 리포지토리 루트에 생성하고 아래 값을 채워 주세요.

```dotenv
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
GEMINI_API_KEY=your_google_gemini_api_key

# 선택 항목
MCP_SERVER_URL=http://127.0.0.1:8000/
MCP_ACCESS_TOKEN=
```

## 로컬 설치
```bash
uv sync                      # 서버/공통 의존성 설치
uv pip install google-genai  # Gemini 클라이언트 전용 추가 패키지
source .venv/bin/activate    # 또는 uv run 사용
```

## MCP 서버 실행
```bash
uv run --env-file .env python mcp-server/server.py
```

서버는 `collect_news` MCP 도구를 노출합니다. 입력 `topic`(예: “AI 반도체”)을 받으면 네이버 뉴스 검색 → 기사 본문 크롤링 → `title`, `url`, `text`를 포함한 JSON을 반환합니다.

또한 다음 프롬프트 템플릿을 제공합니다.
- `News Summarizer & Comparator`: 기사 다건 요약 + 관점 비교
- `Extract Key Entities`: 기업/인물/기술 키워드 추출

## Gemini CLI 실행
서버가 기동 중일 때:

```bash
uv run --env-file .env python client/gemini_integration.py
```

프롬프트를 입력하면 Gemini 2.5 Flash가 MCP 세션을 통해 도구/프롬프트를 호출할 수 있습니다. `exit`/`quit`으로 종료합니다.

## Docker Compose
```bash
docker compose up --build
```
- `mcp-server`: 포트 `8000`에서 FastMCP HTTP 서버 실행
- `client`: 인터랙티브 Gemini 터미널



```json
{
  "clients": [
    {
      "name": "naver-news",
      "command": "uv",
      "args": ["run", "--env-file", ".env", "python", "mcp-server/server.py"],
      "env": {}
    }
  ]
}
```


```bash
uv run --env-file .env python test/test_gemini.py
```

## 문제 해결
- `NAVER_CLIENT_ID/SECRET` 미설정 시 서버 시작 단계에서 예외가 발생합니다.
- 네이버 API 에러나 403/429가 반복되면 호출 제한과 `default_display` 값을 점검하세요.
- Gemini 응답이 비어 있으면 Google AI Studio 쿼터, 모델 지원 지역, 프롬프트 크기를 확인하세요.
