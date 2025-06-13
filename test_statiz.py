import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

def test_statiz():
    """StatIz 사이트 크롤링 테스트"""
    
    print("=== StatIz 사이트 테스트 ===")
    
    # 테스트 날짜들
    test_dates = [
        datetime(2024, 10, 15),
        datetime(2024, 10, 14),
        datetime(2024, 10, 13),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    for date in test_dates:
        year = date.year
        month = date.month
        day = date.day
        
        print(f"\n날짜: {date.strftime('%Y-%m-%d')}")
        
        # StatIz URL
        url = f"http://www.statiz.co.kr/schedule.php?year={year}&month={month:02d}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 일정 테이블 찾기
                schedule_table = soup.find('table', {'class': 'table'})
                if not schedule_table:
                    schedule_table = soup.find('table')
                
                if schedule_table:
                    print("일정 테이블 발견!")
                    
                    # 날짜 형식
                    date_str = f"{month:02d}.{day:02d}"
                    alt_date_str = f"{month}.{day}"
                    
                    games_found = []
                    
                    # 모든 행 검색
                    rows = schedule_table.find_all('tr')
                    for row in rows:
                        row_text = row.get_text()
                        
                        # 해당 날짜 찾기
                        if date_str in row_text or alt_date_str in row_text:
                            cells = row.find_all('td')
                            
                            if len(cells) >= 3:
                                # 경기 정보 파싱
                                for i, cell in enumerate(cells):
                                    cell_text = cell.get_text(strip=True)
                                    
                                    # 점수 패턴 찾기 (예: "KIA 5-3 LG")
                                    if '-' in cell_text and any(team in cell_text for team in ['KIA', 'LG', 'SSG', 'NC', '두산', '삼성', 'KT', '한화', '롯데', '키움']):
                                        try:
                                            # 팀과 점수 분리
                                            parts = cell_text.split()
                                            if len(parts) >= 3:
                                                away_team = parts[0]
                                                score_parts = parts[1].split('-')
                                                home_team = parts[2] if len(parts) > 2 else ''
                                                
                                                if len(score_parts) == 2:
                                                    away_score = int(score_parts[0])
                                                    home_score = int(score_parts[1])
                                                    
                                                    game_info = {
                                                        'date': date.strftime('%Y-%m-%d'),
                                                        'away_team': away_team,
                                                        'home_team': home_team,
                                                        'away_score': away_score,
                                                        'home_score': home_score,
                                                        'winner': away_team if away_score > home_score else home_team
                                                    }
                                                    
                                                    games_found.append(game_info)
                                                    print(f"경기 발견: {away_team} {away_score} - {home_score} {home_team}")
                                                    
                                        except Exception as e:
                                            continue
                    
                    if games_found:
                        print(f"총 {len(games_found)}개 경기 발견")
                        
                        # 결과 저장
                        filename = f"data/statiz_games_{date.strftime('%Y%m%d')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(games_found, f, ensure_ascii=False, indent=2)
                        print(f"결과 저장: {filename}")
                    else:
                        print("해당 날짜의 경기를 찾을 수 없음")
                        
                        # HTML 일부 출력하여 구조 확인
                        print("\n테이블 구조 샘플:")
                        sample_rows = rows[:5] if len(rows) > 5 else rows
                        for row in sample_rows:
                            print(f"행: {row.get_text(strip=True)[:100]}")
                else:
                    print("일정 테이블을 찾을 수 없음")
                    
                    # 페이지 구조 확인
                    print("\n페이지 구조 확인:")
                    tables = soup.find_all('table')
                    print(f"테이블 개수: {len(tables)}")
                    
                    # 다른 가능한 선택자들
                    selectors = [
                        'div.schedule',
                        'div#schedule',
                        'div[class*="schedule"]',
                        'table[class*="schedule"]'
                    ]
                    
                    for selector in selectors:
                        elements = soup.select(selector)
                        if elements:
                            print(f"선택자 '{selector}'로 {len(elements)}개 요소 발견")
                
        except Exception as e:
            print(f"에러: {e}")
            import traceback
            traceback.print_exc()

def test_alternative_sites():
    """다른 대안 사이트들 테스트"""
    
    print("\n=== 대안 사이트 테스트 ===")
    
    # 다른 가능한 야구 통계 사이트들
    sites = [
        {
            'name': 'KBO 공식 (다른 방식)',
            'url': 'https://www.koreabaseball.com/Schedule/Schedule.aspx',
            'method': 'GET'
        },
        {
            'name': '스포츠투아이',
            'url': 'https://www.sports2i.com/baseball/kbo/schedule',
            'method': 'GET'
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    for site in sites:
        print(f"\n테스트: {site['name']}")
        try:
            response = requests.request(site['method'], site['url'], headers=headers, timeout=10)
            print(f"상태 코드: {response.status_code}")
            print(f"응답 크기: {len(response.text)} bytes")
            
            if response.status_code == 200:
                # 경기 관련 키워드 확인
                keywords = ['KIA', 'LG', 'SSG', '두산', '경기', 'score', 'game']
                found_keywords = [kw for kw in keywords if kw in response.text]
                print(f"발견된 키워드: {found_keywords}")
                
        except Exception as e:
            print(f"에러: {e}")

if __name__ == "__main__":
    test_statiz()
    test_alternative_sites()