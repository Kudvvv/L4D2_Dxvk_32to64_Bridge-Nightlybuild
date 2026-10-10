chcp 65001
@REM 从原版wav语音文件里复制valve口型数据到自定义语音wav里，根据目录结构去对应要复制和复制到的wav文件
@REM 完成后需要重建声音缓存snd_rebuildaudiocache
@REM 主要用于编辑gameinfo.txt添加Game Path形式的语音mod，其它形式安装的需自行转化
@REM 所以你得确保left4dead开头和update目录里的语音文件是原版的，
@REM 有些语音mod的安装教程是直接覆盖原版文件，口型数据是存储在wav文件里的，不然会复制不到。

@REM 这个脚本放到游戏根目录下的xxx文件夹，运行即可。
@REM xxx文件夹里是你的自定义语音，也是你编辑gameinfo.txt添加Game所填写的目录名，结构应该是这样"xxx/sound/player/***/*/*"
@REM 命令行输出里有看到过SUCCESS即成功

@REM 游戏根目录路径
set src=..
@REM 要接收添加口型数据的语音文件夹路径
set dst=.\sound\player
set nekomimi=%src%\bin\neko\source_nekomimi.exe
%nekomimi% copy_valve_data "%src%\left4dead2\sound\player" "%dst%"
%nekomimi% copy_valve_data "%src%\left4dead2_dlc1\sound\player" "%dst%"
%nekomimi% copy_valve_data "%src%\left4dead2_dlc2\sound\player" "%dst%"
%nekomimi% copy_valve_data "%src%\left4dead2_dlc3\sound\player" "%dst%"
%nekomimi% copy_valve_data "%src%\update\sound\player" "%dst%"

@REM 脚本文件的两个变量dst和src是相对路径，如果你不按照要求把脚本文件放到正确的地方，相对路径会对不上，你得自己把路径改成绝对路径
pause