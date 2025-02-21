#! /bin/bash

#Остановка скрипта при вознкиновение ошибки
set -e

USER_NAME="sshuser"
NEW_PASSWORD="P@ssw0rd"

device_name=""
DOMAIN=".au.team"

function check_sudo { 
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите скрипт от root!" >&2
        exit 1
    fi
}

echo_header() {
BLUE='\033[0;34m'
NC='\033[0m' # No Color
echo -e "${BLUE}$1${NC}"
}

echo_subheader() {
CYAN='\033[0;36m'
NC='\033[0m' # No Color
echo -e "${CYAN}$1${NC}"
}

function show_select_device_message {
    echo_header $'\n\n#>===================== Выберите устройство =====================<#\n'


    echo_subheader "   1. SW1-HQ"
    echo_subheader "   2. SW2-HQ"
    echo_subheader "   3. SW3-HQ"
    echo_subheader "   3. ADMIN-HQ"
    echo_subheader "   3. SRV1-HQ"
    echo_subheader "   0. exit"


    echo_header $'\n#>=====================================================================<#\n'
}

function input_handler {
    show_select_device_message
    local choice
    read choice
    
    case "$choice" in 

        "1")
            device_name="sw1-hq"
            ;;

        "2")
            device_name="sw2-hq"
            ;;

        "3")
            device_name="sw3-hq"
            ;;

        "4")
            device_name="admin-hq"
            ;;

        "5")
            device_name="srv1-hq"
            ;;

        "0")
            exit 0
            ;;

    esac
}



function check_device_name_on_null {
    #Если строка пустая
    if [[ -z $device_name ]]; then
        return 1
    fi
}

function set_hostname {
    hostnamectl set-hostname "${device_name}"${DOMAIN};
    if [[ $? -ne 0 ]]; then
        echo "Ошибка установки hostname!" >&2
        return 1
    fi
}

function create_user {
    
    if id "$USER_NAME" &>/dev/null; then
        userdel -r $USER_NAME || return 1
    fi
    useradd $USER_NAME -m -U -s /bin/bash || return 1
}

function set_password {
    echo $USER_NAME:$NEW_PASSWORD | chpasswd || return 1
}

function set_admin_role {
    #Нужна проверка, если запись существует
    usermod -aG wheel $USER_NAME || return 1
    echo -e "$USER_NAME ALL=(ALL) NOPASSWD: ALL" | EDITOR="tee -a" visudo >/dev/null || return 1
}


function main_add_user {
    check_sudo
    set_hostname && echo "Hostname установлен!" || echo "Ошибка установки hostname"
    create_user && echo "Пользователь создан!" || echo "Ошибка создания пользователя"
    set_password && echo "Пароль установлен!" || echo "Ошибка установки пароля"
    set_admin_role && echo "Права админа добавлены!" || echo "Ошибка настройки прав"
}

while [[ -z "${device_name}" ]]
do
    input_handler
done
main_add_user

#sudo userdel -r username