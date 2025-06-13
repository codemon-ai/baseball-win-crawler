from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time

def test_naver_with_selenium():
    """Selenium으로 네이버 스포츠 접속하여 실제 데이터 확인"""
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 백그라운드 실행
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 드라이버 생성
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 2024년 10월 15일 경기 결과 페이지
        date = datetime(2024, 10, 15)
        date_str = date.strftime('%Y%m%d')
        
        url = f"https://sports.news.naver.com/kbaseball/schedule/index?date={date_str}"
        print(f"접속 URL: {url}")
        
        driver.get(url)
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)
        
        # 네트워크 요청 로그 확인
        print("\n=== 네트워크 로그 확인 ===")
        logs = driver.get_log('performance')
        for log in logs[:10]:  # 처음 10개만
            print(log['message'][:200])
        
        # JavaScript로 데이터 확인
        print("\n=== JavaScript 실행 ===")
        
        # 1. 전역 변수 확인
        global_vars = driver.execute_script("""
            return Object.keys(window).filter(key => 
                key.includes('schedule') || 
                key.includes('game') || 
                key.includes('data') ||
                key.includes('SPORTS')
            );
        """)
        print(f"관련 전역 변수: {global_vars}")
        
        # 2. 실제 데이터 찾기
        schedule_data = driver.execute_script("""
            // 가능한 데이터 위치들
            if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;
            if (window.scheduleData) return window.scheduleData;
            if (window.gameData) return window.gameData;
            
            // React/Vue 데이터 찾기
            const root = document.querySelector('#root') || document.querySelector('#app');
            if (root && root.__reactInternalInstance) {
                return root.__reactInternalInstance;
            }
            
            return null;
        """)
        
        if schedule_data:
            print("스케줄 데이터 발견!")
            with open("data/selenium_schedule_data.json", "w", encoding="utf-8") as f:
                json.dump(schedule_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 3. DOM에서 직접 데이터 추출
        print("\n=== DOM 파싱 ===")
        
        # 경기 결과 요소 대기
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tb_sc")))
            print("경기 테이블 발견!")
        except:
            print("경기 테이블을 찾을 수 없음")
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 다양한 선택자로 경기 찾기
        selectors = [
            ('div.tb_wrap table.tb_sc tbody tr', 'tr'),  # 테이블 방식
            ('div.game_sch_wrap div.game_cont', 'div'),  # div 방식
            ('div[class*="game"] div[class*="score"]', 'div'),  # 클래스명 패턴
            ('table tbody tr[data-game-id]', 'tr'),  # data 속성
        ]
        
        for selector, tag in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n선택자 '{selector}'로 {len(elements)}개 요소 발견")
                
                # 첫 번째 요소 분석
                if elements:
                    first = elements[0]
                    print(f"첫 번째 요소 클래스: {first.get('class')}")
                    print(f"텍스트 미리보기: {first.text[:100].strip()}")
                    
                    # 경기 데이터 추출 시도
                    if tag == 'tr':
                        # 테이블 행에서 데이터 추출
                        cells = first.find_all('td')
                        if len(cells) >= 3:
                            print(f"셀 개수: {len(cells)}")
                            for i, cell in enumerate(cells[:5]):
                                print(f"셀 {i}: {cell.text.strip()}")
        
        # 4. AJAX 요청 가로채기
        print("\n=== AJAX 요청 확인 ===")
        
        # 페이지 새로고침하여 네트워크 요청 캡처
        driver.refresh()
        time.sleep(3)
        
        # 네트워크 요청 확인
        ajax_script = """
        const performance = window.performance.getEntriesByType('resource');
        const ajaxRequests = performance.filter(entry => 
            entry.name.includes('api') || 
            entry.name.includes('ajax') ||
            entry.name.includes('schedule') ||
            entry.name.includes('game')
        );
        return ajaxRequests.map(req => ({
            url: req.name,
            duration: req.duration,
            size: req.transferSize
        }));
        """
        
        ajax_requests = driver.execute_script(ajax_script)
        print(f"발견된 AJAX 요청: {len(ajax_requests)}개")
        for req in ajax_requests[:5]:
            print(f"URL: {req['url']}")
        
        # HTML 저장
        with open("data/naver_sports_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\nHTML 페이지 저장 완료: data/naver_sports_page.html")
        
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()

def test_kbo_official_with_selenium():
    """KBO 공식 사이트 Selenium 테스트"""
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # KBO 일정 페이지
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
        print(f"\n=== KBO 공식 사이트 테스트 ===")
        print(f"접속 URL: {url}")
        
        driver.get(url)
        time.sleep(3)
        
        # JavaScript 실행하여 데이터 확인
        kbo_data = driver.execute_script("""
            // ASP.NET ViewState 확인
            const viewState = document.getElementById('__VIEWSTATE');
            
            // 가능한 데이터 위치
            if (window.scheduleData) return window.scheduleData;
            if (window.gameList) return window.gameList;
            
            // 테이블에서 데이터 추출
            const games = [];
            const rows = document.querySelectorAll('table.tbl tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length > 0) {
                    games.push(Array.from(cells).map(cell => cell.textContent.trim()));
                }
            });
            
            return games;
        """)
        
        if kbo_data:
            print(f"KBO 데이터 발견: {len(kbo_data)}개 항목")
            print(f"샘플: {kbo_data[:2]}")
        
    except Exception as e:
        print(f"KBO 사이트 에러: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_naver_with_selenium()
    test_kbo_official_with_selenium()