import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.200.112', username='pi', password='pipi', timeout=10)
print("=== Connected ===\n")

commands = [
    ("Project files", "ls -la ~/dustcheck/"),
    ("Installed packages", "pip3 list 2>/dev/null | grep -iE 'sps30|firebase|RPLCD'"),
    ("Python path check", "python3 -c 'import sps30; print(\"sps30 OK\")' 2>&1"),
    ("Firebase check", "python3 -c 'import firebase_admin; print(\"firebase OK\")' 2>&1"),
]

for title, cmd in commands:
    print(f"[{title}]")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8').strip()
    err = stderr.read().decode('utf-8').strip()
    if out:
        print(out)
    if err:
        print(f"(err): {err}")
    print("-" * 50)

ssh.close()
