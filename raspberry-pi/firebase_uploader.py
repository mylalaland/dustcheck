"""
Firebase Realtime Database 업로더 모듈
미세먼지 데이터를 Firebase에 전송하고 오래된 데이터를 정리합니다.
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseUploader:
    """Firebase Realtime Database 업로더"""

    def __init__(self, credentials_path, database_url):
        self.connected = False
        self.db_ref = None
        self.latest_ref = None
        self._init_firebase(credentials_path, database_url)

    def _init_firebase(self, credentials_path, database_url):
        """Firebase를 초기화합니다."""
        try:
            import firebase_admin
            from firebase_admin import credentials, db

            # 이미 초기화된 앱이 있는지 확인
            try:
                firebase_admin.get_app()
                logger.info("Firebase 앱이 이미 초기화되어 있습니다")
            except ValueError:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    "databaseURL": database_url
                })
                logger.info("Firebase 초기화 성공!")

            self.db_ref = db.reference("dust_data")
            self.latest_ref = db.reference("latest")
            self.connected = True

        except ImportError:
            logger.error("firebase-admin 라이브러리가 없습니다!")
            logger.error("→ pip install firebase-admin 으로 설치하세요")
            self.connected = False
        except FileNotFoundError:
            logger.error(f"서비스 계정 키 파일을 찾을 수 없습니다: {credentials_path}")
            logger.error("→ FIREBASE_GUIDE.md를 참고하여 키를 다운로드하세요")
            self.connected = False
        except Exception as e:
            logger.error(f"Firebase 초기화 실패: {e}")
            self.connected = False

    def upload(self, data):
        """
        미세먼지 데이터를 Firebase에 업로드합니다.

        Args:
            data: {"pm1": float, "pm25": float, "pm4": float, "pm10": float}

        Returns:
            bool: 업로드 성공 여부
        """
        if not self.connected:
            logger.warning("Firebase에 연결되지 않아 업로드를 건너뜁니다")
            return False

        now = datetime.now()
        record = {
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(now.timestamp() * 1000),  # 밀리초 타임스탬프
            "pm1": data.get("pm1", 0.0),
            "pm25": data.get("pm25", 0.0),
            "pm4": data.get("pm4", 0.0),
            "pm10": data.get("pm10", 0.0),
        }

        # 재시도 로직 (최대 3회)
        for attempt in range(3):
            try:
                # 히스토리 데이터 추가
                self.db_ref.push(record)

                # 최신값 업데이트 (덮어쓰기)
                self.latest_ref.set(record)

                logger.info(f"Firebase 전송 성공: PM2.5={record['pm25']}")
                return True

            except Exception as e:
                logger.warning(f"Firebase 전송 실패 (시도 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)  # 1, 2, 4초 대기

        logger.error("Firebase 전송 3회 모두 실패!")
        return False

    def cleanup_old_data(self, days=30):
        """오래된 데이터를 정리합니다."""
        if not self.connected:
            return

        try:
            from firebase_admin import db
            cutoff = int((datetime.now().timestamp() - days * 86400) * 1000)

            # 오래된 데이터 조회
            old_data = self.db_ref.order_by_child("timestamp").end_at(cutoff).get()

            if old_data:
                count = len(old_data)
                for key in old_data:
                    self.db_ref.child(key).delete()
                logger.info(f"{days}일 이전 데이터 {count}건 삭제 완료")
            else:
                logger.info("삭제할 오래된 데이터가 없습니다")

        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")
