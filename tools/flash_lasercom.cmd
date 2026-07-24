@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0flash_lasercom.ps1" %*
exit /b %ERRORLEVEL%
