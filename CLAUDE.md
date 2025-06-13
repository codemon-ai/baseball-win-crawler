# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KBO (Korean Baseball Organization) 야구 경기 결과를 자동으로 수집하여 승리팀 정보를 저장하는 크롤러 프로젝트입니다.

## Common Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Crawler
```bash
# 어제 경기 결과 크롤링 (한 번만 실행)
python main.py --once

# 특정 날짜 크롤링 (YYYYMMDD 형식)
python main.py --date 20241015

# 스케줄러 모드 (매일 10:00 자동 실행)
python main.py

# 어제 승리팀 조회
python main.py --winners

# 특정 팀 통계 조회
python main.py --team KIA
```

### Testing
```bash
# 모든 테스트 실행
python -m pytest tests/

# 직접 테스트 실행
python tests/test_crawler.py
```

## Architecture

### Crawler Strategy Pattern
프로젝트는 여러 크롤링 전략을 구현하여 안정성을 확보합니다:
1. `SimpleCrawler` → `KBOAPICrawler` → `SeleniumCrawler` 순서로 폴백
2. 각 크롤러는 독립적으로 작동하며 실패 시 다음 크롤러로 전환

### Data Flow
1. **Crawling**: 웹사이트에서 HTML/JSON 데이터 수집
2. **Parsing**: GameParser가 팀명, 점수, 승리팀 추출
3. **Storage**: DataStorage가 JSON/CSV 형식으로 저장
4. **Scheduling**: 매일 자동 실행 (schedule 라이브러리 사용)

### Module Structure
- `src/crawler.py`: Selenium 기반 동적 페이지 크롤러
- `src/kbo_api_crawler.py`: KBO 공식 API 크롤러
- `src/simple_crawler.py`: requests/BeautifulSoup 크롤러 (메인)
- `src/parser.py`: HTML/JSON 파싱 로직
- `src/storage.py`: 데이터 저장 및 통계 관리
- `src/scheduler.py`: 자동 실행 스케줄러
- `src/logger.py`: 로깅 설정
- `src/config.py`: 전역 설정 (URL, 팀명 매핑 등)

### Data Storage Format
- `data/kbo_results_YYYYMMDD.json`: 전체 경기 결과
- `data/winners_YYYYMMDD.json`: 승리팀만 추출
- `data/monthly_summary_YYYYMM.json`: 월간 통계
- `logs/crawler_YYYYMMDD.log`: 실행 로그

### Key Design Decisions
1. **다중 데이터 소스**: KBO 공식 사이트와 네이버 스포츠를 모두 지원
2. **인코딩 처리**: 한글 처리를 위한 UTF-8 인코딩 일관성 유지
3. **팀명 정규화**: 다양한 형식의 팀명을 표준화 (예: "KIA타이거즈" → "KIA")
4. **더미 데이터**: 개발/테스트용 더미 데이터 제공

## Important Configuration

`src/config.py`의 주요 설정:
- `SCHEDULE_TIME`: 일일 크롤링 실행 시간 (기본값: "10:00")
- `TEAM_NAMES`: 팀명 매핑 딕셔너리
- `KBO_SCHEDULE_URL`, `KBO_RESULT_URL`: 크롤링 대상 URL

## Development Notes

### 크롤링 실패 시 대응
1. 네트워크 연결 확인
2. 대상 사이트 구조 변경 확인 (HTML 선택자 업데이트 필요)
3. 로그 파일에서 상세 에러 확인

### 새로운 크롤러 추가 시
1. `src/` 디렉토리에 새 크롤러 클래스 생성
2. `run(date)` 메서드 구현 (게임 리스트 반환)
3. `scheduler.py`에서 폴백 체인에 추가

### 테스트 데이터
개발 중에는 `SimpleCrawler.get_dummy_data()`가 테스트 데이터를 제공합니다. 
실제 운영 시에는 이 메서드를 제거하거나 조건부로 비활성화하세요.