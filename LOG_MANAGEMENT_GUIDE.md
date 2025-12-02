# 로그 관리 시스템 가이드

이 문서는 프로젝트의 로깅 및 아카이브 관리 시스템 사용법을 설명합니다.

## 개요

로깅 시스템은 다음 기능을 제공합니다:

- **구조화된 로깅**: JSON 형식으로 로그를 기록하여 파싱과 분석이 용이
- **파일 로테이션**: 자동으로 로그 파일을 회전시켜 디스크 공간 관리
- **자동 아카이빙**: 오래된 로그를 압축하여 저장
- **통계 조회**: 로그 및 아카이브 상태를 한눈에 확인

## 디렉토리 구조

```
d:/12-02/
├── runtime/
│   ├── logging_config.py      # 로깅 설정 (JSON, 콘솔, 파일 핸들러)
│   └── log_archiver.py        # 로그 아카이브 관리 (압축, 정리)
├── logs/                       # 로그 파일 저장 디렉토리
│   ├── api_server.json.log    # 주 로그 파일 (JSON)
│   ├── error.log              # 에러 전용 로그
│   ├── api_server.json.log.1  # 로그 로테이션 파일
│   └── archive/               # 아카이브 저장 디렉토리
│       └── logs_archive_2024-12-01.zip
├── manage_logs.py             # 로그 관리 CLI 도구
└── test_logging_system.py     # 로깅 시스템 테스트
```

## 기본 사용법

### 1. 코드에서 로깅 사용

#### 로깅 초기화

```python
from runtime.logging_config import setup_logging, get_logger

# 로깅 설정 (주로 앱 시작 시)
setup_logging(
    log_dir="logs",
    log_level="INFO",
    max_bytes=10*1024*1024,  # 10MB 파일 크기 제한
    backup_count=30,          # 최대 30개 로그 파일 유지
    enable_archiver=True      # 아카이브 기능 활성화
)
```

#### 로거 사용

```python
from runtime.logging_config import get_logger

logger = get_logger(__name__)

# 일반 로깅
logger.debug("디버그 메시지")
logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("에러 메시지")

# 요청 ID와 함께 로깅 (추적 용이)
logger.info(
    "사용자 요청 처리",
    extra={"request_id": "abc123", "duration_ms": 150}
)

# 예외 정보와 함께 로깅
try:
    result = 10 / 0
except ZeroDivisionError:
    logger.error("계산 실패", exc_info=True)
```

### 2. 로그 관리 CLI

manage_logs.py는 로그 파일을 관리하는 명령줄 도구입니다.

#### 명령어 목록

**아카이브 (압축)**
```bash
python manage_logs.py archive [--older-than-days DAYS] [--type zip|gz]
```
지정된 날짜보다 오래된 로그를 압축합니다.
- `--older-than-days`: 기준 날짜 (기본값: 7일)
- `--type`: 압축 형식, zip 또는 gz (기본값: zip)

예:
```bash
# 7일 이상 된 로그를 ZIP으로 압축
python manage_logs.py archive --older-than-days 7 --type zip

# 30일 이상 된 로그를 Gzip으로 압축
python manage_logs.py archive --older-than-days 30 --type gz
```

**날짜별 아카이브**
```bash
python manage_logs.py daily-archive [--date YYYY-MM-DD]
```
특정 날짜의 모든 로그를 하나의 ZIP 아카이브로 생성합니다.

예:
```bash
# 어제 로그의 종합 아카이브 생성
python manage_logs.py daily-archive

# 특정 날짜 아카이브 생성
python manage_logs.py daily-archive --date 2024-12-01
```

**정리 (Cleanup)**
```bash
python manage_logs.py cleanup [--keep-days DAYS]
```
지정된 기간보다 오래된 아카이브를 삭제합니다.

예:
```bash
# 30일 이상 된 아카이브 삭제
python manage_logs.py cleanup --keep-days 30

# 60일 이상 된 아카이브 삭제
python manage_logs.py cleanup --keep-days 60
```

**통계 조회**
```bash
python manage_logs.py stats
```
현재 로그 및 아카이브 상태를 표시합니다.

출력 예:
```
=== 로그 및 아카이브 통계 ===

로그 파일:
  - 파일 수: 2
  - 총 크기: 0.01 MB
  - 가장 오래된 파일: 2025-12-02T14:20:00.540611
  - 가장 최신 파일: 2025-12-02T14:20:23.458589

아카이브 파일:
  - 파일 수: 0
  - 총 크기: 0.00 MB
```

**목록 조회**
```bash
python manage_logs.py list
```
생성된 모든 아카이브 파일의 목록을 표시합니다.

출력 예:
```
=== 아카이브 목록 (2개) ===

파일명: logs_archive_2024-12-01.zip
  - 크기: 1.25 MB
  - 생성일: 2024-12-01T23:59:59.123456
  - 경로: logs/archive/logs_archive_2024-12-01.zip

파일명: error.log.zip
  - 크기: 0.05 MB
  - 생성일: 2024-12-02T10:30:00.654321
  - 경로: logs/archive/error.log.zip
```

**전체 유지보수**
```bash
python manage_logs.py full-maintenance [--older-than-days DAYS] [--keep-days DAYS]
```
로그 압축 + 아카이브 정리를 한번에 수행합니다.

