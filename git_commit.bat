@echo off
rem ============================================
rem  git_commit.bat — 一键提交并推送（防中文乱码）
rem  用法:  git_commit.bat
rem         git_commit.bat "提交消息"
rem ============================================
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

python "%~dp0git_commit.py" %*

if errorlevel 1 (
    echo.
    echo 操作未完成，请查看上方错误信息。
)
pause
