# 로깅 시스템 구현 완료 요약

## 완성된 기능

프로젝트에 완전한 로깅 및 아카이브 관리 시스템이 구축되었습니다.

### 1. 핵심 컴포넌트

#### [runtime/logging_config.py](runtime/logging_config.py) (7.6K)
- **JSON 로그 포맷터**: 구조화된 로그를 JSON으로 저장하여 분석 용이
- **콘솔 포맷터**: 색상 코드가 포함된 읽기 쉬운 콘솔 출력
- **회전 파일 핸들러**: 자동 로그 파일 로테이션 (10MB 단위)
- **아카이버 통합**: 로그 압축 및 정리 기능 자동 초기화
- **공개 API**: 6가지 함수로 로그 관리 기능 제공

#### [runtime/log_archiver.py](runtime/log_archiver.py) (8.4K)
- **로그 압축**: ZIP/Gzip 형식 지원
- **날짜별 아카이브**: 특정 날짜의 모든 로그를 하나로 압축
- **자동 정리**: 설정된 기간보다 오래된 아카이브 자동 삭제
- **통계 조회**: 로그 및 아카이브 상태 모니터링
- **아카이브 목록**: 생성된 아카이브 파일 조회

### 2. 관리 도구

#### [manage_logs.py](manage_logs.py) (8.4K)
전체 로그를 관리하는 CLI 도구로 6가지 명령 제공:

| 명령 | 기능 |
|------|------|
| `archive` | 오래된 로그를 ZIP/Gzip으로 압축 |
| `daily-archive` | 특정 날짜의 모든 로그를 ZIP으로 아카이브 |
| `cleanup` | 오래된 아카이브 파일 자동 삭제 |
| `stats` | 현재 로그 및 아카이브 통계 표시 |
| `list` | 생성된 모든 아카이브 목록 표시 |
| `full-maintenance` | 압축 + 정리 일괄 처리 (자동 유지보수) |

### 3. 테스트 및 문서

#### [test_logging_system.py](test_logging_system.py) (5.5K)
5가지 테스트 케이스로 전체 로깅 시스템 검증:
- 기본 로깅 (DEBUG, INFO, WARNING, ERROR)
- 아카이브 통계 조회
- 파일 로깅 기능
- 아카이브 목록 조회
- 에러 로깅 (예외 정보 포함)

**테스트 결과**: ✅ 모든 테스트 통과

#### [LOG_MANAGEMENT_GUIDE.md](LOG_MANAGEMENT_GUIDE.md) (9.9K)
완전한 사용 설명서 포함:
- 기본 사용법
- 명령어 레퍼런스
- 로그 파일 형식
- 자동화 설정 (스케줄 작업)
- 예제 코드
- 트러블슈팅
- API 레퍼런스
- 성능 고려사항
- 보안 고려사항

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    애플리케이션                              │
└──────────┬──────────────────────────────────────────────────┘
           │
           ├─ setup_logging()
           └─ get_logger()
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│         runtime/logging_config.py (로깅 설정)               │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│ │ Console Handler │  │  File Handler    │  │ Error Handler
│ │ (컬러 출력)     │  │ (JSON format)    │  │ (에러만)    │
│ └─────────────────┘  └──────────────────┘  └─────────────┘ │
│        │                      │                    │         │
│        └──────────────────────┴────────────────────┘         │
│                       logs/                                  │
│         ┌─────────────────────────────────┐                 │
│         │ api_server.json.log             │                 │
│         │ error.log                       │                 │
│         │ (로테이션 파일들)               │                 │
│         └─────────────────────────────────┘                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      runtime/log_archiver.py (아카이브 관리)                │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│ │ 압축 (ZIP)   │  │ 날짜별 아카이브 │  │ 자동 정리 (삭제) │  │
│ │ 압축 (Gzip)  │  │ 통계 조회      │  │ 목록 조회        │  │
│ └──────────────┘  └────────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                    logs/archive/
         ┌──────────────────────────────────┐
         │ logs_archive_2024-12-01.zip      │
         │ logs_archive_2024-12-02.zip      │
         │ error.log.gz                     │
         └──────────────────────────────────┘
