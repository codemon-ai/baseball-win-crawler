import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import HEADERS, TEAM_NAMES

def test_kbo_official():
    """KBO 공식 홈페이지 크롤링 테스트"""
    
    # KBO 공식 홈페이지 일정/결과
    base_url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
    
    # 어제 날짜
    yesterday = datetime.now() - timedelta(days=1)
    
    # 2024년 시즌 데이터로 테스트
    test_date = datetime(2024, 10, 15)
    
    params = {
        'seriesId': '0,9',  # 정규시즌
        'teamId': '',
        'gameMonth': test_date.strftime('%m'),
        'gameYear': test_date.year,
        'gameDate': test_date.strftime('%Y%m%d')
    }
    
    print(f"KBO 공식 홈페이지 테스트")
    print(f"URL: {base_url}")
    print(f"날짜: {test_date.strftime('%Y-%m-%d')}")
    
    try:
        response = requests.get(base_url, headers=HEADERS, params=params)
        response.encoding = 'utf-8'
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 경기 결과 찾기
            game_list = soup.find_all('li', class_='game-cont')
            print(f"\n찾은 경기 수: {len(game_list)}")
            
            results = []
            
            for game in game_list[:3]:  # 처음 3경기만 테스트
                try:
                    # 팀 정보
                    teams = game.find_all('span', class_='team')
                    if len(teams) >= 2:
                        away_team = teams[0].text.strip()
                        home_team = teams[1].text.strip()
                        
                    # 점수 정보
                    scores = game.find_all('em', class_='score')
                    if len(scores) >= 2:
                        away_score = scores[0].text.strip()
                        home_score = scores[1].text.strip()
                        
                    # 경기 상태
                    status = game.find('span', class_='state')
                    if status:
                        game_status = status.text.strip()
                    else:
                        game_status = "종료"
                        
                    result = {
                        'date': test_date.strftime('%Y-%m-%d'),
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_score': away_score,
                        'home_score': home_score,
                        'status': game_status,
                        'winner': home_team if int(home_score) > int(away_score) else away_team
                    }
                    
                    results.append(result)
                    print(f"\n경기: {away_team} vs {home_team}")
                    print(f"점수: {away_score} - {home_score}")
                    print(f"승리팀: {result['winner']}")
                    
                except Exception as e:
                    print(f"경기 파싱 에러: {e}")
                    
            # 결과 저장
            with open('data/kbo_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            # HTML 샘플 저장
            with open('data/kbo_sample.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:5000])
                
            return results
            
    except Exception as e:
        print(f"에러: {e}")
        return None

def test_statiz():
    """Statiz 사이트 테스트 (대안)"""
    url = "http://www.statiz.co.kr/schedule.php"
    
    params = {
        'year': '2024',
        'month': '10'
    }
    
    print(f"\n\nStatiz 테스트")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.encoding = 'utf-8'
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 테이블 찾기
            tables = soup.find_all('table', class_='table')
            print(f"테이블 수: {len(tables)}")
            
            # HTML 샘플 저장
            with open('data/statiz_sample.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:5000])
                
    except Exception as e:
        print(f"에러: {e}")

if __name__ == "__main__":
    print("=== KBO 공식 홈페이지 테스트 ===")
    results = test_kbo_official()
    
    if not results:
        print("\n=== 대안 사이트 테스트 ===")
        test_statiz()