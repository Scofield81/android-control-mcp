@echo off
REM Android Control MCP - egyszeru dupla-kattinthato wrapper az uninstall_windows.ps1-hez.
REM
REM Az "-ExecutionPolicy Bypass" itt KIZAROLAG erre az egyetlen PowerShell
REM folyamatra vonatkozik - NEM modositja a rendszer/felhasznalo TARTOS
REM execution policy-jat (lasd install_windows.cmd megjegyzeset).
REM
REM Tovabbadja a parancssori argumentumokat (pl. uninstall_windows.cmd -InstallDir D:\...).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall_windows.ps1" %*
