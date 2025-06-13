import requests
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import HEADERS

def test_api():
    """네이버 스포츠 API 엔드포인트 테스트"""
    
    # 가능한 API 엔드포인트들
    api_endpoints = [
        # 일정/결과 API
        "https://api.sports.naver.com/v1/schedule/kbaseball",
        "https://sports.news.naver.com/kbaseball/api/schedule/result",
        "https://api-gw.sports.naver.com/gateway/schedule/games/list",
        
        # 모바일 API
        "https://m.sports.naver.com/api/kbaseball/schedule",
        
        # 날짜별 경기 결과
        "https://sports.news.naver.com/ajax/schedule/games/list.nhn"
    ]
    
    # 테스트할 날짜 (어제)
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y%m%d")
    
    for endpoint in api_endpoints:
        print(f"\n테스트 엔드포인트: {endpoint}")
        
        # 다양한 파라미터 조합 테스트
        params_list = [
            {"date": date_str, "sport": "kbaseball"},
            {"date": date_str, "leagueCode": "KBO"},
            {"gameDate": date_str, "sport": "KBASEBALL"},
            {"date": date_str}
        ]
        
        for params in params_list:
            try:
                response = requests.get(endpoint, headers=HEADERS, params=params)
                print(f"  파라미터: {params}")
                print(f"  상태 코드: {response.status_code}")
                
                if response.status_code == 200:
                    print("  ✓ 성공!")
                    # JSON 응답인지 확인
                    try:
                        data = response.json()
                        print(f"  응답 타입: JSON")
                        print(f"  응답 키: {list(data.keys())[:5]}")
                        
                        # 응답 저장
                        with open(f"data/api_response_{endpoint.split('/')[-1]}.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        return endpoint, params
                    except:
                        print(f"  응답 타입: HTML/기타")
                        
            except Exception as e:
                print(f"  에러: {e}")
    
    return None, None

def test_specific_api():
    """특정 API 상세 테스트"""
    # 2024년 10월 데이터로 테스트
    test_date = "20241015"
    
    # 가장 가능성 높은 API
    url = "https://sports.news.naver.com/kbaseball/schedule/index.nhn"
    
    print(f"상세 테스트 URL: {url}")
    print(f"테스트 날짜: {test_date}")
    
    # 네트워크 개발자 도구에서 확인한 실제 요청 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://sports.news.naver.com/kbaseball/schedule/index.nhn'
    }
    
    params = {
        'date': test_date,
        'month': test_date[4:6],
        'year': test_date[:4],
        'teamCode': ''
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"상태 코드: {response.status_code}")
        print(f"응답 크기: {len(response.text)} bytes")
        
        # 응답 저장
        with open("data/detailed_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)
            
    except Exception as e:
        print(f"에러: {e}")

if __name__ == "__main__":
    print("=== API 엔드포인트 테스트 ===")
    endpoint, params = test_api()
    
    if endpoint:
        print(f"\n\n성공한 엔드포인트: {endpoint}")
        print(f"파라미터: {params}")
    else:
        print("\n\n=== 상세 API 테스트 ===")
        test_specific_api()