"""
실제 작동하는 구글 검색 기반 KBO 크롤러
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

class GoogleRealCrawler:
    def __init__(self):
        self.logger = setup_logger('GoogleRealCrawler')
        
    async def get_game_results(self, date=None):
        """구글 검색으로 KBO 경기 결과 가져오기"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        self.logger.info(f"구글 실제 크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        games = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR'
            )
            
            page = await context.new_page()
            
            try:
                # 구글 검색 - 날짜 없이
                search_query = "KBO 경기결과"
                search_url = f"https://www.google.com/search?q={search_query}&hl=ko"
                
                self.logger.info(f"검색: {search_query}")
                await page.goto(search_url)
                await page.wait_for_timeout(5000)
                
                # HTML 콘텐츠 가져오기
                content = await page.content()
                
                # JavaScript로 데이터 추출
                extracted_data = await page.evaluate("""
                    () => {
                        const results = [];
                        const kboTeams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데'];
                        
                        // 모든 텍스트 노드 검색
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        
                        let node;
                        const texts = [];
                        while (node = walker.nextNode()) {
                            const text = node.textContent.trim();
                            if (text.length > 0 && text.length < 200) {
                                texts.push(text);
                            }
                        }
                        
                        // 연속된 텍스트 조합
                        for (let i = 0; i < texts.length - 2; i++) {
                            const combined = texts[i] + ' ' + texts[i+1] + ' ' + texts[i+2];
                            
                            // 팀 이름과 숫자가 포함된 패턴 찾기
                            const team1Match = kboTeams.find(team => texts[i].includes(team));
                            const scoreMatch = texts[i+1].match(/^(\\d+)$/);
                            const team2Match = kboTeams.find(team => texts[i+2].includes(team));
                            
                            if (team1Match && scoreMatch && team2Match && team1Match !== team2Match) {
                                results.push({
                                    text: combined,
                                    team1: team1Match,
                                    score: texts[i+1],
                                    team2: team2Match,
                                    index: i
                                });
                            }
                        }
                        
                        // 점수 패턴 찾기 (예: "NC 7 키움")
                        const allText = document.body.innerText;
                        kboTeams.forEach(team1 => {
                            kboTeams.forEach(team2 => {
                                if (team1 !== team2) {
                                    // 다양한 패턴 시도
                                    const patterns = [
                                        new RegExp(`${team1}\\s+(\\d+)\\s+${team2}`, 'g'),
                                        new RegExp(`${team1}\\s+(\\d+)\\s*vs\\s*(\\d+)\\s+${team2}`, 'g'),
                                        new RegExp(`${team1}\\s+(\\d+)\\s*-\\s*(\\d+)\\s+${team2}`, 'g'),
                                        new RegExp(`${team1}\\s+(\\d+)\\s*:\\s*(\\d+)\\s+${team2}`, 'g')
                                    ];
                                    
                                    patterns.forEach(pattern => {
                                        const matches = allText.matchAll(pattern);
                                        for (const match of matches) {
                                            results.push({
                                                pattern: 'regex',
                                                team1: team1,
                                                score1: match[1],
                                                score2: match[2] || '',
                                                team2: team2,
                                                fullMatch: match[0]
                                            });
                                        }
                                    });
                                }
                            });
                        });
                        
                        return results;
                    }
                """)
                
                self.logger.info(f"추출된 데이터: {len(extracted_data)}개")
                
                # 데이터 파싱
                seen_games = set()
                
                for data in extracted_data:
                    try:
                        if 'pattern' in data and data['pattern'] == 'regex':
                            # 정규식 매치 결과
                            team1 = data['team1']
                            team2 = data['team2']
                            
                            if data['score2']:  # 양팀 점수가 있는 경우
                                score1 = int(data['score1'])
                                score2 = int(data['score2'])
                            else:  # 한 점수만 있는 경우 (다음 요소에서 찾아야 함)
                                continue
                            
                            # 중복 체크
                            game_key = f"{min(team1, team2)}-{max(team1, team2)}"
                            if game_key not in seen_games:
                                seen_games.add(game_key)
                                
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
                
                # BeautifulSoup으로 추가 파싱
                if len(games) < 5:  # 5경기 미만이면 추가 파싱
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()
                    
                    # TVING 패턴 파싱 (예: "NC logo. NC. 7. 키움 logo. 키움")
                    tving_pattern = r'(\w+)\s+logo\.\s+\1\.\s+(\d+)\.\s+(\w+)\s+logo\.\s+\3'
                    tving_matches = re.findall(tving_pattern, text)
                    
                    for match in tving_matches:
                        team1, score, team2 = match
                        if team1 in ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데'] and \
                           team2 in ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']:
                            
                            # 다음 점수 찾기
                            next_score_match = re.search(f"{team2}\\.\\s+(\\d+)", text[text.find(match[0]):])
                            if next_score_match:
                                score1 = int(score)
                                score2 = int(next_score_match.group(1))
                                
                                game_key = f"{min(team1, team2)}-{max(team1, team2)}"
                                if game_key not in seen_games:
                                    seen_games.add(game_key)
                                    
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
                                    self.logger.info(f"TVING 경기: {team1} {score1} - {score2} {team2}")
                
            except Exception as e:
                self.logger.error(f"크롤링 에러: {e}")
                
            finally:
                await browser.close()
        
        return games
    
    def save_results(self, games, date):
        """결과 저장"""
        if not games:
            return
            
        # JSON 파일로 저장
        date_str = date.strftime('%Y%m%d')
        filename = os.path.join(DATA_DIR, f'google_real_results_{date_str}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"결과 저장 완료: {filename}")
        
        # 기존 형식과 동일하게 저장
        kbo_filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.json')
        with open(kbo_filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
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
            self.logger.warning("구글에서 경기 결과를 찾을 수 없습니다.")
            return []

# 동기 래퍼 함수
def run_google_real_crawler(date=None):
    """동기 환경에서 구글 실제 크롤러 실행"""
    crawler = GoogleRealCrawler()
    return asyncio.run(crawler.run(date))

if __name__ == "__main__":
    # 테스트 실행
    results = run_google_real_crawler()
    print(f"\n구글 실제 크롤링 결과: {len(results)}개 경기")
    for game in results:
        print(f"{game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")