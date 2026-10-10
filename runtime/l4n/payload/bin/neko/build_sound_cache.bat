@echo off
chcp 65001
echo 一键生成sound.cache
echo 将sound目录下的任意文件或者文件夹拖入到本bat文件
echo 目前有一个bug，请确保你的音频文件后缀名是小写的
echo 不支持带口型数据的语音

set nekomimi="%~dp0source_nekomimi.exe"
%nekomimi% build_sound_cache %1
pause