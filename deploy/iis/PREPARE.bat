@echo off
cd /d "%~dp0..\.."
echo Preparing IIS hosting...
powershell -ExecutionPolicy Bypass -File "%~dp0prepare_iis.ps1" -VirtualPath /cms
pause
