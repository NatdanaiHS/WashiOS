@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0flash_payload_responder.ps1" %*
exit /b %ERRORLEVEL%
