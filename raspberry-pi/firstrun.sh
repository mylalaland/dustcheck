#!/bin/bash
# ============================================================
# 첫 부팅 시 실행되는 스크립트 (Raspberry Pi Imager --first-run-script)
# 사용자 pi 생성 및 비밀번호 pipi 설정, SSH 활성화, I2C 활성화
# ============================================================

set -e

# 사용자 pi 생성 (이미 있으면 스킵)
if ! id -u pi >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo pi
fi

# 비밀번호 설정
echo 'pi:pipi' | chpasswd

# sudo 비밀번호 없이 사용
echo 'pi ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/010_pi-nopasswd
chmod 0440 /etc/sudoers.d/010_pi-nopasswd

# SSH 활성화
systemctl enable ssh
systemctl start ssh

# 호스트명 설정
echo "pi" > /etc/hostname
sed -i 's/127.0.1.1.*/127.0.1.1\tpi/' /etc/hosts

# 타임존 설정
timedatectl set-timezone Asia/Seoul

# 키보드 레이아웃
localectl set-keymap kr 2>/dev/null || true

# I2C 활성화
if ! grep -q "^i2c-dev" /etc/modules 2>/dev/null; then
    echo "i2c-dev" >> /etc/modules
fi
modprobe i2c-dev 2>/dev/null || true

# 고정 IP 설정 (NetworkManager)
nmcli connection modify "Wired connection 1" \
    ipv4.method manual \
    ipv4.addresses 10.101.72.213/24 \
    ipv4.gateway 10.101.72.254 \
    ipv4.dns 168.126.63.1 \
    connection.autoconnect yes 2>/dev/null || \
nmcli connection add type ethernet con-name "static-eth0" ifname eth0 \
    ipv4.method manual \
    ipv4.addresses 10.101.72.213/24 \
    ipv4.gateway 10.101.72.254 \
    ipv4.dns 168.126.63.1 \
    connection.autoconnect yes 2>/dev/null || true

# 필수 패키지 설치
apt-get update -y
apt-get install -y i2c-tools python3-pip python3-venv python3-smbus git avahi-daemon

# DustCheck 설치 (boot 파티션에서 복사)
DUSTCHECK_DIR="/home/pi/dustcheck"
BOOT_FILES="/boot/firmware/dustcheck-files"

if [ -d "$BOOT_FILES" ]; then
    mkdir -p "$DUSTCHECK_DIR"
    cp -r "${BOOT_FILES}/"* "$DUSTCHECK_DIR/"
    chown -R pi:pi "$DUSTCHECK_DIR"
    
    # Python 가상환경 설정
    sudo -u pi python3 -m venv "${DUSTCHECK_DIR}/dust_env"
    sudo -u pi "${DUSTCHECK_DIR}/dust_env/bin/pip" install --upgrade pip
    sudo -u pi "${DUSTCHECK_DIR}/dust_env/bin/pip" install -r "${DUSTCHECK_DIR}/requirements.txt"
    
    # 데이터 폴더 생성
    mkdir -p "${DUSTCHECK_DIR}/data"
    chown -R pi:pi "${DUSTCHECK_DIR}/data"
    
    # systemd 서비스 등록
    cp "${DUSTCHECK_DIR}/dustcheck.service" /etc/systemd/system/dustcheck.service
    systemctl daemon-reload
    systemctl enable dustcheck.service
    
    echo "DustCheck 설치 완료!" >> /var/log/dustcheck-firstboot.log
fi

# 이 스크립트 자신을 삭제 (한 번만 실행)
rm -f /boot/firmware/firstrun.sh
