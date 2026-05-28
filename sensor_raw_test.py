"""SPS30 센서 Raw 데이터 직접 확인 스크립트"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.101.72.200', username='pi', password='pipi', timeout=10)
print("✅ SSH 연결\n")

# SPS30 raw dict_values 전체 덤프
test_script = '''python3 -u -c "
from sps30 import SPS30
import time

sps = SPS30(1)
sps.start_measurement()
time.sleep(3)

for i in range(5):
    if sps.read_data_ready_flag():
        sps.read_measured_values()
        print(f'=== 측정 #{i+1} ===')
        print(f'전체 dict_values: {sps.dict_values}')
        pm1 = sps.dict_values.get('pm1p0', 'N/A')
        pm25 = sps.dict_values.get('pm2p5', 'N/A')
        pm4 = sps.dict_values.get('pm4p0', 'N/A')
        pm10 = sps.dict_values.get('pm10p0', 'N/A')
        print(f'PM1.0={pm1}, PM2.5={pm25}, PM4.0={pm4}, PM10={pm10}')
        print(f'PM2.5-PM1.0 차이: {round(pm25-pm1, 3)}')
        print(f'PM10-PM2.5 차이: {round(pm10-pm25, 3)}')
        print()
    time.sleep(2)

sps.stop_measurement()
print('완료')
" 2>&1'''

stdin, stdout, stderr = ssh.exec_command(test_script, timeout=30)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print(f"에러: {err}")

ssh.close()
