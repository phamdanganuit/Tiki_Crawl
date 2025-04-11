@echo off
echo ==================================================
echo =     Khoi dong cong cu thu thap du lieu        =
echo ==================================================
echo.

REM Kiem tra Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Khong tim thay Python! Vui long cai dat Python va thu lai.
    pause
    exit /b
)

REM Chay chuong trinh
echo Dang khoi dong chuong trinh...
python src\auto_setup_and_run.py

echo.
if %ERRORLEVEL% NEQ 0 (
    echo Co loi xay ra khi chay chuong trinh.
    pause
)

exit /b