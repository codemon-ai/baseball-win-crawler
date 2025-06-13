import schedule
import time
from datetime import datetime, timedelta
from .unified_crawler import UnifiedCrawler
from .logger import setup_logger
from .config import SCHEDULE_TIME
import sys

class CrawlerScheduler:
    def __init__(self):
        self.logger = setup_logger('CrawlerScheduler')
        self.crawler = UnifiedCrawler()
        
    def run_daily_crawl(self):
        """매일 실행되는 크롤링 작업"""
        self.logger.info("일일 크롤링 시작")
        
        # 어제 날짜
        yesterday = datetime.now() - timedelta(days=1)
        
        try:
            # 통합 크롤러 실행
            self.logger.info("통합 크롤러 실행 중...")
            import asyncio
            results = asyncio.run(self.crawler.run(yesterday))
            
            if results:
                self.logger.info(f"크롤링 성공: {len(results)}개 경기")
                
                # 승리팀 출력
                winners = [game['winner'] for game in results if game.get('winner') and game['winner'] != "무승부"]
                self.logger.info(f"승리팀: {', '.join(winners)}")
            else:
                self.logger.error("크롤링 실패")
                
        except Exception as e:
            self.logger.error(f"크롤링 중 에러 발생: {e}")
            
        self.logger.info("일일 크롤링 완료")
        
    def setup_schedule(self):
        """스케줄 설정"""
        # 매일 지정된 시간에 실행
        schedule.every().day.at(SCHEDULE_TIME).do(self.run_daily_crawl)
        
        self.logger.info(f"스케줄러 설정 완료: 매일 {SCHEDULE_TIME}에 실행")
        
    def run(self):
        """스케줄러 실행"""
        self.logger.info("스케줄러 시작")
        self.setup_schedule()
        
        # 시작 시 한 번 실행 (테스트용)
        self.logger.info("초기 실행 중...")
        self.run_daily_crawl()
        
        # 스케줄 루프
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
            except KeyboardInterrupt:
                self.logger.info("스케줄러 종료")
                break
            except Exception as e:
                self.logger.error(f"스케줄러 에러: {e}")
                time.sleep(60)
                
def run_once():
    """한 번만 실행 (테스트/수동 실행용)"""
    scheduler = CrawlerScheduler()
    scheduler.run_daily_crawl()
    
def run_scheduler():
    """스케줄러 실행"""
    scheduler = CrawlerScheduler()
    scheduler.run()

if __name__ == "__main__":
    # 명령줄 인자로 실행 모드 선택
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print("한 번만 실행 모드")
        run_once()
    else:
        print("스케줄러 모드")
        run_scheduler()