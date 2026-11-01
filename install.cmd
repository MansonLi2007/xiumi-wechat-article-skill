@echo off
rem 双击安装 xiumi-wechat-article 技能（装到 %USERPROFILE%\.dsh\skills）
rem 想装到当前项目：install.cmd project
setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1" %*
echo.
pause
