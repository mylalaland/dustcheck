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
        PM1.0과 PM2.5 수치만 크게 표시하여 시인성을 극대화합니다.

        표시 형식 (16x2 LCD):
            1.0>  9.6  [G]
            2.5> 10.2  [N]

        Args:
            data: {"pm1": float, "pm25": float, "pm4": float, "pm10": float}
        """
        if not self.connected or not self.lcd:
            return

        try:
            pm1 = data.get("pm1", 0.0)
            pm25 = data.get("pm25", 0.0)

            # 공기질 등급 약어 (LCD는 한글 미지원이므로 영문 약어 사용)
            q1 = get_air_quality("pm1", pm1)
            q25 = get_air_quality("pm25", pm25)
            g1 = q1["label_en"][0] if q1 else "?"   # G/N/B/V
            g25 = q25["label_en"][0] if q25 else "?"

            # 1줄: PM1.0 수치 (마커 + 수치 + 등급)
            # 2줄: PM2.5 수치
            line1 = f"1.0>{pm1:6.1f}   [{g1}]"
            line2 = f"2.5>{pm25:6.1f}   [{g25}]"

            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(line1[:self.cols])
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(line2[:self.cols])

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
