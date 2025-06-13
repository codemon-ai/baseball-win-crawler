"""
Playwright를 사용한 구글 검색 결과 크롤링
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
from .logger import setup_logger
from .config import DATA_DIR, TEAM_NAMES
import os

class GooglePlaywrightCrawler:
    def __init__(self):
        self.logger = setup_logger('GooglePlaywrightCrawler')
    
    async def get_game_results(self, date=None):
        """구글 검색으로 KBO 경기 결과 가져오기"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"구글 Playwright 크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        games = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 한국어 설정
            await page.set_extra_http_headers({
                'Accept-Language': 'ko-KR,ko;q=0.9'
            })
            
            try:
                # 구글 검색
                search_query = "KBO 경기결과"
                search_url = f"https://www.google.com/search?q={search_query}&hl=ko"
                
                self.logger.info(f"구글 검색: {search_url}")
                await page.goto(search_url, wait_until='networkidle')
                
                # 스포츠 카드가 로드될 때까지 대기
                await page.wait_for_timeout(3000)
                
                # 스크린샷 저장 (디버깅용)
                await page.screenshot(path="data/google_sports_screenshot.png")
                self.logger.info("스크린샷 저장: data/google_sports_screenshot.png")
                
                # JavaScript로 데이터 추출
                games_data = await page.evaluate("""
                    () => {
                        const games = [];
                        
                        // 구글 스포츠 카드 선택자들
                        const selectors = [
                            '[data-entityname="sports__game"]',
                            '[data-async-type="sports"]',
                            '[jsname="sports_games"]',
                            'g-card',
                            'div[data-hveid]'
                        ];
                        
                        // KBO 팀 목록
                        const kboTeams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데'];
                        
                        // 모든 요소 검색
                        const allElements = document.querySelectorAll('*');
                        
                        allElements.forEach(element => {
                            const text = element.textContent || '';
                            
                            // KBO 팀이 포함된 요소 찾기
                            const hasKboTeam = kboTeams.some(team => text.includes(team));
                            
                            if (hasKboTeam && text.length < 200) {
                                // 점수 패턴 찾기
                                const scorePattern = /(\\d+)\\s*[-:]\\s*(\\d+)/;
                                const match = text.match(scorePattern);
                                
                                if (match) {
                                    // 팀 이름 추출
                                    const teams = kboTeams.filter(team => text.includes(team));
                                    
                                    if (teams.length >= 2) {
                                        games.push({
                                            text: text.trim(),
                                            teams: teams,
                                            score: match[0]
                                        });
                                    }
                                }
                            }
                        });
                        
                        // 중복 제거
                        const uniqueGames = [...new Map(games.map(g => [g.text, g])).values()];
                        
                        return uniqueGames.slice(0, 10);  // 최대 10개
                    }
                """)
                
                self.logger.info(f"발견된 게임 데이터: {len(games_data)}개")
                
                # 게임 데이터 파싱
                for game_data in games_data:
                    try:
                        text = game_data['text']
                        teams = game_data['teams']
                        score_text = game_data['score']
                        
                        # 점수 추출
                        score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', score_text)
                        if score_match and len(teams) >= 2:
                            score1 = int(score_match.group(1))
                            score2 = int(score_match.group(2))
                            
                            # 텍스트에서 팀 순서 확인
                            team1_idx = text.find(teams[0])
                            team2_idx = text.find(teams[1])
                            
                            if team1_idx < team2_idx:
                                away_team, home_team = teams[0], teams[1]
                                away_score, home_score = score1, score2
                            else:
                                away_team, home_team = teams[1], teams[0]
                                away_score, home_score = score2, score1
                            
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
                        self.logger.error(f"게임 파싱 에러: {e}")
                
                # HTML도 파싱 시도
                if not games:
                    content = await page.content()
                    games = self._parse_html_content(content, date)
                
            except Exception as e:
                self.logger.error(f"구글 크롤링 에러: {e}")
                
            finally:
                await browser.close()
        
        return games
    
    def _parse_html_content(self, html, date):
        """HTML 콘텐츠에서 경기 정보 추출"""
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 텍스트 기반 검색
        text = soup.get_text()
        
        # KBO 팀 목록
        kbo_teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']
        
        # 경기 패턴 찾기
        for i, team1 in enumerate(kbo_teams):
            for team2 in kbo_teams[i+1:]:
                # 다양한 패턴으로 검색
                patterns = [
                    f"{team1}\\s*(\\d+)\\s*[-:]\\s*(\\d+)\\s*{team2}",
                    f"{team1}\\s*(\\d+)\\s*{team2}\\s*(\\d+)",
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    
                    for match in matches:
                        try:
                            score1 = int(match[0])
                            score2 = int(match[1])
                            
                            winner = team1 if score1 > score2 else team2
                            
                            game_info = {
                                'date': date.strftime('%Y-%m-%d'),
                                'away_team': team1,
                                'home_team': team2,
                                'away_score': score1,
                                'home_score': score2,
                                'winner': winner
                            }
                            
                            if game_info not in games:
                                games.append(game_info)
                                self.logger.info(f"HTML 파싱 경기: {team1} {score1} - {score2} {team2}")
                                
                        except Exception as e:
                            continue
        
        return games
    
    async def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        games = await self.get_game_results(date)
        
        if games:
            self.save_results(games, date)
            return games
        else:
            self.logger.warning("구글에서 경기 결과를 찾을 수 없습니다.")
            return []
    
    def save_results(self, games, date):
        """결과 저장"""
        if not games:
            return
            
        # JSON 파일로 저장
        date_str = date.strftime('%Y%m%d')
        filename = os.path.join(DATA_DIR, f'google_kbo_results_{date_str}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"결과 저장 완료: {filename}")

# 동기 래퍼 함수
def run_google_crawler(date=None):
    """동기 환경에서 구글 크롤러 실행"""
    crawler = GooglePlaywrightCrawler()
    return asyncio.run(crawler.run(date))

if __name__ == "__main__":
    # 테스트 실행
    results = run_google_crawler()
    print(f"구글 크롤링 결과: {len(results)}개 경기")