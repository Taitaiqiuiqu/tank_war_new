@echo off
setlocal

REM 1) 进入脚本所在目录
cd /d %~dp0

REM 2) 确保 PyInstaller 可用（可选：取消下一行注释自动安装）
REM pip install -U pyinstaller

REM 3) 清理上次构建
if exist dist rd /s /q dist
if exist build rd /s /q build
if exist main.spec del /f /q main.spec

REM 4) 打包
pyinstaller ^
  --onefile ^
  --name tank_war ^
  --add-data "images;images" ^
  --add-data "tank_images;tank_images" ^
  --add-data "musics;musics" ^
  --add-data "videos;videos" ^
  --add-data "maps;maps" ^
  --add-data "src/ui/fonts;src/ui/fonts" ^
  --add-data "src/ui/images;src/ui/images" ^
  --add-data "src/ui/theme.json;src/ui" ^
  main.py

REM 5) 提示输出位置
echo.
echo 打包完成，可执行文件路径：dist\tank_war.exe
echo.

endlocal
pause