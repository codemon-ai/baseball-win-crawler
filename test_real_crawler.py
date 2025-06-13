import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from bs4 import BeautifulSoup
import json

async def test_real_naver_crawler():
    """실제 네이버 스포츠 크롤링 테스트"""
    
    print("=== 실제 네이버 스포츠 크롤링 테스트 ===")
    print("브라우저를 실행하여 실제 DOM 구조를 확인합니다...\n")
    
    async with async_playwright() as p:
        # 헤드리스 모드 끄고 실행 (디버깅용)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 2024년 10월 15일 경기
        date = datetime(2024, 10, 15)
        date_str = date.strftime('%Y%m%d')
        
        url = f"https://sports.news.naver.com/kbaseball/schedule/index?date={date_str}"
        print(f"접속 URL: {url}")
        
        await page.goto(url)
        print("페이지 로딩 중...")
        
        # 충분한 대기 시간
        await page.wait_for_timeout(5000)
        
        # 스크린샷 저장
        await page.screenshot(path="data/naver_sports_screenshot.png")
        print("스크린샷 저장: data/naver_sports_screenshot.png")
        
        # 가능한 선택자들 테스트
        selectors_to_test = [
            # 일반적인 경기 결과 선택자들
            'div[class*="game_result"]',
            'div[class*="game_box"]',
            'div[class*="match"]',
            'table[class*="schedule"]',
            'div[class*="score"]',
            
            # 네이버 특화 선택자
            'div._game_box',
            'div._match_box',
            'div.tb_wrap',
            'table.tb',
            
            # ID 기반
            '#scheduleList',
            '#gameList',
            '#content'
        ]
        
        print("\n=== 선택자 테스트 ===")
        for selector in selectors_to_test:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"✓ '{selector}': {len(elements)}개 발견")
                
                # 첫 번째 요소의 텍스트 확인
                first_text = await elements[0].text_content()
                if first_text:
                    print(f"  → 샘플: {first_text[:100].strip()}")
        
        # JavaScript로 데이터 구조 확인
        print("\n=== JavaScript 데이터 확인 ===")
        js_data = await page.evaluate("""
            () => {
                // 전역 변수 확인
                const globalVars = Object.keys(window).filter(key => 
                    key.toLowerCase().includes('game') || 
                    key.toLowerCase().includes('schedule') ||
                    key.toLowerCase().includes('data')
                );
                
                // React/Vue 컴포넌트 확인
                const root = document.querySelector('#root') || document.querySelector('#app');
                let componentData = null;
                if (root) {
                    const reactKey = Object.keys(root).find(key => key.startsWith('__react'));
                    const vueKey = Object.keys(root).find(key => key.startsWith('__vue'));
                    
                    if (reactKey) componentData = 'React 앱 발견';
                    if (vueKey) componentData = 'Vue 앱 발견';
                }
                
                return {
                    globalVars: globalVars.slice(0, 10),
                    componentType: componentData,
                    hasScheduleData: typeof scheduleData !== 'undefined',
                    documentTitle: document.title
                };
            }
        """)
        
        print(f"전역 변수: {js_data['globalVars']}")
        print(f"컴포넌트 타입: {js_data['componentType']}")
        print(f"문서 제목: {js_data['documentTitle']}")
        
        # HTML 저장
        content = await page.content()
        with open("data/naver_real_html.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("\nHTML 저장: data/naver_real_html.html")
        
        # 실제 경기 데이터 추출 시도
        print("\n=== 경기 데이터 추출 시도 ===")
        
        # 방법 1: 텍스트 기반 검색
        page_text = await page.text_content('body')
        if 'KIA' in page_text or 'LG' in page_text:
            print("✓ 팀 이름 발견")
        
        # 방법 2: 특정 패턴 검색
        games = []
        all_divs = await page.query_selector_all('div')
        
        for div in all_divs[:100]:  # 처음 100개만
            text = await div.text_content()
            if text and any(team in text for team in ['KIA', 'LG', 'SSG', 'NC', '두산']):
                # 점수 패턴이 있는지 확인
                if any(char.isdigit() for char in text):
                    print(f"경기 정보 가능성: {text[:50]}")
        
        print("\n브라우저 창을 확인하여 실제 구조를 보세요.")
        print("10초 후 브라우저가 닫힙니다...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

async def find_working_selector():
    """작동하는 선택자 찾기"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 정규시즌 날짜로 테스트 (2024년 9월)
        url = "https://sports.news.naver.com/kbaseball/schedule/index?date=20240915"
        
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        # 모든 요소의 클래스명 수집
        class_names = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const classes = new Set();
                
                elements.forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        el.className.split(' ').forEach(cls => {
                            if (cls && (
                                cls.includes('game') || 
                                cls.includes('match') || 
                                cls.includes('score') ||
                                cls.includes('team')
                            )) {
                                classes.add(cls);
                            }
                        });
                    }
                });
                
                return Array.from(classes);
            }
        """)
        
        print("\n=== 관련 클래스명 발견 ===")
        for cls in sorted(class_names):
            print(f"  .{cls}")
        
        await browser.close()

if __name__ == "__main__":
    # 실제 크롤링 테스트
    asyncio.run(test_real_naver_crawler())
    
    # 선택자 찾기
    print("\n" + "="*50 + "\n")
    asyncio.run(find_working_selector())