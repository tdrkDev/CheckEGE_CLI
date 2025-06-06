# CheckEGE CLI

![CheckEGE running in iTerm](https://github.com/tdrkDev/CheckEGE_CLI/blob/master/images/sample.png?raw=true)

Have you ever wanted to check your exams' results directly from your terminal?
No worries! This thing exists only for people like you.

## Usage

To login and check your results:
```
./main.py
```

To clean up saved cookies and login data:
```
./main.py --clean
```

P.S. Saved data is located in ~/.checkege on POSIX systems, in %APPDATA%/checkege on Windows.

## Installation
```
git clone https://github.com/tdrkDev/CheckEGE_CLI.git
cd checkege_cli
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Issues?

I've tested the script only with Python 3.13 on macOS. Feel free to create a detailed issue.

## Improvements?

Pull requests are welcome!
