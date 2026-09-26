@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo WP/YZZL F - SCEDATA[71] READ-ONLY EXTRACTOR
echo ================================================================
echo.
echo Double-click this file and choose SRWF.BIN / CUE / SCEDATA.BIN
echo or drag that file onto this CMD.
echo.
echo Source ROM/BIN will NOT be modified.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    if "%~1"=="" (
        py -3 "%~dp0extract_wp_scedata71.py"
    ) else (
        py -3 "%~dp0extract_wp_scedata71.py" %*
    )
    set RC=%errorlevel%
    goto done
)

where python >nul 2>nul
if %errorlevel%==0 (
    if "%~1"=="" (
        python "%~dp0extract_wp_scedata71.py"
    ) else (
        python "%~dp0extract_wp_scedata71.py" %*
    )
    set RC=%errorlevel%
    goto done
)

echo [ERROR] Python 3 was not found.
set RC=9009

:done
echo.
echo Exit code: %RC%
pause
exit /b %RC%
