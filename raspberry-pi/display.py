"""
LCD 1602 I2C 디스플레이 제어 모듈
미세먼지 수치를 2줄에 걸친 큰 숫자로 LCD에 표시합니다.
"""

import logging

logger = logging.getLogger(__name__)

# ─── 커스텀 문자 (CGRAM 0-3) ───
CUSTOM_CHARS = [
    [0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00],  # 0: ▀ 상단 바
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F],  # 1: ▄ 하단 바
    [0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x1F, 0x1F, 0x1F],  # 2: ═ 상하 바
    [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F],  # 3: █ 풀블록
]

F = 3   # █ Full
T = 0   # ▀ Top
B = 1   # ▄ Bottom
M = 2   # ═ Mid
S = 32  # Space

# 각 숫자의 빅넘버 패턴: (윗줄 3칸, 아랫줄 3칸)
BIG = {
    '0': ([F,T,F], [F,B,F]),
    '1': ([T,F,S], [B,F,B]),
    '2': ([M,M,F], [F,B,B]),
    '3': ([T,M,F], [B,B,F]),
    '4': ([F,B,F], [S,S,F]),
    '5': ([F,M,M], [B,B,F]),
    '6': ([F,M,M], [F,M,F]),
    '7': ([T,T,F], [S,S,F]),
    '8': ([F,M,F], [F,M,F]),
    '9': ([F,M,F], [B,B,F]),
    '-': ([S,S,S], [B,B,B]),
}


class DustDisplay:
    def __init__(self, address=0x27, expander="PCF8574", cols=16, rows=2):
        self.lcd = None
        self.connected = False
        self.cols = cols
        self.rows = rows
        self._init_lcd(address, expander, cols, rows)

    def _init_lcd(self, address, expander, cols, rows):
        try:
            from RPLCD.i2c import CharLCD
            self.lcd = CharLCD(expander, address, cols=cols, rows=rows)
            self.lcd.clear()
            self.lcd.backlight_enabled = True
            self.connected = True
            logger.info(f"LCD 연결 성공! (주소: {hex(address)}, 백라이트: ON)")

            for i, cd in enumerate(CUSTOM_CHARS):
                self.lcd.create_char(i, cd)

            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string("DustCheck v1.0")
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string("Starting...")
        except ImportError:
            logger.warning("RPLCD 라이브러리가 없습니다.")
            self.connected = False
        except Exception as e:
            logger.warning(f"LCD 연결 실패: {e}")
            self.connected = False

    def _write_row(self, row, chars):
        try:
            self.lcd.cursor_pos = (row, 0)
            for ch in chars:
                self.lcd.write_string(chr(ch))
        except Exception as e:
            logger.error(f"LCD row{row} 오류: {e}")

    def show_dust_data(self, data, outdoor_pm25=None):
        """3개 수치를 2줄에 걸쳐 큰 숫자로 표시 (각 숫자 3칸×2줄)"""
        if not self.connected or not self.lcd:
            return
        try:
            pm1 = int(round(data.get("pm1", 0.0)))
            pm25 = int(round(data.get("pm25", 0.0)))
            out_val = int(round(outdoor_pm25)) if outdoor_pm25 is not None else None
            s1, s2, s3 = str(pm1), str(pm25), str(out_val) if out_val is not None else "--"

            w1, w2, w3 = len(s1)*3, len(s2)*3, len(s3)*3
            total = w1 + w2 + w3

            if total > self.cols:
                # 빅넘버 불가 → 일반 텍스트 양줄
                line = f"{pm1:>4}  {pm25:>4}  {s3:>4}"
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string(line[:self.cols])
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(line[:self.cols])
                return

            # 남은 공간을 두 간격으로 분배
            space = self.cols - total
            gap1 = (space + 1) // 2
            gap2 = space - gap1

            row0 = []
            row1 = []
            for idx, ns in enumerate([s1, s2, s3]):
                for ch in ns:
                    if ch in BIG:
                        t, b = BIG[ch]
                        row0.extend(t)
                        row1.extend(b)
                if idx == 0:
                    row0.extend([S]*gap1)
                    row1.extend([S]*gap1)
                elif idx == 1:
                    row0.extend([S]*gap2)
                    row1.extend([S]*gap2)

            # 16칸 맞추기
            row0 = (row0 + [S]*self.cols)[:self.cols]
            row1 = (row1 + [S]*self.cols)[:self.cols]

            self._write_row(0, row0)
            self._write_row(1, row1)
        except Exception as e:
            logger.error(f"LCD 표시 오류: {e}")

    def show_message(self, line1="", line2=""):
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
            logger.error(f"LCD 메시지 오류: {e}")

    def clear(self):
        if self.connected and self.lcd:
            try:
                self.lcd.clear()
            except Exception:
                pass
