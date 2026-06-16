# 🌬️ DustCheck - 실내 미세먼지 모니터링 시스템

> SPS30 센서 + 라즈베리파이5 + Firebase + 웹 대시보드

실내 미세먼지를 실시간으로 측정하고, 예쁜 웹 대시보드로 어디서든 확인할 수 있는 IoT 프로젝트입니다.

---

## 📦 필요한 부품

| 부품 | 설명 | 비고 |
|------|------|------|
| 라즈베리파이 5 | 메인 컴퓨터 | 4GB 이상 권장 |
| SPS30 센서 | 센서리온 미세먼지 센서 | PM1.0/2.5/4.0/10 측정 |
| LCD 1602 I2C | 16x2 캐릭터 LCD (I2C 백팩 포함) | 실시간 수치 표시용 |
| Micro SD 카드 | 라즈베리파이 OS 설치용 | 16GB 이상 |
| 3.1A 어댑터 | 라즈베리파이5 전원 | USB-C |
| 점퍼 케이블 | F/F 타입 | SPS30: 5가닥, LCD: 4가닥 |
| 브레드보드 (선택) | SDA/SCL 핀 공유용 | 없으면 꼬아서 연결 |

---

## 🚀 빠른 시작 (5단계)

### 1단계: 라즈베리파이 OS 설치
👉 [상세 가이드: SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

### 2단계: 하드웨어 선 연결
👉 [상세 가이드: WIRING_GUIDE.md](docs/WIRING_GUIDE.md)

### 3단계: Firebase 프로젝트 만들기
👉 [상세 가이드: FIREBASE_GUIDE.md](docs/FIREBASE_GUIDE.md)

### 4단계: 라즈베리파이에서 프로그램 실행

```bash
# 1. GitHub에서 프로젝트 클론
git clone https://github.com/mylalaland/dustcheck
cd dustcheck/raspberry-pi

# 2. 자동 설치 스크립트 실행 (한 번만)
chmod +x setup.sh
./setup.sh

# 3. Firebase 서비스 계정 키 파일 복사 (필수!)
#    Firebase Console → 프로젝트 설정 → 서비스 계정 → 새 비공개 키 생성
#    다운로드한 파일을 serviceAccountKey.json 으로 이름 변경 후 이 폴더에 넣기
cp /path/to/downloaded-key.json serviceAccountKey.json

# 4. config.py에서 Firebase URL과 에어코리아 설정 확인
nano config.py

# 5. 가상환경 활성화 후 실행!
source dust_env/bin/activate
python monitor.py
```

> ⚠️ **중요**: `serviceAccountKey.json` 파일은 보안상 GitHub에 포함되지 않습니다.
> Firebase Console에서 직접 다운로드하여 `raspberry-pi/` 폴더에 넣어야 합니다.

### 5단계: 웹 대시보드 배포
```bash
# Firebase CLI 설치 (라즈베리파이 또는 PC에서)
npm install -g firebase-tools
firebase login

# web-dashboard 폴더에서
cd dustcheck/web-dashboard
firebase deploy
```

배포 후 `https://프로젝트명.web.app` 주소로 접속하면 실시간 미세먼지 대시보드를 볼 수 있습니다!

---

## 📊 기능 요약

- ✅ **실시간 측정**: PM1.0, PM2.5, PM4.0, PM10 동시 측정 (10초 간격)
- ✅ **LCD 전광판**: 큰 숫자 3자리 대응, 공기질 등급 표시
- ✅ **실외 미세먼지**: 에어코리아 API로 지역 PM2.5/PM10 수치 표시
- ✅ **클라우드 저장**: Firebase Realtime Database에 1분마다 자동 전송
- ✅ **로컬 백업**: CSV 파일로 라즈베리파이에도 백업
- ✅ **웹 대시보드**: 실시간/24시간/7일/30일/1년 그래프 + 공기질 게이지
- ✅ **5개 PM 카드**: PM1.0, PM2.5, 지역PM2.5, PM10, 지역PM10
- ✅ **측정소 검색**: 지역명 입력으로 가까운 에어코리아 측정소 설정
- ✅ **반응형 디자인**: 스마트폰/태블릿/PC 모두 지원
- ✅ **다크모드**: 라이트/다크 테마 전환
- ✅ **외부 공유**: Firebase Hosting으로 누구나 접속 가능
- ✅ **커스텀 도메인**: 본인 도메인 연결 가능

---

## ⚙️ 설정 파일 안내

### `raspberry-pi/config.py` (라즈베리파이용)

```python
# Firebase 설정 (필수 수정)
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://프로젝트명-default-rtdb.firebaseio.com/"

# 에어코리아 설정 (실외 미세먼지 조회)
AIRKOREA_API_KEY = "data.go.kr에서 발급받은 API 키"
AIRKOREA_STATION = "물금읍"  # 가까운 측정소명

# 측정 설정
SENSOR_READ_INTERVAL = 10   # 센서 읽기 주기 (초)
FIREBASE_SEND_INTERVAL = 60  # Firebase 전송 주기 (초)
```

### `web-dashboard/js/config.js` (웹 대시보드용)

```javascript
// Firebase 클라이언트 설정 (필수 수정)
const FIREBASE_CONFIG = {
    apiKey: "Firebase Console에서 확인",
    databaseURL: "https://프로젝트명-default-rtdb.firebaseio.com",
    projectId: "프로젝트명",
    // ... 나머지 설정
};

// 에어코리아 API 키 (실외 미세먼지용)
const AIRKOREA_API_KEY = "data.go.kr에서 발급받은 API 키";
```

---

## 📁 프로젝트 구조

```
dustcheck/
├── README.md                     ← 지금 보고 있는 파일
├── docs/                         ← 상세 가이드 문서
│   ├── SETUP_GUIDE.md
│   ├── WIRING_GUIDE.md
│   └── FIREBASE_GUIDE.md
├── raspberry-pi/                 ← 라즈베리파이 실행 코드
│   ├── config.py                 ← ⚙️ 설정값 (이것만 수정!)
│   ├── sensor.py                 ← SPS30 센서 제어
│   ├── display.py                ← LCD 전광판 표시
│   ├── outdoor.py                ← 에어코리아 실외 미세먼지 조회
│   ├── firebase_uploader.py      ← Firebase 전송 (실외 포함)
│   ├── csv_logger.py             ← CSV 백업
│   ├── monitor.py                ← 🚀 메인 실행 파일
│   ├── setup.sh                  ← 자동 설치 스크립트
│   └── requirements.txt
└── web-dashboard/                ← 웹 대시보드 (Firebase 배포용)
    ├── index.html
    ├── css/style.css
    ├── js/app.js
    ├── js/config.js              ← ⚙️ Firebase + API 설정
    ├── firebase.json
    └── .firebaserc
```

---

## 🔒 보안 안내

| 파일 | GitHub 포함 | 설명 |
|------|:-:|------|
| `serviceAccountKey.json` | ❌ | Firebase 서비스 계정 키. 절대 공유하지 마세요. |
| `config.py` | ✅ | 에어코리아 API 키 포함. 필요 시 본인 키로 교체. |
| `config.js` | ✅ | Firebase 클라이언트 설정 (공개 설계). |

> 💡 다른 Pi에서 이 프로젝트를 실행하려면 `serviceAccountKey.json` 파일만 별도로 복사하면 됩니다.

---

## 🌐 에어코리아 API 설정

실외 미세먼지 조회를 위해 [data.go.kr](https://www.data.go.kr/)에서 아래 2개 API를 신청하세요:

1. **한국환경공단_에어코리아_대기오염정보** - 대기질 측정값 조회
2. **한국환경공단_에어코리아_측정소정보** - 측정소 검색 (웹에서 측정소 변경 시)

발급받은 인코딩 API 키를 `config.py`와 `config.js`에 넣으면 됩니다.

---

## ❓ 문제 해결

| 증상 | 해결 방법 |
|------|-----------|
| LCD에 아무것도 안 나옴 | LCD 뒷면 파란 가변저항을 돌려 밝기 조절 |
| SPS30 센서를 못 찾음 | SEL 핀이 GND에 연결됐는지 확인 |
| Firebase 전송 실패 | Wi-Fi 연결 확인 + `config.py`의 URL 확인 |
| 웹 그래프가 안 나옴 | `js/config.js`의 Firebase 설정값 확인 |
| `i2cdetect`에 기기 안 보임 | `sudo raspi-config`에서 I2C 활성화 확인 |
| `serviceAccountKey.json` 에러 | Firebase Console에서 키 파일 다운로드 후 폴더에 넣기 |
| 실외 미세먼지가 안 나옴 | `config.py`에 에어코리아 API 키 설정 확인 |
| 웹에서 지역 데이터 그래프 없음 | Pi가 실행 중이어야 실외 데이터가 Firebase에 쌓임 |

---

## 📜 라이선스

이 프로젝트는 자유롭게 사용, 수정, 배포할 수 있습니다.  
참조: [SPS30으로 실내 미세먼지 측정하기 (zariski 블로그)](https://zariski.wordpress.com/2026/03/21/sps30%ec%9c%bc%eb%a1%9c-%ec%8b%a4%eb%82%b4-%eb%af%b8%ec%84%b8%eb%a8%bc%ec%a7%80-%ec%b8%a1%ec%a0%95%ed%95%98%ea%b8%b0/)
