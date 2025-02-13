import os
import logging
from app.config import settings
# 로깅 설정
log_dir = os.path.dirname(settings.LOG_PATH)
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_PATH),  # 로그를 파일로 저장출력
        logging.StreamHandler(),        # 콘솔에도
    ],
)

logger = logging.getLogger(__name__)
