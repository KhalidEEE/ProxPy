import subprocess
import os

# Проверка на sudo
def running_as_root() -> bool:
    return os.getuid() == 0

def restart_network():
    try:
        subprocess.run(["systemct", "restart", "network"], check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to restart network", e.stderr)