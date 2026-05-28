"""
라즈베리파이에 DustCheck 프로젝트를 배포하고 실행하는 스크립트
1. SFTP로 파일 전송
2. pip으로 라이브러리 설치
3. monitor.py 실행 (30초간 측정 후 결과 출력)
"""
import paramiko
import sys
import io
import os
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOSTNAME = '10.101.72.200'
USERNAME = 'pi'
PASSWORD = 'pipi'
REMOTE_DIR = '/home/pi/dustcheck'
LOCAL_DIR = os.path.join(os.path.dirname(__file__), 'raspberry-pi')

# SSH 연결
print("=" * 60)
print("🚀 DustCheck 배포 시작")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD, timeout=10)
print(f"✅ SSH 연결: {USERNAME}@{HOSTNAME}\n")

# 1. 원격 디렉토리 생성
print("[1/3] 원격 디렉토리 생성...")
ssh.exec_command(f'mkdir -p {REMOTE_DIR}')
time.sleep(1)

# 2. SFTP로 파일 전송
print("[2/3] 파일 전송 중...")
sftp = ssh.open_sftp()

files_to_send = [
    'config.py',
    'monitor.py',
    'sensor.py',
    'display.py',
    'firebase_uploader.py',
    'csv_logger.py',
    'requirements.txt',
    'serviceAccountKey.json',
    'dustcheck.service',
    'setup_autostart.sh',
]

for filename in files_to_send:
    local_path = os.path.join(LOCAL_DIR, filename)
    remote_path = f'{REMOTE_DIR}/{filename}'
    if os.path.exists(local_path):
        sftp.put(local_path, remote_path)
        print(f"  📄 {filename} → 전송 완료")
    else:
        print(f"  ⚠️  {filename} → 로컬에 없음, 건너뜀")

sftp.close()
print()

# 2.5. Auto-start 설정
print("[2.5/3] 부팅 시 자동 시작 설정 중...")
autostart_cmds = [
    f'sudo cp {REMOTE_DIR}/dustcheck.service /etc/systemd/system/dustcheck.service',
    'sudo systemctl daemon-reload',
    'sudo systemctl enable dustcheck.service',
]
for cmd in autostart_cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
print("  ✅ systemd 서비스 등록 완료 (부팅 시 자동 시작)")
print()

# 3. 라이브러리 설치
print("[3/3] 필요 라이브러리 설치 중...")
install_cmd = 'pip3 install sps30 firebase-admin RPLCD smbus2 --break-system-packages 2>&1'
stdin, stdout, stderr = ssh.exec_command(install_cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
# Show key lines
for line in out.split('\n'):
    line = line.strip()
    if line and ('Successfully' in line or 'already' in line or 'Requirement' in line or 'Installing' in line):
        print(f"  {line}")
if err:
    for line in err.split('\n'):
        if line.strip() and 'WARNING' not in line:
            print(f"  (err) {line.strip()}")
print()

# 4. 측정 실행 (30초간)
print("=" * 60)
print("🌬️  미세먼지 측정 시작! (약 35초간 측정)")
print("=" * 60)

run_cmd = f'cd {REMOTE_DIR} && timeout 35 python3 -u monitor.py 2>&1'
stdin, stdout, stderr = ssh.exec_command(run_cmd, get_pty=True)

# Stream output in real-time
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')

err = stderr.read().decode('utf-8').strip()
if err:
    print(f"\n(stderr): {err}")

print("\n" + "=" * 60)
print("✅ 측정 완료!")
print("=" * 60)

ssh.close()
