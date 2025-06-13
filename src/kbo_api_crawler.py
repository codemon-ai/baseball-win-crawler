import requests
from datetime import datetime, timedelta
import json
import os
from .logger import setup_logger
from .config import DATA_DIR, TEAM_NAMES

class KBOAPICrawler:
    def __init__(self):
        self.logger = setup_logger('KBOAPICrawler')
        self.base_url = "https://www.koreabaseball.com"
        
    def get_game_results(self, date=None):
        """KBO 공식 사이트에서 경기 결과 가져오기"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        date_str = date.strftime('%Y%m%d')
        year = date.year
        month = date.month
        
        # KBO 공식 API 엔드포인트
        url = f"{self.base_url}/ws/Schedule.asmx/GetScheduleList"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{self.base_url}/Schedule/Schedule.aspx'
        }
        
        # API 파라미터
        data = {
            'leId': '1',  # KBO 리그
            'srId': '0,9',  # 정규시즌
            'date': date_str,
            'tmId': ''
        }
        
        try:
            self.logger.info(f"KBO API 호출: {url}")
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'd' in result and 'list' in result['d']:
                    games = result['d']['list']
                    return self.parse_games(games, date)
                else:
                    self.logger.warning("예상치 못한 API 응답 형식")
                    return []
            else:
                self.logger.error(f"API 호출 실패: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"API 호출 에러: {e}")
            return []
            
    def parse_games(self, games, date):
        """게임 데이터 파싱"""
        results = []
        
        for game in games:
            try:
                # 경기가 종료된 경우만 처리
                if game.get('status') == '종료' or game.get('gmsc') == 'F':
                    away_team = game.get('awayNm', '').strip()
                    home_team = game.get('homeNm', '').strip()
                    away_score = int(game.get('asc', 0))
                    home_score = int(game.get('hsc', 0))
                    
                    # 승리팀 결정
                    if away_score > home_score:
                        winner = away_team
                    elif home_score > away_score:
                        winner = home_team
                    else:
                        winner = "무승부"
                        
                    game_info = {
                        'date': date.strftime('%Y-%m-%d'),
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_score': away_score,
                        'home_score': home_score,
                        'winner': winner,
                        'stadium': game.get('stadium', ''),
                        'game_time': game.get('time', '')
                    }
                    
                    results.append(game_info)
                    self.logger.info(f"경기: {away_team} {away_score} - {home_score} {home_team}, 승리: {winner}")
                    
            except Exception as e:
                self.logger.error(f"게임 파싱 에러: {e}")
                continue
                
        return results
        
    def save_results(self, games, date):
        """결과 저장"""
        if not games:
            self.logger.warning("저장할 경기 결과가 없습니다.")
            return
            
        # JSON 파일로 저장
        date_str = date.strftime('%Y%m%d')
        filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"결과 저장 완료: {filename}")
        
        # CSV 파일로도 저장
        csv_filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.csv')
        import pandas as pd
        df = pd.DataFrame(games)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"CSV 저장 완료: {csv_filename}")
        
        # 승리팀만 별도 저장
        winners = [{'date': g['date'], 'winner': g['winner']} for g in games if g['winner'] != "무승부"]
        winners_filename = os.path.join(DATA_DIR, f'winners_{date_str}.json')
        
        with open(winners_filename, 'w', encoding='utf-8') as f:
            json.dump(winners, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"승리팀 저장 완료: {winners_filename}")
        
    def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        games = self.get_game_results(date)
        
        if games:
            self.save_results(games, date)
            return games
        else:
            self.logger.warning("크롤링된 경기 결과가 없습니다.")
            return []

# 대안: 정적 HTML 파싱 방식
def crawl_with_requests(date=None):
    """requests와 BeautifulSoup을 사용한 크롤링"""
    from bs4 import BeautifulSoup
    
    if date is None:
        date = datetime.now() - timedelta(days=1)
        
    # StatIz 사이트 사용 (대안)
    year = date.year
    month = date.month
    day = date.day
    
    url = f"http://www.statiz.co.kr/schedule.php?year={year}&month={month:02d}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 날짜별 경기 찾기
            date_str = f"{month:02d}.{day:02d}"
            games = []
            
            # 테이블에서 해당 날짜 찾기
            rows = soup.find_all('tr')
            
            for row in rows:
                if date_str in row.text:
                    # 경기 정보 추출
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            teams_score = cells[1].text.strip()
                            if ' ' in teams_score and '-' in teams_score:
                                parts = teams_score.split(' ')
                                away_team = parts[0]
                                score_part = parts[1]
                                home_team = parts[2] if len(parts) > 2 else ''
                                
                                scores = score_part.split('-')
                                if len(scores) == 2:
                                    away_score = int(scores[0])
                                    home_score = int(scores[1])
                                    
                                    winner = away_team if away_score > home_score else home_team
                                    
                                    game_info = {
                                        'date': date.strftime('%Y-%m-%d'),
                                        'away_team': away_team,
                                        'home_team': home_team,
                                        'away_score': away_score,
                                        'home_score': home_score,
                                        'winner': winner
                                    }
                                    
                                    games.append(game_info)
                                    
                        except Exception as e:
                            print(f"파싱 에러: {e}")
                            continue
                            
            return games
            
    except Exception as e:
        print(f"크롤링 에러: {e}")
        return []

if __name__ == "__main__":
    # API 크롤러 테스트
    crawler = KBOAPICrawler()
    
    # 2024년 10월 15일 데이터 테스트
    test_date = datetime(2024, 10, 15)
    results = crawler.run(test_date)
    
    if not results:
        print("\nAPI 크롤링 실패, 대안 방법 시도...")
        results = crawl_with_requests(test_date)
        
    print(f"\n총 {len(results)}개 경기 크롤링 완료")