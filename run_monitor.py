"""
수정된 sensor.py를 다시 전송하고 monitor.py를 실행합니다 (40초간 측정)
"""
import paramiko
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOSTNAME = '192.168.200.112'
USERNAME = 'pi'
PASSWORD = 'pipi'
REMOTE_DIR = '/home/pi/dustcheck'
LOCAL_DIR = os.path.join(os.path.dirname(__file__), 'raspberry-pi')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD, timeout=10)
print("✅ SSH 연결 완료\n")

# 수정된 sensor.py 재전송
print("📄 수정된 sensor.py 전송 중...")
sftp = ssh.open_sftp()
sftp.put(os.path.join(LOCAL_DIR, 'sensor.py'), f'{REMOTE_DIR}/sensor.py')
sftp.close()
print("✅ 전송 완료!\n")

# monitor.py 실행 (40초)
print("=" * 60)
print("🌬️  미세먼지 측정 시작! (약 40초간 측정)")
print("=" * 60)

run_cmd = f'cd {REMOTE_DIR} && timeout 40 python3 -u monitor.py 2>&1'
stdin, stdout, stderr = ssh.exec_command(run_cmd, get_pty=True)

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
