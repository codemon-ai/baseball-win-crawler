import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

KBO_SCHEDULE_URL = "https://sports.news.naver.com/kbaseball/schedule/index"
KBO_RESULT_URL = "https://sports.news.naver.com/kbaseball/schedule/result"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

TEAM_NAMES = {
    'KIA': 'KIA',
    'LG': 'LG',
    'NC': 'NC',
    'KT': 'KT',
    'SSG': 'SSG',
    '한화': '한화',
    '롯데': '롯데',
    '삼성': '삼성',
    '두산': '두산',
    '키움': '키움'
}

SCHEDULE_TIME = "10:00"

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(LOG_DIR, f'crawler_{datetime.now().strftime("%Y%m%d")}.log')