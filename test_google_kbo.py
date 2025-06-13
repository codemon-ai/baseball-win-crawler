"""
KBO 경기결과 구글 검색 크롤링 테스트
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from bs4 import BeautifulSoup
import re

async def test_google_kbo_search():
    """KBO 경기결과 구글 검색 테스트"""
    
    print("=== KBO 경기결과 구글 검색 테스트 ===")
    
    async with async_playwright() as p:
        # 브라우저 실행 (헤드리스 모드 끄기 - 디버깅용)
        browser = await p.chromium.launch(
            headless=True,  # False로 하면 브라우저 창이 보임
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ko-KR'
        )
        
        page = await context.new_page()
        
        try:
            # 구글 검색
            search_query = "KBO 경기결과"
            search_url = f"https://www.google.com/search?q={search_query}&hl=ko"
            
            print(f"검색 URL: {search_url}")
            await page.goto(search_url)
            
            # 페이지 로딩 대기
            print("페이지 로딩 중...")
            await page.wait_for_timeout(5000)
            
            # 스크린샷 저장
            await page.screenshot(path="data/google_kbo_search.png", full_page=True)
            print("스크린샷 저장: data/google_kbo_search.png")
            
            # HTML 저장
            content = await page.content()
            with open("data/google_kbo_search.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("HTML 저장: data/google_kbo_search.html")
            
            # 1. 구글 스포츠 카드 찾기
            print("\n=== 구글 스포츠 카드 검색 ===")
            
            # 다양한 선택자 시도
            selectors = [
                # 구글 스포츠 위젯
                'div[data-async-context*="sport"]',
                'div[class*="sports-app"]',
                'div[data-entityname*="sports"]',
                'g-scrolling-carousel',
                
                # 일반 카드
                'div[jscontroller]',
                'div[data-hveid]',
                'div.g',
                
                # 스포츠 관련
                '[aria-label*="경기"]',
                '[aria-label*="야구"]',
                '[aria-label*="KBO"]'
            ]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"'{selector}' 선택자: {len(elements)}개 발견")
                    
                    # 첫 번째 요소 텍스트 확인
                    if elements and len(elements) > 0:
                        try:
                            text = await elements[0].text_content()
                            if text and len(text.strip()) > 0:
                                preview = text[:100].replace('\n', ' ')
                                print(f"  → 내용: {preview}...")
                        except:
                            pass
            
            # 2. JavaScript로 데이터 추출
            print("\n=== JavaScript 데이터 추출 ===")
            
            sports_data = await page.evaluate("""
                () => {
                    // 결과 저장
                    const results = {
                        games: [],
                        elements: [],
                        rawTexts: []
                    };
                    
                    // KBO 팀 목록
                    const teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데'];
                    
                    // 모든 div 요소 검색
                    const divs = document.querySelectorAll('div');
                    
                    divs.forEach(div => {
                        const text = div.innerText || div.textContent || '';
                        
                        // KBO 팀이 2개 이상 포함된 요소
                        const foundTeams = teams.filter(team => text.includes(team));
                        
                        if (foundTeams.length >= 2) {
                            // 숫자(점수)도 포함되어 있는지 확인
                            const hasNumbers = /\\d+/.test(text);
                            
                            if (hasNumbers && text.length < 500) {
                                results.elements.push({
                                    text: text.trim(),
                                    teams: foundTeams,
                                    className: div.className,
                                    id: div.id
                                });
                            }
                        }
                    });
                    
                    // 점수 패턴 찾기
                    results.elements.forEach(elem => {
                        // 다양한 점수 패턴
                        const patterns = [
                            /(\\d+)\\s*[-:]\\s*(\\d+)/g,  // 5-3, 5:3
                            /(\\d+)\\s+(\\d+)/g,           // 5 3
                        ];
                        
                        for (const pattern of patterns) {
                            const matches = elem.text.matchAll(pattern);
                            for (const match of matches) {
                                if (match[1] && match[2]) {
                                    results.games.push({
                                        score: `${match[1]}-${match[2]}`,
                                        teams: elem.teams,
                                        fullText: elem.text
                                    });
                                    break;
                                }
                            }
                        }
                    });
                    
                    // 전체 페이지에서 경기 결과 텍스트 찾기
                    const pageText = document.body.innerText;
                    teams.forEach(team1 => {
                        teams.forEach(team2 => {
                            if (team1 !== team2) {
                                // 팀1 점수 팀2 패턴
                                const regex = new RegExp(`${team1}\\\\s*(\\\\d+)\\\\s*[-:]?\\\\s*(\\\\d+)\\\\s*${team2}`, 'g');
                                const matches = pageText.matchAll(regex);
                                
                                for (const match of matches) {
                                    results.rawTexts.push({
                                        team1: team1,
                                        score1: match[1],
                                        score2: match[2],
                                        team2: team2
                                    });
                                }
                            }
                        });
                    });
                    
                    return results;
                }
            """)
            
            print(f"발견된 요소: {len(sports_data['elements'])}개")
            print(f"발견된 게임: {len(sports_data['games'])}개")
            print(f"원시 텍스트 매치: {len(sports_data['rawTexts'])}개")
            
            # 결과 출력
            if sports_data['games']:
                print("\n=== 발견된 경기 ===")
                for game in sports_data['games'][:5]:  # 최대 5개
                    print(f"점수: {game['score']}, 팀: {game['teams']}")
                    print(f"전체 텍스트: {game['fullText'][:100]}...")
            
            if sports_data['rawTexts']:
                print("\n=== 텍스트 매치 ===")
                for match in sports_data['rawTexts'][:5]:  # 최대 5개
                    print(f"{match['team1']} {match['score1']} - {match['score2']} {match['team2']}")
            
            # 3. BeautifulSoup으로 파싱
            print("\n=== BeautifulSoup 파싱 ===")
            soup = BeautifulSoup(content, 'html.parser')
            
            # 텍스트에서 직접 찾기
            page_text = soup.get_text()
            
            # KBO 팀 찾기
            kbo_teams = ['SSG', 'LG', 'NC', '키움', '두산', '한화', '삼성', 'KIA', 'KT', '롯데']
            found_teams = [team for team in kbo_teams if team in page_text]
            print(f"페이지에서 발견된 팀: {found_teams}")
            
            # 점수 패턴
            score_patterns = re.findall(r'(\d+)\s*[-:]\s*(\d+)', page_text)
            print(f"점수 패턴 발견: {len(score_patterns)}개")
            
            # 결과 저장
            results = {
                'search_query': search_query,
                'timestamp': datetime.now().isoformat(),
                'found_elements': len(sports_data['elements']),
                'found_games': len(sports_data['games']),
                'games': sports_data['games'][:10] if sports_data['games'] else [],
                'raw_matches': sports_data['rawTexts'][:10] if sports_data['rawTexts'] else []
            }
            
            with open("data/google_kbo_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print("\n결과 저장: data/google_kbo_results.json")
            
        except Exception as e:
            print(f"에러 발생: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_google_kbo_search())