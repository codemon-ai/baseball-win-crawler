import requests
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import KBO_RESULT_URL, HEADERS
from datetime import datetime

def test_kbo_page():
    """KBO 경기 결과 페이지 구조 분석"""
    try:
        # 네이버 스포츠 KBO 일정/결과 페이지
        # 다양한 URL 패턴 테스트
        urls_to_test = [
            "https://sports.news.naver.com/kbaseball/schedule/index.nhn",
            "https://sports.news.naver.com/kbaseball/schedule/index",
            "https://m.sports.naver.com/kbaseball/schedule/index",
            f"https://sports.news.naver.com/kbaseball/schedule/index.nhn?date=20241001"
        ]
        
        for test_url in urls_to_test:
            print(f"\n테스트 URL: {test_url}")
            try:
                response = requests.get(test_url, headers=HEADERS)
                if response.status_code == 200:
                    print(f"✓ 성공! 상태 코드: {response.status_code}")
                    url = test_url
                    break
                else:
                    print(f"✗ 실패. 상태 코드: {response.status_code}")
            except Exception as e:
                print(f"✗ 에러: {e}")
        else:
            print("\n모든 URL 테스트 실패")
            return
        
        print(f"접속 URL: {url}")
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n=== 페이지 구조 분석 ===")
        
        # 경기 결과 테이블 찾기
        game_boxes = soup.find_all('div', class_='sch_tb')
        print(f"경기 박스 개수: {len(game_boxes)}")
        
        if game_boxes:
            # 첫 번째 경기 박스 분석
            first_game = game_boxes[0]
            
            # 날짜 정보
            date_info = first_game.find('span', class_='td_date')
            if date_info:
                print(f"날짜: {date_info.text.strip()}")
            
            # 팀 정보
            teams = first_game.find_all('span', class_='team_lft') + first_game.find_all('span', class_='team_rgt')
            print(f"팀 정보: {[team.text.strip() for team in teams]}")
            
            # 점수 정보
            scores = first_game.find_all('strong', class_='td_score')
            print(f"점수: {[score.text.strip() for score in scores]}")
            
            # 경기 상태
            status = first_game.find('span', class_='td_hour')
            if status:
                print(f"경기 상태: {status.text.strip()}")
        
        # 다른 가능한 선택자들 테스트
        print("\n=== 대안 선택자 테스트 ===")
        
        # 테이블 형식으로 되어있을 경우
        tables = soup.find_all('table')
        print(f"테이블 개수: {len(tables)}")
        
        # div 클래스로 찾기
        result_divs = soup.find_all('div', class_=['game_result', 'game_schedule', 'sch_tb2'])
        print(f"결과 div 개수: {len(result_divs)}")
        
        # HTML 일부 저장 (디버깅용)
        with open('data/sample_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:10000])  # 처음 10000자만 저장
        print("\n샘플 HTML이 data/sample_page.html에 저장되었습니다.")
        
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    test_kbo_page()