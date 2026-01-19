# Naver News MCP

FastMCP 서버가 네이버 뉴스 검색 API와 직접 통신해 기사 본문을 수집하고, Gemini 등 MCP 호환 LLM이 해당 도구와 프롬프트를 활용해 요약·분석하도록 돕는 프로젝트입니다.


## 필요 조건
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker / Kubernetes (선택)
- Naver Developers Open API 계정 (뉴스 검색)
- Google AI Studio 계정 및 `GEMINI_API_KEY`

## 시작하기 (Quick Start)

가장 먼저 환경 변수 파일을 설정해야 합니다.

1.  예시 파일을 복사하여 `.env` 파일을 생성합니다.
    ```bash
    cp .env.example .env
    ```
2.  생성된 `.env` 파일을 열어 API 키를 입력합니다.
    ```ini
    NAVER_CLIENT_ID="여기에 네이버 클라이언트 ID를 입력하세요"
    NAVER_CLIENT_SECRET="여기에 네이버 클라이언트 시크릿을 입력하세요"

    # Gemini API 키 (Google AI Studio에서 발급)
    GEMINI_API_KEY="여기에 Gemini API 키를 입력하세요"

    # MCP 서버 URL (클라이언트가 접속할 주소)
    # Docker Compose 환경에서는 아래 주소를 그대로
    MCP_SERVER_URL="http://mcp-server:8000/"
    ```
    *Docker 실행 시 이 파일이 자동으로 컨테이너에 적용됩니다.*

## 로컬 설치
```bash
uv sync                      # 서버/공통 의존성 설치
uv pip install google-genai  # Gemini 클라이언트 전용 추가 패키지
source .venv/bin/activate    # 또는 uv run 사용
```

## MCP 서버 실행
```bash
uv run --env-file .env python src/mcp_server/server.py
```

서버는 `collect_news` MCP 도구를 노출합니다. 입력 `topic`(예: “AI 반도체”)을 받으면 네이버 뉴스 검색 → 기사 본문 크롤링 → `title`, `url`, `text`를 포함한 JSON을 반환합니다.

다음과 같은 프롬프트 템플릿도 함께 제공합니다.
- `news_query_prompt`
- `summarize_articles_prompt`
- `analyze_trends_prompt`
- `classify_category_prompt`
- `extract_keywords_prompt`
- `async_news_prompt`



## 문제 해결
- `NAVER_CLIENT_ID/SECRET` 미설정 시 서버 시작 단계에서 예외가 발생합니다.
- 네이버 API 에러나 403/429가 반복되면 호출 제한과 `default_display` 값을 점검하세요.
- Gemini 응답이 비어 있으면 Google AI Studio 쿼터, 모델 지원 지역, 프롬프트 크기를 확인하세요.

## Kubernetes 배포 (Deployment)

Docker Compose 대신 Kubernetes(k8s) 환경에서 배포하려면 다음 절차를 따르세요.

### 1. 사전 준비
- `aI-news.yaml` 파일 다운로드
- `.env` 파일 생성 (API 키 설정)

### 2. Secret 생성
`.env` 파일의 내용을 바탕으로 Kubernetes Secret을 생성합니다.
```bash
kubectl create secret generic mcp-secrets --from-env-file=.env
```
생성된 Secret 확인:
```bash
kubectl get secrets
```


env 파일은 다음과같이 구성
# 네이버 API 키 (네이버 개발자 센터에서 발급)
NAVER_CLIENT_ID="여기에 네이버 클라이언트 ID를 입력하세요"
NAVER_CLIENT_SECRET="여기에 네이버 클라이언트 시크릿을 입력하세요"

# Gemini API 키 (Google AI Studio에서 발급)
GEMINI_API_KEY="여기에 Gemini API 키를 입력하세요"

# MCP 서버 URL (클라이언트가 접속할 주소)
# Docker Compose 환경에서는 아래 주소를 그대로
MCP_SERVER_URL="http://mcp-server:8000/"





### 3. 리소스 배포
Pod, Service, Deployment 등을 생성합니다.
```bash
kubectl apply -f aI-news.yaml
```

### 4. 클라이언트 접속
생성된 `mcp-client` Pod에 접속하여 프로그램을 실행합니다.
```bash
kubectl exec -it mcp-client -- python client/client.py
```

