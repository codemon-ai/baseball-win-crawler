"""
간단한 크롤러 테스트 - 실제로 작동하는 방법 찾기
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def test_naver_sports_simple():
    """네이버 스포츠 간단한 테스트"""
    
    print("=== 네이버 스포츠 간단한 테스트 ===")
    
    # 2024년 정규시즌 날짜
    test_dates = [
        "20240915",  # 9월 15일
        "20240820",  # 8월 20일
        "20240715",  # 7월 15일
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://sports.news.naver.com/'
    }
    
    for date_str in test_dates:
        print(f"\n날짜: {date_str}")
        
        # 다양한 URL 패턴 시도
        urls = [
            f"https://sports.news.naver.com/kbaseball/schedule/index.nhn?date={date_str}",
            f"https://sports.news.naver.com/kbaseball/schedule/index?date={date_str}",
            f"https://m.sports.naver.com/kbaseball/schedule?date={date_str}",
        ]
        
        for url in urls:
            try:
                print(f"\nURL: {url}")
                response = requests.get(url, headers=headers)
                print(f"상태: {response.status_code}")
                
                if response.status_code == 200:
                    # KBO 팀 이름 확인
                    teams = ['KIA', 'LG', 'SSG', 'NC', '두산', '삼성', 'KT', '한화', '롯데', '키움']
                    found_teams = [team for team in teams if team in response.text]
                    
                    if found_teams:
                        print(f"발견된 팀: {found_teams}")
                        
                        # HTML 파싱
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 스크립트 태그에서 데이터 찾기
                        for script in soup.find_all('script'):
                            if script.string:
                                # JSON 데이터 패턴 찾기
                                if 'gameList' in script.string or 'scheduleData' in script.string:
                                    print("JavaScript 데이터 발견!")
                                    
                                    # 간단한 JSON 추출 시도
                                    import re
                                    json_pattern = r'var\s+\w+\s*=\s*(\{[^;]+\});'
                                    matches = re.findall(json_pattern, script.string)
                                    
                                    for match in matches[:2]:
                                        try:
                                            data = json.loads(match)
                                            print(f"JSON 데이터: {list(data.keys())}")
                                        except:
                                            pass
                        
                        # 실제 작동 확인된 URL 저장
                        if found_teams:
                            return url, found_teams
                            
            except Exception as e:
                print(f"에러: {e}")
    
    return None, None

def test_api_endpoints():
    """API 엔드포인트 직접 테스트"""
    
    print("\n=== API 엔드포인트 테스트 ===")
    
    # 가능한 API 패턴들
    api_patterns = [
        "https://api-gw.sports.naver.com/v1/kbaseball/games/schedule",
        "https://api.sports.naver.com/v2/kbaseball/schedule",
        "https://sports.news.naver.com/kbaseball/api/v1/schedule",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://sports.news.naver.com/'
    }
    
    for api in api_patterns:
        print(f"\nAPI: {api}")
        try:
            # GET 요청
            response = requests.get(api, headers=headers, params={'date': '20240915'})
            print(f"GET 상태: {response.status_code}")
            
            # POST 요청
            response = requests.post(api, headers=headers, json={'date': '20240915'})
            print(f"POST 상태: {response.status_code}")
            
        except Exception as e:
            print(f"에러: {e}")

def create_simple_working_crawler():
    """실제로 작동할 수 있는 간단한 크롤러"""
    
    print("\n=== 실제 작동 가능한 방법 ===")
    
    # 방법 1: 모바일 버전 사용
    print("\n1. 모바일 버전 접근")
    mobile_headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
    }
    
    url = "https://m.sports.naver.com/kbaseball/schedule"
    response = requests.get(url, headers=mobile_headers)
    print(f"모바일 상태: {response.status_code}")
    
    # 방법 2: 캐시된 페이지 사용
    print("\n2. 구글 캐시 사용")
    cached_url = "http://webcache.googleusercontent.com/search?q=cache:https://sports.news.naver.com/kbaseball/schedule/index"
    
    # 방법 3: RSS/피드 확인
    print("\n3. RSS 피드 확인")
    rss_url = "https://sports.news.naver.com/kbaseball/rss.nhn"
    
    print("\n현재 상황:")
    print("- 모든 주요 사이트가 JavaScript 렌더링 필요")
    print("- Playwright가 최선의 선택이지만 현재 환경에서 문제 발생")
    print("- 대안: Docker 환경에서 실행 또는 GitHub Actions 사용")

if __name__ == "__main__":
    # 네이버 스포츠 테스트
    url, teams = test_naver_sports_simple()
    
    if url:
        print(f"\n작동 가능한 URL: {url}")
        print(f"발견된 팀: {teams}")
    
    # API 테스트
    test_api_endpoints()
    
    # 실제 작동 방법
    create_simple_working_crawler()