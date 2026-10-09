# ThinFlex 缓存崩溃：限定版本的实验修复

本修复针对游戏引擎 `studiorender.dll` 内部的 ThinFlex 顶点缓存耗尽后空指针写入问题。完整发布包直接提供修复后的 `bin/studiorender.dll` 和 `ENGINE-PATCH.json`；玩家按 [安装与恢复说明](THINFLEX-TEST-README.txt) 核对版本、备份并覆盖即可，无需运行补丁工具。

2026-10-10 收到用户反馈：**v1.0.10 ThinFlex 修复有效**。本次继续使用相同补丁算法和输入／输出 DLL 哈希。反馈未提供游玩时长和完整模型范围，不能据此确认所有场景的长期稳定性。

修复 DLL 与三项 Bridge 性能优化放在同一个完整 ZIP 中发布：关闭 API 日志时避免临时字符串分配、完整且紧密排列的表面采用整块复制、普通定期内存扫描移出 Present 线程。包内修复版 SHA-256 为 `03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6`。已有相同修复版可保留；安装目录中的 DLL 若既不是下表原版，也不是此修复版，先跳过该文件，只更新 Bridge。

固定 L4N 回放的三对对照中，配对提升中位数为 1% low **4.57%**、0.1% low **33.09%**、平均 FPS **10.14%**、一秒 Present 峰值 **7.89%**；同时 p99 帧时间增加 **3.48%**，并非所有帧时间指标均改善。性能测试没有安装 ThinFlex 补丁，这些数据不能视为合并安装后的性能结果。测试条件、范围与限制见 [性能报告](https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/blob/main/docs/PERFORMANCE-2026-10-10.md)。

## 证据范围

本次结论只依据补充的三份转储：`20261009_230408`、`20261009_231259`、`20261010_001139`。三份转储中的 Bridge 客户端均匹配 **v1.0.6 / 上游 `5fd30eae` / 构建 `37926413396`**：PE 时间戳为 `0x6ac8d609`，SizeOfImage 为 `0x1f8000`，CodeView GUID 为 `dbe92864-8053-4af4-a434-8964ffc88424`、Age 为 1。

这与之后发布的 **v1.0.6 / 上游 `96547312` / 构建 `37951137320`** 不同；后者客户端时间戳为 `0x6ac906f7`，CodeView GUID 为 `2cbc1c87-6570-4b16-bce6-9cfc0ffccd45`。二者都标为 v1.0.6，不能仅凭版本号称转储与最新发布包完全一致。本次身份比较直接使用相应发布包中的二进制及构建元数据，不依赖日志中的版本字符串。

三份转储表现相同：

- 异常位置均为 `studiorender.dll + 0x11070`，执行 `movaps [eax], xmm0` 时 `EAX = 0`，访问异常明确记录向地址零写入。
- 调用点 `+0x1104b` 调用引擎内部的 `+0x1080`。匹配版本的机器码显示，该函数在 ThinFlex 计数达到 10000 时返回空指针，调用者随后没有检查结果。
- 对象均位于该模块基址加 `0xb2940`；调用参数 `vertCount` 均为 11855。
- 直接来源是引擎自己的 CPU 侧 ThinFlex 缓存，返回值不是 D3D 顶点缓冲区或索引缓冲区的 `Lock` 上传地址。

**三份小型转储没有收录缓存计数字段。** “达到上限”是根据匹配机器码中返回空指针的分支推导，不能说已从现场读到计数恰好为 10000。参数 11855 是当前调用的顶点范围，也不是已经成功分配的缓存条目数。ThinFlex 计数在一次模型绘制内可跨 mesh 累计。

Valve 公开 SDK 的 [`studio.h`](https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/public/studio.h) 定义了 `MAXSTUDIOFLEXVERTS = 10000`，在此仅作为结构常量参考。本项目的定位及修改清单来自匹配二进制的独立检查。发布 DLL 取自维护者本机的匹配游戏文件并按用户要求修改；原引擎归 Valve，不属于根目录 MIT 授权，见 [引擎归属说明](../licenses/Valve-engine-NOTICE.txt)。

这些证据足以定位本次空指针的直接来源，但不能据此宣称已经排除所有 Bridge、L4N 或模型数据的间接影响。

## 实验副本改动范围

修复只针对以下原始文件。维护者生成脚本会拒绝任何不匹配输入，不按文件名、游戏版本号或模糊特征猜测补丁位置；玩家直接复制成品时，仍需先核对安装目录内的文件哈希：

| 校验项 | 原始值 |
| --- | --- |
| 文件 | `bin/studiorender.dll` |
| SHA-256 | `3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85` |
| PE 时间戳 | `0x6a440dd6` |
| 架构 | x86 / PE32 |
| SizeOfImage | `0x453000` |

