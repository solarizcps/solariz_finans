@echo off
cd /d C:\finans

:START
py finans_server.py

echo Finans kapandi. 120 saniye sonra tekrar aciliyor...
timeout /t 120

goto START