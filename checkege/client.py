import aiohttp
import os
import json
import base64
from .exams_model import ExamStatus
from .login_model import LoginData
from .regions import regions

class CheckegeClient:
    BASE_URL = f"https://checkege.rustest.ru/api/"

    def __init__(self):
        self.jar = aiohttp.CookieJar()
        self.client = aiohttp.ClientSession(
            self.BASE_URL,
            cookie_jar=self.jar
        )

        path = self.__jar_path()
        if os.path.exists(path):
            self.jar.load(path)

    def __jar_path(self):
        '''
        Returns the path to the cookie jar file.
        '''
        if os.getenv("CHECKEGE_JAR"):
            return os.getenv("CHECKEGE_JAR")
        
        path = "cookies.txt"
        if os.name == "nt":
            path = os.path.join(os.getenv("APPDATA"), "checkege", "cookies.txt")
        elif os.name == "posix":
            path = os.path.join(os.getenv("HOME"), ".checkege", "cookies.txt")

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
    
    @property
    def is_logged_in(self) -> bool:
        cookies = self.jar.filter_cookies(self.BASE_URL)
        return "Participant" in cookies

    async def get_regions(self) -> dict[int, str]:
        '''
        Get eligible regions
        '''

        url = f"region"
        async with self.client.get(url) as response:
            data = await response.json()
            return {key["Id"]: regions[key["Id"]] for key in data if key["Id"] in regions}
    
    async def get_captcha(self) -> tuple[str, bytes]:
        '''
        Get captcha image URL for login.
        Returns token and image bytes.
        '''

        url = f"captcha"
        async with self.client.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch captcha: {response.status}")
            elif response.status == 403:
                raise Exception("Captcha is required but not provided.")

            data = await response.json()
            return data.get("Token"), base64.b64decode(data.get("Image"))
    
    async def login(self, data: LoginData):
        '''
        Login to EGE portal with provided credentials.
        Returns True if login was successful, raises an exception otherwise.
        '''

        url = f"participant/login"
        async with self.client.post(url, data=data.form(), headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*",
            "Origin": "https://checkege.rustest.ru",
            "Referer": "https://checkege.rustest.ru/",
        }) as response:
            if response.status == 403:
                raise Exception("Invalid login credentials or captcha required.")
            elif response.status == 400:
                print("Data: ")
                print(str(data.form()._gen_form_urlencoded().decode()))
                print("Response: ")
                print(await response.text())
            elif response.status != 204 and response.status != 200:
                raise Exception(f"Login failed: {response.status}")

            self.jar.save(self.__jar_path())

    async def get_results(self) -> list[ExamStatus]:
        '''
        Get EGE results, requires login and valid cookies.
        '''

        if not self.is_logged_in:
            raise Exception("Not logged in or cookies were invalidated.")

        url = f"exam"
        results = []
        async with self.client.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch results: {response.status}")
            elif response.status == 400 or response.status == 403:
                self.jar.clear()
                self.jar.save(self.__jar_path())
                raise Exception("Cookies have expired")
        
            
            data = await response.json()
            for item in data.get("Result", []).get("Exams", []):
                has_oral_part = item.get("OralExamId") != None
                if has_oral_part:
                    oral_exam = ExamStatus(item, is_oral=True)
                    results.append(oral_exam)

                exam = ExamStatus(item)
                results.append(exam)
        
        return results
    
    def clean(self):
        self.jar.clear()
        self.jar.save(self.__jar_path())
    
    async def stop(self):
        await self.client.close()
        self.jar.save(self.__jar_path())