实验副本只改动六处代码立即数：

| 指令 RVA | 改动 |
| --- | --- |
| `0x1083` | ThinFlex 条目上限从 10000 改为 65536 |
| `0x10cd` | 分配器返回新数组中的条目 |
| `0x540b` | 顶点计算读取新数组 |
| `0xded1` | mesh 数据读取新数组 |
| `0x11083` | 普通 flex 路径读取新数组 |
| `0x112d7` | wrinkle flex 路径读取新数组 |

此外，PE 中新增 `.cflex` 节，位于 RVA `0x453000`，容纳 `65536 × 32` 字节，即 2 MiB 的可读写、不可执行缓存。该节由加载器零初始化，不在文件中附加 2 MiB 数据。PE 节数量、映像大小、未初始化数据大小和校验和随之更新；原有节的位置、对象布局、其他成员偏移以及原始证书和文件尾数据保持原样。

原有 ThinFlex 映射使用 16 位无符号索引。65536 个条目对应合法索引 **0 至 65535**；计数保持 32 位，达到 65536 后仍拒绝新分配。此实验没有扩大其他引擎缓存，也不支持超出现有索引能力的任意模型。

静态检查找到了上述五处数组地址计算，未发现指向旧 ThinFlex 数组的重定位指针；已识别的构造、析构路径使用同一个全局缓存对象。这些检查限定于上表的精确二进制，不能推广到其他游戏更新。

修复设计保留原来的 flex 计算和表情数据，不通过关闭表情、跳过超限顶点或降低画质避免崩溃。Bridge 偏色修复、GPLALL 后端、x64 Host、协议及默认配置均不在修改范围内；它也不调整 VSync、G-SYNC 或帧率限制。实际画面和游戏兼容性仍需实测。

**修改后的 DLL 原 Authenticode 签名失效。** 保留原始证书字节及重算 PE 校验和都不能恢复签名。清单明确记录此状态；该文件不应被描述成仍有有效原厂签名的文件。完整包保留 `licenses/Valve-engine-NOTICE.txt`，不包含玩家私有转储。

## 维护者：生成和校验副本

以下命令用于维护者复现补丁和检查成品；玩家无需执行，也无需在多个工具版本间选择。仓库保留 Python 参考实现与原生维护工具，完整发布 ZIP 不包含补丁工具。Python 参考实现只生成独立副本和清单，不安装文件或启动游戏。

需要 Python 3。以下 PowerShell 示例在本仓库根目录执行；先将 `$gameRoot` 替换为实际游戏目录。游戏及其 Bridge Host 必须先正常退出。

```powershell
$gameRoot = '<游戏目录>'
$source = Join-Path $gameRoot 'bin\studiorender.dll'
$work = Join-Path (Get-Location) 'thinflex-test'

if (Get-Process -Name left4dead2,L4D2Bridge64 -ErrorAction SilentlyContinue) {
    throw '请先正常退出游戏及 Bridge Host。'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw '找不到游戏 DLL，请检查 gameRoot。'
}
if (Test-Path -LiteralPath $work) {
    throw '实验目录已经存在；请选用新的空目录，保留原备份。'
}
New-Item -ItemType Directory -Path $work -ErrorAction Stop | Out-Null

$original = Join-Path $work 'studiorender.original.dll'
$patched = Join-Path $work 'studiorender.experimental.dll'
$manifest = Join-Path $work 'studiorender.experimental.manifest.json'
Copy-Item -LiteralPath $source -Destination $original -ErrorAction Stop

python scripts/patch_studiorender_flex.py create $original $patched --manifest $manifest --experimental-engine-patch
if ($LASTEXITCODE -ne 0) { throw '生成失败，请勿安装。' }

python scripts/patch_studiorender_flex.py verify $original $patched $manifest
if ($LASTEXITCODE -ne 0) { throw '校验失败，请勿安装。' }
```

`create` 拒绝覆盖已存在的输出文件，也拒绝输入、输出或清单指向同一路径。`verify` 会从原始文件重新计算完整预期输出，再逐字节比较副本及清单；它不只是对照清单中填写的哈希。

以上步骤结束后，游戏安装目录仍未改变。保留原始备份、实验副本和清单三者，以便验证和恢复。

## 维护者：手工安装实验副本

以下是实验验证步骤，不属于脚本的自动行为。离线验证不能代替游戏验证；只有准备进行实验测试时才执行安装。继续使用上一节中的变量，并确保游戏及 Host 已退出。

