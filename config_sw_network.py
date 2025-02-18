import configparser
import fileinput
import subprocess
import tempfile
import os
import shutil

from utils import restart_network

IFACES_DIR = "/etc/net/ifaces/"
ENS18_NAME = "ens18"
ENP7S1_NAME = "enp7s1"
ENP7S2_NAME = "enp7s2"
ENP7S3_NAME = "enp7s3"
ENP7S4_NAME = "enp7s4"

device_name = ""
device_ip_address = ""
device_gateway = "192.168.11.81"

ip_address_dict = {
    "sw1-hq": "192.168.11.82/29",
    "sw2-hq": "192.168.11.83/29",
    "sw3-hq": "192.168.11.84/29"
}

def message() -> str:
    print("Выберите утсройство:\n1.SW1-HQ\n2.SW2-HQ\n3.SW3-HQ")
    inpt = input()
    if inpt == "1":
        return "sw1-hq"
    elif inpt == "2":
        return "sw2-hq"
    elif inpt == "3":
        return "sw3-hq"
    return ""


def conf_main_interface():
    backup_path = f"{IFACES_DIR}{ENS18_NAME}.bak"
    try:
        if not os.path.exists(f"{IFACES_DIR}{ENS18_NAME}"):
            raise FileNotFoundError

        shutil.copy(f"{IFACES_DIR}{ENS18_NAME}", backup_path)

        replaced = False
        with fileinput.FileInput(f"{IFACES_DIR}enp7s1/options", "w") as file:
            for line in file:
                if "BOOTPROTO=dhcp" in line:
                    new_line = line.replace("BOOTPROTO=dhcp", "BOOTPROTO=static")
                    print(new_line, end="")
                    replaced = True
                else:
                    print(line, end="")
        if not replaced:
            raise ValueError("Конфигурация файла ens18 неверная")

        os.rename(f"{IFACES_DIR}{ENS18_NAME}", f"{IFACES_DIR}{ENP7S1_NAME}")
        print("enp7s1 создан и настроен")
    except subprocess.CalledProcessError as e:
        print("Ошибка при создание enp7s1:", e.stderr)
        os.remove(f"{IFACES_DIR}{ENS18_NAME}")
        os.rename(backup_path, f"{IFACES_DIR}{ENS18_NAME}")

def create_additional_interfaces():
    created_resources = []
    try:
        os.makedirs(f"{IFACES_DIR}{ENP7S2_NAME}", exist_ok=True)
        options_path = os.path.join(IFACES_DIR, ENP7S2_NAME, "options")
        with open(options_path, "w") as enp7s2:
            enp7s2.write("TYPE=eth\nBOOTPROTO=static")
        created_resources.append(f"{IFACES_DIR}{ENP7S2_NAME}")

        if device_name == "sw2-hq":
            shutil.copy(f"{IFACES_DIR}{ENP7S2_NAME}", f"{IFACES_DIR}{ENP7S3_NAME}")
            shutil.copy(f"{IFACES_DIR}{ENP7S2_NAME}", f"{IFACES_DIR}{ENP7S4_NAME}")
            created_resources.append(f"{IFACES_DIR}{ENP7S3_NAME}")
            created_resources.append(f"{IFACES_DIR}{ENP7S4_NAME}")
        else:
            shutil.copy(f"{IFACES_DIR}{ENP7S2_NAME}", f"{IFACES_DIR}{ENP7S3_NAME}")
            created_resources.append(f"{IFACES_DIR}{ENP7S3_NAME}")
    except (OSError, IOError, shutil.Error) as e:
        print(f"Ошибка при создании интерфейсов: {str(e)}")
        rollback_created_resources(created_resources)

def rollback_created_resources(resources):
    for path in resources:
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"Ошибка при удаление: {path}", e)


