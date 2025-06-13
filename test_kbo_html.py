import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

def test_kbo_html_parsing():
    """KBO 공식 사이트 HTML 직접 파싱"""
    
    print("=== KBO 공식 사이트 HTML 파싱 테스트 ===")
    
    # 세션 사용 (쿠키 유지)
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    # 테스트할 날짜들
    test_dates = [
        datetime(2024, 10, 15),
        datetime(2024, 10, 14),
        datetime(2024, 9, 15),  # 정규 시즌
    ]
    
    for date in test_dates:
        print(f"\n날짜: {date.strftime('%Y-%m-%d')}")
        
        # 연, 월 파라미터
        year = date.year
        month = date.month
        
        # KBO 일정 페이지 URL
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
        
        # GET 파라미터
        params = {
            'seriesId': '0',  # 정규시즌
            'year': str(year),
            'month': f'{month:02d}'
        }
        
        try:
            response = session.get(url, headers=headers, params=params, timeout=10)
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                # HTML 저장 (디버깅용)
                with open(f"data/kbo_html_{date.strftime('%Y%m')}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 일정 테이블 찾기 - 다양한 선택자 시도
                schedule_selectors = [
                    'table.tbl',
                    'table#tblSchedule',
                    'div.schedule_wrap table',
                    'div.sch_tb table',
                    'table[summary*="경기일정"]'
                ]
                
                schedule_table = None
                for selector in schedule_selectors:
                    schedule_table = soup.select_one(selector)
                    if schedule_table:
                        print(f"테이블 발견: {selector}")
                        break
                
                if not schedule_table:
                    # 모든 테이블 확인
                    all_tables = soup.find_all('table')
                    print(f"페이지의 테이블 개수: {len(all_tables)}")
                    
                    # 첫 번째 테이블 구조 확인
                    if all_tables:
                        first_table = all_tables[0]
                        print(f"첫 번째 테이블 클래스: {first_table.get('class')}")
                        print(f"첫 번째 행: {first_table.get_text()[:200]}")
                
                # 날짜별 경기 찾기
                date_str = f"{date.day}"  # 일자만
                games_found = []
                
                # 모든 td 요소 검색
                all_cells = soup.find_all('td')
                
                for i, cell in enumerate(all_cells):
                    cell_text = cell.get_text(strip=True)
                    
                    # 날짜 셀 찾기
                    if cell_text == date_str:
                        print(f"날짜 {date_str} 발견!")
                        
                        # 주변 셀들에서 경기 정보 찾기
                        parent_row = cell.find_parent('tr')
                        if parent_row:
                            # 같은 행의 다른 셀들 확인
                            row_cells = parent_row.find_all('td')
                            
                            for row_cell in row_cells:
                                # 경기 정보가 있는 셀 찾기
                                links = row_cell.find_all('a')
                                for link in links:
                                    link_text = link.get_text(strip=True)
                                    
                                    # 점수 패턴 찾기 (예: "KIA 5:3 LG")
                                    score_pattern = r'(\w+)\s*(\d+):(\d+)\s*(\w+)'
                                    match = re.search(score_pattern, link_text)
                                    
                                    if match:
                                        away_team = match.group(1)
                                        away_score = int(match.group(2))
                                        home_score = int(match.group(3))
                                        home_team = match.group(4)
                                        
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
                
                # 다른 패턴으로도 시도
                if not games_found:
                    print("다른 패턴으로 검색 중...")
                    
                    # 모든 링크에서 경기 정보 찾기
                    all_links = soup.find_all('a')
                    for link in all_links:
                        link_text = link.get_text(strip=True)
                        
                        # 다양한 점수 패턴
                        patterns = [
                            r'(\w+)\s*(\d+):(\d+)\s*(\w+)',  # KIA 5:3 LG
                            r'(\w+)\s*(\d+)-(\d+)\s*(\w+)',  # KIA 5-3 LG
                            r'(\w+)\s+(\d+)\s+(\d+)\s+(\w+)', # KIA 5 3 LG
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, link_text)
                            if match:
                                away_team = match.group(1)
                                away_score = int(match.group(2))
                                home_score = int(match.group(3))
                                home_team = match.group(4)
                                
                                # 날짜 확인 (링크 주변 텍스트에서)
                                parent = link.find_parent()
                                if parent and str(date.day) in parent.get_text():
                                    game_info = {
                                        'date': date.strftime('%Y-%m-%d'),
                                        'away_team': away_team,
                                        'home_team': home_team,
                                        'away_score': away_score,
                                        'home_score': home_score,
                                        'winner': away_team if away_score > home_score else home_team
                                    }
                                    
                                    if game_info not in games_found:
                                        games_found.append(game_info)
                                        print(f"경기 발견: {away_team} {away_score} - {home_score} {home_team}")
                
                if games_found:
                    print(f"\n총 {len(games_found)}개 경기 발견")
                    
                    # 결과 저장
                    filename = f"data/kbo_games_{date.strftime('%Y%m%d')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(games_found, f, ensure_ascii=False, indent=2)
                    print(f"결과 저장: {filename}")
                    
                    return games_found
                else:
                    print("경기 정보를 찾을 수 없음")
                    
                    # JavaScript 렌더링 필요 여부 확인
                    if '__doPostBack' in response.text:
                        print("ASP.NET PostBack 방식 사용 - JavaScript 렌더링 필요")
                    
        except Exception as e:
            print(f"에러: {e}")
            import traceback
            traceback.print_exc()
    
    return []

def test_simple_request():
    """간단한 요청 테스트"""
    print("\n=== 간단한 요청 테스트 ===")
    
    # 2024년 10월 직접 URL
    url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=0&year=2024&month=10"
    
    response = requests.get(url)
    print(f"상태: {response.status_code}")
    
    # 팀 이름이 있는지 확인
    teams = ['KIA', 'LG', 'SSG', 'NC', '두산', '삼성', 'KT', '한화', '롯데', '키움']
    found_teams = [team for team in teams if team in response.text]
    print(f"발견된 팀: {found_teams}")
    
    # 점수 패턴 찾기
    score_patterns = re.findall(r'\d+:\d+', response.text)
    print(f"점수 패턴 발견: {len(score_patterns)}개")
    if score_patterns:
        print(f"샘플: {score_patterns[:5]}")

if __name__ == "__main__":
    games = test_kbo_html_parsing()
    
    if not games:
        test_simple_request()