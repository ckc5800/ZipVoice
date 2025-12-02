#!/usr/bin/env python3
"""
로그 아카이브 관리 스크립트

로그 파일을 압축, 정리, 아카이브하는 CLI 도구입니다.
- 오래된 로그 파일을 자동으로 압축
- 날짜별 종합 아카이브 생성
- 아카이브 통계 조회
- 오래된 아카이브 자동 정리
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

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


def cmd_archive(args) -> int:
    """오래된 로그 파일 아카이브"""
    logger = get_logger(__name__)

    try:
        logger.info(f"로그 압축 시작: {args.older_than_days}일 이상 된 파일")

        compressed = archive_logs(older_than_days=args.older_than_days, archive_type=args.type)

        if not compressed:
            logger.info("압축할 파일이 없습니다.")
            return 0

        logger.info(f"압축 완료: {len(compressed)}개 파일")
        for filename, size_bytes in compressed.items():
            try:
                size_mb = size_bytes / (1024 * 1024)
                print(f"  - {filename}: {size_mb:.2f} MB")
            except Exception as e:
                logger.warning(f"파일 크기 계산 실패 ({filename}): {e}")
                print(f"  - {filename}: 계산 오류")

        return 0
    except Exception as e:
        logger.error(f"아카이브 명령 실행 중 오류: {e}", exc_info=True)
        return 1


def cmd_daily_archive(args) -> int:
    """날짜별 종합 아카이브 생성"""
    logger = get_logger(__name__)

    try:
        logger.info(f"날짜별 아카이브 생성: {args.date or '어제'}")

        result = create_daily_archive(date_str=args.date)

        if result:
            logger.info(f"아카이브 생성 완료: {result}")
            print(f"생성된 아카이브: {result}")
            return 0
        else:
            logger.error("아카이브 생성 실패")
            return 1
    except Exception as e:
        logger.error(f"날짜별 아카이브 명령 실행 중 오류: {e}", exc_info=True)
        return 1


def cmd_cleanup(args) -> int:
    """오래된 아카이브 정리"""
    logger = get_logger(__name__)

    try:
        logger.info(f"오래된 아카이브 정리 시작: {args.keep_days}일 이상 된 파일 삭제")

        deleted_count = cleanup_old_archives(keep_days=args.keep_days)

        logger.info(f"정리 완료: {deleted_count}개 파일 삭제")
        print(f"삭제된 아카이브: {deleted_count}개")

        return 0
    except Exception as e:
        logger.error(f"정리 명령 실행 중 오류: {e}", exc_info=True)
        return 1


def cmd_stats(args) -> int:
    """아카이브 통계 조회"""
    logger = get_logger(__name__)

    try:
        logger.info("아카이브 통계 조회")

        stats = get_archive_stats()

        if not stats:
            logger.warning("통계 정보가 없습니다.")
            return 1

        # 보기 좋게 출력
        print("\n=== 로그 및 아카이브 통계 ===\n")

        print("로그 파일:")
        print(f"  - 파일 수: {stats.get('log_count', 0)}")
        print(f"  - 총 크기: {stats.get('log_size_mb', 0):.2f} MB")
        if stats.get('oldest_log'):
            print(f"  - 가장 오래된 파일: {stats['oldest_log']}")
        if stats.get('newest_log'):
            print(f"  - 가장 최신 파일: {stats['newest_log']}")

        print("\n아카이브 파일:")
        print(f"  - 파일 수: {stats.get('archive_count', 0)}")
        print(f"  - 총 크기: {stats.get('archive_size_mb', 0):.2f} MB")

        return 0
    except Exception as e:
        logger.error(f"통계 조회 명령 실행 중 오류: {e}", exc_info=True)
        return 1


def cmd_list(args) -> int:
    """아카이브 목록 조회"""
    logger = get_logger(__name__)

    try:
        logger.info("아카이브 목록 조회")

        archives = list_archives()

        if not archives:
            print("아카이브 파일이 없습니다.")
            return 0

        print(f"\n=== 아카이브 목록 ({len(archives)}개) ===\n")

        for archive in archives:
            try:
                print(f"파일명: {archive['name']}")
                print(f"  - 크기: {archive['size_mb']:.2f} MB")
                print(f"  - 생성일: {archive['created']}")
                print(f"  - 경로: {archive['path']}")
                print()
            except Exception as e:
                logger.warning(f"아카이브 정보 출력 실패: {e}")

        return 0
    except Exception as e:
        logger.error(f"목록 조회 명령 실행 중 오류: {e}", exc_info=True)
        return 1


def cmd_full_maintenance(args) -> int:
    """전체 유지보수 (아카이브 + 정리)"""
    logger = get_logger(__name__)

    try:
        logger.info("전체 로그 유지보수 시작")

        print("=== 로그 유지보수 시작 ===\n")

        # 1단계: 오래된 로그 압축
        print("1단계: 오래된 로그 압축...")
        try:
            compressed = archive_logs(older_than_days=args.older_than_days)
            print(f"  완료: {len(compressed)}개 파일 압축\n")
        except Exception as e:
            logger.error(f"로그 압축 실패: {e}")
            print(f"  실패: {e}\n")

        # 2단계: 날짜별 아카이브 생성
        print("2단계: 날짜별 아카이브 생성...")
        try:
            result = create_daily_archive()
            if result:
                print(f"  완료: {result}\n")
            else:
                print("  실패\n")
        except Exception as e:
            logger.error(f"아카이브 생성 실패: {e}")
            print(f"  실패: {e}\n")

        # 3단계: 오래된 아카이브 정리
        print("3단계: 오래된 아카이브 정리...")
        try:
            deleted_count = cleanup_old_archives(keep_days=args.keep_days)
            print(f"  완료: {deleted_count}개 파일 삭제\n")
        except Exception as e:
            logger.error(f"아카이브 정리 실패: {e}")
            print(f"  실패: {e}\n")

        # 4단계: 통계 출력
        print("4단계: 최종 통계")
        try:
            stats = get_archive_stats()
            print(f"  로그 파일: {stats.get('log_count', 0)}개, {stats.get('log_size_mb', 0):.2f} MB")
            print(f"  아카이브: {stats.get('archive_count', 0)}개, {stats.get('archive_size_mb', 0):.2f} MB")
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            print(f"  실패: {e}\n")

        logger.info("전체 로그 유지보수 완료")
        print("\n=== 유지보수 완료 ===")

        return 0
    except Exception as e:
        logger.error(f"전체 유지보수 명령 실행 중 오류: {e}", exc_info=True)
        return 1


def main():
    """메인 함수"""
    # 로깅 설정
    setup_logging(log_dir="logs", log_level="INFO", enable_archiver=True)
    logger = get_logger(__name__)

    # 인자 파싱
    parser = argparse.ArgumentParser(
        description="로그 아카이브 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 7일 이상 된 로그 압축
  python manage_logs.py archive --older-than-days 7

  # 어제 로그의 종합 아카이브 생성
  python manage_logs.py daily-archive

  # 30일 이상 된 아카이브 삭제
  python manage_logs.py cleanup --keep-days 30

  # 로그 및 아카이브 통계 조회
  python manage_logs.py stats

  # 아카이브 목록 조회
  python manage_logs.py list

  # 전체 유지보수 (압축 + 정리)
  python manage_logs.py full-maintenance
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어")

    # archive 명령어
    archive_parser = subparsers.add_parser("archive", help="오래된 로그 파일 압축")
    archive_parser.add_argument(
        "--older-than-days",
        type=int,
        default=7,
        help="이 날짜보다 오래된 파일 압축 (기본값: 7일)"
    )
    archive_parser.add_argument(
        "--type",
        choices=["zip", "gz"],
        default="zip",
        help="압축 형식 (기본값: zip)"
    )
    archive_parser.set_defaults(func=cmd_archive)

    # daily-archive 명령어
    daily_parser = subparsers.add_parser("daily-archive", help="날짜별 아카이브 생성")
    daily_parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="아카이브 날짜 (형식: YYYY-MM-DD, 기본값: 어제)"
    )
    daily_parser.set_defaults(func=cmd_daily_archive)

    # cleanup 명령어
    cleanup_parser = subparsers.add_parser("cleanup", help="오래된 아카이브 정리")
    cleanup_parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="유지할 기간 (기본값: 30일)"
    )
    cleanup_parser.set_defaults(func=cmd_cleanup)

    # stats 명령어
    stats_parser = subparsers.add_parser("stats", help="아카이브 통계 조회")
    stats_parser.set_defaults(func=cmd_stats)

    # list 명령어
    list_parser = subparsers.add_parser("list", help="아카이브 목록 조회")
    list_parser.set_defaults(func=cmd_list)

    # full-maintenance 명령어
    full_parser = subparsers.add_parser("full-maintenance", help="전체 유지보수")
    full_parser.add_argument(
        "--older-than-days",
        type=int,
        default=7,
        help="로그 압축 기준 (기본값: 7일)"
    )
    full_parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="아카이브 유지 기간 (기본값: 30일)"
    )
    full_parser.set_defaults(func=cmd_full_maintenance)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
