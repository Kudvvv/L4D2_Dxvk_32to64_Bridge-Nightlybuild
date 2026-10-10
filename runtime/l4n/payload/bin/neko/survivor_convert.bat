@echo off

@REM 幸存者模型转换的进阶脚本，需要熟悉一些制作幸存者mod的概念
@REM 本例子使用zoey的mdl作为输入
@REM 因为不需要生成zoey的mdl，所以后面会把zoey mdl的生成调用给注释掉
@REM 需要把本bat复制到例如xxxx文件夹里修改并运行
@REM 参考目录结构：
@REM xxxx\survivor_convert.bat
@REM xxxx\release\models\survivors\survivor_teenangst.mdl

@REM 用来转换的输入mdl，w模和v模
set INPUT_FILE=%~dp0\release\models\survivors\survivor_teenangst.mdl
set INPUT_VMODEL=%~dp0\release\models\weapons\arms\v_arms_zoey.mdl

@REM 用于复制动画预设的参考mdl路径，l4n只提供了八人使用zoey动画的预设，在survivor_converter目录下
@REM 你可能需要: 八人使用bill动画的预设、八人使用小人zoey动画的预设、八人使用zoey动画带静态表情的预设...
@REM 这些预设可以从现有的八人包里解包mdl来获得
@REM 如果拥有制作幸存者mod的能力，可以自己定制一套参考mdl
set REF_DIR=C:\Program Files (x86)\Steam\steamapps\common\Left 4 Dead 2\bin\neko\survivor_converter

@REM 转换工具的路径
set CONVERTER=C:\Program Files (x86)\Steam\steamapps\common\Left 4 Dead 2\bin\neko\l4n_magic_converter.exe

set W_MODEL_CMD="%CONVERTER%" survivor_wmodel_convert "%INPUT_FILE%"
@REM 调用转换工具，使用参考mdl的动画预设将输入mdl转换为对应幸存者的mdl
call %W_MODEL_CMD% "%REF_DIR%\survivor_biker.mdl"
call %W_MODEL_CMD% "%REF_DIR%\survivor_coach.mdl"
call %W_MODEL_CMD% "%REF_DIR%\survivor_gambler.mdl"
call %W_MODEL_CMD% "%REF_DIR%\survivor_manager.mdl"
call %W_MODEL_CMD% "%REF_DIR%\survivor_mechanic.mdl"
call %W_MODEL_CMD% "%REF_DIR%\survivor_namvet.mdl"
call %W_MODEL_CMD% "%REF_DIR%\survivor_producer.mdl"
@REM call %W_MODEL_CMD% "%REF_DIR%\survivor_teenangst.mdl"

@REM 调用转换工具，转换v模mdl
call "%CONVERTER%" survivor_vmodel_gen "%INPUT_VMODEL%"

@REM "Bill" 		"survivor_namvet" 		"v_arms_bill"
@REM "Coach" 		"survivor_coach" 		"v_arms_coach_new"
@REM "Ellis" 		"survivor_mechanic" 	"v_arms_mechanic_new"
@REM "Francis" 		"survivor_biker" 		"v_arms_francis"
@REM "Louis" 		"survivor_manager" 		"v_arms_louis"
@REM "Nick" 		"survivor_gambler" 		"v_arms_gambler_new"
@REM "Rochelle" 	"survivor_producer" 	"v_arms_producer_new"
@REM "Zoey" 		"survivor_teenangst" 	"v_arms_zoey"

pause