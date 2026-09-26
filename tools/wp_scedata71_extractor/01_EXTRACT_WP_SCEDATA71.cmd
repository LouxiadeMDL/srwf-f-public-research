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
if not errorlevel 1 goto use_py
where python >nul 2>nul
if not errorlevel 1 goto use_python
echo [ERROR] Python 3 was not found.
set RC=9009
goto done

:use_py
if "%~1"=="" goto use_py_noarg
py -3 "%~dp0extract_wp_scedata71.py" %*
set RC=%errorlevel%
goto done

:use_py_noarg
py -3 "%~dp0extract_wp_scedata71.py"
set RC=%errorlevel%
goto done

:use_python
if "%~1"=="" goto use_python_noarg
python "%~dp0extract_wp_scedata71.py" %*
set RC=%errorlevel%
goto done

:use_python_noarg
python "%~dp0extract_wp_scedata71.py"
set RC=%errorlevel%

:done
echo.
echo Exit code: %RC%
pause
exit /b %RC%