```

## 주요 특징

### 1. 자동 로테이션
- 로그 파일이 10MB 도달 시 자동으로 백업 생성
- 최대 30개의 로그 파일 유지

### 2. JSON 기반 저장
```json
{
  "timestamp": "2025-12-02T14:20:00.123456Z",
  "level": "INFO",
  "logger": "module_name",
  "message": "요청 완료",
  "request_id": "abc123",
  "duration_ms": 150.5
}
```

### 3. 완전 자동화
```bash
# 매일 자동으로 실행되도록 설정 가능
python manage_logs.py full-maintenance
```

### 4. 통합된 아카이빙
- 오래된 로그 자동 압축
- 압축 형식 선택 가능 (ZIP/Gzip)
- 오래된 아카이브 자동 삭제

## 빠른 시작

### 1. 기본 사용

```python
from runtime.logging_config import setup_logging, get_logger

# 초기화
setup_logging(log_dir="logs", log_level="INFO", enable_archiver=True)

# 로깅
logger = get_logger(__name__)
logger.info("안녕하세요!")
logger.error("에러 발생!", exc_info=True)
```

### 2. 로그 관리

```bash
# 현재 상태 확인
python manage_logs.py stats

# 오래된 로그 압축
python manage_logs.py archive --older-than-days 7

# 오래된 아카이브 삭제
python manage_logs.py cleanup --keep-days 30

# 전체 유지보수
python manage_logs.py full-maintenance
```

### 3. 테스트

```bash
python test_logging_system.py
```

## 통합 예제

### FastAPI 애플리케이션

```python
from fastapi import FastAPI
from runtime.logging_config import setup_logging, get_logger

# 로깅 설정
setup_logging(log_dir="logs", log_level="INFO", enable_archiver=True)
logger = get_logger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("애플리케이션 시작")

@app.get("/api/endpoint")
async def endpoint():
    logger.info("요청 처리")
    return {"status": "ok"}
```

## 자동화 설정

### Windows Task Scheduler
1. 작업 스케줄러 열기
2. "기본 작업 만들기"
3. 이름: "로그 유지보수"
4. 트리거: 매일 오전 2시
5. 작업: `python D:\12-02\manage_logs.py full-maintenance`

### Linux/macOS (Cron)
```bash
# 매일 오전 2시 실행
0 2 * * * cd /path/to/project && python manage_logs.py full-maintenance
```

## 디스크 사용량 관리

### 현재 상태 확인
```bash
python manage_logs.py stats
```

### 권장 설정
- **로그 파일**: 10MB 회전 (최대 30개)
- **아카이브 보유**: 30일
- **압축 기준**: 7일 이상 된 파일

### 계산 예시
```
로그 파일: 10MB × 30개 = 300MB
아카이브: 일반적으로 80% 압축 = 60MB/월
총 소비: ~1.2GB/월
```

## 문제 해결

### 1. 로그 파일이 생성되지 않음
```bash
mkdir -p logs/archive
python -c "from runtime.logging_config import setup_logging; setup_logging()"
```

### 2. 아카이브 실패
```bash
# 디스크 공간 확인
df -h

# 오래된 아카이브 정리
python manage_logs.py cleanup --keep-days 7
```

### 3. 권한 문제
```bash
# 로그 디렉토리 권한 설정
chmod -R 755 logs/
```

## 추가 리소스

- [LOG_MANAGEMENT_GUIDE.md](LOG_MANAGEMENT_GUIDE.md) - 상세 사용 설명서
- [runtime/logging_config.py](runtime/logging_config.py) - 로깅 설정 코드
- [runtime/log_archiver.py](runtime/log_archiver.py) - 아카이버 코드
- [manage_logs.py](manage_logs.py) - CLI 도구
- [test_logging_system.py](test_logging_system.py) - 테스트 스크립트

## 다음 단계

1. **애플리케이션 통합**: 기존 코드에서 `setup_logging()` 호출
2. **자동화 설정**: 스케줄 작업 또는 Cron으로 `full-maintenance` 설정
3. **모니터링**: 정기적으로 `stats` 명령어로 상태 확인
4. **커스터마이제이션**: 필요에 따라 로그 레벨, 파일 크기, 보유 기간 조정

---

구현 완료: 2025-12-02
버전: 1.0.0
