# ☁️ 3단계: Firebase 설정 가이드

> Firebase를 사용하면 데이터를 클라우드에 저장하고, 웹사이트도 무료로 호스팅할 수 있습니다.

## 1. Firebase 프로젝트 만들기

1. [Firebase 콘솔](https://console.firebase.google.com/) 접속
2. Google 계정으로 로그인
3. **"프로젝트 추가"** 클릭
4. 프로젝트 이름: `dustcheck` (원하는 이름으로)
5. Google 애널리틱스: **사용 안함** 선택 (간단하게 하기 위해)
6. **"프로젝트 만들기"** 클릭

## 2. Realtime Database 만들기

1. 왼쪽 메뉴 → **빌드** → **Realtime Database**
2. **"데이터베이스 만들기"** 클릭
3. 위치: `싱가포르` 또는 `미국` 선택
4. 보안 규칙: **"테스트 모드에서 시작"** 선택 → 사용 설정

> ⚠️ 테스트 모드는 30일 후 만료됩니다. 나중에 규칙을 아래처럼 변경하세요:
```json
{
  "rules": {
    "dust_data": { ".read": true, ".write": true },
    "latest": { ".read": true, ".write": true }
  }
}
```

5. 데이터베이스 URL을 복사합니다 (예: `https://dustcheck-xxxxx-default-rtdb.firebaseio.com/`)

## 3. 서비스 계정 키 만들기 (라즈베리파이용)

1. Firebase 콘솔 → ⚙️ **프로젝트 설정** (왼쪽 위 톱니바퀴)
2. **서비스 계정** 탭 클릭
3. **"새 비공개 키 생성"** 클릭 → JSON 파일 다운로드
4. 파일 이름을 `serviceAccountKey.json`으로 변경
5. 이 파일을 라즈베리파이의 `raspberry-pi/` 폴더에 넣습니다

> ⚠️ **이 파일은 비밀번호와 같습니다! 절대 공개하지 마세요!**

## 4. 웹 앱 등록 (대시보드용)

1. Firebase 콘솔 → ⚙️ **프로젝트 설정**
2. **일반** 탭 → 아래쪽 **"내 앱"** → `</>` (웹) 아이콘 클릭
3. 앱 닉네임: `dustcheck-web`
4. **Firebase Hosting 설정** 체크
5. **"앱 등록"** 클릭
6. 나오는 `firebaseConfig` 값을 복사합니다:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "dustcheck-xxxxx.firebaseapp.com",
  databaseURL: "https://dustcheck-xxxxx-default-rtdb.firebaseio.com",
  projectId: "dustcheck-xxxxx",
  storageBucket: "dustcheck-xxxxx.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};
```

7. 이 값을 `web-dashboard/js/config.js` 파일에 붙여넣습니다

## 5. Firebase Hosting 배포

```bash
# Node.js 설치 (라즈베리파이 또는 PC)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

# Firebase CLI 설치
sudo npm install -g firebase-tools

# Firebase 로그인
firebase login

# web-dashboard 폴더에서 배포
cd dustcheck/web-dashboard
firebase deploy
```

배포 완료 후 `https://프로젝트명.web.app` 에서 대시보드를 볼 수 있습니다!

## 6. 커스텀 도메인 연결 (선택)

1. Firebase 콘솔 → **Hosting** → **커스텀 도메인 추가**
2. 본인 도메인 입력 (예: `dust.mydomain.com`)
3. 안내에 따라 도메인 DNS 설정에서 **A 레코드** 추가
4. SSL 인증서가 자동으로 발급됩니다 (최대 24시간)

## 다음 단계
👉 config.py와 js/config.js에 위에서 복사한 값들을 넣으세요!
