@echo off
setlocal EnableExtensions

cd /d "%~dp0"

title BankCreditLens - Local Dashboard

echo.
echo ============================================================
echo   BankCreditLens - Local Dashboard
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 1. Create local virtual environment if it does not exist
REM ------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Chua tim thay .venv. Dang tao moi truong Python...

    where py >nul 2>&1
    if %errorlevel%==0 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )

    if errorlevel 1 (
        echo.
        echo [LOI] Khong the tao moi truong Python.
        echo Hay kiem tra Python da duoc cai va them vao PATH.
        echo.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Da tim thay .venv.
)

REM ------------------------------------------------------------
REM 2. Install dashboard dependencies only when needed
REM ------------------------------------------------------------
echo [2/3] Dang kiem tra thu vien...

".venv\Scripts\python.exe" -c "import streamlit, plotly, pandas, openpyxl" >nul 2>&1

if errorlevel 1 (
    echo Dang cai cac thu vien can thiet...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r "dashboard\requirements.txt"

    if errorlevel 1 (
        echo.
        echo [LOI] Cai thu vien that bai.
        echo Thu chay thu cong:
        echo .venv\Scripts\python.exe -m pip install -r dashboard\requirements.txt
        echo.
        pause
        exit /b 1
    )
) else (
    echo Thu vien da san sang.
)

REM ------------------------------------------------------------
REM 3. Run Streamlit
REM ------------------------------------------------------------
echo [3/3] Dang khoi dong BankCreditLens...
echo.
echo Trinh duyet se mo tai: http://localhost:8501
echo Nhan Ctrl+C trong cua so nay de dung server.
echo.
".venv\Scripts\python.exe" -m streamlit run "dashboard\app.py"

if errorlevel 1 (
    echo.
    echo [LOI] Streamlit dung voi ma loi %errorlevel%.
    echo.
    pause
)

endlocal
