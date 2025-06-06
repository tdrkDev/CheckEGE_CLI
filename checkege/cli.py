RESET_COLOR = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
GRAY = "\033[90m"

from . import client, captcha_gui, regions, login_model
import os
from getpass import getpass
import sys
import traceback
import hashlib
import base64
import json
from cryptography.fernet import Fernet

if os.name == "nt":
    from pyreadline3 import Readline
else:
    try:
        import gnureadline as _readline
    except ImportError:
        import readline as _readline

class Completer:
    def __init__(self, regions: dict[int, str], readline, line: str):
        self.regions = regions
        self.reg = sorted(regions.values())
        self.readline = readline
        self.line = line

    def complete(self, text, state):
        if text.isnumeric():
            if state != 0: return None
            return self.regions.get(int(text), None)
        
        if state == 0:
            if not text:
                self.matches = self.reg[:]
            else:
                self.matches = [r for r in self.reg if text.lower() in r.lower()]
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def display_matches(self, substitution, matches, longest_match_length):
        buf = self.readline.get_line_buffer()
        columns = os.get_terminal_size().columns
        itemsize = longest_match_length + 10
        items_per_line = columns // (itemsize)

        print()
        for i in range(0, len(matches), items_per_line):
            count = min(items_per_line, len(matches) - i)
            for j in range(count):
                print(f"{matches[i + j]:<{itemsize}}", end="")
            print()
    
        print(self.line, end="")
        print(buf, end="")
        sys.stdout.flush()

