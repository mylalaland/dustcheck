import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.200.112', username='pi', password='pipi', timeout=10)

# Check SPS30 library API
cmd = """python3 -c "
from sps30 import SPS30
s = SPS30(1)
print('=== SPS30 methods ===')
methods = [m for m in dir(s) if not m.startswith('_')]
for m in methods:
    print(f'  {m}')
print()
print('=== Try read_article_code ===')
try:
    r = s.read_article_code()
    print(f'  article_code = {r}')
except Exception as e:
    print(f'  ERROR: {e}')
print()
print('=== Try serial ===')
try:
    r = s.read_serial()
    print(f'  serial = {r}')
except Exception as e:
    print(f'  ERROR: {e}')
" 2>&1
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8').strip()
print(out)
ssh.close()
