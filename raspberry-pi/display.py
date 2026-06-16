"""
LCD 1602 I2C 디스플레이 제어 모듈
미세먼지 수치를 커스텀 큰 숫자 폰트로 LCD에 표시합니다.
3칸 × 2줄 빅넘버 + 적응형 레이아웃
"""

import logging
from config import get_air_quality

logger = logging.getLogger(__name__)

# ─── 빅넘버 커스텀 문자 정의 (CGRAM) ───
# 3칸 너비 × 2줄 높이로 0-9 숫자를 표시하기 위한 빌딩 블록
CUSTOM_CHARS = [
    [0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00],  # 0: ▀ 상단 바
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F],  # 1: ▄ 하단 바
    [0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x1F, 0x1F, 0x1F],  # 2: ═ 상하단 바 (중간 빈)
    [0x00, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00],  # 3: · 구분 점 (소수점/구분자)
]

# 0xFF = █ 풀블록 (내장), 0x20 = ' ' 공백 (내장)
F = 0xFF  # Full block
T = 0     # Top bar (char 0)
B = 1     # Bottom bar (char 1)
M = 2     # Mid bar (char 2)
S = 0x20  # Space

# 각 숫자의 빅넘버 패턴: (윗줄 3칸, 아랫줄 3칸)
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
    '-': ([S, S, S], [S, M, S]),
    ' ': ([S, S, S], [S, S, S]),
}

# "1"은 2칸으로 축소 가능 (공간 절약)
BIG_DIGIT_1_NARROW = ([F, S], [F, B])


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

            # 커스텀 문자 등록 (빅넘버용)
            for i, char_data in enumerate(CUSTOM_CHARS):
                self.lcd.create_char(i, char_data)

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

    def _big_number_width(self, digits, narrow_one=False):
        """빅넘버 문자열의 총 칸 수를 계산합니다."""
        w = 0
        for d in digits:
            if narrow_one and d == '1':
                w += 2
            else:
                w += 3
        return w

    def _write_big_number(self, digits, start_col, narrow_one=False):
        """빅넘버를 LCD에 씁니다."""
        col = start_col
        for d in digits:
            if d not in BIG_DIGITS:
                continue
            if narrow_one and d == '1':
                top, bot = BIG_DIGIT_1_NARROW
            else:
                top, bot = BIG_DIGITS[d]
            for j, ch in enumerate(top):
                self.lcd.cursor_pos = (0, col + j)
                self.lcd.write_string(chr(ch))
            for j, ch in enumerate(bot):
                self.lcd.cursor_pos = (1, col + j)
                self.lcd.write_string(chr(ch))
            col += len(top)
        return col

    def show_dust_data(self, data, outdoor_pm25=None):
        """
        미세먼지 데이터를 LCD에 빅넘버로 표시합니다.
        3개 수치를 가로 한 줄처럼 보이도록 2줄에 걸쳐 크게 표시합니다.

        표시 형식 (16x2 LCD, 3칸×2줄 빅넘버):
            ██▀██ ══█ █▀█     ← 윗줄
            ██▄██ █▄▄ █▄█     ← 아랫줄
             10    2   40     (실제 수치)
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

            # 총 너비 계산 (구분자 포함)
            # 먼저 "1"을 좁게 쓰는 모드로 시도
            w1 = self._big_number_width(s1, narrow_one=True)
            w2 = self._big_number_width(s2, narrow_one=True)
            w3 = self._big_number_width(s3, narrow_one=True)
            total = w1 + 1 + w2 + 1 + w3  # 구분자 1칸씩

            narrow = True
            if total > self.cols:
                # 좁은 1로도 안 되면 구분자 없이 시도
                total = w1 + w2 + w3
                if total > self.cols:
                    # 빅넘버가 안 들어가면 일반 텍스트로 표시
                    line = f"{pm1:>4}  {pm25:>4}  {s3:>4}"
                    self.lcd.cursor_pos = (0, 0)
                    self.lcd.write_string(line[:self.cols])
                    self.lcd.cursor_pos = (1, 0)
                    self.lcd.write_string(line[:self.cols])
                    return

            self.lcd.clear()

            # 센터링: 남는 공간을 양쪽에 분배
            pad = (self.cols - total) // 2
            col = pad

            # 첫 번째 수치
            col = self._write_big_number(s1, col, narrow_one=narrow)

            # 구분자 (공간이 있으면)
            if total <= self.cols - 2:
                col += 1  # 1칸 공백 구분

            # 두 번째 수치
            col = self._write_big_number(s2, col, narrow_one=narrow)

            # 구분자
            if total <= self.cols - 2:
                col += 1

            # 세 번째 수치
            self._write_big_number(s3, col, narrow_one=narrow)

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
