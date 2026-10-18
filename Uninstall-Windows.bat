@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python mod.py uninstall %*
) else (
  py -3 mod.py uninstall %*
)
set RESULT=%ERRORLEVEL%
echo.
pause
exit /b %RESULT%
