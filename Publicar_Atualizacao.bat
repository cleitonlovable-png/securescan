@echo off
setlocal

cd /d %~dp0
set ROOT_DIR=%cd%
set DESKTOP_DIR=%ROOT_DIR%\desktop
set FRONTEND_DIR=%ROOT_DIR%\frontend

echo ===================================================
echo   SecureScan — Publicador de Atualizacao Completa
echo ===================================================
echo.
set /p NEW_VER="Digite a nova versao (ex: 1.2.0): "
set /p NOTES="Digite o resumo do que mudou: "

if "%NEW_VER%"=="" (
    echo Versao invalida. Cancelando.
    pause
    exit /b 1
)

REM 1. Atualiza VERSION.json
echo { "version": "%NEW_VER%", "release_date": "%DATE%", "notes": "%NOTES%" } > "%ROOT_DIR%\VERSION.json"

REM 2. Build do frontend estatico
echo.
echo [1/5] Compilando frontend Next.js...
cd /d "%FRONTEND_DIR%"
copy /Y next.config.js next.config.js.bak >nul
copy /Y next.config.desktop.js next.config.js >nul
copy /Y .env.desktop .env.production.local >nul
call npm run build
copy /Y next.config.js.bak next.config.js >nul
del next.config.js.bak >nul
del .env.production.local >nul

if exist "%DESKTOP_DIR%\frontend_static" rmdir /s /q "%DESKTOP_DIR%\frontend_static"
xcopy /E /I /Y out "%DESKTOP_DIR%\frontend_static" >nul
copy /Y "%ROOT_DIR%\VERSION.json" "%DESKTOP_DIR%\frontend_static\version.json" >nul

REM 3. Empacota o .exe com PyInstaller
echo.
echo [2/5] Gerando SecureScan.exe (PyInstaller)...
cd /d "%DESKTOP_DIR%"
call "%ROOT_DIR%\.venv\Scripts\activate.bat"
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
    --collect-submodules app ^
    --collect-submodules scanner_engine ^
    --hidden-import=app.main ^
    --hidden-import=bcrypt ^
    --hidden-import=email_validator ^
    --hidden-import=multipart ^
    --hidden-import=python_multipart ^
    main.py

REM 4. Gera o instalador SecureScan_Setup.exe com Inno Setup
echo.
echo [3/5] Compilando instalador SecureScan_Setup.exe (v%NEW_VER%)...
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" /DMyAppVersion="%NEW_VER%" installer.iss

REM 5. Commit, Push, GitHub Release (com o .exe anexado) e Cloudflare Pages
echo.
echo [4/5] Enviando codigo e criando Release v%NEW_VER% no GitHub...
cd /d "%ROOT_DIR%"
git add .
git commit -m "release: v%NEW_VER% - %NOTES%"
git push origin master
gh release create "v%NEW_VER%" "%DESKTOP_DIR%\installer\SecureScan_Setup.exe" --title "SecureScan v%NEW_VER%" --notes "%NOTES%"

echo.
echo [5/5] Atualizando dominio Cloudflare Pages (securescan.pages.dev)...
call wrangler pages deploy "%DESKTOP_DIR%\frontend_static" --project-name securescan --branch master --commit-dirty=true

echo.
echo ===================================================
echo   Atualizacao v%NEW_VER% publicada com sucesso!
echo   Todos os usuarios receberao o aviso no app!
echo ===================================================
pause
