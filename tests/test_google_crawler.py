import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.google_crawler import GoogleCrawler
from datetime import datetime

def test_google_crawler():
    """구글 크롤러 테스트"""
    
    print("=== 구글 검색 크롤러 테스트 ===")
    
    crawler = GoogleCrawler()
    
    # 1. 어제 경기 결과 테스트
    print("\n1. 어제 경기 결과 검색")
    results = crawler.run()
    
    if results:
        print(f"성공! {len(results)}개 경기 발견")
        for game in results:
            print(f"  {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")
    else:
        print("경기 결과를 찾을 수 없음")
    
    # 2. 실시간 스코어 테스트
    print("\n2. 실시간 스코어 검색")
    live_scores = crawler.get_live_scores()
    
    if live_scores:
        print(f"실시간 {len(live_scores)}개 경기 발견")
        for game in live_scores:
            status = f"{game.get('inning', '')}회" if game['status'] == '진행중' else game['status']
            print(f"  {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} ({status})")
    else:
        print("실시간 경기 없음")
    
    # 3. 특정 날짜 테스트
    print("\n3. 특정 날짜 검색 (2024-10-15)")
    test_date = datetime(2024, 10, 15)
    results = crawler.get_game_results(test_date)
    
    if results:
        print(f"{len(results)}개 경기 발견")
    else:
        print("해당 날짜 경기 결과 없음")

def test_google_search_url():
    """구글 검색 URL 직접 테스트"""
    
    print("\n=== 구글 검색 URL 테스트 ===")
    
    import requests
    from bs4 import BeautifulSoup
    
    # 실제 구글 검색 URL (제공하신 URL의 패턴)
    search_urls = [
        "https://www.google.com/search?q=KBO+경기+결과",
        "https://www.google.com/search?q=국내야구+실시간+스코어",
        "https://www.google.com/search?q=프로야구+오늘+경기"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9'
    }
    
    for url in search_urls:
        print(f"\nURL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"상태: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # KBO 팀 찾기
                teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']
                found_teams = [team for team in teams if team in response.text]
                
                if found_teams:
                    print(f"발견된 팀: {found_teams}")
                    
                    # HTML 저장 (디버깅용)
                    filename = f"data/google_search_{url.split('=')[1][:10]}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"HTML 저장: {filename}")
                    
                    # 스포츠 카드 찾기
                    sports_elements = soup.find_all(['div', 'g-card'], {'data-hveid': True})
                    print(f"스포츠 요소: {len(sports_elements)}개")
                    
                    # 점수 패턴 찾기
                    import re
                    score_patterns = re.findall(r'(\d+)\s*[-:]\s*(\d+)', response.text)
                    print(f"점수 패턴: {len(score_patterns)}개 발견")
                    
        except Exception as e:
            print(f"에러: {e}")

if __name__ == "__main__":
    # 구글 크롤러 테스트
    test_google_crawler()
    
    # URL 직접 테스트
    test_google_search_url()