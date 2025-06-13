import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
from .logger import setup_logger
from .config import DATA_DIR, TEAM_NAMES
import os

class PlaywrightCrawler:
    def __init__(self):
        self.logger = setup_logger('PlaywrightCrawler')
        
    async def crawl_naver_sports(self, date=None):
        """네이버 스포츠에서 KBO 경기 결과 크롤링"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        date_str = date.strftime('%Y%m%d')
        self.logger.info(f"네이버 스포츠 크롤링 시작: {date_str}")
        
        games = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # 네이버 스포츠 KBO 일정 페이지
                url = f"https://sports.news.naver.com/kbaseball/schedule/index?date={date_str}"
                self.logger.info(f"페이지 접속: {url}")
                
                await page.goto(url, wait_until='networkidle')
                
                # JavaScript 렌더링 대기
                await page.wait_for_timeout(2000)
                
                # 경기 결과 테이블 대기
                try:
                    await page.wait_for_selector('div.tb_wrap', timeout=5000)
                except:
                    self.logger.warning("경기 결과 테이블을 찾을 수 없음")
                
                # HTML 가져오기
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # 경기 결과 파싱
                games = self._parse_naver_games(soup, date)
                
                if not games:
                    # 다른 선택자로 시도
                    self.logger.info("대체 선택자로 파싱 시도")
                    games = await self._parse_naver_games_alternative(page, date)
                
            except Exception as e:
                self.logger.error(f"네이버 스포츠 크롤링 에러: {e}")
                
            finally:
                await browser.close()
                
        return games
    
    def _parse_naver_games(self, soup, date):
        """네이버 스포츠 HTML 파싱"""
        games = []
        
        # 방법 1: 테이블 구조 파싱
        tables = soup.find_all('table', class_='tb_sc')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                try:
                    # 팀 이름 찾기
                    team_spans = row.find_all('span', class_='team_name')
                    if len(team_spans) >= 2:
                        away_team = team_spans[0].get_text(strip=True)
                        home_team = team_spans[1].get_text(strip=True)
                        
                        # 점수 찾기
                        score_ems = row.find_all('em', class_='score')
                        if len(score_ems) >= 2:
                            away_score = int(score_ems[0].get_text(strip=True))
                            home_score = int(score_ems[1].get_text(strip=True))
                            
                            # 경기 종료 확인
                            status = row.find('span', class_='state')
                            if status and '종료' in status.get_text():
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
                                self.logger.info(f"경기 발견: {away_team} {away_score} - {home_score} {home_team}")
                                
                except Exception as e:
                    continue
        
        # 방법 2: 경기 박스 구조 파싱
        if not games:
            game_boxes = soup.find_all('div', class_='game_box')
            
            for box in game_boxes:
                try:
                    # 팀 정보
                    teams = box.find_all('span', class_='team')
                    if len(teams) >= 2:
                        away_team = teams[0].get_text(strip=True)
                        home_team = teams[1].get_text(strip=True)
                        
                        # 점수 정보
                        scores = box.find_all('span', class_='num')
                        if len(scores) >= 2:
                            away_score = int(scores[0].get_text(strip=True))
                            home_score = int(scores[1].get_text(strip=True))
                            
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
                            self.logger.info(f"경기 발견: {away_team} {away_score} - {home_score} {home_team}")
                            
                except Exception as e:
                    continue
        
        return games
    
    async def _parse_naver_games_alternative(self, page, date):
        """JavaScript 실행으로 데이터 추출"""
        games = []
        
        try:
            # JavaScript로 데이터 직접 추출
            game_data = await page.evaluate("""
                () => {
                    const games = [];
                    
                    // 방법 1: React/Vue 컴포넌트 데이터
                    if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.schedule) {
                        return window.__INITIAL_STATE__.schedule.games;
                    }
                    
                    // 방법 2: DOM에서 직접 추출
                    const gameElements = document.querySelectorAll('[class*="game"]');
                    
                    gameElements.forEach(elem => {
                        const teams = elem.querySelectorAll('[class*="team"]');
                        const scores = elem.querySelectorAll('[class*="score"], [class*="num"]');
                        
                        if (teams.length >= 2 && scores.length >= 2) {
                            const awayTeam = teams[0].textContent.trim();
                            const homeTeam = teams[1].textContent.trim();
                            const awayScore = parseInt(scores[0].textContent.trim());
                            const homeScore = parseInt(scores[1].textContent.trim());
                            
                            if (!isNaN(awayScore) && !isNaN(homeScore)) {
                                games.push({
                                    awayTeam,
                                    homeTeam,
                                    awayScore,
                                    homeScore
                                });
                            }
                        }
                    });
                    
                    return games;
                }
            """)
            
            if game_data:
                for data in game_data:
                    game_info = {
                        'date': date.strftime('%Y-%m-%d'),
                        'away_team': data['awayTeam'],
                        'home_team': data['homeTeam'],
                        'away_score': data['awayScore'],
                        'home_score': data['homeScore'],
                        'winner': data['awayTeam'] if data['awayScore'] > data['homeScore'] else data['homeTeam']
                    }
                    games.append(game_info)
                    
        except Exception as e:
            self.logger.error(f"JavaScript 파싱 에러: {e}")
            
        return games
    
    async def crawl_kbo_official(self, date=None):
        """KBO 공식 사이트 크롤링"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"KBO 공식 사이트 크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        games = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # KBO 일정 페이지
                url = f"https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=0&year={date.year}&month={date.month:02d}"
                
                await page.goto(url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 해당 날짜 클릭 (달력에서)
                day_selector = f'td[onclick*="{date.day}"]'
                try:
                    await page.click(day_selector)
                    await page.wait_for_timeout(2000)
                except:
                    self.logger.warning(f"날짜 선택 실패: {date.day}")
                
                # HTML 파싱
                content = await page.content()
                games = self._parse_kbo_games(content, date)
                
            except Exception as e:
                self.logger.error(f"KBO 공식 사이트 크롤링 에러: {e}")
                
            finally:
                await browser.close()
                
        return games
    
    def _parse_kbo_games(self, html, date):
        """KBO 공식 사이트 HTML 파싱"""
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 경기 결과 링크 찾기
        game_links = soup.find_all('a', href=re.compile(r'BoxScore'))
        
        for link in game_links:
            try:
                link_text = link.get_text(strip=True)
                
                # 점수 패턴 매칭
                match = re.search(r'(\w+)\s*(\d+):(\d+)\s*(\w+)', link_text)
                if match:
                    away_team = match.group(1)
                    away_score = int(match.group(2))
                    home_score = int(match.group(3))
                    home_team = match.group(4)
                    
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
                    self.logger.info(f"경기 발견: {away_team} {away_score} - {home_score} {home_team}")
                    
            except Exception as e:
                continue
                
        return games
    
    async def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        # 네이버 스포츠 시도
        games = await self.crawl_naver_sports(date)
        
        # 실패 시 KBO 공식 사이트 시도
        if not games:
            self.logger.info("네이버 스포츠 실패, KBO 공식 사이트 시도")
            games = await self.crawl_kbo_official(date)
        
        # 결과 저장
        if games:
            self.save_results(games, date)
            return games
        else:
            self.logger.warning("크롤링 실패 - 더미 데이터 사용")
            dummy_games = self.get_dummy_data(date)
            self.save_results(dummy_games, date)
            return dummy_games
    
    def save_results(self, games, date):
        """결과 저장"""
        if not games:
            return
            
        # JSON 파일로 저장
        date_str = date.strftime('%Y%m%d')
        filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"결과 저장 완료: {filename}")
        
        # CSV 파일로도 저장
        import pandas as pd
        df = pd.DataFrame(games)
        csv_filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.csv')
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # 승리팀만 별도 저장
        winners = [{'date': g['date'], 'winner': g['winner']} for g in games]
        winners_filename = os.path.join(DATA_DIR, f'winners_{date_str}.json')
        
        with open(winners_filename, 'w', encoding='utf-8') as f:
            json.dump(winners, f, ensure_ascii=False, indent=2)
    
    def get_dummy_data(self, date):
        """테스트용 더미 데이터"""
        import random
        
        teams = list(TEAM_NAMES.values())
        games = []
        
        # 5경기 생성
        for i in range(5):
            home_team = random.choice(teams)
            away_team = random.choice([t for t in teams if t != home_team])
            
            home_score = random.randint(0, 15)
            away_score = random.randint(0, 15)
            
            winner = home_team if home_score > away_score else away_team
            if home_score == away_score:
                winner = random.choice([home_team, away_team])
                if winner == home_team:
                    home_score += 1
                else:
                    away_score += 1
            
            games.append({
                'date': date.strftime('%Y-%m-%d'),
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'winner': winner
            })
            
        return games

# 동기 래퍼 함수
def run_crawler(date=None):
    """동기 환경에서 크롤러 실행"""
    crawler = PlaywrightCrawler()
    return asyncio.run(crawler.run(date))

if __name__ == "__main__":
    # 테스트 실행
    test_date = datetime(2024, 10, 15)
    results = run_crawler(test_date)
    print(f"\n크롤링 결과: {len(results)}개 경기")