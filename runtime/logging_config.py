"""
프로덕션급 로깅 설정 모듈

구조화된 JSON 로깅과 파일 로테이션, 자동 아카이빙을 제공합니다.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import json
from logging.handlers import RotatingFileHandler
from runtime.log_archiver import LogArchiver


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 요청 ID가 있으면 추가
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # 처리 시간이 있으면 추가
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        # 예외 정보가 있으면 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """콘솔용 읽기 쉬운 포맷터"""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # 요청 ID 추가
        request_id = getattr(record, "request_id", "")
        if request_id:
            record.msg = f"[{request_id}] {record.msg}"
        
        return super().format(record)


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 30,
    enable_archiver: bool = True,
) -> logging.Logger:
    """
    로깅 설정 (아카이브 기능 포함)

    Args:
        log_dir: 로그 파일 디렉토리
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
        enable_archiver: 아카이브 기능 활성화 여부

    Returns:
        설정된 로거
    """
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # 기존 핸들러 제거
    logger.handlers.clear()

    # 콘솔 핸들러 (읽기 쉬운 포맷)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ConsoleFormatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (JSON 포맷)
    json_file = log_path / "api_server.json.log"
    file_handler = RotatingFileHandler(
        json_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # 파일에는 모든 레벨 저장
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # 에러 전용 파일 핸들러
    error_file = log_path / "error.log"
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)

    # 아카이버 설정 (전역 변수에 저장)
    if enable_archiver:
        global _archiver
        _archiver = LogArchiver(log_dir=log_dir, archive_dir=f"{log_dir}/archive")

    logger.info(f"로깅 설정 완료: {log_dir} (레벨: {log_level}, 아카이브: {enable_archiver})")

    return logger


# 전역 아카이버 인스턴스
_archiver: Optional[LogArchiver] = None


def get_logger(name: str) -> logging.Logger:
    """
    이름으로 로거 가져오기

    Args:
        name: 로거 이름 (보통 __name__)

    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)


def archive_logs(older_than_days: int = 7, archive_type: str = "zip") -> dict:
    """
    오래된 로그 파일을 아카이브

    Args:
        older_than_days: 이 날짜보다 오래된 파일을 압축
        archive_type: 압축 형식 ('zip' 또는 'gz')

    Returns:
        압축 결과 딕셔너리
    """
    if _archiver is None:
        logger = logging.getLogger(__name__)
        logger.warning("아카이버가 초기화되지 않았습니다. setup_logging에서 enable_archiver=True를 설정하세요.")
        return {}

    return _archiver.compress_logs(older_than_days=older_than_days, archive_type=archive_type)


def create_daily_archive(date_str: Optional[str] = None) -> Optional[str]:
    """
    날짜별 종합 아카이브 생성

    Args:
        date_str: 아카이브 날짜 (기본값: 어제)

    Returns:
        생성된 아카이브 파일 경로
    """
    if _archiver is None:
        logger = logging.getLogger(__name__)
        logger.warning("아카이버가 초기화되지 않았습니다. setup_logging에서 enable_archiver=True를 설정하세요.")
        return None

    result = _archiver.create_daily_archive(date_str=date_str)
    return str(result) if result else None


def cleanup_old_archives(keep_days: int = 30) -> int:
    """
    오래된 아카이브 파일 정리

    Args:
        keep_days: 유지할 기간 (기본값: 30일)

    Returns:
        삭제된 파일 개수
    """
    if _archiver is None:
        logger = logging.getLogger(__name__)
        logger.warning("아카이버가 초기화되지 않았습니다. setup_logging에서 enable_archiver=True를 설정하세요.")
        return 0

    return _archiver.cleanup_old_archives(keep_days=keep_days)


def get_archive_stats() -> dict:
    """
    아카이브 통계 조회

    Returns:
        아카이브 통계 딕셔너리
    """
    if _archiver is None:
        logger = logging.getLogger(__name__)
        logger.warning("아카이버가 초기화되지 않았습니다. setup_logging에서 enable_archiver=True를 설정하세요.")
        return {}

    return _archiver.get_archive_stats()


def list_archives() -> list:
    """
    아카이브 파일 목록 조회

    Returns:
        아카이브 파일 정보 리스트
    """
    if _archiver is None:
        logger = logging.getLogger(__name__)
        logger.warning("아카이버가 초기화되지 않았습니다. setup_logging에서 enable_archiver=True를 설정하세요.")
        return []

    return _archiver.list_archives()
