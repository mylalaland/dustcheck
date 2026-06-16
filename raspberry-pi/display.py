"""
LCD 1602 I2C 디스플레이 제어 모듈
미세먼지 수치를 최대 시인성으로 LCD에 표시합니다.
양줄에 동일한 내용을 표시하여 전광판처럼 보입니다.
"""

import logging

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

            # 시작 메시지
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string("DustCheck v1.0")
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string("Starting...")

        except ImportError:
            logger.warning("RPLCD 라이브러리가 없습니다. LCD 없이 진행합니다.")
            self.connected = False
        except Exception as e:
            logger.warning(f"LCD 연결 실패: {e}")
            self.connected = False

    def show_dust_data(self, data, outdoor_pm25=None):
        """
        미세먼지 3개 수치를 전광판 스타일로 표시합니다.
        PM1.0  PM2.5  지역PM2.5
        구분선 없이 넓은 간격으로 배치, 양줄 동일 표시.

        16칸 레이아웃 (각 4칸 + 간격 2칸):
          "   3    4   14"
          "   3    4   14"
        """
        if not self.connected or not self.lcd:
            return

        try:
            pm1 = int(round(data.get("pm1", 0.0)))
            pm25 = int(round(data.get("pm25", 0.0)))
            out_val = int(round(outdoor_pm25)) if outdoor_pm25 is not None else None
            out_str = str(out_val) if out_val is not None else "--"

            # 16칸: 4자리 + 2칸공백 + 4자리 + 2칸공백 + 4자리 = 16
            line = f"{pm1:>4}  {pm25:>4}  {out_str:>4}"

            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(line[:self.cols])
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(" " * self.cols)

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
