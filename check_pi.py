import paramiko
import sys

HOSTNAME = '10.101.72.200'
USERNAME = 'pi'
PASSWORD = 'pipi'

print("Connecting to Pi...")
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOSTNAME, username=USERNAME, password=PASSWORD, timeout=5)
    print("Connected.")
    
    print("\n--- systemctl status dustcheck ---")
    stdin, stdout, stderr = ssh.exec_command('systemctl status dustcheck --no-pager -l')
    print(stdout.read().decode('utf-8'))
    
    print("\n--- journalctl -u dustcheck -n 30 ---")
    stdin, stdout, stderr = ssh.exec_command('journalctl -u dustcheck -n 30 --no-pager')
    print(stdout.read().decode('utf-8'))
    
    print("\n--- monitor.log ---")
    stdin, stdout, stderr = ssh.exec_command('tail -n 30 /home/pi/dustcheck/monitor.log')
    print(stdout.read().decode('utf-8'))

    ssh.close()
except Exception as e:
    print(f"Error: {e}")
