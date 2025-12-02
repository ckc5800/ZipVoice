"""
로그 아카이브 관리 모듈

로그 파일을 자동으로 압축, 정렬, 아카이브하는 기능을 제공합니다.
"""
import logging
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import gzip
import os


class LogArchiver:
    """로그 파일 아카이브 관리자"""

    def __init__(self, log_dir: str = "logs", archive_dir: Optional[str] = None):
        """
        로그 아카이버 초기화

        Args:
            log_dir: 로그 파일 디렉토리
            archive_dir: 아카이브 저장 디렉토리 (기본값: logs/archive)
        """
        self.log_path = Path(log_dir)
        self.archive_path = Path(archive_dir or f"{log_dir}/archive")
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def compress_logs(self, older_than_days: int = 7, archive_type: str = "zip") -> Dict[str, int]:
        """
        지정된 날짜보다 오래된 로그 파일을 압축

        Args:
            older_than_days: 이 날짜보다 오래된 파일을 압축 (기본값: 7일)
            archive_type: 압축 형식 ('zip' 또는 'gz', 기본값: 'zip')

        Returns:
            압축 결과 딕셔너리 {file_name: size_bytes}
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        compressed_files = {}

        if not self.log_path.exists():
            self.logger.warning(f"로그 디렉토리가 없습니다: {self.log_path}")
            return compressed_files

        # 압축 대상 파일 찾기
        try:
            for log_file in self.log_path.glob("*.log"):
                try:
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        if archive_type == "gz":
                            compressed_path = self._compress_gzip(log_file)
                        else:
                            compressed_path = self._compress_zip(log_file)

                        if compressed_path:
                            compressed_files[compressed_path.name] = compressed_path.stat().st_size
                            # 원본 파일 삭제
                            try:
                                log_file.unlink()
                                self.logger.info(f"압축 및 삭제 완료: {log_file.name}")
                            except Exception as e:
                                self.logger.error(f"파일 삭제 실패 ({log_file.name}): {e}")
                except OSError as e:
                    self.logger.error(f"파일 상태 확인 실패 ({log_file}): {e}")
        except Exception as e:
            self.logger.error(f"로그 압축 중 오류: {e}")

        return compressed_files

    def _compress_gzip(self, log_file: Path) -> Optional[Path]:
        """Gzip 압축"""
        try:
            archive_file = self.archive_path / f"{log_file.name}.gz"
            with open(log_file, 'rb') as f_in:
                with gzip.open(archive_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.logger.info(f"Gzip 압축 완료: {log_file.name} -> {archive_file.name}")
            return archive_file
        except IOError as e:
            self.logger.error(f"Gzip 압축 실패 (I/O 오류, {log_file}): {e}")
            return None
        except Exception as e:
            self.logger.error(f"Gzip 압축 실패 ({log_file}): {e}")
            return None

    def _compress_zip(self, log_file: Path) -> Optional[Path]:
        """Zip 압축"""
        try:
            archive_file = self.archive_path / f"{log_file.name}.zip"
            with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(log_file, arcname=log_file.name)
            self.logger.info(f"ZIP 압축 완료: {log_file.name} -> {archive_file.name}")
            return archive_file
        except zipfile.BadZipFile as e:
            self.logger.error(f"ZIP 압축 실패 (잘못된 ZIP 형식, {log_file}): {e}")
            return None
        except IOError as e:
            self.logger.error(f"ZIP 압축 실패 (I/O 오류, {log_file}): {e}")
            return None
        except Exception as e:
            self.logger.error(f"ZIP 압축 실패 ({log_file}): {e}")
            return None

    def create_daily_archive(self, date_str: Optional[str] = None) -> Optional[Path]:
        """
        날짜별 종합 아카이브 생성

        Args:
            date_str: 아카이브 날짜 (기본값: 어제, 형식: 'YYYY-MM-DD')

        Returns:
            생성된 아카이브 파일 경로
        """
        if date_str is None:
            target_date = datetime.now() - timedelta(days=1)
            date_str = target_date.strftime("%Y-%m-%d")

        archive_name = f"logs_archive_{date_str}.zip"
        archive_path = self.archive_path / archive_name

        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                files_added = 0

                # 로그 파일 추가
                if self.log_path.exists():
                    try:
                        for log_file in self.log_path.glob("*.log"):
                            try:
                                zf.write(log_file, arcname=log_file.name)
                                files_added += 1
                            except Exception as e:
                                self.logger.warning(f"로그 파일 추가 실패 ({log_file.name}): {e}")
                    except Exception as e:
                        self.logger.warning(f"로그 파일 스캔 실패: {e}")

                # 이미 압축된 파일 추가
                try:
                    for archive_file in self.archive_path.glob("*.gz"):
                        if archive_file.name != archive_name:
                            try:
                                zf.write(archive_file, arcname=archive_file.name)
                                files_added += 1
                            except Exception as e:
                                self.logger.warning(f"압축 파일 추가 실패 ({archive_file.name}): {e}")
                except Exception as e:
                    self.logger.warning(f"압축 파일 스캔 실패: {e}")

            if files_added == 0:
                self.logger.warning(f"아카이브에 추가된 파일이 없습니다: {archive_name}")
            else:
                self.logger.info(f"일일 아카이브 생성 완료: {archive_path} ({files_added}개 파일)")

            return archive_path
        except zipfile.BadZipFile as e:
            self.logger.error(f"아카이브 생성 실패 (잘못된 ZIP): {e}")
            return None
        except IOError as e:
            self.logger.error(f"아카이브 생성 실패 (I/O 오류): {e}")
            return None
        except Exception as e:
            self.logger.error(f"아카이브 생성 실패: {e}")
            return None

    def cleanup_old_archives(self, keep_days: int = 30) -> int:
        """
        오래된 아카이브 파일 정리

        Args:
            keep_days: 유지할 기간 (기본값: 30일)

        Returns:
            삭제된 파일 개수
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        if not self.archive_path.exists():
            return 0

        for archive_file in self.archive_path.glob("*"):
            if archive_file.is_file() and archive_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    archive_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"오래된 아카이브 삭제: {archive_file.name}")
                except Exception as e:
                    self.logger.error(f"아카이브 삭제 실패 ({archive_file}): {e}")

        return deleted_count

    def get_archive_stats(self) -> Dict[str, object]:
        """
        아카이브 통계 조회

        Returns:
            {
                'log_count': 로그 파일 수,
                'log_size_mb': 로그 파일 총 크기 (MB),
                'archive_count': 아카이브 파일 수,
                'archive_size_mb': 아카이브 총 크기 (MB),
                'oldest_log': 가장 오래된 로그 파일 생성 날짜,
                'newest_log': 가장 최신 로그 파일 생성 날짜
            }
        """
        stats = {
            'log_count': 0,
            'log_size_mb': 0,
            'archive_count': 0,
            'archive_size_mb': 0,
            'oldest_log': None,
            'newest_log': None
        }

        try:
            if self.log_path.exists():
                try:
                    log_files = list(self.log_path.glob("*.log"))
                    stats['log_count'] = len(log_files)

                    total_size = 0
                    mtimes = []

                    for log_file in log_files:
                        try:
                            size = log_file.stat().st_size
                            total_size += size
                            mtimes.append(log_file.stat().st_mtime)
                        except OSError as e:
                            self.logger.warning(f"로그 파일 stat 실패 ({log_file.name}): {e}")

                    stats['log_size_mb'] = total_size / (1024 * 1024)

                    if mtimes:
                        stats['oldest_log'] = datetime.fromtimestamp(min(mtimes)).isoformat()
                        stats['newest_log'] = datetime.fromtimestamp(max(mtimes)).isoformat()

                except Exception as e:
                    self.logger.warning(f"로그 파일 통계 조회 실패: {e}")

            if self.archive_path.exists():
                try:
                    archive_files = list(self.archive_path.glob("*"))
                    stats['archive_count'] = len(archive_files)

                    total_size = 0
                    for archive_file in archive_files:
                        try:
                            if archive_file.is_file():
                                total_size += archive_file.stat().st_size
                        except OSError as e:
                            self.logger.warning(f"아카이브 파일 stat 실패 ({archive_file.name}): {e}")

                    stats['archive_size_mb'] = total_size / (1024 * 1024)

                except Exception as e:
                    self.logger.warning(f"아카이브 파일 통계 조회 실패: {e}")

        except Exception as e:
            self.logger.error(f"통계 조회 중 오류: {e}")

        return stats

    def list_archives(self) -> List[Dict[str, object]]:
        """
        아카이브 파일 목록 조회

        Returns:
            아카이브 파일 정보 리스트
        """
        archives = []

        if not self.archive_path.exists():
            return archives

        try:
            archive_files = []
            for archive_file in self.archive_path.glob("*"):
                if archive_file.is_file():
                    try:
                        mtime = archive_file.stat().st_mtime
                        archive_files.append((archive_file, mtime))
                    except OSError as e:
                        self.logger.warning(f"아카이브 파일 stat 실패 ({archive_file.name}): {e}")

            # mtime 기준 정렬 (최신 파일 먼저)
            archive_files.sort(key=lambda x: x[1], reverse=True)

            for archive_file, mtime in archive_files:
                try:
                    size = archive_file.stat().st_size
                    archives.append({
                        'name': archive_file.name,
                        'size_mb': size / (1024 * 1024),
                        'created': datetime.fromtimestamp(mtime).isoformat(),
                        'path': str(archive_file)
                    })
                except OSError as e:
                    self.logger.warning(f"아카이브 파일 정보 조회 실패 ({archive_file.name}): {e}")

        except Exception as e:
            self.logger.error(f"아카이브 목록 조회 중 오류: {e}")

        return archives


def setup_archiver(log_dir: str = "logs", archive_dir: Optional[str] = None) -> LogArchiver:
    """
    로그 아카이버 설정

    Args:
        log_dir: 로그 디렉토리
        archive_dir: 아카이브 디렉토리

    Returns:
        LogArchiver 인스턴스
    """
    return LogArchiver(log_dir=log_dir, archive_dir=archive_dir)
