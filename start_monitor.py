"""라즈베리파이에서 monitor.py를 백그라운드 상시 실행으로 시작"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOSTNAME = '10.101.72.200'
USERNAME = 'pi'
PASSWORD = 'pipi'
REMOTE_DIR = '/home/pi/dustcheck'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD, timeout=10)
print(f"✅ SSH 연결 성공\n")

# 1. 기존 monitor.py 프로세스 종료
print("[1/3] 기존 monitor.py 종료...")
ssh.exec_command("pkill -f 'python3.*monitor.py'")
time.sleep(2)

# 확인
stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python3.*monitor.py'")
remaining = stdout.read().decode().strip()
if remaining:
    print(f"  ⚠️ 아직 실행 중: {remaining}, 강제 종료...")
    ssh.exec_command("pkill -9 -f 'python3.*monitor.py'")
    time.sleep(1)
else:
    print("  ✅ 기존 프로세스 없음")

# 2. 백그라운드로 monitor.py 시작
print("\n[2/3] monitor.py 백그라운드 실행 시작...")
start_cmd = f'cd {REMOTE_DIR} && nohup python3 -u monitor.py > monitor_output.log 2>&1 &'
ssh.exec_command(start_cmd)
time.sleep(5)

# 3. 실행 확인
print("[3/3] 실행 상태 확인...")
stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python3.*monitor.py'")
pid = stdout.read().decode().strip()

if pid:
    print(f"  ✅ monitor.py 실행 중! (PID: {pid})")
    
    # 로그 마지막 몇 줄 확인
    stdin, stdout, stderr = ssh.exec_command(f'tail -8 {REMOTE_DIR}/monitor_output.log')
    log = stdout.read().decode()
    print(f"\n📋 최근 로그:")
    print(log)
else:
    print("  ❌ monitor.py 실행 실패!")
    stdin, stdout, stderr = ssh.exec_command(f'cat {REMOTE_DIR}/monitor_output.log | tail -20')
    print(stdout.read().decode())

ssh.close()
print("✅ 완료 - monitor.py가 백그라운드에서 계속 실행됩니다.")
print("   대시보드에 1분 내 데이터가 업데이트됩니다.")
