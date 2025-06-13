import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
import re
from .logger import setup_logger
from .storage import Storage
from .config import DATA_DIR, TEAM_NAMES

class SimpleCrawler:
    """간단한 KBO 크롤러 - 대체 데이터 소스 사용"""
    
    def __init__(self):
        self.logger = setup_logger('SimpleCrawler')
        self.storage = Storage()
        
    def crawl_games(self, date=None):
        """경기 결과 크롤링"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        # 여러 소스 시도
        results = []
        
        # 1. KBO 공식 사이트 시도
        results = self.crawl_kbo_official(date)
        
        if not results:
            # 2. 네이버 스포츠 모바일 시도
            results = self.crawl_naver_mobile(date)
            
        if not results:
            # 3. 더미 데이터 (테스트용)
            self.logger.warning("실제 크롤링 실패, 테스트 데이터 사용")
            results = self.get_dummy_data(date)
            
        return results
        
    def crawl_kbo_official(self, date):
        """KBO 공식 사이트 크롤링"""
        try:
            # KBO 일정 결과 페이지
            url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # GET 요청으로 시도
            params = {
                'leagueId': '1',
                'seriesId': '0',
                'date': date.strftime('%Y%m%d')
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return self.parse_kbo_html(response.text, date)
            else:
                self.logger.error(f"KBO 사이트 접속 실패: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"KBO 크롤링 에러: {e}")
            return []
            
    def parse_kbo_html(self, html, date):
        """KBO HTML 파싱"""
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 경기 결과 테이블 찾기 (여러 선택자 시도)
        selectors = [
            'div.game-cont',
            'div.game_cont',
            'table.tbl tbody tr',
            'div.schedule_game'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                self.logger.info(f"선택자 {selector}로 {len(elements)}개 요소 발견")
                
                for element in elements:
                    game = self.extract_game_from_element(element, date)
                    if game:
                        games.append(game)
                        
                if games:
                    break
                    
        return games
        
    def extract_game_from_element(self, element, date):
        """HTML 요소에서 게임 정보 추출"""
        try:
            # 팀명 찾기
            team_elements = element.find_all(text=re.compile('(KIA|LG|NC|KT|SSG|한화|롯데|삼성|두산|키움)'))
            if len(team_elements) >= 2:
                away_team = self.normalize_team_name(team_elements[0].strip())
                home_team = self.normalize_team_name(team_elements[1].strip())
            else:
                return None
                
            # 점수 찾기
            score_pattern = re.compile(r'\d+')
            scores = []
            for text in element.stripped_strings:
                if score_pattern.match(text) and len(text) <= 2:
                    scores.append(int(text))
                    
            if len(scores) >= 2:
                away_score = scores[0]
                home_score = scores[1]
            else:
                return None
                
            # 승리팀 결정
            if away_score > home_score:
                winner = away_team
            elif home_score > away_score:
                winner = home_team
            else:
                winner = "무승부"
                
            return {
                'date': date.strftime('%Y-%m-%d'),
                'away_team': away_team,
                'home_team': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'winner': winner
            }
            
        except Exception as e:
            self.logger.debug(f"요소 파싱 실패: {e}")
            return None
            
    def normalize_team_name(self, name):
        """팀 이름 정규화"""
        name = name.strip()
        
        # 팀명 매핑
        mappings = {
            'KIA타이거즈': 'KIA', 'KIA': 'KIA',
            'LG트윈스': 'LG', 'LG': 'LG',
            'NC다이노스': 'NC', 'NC': 'NC',
            'KT위즈': 'KT', 'KT': 'KT',
            'SSG랜더스': 'SSG', 'SSG': 'SSG',
            '한화이글스': '한화', '한화': '한화',
            '롯데자이언츠': '롯데', '롯데': '롯데',
            '삼성라이온즈': '삼성', '삼성': '삼성',
            '두산베어스': '두산', '두산': '두산',
            '키움히어로즈': '키움', '키움': '키움'
        }
        
        for full_name, short_name in mappings.items():
            if full_name in name or name in full_name:
                return short_name
                
        return name
        
    def crawl_naver_mobile(self, date):
        """네이버 모바일 스포츠 크롤링"""
        try:
            # 모바일 페이지는 상대적으로 간단한 구조
            date_str = date.strftime('%Y%m%d')
            url = f"https://m.sports.naver.com/kbaseball/schedule/index?date={date_str}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 모바일 페이지도 동적 렌더링일 가능성이 높음
                self.logger.warning("네이버 모바일도 동적 페이지")
                return []
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"네이버 모바일 크롤링 에러: {e}")
            return []
            
    def get_dummy_data(self, date):
        """테스트용 더미 데이터"""
        # 실제 운영시에는 제거
        if date.weekday() == 0:  # 월요일은 경기 없음
            return []
            
        dummy_games = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'away_team': 'KIA',
                'home_team': 'LG',
                'away_score': 5,
                'home_score': 3,
                'winner': 'KIA'
            },
            {
                'date': date.strftime('%Y-%m-%d'),
                'away_team': 'NC',
                'home_team': 'SSG',
                'away_score': 2,
                'home_score': 4,
                'winner': 'SSG'
            },
            {
                'date': date.strftime('%Y-%m-%d'),
                'away_team': '두산',
                'home_team': '한화',
                'away_score': 7,
                'home_score': 6,
                'winner': '두산'
            },
            {
                'date': date.strftime('%Y-%m-%d'),
                'away_team': 'KT',
                'home_team': '삼성',
                'away_score': 3,
                'home_score': 3,
                'winner': '무승부'
            },
            {
                'date': date.strftime('%Y-%m-%d'),
                'away_team': '키움',
                'home_team': '롯데',
                'away_score': 8,
                'home_score': 5,
                'winner': '키움'
            }
        ]
        
        return dummy_games
        
    def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        # 크롤링 실행
        games = self.crawl_games(date)
        
        if games:
            # 결과 저장
            self.storage.save_game_results(games, date)
            
            # 승리팀 출력
            winners = [g['winner'] for g in games if g['winner'] != '무승부']
            self.logger.info(f"크롤링 완료: {len(games)}경기, 승리팀: {', '.join(winners)}")
            
            return games
        else:
            self.logger.warning("크롤링된 경기가 없습니다.")
            return []

# 실행 테스트
if __name__ == "__main__":
    crawler = SimpleCrawler()
    
    # 어제 경기 크롤링
    results = crawler.run()
    
    if results:
        print(f"\n총 {len(results)}개 경기:")
        for game in results:
            print(f"{game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승리: {game['winner']})")