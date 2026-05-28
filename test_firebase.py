"""
DustCheck Firebase 테스트 스크립트
Firebase에 더미 데이터를 보내서 웹 대시보드가 잘 작동하는지 확인합니다.
"""

import sys
import io
import time
import random
from datetime import datetime, timedelta

# 한글 출력 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import firebase_admin
from firebase_admin import credentials, db

# Firebase 초기화
cred = credentials.Certificate("raspberry-pi/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://dustcheck-da9e1-default-rtdb.firebaseio.com/"
})

dust_ref = db.reference("dust_data")
latest_ref = db.reference("latest")

print("=" * 50)
print("DustCheck Firebase Test")
print("=" * 50)

# 과거 30분치 데이터 생성 (1분 간격)
print("\n[*] Creating 30 minutes of test data...")
for i in range(30, 0, -1):
    t = datetime.now() - timedelta(minutes=i)
    record = {
        "time": t.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(t.timestamp() * 1000),
        "pm1": round(5 + random.random() * 10, 2),
        "pm25": round(10 + random.random() * 25, 2),
        "pm4": round(15 + random.random() * 20, 2),
        "pm10": round(18 + random.random() * 30, 2),
    }
    dust_ref.push(record)
    print(f"  [{record['time']}] PM2.5: {record['pm25']:.1f}")

# 최신값 업데이트
now = datetime.now()
latest_data = {
    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
    "timestamp": int(now.timestamp() * 1000),
    "pm1": 8.5,
    "pm25": 18.3,
    "pm4": 22.1,
    "pm10": 28.7,
}
latest_ref.set(latest_data)

print(f"\n[OK] Data sent successfully!")
print(f"   PM1.0: {latest_data['pm1']}")
print(f"   PM2.5: {latest_data['pm25']}")
print(f"   PM4.0: {latest_data['pm4']}")
print(f"   PM10:  {latest_data['pm10']}")
print(f"\n[*] Open http://localhost:8080 to see the dashboard!")
