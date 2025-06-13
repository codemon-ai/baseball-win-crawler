#!/usr/bin/env python
"""
KBO 야구 승리팀 크롤러 메인 실행 파일
"""
import argparse
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.playwright_crawler import run_crawler
from src.google_playwright_crawler import run_google_crawler
from src.google_real_crawler import run_google_real_crawler
from src.kbo_official_crawler import run_kbo_official_crawler
from src.storage import Storage
from src.scheduler import CrawlerScheduler as Scheduler
from src.logger import setup_logger

logger = setup_logger('main')

def main():
    parser = argparse.ArgumentParser(description='KBO 야구 승리팀 크롤러')
    parser.add_argument('--date', type=str, help='크롤링할 날짜 (YYYYMMDD)')
    parser.add_argument('--once', action='store_true', help='한 번만 실행 (어제 경기)')
    parser.add_argument('--winners', action='store_true', help='어제 승리팀 조회')
    parser.add_argument('--team', type=str, help='특정 팀 통계 조회')
    parser.add_argument('--test', action='store_true', help='테스트 실행 (더미 데이터)')
    parser.add_argument('--google', action='store_true', help='구글 검색으로 크롤링')
    parser.add_argument('--kbo', action='store_true', help='KBO 공식 사이트 크롤링')
    parser.add_argument('--source', type=str, choices=['google', 'kbo', 'naver'], help='크롤링 소스 선택')
    
    args = parser.parse_args()
    
    storage = Storage()
    
    # 승리팀 조회
    if args.winners:
        date = datetime.now() - timedelta(days=1)
        winners = storage.get_winners(date)
        if winners:
            print(f"\n{date.strftime('%Y-%m-%d')} 승리팀:")
            for game in winners:
                print(f"  - {game['winner']}")
        else:
            print("어제 경기 결과가 없습니다.")
        return
    
    # 팀 통계 조회
    if args.team:
        stats = storage.get_team_stats(args.team)
        if stats:
            print(f"\n{args.team} 팀 통계:")
            print(f"  총 경기: {stats['total_games']}")
            print(f"  승리: {stats['wins']}")
            print(f"  패배: {stats['losses']}")
            print(f"  승률: {stats['win_rate']:.3f}")
        else:
            print(f"{args.team} 팀의 기록이 없습니다.")
        return
    
    # 크롤링 실행
    if args.date:
        # 특정 날짜 크롤링
        date = datetime.strptime(args.date, '%Y%m%d')
        logger.info(f"크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        if args.google or args.source == 'google':
            logger.info("구글 검색 크롤링 사용")
            games = run_google_real_crawler(date)
        elif args.kbo or args.source == 'kbo':
            logger.info("KBO 공식 사이트 크롤링 사용")
            games = run_kbo_official_crawler(date)
        else:
            games = run_crawler(date)
        
        if games:
            print(f"\n{date.strftime('%Y-%m-%d')} 경기 결과:")
            for game in games:
                print(f"  {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")
        else:
            print("경기 결과를 가져올 수 없습니다.")
            
    elif args.once or args.test:
        # 어제 경기 크롤링
        date = datetime.now() - timedelta(days=1)
        logger.info(f"크롤링 시작: {date.strftime('%Y-%m-%d')}")
        
        if args.google or args.source == 'google':
            logger.info("구글 검색 크롤링 사용")
            games = run_google_real_crawler(date)
        elif args.kbo or args.source == 'kbo':
            logger.info("KBO 공식 사이트 크롤링 사용")
            games = run_kbo_official_crawler(date)
        else:
            games = run_crawler(date)
        
        if games:
            print(f"\n{date.strftime('%Y-%m-%d')} 경기 결과:")
            for game in games:
                print(f"  {game['away_team']} {game['away_score']} - {game['home_score']} {game['home_team']} (승: {game['winner']})")
            
            if args.test:
                print("\n(테스트 모드: 더미 데이터 사용)")
        else:
            print("경기 결과를 가져올 수 없습니다.")
            
    else:
        # 스케줄러 실행
        print("스케줄러를 시작합니다. (매일 10:00 자동 크롤링)")
        print("중지하려면 Ctrl+C를 누르세요.")
        scheduler = Scheduler()
        scheduler.start()

if __name__ == "__main__":
    main()