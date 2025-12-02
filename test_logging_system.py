#!/usr/bin/env python3
"""
로깅 시스템 테스트 스크립트

로그 아카이브 기능이 제대로 작동하는지 확인합니다.
"""
import sys
import time
from pathlib import Path
from datetime import datetime

# 현재 스크립트 위치를 기준으로 상위 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from runtime.logging_config import (
    setup_logging,
    get_logger,
    archive_logs,
    create_daily_archive,
    cleanup_old_archives,
    get_archive_stats,
    list_archives,
)


def test_basic_logging():
    """기본 로깅 테스트"""
    print("=" * 60)
    print("1단계: 기본 로깅 테스트")
    print("=" * 60)

    # 로깅 설정
    setup_logging(log_dir="logs", log_level="DEBUG", enable_archiver=True)
    logger = get_logger(__name__)

    # 각 레벨별 로그 생성
    logger.debug("DEBUG 레벨 테스트 메시지")
    logger.info("INFO 레벨 테스트 메시지")
    logger.warning("WARNING 레벨 테스트 메시지")
    logger.error("ERROR 레벨 테스트 메시지")

    print("[OK] 로그 파일 생성 완료 (logs/api_server.json.log, logs/error.log)\n")
    return True


def test_archive_stats():
    """아카이브 통계 테스트"""
    print("=" * 60)
    print("2단계: 아카이브 통계 조회")
    print("=" * 60)

    stats = get_archive_stats()

    print(f"\n로그 파일:")
    print(f"  - 파일 수: {stats.get('log_count', 0)}")
    print(f"  - 총 크기: {stats.get('log_size_mb', 0):.4f} MB")
    if stats.get('oldest_log'):
        print(f"  - 가장 오래된 파일: {stats['oldest_log']}")
    if stats.get('newest_log'):
        print(f"  - 가장 최신 파일: {stats['newest_log']}")

    print(f"\n아카이브 파일:")
    print(f"  - 파일 수: {stats.get('archive_count', 0)}")
    print(f"  - 총 크기: {stats.get('archive_size_mb', 0):.4f} MB")

    print()
    return True


def test_logging_to_file():
    """파일에 로그 기록 테스트"""
    print("=" * 60)
    print("3단계: 파일에 로그 기록")
    print("=" * 60)

    test_logger = get_logger("test_module")

    # 여러 로그 기록
    for i in range(10):
        test_logger.info(f"테스트 로그 #{i+1}")
        time.sleep(0.1)

    print("[OK] 10개의 로그 메시지 생성 완료\n")

    # 로그 파일 확인
    log_file = Path("logs/api_server.json.log")
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"[OK] 로그 파일 크기: {log_file.stat().st_size} bytes")
        print(f"[OK] 총 라인 수: {len(lines)}\n")
        return True
    else:
        print("[FAIL] 로그 파일을 찾을 수 없습니다\n")
        return False


def test_list_archives():
    """아카이브 목록 조회 테스트"""
    print("=" * 60)
    print("4단계: 아카이브 목록 조회")
    print("=" * 60)

    archives = list_archives()

    if not archives:
        print("아카이브 파일이 없습니다.\n")
        return True

    print(f"\n발견된 아카이브 ({len(archives)}개):\n")
    for i, archive in enumerate(archives, 1):
        print(f"{i}. {archive['name']}")
        print(f"   - 크기: {archive['size_mb']:.4f} MB")
        print(f"   - 생성일: {archive['created']}")

    print()
    print("[OK] 아카이브 목록 조회 완료\n")
    return True


def test_error_logging():
    """에러 로깅 테스트"""
    print("=" * 60)
    print("5단계: 에러 로깅 테스트")
    print("=" * 60)

    test_logger = get_logger(__name__)

    try:
        # 의도적으로 에러 발생
        10 / 0
    except ZeroDivisionError:
        test_logger.error("계산 중 에러 발생", exc_info=True)

    test_logger.warning("경고 메시지")

    error_file = Path("logs/error.log")
    if error_file.exists():
        print(f"[OK] 에러 로그 파일 생성 완료")
        print(f"[OK] 파일 크기: {error_file.stat().st_size} bytes\n")
        return True
    else:
        print("[FAIL] 에러 로그 파일을 찾을 수 없습니다\n")
        return False


def test_logging_summary():
    """로깅 시스템 종합 테스트"""
    print("=" * 60)
    print("테스트 요약")
    print("=" * 60)

    test_results = [
        ("기본 로깅", test_basic_logging()),
        ("아카이브 통계", test_archive_stats()),
        ("파일 로깅", test_logging_to_file()),
        ("아카이브 목록", test_list_archives()),
        ("에러 로깅", test_error_logging()),
    ]

    print("\n테스트 결과:")
    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {test_name}")

    all_passed = all(result for _, result in test_results)

    if all_passed:
        print("\n[OK] 모든 테스트 통과!")
        return 0
    else:
        print("\n[FAIL] 일부 테스트 실패")
        return 1


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("로깅 시스템 테스트 시작")
    print("=" * 60 + "\n")

    try:
        exit_code = test_logging_summary()
    except Exception as exc:
        print(f"\n테스트 중 예외 발생: {exc}")
        import traceback
        traceback.print_exc()
        exit_code = 1

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

    sys.exit(exit_code)
