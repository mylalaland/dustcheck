"""
SPS30 미세먼지 센서 제어 모듈
센서리온 SPS30에서 PM1.0, PM2.5, PM4.0, PM10 값을 읽습니다.
"""

import time
import logging

logger = logging.getLogger(__name__)


class DustSensor:
    """SPS30 미세먼지 센서 래퍼 클래스"""

    def __init__(self, i2c_bus=1):
        self.i2c_bus = i2c_bus
        self.sps = None
        self.connected = False
        self._init_sensor()

    def _init_sensor(self):
        """센서를 초기화합니다."""
        try:
            from sps30 import SPS30
            self.sps = SPS30(self.i2c_bus)

            # 센서 확인
            article_code = self.sps.read_article_code()
            if article_code == self.sps.ARTICLE_CODE_ERROR:
                logger.error("SPS30 센서를 찾을 수 없습니다!")
                logger.error("→ SEL 핀이 GND에 연결되었는지 확인하세요")
                logger.error("→ i2cdetect -y 1 명령으로 0x69가 보이는지 확인하세요")
                self.connected = False
                return

            serial = self.sps.read_device_serial()
            logger.info(f"SPS30 센서 연결 성공! (시리얼: {serial})")

            # 측정 시작
            self.sps.start_measurement()
            self.connected = True

            # 센서가 안정화될 때까지 잠시 대기
            time.sleep(2)
            logger.info("센서 측정을 시작합니다")

        except ImportError:
            logger.error("sps30 라이브러리가 설치되지 않았습니다!")
            logger.error("→ pip install sps30 명령으로 설치하세요")
            self.connected = False
        except Exception as e:
            logger.error(f"센서 초기화 실패: {e}")
            self.connected = False

    def read(self):
        """
        센서에서 미세먼지 값을 읽어옵니다.

        Returns:
            dict: PM 값들을 담은 딕셔너리
                  {"pm1": float, "pm25": float, "pm4": float, "pm10": float, "ok": bool}
        """
        result = {
            "pm1": 0.0,
            "pm25": 0.0,
            "pm4": 0.0,
            "pm10": 0.0,
            "ok": False,
        }

        if not self.connected or self.sps is None:
            logger.warning("센서가 연결되지 않았습니다. 더미 데이터를 반환합니다.")
            return result

        try:
            # 데이터 준비 확인
            if not self.sps.read_data_ready_flag():
                logger.debug("센서 데이터가 아직 준비되지 않음")
                return result

            self.sps.read_measured_values()

            result["pm1"] = round(self.sps.dict_values.get("pm1p0", 0.0), 2)
            result["pm25"] = round(self.sps.dict_values.get("pm2p5", 0.0), 2)
            result["pm4"] = round(self.sps.dict_values.get("pm4p0", 0.0), 2)
            result["pm10"] = round(self.sps.dict_values.get("pm10p0", 0.0), 2)
            result["ok"] = True

        except Exception as e:
            logger.error(f"센서 읽기 오류: {e}")
            # 재연결 시도
            self._reconnect()

        return result

    def _reconnect(self):
        """센서 재연결을 시도합니다."""
        logger.info("센서 재연결 시도 중...")
        try:
            if self.sps:
                try:
                    self.sps.stop_measurement()
                except Exception:
                    pass
            time.sleep(2)
            self._init_sensor()
        except Exception as e:
            logger.error(f"재연결 실패: {e}")

    def clean(self):
        """센서 팬 청소 기능을 실행합니다 (주기적으로 권장)."""
        if self.connected and self.sps:
            try:
                self.sps.start_fan_cleaning()
                logger.info("센서 팬 청소 시작 (약 10초)")
            except Exception as e:
                logger.error(f"팬 청소 실패: {e}")

    def stop(self):
        """센서 측정을 종료합니다."""
        if self.connected and self.sps:
            try:
                self.sps.stop_measurement()
                logger.info("센서 측정 종료")
            except Exception as e:
                logger.error(f"센서 종료 오류: {e}")
        self.connected = False
