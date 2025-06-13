import requests
from datetime import datetime, timedelta
import json

def test_kbo_api():
    """KBO 공식 API 테스트"""
    
    # 테스트할 날짜들
    test_dates = [
        datetime(2024, 10, 15),  # 2024년 10월 15일
        datetime(2024, 10, 14),  # 2024년 10월 14일
        datetime.now() - timedelta(days=1),  # 어제
    ]
    
    base_url = "https://www.koreabaseball.com"
    
    for date in test_dates:
        date_str = date.strftime('%Y%m%d')
        print(f"\n=== 테스트 날짜: {date_str} ===")
        
        # 1. Schedule API
        url = f"{base_url}/ws/Schedule.asmx/GetScheduleList"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{base_url}/Schedule/Schedule.aspx',
            'Origin': base_url,
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
        
        # 다양한 파라미터 조합 테스트
        param_sets = [
            {
                'leId': '1',  # KBO 리그
                'srId': '0,9',  # 정규시즌
                'date': date_str,
                'tmId': ''
            },
            {
                'leagueId': '1',
                'seriesId': '0',
                'gameDate': date_str,
                'teamId': ''
            },
            {
                'leId': '1',
                'srId': '0',
                'date': date_str
            }
        ]
        
        for i, params in enumerate(param_sets):
            print(f"\n파라미터 세트 {i+1}: {params}")
            
            try:
                response = requests.post(url, headers=headers, data=params, timeout=10)
                print(f"상태 코드: {response.status_code}")
                print(f"응답 헤더: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print("응답 내용 (처음 500자):")
                    print(response.text[:500])
                    
                    # JSON 파싱 시도
                    try:
                        data = response.json()
                        print(f"JSON 파싱 성공! 키: {list(data.keys())}")
                        
                        # 응답 저장
                        with open(f"data/kbo_api_test_{i}.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            
                    except json.JSONDecodeError:
                        print("JSON 파싱 실패")
                        
            except requests.exceptions.RequestException as e:
                print(f"요청 에러: {e}")
                
        # 2. 다른 가능한 엔드포인트들
        other_endpoints = [
            f"{base_url}/Schedule/Schedule.aspx",
            f"{base_url}/ws/Main.asmx/GetKboGameList",
            f"{base_url}/Game/BoxScore.aspx"
        ]
        
        print("\n=== 다른 엔드포인트 테스트 ===")
        for endpoint in other_endpoints:
            print(f"\n엔드포인트: {endpoint}")
            try:
                response = requests.get(endpoint, headers={'User-Agent': headers['User-Agent']}, timeout=10)
                print(f"상태 코드: {response.status_code}")
            except Exception as e:
                print(f"에러: {e}")

if __name__ == "__main__":
    test_kbo_api()