예:
```bash
# 기본값으로 유지보수 실행 (7일 이상 로그 압축, 30일 이상 아카이브 삭제)
python manage_logs.py full-maintenance

# 커스텀 기준으로 실행
python manage_logs.py full-maintenance --older-than-days 14 --keep-days 60
```

## 로그 파일 형식

### JSON 로그 (api_server.json.log)

각 로그 항목은 JSON 형식으로 저장되어 파싱과 분석이 용이합니다:

```json
{
  "timestamp": "2025-12-02T14:20:00.123456Z",
  "level": "INFO",
  "logger": "module_name",
  "message": "요청 완료: GET /api/endpoint - 200",
  "module": "api_server",
  "function": "handle_request",
  "line": 42,
  "request_id": "abc123",
  "duration_ms": 150.5,
  "status_code": 200
}
```

### 에러 로그 (error.log)

ERROR 이상의 레벨만 기록되며, 예외 정보가 포함됩니다:

```json
{
  "timestamp": "2025-12-02T14:20:00.123456Z",
  "level": "ERROR",
  "logger": "module_name",
  "message": "TTS 생성 실패",
  "exception": "Traceback (most recent call last):\n  ...\nZeroDivisionError: division by zero"
}
```

## 자동화 설정

### 스케줄 작업 (Windows Task Scheduler)

매일 자동으로 로그를 정리하려면:

1. **작업 스케줄러 열기**
2. **기본 작업 만들기**
3. **트리거 설정**: 매일 오전 2시
4. **작업 설정**: 다음 프로그램 실행
   ```
   Program: python
   Arguments: D:\12-02\manage_logs.py full-maintenance
   Start in: D:\12-02
   ```

### Cron 작업 (Linux/macOS)

```bash
# 매일 오전 2시에 실행
0 2 * * * cd /path/to/project && python manage_logs.py full-maintenance
```

## 예제

### 예제 1: 주간 유지보수

```bash
# 매주 월요일 자정에 다음 명령 실행
python manage_logs.py full-maintenance --older-than-days 7 --keep-days 30
```

### 예제 2: 로그 분석

로그를 JSON으로 저장하므로 Python에서 쉽게 분석할 수 있습니다:

```python
import json
from pathlib import Path

log_file = Path("logs/api_server.json.log")
with open(log_file) as f:
    for line in f:
        log_entry = json.loads(line)
        if log_entry['level'] == 'ERROR':
            print(f"Error: {log_entry['message']}")
            print(f"Time: {log_entry['timestamp']}")
```

### 예제 3: 요청 추적

요청 ID를 사용하여 관련 로그를 추적합니다:

```python
import uuid
logger = get_logger(__name__)

request_id = str(uuid.uuid4())[:8]
logger.info("요청 시작", extra={"request_id": request_id})
# ... 처리 ...
logger.info("요청 완료", extra={"request_id": request_id})
```

그 후 요청 ID로 로그를 검색:

```bash
grep "abc123" logs/api_server.json.log | jq .
```

## 트러블슈팅

### 로그 파일이 생성되지 않음

**문제**: logs 디렉토리가 없거나 권한 문제

**해결**:
```bash
# 디렉토리 생성
mkdir -p logs/archive

# 권한 확인
ls -la logs/
```

### 아카이버가 초기화되지 않음

**문제**: `setup_logging(..., enable_archiver=False)`로 설정됨

**해결**:
```python
setup_logging(enable_archiver=True)
```

### 압축 실패

**문제**: 디스크 공간 부족 또는 권한 문제

**해결**:
```bash
# 디스크 공간 확인
df -h

# 로그 정리
python manage_logs.py cleanup --keep-days 7
```

## API 레퍼런스

### logging_config 모듈

```python
from runtime.logging_config import (
    setup_logging,           # 로깅 초기화
    get_logger,             # 로거 인스턴스 얻기
    archive_logs,           # 로그 아카이브
    create_daily_archive,   # 날짜별 아카이브
    cleanup_old_archives,   # 오래된 아카이브 정리
    get_archive_stats,      # 통계 조회
    list_archives           # 아카이브 목록 조회
)
```

### LogArchiver 클래스

```python
from runtime.log_archiver import LogArchiver

archiver = LogArchiver(log_dir="logs", archive_dir="logs/archive")

# 로그 압축
compressed = archiver.compress_logs(older_than_days=7, archive_type="zip")

# 날짜별 아카이브
path = archiver.create_daily_archive(date_str="2024-12-01")

# 오래된 아카이브 정리
deleted_count = archiver.cleanup_old_archives(keep_days=30)

# 통계
stats = archiver.get_archive_stats()

# 아카이브 목록
archives = archiver.list_archives()
```

## 성능 고려사항

### 로그 로테이션 설정

- **max_bytes**: 10MB (기본값) - 필요시 조정
- **backup_count**: 30 (기본값) - 최대 30개 로그 파일 유지

### 아카이브 보유 기간

- 기본값: 30일
- 스토리지 제약이 있으면 감소시키기
- 규제 요구사항이 있으면 증가시키기

### 성능 최적화

1. **배치 작업**: full-maintenance를 정기적으로 실행
2. **압축**: gzip이 zip보다 빠르고 효율적
3. **정리**: 오래된 아카이브를 주기적으로 삭제

## 보안 고려사항

- 로그 디렉토리 권한 제한 (민감 정보 포함 가능)
- 정기적인 아카이브 삭제로 저장 공간 관리
- 외부 스토리지로 장기 아카이브 백업 권장
