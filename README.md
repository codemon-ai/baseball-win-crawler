# KBO 야구 승리팀 크롤러

한국 프로야구(KBO) 경기 결과를 자동으로 수집하여 승리팀 정보를 저장하는 크롤러입니다.

## 기능

- KBO 경기 결과 자동 수집
- 승리팀, 점수, 날짜 정보 파싱
- 데이터 저장 (JSON/CSV)
- 매일 자동 실행 스케줄러
- 팀별 통계 조회
- 에러 로깅

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt
```

## 사용법

### 1. 한 번 실행 (어제 경기 크롤링)
```bash
python main.py --once
```

### 2. 특정 날짜 크롤링
```bash
python main.py --date 20241015
```

### 3. 스케줄러 실행 (매일 10:00 자동 크롤링)
```bash
python main.py
```

### 4. 어제 승리팀 조회
```bash
python main.py --winners
```

### 5. 특정 팀 통계 조회
```bash
python main.py --team KIA
```

### 6. 테스트 실행
```bash
python -m pytest tests/
# 또는
python tests/test_crawler.py
```

## 데이터 형식

### 경기 결과 (JSON)
```json
{
  "date": "2024-10-15",
  "away_team": "KIA",
  "home_team": "LG",
  "away_score": 5,
  "home_score": 3,
  "winner": "KIA"
}
```

### 저장 파일
- `data/kbo_results_YYYYMMDD.json` - 전체 경기 결과
- `data/kbo_results_YYYYMMDD.csv` - CSV 형식
- `data/winners_YYYYMMDD.json` - 승리팀만 추출
- `data/monthly_summary_YYYYMM.json` - 월간 집계

## 프로젝트 구조

```
baseball-win-crawler/
├── main.py             # 메인 실행 파일
├── src/
│   ├── crawler.py      # Selenium 크롤러
│   ├── kbo_api_crawler.py  # API 크롤러
│   ├── simple_crawler.py   # 간단한 크롤러
│   ├── parser.py       # HTML/JSON 파싱
│   ├── storage.py      # 데이터 저장
│   ├── scheduler.py    # 스케줄러
│   ├── logger.py       # 로깅
│   └── config.py       # 설정
├── tests/              # 테스트 코드
├── data/               # 수집된 데이터
├── logs/               # 로그 파일
└── requirements.txt    # 의존성
```

## 주의사항

- 크롤링 대상 사이트의 구조가 변경되면 파싱 로직 수정이 필요할 수 있습니다
- 과도한 요청은 차단될 수 있으므로 적절한 딜레이를 설정하세요
- Selenium 사용 시 Chrome 드라이버가 자동으로 설치됩니다

## 문제 해결

1. **크롤링 실패 시**
   - 네트워크 연결 확인
   - 대상 사이트 접속 가능 여부 확인
   - 로그 파일 확인 (`logs/crawler_YYYYMMDD.log`)

2. **Selenium 오류 시**
   - Chrome 브라우저 설치 확인
   - `webdriver-manager` 재설치

3. **데이터 없음**
   - 월요일은 일반적으로 경기가 없습니다
   - 날짜 형식 확인 (YYYYMMDD)