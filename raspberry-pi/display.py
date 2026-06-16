"""
LCD 1602 I2C 디스플레이 제어 모듈
미세먼지 수치를 커스텀 큰 숫자 폰트로 LCD에 표시합니다.
"""

import logging

logger = logging.getLogger(__name__)

# ─── 빅넘버 커스텀 문자 (CGRAM 0-7) ───
# 3칸 너비 × 2줄 높이의 빌딩 블록
CUSTOM_CHARS = [
    [0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00],  # 0: ▀ 상단 바
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F],  # 1: ▄ 하단 바
    [0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x1F, 0x1F, 0x1F],  # 2: ═ 상하단 바
    [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F],  # 3: █ 풀블록
]

# 빅넘버 패턴: (윗줄, 아랫줄) - 각 3칸
# 3=풀블록, 0=상단바, 1=하단바, 2=상하단바, 32=공백
F = 3   # Full block (custom char 3)
T = 0   # Top bar
B = 1   # Bottom bar
M = 2   # Mid bar (top+bottom)
S = 32  # Space (ASCII 0x20)

BIG_DIGITS = {
    '0': ([F, T, F], [F, B, F]),
    '1': ([T, F, S], [B, F, B]),
    '2': ([M, M, F], [F, B, B]),
    '3': ([T, M, F], [B, B, F]),
    '4': ([F, B, F], [S, S, F]),
    '5': ([F, M, M], [B, B, F]),
    '6': ([F, M, M], [F, M, F]),
    '7': ([T, T, F], [S, S, F]),
    '8': ([F, M, F], [F, M, F]),
    '9': ([F, M, F], [B, B, F]),
    '-': ([S, S, S], [B, B, B]),
}


def _digit_width(d):
    """숫자 한 글자의 빅넘버 폭"""
    return 3  # 모든 숫자 3칸 고정


class DustDisplay:
    """LCD 1602 I2C 디스플레이 래퍼 클래스"""

    def __init__(self, address=0x27, expander="PCF8574", cols=16, rows=2):
        self.lcd = None
        self.connected = False
        self.cols = cols
        self.rows = rows
        self._last_line0 = ""
        self._last_line1 = ""
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

            # 커스텀 문자 등록
            for i, char_data in enumerate(CUSTOM_CHARS):
                self.lcd.create_char(i, char_data)

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

    def _write_row(self, row, content):
        """한 줄을 효율적으로 씁니다 (변경된 부분만)."""
        try:
            self.lcd.cursor_pos = (row, 0)
            for ch in content:
                if ch < 8:
                    # 커스텀 문자 0-7
                    self.lcd.write_string(chr(ch))
                else:
                    self.lcd.write_string(chr(ch))
        except Exception as e:
            logger.error(f"LCD 쓰기 오류 (row {row}): {e}")

    def show_dust_data(self, data, outdoor_pm25=None):
        """
        미세먼지 데이터를 빅넘버로 LCD에 표시합니다.
        3개 수치를 2줄에 걸쳐 하나의 큰 줄처럼 보여줍니다.
        """
        if not self.connected or not self.lcd:
            return

        try:
            pm1 = int(round(data.get("pm1", 0.0)))
            pm25 = int(round(data.get("pm25", 0.0)))
            out_val = int(round(outdoor_pm25)) if outdoor_pm25 is not None else None

            s1 = str(pm1)
            s2 = str(pm25)
            s3 = str(out_val) if out_val is not None else "--"

            # 각 숫자의 폭 계산
            w1 = len(s1) * 3
            w2 = len(s2) * 3
            w3 = len(s3) * 3

            # 구분자 포함 총 폭
            total_with_sep = w1 + 1 + w2 + 1 + w3
            total_no_sep = w1 + w2 + w3

            if total_with_sep <= self.cols:
                # 구분자 포함 가능
                total = total_with_sep
                use_sep = True
            elif total_no_sep <= self.cols:
                # 구분자 없이 가능
                total = total_no_sep
                use_sep = False
            else:
                # 빅넘버 불가 → 일반 텍스트 (깜빡임 방지를 위해 clear 없이)
                line = f"{pm1:>4}  {pm25:>4}  {s3:>4}"
                row0 = [ord(c) for c in line[:self.cols].ljust(self.cols)]
                self._write_row(0, row0)
                self._write_row(1, row0)
                return

            # 빅넘버 렌더링
            pad = (self.cols - total) // 2
            row0 = [S] * self.cols
            row1 = [S] * self.cols

            col = pad
            for num_str in [s1, s2, s3]:
                for ch in num_str:
                    if ch in BIG_DIGITS:
                        top, bot = BIG_DIGITS[ch]
                        for j in range(3):
                            if col + j < self.cols:
                                row0[col + j] = top[j]
                                row1[col + j] = bot[j]
                        col += 3
                # 구분자
                if use_sep and num_str != s3:
                    col += 1  # 1칸 공백

            self._write_row(0, row0)
            self._write_row(1, row1)

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
