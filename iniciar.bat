@echo off
title SecureScan
cd /d %~dp0

echo ===================================================
echo   Verificando se o Docker Desktop esta rodando...
echo ===================================================
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo O Docker Desktop nao esta aberto ou ainda nao terminou de iniciar.
    echo Abra o Docker Desktop, espere o icone da baleia ficar parado
    echo na bandeja do sistema, e rode este arquivo de novo.
    echo.
    pause
    exit /b 1
)

echo Docker Desktop OK.
echo.

cd docker

echo ===================================================
echo   Subindo o SecureScan (primeira vez pode demorar
echo   varios minutos, baixando imagens e instalando tudo)
echo ===================================================
echo.

REM abre o navegador automaticamente depois de um tempo, em paralelo
start "" cmd /c "timeout /t 30 /nobreak >nul && start http://localhost:3001"

docker compose up --build

pause