```powershell
if (Get-Process -Name left4dead2,L4D2Bridge64 -ErrorAction SilentlyContinue) {
    throw '请先正常退出游戏及 Bridge Host。'
}
python scripts/patch_studiorender_flex.py verify $original $patched $manifest
if ($LASTEXITCODE -ne 0) { throw '副本校验失败。' }

$record = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
$installedHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
if ($installedHash -ne $record.original_sha256) {
    throw '游戏文件已变化；请勿覆盖，重新检查版本。'
}
Copy-Item -LiteralPath $patched -Destination $source -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $record.output_sha256) {
    throw '安装后哈希不符，请恢复原文件。'
}
```

测试应使用原先出现问题的模型、地图及动作，检查表情、wrinkle 效果和持续游玩情况。记录实际使用的 DLL 哈希；出现新问题时保留新的转储并恢复原文件。不要仅凭能进入游戏就宣布修复成功。

## 维护者：恢复原文件

先正常退出游戏及 Host。以下命令验证备份确为受支持原文件，并拒绝覆盖既不是本实验副本、也不是原文件的其他版本，避免回滚时覆盖后续游戏更新。

```powershell
if (Get-Process -Name left4dead2,L4D2Bridge64 -ErrorAction SilentlyContinue) {
    throw '请先正常退出游戏及 Bridge Host。'
}
python scripts/patch_studiorender_flex.py verify $original $patched $manifest
if ($LASTEXITCODE -ne 0) { throw '原备份或实验记录校验失败。' }

$record = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
$installedHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
if ($installedHash -notin @($record.original_sha256, $record.output_sha256)) {
    throw '当前游戏 DLL 已是其他版本，请勿用旧备份覆盖。'
}
Copy-Item -LiteralPath $original -Destination $source -Force -ErrorAction Stop
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $record.original_sha256) {
    throw '恢复后哈希不符。'
}
```

恢复只涉及 `studiorender.dll`。保留实验目录，直到确认恢复成功；不需要重置游戏、L4N、Bridge 或显卡配置。

## 验证状态

| 验证项目 | 状态 |
| --- | --- |
| 补丁生成、严格输入拒绝及副本校验测试 | 最初修复验证通过 8 项补丁工具测试，包含半写失败清理、竞争创建和篡改拒绝；当时项目全部 62 项 Python 测试通过，后续新增测试以对应构建记录为准 |
| 六处机器码改动、数组边界与计算路径验证 | 通过限定指令片段测试；两个 ASLR 基址下实际执行分配器、四条地址读取前缀、普通/wrinkle 初始化前缀及 StartModel |
| 新 PE 节映射、零初始化、对齐和访问权限 | Windows 原生映射通过；SEC_IMAGE 下新池为 PAGE_WRITECOPY、不可执行，完整 2 MiB 全零；未执行入口或 DllMain |
| 游戏内使用反馈 | 2026-10-10 收到用户反馈，v1.0.10 ThinFlex 修复有效；未提供游戏时长及完整模型范围 |
| 持续游玩、表情效果和兼容性的完整验证 | 尚无覆盖全部场景的验证记录 |

离线验证、用户使用反馈和本项目性能对照分别记录。v1.0.10 的工具曾作为测试版发布；当前完整包直接提供同一修复结果。收到有效反馈不等同于所有模型、表情效果和长期稳定性均已验证。

2026-10-10 验证的候选 SHA-256：`03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6`。

机器码对照使用原始 DLL 的实际 x86 指令：旧版在计数 10000 时于 `+0x11070` 重现空地址写入；实验版同条件通过。额外覆盖 11855 范围、全部 65536 槽、32767/32768/65535 索引、自然计数饱和后拒绝、最终全池数据完整性、旧数组与相邻状态不受写入、池尾不可访问页，以及 tag 回绕与模型重置。四条读取测试只执行地址计算前缀，不等同于完整渲染函数或视觉验证。

Windows 检查分别以 `SEC_IMAGE_NO_EXECUTE` 和 `SEC_IMAGE` 建立映像映射，随后读取 PE 头、页属性和零填充区域，释放全部句柄。前者强制只读，后者确认缓存页具备写时复制权限。此检查未解析导入、执行 DLL 初始化或验证游戏的签名策略。

维护者可使用自己的匹配 DLL 复现离线测试。生成工具仅需 Python 标准库；下面的机器码验证另需 `pefile` 和 `unicorn`：

```powershell
python -m unittest discover -s tests -p 'test_*.py'
python -m venv .deps/thinflex-validation
.deps/thinflex-validation/Scripts/python.exe -m pip install pefile unicorn
.deps/thinflex-validation/Scripts/python.exe scripts/validate_studiorender_flex.py $original --report $work/machine-validation.json
```

运行验证脚本不会启动游戏、安装补丁或上传 DLL。游戏实测前仍须按上面的步骤备份、核对精确哈希；长期崩溃是否消失以原报错场景复测为准。
