@echo off
title SecureScan - Parar
cd /d %~dp0\docker

echo Parando o SecureScan...
docker compose down

echo.
echo Containers parados. Os dados do banco continuam salvos.
pause
