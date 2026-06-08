@echo off
chcp 65001 >nul
echo ================================================
echo   Solariz Finans Sunucu - Kurulum ve Baslatma
echo ================================================
echo.

set KLASOR=D:\Firma_Ozel\adem\solariz finans
set PYTHON=python
set SUNUCU=%KLASOR%\finans_server.py
set TASK_XML=%KLASOR%\FinansServer_Task.xml
set TASK_ADI=FinansServer5058

:: Python kontrolu
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    pause
    exit /b 1
)

:: Gerekli paketler
echo [1/3] Gerekli Python paketleri kontrol ediliyor...
%PYTHON% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask yukleniyor...
    %PYTHON% -m pip install flask flask-cors
)

:: Task Scheduler kaydi
echo [2/3] Task Scheduler'a ekleniyor...
schtasks /query /tn "%TASK_ADI%" >nul 2>&1
if errorlevel 1 (
    schtasks /create /xml "%TASK_XML%" /tn "%TASK_ADI%" /f
    echo Task Scheduler'a eklendi: %TASK_ADI%
) else (
    echo Task zaten kayitli: %TASK_ADI%
)

:: Sunucuyu baslat
echo [3/3] Finans sunucu baslatiliyor (port 5058)...
schtasks /run /tn "%TASK_ADI%" >nul 2>&1

echo.
echo ================================================
echo   Tamamlandi!
echo   Adres: http://192.168.1.16:5058
echo ================================================
echo.
pause
