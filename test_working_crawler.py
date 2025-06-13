import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

def crawl_naver_sports_pc():
    """네이버 스포츠 PC 버전 크롤링"""
    print("=== 네이버 스포츠 PC 버전 테스트 ===")
    
    # 2024년 10월 15일 직접 URL
    date = datetime(2024, 10, 15)
    
    # 네이버 스포츠 KBO 일정 결과 페이지
    # URL 형식이 변경되었을 수 있으므로 여러 패턴 시도
    urls = [
        f"https://sports.news.naver.com/kbaseball/schedule/index?date={date.strftime('%Y%m%d')}",
        f"https://sports.news.naver.com/kbaseball/schedule/result?date={date.strftime('%Y%m%d')}",
        "https://sports.news.naver.com/kbaseball/schedule/index.nhn"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Referer': 'https://sports.news.naver.com/'
    }
    
    session = requests.Session()
    
    for url in urls:
        print(f"\nURL 테스트: {url}")
        
        try:
            response = session.get(url, headers=headers, timeout=10)
            print(f"상태: {response.status_code}")
            
            if response.status_code == 200:
                # HTML 저장
                with open("data/naver_sports_test.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 스크립트 태그에서 데이터 찾기
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and ('scheduleData' in script.string or 'gameData' in script.string):
                        print("JavaScript 데이터 발견!")
                        
                        # JSON 데이터 추출 시도
                        json_pattern = r'var\s+\w+\s*=\s*({[\s\S]*?});'
                        matches = re.findall(json_pattern, script.string)
                        
                        for match in matches:
                            try:
                                data = json.loads(match)
                                print(f"JSON 데이터 파싱 성공!")
                                with open("data/naver_json_data.json", "w", encoding="utf-8") as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                            except:
                                pass
                
                # HTML 구조에서 직접 찾기
                # 네이버는 여러 가지 구조를 사용할 수 있음
                selectors = [
                    # 테이블 기반
                    ('table.tb_sc tbody tr', 'table'),
                    ('div.tb_wrap table tbody tr', 'table'),
                    # 리스트 기반
                    ('ul.game_list li', 'list'),
                    ('div.game_list div.game_item', 'list'),
                    # 박스 기반
                    ('div.game_box', 'box'),
                    ('div.game_result', 'box')
                ]
                
                for selector, type_ in selectors:
                    elements = soup.select(selector)
                    if elements:
                        print(f"\n'{selector}'로 {len(elements)}개 요소 발견")
                        
                        # 첫 번째 요소 분석
                        elem = elements[0]
                        text = elem.get_text(strip=True)
                        print(f"텍스트: {text[:100]}")
                        
                        # 경기 정보 추출
                        if type_ == 'table':
                            cells = elem.find_all('td')
                            if len(cells) >= 3:
                                for cell in cells:
                                    cell_text = cell.get_text(strip=True)
                                    # 팀명과 점수 패턴
                                    if any(team in cell_text for team in ['KIA', 'LG', 'SSG', 'NC', '두산']):
                                        print(f"경기 정보 가능성: {cell_text}")
                
                return True
                
        except Exception as e:
            print(f"에러: {e}")
    
    return False

def crawl_sports_reference():
    """다른 스포츠 통계 사이트 시도"""
    print("\n=== 대체 사이트 크롤링 시도 ===")
    
    # MyKBO 등 다른 사이트들
    alternative_sites = [
        {
            'name': 'ESPN',
            'url': 'https://www.espn.com/mlb/scoreboard',
            'korean': False
        },
        {
            'name': '야구 기록실',
            'url': 'http://www.kbreport.com/schedule/main',
            'korean': True
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for site in alternative_sites:
        print(f"\n{site['name']} 테스트")
        try:
            response = requests.get(site['url'], headers=headers, timeout=10)
            print(f"상태: {response.status_code}")
            
            if response.status_code == 200 and site['korean']:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # KBO 팀 찾기
                teams = ['KIA', 'LG', 'SSG', 'NC', '두산', '삼성', 'KT', '한화', '롯데', '키움']
                found_teams = []
                
                for team in teams:
                    if team in response.text:
                        found_teams.append(team)
                
                if found_teams:
                    print(f"KBO 팀 발견: {found_teams}")
                    
                    # 점수 패턴 찾기
                    score_patterns = re.findall(r'(\d+)\s*[-:]\s*(\d+)', response.text)
                    if score_patterns:
                        print(f"점수 패턴 {len(score_patterns)}개 발견")
                    
                    return site['url']
        
        except Exception as e:
            print(f"에러: {e}")
    
    return None

def create_working_crawler():
    """작동하는 크롤러 생성"""
    print("\n=== 실제 작동하는 크롤러 구현 ===")
    
    # 지금까지 테스트 결과: 대부분의 사이트가 JavaScript 렌더링 필요
    # 또는 API가 변경되어 직접 접근 불가
    
    # 임시 해결책: 더미 데이터로 시스템 테스트
    print("현재 모든 데이터 소스가 JavaScript 렌더링을 요구하거나 API가 변경됨")
    print("Selenium with proper ChromeDriver 설정이 필요")
    
    # 작동하는 크롤러 템플릿
    template = """
# 실제 작동하는 크롤러를 위한 옵션들:

1. Selenium + ChromeDriver 수정
   - ARM64 Mac용 ChromeDriver 직접 설치
   - Docker 컨테이너로 Selenium 실행

2. Playwright 사용 (Selenium 대체)
   - 더 현대적이고 안정적
   - 자동 브라우저 다운로드

3. API 리버스 엔지니어링
   - 브라우저 개발자 도구로 실제 API 호출 캡처
   - 인증 토큰 등 필요한 헤더 파악

4. 크롤링 서비스 사용
   - ScrapingBee, Scrapy Cloud 등
   - 유료지만 안정적

5. 모바일 앱 API 분석
   - 네이버 스포츠 앱의 API 분석
   - 보통 더 간단한 구조
"""
    
    print(template)
    
    # 개발 계획 업데이트
    with open("data/crawler_analysis.txt", "w", encoding="utf-8") as f:
        f.write("""
크롤러 분석 결과 (2025-01-13)

테스트한 소스:
1. KBO 공식 API - 500 에러 (서버 문제)
2. 네이버 스포츠 API - 404 에러 (API 변경)
3. StatIz - 일정 페이지가 아닌 통계 페이지 반환
4. KBO 공식 HTML - JavaScript 렌더링 필요
5. 네이버 스포츠 HTML - JavaScript 렌더링 필요

결론:
- 모든 주요 소스가 클라이언트 사이드 렌더링 사용
- 단순 requests로는 데이터 수집 불가
- Selenium/Playwright 등 브라우저 자동화 필요

추천 방안:
1. Playwright 설치 및 구현 (가장 현대적)
2. Docker로 Selenium Grid 구성
3. 크롤링 API 서비스 사용 검토
""")
    
    print("\n분석 결과를 data/crawler_analysis.txt에 저장했습니다.")

if __name__ == "__main__":
    # 네이버 스포츠 테스트
    naver_success = crawl_naver_sports_pc()
    
    # 대체 사이트 테스트
    alt_site = crawl_sports_reference()
    
    # 결론 및 해결책
    create_working_crawler()