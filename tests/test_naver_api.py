import requests
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup

def test_naver_sports():
    """네이버 스포츠 실제 API 찾기"""
    
    # 테스트 날짜
    test_dates = [
        datetime(2024, 10, 15),
        datetime(2024, 10, 14),
    ]
    
    for date in test_dates:
        date_str = date.strftime('%Y%m%d')
        print(f"\n=== 날짜: {date_str} ===")
        
        # 1. 네이버 스포츠 일정 페이지에서 실제 API 찾기
        base_url = "https://sports.news.naver.com/kbaseball/schedule/index"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        params = {
            'date': date_str,
            'month': date.strftime('%m'),
            'year': date.strftime('%Y')
        }
        
        try:
            # 메인 페이지 요청
            response = requests.get(base_url, headers=headers, params=params)
            print(f"메인 페이지 상태: {response.status_code}")
            
            if response.status_code == 200:
                # HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # script 태그에서 API 정보 찾기
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'scheduleData' in script.string:
                        print("스케줄 데이터 발견!")
                        print(script.string[:500])
                
                # 실제 데이터가 있는 부분 찾기
                schedule_container = soup.find('div', {'id': 'calendarWrap'})
                if schedule_container:
                    print("캘린더 래퍼 발견")
                    
                # 경기 결과 찾기
                games = soup.find_all('div', class_='game_result')
                print(f"찾은 경기 수: {len(games)}")
                
                # 2. AJAX 엔드포인트 테스트
                ajax_endpoints = [
                    f"https://sports.news.naver.com/kbaseball/schedule/gameList?date={date_str}",
                    f"https://sports.news.naver.com/kbaseball/api/game/schedule?date={date_str}",
                    f"https://api-gw.sports.naver.com/gateway/v1/kbaseball/schedule?date={date_str}",
                ]
                
                ajax_headers = headers.copy()
                ajax_headers.update({
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f'{base_url}?date={date_str}'
                })
                
                print("\n=== AJAX 엔드포인트 테스트 ===")
                for endpoint in ajax_endpoints:
                    try:
                        resp = requests.get(endpoint, headers=ajax_headers)
                        print(f"\n엔드포인트: {endpoint}")
                        print(f"상태: {resp.status_code}")
                        if resp.status_code == 200:
                            print(f"응답 크기: {len(resp.text)}")
                            # JSON 파싱 시도
                            try:
                                data = resp.json()
                                print(f"JSON 데이터 발견! 키: {list(data.keys())[:5]}")
                                with open(f"data/naver_api_response_{date_str}.json", "w", encoding="utf-8") as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                            except:
                                print("JSON 파싱 실패")
                    except Exception as e:
                        print(f"에러: {e}")
                
                # 3. HTML에서 직접 데이터 추출
                print("\n=== HTML 파싱 ===")
                # 경기 결과 테이블 찾기
                game_boxes = soup.find_all('div', class_='game_box')
                print(f"게임 박스 수: {len(game_boxes)}")
                
                for i, box in enumerate(game_boxes[:2]):  # 처음 2개만
                    try:
                        # 팀 이름
                        teams = box.find_all('span', class_='team_name')
                        if len(teams) >= 2:
                            away_team = teams[0].text.strip()
                            home_team = teams[1].text.strip()
                            print(f"\n경기 {i+1}: {away_team} vs {home_team}")
                            
                        # 점수
                        scores = box.find_all('em', class_='score')
                        if len(scores) >= 2:
                            away_score = scores[0].text.strip()
                            home_score = scores[1].text.strip()
                            print(f"점수: {away_score} - {home_score}")
                    except Exception as e:
                        print(f"파싱 에러: {e}")
                        
        except Exception as e:
            print(f"요청 에러: {e}")

def test_mobile_api():
    """모바일 API 테스트"""
    print("\n=== 모바일 API 테스트 ===")
    
    # 모바일 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Referer': 'https://m.sports.naver.com/'
    }
    
    date = datetime(2024, 10, 15)
    date_str = date.strftime('%Y%m%d')
    
    mobile_endpoints = [
        f"https://m.sports.naver.com/kbaseball/api/schedule/dailySchedule?date={date_str}",
        f"https://api.sports.naver.com/schedule/mobile/baseball/kbo?date={date_str}",
        f"https://m-sports.naver.com/api/baseball/schedule/kbo/{date_str}",
    ]
    
    for endpoint in mobile_endpoints:
        try:
            print(f"\n엔드포인트: {endpoint}")
            response = requests.get(endpoint, headers=headers)
            print(f"상태: {response.status_code}")
            if response.status_code == 200:
                print(f"응답 타입: {response.headers.get('Content-Type')}")
                print(f"응답 크기: {len(response.text)}")
        except Exception as e:
            print(f"에러: {e}")

if __name__ == "__main__":
    test_naver_sports()
    test_mobile_api()