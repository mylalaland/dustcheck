#!/usr/bin/env python3
"""
DustCheck - 실내 미세먼지 모니터링 시스템
==========================================
SPS30 센서로 미세먼지를 측정하고,
LCD에 표시하고, Firebase에 전송하고, CSV에 백업합니다.

실행: python monitor.py
종료: Ctrl + C
"""

import sys
import time
import signal
import logging
from datetime import datetime

from config import (
    FIREBASE_CREDENTIALS_PATH,
    FIREBASE_DATABASE_URL,
    LCD_I2C_ADDRESS,
    LCD_I2C_EXPANDER,
    LCD_COLS,
    LCD_ROWS,
    I2C_BUS,
    SENSOR_READ_INTERVAL,
    FIREBASE_SEND_INTERVAL,
    CSV_SAVE_DIR,
    AIRKOREA_API_KEY,
    AIRKOREA_STATION,
    get_air_quality,
)
from sensor import DustSensor
from display import DustDisplay
from firebase_uploader import FirebaseUploader
from csv_logger import CSVLogger
from outdoor import fetch_outdoor_data

# ─────────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("dustcheck.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 콘솔 컬러 출력
# ─────────────────────────────────────────────
COLORS = {
    "좋음": "\033[92m",      # 초록
    "보통": "\033[93m",      # 노랑
    "나쁨": "\033[91m",      # 빨강
    "매우나쁨": "\033[95m",  # 보라
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "DIM": "\033[2m",
}


def print_banner():
    """시작 배너를 출력합니다."""
    banner = f"""
{COLORS['BOLD']}╔══════════════════════════════════════════════╗
║  🌬️  DustCheck v1.0 - 미세먼지 모니터링     ║
║  센서: SPS30 | 화면: LCD 1602 | DB: Firebase ║
╚══════════════════════════════════════════════╝{COLORS['RESET']}
"""
    print(banner)


def print_dust_data(data, quality):
    """미세먼지 데이터를 컬러로 콘솔에 출력합니다."""
    color = COLORS.get(quality["label"], "")
    reset = COLORS["RESET"]
    dim = COLORS["DIM"]
    now = datetime.now().strftime("%H:%M:%S")

    print(
        f"{dim}[{now}]{reset} "
        f"PM2.5: {color}{data['pm25']:6.1f}{reset} | "
        f"PM10: {data['pm10']:6.1f} | "
        f"PM1.0: {data['pm1']:5.1f} | "
        f"PM4.0: {data['pm4']:5.1f} | "
        f"등급: {color}{quality['emoji']} {quality['label']}{reset}"
    )


