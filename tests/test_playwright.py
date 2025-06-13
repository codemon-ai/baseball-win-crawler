import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.playwright_crawler import PlaywrightCrawler
from datetime import datetime, timedelta

async def test_playwright_crawler():
    """Playwright 크롤러 테스트"""
    
    print("=== Playwright 크롤러 테스트 ===")
    
    crawler = PlaywrightCrawler()
    
    # 테스트할 날짜들
    test_dates = [
        datetime(2024, 10, 15),  # 포스트시즌
        datetime(2024, 9, 15),   # 정규시즌
        datetime(2024, 8, 20),   # 정규시즌
    ]
    
    for date in test_dates:
        print(f"\n날짜: {date.strftime('%Y-%m-%d')}")
        
        # 네이버 스포츠 테스트
        print("\n1. 네이버 스포츠 크롤링...")
        games = await crawler.crawl_naver_sports(date)
        
        if games:
            print(f"성공! {len(games)}개 경기 발견")
            for game in games[:2]:  # 처음 2개만 출력
                print(f"  {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")
        else:
            print("네이버 스포츠에서 데이터를 찾을 수 없음")
            
            # KBO 공식 사이트 테스트
            print("\n2. KBO 공식 사이트 크롤링...")
            games = await crawler.crawl_kbo_official(date)
            
            if games:
                print(f"성공! {len(games)}개 경기 발견")
                for game in games[:2]:
                    print(f"  {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")
            else:
                print("KBO 공식 사이트에서도 데이터를 찾을 수 없음")
        
        # 첫 번째 날짜만 상세 테스트
        if date == test_dates[0]:
            break
    
    # 전체 실행 테스트
    print("\n\n=== 전체 실행 테스트 ===")
    games = await crawler.run(test_dates[0])
    
    if games:
        print(f"최종 결과: {len(games)}개 경기")
        
        # 결과 파일 확인
        date_str = test_dates[0].strftime('%Y%m%d')
        json_file = f"data/kbo_results_{date_str}.json"
        csv_file = f"data/kbo_results_{date_str}.csv"
        winners_file = f"data/winners_{date_str}.json"
        
        print(f"\n저장된 파일:")
        for file in [json_file, csv_file, winners_file]:
            if os.path.exists(file):
                print(f"  ✓ {file}")
            else:
                print(f"  ✗ {file}")

if __name__ == "__main__":
    asyncio.run(test_playwright_crawler())