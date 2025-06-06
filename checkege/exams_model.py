from . import cli as c

SCOPE_BASIC_MATH = 1
SCOPE_COMPOSITION = 2
SCOPE_FOREIGN_LANGUAGE = 3

COLOR_SYSTEM = c.GRAY
COLOR_BAD = c.RED # mark100 < min100
COLOR_ACCEPTABLE = c.YELLOW # min100 <= mark100 < 60
COLOR_GOOD = c.BLUE # 60 <= mark100 < 75
COLOR_GREAT = c.GREEN # 75 <= mark100

class ExamMark:
    def __init__(self, mark5: int, mark100: int, min100: int, scope: int = 0):
        self.mark5 = mark5
        self.min100 = min100
        self.mark100 = mark100
        self.scope = scope

    def __str__(self):
        completion = "прошел" if self.completion else "не прошел"
        if self.scope == SCOPE_BASIC_MATH:
            return f"{completion} ({self.mark5} / 3)"
        elif self.scope == SCOPE_COMPOSITION:
            return completion
        else:
            return f"{completion} ({self.mark100} / {self.min100})"
    
    @property
    def display(self):
        return str(self)
    
    @property
    def color(self) -> str:
        if self.scope == SCOPE_COMPOSITION:
            return COLOR_GREAT if self.mark5 == 5 else COLOR_BAD
        elif self.scope == SCOPE_BASIC_MATH:
            if self.mark5 < 3:
                return COLOR_BAD
            elif self.mark5 == 3:
                return COLOR_ACCEPTABLE
            elif self.mark5 == 4:
                return COLOR_GOOD
            elif self.mark5 >= 5:
                return COLOR_GREAT
        else:
            if self.mark100 < self.min100:
                return COLOR_BAD
            elif self.mark100 < 60:
                return COLOR_ACCEPTABLE
            elif self.mark100 < 75:
                return COLOR_GOOD
            else:
                return COLOR_GREAT
        
    @property
    def completion(self):
        if self.scope == SCOPE_COMPOSITION:
            return self.mark5 == 5
        elif self.scope == SCOPE_BASIC_MATH:
            return self.mark5 >= 3
        else:
            return self.mark100 >= self.min100

class ExamStatus:
    def __init__(self, data: dict, is_oral: bool = False):
        self.data = data
        self.prefix = "Oral" if is_oral else ""

    def __getitem__(self, item):
        return self.data.get(item)
    
    def __get(self, item):
        return self.__getitem__(self.prefix + item)
    
    @property
    def __has_results(self):
        return self["Has" + self.prefix + "Result"] == True
    
    @property
    def id(self):
        return self.__get("ExamId")
    
    @property
    def date(self):
        return self.__get("ExamDate")
    
    @property
    def subject(self):
        return self.__get("Subject")
    
    @property
    def int_status(self):
        return self.__get("Status")
    
    @property
    def mark(self):
        if self.__has_results:
            scope = 0
            if self.__get("IsBasicMath"): scope = SCOPE_BASIC_MATH
            if self.__get("IsComposition"): scope = SCOPE_COMPOSITION
            if self.__get("IsForeignLanguage"): scope = SCOPE_FOREIGN_LANGUAGE
            return ExamMark(self["Mark5"], self["TestMark"], self["MinMark"], scope)
        return None

    @property
    def display_status(self):
        status_map = {
            0: "Сформировано заявление участником",
            1: "Сформировано заявление оператором",
            2: "Отменена участником",
            3: "Отменена оператором",
            4: "Апелляция открыта участником заново",
            5: "Апелляция открыта оператором заново",
            10: "Сформировано заявление в РЦОИ",
            11: "Распечатаны бланки",
            12: "Введены данные",
            20: "На обработке",
            30: "Ожидание подтверждения",
            32: "Введено подтверждение",
            40: "Подтверждение на обработке",
            52: "Создано блокирование",
            60: "Блокирование на обработке",
            100: "Удовлетворена",
            101: "Отклонена конфликтной комиссией субъекта РФ",
            103: "Заблокирована",
            1000: "Задержана"
        }
        return status_map.get(self.int_status, ("Имеются результаты" if self.__has_results else str(self.int_status)))
    
    @property
    def display_status_color(self) -> str:
        status_map = {
            0: COLOR_SYSTEM,
            1: COLOR_SYSTEM,
            2: COLOR_BAD,
            3: COLOR_BAD,
            4: COLOR_ACCEPTABLE,
            5: COLOR_ACCEPTABLE,
            10: COLOR_ACCEPTABLE,
            11: COLOR_SYSTEM,
            12: COLOR_SYSTEM,
            20: COLOR_ACCEPTABLE,
            30: COLOR_ACCEPTABLE,
            32: COLOR_ACCEPTABLE,
            40: COLOR_ACCEPTABLE,
            52: COLOR_BAD,
            60: COLOR_BAD,
            100: COLOR_ACCEPTABLE,
            101: COLOR_BAD,
            103: COLOR_BAD,
            1000: COLOR_BAD,
        }
        return status_map.get(self.int_status, (COLOR_GREAT if self.__has_results else COLOR_SYSTEM))
    
    @property
    def is_oral(self):
        return len(self.prefix) > 0

    @property
    def exam_type(self):
        return "устный" if self.is_oral else "письменный"    
