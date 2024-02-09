from datetime import datetime
import paramiko
from scp import SCPClient
import argparse

def parse_args():
    arg = argparse.ArgumentParser()
    arg.add_argument("-r", "--remote",    type=str, help="Адрес удаленного стенда",                           default=None)
    arg.add_argument("-P", "--port",      type=int, help="Порт удаленного стенда",                            default=22)
    arg.add_argument("-u", "--user",      type=str, help="Имя пользователя на удаленном стенде",              default="user")
    arg.add_argument("-p", "--password",  type=str, help="Пароль пользователя на удаленном стенде",           default="")
    arg.add_argument("--path",            type=str, help="Путь к файлам которые нужно скопировать",           default="/")
    arg.add_argument("--dest",            type=str, help="Путь куда файлы нужно скопировать",                 default="/tmp")
    arg.add_argument("-R", "--regexp",    type=str, help="Регулярное выражение для выбора копируемых файлов", default="*.*")
    arg.add_argument("-b", "--datebegin", type=str, help="Дата начала интересующего временного интервала",    default=None)
    arg.add_argument("-e", "--dateend",   type=str, help="Дата конца интересующего временного интервала",     default=None)
    return arg.parse_args()

def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def ssh_connect(args):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=args.remote, port=args.port, username=args.user, password=args.password,
                timeout=3, allow_agent=False, look_for_keys=False)
    return ssh

def main():
    """Основная функция"""
    print("Утилита скачивания файлов")

    """Обработка аргументов командной строки"""
    args = parse_args()
    if args.remote is None:
        print("Не опредлен адрес удаленного подключения. Укажите корректный адрес.")
        return 1

    if not validate_ip(args.remote):
        print("Адрес удаленного подключения введен некорректно. Укажите корректный адрес.")


    dBegin, dEnd = None, None

    if not (args.datebegin is None):
        dBegin = datetime.strptime(args.datebegin, '%Y.%m.%d')
    if not (args.dateend is None):
        dEnd   = datetime.strptime(args.dateend, '%Y.%m.%d')

    print(f"Параметры подключения: Адрес - {args.remote}, порт - {args.port}, пользователь - {args.user}")
    if (dBegin is None) and (dEnd is None):
        print(f"Копирование файлов {args.path + args.regexp}")
    else:
        if (not (dBegin is None)) and (dEnd is None):
            print(f"Копирование файлов {args.path + args.regexp} не старше {dBegin}")
        elif (dBegin is None) and (not (dEnd is None)):
            print(f"Копирование файлов {args.path + args.regexp} не новее {dEnd}")
        else:
            print(f"Копирование файлов {args.path + args.regexp} за период с {dBegin} по {dEnd}")

    """Создание SSH-подключения"""
    client = ssh_connect(args)

    """Поиск подходящих файлов"""
    command  = f"echo Searching for files &&"
    command += f"cd {args.path} &&"
    command += f"pwd &&"
    command += f'find -newerct "{dBegin.year}-{dBegin.month}-{dBegin.day}  00:00:00" ! -newerct "{dEnd.year}-{dEnd.month}-{dEnd.day} 23:59:59" -type f | wc -l &&'
    command += f"echo ' Files: ' &&"
    command += f'find -newerct "{dBegin.year}-{dBegin.month}-{dBegin.day}  00:00:00" ! -newerct "{dEnd.year}-{dEnd.month}-{dEnd.day} 23:59:59" -type f'
    (stdin, stdout, stderr) = client.exec_command(command)

    cmd_output = (str(stdout.read())[2:-3].replace(r'\n', ', ').replace('./', '\n')
                  .replace('Files: ,', '\nFiles: '))
    out = cmd_output.split('Files:')

    if False:
        print('VERBOSE: ', cmd_output)
    else:
        print((out[0])[0:-4]," files found")

    files_list = out[1].replace('\n', '').replace(' ', '').split(',')

    if False:
        print(files_list)

    clientScp = SCPClient(client.get_transport())
    for fName in files_list:
        print(f"Copying {args.path+fName} ---> {args.dest + '/'}")
        clientScp.get(remote_path=args.path + '/' + fName, local_path=args.dest + '/' )

    """Разрыв SSH-подключения"""
    client.close()

    return 0

if __name__ == "__main__":
    main()