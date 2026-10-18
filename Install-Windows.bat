@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python mod.py install %*
) else (
  py -3 mod.py install %*
)
set RESULT=%ERRORLEVEL%
echo.
pause
exit /b %RESULT%
