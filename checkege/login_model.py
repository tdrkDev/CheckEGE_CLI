import hashlib
import aiohttp

class LoginData:
    def __init__(self, name: str, surname: str, patronymic: str, passnum: str, region: int):
        self.name = name.strip()
        self.surname = surname.strip()
        self.patronymic = patronymic.strip()
        self.passnum = passnum.strip()
        self.region = region

    def __simplifyName(self):
        # Replacement of "transform-fio.js"
        return (self.surname + self.name + self.patronymic).lower().replace("ё", "е").replace("й", "и")

    def __transformPassnum(self):
        length = 12
        count = len(self.passnum)
        prefix = '0' * (length - count)
        return prefix + self.passnum
    
    def setCaptcha(self, token, code):
        self.captcha_token = token
        self.captcha_code = code

    def json(self):
        if self.captcha_code is None or self.captcha_token is None:
            raise ValueError("Captcha code and token must be set before generating JSON.")

        return {
            "Hash": hashlib.md5(self.__simplifyName().encode('utf-8')).hexdigest(),
            "Code": "",
            "Document": self.__transformPassnum(),
            "Region": str(self.region),
            "AgereeCheck": "on",
            "Captcha": str(self.captcha_code),
            "Token": self.captcha_token,
            "reCaptureToken": str(self.captcha_code),
        }
    
    def form(self):
        return aiohttp.FormData(self.json(), charset='utf-8')