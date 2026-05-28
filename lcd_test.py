"""LCD 진단 스크립트 - PC에서 SSH로 파이에 접속하여 LCD 테스트"""
import paramiko
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOSTNAME = '10.101.72.200'
USERNAME = 'pi'
PASSWORD = 'pipi'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD, timeout=10)
print(f"✅ SSH 연결: {USERNAME}@{HOSTNAME}")

# 1. I2C 디바이스 스캔
print("\n[1] I2C 디바이스 스캔:")
stdin, stdout, stderr = ssh.exec_command('i2cdetect -y 1')
print(stdout.read().decode())

# 2. 현재 실행 중인 monitor.py 프로세스 확인
print("[2] monitor.py 프로세스 확인:")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep monitor | grep -v grep')
out = stdout.read().decode().strip()
print(f"  {'실행 중: ' + out if out else '❌ 실행 중인 monitor.py 없음'}")

# 3. LCD 직접 테스트
print("\n[3] LCD 직접 테스트:")
test_script = '''python3 -u -c "
from RPLCD.i2c import CharLCD
import time

print('LCD 초기화 중...')
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)
print('LCD 객체 생성 완료')

lcd.clear()
print('LCD clear 완료')

lcd.backlight_enabled = True
print('백라이트 ON')

lcd.cursor_pos = (0, 0)
lcd.write_string('PM1  PM2.5  PM10')
lcd.cursor_pos = (1, 0)
lcd.write_string('10.7  11.3  11.3')
print('텍스트 출력 완료 - LCD를 확인하세요!')
" 2>&1'''

stdin, stdout, stderr = ssh.exec_command(test_script)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print(f"  에러: {err}")

ssh.close()
print("\n✅ 진단 완료")
