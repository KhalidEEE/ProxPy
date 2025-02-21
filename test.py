import fileinput


options_path = "/etc/bind/options.conf"



with fileinput.FileInput(options_path, inplace=True) as file:
    for line in file:
        if file.lineno() == 16:
            new_line = "listen-on { 127.0.0.1; 192.168.11.66; };"
            print(new_line, end="")
        elif file.lineno() == 17:
            new_line = "listen-on-v6 { any; };"
            print(new_line, end="")
        elif file.lineno() == 24:
            new_line = "forwarders { 77.88.8.8; };"
            print(new_line, end="")
        elif file.lineno() == 29:
            new_line = "allow-query { 192.168.11.0/24; 192.168.33.0/24; };"
            print(new_line, end="")
        elif file.lineno() == 30:
            new_line = "allow-transfer { 192.168.33.66; };"
            print(new_line, end="")
        else:
            print(line, end="")