class Cli:
    def __init__(self):
        self.client = client.CheckegeClient()
        self.captcha_gui = captcha_gui.CaptchaGUI()
        self.regions = None
        self.name = None
        self.surname = None
        self.patronymic = None
        self.passnum = None
        self.region = None

    def __cfg_path(self):
        if os.getenv("CHECKEGE_CFG"):
            return os.getenv("CHECKEGE_CFG")
        
        path = "cookies.txt"
        if os.name == "nt":
            path = os.path.join(os.getenv("APPDATA"), "checkege", "config.json")
        elif os.name == "posix":
            path = os.path.join(os.getenv("HOME"), ".checkege", "config.json")

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
    
    def __get_fernet(self):
        if self.passnum is None:
            raise ValueError("Паспорт не установлен.")
        
        # a bit cursed but it works
        key = hashlib.sha256(self.passnum.encode('utf-8')).hexdigest().encode()
        fernet_key = base64.urlsafe_b64encode(hashlib.shake_256(key).digest(32))
        return Fernet(fernet_key)
    
    async def try_load_config(self):
        path = self.__cfg_path()
        if not os.path.exists(path): return

        self.print_important("Желаете ли вы загрузить сохранённые данные для входа?")
        choice = input(f"Введите {ITALIC}{YELLOW}Y{RESET_COLOR} для загрузки или {ITALIC}{YELLOW}N{RESET_COLOR} для ввода данных вручную: ").strip().lower()
        if choice not in ("y", "yes", "д", "да"):
            self.print_notice("Удаление сохраненной конфигурации.")
            os.remove(self.__cfg_path())
            return

        self.print_notice("Ваш паспорт - ваш пароль от сохраненных данных.")
        passnum = getpass(f"Введите {ITALIC}{RED}последние 6 цифр{RESET_COLOR} паспорта {GRAY}(данные скрыты){RESET_COLOR}: ").strip()
        if not passnum.isdigit() or len(passnum) != 6:
            self.print_error("Паспорт должен содержать 6 цифр.")
            return await self.try_load_config()

        self.passnum = passnum

        fernet = self.__get_fernet()
        
        try:
            with open(path, "r") as f:
                encrypted_data = f.read()
                data = fernet.decrypt(encrypted_data).decode('utf-8')
                config = json.loads(data)

                self.name = config.get("name")
                self.surname = config.get("surname")
                self.patronymic = config.get("patronymic")
                self.region = config.get("region")
        except Exception as e:
            self.print_error(f"Не удалось загрузить конфигурацию.")
            self.print_notice("Откат к вводу данных вручную.")
            return

    async def save_config(self):
        path = self.__cfg_path()
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)

        fernet = self.__get_fernet()

        config = {
            "name": self.name,
            "surname": self.surname,
            "patronymic": self.patronymic,
            "region": self.region
        }

        with open(path, "w") as f:
            encrypted_data = fernet.encrypt(json.dumps(config).encode('utf-8'))
            f.write(encrypted_data.decode('utf-8'))

        #self.print_success("Конфигурация успешно сохранена.")
    
    def print_error(self, message: str):
        print(f"{RED}{message}{RESET_COLOR}")

    def print_important(self, message: str):
        print(f"{ITALIC}{YELLOW}{message}{RESET_COLOR}")

    def print_notice(self, message: str):
        print(f"{BOLD}{GRAY}{message}{RESET_COLOR}")

    def print_success(self, message: str):
        print(f"{GREEN}{message}{RESET_COLOR}")

    async def login(self) -> bool:
        await self.try_load_config()

        if self.region == None:
            if self.regions == None:
                self.print_notice("Загружаю список регионов...")
                self.regions = await self.client.get_regions()
                #self.regions = regions.regions
                self.print_notice(f"Загружено {YELLOW}{len(self.regions)}{GRAY} регионов.")

            if os.name == "nt":
                readline = Readline()
            else:
                readline = _readline

            line = "Введите регион (исп. TAB): "
            compl = Completer(self.regions, readline, line)
            if os.name != "nt":
                readline.set_completion_display_matches_hook(compl.display_matches)

            readline.set_completer_delims('\t\n;')
            readline.set_completer(compl.complete)
            readline.parse_and_bind('tab: complete')
            region = input(line).strip()
            readline.set_completer(None)

            if not region:
                self.print_error("Регион не может быть пустым.")
                return await self.login()

            if region.isnumeric():
                region = int(region)
                if region not in self.regions:
                    self.print_error(f"Регион {RESET_COLOR}{YELLOW}{ITALIC}{region}{RESET_COLOR}{RED} не найден (поиск по №).")
                    return await self.login()
            elif region in self.regions.values():
                region = list(self.regions.keys())[list(self.regions.values()).index(region)]
            else:
                self.print_error(f"Регион {RESET_COLOR}{YELLOW}{ITALIC}\"{region}\"{RESET_COLOR}{RED} не найден (поиск по названию).")
                return await self.login()

            self.region = region

        if self.name is None:
            name = input("Введите имя: ").strip()
            if not name:
                self.print_error("Имя не может быть пустым.")
                return await self.login()
            
            self.name = name

        if self.surname is None:
            surname = input("Введите фамилию: ").strip()
            if not surname:
                self.print_error("Фамилия не может быть пустой.")
                return await self.login()
            
            self.surname = surname

        if self.patronymic is None:
            patronymic = input("Введите отчество: ").strip()
            if not patronymic:
                self.print_error("Отчество не может быть пустым.")
                return await self.login()
            
            self.patronymic = patronymic

        if self.passnum is None:
            passnum = getpass(f"Введите {ITALIC}{RED}последние 6 цифр{RESET_COLOR} паспорта {GRAY}(данные скрыты){RESET_COLOR}: ").strip()
            if not passnum.isdigit() or len(passnum) != 6:
                self.print_error("Паспорт должен содержать 6 цифр.")
                return await self.login()

            self.passnum = passnum

        await self.save_config()

        token, captcha_image = await self.client.get_captcha()
        if not token or not captcha_image:
            self.print_error("Не удалось получить капчу.")
            return False

        self.captcha_gui.set_captcha(captcha_image)
        captcha_code = self.captcha_gui.solve()

        if not captcha_code:
            return await self.login()

        data = login_model.LoginData(self.name, self.surname, self.patronymic, self.passnum, self.region)
        data.setCaptcha(token, captcha_code)
        await self.client.login(data)
        self.print_success("Успешный вход!")
        return True
    
    async def print_results(self) -> bool:
        if not self.client.is_logged_in:
            self.print_error("Необходимо войти в систему.")
            return False

        exams = await self.client.get_results()
        if not exams:
            self.print_notice("Нет доступных экзаменов.")
            return False

        self.print_notice("Результаты:")

        # at first, calculate the longest names
        longest_date = max(len(exam.date) for exam in exams)
        longest_subject = max(len(exam.subject) for exam in exams)
        longest_status = max(len(exam.display_status) for exam in exams)
        longest_mark = max(len(exam.mark.display) if exam.mark else len("Неизвестно") for exam in exams)
        longest_type = max(len(exam.exam_type) for exam in exams)
        has_oral = any(exam.is_oral for exam in exams)
        total_width = longest_date + longest_subject + longest_status + longest_mark + 13 + ((longest_type + 3) if has_oral else 0)
        
        LINETYPE_FIRST = 0
        LINETYPE_MIDDLE = 1
        LINETYPE_LAST = 2
        def print_line(type: int):
            print(GRAY)
            corner1 = "┏" if type == LINETYPE_FIRST else "┣" if type == LINETYPE_MIDDLE else "┗"
            corner2 = "┓" if type == LINETYPE_FIRST else "┫" if type == LINETYPE_MIDDLE else "┛"
            connector = "┳" if type == LINETYPE_FIRST else "╋" if type == LINETYPE_MIDDLE else "┻"

            print(corner1 , end="")
            print("━" * (longest_date + 2), end="")
            print(connector, end="")
            print("━" * (longest_subject + 2), end="")
            print(connector, end="")
            print("━" * (longest_status + 2), end="")
            print(connector, end="")
            print("━" * (longest_mark + 2), end="")
            if has_oral:
                print(connector, end="")
                print("━" * (longest_type + 2), end="")
            print(corner2, end="")
            print()
            print(RESET_COLOR, end='')
        
        print_line(LINETYPE_FIRST)
        for exam in exams:
            mark = exam.mark.display if exam.mark else "Неизвестно"
            mark_color = exam.mark.color if exam.mark else GRAY
            oral_status = "письменный" if not exam.is_oral else "устный"

            d = f"{GRAY} ┃ {RESET_COLOR}"


            print(f"{GRAY}┃{RESET_COLOR} {exam.date:<{longest_date}}{RESET_COLOR}{d}", end="")
            print(f"{ITALIC}{exam.subject:<{longest_subject}}{RESET_COLOR}{d}{exam.display_status_color}{exam.display_status:<{longest_status}}{RESET_COLOR}{d}{mark_color}{mark:<{longest_mark}}{RESET_COLOR}", end="")
            if has_oral:
                print(f"{d}{GRAY}{oral_status:<{longest_type}}{RESET_COLOR} {GRAY}┃{RESET_COLOR}", end="")
            else:
                print(f" {GRAY}┃{RESET_COLOR}", end="")

            print_line(LINETYPE_MIDDLE if exam != exams[-1] else LINETYPE_LAST)

        return True
        
    
    async def __run_safe(self) -> int:
        print(f"{BOLD}CheckEGE CLI {YELLOW}v1.0{RESET_COLOR}")

        if len(sys.argv) >= 2 and sys.argv[1] == "--clear":
            self.print_important("Очистка сохраненных данных...")
            if os.path.exists(self.__cfg_path()):
                os.remove(self.__cfg_path())
            self.client.clean()
            self.print_success("Успешно.")
            return 0


        if not self.client.is_logged_in:
            self.print_important("Требуется вход.")
            if not await self.login(): return 1

        if not await self.print_results() and not self.client.is_logged_in:
            self.print_error("Необходимо заново войти в систему.")
            if not await self.login(): return 1
            if not await self.print_results(): return 1
        return 0

    async def run(self) -> int:
        try:
            return await self.__run_safe()
        except Exception as e:
            traceback.print_exception(e)
            print(f"Ошибка: {e}")
            return 1
        finally:
            await self.client.stop()
