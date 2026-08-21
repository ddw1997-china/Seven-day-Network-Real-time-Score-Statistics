@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

:: 读取提交消息文件（UTF-8）
if "%~1"=="" (
    echo 用法: git_commit.bat "提交消息"
    exit /b 1
)

:: 写入临时文件
echo %* > "%TEMP%\git_commit_msg.txt"

:: 使用 Python 执行提交（避免中文乱码）
python -c "
import subprocess
import os
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'
with open(r'%TEMP%\git_commit_msg.txt', 'r', encoding='utf-8') as f:
    msg = f.read().strip()
with open(r'%TEMP%\git_commit_msg.txt', 'w', encoding='utf-8') as f:
    f.write(msg)
subprocess.run(['git', 'commit', '-F', r'%TEMP%\git_commit_msg.txt'], env=env)
"

:: 清理临时文件
del "%TEMP%\git_commit_msg.txt"