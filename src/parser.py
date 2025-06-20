from bs4 import BeautifulSoup
import re
from datetime import datetime
from .logger import setup_logger

class GameParser:
    def __init__(self):
        self.logger = setup_logger('GameParser')
        
    def parse_team_name(self, team_name):
        """  t� �T"""
        #   t� �Q
        team_mapping = {
            'KIA': 'KIA',
            'LG': 'LG',
            'NC': 'NC',
            'KT': 'KT',
            'SSG': 'SSG',
            '\T': '\T',
            'op': 'op',
            '�1': '�1',
            'P�': 'P�',
            '��': '��',
            'KIA�tp�': 'KIA',
            'LG��': 'LG',
            'NC�tx�': 'NC',
            'KT�': 'KT',
            'SSG�T�': 'SSG',
            '\Tt �': '\T',
            'op�t� ': 'op',
            '�1|t(�': '�1',
            'P����': 'P�',
            '����\�': '��'
        }
        
        # �T
        cleaned_name = team_name.strip()
        for key, value in team_mapping.items():
            if key in cleaned_name:
                return value
                
        return cleaned_name
        
    def parse_score(self, score_text):
        """ �"""
        try:
            # +�� ��
            score = re.findall(r'\d+', str(score_text))
            if score:
                return int(score[0])
            return None
        except:
            return None
            
    def parse_game_status(self, status_text):
        """�0 �� �"""
        if not status_text:
            return "��"
            
        status = status_text.strip().lower()
        
        if any(word in status for word in ['��', ']', 'final', 'f']):
            return "��"
        elif any(word in status for word in ['�', 'cancel', '��']):
            return "�"
        elif any(word in status for word in ['�0', 'postpone']):
            return "�0"
        else:
            return "ĉ"
            
    def determine_winner(self, away_score, home_score, away_team, home_team):
        """��  �"""
        if away_score is None or home_score is None:
            return None
            
        if away_score > home_score:
            return away_team
        elif home_score > away_score:
            return home_team
        else:
            return "4��"
            
    def parse_naver_sports(self, html_content, date):
        """$t� ��  HTML �"""
        games = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # �\  ݐ ��
        selectors = [
            'div.sch_tb',
            'div.game_schedule',
            'table.schedule_table tr',
            'div.game_result'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                self.logger.info(f" ݐ {selector}\ {len(elements)} �� �")
                break
                
        # �0 � ��
        for element in elements:
            try:
                game_info = self._extract_game_info_naver(element, date)
                if game_info:
                    games.append(game_info)
            except Exception as e:
                self.logger.error(f"�� � ��: {e}")
                continue
                
        return games
        
    def _extract_game_info_naver(self, element, date):
        """$t� ��  �� � ��"""
        #   �
        teams = element.select('span.team_lft, span.team_rgt, span.team')
        if len(teams) < 2:
            return None
            
        away_team = self.parse_team_name(teams[0].text)
        home_team = self.parse_team_name(teams[1].text)
        
        #  �
        scores = element.select('strong.td_score, span.score, em.score')
        if len(scores) < 2:
            return None
            
        away_score = self.parse_score(scores[0].text)
        home_score = self.parse_score(scores[1].text)
        
        if away_score is None or home_score is None:
            return None
            
        # �0 ��
        status_elem = element.select_one('span.td_hour, span.state, span.status')
        status = self.parse_game_status(status_elem.text if status_elem else "��")
        
        if status != "��":
            return None
            
        # �� 
        winner = self.determine_winner(away_score, home_score, away_team, home_team)
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'away_team': away_team,
            'home_team': home_team,
            'away_score': away_score,
            'home_score': home_score,
            'winner': winner,
            'status': status
        }
        
    def parse_kbo_official(self, json_data, date):
        """KBO �� API Q� �"""
        games = []
        
        if not isinstance(json_data, list):
            if 'd' in json_data and 'list' in json_data['d']:
                json_data = json_data['d']['list']
            elif 'data' in json_data:
                json_data = json_data['data']
            else:
                return games
                
        for game in json_data:
            try:
                # �0 �� Ux
                status = game.get('gmsc', game.get('status', ''))
                if status not in ['F', '��', 'FINAL']:
                    continue
                    
                #   �
                away_team = self.parse_team_name(game.get('awayNm', game.get('away_team', '')))
                home_team = self.parse_team_name(game.get('homeNm', game.get('home_team', '')))
                
                #  �
                away_score = int(game.get('asc', game.get('away_score', 0)))
                home_score = int(game.get('hsc', game.get('home_score', 0)))
                
                # �� 
                winner = self.determine_winner(away_score, home_score, away_team, home_team)
                
                game_info = {
                    'date': date.strftime('%Y-%m-%d'),
                    'away_team': away_team,
                    'home_team': home_team,
                    'away_score': away_score,
                    'home_score': home_score,
                    'winner': winner,
                    'stadium': game.get('stadium', ''),
                    'game_time': game.get('time', '')
                }
                
                games.append(game_info)
                
            except Exception as e:
                self.logger.error(f"KBO �� � ��: {e}")
                continue
                
        return games