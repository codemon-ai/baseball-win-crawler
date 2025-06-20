import unittest
from datetime import datetime
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import GameParser
from src.storage import DataStorage
from src.config import DATA_DIR

class TestGameParser(unittest.TestCase):
    def setUp(self):
        self.parser = GameParser()
        
    def test_parse_team_name(self):
        """  t� �T L��"""
        self.assertEqual(self.parser.parse_team_name('KIA�tp�'), 'KIA')
        self.assertEqual(self.parser.parse_team_name('LG��'), 'LG')
        self.assertEqual(self.parser.parse_team_name('KIA'), 'KIA')
        self.assertEqual(self.parser.parse_team_name(' SSG '), 'SSG')
        
    def test_parse_score(self):
        """ � L��"""
        self.assertEqual(self.parser.parse_score('5'), 5)
        self.assertEqual(self.parser.parse_score('10'), 10)
        self.assertEqual(self.parser.parse_score(': 7'), 7)
        self.assertIsNone(self.parser.parse_score(''))
        self.assertIsNone(self.parser.parse_score('�L'))
        
    def test_parse_game_status(self):
        """�0 �� � L��"""
        self.assertEqual(self.parser.parse_game_status('��'), '��')
        self.assertEqual(self.parser.parse_game_status('FINAL'), '��')
        self.assertEqual(self.parser.parse_game_status('�'), '�')
        self.assertEqual(self.parser.parse_game_status('���'), '�')
        self.assertEqual(self.parser.parse_game_status('5�'), 'ĉ')
        
    def test_determine_winner(self):
        """��  � L��"""
        self.assertEqual(self.parser.determine_winner(5, 3, 'KIA', 'LG'), 'KIA')
        self.assertEqual(self.parser.determine_winner(2, 7, 'NC', 'SSG'), 'SSG')
        self.assertEqual(self.parser.determine_winner(4, 4, '\T', 'P�'), '4��')
        self.assertIsNone(self.parser.determine_winner(None, 5, 'KT', '�1'))
        
class TestDataStorage(unittest.TestCase):
    def setUp(self):
        self.storage = DataStorage()
        self.test_date = datetime(2024, 10, 15)
        self.test_data = [
            {
                'date': '2024-10-15',
                'away_team': 'KIA',
                'home_team': 'LG',
                'away_score': 5,
                'home_score': 3,
                'winner': 'KIA'
            },
            {
                'date': '2024-10-15',
                'away_team': 'NC',
                'home_team': 'SSG',
                'away_score': 2,
                'home_score': 4,
                'winner': 'SSG'
            }
        ]
        
    def test_save_and_load_json(self):
        """JSON  �  \� L��"""
        filename = 'test_data.json'
        
        #  �
        self.assertTrue(self.storage.save_json(self.test_data, filename))
        
        # \�
        loaded_data = self.storage.load_json(filename)
        self.assertEqual(loaded_data, self.test_data)
        
        # | �
        os.remove(os.path.join(DATA_DIR, filename))
        
    def test_save_csv(self):
        """CSV  � L��"""
        filename = 'test_data.csv'
        
        #  �
        self.assertTrue(self.storage.save_csv(self.test_data, filename))
        
        # | t� Ux
        filepath = os.path.join(DATA_DIR, filename)
        self.assertTrue(os.path.exists(filepath))
        
        # | �
        os.remove(filepath)
        
    def test_save_game_results(self):
        """�0 ��  � L��"""
        #  �
        self.assertTrue(self.storage.save_game_results(self.test_data, self.test_date))
        
        # |� t� Ux
        date_str = self.test_date.strftime('%Y%m%d')
        json_file = os.path.join(DATA_DIR, f'kbo_results_{date_str}.json')
        csv_file = os.path.join(DATA_DIR, f'kbo_results_{date_str}.csv')
        winners_file = os.path.join(DATA_DIR, f'winners_{date_str}.json')
        
        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(csv_file))
        self.assertTrue(os.path.exists(winners_file))
        
        # ��  pt0 Ux
        winners = self.storage.load_json(f'winners_{date_str}.json')
        self.assertEqual(len(winners), 2)
        self.assertEqual(winners[0]['winner'], 'KIA')
        self.assertEqual(winners[1]['winner'], 'SSG')
        
        # | �
        for file in [json_file, csv_file, winners_file]:
            if os.path.exists(file):
                os.remove(file)
                
        # � �� |� �
        month_file = os.path.join(DATA_DIR, f'monthly_summary_{self.test_date.strftime("%Y%m")}.json')
        if os.path.exists(month_file):
            os.remove(month_file)
            
class TestIntegration(unittest.TestCase):
    def test_parser_with_sample_html(self):
        """� HTML � �i L��"""
        parser = GameParser()
        
        # � HTML ($t� ��  �)
        sample_html = '''
        <div class="sch_tb">
            <span class="team_lft">KIA</span>
            <strong class="td_score">5</strong>
            <strong class="td_score">3</strong>
            <span class="team_rgt">LG</span>
            <span class="td_hour">��</span>
        </div>
        '''
        
        date = datetime(2024, 10, 15)
        games = parser.parse_naver_sports(sample_html, date)
        
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['away_team'], 'KIA')
        self.assertEqual(games[0]['home_team'], 'LG')
        self.assertEqual(games[0]['away_score'], 5)
        self.assertEqual(games[0]['home_score'], 3)
        self.assertEqual(games[0]['winner'], 'KIA')
        
    def test_parser_with_kbo_json(self):
        """KBO API Q� � �i L��"""
        parser = GameParser()
        
        # � JSON (KBO API �)
        sample_json = [
            {
                'gmsc': 'F',
                'awayNm': 'KIA',
                'homeNm': 'LG', 
                'asc': '5',
                'hsc': '3',
                'stadium': '��',
                'time': '18:30'
            }
        ]
        
        date = datetime(2024, 10, 15)
        games = parser.parse_kbo_official(sample_json, date)
        
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['away_team'], 'KIA')
        self.assertEqual(games[0]['home_team'], 'LG')
        self.assertEqual(games[0]['away_score'], 5)
        self.assertEqual(games[0]['home_score'], 3)
        self.assertEqual(games[0]['winner'], 'KIA')

if __name__ == '__main__':
    unittest.main()