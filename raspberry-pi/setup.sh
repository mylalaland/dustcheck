#!/bin/bash
# ============================================================
# DustCheck 자동 설치 스크립트
# ============================================================
# 라즈베리파이에서 이 스크립트를 실행하면
# 필요한 모든 것이 자동으로 설치됩니다.
#
# 실행 방법:
#   chmod +x setup.sh
#   ./setup.sh
# ============================================================

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  🌬️  DustCheck 설치 스크립트                ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. 시스템 패키지 업데이트
echo "📦 [1/4] 시스템 패키지 업데이트 중..."
sudo apt-get update -y
sudo apt-get install -y i2c-tools python3-pip python3-venv

# 2. I2C 활성화 확인
echo ""
echo "🔌 [2/4] I2C 활성화 확인 중..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
    echo "⚠️  I2C가 비활성화되어 있을 수 있습니다."
    echo "    sudo raspi-config → Interface Options → I2C → Yes"
    echo "    설정 후 재부팅하세요: sudo reboot"
else
    echo "✅ I2C가 활성화되어 있습니다."
fi

# 3. Python 가상환경 생성 및 패키지 설치
echo ""
echo "🐍 [3/4] Python 가상환경 설정 중..."
if [ ! -d "dust_env" ]; then
    python3 -m venv dust_env
    echo "✅ 가상환경 생성 완료: dust_env/"
else
    echo "✅ 가상환경이 이미 존재합니다."
fi

source dust_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python 패키지 설치 완료!"

# 4. 데이터 폴더 생성
echo ""
echo "📁 [4/4] 데이터 폴더 생성 중..."
mkdir -p data
echo "✅ data/ 폴더 생성 완료"

# I2C 기기 확인
echo ""
echo "═══════════════════════════════════════════════"
echo "🔍 I2C 기기 스캔 결과:"
echo "═══════════════════════════════════════════════"
i2cdetect -y 1 2>/dev/null || echo "⚠️ I2C 스캔 실패 (재부팅이 필요할 수 있습니다)"

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ 설치 완료!"
echo "═══════════════════════════════════════════════"
echo ""
echo "다음 단계:"
echo "  1. config.py 에서 Firebase URL을 수정하세요"
echo "  2. serviceAccountKey.json 파일을 이 폴더에 넣으세요"
echo "  3. 실행: source dust_env/bin/activate && python monitor.py"
echo ""
