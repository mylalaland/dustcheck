import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

candidates = ['192.168.200.112', '192.168.200.111']
USERNAME = 'pi'
PASSWORD = 'pipi'

for ip in candidates:
    print(f"Trying {ip}...", end=" ")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=USERNAME, password=PASSWORD, timeout=5)
        stdin, stdout, stderr = ssh.exec_command('hostname')
        hostname = stdout.read().decode('utf-8').strip()
        stdin2, stdout2, stderr2 = ssh.exec_command('cat /etc/os-release | grep PRETTY_NAME')
        os_info = stdout2.read().decode('utf-8').strip()
        print(f"SUCCESS! hostname={hostname}, {os_info}")
        
        # Start monitor in background
        print(f"\n=== Pi found at {ip}! Starting monitor... ===")
        
        # Kill old monitor
        ssh.exec_command('pkill -f monitor.py 2>/dev/null')
        import time; time.sleep(2)
        
        # Start fresh
        cmd = 'cd /home/pi/dustcheck && nohup python3 -u monitor.py > monitor_output.log 2>&1 & echo $!'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        pid = stdout.read().decode('utf-8').strip()
        print(f"  monitor.py started with PID: {pid}")
        time.sleep(8)
        
        # Check if running
        stdin, stdout, stderr = ssh.exec_command('ps aux | grep monitor.py | grep -v grep')
        ps = stdout.read().decode('utf-8').strip()
        if ps:
            print(f"  ✅ Running!")
        else:
            print(f"  ⚠️ Process not found, checking log...")
        
        # Show log
        stdin, stdout, stderr = ssh.exec_command('cat /home/pi/dustcheck/monitor_output.log 2>/dev/null | tail -25')
        log = stdout.read().decode('utf-8').strip()
        if log:
            print(f"\n--- Monitor Log ---")
            print(log)
        
        ssh.close()
        break
    except Exception as e:
        print(f"FAILED ({e})")
        ssh.close()
