@echo off
REM Install uv if not already installed
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

REM Create virtual environment with Python 3.12
uv venv --python 3.12

REM Activate the virtual environment
call .venv\Scripts\activate

REM Install dependencies
uv pip install -r requirements.txt
