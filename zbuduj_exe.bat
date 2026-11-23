@echo off
rem Buduje samodzielny plik dist\ElectroMan.exe (nie wymaga Pythona na docelowym komputerze).
rem 32-bitowy Python da 32-bitowy .exe, 64-bitowy Python - 64-bitowy .exe.
cd /d "%~dp0"
python -m pip install --upgrade -r requirements.txt pyinstaller || goto :error
python -m PyInstaller --noconfirm --onefile --windowed --name ElectroMan --icon icon.ico --add-data "data;data" em.py || goto :error
echo.
echo Gotowe: dist\ElectroMan.exe
pause
exit /b 0
:error
echo Budowanie nie powiodlo sie.
pause
exit /b 1
