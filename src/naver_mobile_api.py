import requests
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import HEADERS, TEAM_NAMES

def test_naver_mobile_api():
    """네이버 스포츠 모바일 API 테스트"""
    
    # 2024년 10월 15일 데이터로 테스트
    test_date = "20241015"
    
    # 모바일 API 엔드포인트들
    api_urls = [
        f"https://m.sports.naver.com/kbaseball/api/game/gameListByDate?date={test_date}&leagueCode=KBO",
        f"https://m-sports.naver.com/kbaseball/api/game/gameListByDate?date={test_date}",
        f"https://api.sports.naver.com/kbaseball/schedule/daily?date={test_date}",
        f"https://m.sports.naver.com/api/kbaseball/schedule?date={test_date}",
        f"https://m-sports.naver.com/api/kbo/schedule/list?date={test_date}"
    ]
    
    # 모바일 헤더
    mobile_headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://m.sports.naver.com/kbaseball/schedule'
    }
    
    for url in api_urls:
        print(f"\n테스트 URL: {url}")
        try:
            response = requests.get(url, headers=mobile_headers)
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✓ JSON 응답 성공!")
                    
                    # 응답 구조 분석
                    if isinstance(data, dict):
                        print(f"응답 키: {list(data.keys())}")
                        
                        # 게임 리스트 찾기
                        if 'result' in data and 'games' in data['result']:
                            games = data['result']['games']
                            print(f"경기 수: {len(games)}")
                            parse_games(games)
                        elif 'games' in data:
                            games = data['games']
                            print(f"경기 수: {len(games)}")
                            parse_games(games)
                        elif 'list' in data:
                            games = data['list']
                            print(f"경기 수: {len(games)}")
                            parse_games(games)
                    
                    # 응답 저장
                    filename = url.split('/')[-1].split('?')[0]
                    with open(f'data/api_response_{filename}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    return url, data
                    
                except json.JSONDecodeError:
                    print("✗ JSON 파싱 실패")
                    
        except Exception as e:
            print(f"✗ 에러: {e}")
    
    return None, None

def parse_games(games):
    """게임 데이터 파싱"""
    if not games:
        return
        
    for i, game in enumerate(games[:2]):  # 처음 2개만 테스트
        print(f"\n경기 {i+1}:")
        
        # 다양한 키 이름으로 시도
        home_team_keys = ['homeTeamName', 'home_team', 'homeTeam', 'hTeam']
        away_team_keys = ['awayTeamName', 'away_team', 'awayTeam', 'aTeam']
        home_score_keys = ['homeTeamScore', 'home_score', 'homeScore', 'hScore']
        away_score_keys = ['awayTeamScore', 'away_score', 'awayScore', 'aScore']
        
        # 팀 이름 찾기
        home_team = None
        away_team = None
        for key in home_team_keys:
            if key in game:
                home_team = game[key]
                break
        for key in away_team_keys:
            if key in game:
                away_team = game[key]
                break
                
        # 점수 찾기
        home_score = None
        away_score = None
        for key in home_score_keys:
            if key in game:
                home_score = game[key]
                break
        for key in away_score_keys:
            if key in game:
                away_score = game[key]
                break
                
        if home_team and away_team:
            print(f"  {away_team} vs {home_team}")
        if home_score is not None and away_score is not None:
            print(f"  점수: {away_score} - {home_score}")
            
        # 기타 정보 출력
        if 'gameDate' in game:
            print(f"  날짜: {game['gameDate']}")
        if 'status' in game:
            print(f"  상태: {game['status']}")

def test_direct_api():
    """직접 API 엔드포인트 테스트"""
    
    # 2024년 정규시즌 데이터
    test_date = "20241015"
    
    # 가능한 API 패턴들
    api_patterns = [
        f"https://sports.news.naver.com/kbaseball/schedule/gameList.nhn?date={test_date}",
        f"https://api-gw.sports.naver.com/schedule/games?date={test_date}&discipline=kbaseball",
        f"https://sports.news.naver.com/ajax/main/scoreboard/todayGames.nhn?sports=kbaseball&date={test_date}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://sports.news.naver.com/kbaseball/schedule/index'
    }
    
    for url in api_patterns:
        print(f"\n테스트: {url}")
        try:
            response = requests.get(url, headers=headers)
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"Content-Type: {content_type}")
                
                if 'json' in content_type:
                    data = response.json()
                    print("✓ JSON 응답!")
                    with open(f'data/direct_api_{api_patterns.index(url)}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
        except Exception as e:
            print(f"에러: {e}")

if __name__ == "__main__":
    print("=== 네이버 모바일 API 테스트 ===")
    url, data = test_naver_mobile_api()
    
    if url:
        print(f"\n\n성공한 API: {url}")
    else:
        print("\n\n=== 직접 API 테스트 ===")
        test_direct_api()