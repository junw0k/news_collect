import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. .env 파일에서 환경 변수 로드
load_dotenv()

# 2. API 키 설정
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except TypeError:
    print("❌ ERROR: GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")
    exit()

# 3. 사용할 모델 지정 및 생성
#    'gemini-1.5-flash' -> 'gemini-1.0-pro'로 변경!
#    이 모델은 거의 모든 계정과 지역에서 지원됩니다.
model = genai.GenerativeModel('gemini-2.5-flash') 

# 4. 콘텐츠 생성 요청
try:
    response = model.generate_content("Explain how AI works in a few words")
    
    # 5. 결과에서 텍스트 부분만 출력
    print("✅ Success!")
    print(response.text)

except Exception as e:
    # API 호출 실패 시 더 자세한 오류 메시지를 출력하도록 수정
    print(f"❌ API 호출 중 오류가 발생했습니다: {e}")