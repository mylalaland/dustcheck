# ============================================================
# DustCheck 설정 파일
# ============================================================
# 이 파일에서 본인 환경에 맞게 값을 수정하세요.
# 수정할 곳에 ★ 표시가 되어 있습니다.
# ============================================================

# ─────────────────────────────────────────────
# ★ Firebase 설정 (FIREBASE_GUIDE.md 참고)
# ─────────────────────────────────────────────
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"  # 서비스 계정 키 파일 경로
FIREBASE_DATABASE_URL = "https://dustcheck-da9e1-default-rtdb.firebaseio.com/"  # ✅ 설정 완료!

# ─────────────────────────────────────────────
# LCD 설정
# ─────────────────────────────────────────────
LCD_I2C_ADDRESS = 0x27  # ★ i2cdetect로 확인 (0x27 또는 0x3F)
LCD_I2C_EXPANDER = "PCF8574"  # I2C 백팩 칩 종류
LCD_COLS = 16  # LCD 칸 수
LCD_ROWS = 2   # LCD 줄 수

# ─────────────────────────────────────────────
# 센서 설정
# ─────────────────────────────────────────────
I2C_BUS = 1  # I2C 버스 번호 (라즈베리파이는 보통 1)
SENSOR_READ_INTERVAL = 10  # 센서 읽기 주기 (초)
FIREBASE_SEND_INTERVAL = 60  # Firebase 전송 주기 (초)

# ─────────────────────────────────────────────
# ★ 실외 미세먼지 (에어코리아 API)
# ─────────────────────────────────────────────
# API 키 발급: https://www.data.go.kr/data/15073861/openapi.do
# 무료 회원가입 후 즉시 발급 가능합니다.
AIRKOREA_API_KEY = ""  # ★ data.go.kr에서 발급받은 인코딩된 API 키
AIRKOREA_STATION = "물금읍"  # ★ 양산시 측정소 (물금읍, 북부동, 웅상읍 등)

# ─────────────────────────────────────────────
# CSV 백업 설정
# ─────────────────────────────────────────────
CSV_SAVE_DIR = "data"  # CSV 파일 저장 폴더
CSV_SAVE_INTERVAL = 60  # CSV 저장 주기 (초) - Firebase 전송과 동일

# ─────────────────────────────────────────────
# 공기질 등급 기준 (단위: μg/m³)
# WHO 및 한국 환경부 기준 참고
# ─────────────────────────────────────────────
AIR_QUALITY_LEVELS = {
    "pm1": [
        {"label": "좋음",     "label_en": "Good",      "max": 10,  "emoji": "😊", "color": "#00d4aa"},
        {"label": "보통",     "label_en": "Normal",    "max": 25,  "emoji": "🙂", "color": "#ffc107"},
        {"label": "나쁨",     "label_en": "Bad",       "max": 50,  "emoji": "😷", "color": "#ff6b35"},
        {"label": "매우나쁨", "label_en": "Very Bad",  "max": 9999, "emoji": "🚨", "color": "#ff2d55"},
    ],
    "pm25": [
        {"label": "좋음",     "label_en": "Good",      "max": 15,  "emoji": "😊", "color": "#00d4aa"},
        {"label": "보통",     "label_en": "Normal",    "max": 35,  "emoji": "🙂", "color": "#ffc107"},
        {"label": "나쁨",     "label_en": "Bad",       "max": 75,  "emoji": "😷", "color": "#ff6b35"},
        {"label": "매우나쁨", "label_en": "Very Bad",  "max": 9999, "emoji": "🚨", "color": "#ff2d55"},
    ],
    "pm10": [
        {"label": "좋음",     "label_en": "Good",      "max": 30,  "emoji": "😊", "color": "#00d4aa"},
        {"label": "보통",     "label_en": "Normal",    "max": 80,  "emoji": "🙂", "color": "#ffc107"},
        {"label": "나쁨",     "label_en": "Bad",       "max": 150, "emoji": "😷", "color": "#ff6b35"},
        {"label": "매우나쁨", "label_en": "Very Bad",  "max": 9999, "emoji": "🚨", "color": "#ff2d55"},
    ],
}


def get_air_quality(pm_type, value):
    """미세먼지 값으로 공기질 등급을 반환합니다."""
    levels = AIR_QUALITY_LEVELS.get(pm_type, AIR_QUALITY_LEVELS["pm25"])
    for level in levels:
        if value <= level["max"]:
            return level
    return levels[-1]
