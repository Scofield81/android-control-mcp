@echo off
REM Android Control MCP - egyszeru dupla-kattinthato wrapper az install_windows.ps1-hez.
REM Tovabbadja a parancssori argumentumokat (pl. install_windows.cmd -InstallDir D:\...).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*
