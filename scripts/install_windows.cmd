@echo off
REM Android Control MCP - egyszeru dupla-kattinthato wrapper az install_windows.ps1-hez.
REM
REM Az "-ExecutionPolicy Bypass" itt KIZAROLAG erre az egyetlen, ezzel a
REM paranccsal inditott PowerShell FOLYAMATRA vonatkozik - NEM modositja a
REM rendszer/felhasznalo TARTOS execution policy-jat (nincs Set-ExecutionPolicy
REM hivas sem itt, sem az install_windows.ps1-ben/uninstall_windows.ps1-ben).
REM A Windows sajat "PowerShell szkriptek futtatasa le van tiltva" alapertelmezett
REM vedelmet ez a folyamat-szintu kapcsolo kerueli meg BIZTONSAGOSAN, csak erre
REM az egy inditasra - a gepen semmilyen mas szkript/session policy-ja nem valtozik.
REM
REM Tovabbadja a parancssori argumentumokat (pl. install_windows.cmd -InstallDir D:\...).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*
