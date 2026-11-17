@echo off
setlocal enabledelayedexpansion
rem Abre JMeter en modo grafico pasando la contrasena de la BD desde .env
rem Uso: doble clic o  jmeter\scripts\abrir-jmeter.cmd

set "ROOT=%~dp0..\.."
set "DBPASS="

for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%\.env") do (
    if /i "%%A"=="DB_PASSWORD" set "DBPASS=%%B"
)
if "%DBPASS%"=="" set "DBPASS=sa"

set "JMETER_HOME=%USERPROFILE%\apache-jmeter-5.6.3"
if not exist "%JMETER_HOME%\bin\jmeter.bat" (
    echo No se encontro JMeter en "%JMETER_HOME%"
    pause
    exit /b 1
)

start "JMeter" "%JMETER_HOME%\bin\jmeter.bat" -Jdb.password=%DBPASS%
endlocal
