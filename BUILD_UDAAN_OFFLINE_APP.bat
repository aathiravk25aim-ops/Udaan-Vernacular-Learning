@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo   UDAAN - Build Windows Offline Desktop App
echo ===============================================
echo This first build needs internet to download packaging dependencies.
echo After building, normal use of the packaged core app is offline.
echo.
powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0BUILD_UDAAN_OFFLINE_APP.ps1"