def openvswitch_configuring():
    created_resources = []
    try:
        subprocess.run(["ovs-vsctl", "add-br", f"{device_name.upper()}"])
        if device_name == "sw1-hq":
            for interface_name in [ENP7S1_NAME, ENP7S2_NAME, ENP7S3_NAME]:
                subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{interface_name}", "trunk=110,220,330"], check=True)
        elif device_name == "sw2-hq":
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S1_NAME}", "trunk=110,220,330"], check=True)
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S2_NAME}", "trunk=110,220,330"], check=True)
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S3_NAME}", "tag=220"], check=True)
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S4_NAME}", "tag=110"], check=True)
        elif device_name == "sw3-hq":
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S1_NAME}", "trunk=110,220,330"], check=True)
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S2_NAME}", "trunk=110,220,330"], check=True)
            subprocess.run(["ovs-vsctl", "add-port", "SW1-HQ", f"{ENP7S3_NAME}", "tag=330"], check=True)
    except subprocess.CalledProcessError as e:
        print()
        subprocess.run(["ovs-vsctl", "del-port", "SW1-HQ"], check=True)

def mgmt_configuring():
    mgmt_path = "/etc/net/ifaces/MGMT"
    try:
        options_path = os.path.join(mgmt_path, "options")
        ipv4address_path = os.path.join(mgmt_path, "ipv4address")
        ipv4route_path = os.path.join(mgmt_path, "ipv4route")

        os.makedirs(mgmt_path)

        with open(options_path, "w") as mgmt:
            mgmt.write(f"TYPE=ovsport\nBOOTPROTO=static\nCONFIG_IPV4=yes\nBRIDGE={device_name.upper()}\nVID=330")
        with open(ipv4address_path, "w") as mgmt:
            mgmt.write(f"{device_ip_address}")
        with open(ipv4route_path, "w") as mgmt:
            mgmt.write(f"default via {device_gateway}")
    except (OSError, IOError) as e:
        print("Ошибка при настройке MGMT:", e.stderr)
        shutil.rmtree(mgmt_path)

def default_interface_configuring():
    default_interface_path = "/etc/net/ifaces/default"
    options_path = os.path.join(default_interface_path, "options")
    backup_path = f"{default_interface_path}.bak"
    try:
        if not os.path.exists(default_interface_path):
            raise FileNotFoundError

        shutil.copy(default_interface_path, backup_path)

        replaced = False
        with fileinput.FileInput(default_interface_path, "w") as file:
            for line in file:
                if "OVS_REMOVE=yes" in line:
                    new_line = line.replace("OVS_REMOVE=yes", "OVS_REMOVE=no")
                    print(new_line, end="")
                    replaced = True
                elif "OVS_REMOVE=no" in line:
                    replaced = True
                else:
                    print(line, end="")
        if not replaced:
            raise ValueError("Конфигурация файла default/options неверна")
    except Exception as e:
        print("Ошибка при настройке default интерфейса")
        shutil.rmtree(default_interface_path)
        os.rename(backup_path, default_interface_path)

def modprobe_configuring():
    module_path = "/etc/modules"
    backup_path = f"{module_path}.bak"
    try:
        subprocess.run(["modprobe", "8021q"], check=True)

        shutil.copy(module_path, backup_path)

        with open(module_path, "r+") as f:
            lines = f.readlines()
            if any(line.strip() == "8021q" for line in lines):
                print("Модуль уже настроен")
            else:
                f.write("8021q\n")
                print("Модуль добавлен")

    except Exception as e:
        print("Ошибка при настройке modprobe 8021q")
        shutil.rmtree(module_path)
        os.rename(backup_path, module_path)


def main():
    if not os.path.exists(ENS18_NAME):
        print("ens18 не найден")
        exit(1)
    device_name = message()
    device_ip = ip_address_dict[device_name]

    conf_main_interface()
    create_additional_interfaces()
    restart_network()
    openvswitch_configuring()
    mgmt_configuring()
    restart_network()
    default_interface_configuring()
    modprobe_configuring()
    restart_network()


