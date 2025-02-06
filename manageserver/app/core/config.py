"""
환경 변수 및 설정 관리
- .env 파일을 로드하여 API 키 및 설정 값 관리
"""

from dotenv import load_dotenv
import os

load_dotenv()

KAKAO_API_URL = os.getenv("KAKAO_API_URL")
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
