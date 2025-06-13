import json
import pandas as pd
import os
from datetime import datetime
from .logger import setup_logger
from .config import DATA_DIR

class Storage:
    def __init__(self):
        self.logger = setup_logger('Storage')
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """데이터 디렉토리 확인 및 생성"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            self.logger.info(f"데이터 디렉토리 생성: {DATA_DIR}")
            
    def save_json(self, data, filename):
        """JSON 파일 저장"""
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"JSON 파일 저장: {filepath}")
        
    def load_json(self, filename):
        """JSON 파일 로드"""
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
        
    def save_csv(self, data, filename):
        """CSV 파일 저장"""
        filepath = os.path.join(DATA_DIR, filename)
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        self.logger.info(f"CSV 파일 저장: {filepath}")
        
    def get_winners(self, date):
        """특정 날짜의 승리팀 조회"""
        date_str = date.strftime('%Y%m%d')
        filename = f'winners_{date_str}.json'
        
        winners = self.load_json(filename)
        if winners:
            return winners
            
        # 전체 경기 결과에서 추출
        games_filename = f'kbo_results_{date_str}.json'
        games = self.load_json(games_filename)
        
        if games:
            winners = []
            for game in games:
                if 'winner' in game:
                    winners.append({
                        'date': game.get('date', date.strftime('%Y-%m-%d')),
                        'winner': game['winner'],
                        'game': f"{game.get('away_team', '?')} vs {game.get('home_team', '?')}"
                    })
            return winners
            
        return []
        
    def get_team_stats(self, team_name):
        """팀별 통계 조회"""
        stats = {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0
        }
        
        # 모든 JSON 파일에서 팀 검색
        for filename in os.listdir(DATA_DIR):
            if filename.startswith('kbo_results_') and filename.endswith('.json'):
                games = self.load_json(filename)
                if games:
                    for game in games:
                        if team_name in [game.get('home_team'), game.get('away_team')]:
                            stats['total_games'] += 1
                            if game.get('winner') == team_name:
                                stats['wins'] += 1
                            else:
                                stats['losses'] += 1
                                
        if stats['total_games'] > 0:
            stats['win_rate'] = stats['wins'] / stats['total_games']
            
        return stats
        
    def get_monthly_summary(self, year, month):
        """월간 요약 통계"""
        summary = {}
        
        # 해당 월의 모든 파일 검색
        for day in range(1, 32):
            date_str = f"{year}{month:02d}{day:02d}"
            filename = f'kbo_results_{date_str}.json'
            
            games = self.load_json(filename)
            if games:
                for game in games:
                    winner = game.get('winner')
                    if winner:
                        if winner not in summary:
                            summary[winner] = {'wins': 0, 'games': 0}
                        summary[winner]['wins'] += 1
                        
                    # 모든 참가 팀의 게임 수 카운트
                    for team in [game.get('home_team'), game.get('away_team')]:
                        if team:
                            if team not in summary:
                                summary[team] = {'wins': 0, 'games': 0}
                            summary[team]['games'] += 1
                            
        # 승률 계산
        for team, stats in summary.items():
            if stats['games'] > 0:
                stats['win_rate'] = stats['wins'] / stats['games']
            else:
                stats['win_rate'] = 0.0
                
        return summary