@echo off
:: Right-click -> Run as administrator
cd /d "%~dp0..\.."
powershell -ExecutionPolicy Bypass -File "%~dp0configure_iis_admin.ps1"
if errorlevel 1 pause
