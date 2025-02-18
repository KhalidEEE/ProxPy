import subprocess
import tempfile
import os

from utils import running_as_root

# capture_output=True - позволяет передать ошибки в python
# text=True - вместо набора байт, будет string
# check=True заставляет генерировать исключение, если команда завершится с ошибкой

USER_NAME = "sshuser"
NEW_PASSWORD = "P@ssw0rd"
DOMAIN = ".au.team"

device_name = "SW1-HQ"

def _set_hostname():
    old_hostname = subprocess.run(["hostname"], capture_output=True, text=True).stdout
    try:
        subprocess.run(["hostnamectl", "set-hostname", f"{device_name}{DOMAIN}"], check=True)
        print("Hostname задан")
    except subprocess.CalledProcessError as e:
        print("Ошибка установки нового hostname:", e.stderr)
        subprocess.run(["hostnamectl", "set-hostname", f"{old_hostname}"], check=True)

def _create_user_and_configure():
    try:
        subprocess.run(["useradd", f"{USER_NAME}", "-m", "-U", "-s", "/bin/bash"], check=True)
        print("Пользователь создан")
        subprocess.run(["/usr/sbin/chpasswd"],
            text=True,
            input=f"{NEW_PASSWORD}:{NEW_PASSWORD}",
            check=True,
        )
        print("Пароль задан")
    except subprocess.CalledProcessError as e:
        print("Ошибка создания пользователя:", e.stderr)
        subprocess.run(["userdel", "-r", f"{USER_NAME}"])

def _set_admin_role():
    # Create file and check syntax command
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write(f"{USER_NAME} ALL=(ALL) NOPASSWD: ALL\n")
        tmp_filename = tmp.name
    try:
        subprocess.run(["usermod", "-aG", "wheel", f"{USER_NAME}"], check=True)

        called = subprocess.run(["visudo", "-c", "-f", tmp_filename],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        dest = f"/etc/sudoers.d/{USER_NAME}"
        subprocess.run(["cp", tmp_filename, dest], check=True)
        print("Правило добавлено")
    except subprocess.CalledProcessError as e:
        print("Ошибка при добавление роли:", e.stderr)
    finally:
        os.unlink(tmp_filename)

def main():
    if not running_as_root(): exit(1)
    _set_hostname()
    _create_user_and_configure()
    _set_admin_role()