ThinFlex 崩溃修复工具 — 测试版
===========================

适用问题：studiorender.dll 的 ThinFlex 表情顶点缓存达到 10000 项后空指针崩溃。
工具只生成缓存扩至 65536 项的独立 DLL 副本，不自动安装，不关闭表情或降低画质。
离线测试已通过，原报错场景的游戏内验证和持续游玩验证尚未完成。

本附件不包含游戏 DLL。ThinFlexPatch.exe 可直接在 Windows 运行，无需安装 Python。
随附 patch_studiorender_flex.py 是相同工具的源码；详细证据见 docs/THINFLEX-CRASH-FIX.md。
同一 Release 的普通 Bridge ZIP 本身不会应用此修复；需要单独执行以下步骤。

仅接受原始 bin/studiorender.dll 的 SHA-256：
3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85
预期实验副本 SHA-256：
03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6
不匹配时工具会拒绝处理；不要用其他玩家的 DLL 强行替换，也不要绕过检查。
修改后的 DLL 原数字签名失效。保留证书字节或重算 PE 校验和不能恢复签名。
本测试版不代表原厂签名文件，也不代表已经证实所有崩溃都得到解决。

一、备份并生成（PowerShell）

1. 正常退出 L4D2/L4N 游戏及 L4D2Bridge64 Host。
2. 把本工具 ZIP 解压到独立目录，在该目录打开 PowerShell。
3. 修改下方游戏路径，逐段执行。请使用新的 test-copy 目录，不覆盖已有备份。

$gameRoot = 'E:\Steam\steamapps\common\Left 4 Dead 2'
$source = Join-Path $gameRoot 'bin\studiorender.dll'
$work = Join-Path (Get-Location) 'test-copy'
if (Get-Process -Name left4dead2,L4D2Bridge64 -ErrorAction SilentlyContinue) { throw '请先退出游戏及 Host。' }
if (Test-Path -LiteralPath $work) { throw 'test-copy 已存在，请保留备份并改用新的目录名。' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne '3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85') { throw '原始 DLL 不匹配，停止。' }
New-Item -ItemType Directory -Path $work -ErrorAction Stop | Out-Null
$original = Join-Path $work 'studiorender.original.dll'
$patched = Join-Path $work 'studiorender.experimental.dll'
$manifest = Join-Path $work 'studiorender.experimental.manifest.json'
Copy-Item -LiteralPath $source -Destination $original -ErrorAction Stop
.\ThinFlexPatch.exe create $original $patched --manifest $manifest --experimental-engine-patch
if ($LASTEXITCODE -ne 0) { throw '生成失败，请勿安装。' }
.\ThinFlexPatch.exe verify $original $patched $manifest
if ($LASTEXITCODE -ne 0) { throw '校验失败，请勿安装。' }

以上步骤不改变游戏目录。请保留原始备份、实验副本和 manifest，勿删除。

二、手工安装供测试（继续在同一 PowerShell 窗口）

先确认游戏及 Host 已退出。以下复制才会替换游戏 bin/studiorender.dll。

if (Get-Process -Name left4dead2,L4D2Bridge64 -ErrorAction SilentlyContinue) { throw '请先退出游戏及 Host。' }
.\ThinFlexPatch.exe verify $original $patched $manifest
if ($LASTEXITCODE -ne 0) { throw '校验失败，停止。' }
$record = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $record.original_sha256) { throw '游戏 DLL 已变化，请勿覆盖。' }
Copy-Item -LiteralPath $patched -Destination $source -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $record.output_sha256) { throw '安装校验失败，请恢复备份。' }

使用原先报错的地图和模型复测；关注人物表情及持续游玩是否再次崩溃。
记录实际 DLL 哈希及测试场景；如出现问题，保存新的 dump 并恢复原文件。
该实验副本不调整 Bridge 默认配置、GPLALL、画质、VSync 或 G-SYNC。

三、回退（继续使用上述变量；若重开 PowerShell，先重新设置这些路径）

if (Get-Process -Name left4dead2,L4D2Bridge64 -ErrorAction SilentlyContinue) { throw '请先退出游戏及 Host。' }
.\ThinFlexPatch.exe verify $original $patched $manifest
if ($LASTEXITCODE -ne 0) { throw '备份或实验记录校验失败，停止。' }
$record = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
$currentHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
if ($currentHash -notin @($record.original_sha256, $record.output_sha256)) { throw '游戏文件已经更新或被另行修改，请勿用旧备份覆盖。' }
Copy-Item -LiteralPath $original -Destination $source -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $record.original_sha256) { throw '恢复后校验失败。' }

游戏更新后的 DLL 如果哈希变化，本工具会拒绝处理；请等待匹配版本的后续验证。
下载附件旁的 .sha256 可核对工具包完整性。BUILD.json 记录构建来源和已验证的 DLL 哈希，
其中 game_validated=false 表示尚未完成游戏验证，不表示你的本地游戏已经打补丁。
