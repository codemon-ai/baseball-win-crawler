"""
KBO 공식 사이트 크롤러 - 실제 작동 버전
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

class KBOOfficialCrawler:
    def __init__(self):
        self.logger = setup_logger('KBOOfficialCrawler')
        self.base_url = "https://www.koreabaseball.com"
        
    async def get_game_results(self, date=None):
        """KBO 공식 사이트에서 경기 결과 가져오기"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"KBO 공식 사이트 크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
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
                # KBO 일정 페이지 접속
                url = f"{self.base_url}/schedule/schedule.aspx"
                self.logger.info(f"접속 URL: {url}")
                
                await page.goto(url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 년월 선택
                year = date.year
                month = date.month
                
                # JavaScript로 년월 설정
                await page.evaluate(f"""
                    () => {{
                        // 년도 선택
                        const yearSelect = document.querySelector('select[name*="year"], #year, select.year');
                        if (yearSelect) {{
                            yearSelect.value = '{year}';
                            yearSelect.dispatchEvent(new Event('change'));
                        }}
                        
                        // 월 선택
                        const monthSelect = document.querySelector('select[name*="month"], #month, select.month');
                        if (monthSelect) {{
                            monthSelect.value = '{month:02d}';
                            monthSelect.dispatchEvent(new Event('change'));
                        }}
                    }}
                """)
                
                await page.wait_for_timeout(2000)
                
                # 조회 버튼 클릭 (있는 경우)
                try:
                    await page.click('button[type="submit"], input[type="submit"], button.btn-search')
                    await page.wait_for_timeout(3000)
                except:
                    pass
                
                # 스크린샷 저장 (디버깅용)
                screenshot_path = f"data/kbo_official_{date.strftime('%Y%m%d')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                self.logger.info(f"스크린샷 저장: {screenshot_path}")
                
                # HTML 가져오기
                content = await page.content()
                
                # HTML 저장 (디버깅용)
                html_path = f"data/kbo_official_{date.strftime('%Y%m%d')}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # JavaScript로 경기 데이터 추출
                games_data = await page.evaluate("""
                    () => {
                        const games = [];
                        
                        // 테이블 찾기
                        const tables = document.querySelectorAll('table');
                        
                        tables.forEach(table => {
                            // 경기 결과가 있는 행 찾기
                            const rows = table.querySelectorAll('tr');
                            
                            rows.forEach(row => {
                                const cells = row.querySelectorAll('td');
                                
                                // 경기 정보가 있는 셀 찾기
                                cells.forEach(cell => {
                                    const text = cell.innerText || cell.textContent || '';
                                    
                                    // 점수 패턴 찾기 (예: "SSG 5 : 3 LG")
                                    const scorePattern = /(\\w+)\\s+(\\d+)\\s*:\\s*(\\d+)\\s+(\\w+)/;
                                    const match = text.match(scorePattern);
                                    
                                    if (match) {
                                        games.push({
                                            awayTeam: match[1],
                                            awayScore: parseInt(match[2]),
                                            homeScore: parseInt(match[3]),
                                            homeTeam: match[4],
                                            cellText: text,
                                            date: cell.getAttribute('data-date') || ''
                                        });
                                    }
                                    
                                    // 링크가 있는 경우
                                    const links = cell.querySelectorAll('a');
                                    links.forEach(link => {
                                        const linkText = link.innerText || link.textContent || '';
                                        const linkMatch = linkText.match(scorePattern);
                                        
                                        if (linkMatch) {
                                            games.push({
                                                awayTeam: linkMatch[1],
                                                awayScore: parseInt(linkMatch[2]),
                                                homeScore: parseInt(linkMatch[3]),
                                                homeTeam: linkMatch[4],
                                                linkText: linkText,
                                                href: link.href
                                            });
                                        }
                                    });
                                });
                            });
                        });
                        
                        // 중복 제거
                        const uniqueGames = [];
                        const seen = new Set();
                        
                        games.forEach(game => {
                            const key = `${game.awayTeam}-${game.homeTeam}-${game.awayScore}-${game.homeScore}`;
                            if (!seen.has(key)) {
                                seen.add(key);
                                uniqueGames.push(game);
                            }
                        });
                        
                        return uniqueGames;
                    }
                """)
                
                self.logger.info(f"JavaScript 추출 결과: {len(games_data)}개")
                
                # 추출된 데이터를 표준 형식으로 변환
                for game_data in games_data:
                    try:
                        away_team = self._normalize_team_name(game_data['awayTeam'])
                        home_team = self._normalize_team_name(game_data['homeTeam'])
                        away_score = game_data['awayScore']
                        home_score = game_data['homeScore']
                        
                        if away_team and home_team:
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
                
                # JavaScript 추출이 실패한 경우 BeautifulSoup 사용
                if not games:
                    self.logger.info("JavaScript 추출 실패, BeautifulSoup 시도")
                    games = self._parse_with_beautifulsoup(content, date)
                
            except Exception as e:
                self.logger.error(f"크롤링 에러: {e}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
        
        return games
    
    def _parse_with_beautifulsoup(self, html, date):
        """BeautifulSoup으로 HTML 파싱"""
        games = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 다양한 패턴으로 경기 찾기
        # 1. 테이블에서 찾기
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                for cell in cells:
                    cell_text = cell.get_text(strip=True)
                    
                    # 점수 패턴 매칭
                    patterns = [
                        r'(\w+)\s+(\d+)\s*:\s*(\d+)\s+(\w+)',  # SSG 5 : 3 LG
                        r'(\w+)\s+(\d+)\s*-\s*(\d+)\s+(\w+)',  # SSG 5 - 3 LG
                        r'(\w+)\s+(\d+)\s+vs\s+(\d+)\s+(\w+)', # SSG 5 vs 3 LG
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, cell_text)
                        if match:
                            away_team = self._normalize_team_name(match.group(1))
                            away_score = int(match.group(2))
                            home_score = int(match.group(3))
                            home_team = self._normalize_team_name(match.group(4))
                            
                            if away_team and home_team:
                                winner = away_team if away_score > home_score else home_team
                                
                                game_info = {
                                    'date': date.strftime('%Y-%m-%d'),
                                    'away_team': away_team,
                                    'home_team': home_team,
                                    'away_score': away_score,
                                    'home_score': home_score,
                                    'winner': winner
                                }
                                
                                # 중복 체크
                                if game_info not in games:
                                    games.append(game_info)
                                    self.logger.info(f"BS 경기: {away_team} {away_score} - {home_score} {home_team}")
                            break
        
        return games
    
    def _normalize_team_name(self, name):
        """팀 이름 정규화"""
        team_mapping = {
            'SSG': 'SSG',
            '랜더스': 'SSG',
            'LG': 'LG',
            '트윈스': 'LG',
            'NC': 'NC',
            '다이노스': 'NC',
            '키움': '키움',
            '히어로즈': '키움',
            '두산': '두산',
            '베어스': '두산',
            '한화': '한화',
            '이글스': '한화',
            '삼성': '삼성',
            '라이온즈': '삼성',
            'KIA': 'KIA',
            '타이거즈': 'KIA',
            'KT': 'KT',
            '위즈': 'KT',
            '롯데': '롯데',
            '자이언츠': '롯데'
        }
        
        # 정확한 매칭
        if name in team_mapping:
            return team_mapping[name]
        
        # 부분 매칭
        for key, value in team_mapping.items():
            if key in name or name in key:
                return value
        
        return None
    
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
        
        # CSV 저장
        import pandas as pd
        df = pd.DataFrame(games)
        csv_filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.csv')
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # 승리팀 저장
        winners = [{'date': g['date'], 'winner': g['winner']} for g in games]
        winners_filename = os.path.join(DATA_DIR, f'winners_{date_str}.json')
        with open(winners_filename, 'w', encoding='utf-8') as f:
            json.dump(winners, f, ensure_ascii=False, indent=2)
    
    async def run(self, date=None):
        """크롤러 실행"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        games = await self.get_game_results(date)
        
        if games:
            self.save_results(games, date)
            return games
        else:
            self.logger.warning("KBO 공식 사이트에서 경기 결과를 찾을 수 없습니다.")
            return []

# 동기 래퍼 함수
def run_kbo_official_crawler(date=None):
    """동기 환경에서 KBO 공식 크롤러 실행"""
    crawler = KBOOfficialCrawler()
    return asyncio.run(crawler.run(date))

if __name__ == "__main__":
    # 테스트 실행
    test_date = datetime(2024, 10, 15)
    results = run_kbo_official_crawler(test_date)
    print(f"\nKBO 공식 크롤링 결과: {len(results)}개 경기")
    for game in results:
        print(f"{game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")