class DustCheckMonitor:
    """메인 모니터링 클래스"""

    def __init__(self):
        self.running = False
        self.sensor = None
        self.display = None
        self.uploader = None
        self.csv_logger = None
        self.last_firebase_time = 0
        self.reading_count = 0

    def setup(self):
        """모든 컴포넌트를 초기화합니다."""
        print_banner()
        logger.info("시스템을 초기화하는 중...")

        # 1. 센서 초기화
        logger.info("─── 센서 초기화 ───")
        self.sensor = DustSensor(I2C_BUS)

        # 2. LCD 초기화
        logger.info("─── LCD 초기화 ───")
        self.display = DustDisplay(
            address=LCD_I2C_ADDRESS,
            expander=LCD_I2C_EXPANDER,
            cols=LCD_COLS,
            rows=LCD_ROWS,
        )

        # 3. Firebase 초기화
        logger.info("─── Firebase 초기화 ───")
        self.uploader = FirebaseUploader(
            FIREBASE_CREDENTIALS_PATH,
            FIREBASE_DATABASE_URL,
        )

        # 4. CSV 로거 초기화
        logger.info("─── CSV 로거 초기화 ───")
        self.csv_logger = CSVLogger(CSV_SAVE_DIR)

        # 상태 요약
        print()
        logger.info("═══ 초기화 결과 ═══")
        logger.info(f"  센서 (SPS30):  {'✅ 연결됨' if self.sensor.connected else '❌ 미연결'}")
        logger.info(f"  화면 (LCD):    {'✅ 연결됨' if self.display.connected else '⚠️ 미연결 (콘솔만 사용)'}")
        logger.info(f"  클라우드 (FB): {'✅ 연결됨' if self.uploader.connected else '⚠️ 미연결 (로컬만 저장)'}")
        logger.info(f"  CSV 백업:      ✅ 활성")
        logger.info(f"  실외 PM2.5:    {'✅ API 키 설정됨 (' + AIRKOREA_STATION + ')' if AIRKOREA_API_KEY else '⚠️ API 키 미설정'}")
        logger.info(f"  측정 주기:     {SENSOR_READ_INTERVAL}초")
        logger.info(f"  전송 주기:     {FIREBASE_SEND_INTERVAL}초")
        print()

        # 실외 PM2.5/PM10 초기 조회
        if AIRKOREA_API_KEY:
            outdoor_init = fetch_outdoor_data(AIRKOREA_API_KEY, AIRKOREA_STATION)
            if outdoor_init["pm25"] is not None:
                logger.info(f"  실외 PM2.5 ({AIRKOREA_STATION}): {outdoor_init['pm25']} μg/m³, PM10: {outdoor_init['pm10']} μg/m³")
            else:
                logger.warning(f"  실외 미세먼지 초기 조회 실패")

        if not self.sensor.connected:
            logger.error("⚠️  센서가 연결되지 않았습니다! 선 연결을 확인하세요.")
            logger.error("    docs/WIRING_GUIDE.md 를 참고하세요.")

    def run(self):
        """메인 모니터링 루프를 실행합니다."""
        self.running = True
        logger.info("🚀 측정을 시작합니다! (종료: Ctrl+C)")
        print("─" * 60)

        while self.running:
            try:
                # 센서 데이터 읽기
                data = self.sensor.read()

                if data["ok"]:
                    self.reading_count += 1
                    quality = get_air_quality("pm25", data["pm25"])

                    # 실외 PM2.5/PM10 조회 (LCD + Firebase 공용)
                    outdoor = fetch_outdoor_data(AIRKOREA_API_KEY, AIRKOREA_STATION) if AIRKOREA_API_KEY else {"pm25": None, "pm10": None}
                    outdoor_pm25 = outdoor["pm25"]
                    outdoor_pm10 = outdoor["pm10"]

                    # 콘솔 출력
                    print_dust_data(data, quality)

                    # LCD 표시
                    self.display.show_dust_data(data, outdoor_pm25=outdoor_pm25)

                    # Firebase 전송 (주기 확인) - 실외 데이터 포함
                    now = time.time()
                    if now - self.last_firebase_time >= FIREBASE_SEND_INTERVAL:
                        if outdoor_pm25 is not None:
                            data["outdoor_pm25"] = outdoor_pm25
                        if outdoor_pm10 is not None:
                            data["outdoor_pm10"] = outdoor_pm10
                        self.uploader.upload(data)
                        self.csv_logger.save(data)
                        self.last_firebase_time = now

                # 대기
                time.sleep(SENSOR_READ_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"루프 오류: {e}")
                time.sleep(SENSOR_READ_INTERVAL)

    def shutdown(self):
        """시스템을 종료합니다."""
        self.running = False
        print()
        logger.info("시스템을 종료하는 중...")

        # 센서 정지
        if self.sensor:
            self.sensor.stop()

        # LCD 종료 메시지
        if self.display:
            self.display.show_message("DustCheck", "Stopped.")
            time.sleep(1)
            self.display.clear()

        count = self.csv_logger.get_today_count() if self.csv_logger else 0
        logger.info(f"총 {self.reading_count}회 측정, 오늘 CSV {count}건 저장")
        logger.info("👋 DustCheck를 종료합니다.")


def main():
    """메인 함수"""
    monitor = DustCheckMonitor()

    # Ctrl+C 핸들러
    def signal_handler(sig, frame):
        monitor.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        monitor.setup()
        monitor.run()
    except Exception as e:
        logger.error(f"치명적 오류: {e}")
    finally:
        monitor.shutdown()


if __name__ == "__main__":
    main()
