@echo off
echo Building PLEXY Bot executable...
echo.

pip install pyinstaller
pip install -r requirements.txt

echo.
echo Creating executable...
echo.

python -m PyInstaller --noconfirm --onefile --windowed --add-data="%cd%\.env;." --name="PLEXY_Bot" --hidden-import=aiogram.types --hidden-import=aiogram.filters "bot_launcher.py"

echo.
echo Build completed!
echo.
echo The executable is located in the "dist" folder.
echo.
pause 