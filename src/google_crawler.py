"""
구글 검색 결과에서 KBO 경기 정보 크롤링
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
from .logger import setup_logger
from .config import DATA_DIR, TEAM_NAMES
import os

class GoogleCrawler:
    def __init__(self):
        self.logger = setup_logger('GoogleCrawler')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def get_game_results(self, date=None):
        """구글 검색으로 KBO 경기 결과 가져오기"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"구글 검색 크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        # 구글 검색 쿼리
        search_query = "KBO 야구 경기 결과"
        search_url = f"https://www.google.com/search?q={search_query}&hl=ko"
        
        try:
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 구글 스포츠 위젯 찾기
                games = self._parse_google_sports_widget(soup, date)
                
                if not games:
                    # 대체 방법: 일반 검색 결과에서 찾기
                    games = self._parse_search_results(soup, date)
                
                return games
            else:
                self.logger.error(f"구글 검색 실패: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"구글 크롤링 에러: {e}")
            return []
    
    def _parse_google_sports_widget(self, soup, date):
        """구글 스포츠 위젯에서 경기 정보 파싱"""
        games = []
        
        # 구글 스포츠 위젯 선택자들
        widget_selectors = [
            'div[data-async-context*="sports"]',
            'div[class*="sports-"]',
            'div[jsname*="sports"]',
            'g-expandable-content',
            'div[data-hveid][data-ved]'
        ]
        
        for selector in widget_selectors:
            widgets = soup.select(selector)
            
            for widget in widgets:
                widget_text = widget.get_text()
                
                # KBO 팀 이름이 포함된 위젯인지 확인
                kbo_teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']
                if any(team in widget_text for team in kbo_teams):
                    self.logger.info("KBO 경기 위젯 발견!")
                    
                    # 경기 정보 추출
                    game_elements = widget.find_all(['div', 'span'], recursive=True)
                    
                    for i in range(0, len(game_elements), 4):  # 팀1, 점수1, 팀2, 점수2
                        try:
                            if i + 3 < len(game_elements):
                                team1_elem = game_elements[i]
                                score1_elem = game_elements[i + 1]
                                team2_elem = game_elements[i + 2]
                                score2_elem = game_elements[i + 3]
                                
                                team1 = team1_elem.get_text(strip=True)
                                score1 = score1_elem.get_text(strip=True)
                                team2 = team2_elem.get_text(strip=True)
                                score2 = score2_elem.get_text(strip=True)
                                
                                # 팀 이름과 점수 검증
                                if team1 in kbo_teams and team2 in kbo_teams and score1.isdigit() and score2.isdigit():
                                    score1 = int(score1)
                                    score2 = int(score2)
                                    
                                    winner = team1 if score1 > score2 else team2
                                    
                                    game_info = {
                                        'date': date.strftime('%Y-%m-%d'),
                                        'away_team': team1,
                                        'home_team': team2,
                                        'away_score': score1,
                                        'home_score': score2,
                                        'winner': winner
                                    }
                                    
                                    games.append(game_info)
                                    self.logger.info(f"경기 발견: {team1} {score1} - {score2} {team2}")
                                    
                        except Exception as e:
                            continue
        
        return games
    
    def _parse_search_results(self, soup, date):
        """일반 검색 결과에서 경기 정보 찾기"""
        games = []
        
        # 검색 결과 항목들
        search_results = soup.find_all(['div', 'g'], class_=['g', 'tF2Cxc'])
        
        for result in search_results:
            text = result.get_text()
            
            # 점수 패턴 찾기 (예: "SSG 6 - 8 LG", "두산 2:3 한화")
            patterns = [
                r'([가-힣A-Z]+)\s*(\d+)\s*[-:]\s*(\d+)\s*([가-힣A-Z]+)',
                r'([가-힣A-Z]+)\s+(\d+)\s+(\d+)\s+([가-힣A-Z]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                
                for match in matches:
                    team1, score1, score2, team2 = match
                    
                    # KBO 팀인지 확인
                    kbo_teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']
                    if team1 in kbo_teams and team2 in kbo_teams:
                        score1 = int(score1)
                        score2 = int(score2)
                        
                        winner = team1 if score1 > score2 else team2
                        
                        game_info = {
                            'date': date.strftime('%Y-%m-%d'),
                            'away_team': team1,
                            'home_team': team2,
                            'away_score': score1,
                            'home_score': score2,
                            'winner': winner
                        }
                        
                        # 중복 체크
                        if game_info not in games:
                            games.append(game_info)
                            self.logger.info(f"경기 발견: {team1} {score1} - {score2} {team2}")
        
        return games
    
    def get_live_scores(self):
        """실시간 경기 스코어 가져오기"""
        self.logger.info("구글에서 실시간 스코어 검색")
        
        # 실시간 스코어 검색
        search_query = "KBO 실시간 스코어"
        search_url = f"https://www.google.com/search?q={search_query}&hl=ko"
        
        try:
            response = requests.get(search_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 실시간 스코어 위젯 찾기
                live_games = []
                
                # 구글 실시간 스포츠 카드
                sports_cards = soup.find_all('div', {'data-hveid': True})
                
                for card in sports_cards:
                    card_text = card.get_text()
                    
                    # 진행 중인 경기 찾기
                    if '회' in card_text or '종료' in card_text:
                        # 팀과 점수 추출
                        teams_scores = re.findall(r'([가-힣A-Z]+)\s*(\d+)', card_text)
                        
                        if len(teams_scores) >= 2:
                            team1, score1 = teams_scores[0]
                            team2, score2 = teams_scores[1]
                            
                            status = '진행중' if '회' in card_text else '종료'
                            
                            game_info = {
                                'home_team': team1,
                                'away_team': team2,
                                'home_score': int(score1),
                                'away_score': int(score2),
                                'status': status,
                                'inning': card_text.split('회')[0][-1] if '회' in card_text else None
                            }
                            
                            live_games.append(game_info)
                            self.logger.info(f"실시간 경기: {team1} {score1} - {score2} {team2} ({status})")
                
                return live_games
                
        except Exception as e:
            self.logger.error(f"실시간 스코어 크롤링 에러: {e}")
            return []
    
    def save_results(self, games, date):
        """결과 저장"""
        if not games:
            self.logger.warning("저장할 경기 결과가 없습니다.")
            return
            
        # JSON 파일로 저장
        date_str = date.strftime('%Y%m%d')
        filename = os.path.join(DATA_DIR, f'google_kbo_results_{date_str}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"결과 저장 완료: {filename}")
        
        # CSV 파일로도 저장
        import pandas as pd
        df = pd.DataFrame(games)
        csv_filename = os.path.join(DATA_DIR, f'google_kbo_results_{date_str}.csv')
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"CSV 저장 완료: {csv_filename}")
    
    def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        games = self.get_game_results(date)
        
        if games:
            self.save_results(games, date)
            return games
        else:
            self.logger.warning("구글에서 경기 결과를 찾을 수 없습니다.")
            return []

if __name__ == "__main__":
    # 테스트 실행
    crawler = GoogleCrawler()
    
    # 어제 경기 결과
    results = crawler.run()
    print(f"경기 결과: {len(results)}개")
    
    # 실시간 스코어
    live_scores = crawler.get_live_scores()
    print(f"실시간 경기: {len(live_scores)}개")