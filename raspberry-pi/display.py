"""
LCD 1602 I2C 디스플레이 제어 모듈
미세먼지 수치와 공기질 등급을 LCD에 표시합니다.
"""

import logging
from config import get_air_quality

logger = logging.getLogger(__name__)


class DustDisplay:
    """LCD 1602 I2C 디스플레이 래퍼 클래스"""

    def __init__(self, address=0x27, expander="PCF8574", cols=16, rows=2):
        self.lcd = None
        self.connected = False
        self.cols = cols
        self.rows = rows
        self._init_lcd(address, expander, cols, rows)

    def _init_lcd(self, address, expander, cols, rows):
        """LCD를 초기화합니다."""
        try:
            from RPLCD.i2c import CharLCD
            self.lcd = CharLCD(expander, address, cols=cols, rows=rows)
            self.lcd.clear()
            self.lcd.backlight_enabled = True
            self.connected = True
            logger.info(f"LCD 연결 성공! (주소: {hex(address)}, 백라이트: ON)")

            # 시작 메시지 표시
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string("DustCheck v1.0")
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string("Starting...")

        except ImportError:
            logger.warning("RPLCD 라이브러리가 없습니다. LCD 없이 진행합니다.")
            self.connected = False
        except Exception as e:
            logger.warning(f"LCD 연결 실패: {e}")
            logger.warning("→ LCD 없이도 프로그램은 정상 작동합니다")
            logger.warning("→ LCD 주소를 확인하세요: i2cdetect -y 1")
            self.connected = False

    def show_dust_data(self, data):
        """
        미세먼지 데이터를 LCD에 표시합니다.
        16x2 LCD에 PM1.0, PM2.5, PM10 세 가지 값을 표시합니다.

        표시 형식:
            PM1  PM2.5  PM10
             9.6  10.2  10.2

        Args:
            data: {"pm1": float, "pm25": float, "pm4": float, "pm10": float}
        """
        if not self.connected or not self.lcd:
            return

        try:
            pm1 = data.get("pm1", 0.0)
            pm25 = data.get("pm25", 0.0)
            pm10 = data.get("pm10", 0.0)

            # 1번째 줄: 라벨 (16자)
            line1 = "PM1  PM2.5  PM10"

            # 2번째 줄: 수치 (각 4자 + 공백2 = 16자)
            line2 = f"{pm1:4.1f}  {pm25:4.1f}  {pm10:4.1f}"

            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(line1)
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(line2)

        except Exception as e:
            logger.error(f"LCD 표시 오류: {e}")

    def show_message(self, line1="", line2=""):
        """LCD에 임의의 메시지를 표시합니다."""
        if not self.connected or not self.lcd:
            return

        try:
            self.lcd.clear()
            if line1:
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string(line1[:self.cols])
            if line2:
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(line2[:self.cols])
        except Exception as e:
            logger.error(f"LCD 메시지 표시 오류: {e}")

    def clear(self):
        """LCD 화면을 지웁니다."""
        if self.connected and self.lcd:
            try:
                self.lcd.clear()
            except Exception:
                pass
