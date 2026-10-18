@echo off
setlocal

cd /d %~dp0
set DESKTOP_DIR=%cd%
set ROOT_DIR=%DESKTOP_DIR%\..
set FRONTEND_DIR=%ROOT_DIR%\frontend

echo ===================================================
echo   SecureScan Desktop — build
echo ===================================================
echo.
echo Isso faz 3 coisas:
echo   1. Builda o frontend como site estatico (next export)
echo   2. Instala as dependencias Python do modo desktop
echo   3. Empacota tudo num unico SecureScan.exe
echo.
echo Requisitos: Python 3.12+ e Node.js instalados.
echo.
pause

REM --- 1. Build do frontend (export estatico) ---
echo.
echo [1/3] Buildando o frontend...
cd /d "%FRONTEND_DIR%"

if not exist node_modules (
    echo Instalando dependencias do frontend pela primeira vez...
    call npm install --legacy-peer-deps
)

REM troca temporariamente para a config/env do desktop
copy /Y next.config.js next.config.js.bak >nul
copy /Y next.config.desktop.js next.config.js >nul
copy /Y .env.desktop .env.production.local >nul

call npm run build

REM restaura os arquivos originais, mesmo se o build falhar
copy /Y next.config.js.bak next.config.js >nul
del next.config.js.bak >nul
del .env.production.local >nul

if not exist out (
    echo.
    echo ERRO: a pasta "out" nao foi gerada. O "next build" falhou — veja o
    echo erro acima. Build interrompido.
    pause
    exit /b 1
)

echo Copiando o site estatico para desktop\frontend_static ...
if exist "%DESKTOP_DIR%\frontend_static" rmdir /s /q "%DESKTOP_DIR%\frontend_static"
xcopy /E /I /Y out "%DESKTOP_DIR%\frontend_static" >nul

cd /d "%DESKTOP_DIR%"

REM --- 2. Dependencias Python ---
echo.
echo [2/3] Instalando dependencias Python do modo desktop...
if not exist "%ROOT_DIR%\.venv" (
    python -m venv "%ROOT_DIR%\.venv"
)
call "%ROOT_DIR%\.venv\Scripts\activate.bat"
pip install -r requirements-desktop.txt
pip install -e "%ROOT_DIR%\scanner-engine"

REM --- 3. Empacotar em .exe ---
echo.
echo [3/3] Empacotando em SecureScan.exe (isso demora alguns minutos)...

pyinstaller --noconfirm --onedir --windowed --name SecureScan ^
    --paths "%ROOT_DIR%\backend" ^
    --paths "%ROOT_DIR%\scanner-engine" ^
    --add-data "%ROOT_DIR%\VERSION.json;." ^
    --add-data "%ROOT_DIR%\backend;backend" ^
    --add-data "%ROOT_DIR%\scanner-engine\scanner_engine;scanner_engine" ^
    --add-data "frontend_static;desktop\frontend_static" ^
    --collect-all passlib ^
    --collect-all slowapi ^
    --collect-all uvicorn ^
    --collect-all reportlab ^
    --collect-all zapv2 ^
    --collect-submodules app ^
    --collect-submodules scanner_engine ^
    --hidden-import=app.main ^
    --hidden-import=bcrypt ^
    --hidden-import=email_validator ^
    --hidden-import=multipart ^
    --hidden-import=python_multipart ^
    main.py


if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    echo.
    echo [4/4] Gerando o instalador SecureScan_Setup.exe ...
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss
)

echo.
echo ===================================================
echo   Pronto!
echo   Executavel: %DESKTOP_DIR%\dist\SecureScan\SecureScan.exe
echo   Instalador: %DESKTOP_DIR%\installer\SecureScan_Setup.exe
echo ===================================================
pause


