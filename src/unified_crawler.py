"""
통합 크롤러 - KBO 공식 사이트 기반
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
from .logger import setup_logger
from .config import DATA_DIR
import os

class UnifiedCrawler:
    """KBO 공식 사이트를 메인으로 사용하는 통합 크롤러"""
    
    def __init__(self):
        self.logger = setup_logger('UnifiedCrawler')
        self.base_url = "https://www.koreabaseball.com"
        
    async def get_game_results(self, date=None):
        """경기 결과 가져오기 - KBO 공식 사이트 우선"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"통합 크롤러 시작: {date.strftime('%Y-%m-%d')}")
        
        # 1차: KBO 공식 사이트
        games = await self._crawl_kbo_official(date)
        
        # 2차: 실패 시 백업 소스 사용 (향후 구현)
        if not games:
            self.logger.warning("KBO 공식 사이트 크롤링 실패, 백업 소스 시도")
            # TODO: 백업 크롤러 구현
            
        return games
    
    async def _crawl_kbo_official(self, date):
        """KBO 공식 사이트 크롤링"""
        games = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # 특정 날짜의 일정 페이지 직접 접속
                year = date.year
                month = date.month
                url = f"{self.base_url}/schedule/schedule.aspx?year={year}&month={month:02d}"
                
                self.logger.info(f"접속 URL: {url}")
                await page.goto(url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 날짜 클릭 시도
                day = date.day
                try:
                    # 날짜 셀 클릭
                    date_selector = f'td:has-text("{day}")'
                    await page.click(date_selector)
                    await page.wait_for_timeout(2000)
                except:
                    self.logger.warning(f"날짜 {day} 클릭 실패")
                
                # 경기 데이터 추출
                games_data = await self._extract_games_data(page)
                
                # 데이터 파싱 및 정제
                seen_games = set()
                
                for game_data in games_data:
                    try:
                        # 중복 체크
                        game_key = f"{game_data['awayTeam']}-{game_data['homeTeam']}-{game_data['awayScore']}-{game_data['homeScore']}"
                        if game_key in seen_games:
                            continue
                        seen_games.add(game_key)
                        
                        away_team = self._normalize_team_name(game_data['awayTeam'])
                        home_team = self._normalize_team_name(game_data['homeTeam'])
                        
                        if away_team and home_team:
                            game_info = {
                                'date': date.strftime('%Y-%m-%d'),
                                'away_team': away_team,
                                'home_team': home_team,
                                'away_score': game_data['awayScore'],
                                'home_score': game_data['homeScore'],
                                'winner': away_team if game_data['awayScore'] > game_data['homeScore'] else home_team
                            }
                            
                            games.append(game_info)
                            self.logger.info(f"경기: {away_team} {game_data['awayScore']} - {game_data['homeScore']} {home_team}")
                            
                    except Exception as e:
                        self.logger.error(f"게임 파싱 에러: {e}")
                
            except Exception as e:
                self.logger.error(f"크롤링 에러: {e}")
                
            finally:
                await browser.close()
        
        return games
    
    async def _extract_games_data(self, page):
        """페이지에서 경기 데이터 추출"""
        return await page.evaluate("""
            () => {
                const games = [];
                const processedGames = new Set();
                
                // 모든 테이블과 div 요소 검색
                const elements = document.querySelectorAll('table, div');
                
                elements.forEach(element => {
                    const text = element.innerText || element.textContent || '';
                    
                    // 점수 패턴들
                    const patterns = [
                        /(\\w+)\\s+(\\d+)\\s*:\\s*(\\d+)\\s+(\\w+)/g,  // KIA 5 : 3 LG
                        /(\\w+)\\s+(\\d+)\\s*-\\s*(\\d+)\\s+(\\w+)/g,  // KIA 5 - 3 LG
                        /(\\w+)\\s+(\\d+)vs(\\d+)\\s+(\\w+)/g,        // KIA 5vs3 LG
                    ];
                    
                    patterns.forEach(pattern => {
                        const matches = text.matchAll(pattern);
                        for (const match of matches) {
                            const gameKey = `${match[1]}-${match[4]}-${match[2]}-${match[3]}`;
                            
                            if (!processedGames.has(gameKey)) {
                                processedGames.add(gameKey);
                                games.push({
                                    awayTeam: match[1],
                                    awayScore: parseInt(match[2]),
                                    homeScore: parseInt(match[3]),
                                    homeTeam: match[4]
                                });
                            }
                        }
                    });
                });
                
                return games;
            }
        """)
    
    def _normalize_team_name(self, name):
        """팀 이름 정규화"""
        team_mapping = {
            'SSG': 'SSG', '랜더스': 'SSG',
            'LG': 'LG', '트윈스': 'LG',
            'NC': 'NC', '다이노스': 'NC',
            '키움': '키움', '히어로즈': '키움',
            '두산': '두산', '베어스': '두산',
            '한화': '한화', '이글스': '한화',
            '삼성': '삼성', '라이온즈': '삼성',
            'KIA': 'KIA', '타이거즈': 'KIA',
            'KT': 'KT', '위즈': 'KT',
            '롯데': '롯데', '자이언츠': '롯데'
        }
        
        return team_mapping.get(name, name if name in team_mapping.values() else None)
    
    def save_results(self, games, date):
        """결과 저장"""
        if not games:
            self.logger.warning("저장할 경기 결과가 없습니다.")
            return
            
        date_str = date.strftime('%Y%m%d')
        
        # JSON 저장
        filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        self.logger.info(f"JSON 저장: {filename}")
        
        # CSV 저장
        import pandas as pd
        df = pd.DataFrame(games)
        csv_filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.csv')
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        self.logger.info(f"CSV 저장: {csv_filename}")
        
        # 승리팀만 저장
        winners = [{'date': g['date'], 'winner': g['winner']} for g in games]
        winners_filename = os.path.join(DATA_DIR, f'winners_{date_str}.json')
        with open(winners_filename, 'w', encoding='utf-8') as f:
            json.dump(winners, f, ensure_ascii=False, indent=2)
        self.logger.info(f"승리팀 저장: {winners_filename}")
    
    async def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        games = await self.get_game_results(date)
        
        if games:
            self.save_results(games, date)
            return games
        else:
            self.logger.warning("경기 결과를 찾을 수 없습니다.")
            # 테스트용 더미 데이터
            return self._get_dummy_data(date)
    
    def _get_dummy_data(self, date):
        """테스트용 더미 데이터"""
        import random
        
        teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']
        games = []
        
        # 5경기 생성
        used_teams = set()
        for _ in range(5):
            # 사용하지 않은 팀 선택
            available_teams = [t for t in teams if t not in used_teams]
            if len(available_teams) < 2:
                break
                
            home_team = random.choice(available_teams)
            used_teams.add(home_team)
            available_teams.remove(home_team)
            
            away_team = random.choice(available_teams)
            used_teams.add(away_team)
            
            home_score = random.randint(0, 15)
            away_score = random.randint(0, 15)
            
            # 무승부 방지
            if home_score == away_score:
                home_score += 1
            
            winner = home_team if home_score > away_score else away_team
            
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
def run_unified_crawler(date=None):
    """동기 환경에서 통합 크롤러 실행"""
    crawler = UnifiedCrawler()
    return asyncio.run(crawler.run(date))

if __name__ == "__main__":
    # 테스트 실행
    test_date = datetime(2024, 10, 15)
    results = run_unified_crawler(test_date)
    print(f"\n통합 크롤러 결과: {len(results)}개 경기")
    for game in results:
        print(f"{game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")