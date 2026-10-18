@echo off
setlocal

cd /d %~dp0
set DESKTOP_DIR=%cd%
set ROOT_DIR=%DESKTOP_DIR%\..
set FRONTEND_DIR=%ROOT_DIR%\frontend

echo ===================================================
echo   SecureScan Desktop — modo de teste (sem empacotar)
echo ===================================================
echo.
echo Isso builda o frontend uma vez e roda o app direto com Python,
echo pra voce testar rapido antes de gerar o .exe final com build.bat.
echo.

if not exist frontend_static (
    echo Nenhum build do frontend encontrado — buildando agora...
    cd /d "%FRONTEND_DIR%"

    if not exist node_modules call npm install --legacy-peer-deps

    copy /Y next.config.js next.config.js.bak >nul
    copy /Y next.config.desktop.js next.config.js >nul
    copy /Y .env.desktop .env.production.local >nul

    call npm run build

    copy /Y next.config.js.bak next.config.js >nul
    del next.config.js.bak >nul
    del .env.production.local >nul

    xcopy /E /I /Y out "%DESKTOP_DIR%\frontend_static" >nul
    cd /d "%DESKTOP_DIR%"
)

if not exist "%ROOT_DIR%\.venv" (
    python -m venv "%ROOT_DIR%\.venv"
)
call "%ROOT_DIR%\.venv\Scripts\activate.bat"

echo Instalando dependencias Python (rapido se ja instalado antes)...
pip install -r requirements-desktop.txt -q
pip install -e "%ROOT_DIR%\scanner-engine" -q

echo.
echo Iniciando o SecureScan...
python main.py

