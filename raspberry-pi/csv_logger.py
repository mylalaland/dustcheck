"""
CSV 데이터 로거 모듈
미세먼지 데이터를 로컬 CSV 파일에 백업합니다.
날짜별로 파일을 분리하여 관리합니다.
"""

import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVLogger:
    """CSV 파일 데이터 로거"""

    def __init__(self, save_dir="data"):
        self.save_dir = save_dir
        self._ensure_dir()

    def _ensure_dir(self):
        """저장 디렉토리를 생성합니다."""
        try:
            os.makedirs(self.save_dir, exist_ok=True)
            logger.info(f"CSV 저장 폴더: {os.path.abspath(self.save_dir)}")
        except Exception as e:
            logger.error(f"CSV 폴더 생성 실패: {e}")

    def _get_filepath(self):
        """오늘 날짜에 해당하는 CSV 파일 경로를 반환합니다."""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.save_dir, f"dust_{today}.csv")

    def save(self, data):
        """
        미세먼지 데이터를 CSV 파일에 기록합니다.

        Args:
            data: {"pm1": float, "pm25": float, "pm4": float, "pm10": float}

        Returns:
            bool: 저장 성공 여부
        """
        filepath = self._get_filepath()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # 파일이 없으면 헤더 추가
            file_exists = os.path.exists(filepath)

            with open(filepath, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                if not file_exists:
                    writer.writerow(["Time", "PM1.0", "PM2.5", "PM4.0", "PM10"])
                    logger.info(f"새 CSV 파일 생성: {filepath}")

                writer.writerow([
                    now,
                    data.get("pm1", 0.0),
                    data.get("pm25", 0.0),
                    data.get("pm4", 0.0),
                    data.get("pm10", 0.0),
                ])

            logger.debug(f"CSV 저장: {filepath}")
            return True

        except Exception as e:
            logger.error(f"CSV 저장 실패: {e}")
            return False

    def get_today_count(self):
        """오늘 기록된 데이터 수를 반환합니다."""
        filepath = self._get_filepath()
        if not os.path.exists(filepath):
            return 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return sum(1 for _ in f) - 1  # 헤더 제외
        except Exception:
            return 0
