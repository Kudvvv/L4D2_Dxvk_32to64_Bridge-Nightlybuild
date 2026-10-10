@echo off
@REM 将幸存者单人包vpk拖动到此bat上即可自动转换，更多信息请查看survivor_convert.bat
call "%~dp0\l4n_magic_converter.exe" survivor_vpk_gen %*
pause