from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json
from .logger import setup_logger
from .config import DATA_DIR, TEAM_NAMES
import os

class KBOCrawler:
    def __init__(self):
        self.logger = setup_logger('KBOCrawler')
        self.driver = None
        
    def setup_driver(self):
        """Selenium �|t� $"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 1�|�� �
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("Selenium �|t� $ D�")
        except Exception as e:
            self.logger.error(f"�|t� $ �(: {e}")
            raise
            
    def close_driver(self):
        """�|t� ��"""
        if self.driver:
            self.driver.quit()
            self.logger.info("�|t� ��")
            
    def crawl_kbo_results(self, date=None):
        """KBO �0 �� ld�"""
        if date is None:
            date = datetime.now() - timedelta(days=1)  # � ��
            
        date_str = date.strftime('%Y%m%d')
        self.logger.info(f"ld� ��: {date_str}")
        
        try:
            # $t� ��  KBO | �t�
            url = f"https://sports.news.naver.com/kbaseball/schedule/index.nhn?date={date_str}"
            self.logger.info(f"� URL: {url}")
            
            self.driver.get(url)
            
            # �t� \)  0
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sch_tb")))
            
            time.sleep(2)  # � �P  \)  0
            
            # BeautifulSoup<\ �
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # �0 �� ��
            games = []
            game_boxes = soup.find_all('div', class_='sch_tb')
            
            for game_box in game_boxes:
                try:
                    # �0 ��
                    game_date = date.strftime('%Y-%m-%d')
                    
                    #   �
                    teams = game_box.find_all('span', class_=['team_lft', 'team_rgt'])
                    if len(teams) >= 2:
                        away_team = teams[0].text.strip()
                        home_team = teams[1].text.strip()
                    else:
                        continue
                        
                    #  �
                    scores = game_box.find_all('strong', class_='td_score')
                    if len(scores) >= 2:
                        away_score = scores[0].text.strip()
                        home_score = scores[1].text.strip()
                        
                        #   +�x� Ux
                        if away_score.isdigit() and home_score.isdigit():
                            away_score = int(away_score)
                            home_score = int(home_score)
                            
                            # ��  �
                            if away_score > home_score:
                                winner = away_team
                            elif home_score > away_score:
                                winner = home_team
                            else:
                                winner = "4��"
                                
                            game_info = {
                                'date': game_date,
                                'away_team': away_team,
                                'home_team': home_team,
                                'away_score': away_score,
                                'home_score': home_score,
                                'winner': winner
                            }
                            
                            games.append(game_info)
                            self.logger.info(f"�0 ��: {away_team} {away_score} - {home_score} {home_team}, ��: {winner}")
                            
                except Exception as e:
                    self.logger.error(f"�0 � ��: {e}")
                    continue
                    
            return games
            
        except Exception as e:
            self.logger.error(f"ld� ��: {e}")
            return []
            
    def save_results(self, games, date):
        """��  �"""
        if not games:
            self.logger.warning(" �` �0 ��  Ƶ��.")
            return
            
        # JSON |\  �
        date_str = date.strftime('%Y%m%d')
        filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"��  � D�: {filename}")
        
        # CSV |\�  �
        csv_filename = os.path.join(DATA_DIR, f'kbo_results_{date_str}.csv')
        import pandas as pd
        df = pd.DataFrame(games)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"CSV  � D�: {csv_filename}")
        
    def run(self, date=None):
        """ld� �"""
        try:
            self.setup_driver()
            games = self.crawl_kbo_results(date)
            
            if games:
                self.save_results(games, date if date else datetime.now() - timedelta(days=1))
                return games
            else:
                self.logger.warning("ld� �0 ��  Ƶ��.")
                return []
                
        finally:
            self.close_driver()

# L��� �
if __name__ == "__main__":
    crawler = KBOCrawler()
    
    # 2024D 10� 15| pt0 L��
    test_date = datetime(2024, 10, 15)
    results = crawler.run(test_date)
    
    print(f"\n {len(results)} �0 ld� D�")