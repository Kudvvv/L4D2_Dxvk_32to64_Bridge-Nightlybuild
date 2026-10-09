ThinFlex 崩溃修复 — 测试版安装说明
=================================

本完整 ZIP 已包含修复好的 bin/studiorender.dll、ENGINE-PATCH.json 及
licenses/Valve-engine-NOTICE.txt，与配套 Bridge Client/Host、GPLALL 后端一起提供。
确认游戏 DLL 版本匹配后，复制包内文件即可应用修复，无需运行补丁工具或安装 Python。
玩家包不附带 tools/thinflex 或补丁工具 EXE。

适用问题：studiorender.dll 的 ThinFlex 表情顶点缓存达到 10000 项后空指针崩溃。
修复将缓存扩至 65536 项，新增 2 MiB 缓存，保留原有表情计算及画质。
离线测试已通过。2026-10-10 收到用户反馈：v1.0.10 ThinFlex 修复有效。
本次保留相同补丁算法与输入／输出 DLL 哈希；反馈未提供游玩时长或完整模型范围，
不能据此确认所有场景的长期稳定性。

同次发布的 Bridge 包含三项性能优化：关闭 API 日志时避免临时字符串分配、
完整且紧密排列的表面整块复制、普通定期内存扫描移出 Present 线程。
固定 L4N 回放三对对照的提升中位数：1% low +4.57%、0.1% low +33.09%、
平均 FPS +10.14%、一秒 Present 峰值 +7.89%；p99 帧时间同时增加 3.48%。
性能测试未安装 ThinFlex，以上不是合并安装后的性能结果，也不保证其他电脑同幅提升。
测试条件、范围和限制：
https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/blob/main/docs/PERFORMANCE-2026-10-10.md

一、备份与版本核对

1. 正常退出 L4D2/L4N 游戏及 L4D2Bridge64 Host，将 ZIP 解压到独立临时目录。
2. 备份现有 Bridge 客户端、Host、配置及游戏 bin/studiorender.dll。
   若已安装本修复，请继续保留最初原版 studiorender.dll 的备份，
   不要用已经修复的 DLL 覆盖原版备份。
3. 保留现有配置：从临时解压目录移除会覆盖已有 dxvk.conf、bridge.conf、
   自定义后端、ReShade 或 DB 的对应文件。详细路径见包内 README.txt 或仓库 README.md。
4. 在 PowerShell 核对游戏目录中 DLL 的 SHA-256（修改下面的游戏路径）：

Get-FileHash -LiteralPath 'E:\Steam\steamapps\common\Left 4 Dead 2\bin\studiorender.dll' -Algorithm SHA256

支持的原始 DLL SHA-256：
3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85
包内修复 DLL SHA-256：
03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6

匹配原始哈希：完成原版备份后，可复制包内修复 DLL。
匹配修复哈希：已经应用本修复，可保留现有 DLL；务必继续保存原版备份。
其他哈希：游戏版本不匹配或已被另行修改，从临时解压目录移除 bin/studiorender.dll，
只更新 Bridge，不要强行替换引擎文件。

二、复制安装与复测

将准备好的临时目录内容合并复制到游戏根目录，成对更新 bin/d3d9.dll 与
bin/.l4d2bridge/L4D2Bridge64.exe。版本匹配时，复制 bin/studiorender.dll 即安装修复。
安装后再次核对该 DLL 哈希应为上面的修复哈希，并保存 ENGINE-PATCH.json 和原版备份。
客户端默认位于 bin/d3d9.dll，移除 -vulkan；使用该启动项的玩家按包内 README.txt
将客户端改名放在 bin/dxvk_d3d9.dll。现有配置、自定义后端、ReShade 与 DB 应保留。

使用原先报错的地图和模型复测；关注人物表情及持续游玩是否再次崩溃。
记录实际 DLL 哈希及测试场景；如出现问题，保存新的 dump 并恢复原文件。
此修复不调整 Bridge 默认配置、GPLALL、画质、VSync 或 G-SYNC。

三、回退

退出游戏及 Host。核对当前 bin/studiorender.dll 为上述原始或修复哈希，
并核对原版备份确为上述原始哈希，再用原版备份恢复 bin/studiorender.dll。
恢复后重新核对哈希。若游戏更新后当前 DLL 已变成其他哈希，不要用旧备份覆盖它。
如果没有匹配的原版备份，请用游戏官方文件验证恢复当前版本，不要下载未知来源 DLL。

修改后的 DLL 原数字签名失效。保留证书字节或重算 PE 校验和不能恢复签名。
该 Valve 游戏引擎文件不适用项目根目录 MIT 许可；归属说明见 Valve-engine-NOTICE.txt。
公开 Source SDK 仅用于定位常量，其许可不能据此视为覆盖整个游戏 DLL。
本测试版不代表原厂签名文件，也不代表已经证实所有崩溃都得到解决。
附件旁的 .sha256 可核对完整 ZIP；ENGINE-PATCH.json 记录引擎补丁及输入／输出身份。

维护者工具仍保存在源码仓库中，不放入玩家 ZIP。生成和验证命令（create/verify）、
补丁细节及三份 dump 的证据边界见 docs/THINFLEX-CRASH-FIX.md。
