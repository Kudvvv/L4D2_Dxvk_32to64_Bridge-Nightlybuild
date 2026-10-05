# L4D2 DXVK Bridge — v1.1

[中文](#chinese) | [English](#english) · [v1.1 发布说明 / Release notes](docs/RELEASE-V1.1.md)

<a id="chinese"></a>

## 项目目的与当前状态

在 Windows《Left 4 Dead 2》的 **32 位游戏进程**中接收 D3D9 调用，再通过共享内存和命令队列交给独立 Bridge Host，由 DXVK 转为 Vulkan 渲染。可选 **x64 或 x86 Host**；游戏引擎本身仍是 32 位。x64 模式提供更大的渲染端地址空间，v1.1 的客户端资源保留策略减少不必要的 CPU 副本。

v1.1 是当前已实机测试并由作者确认的稳定版本，已测试配置没有已知的发布阻断问题；这不表示所有设备、Mod 或场景都没有问题。项目没有显卡厂商白名单，不要求 NVIDIA/RTX。当前参考 GPU 为 Intel Arc B580，其他 GPU/驱动需按实际兼容性验证。

## 快速开始

需要 **64 位 Windows 10/11**、Steam 版 L4D2，以及能运行所选 DXVK 的 Vulkan 显卡/驱动。首次使用窗口模式。

1. 下载 v1.1 完整发布包，或 [成功的 v1.1 Actions 构建](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/workflows/build.yml) 中的 **`l4d2-bridge-v1.1`** artifact。核对包内 `VERSION` 为 `1.1`；旧构建不是 v1.1。更新已有安装时先备份客户端、整个 `.l4d2bridge` 目录和 Steam 启动选项。
2. 关闭游戏及所有桥进程，将包内 `bin` 合并到游戏根目录。首次安装使用包内 `bridge.conf`；升级时手动合并配置，保留已有 DXVK、ReShade 和 retention DB。完整包带官方后端，直接覆盖会替换你的定制后端。
3. 本项目使用 `bin/dxvk_d3d9.dll` 加载路径。如果原来在游戏根目录安装了 DXVK `d3d9.dll`，先备份并改名为 `d3d9.dll.before-bridge`，避免加载链混用。不要修改 Windows 系统 DLL。
4. Steam → L4D2 → 属性 → 启动选项，使用：

```text
-vulkan -insecure -windowed
```

`-vulkan` 让 L4D2 加载 `bin/dxvk_d3d9.dll`；客户端接口仍为 D3D9。需要控制台日志时可加 `-console -condebug`。`-insecure` 是非 VAC 安全模式；需要 VAC 安全模式时恢复原始安装。

```text
Left 4 Dead 2/
├─ left4dead2.exe
└─ bin/
   ├─ dxvk_d3d9.dll                  # 本项目 x86 客户端，不能换成普通 DXVK
   └─ .l4d2bridge/
      ├─ bridge.conf
      ├─ L4D2Bridge64.exe            # x64 Host
      ├─ d3d9vk_x64.dll              # x64 DXVK 后端
      ├─ L4D2Bridge32.exe            # x86 Host
      └─ d3d9vk_x86.dll              # x86 DXVK 后端
```

5. 从 Steam 启动游戏。客户端会自动启动所选 Host，**不要单独双击桥 EXE**。检查菜单、进图、输入和正常退出；只有进程存在不代表渲染正常。

### 正常 / 推荐配置

完整设置见 [config/bridge.conf](config/bridge.conf)。v1.1 随包推荐 **x64 + learned-aggressive**，详细诊断关闭，ReShade 输入窗口按需启用。以下是关键设置，编辑时每个键只保留一份：

```ini
server.useVanillaDxvk = True
exposeRemixApi = False
forceX64Server = True
client.testX86Server = False
client.forceWindowed = True
useSharedHeap = False
useShadowMemoryForDynamicBuffers = True
clientChannelMemSize = 96MB
threadSafetyPolicy = 1
client.pageBlockRetentionPolicy = learned-aggressive
client.pageBlockRetentionDb = .l4d2bridge/resource-retention.db
client.testReadbackRecovery = False
client.pageBlockDiagnostics = False
server.presenterWindow = False
logApiCalls = False
logServerCommands = False
logLevel = Info
```

`learned-aggressive` 不等于丢弃全部资源：只处理支持的 MANAGED、Usage=0 静态 2D 纹理；其他资源或不完整上传保留原行为。恢复读取服务器/DXVK 当前资源，可能读取 DXVK 自身的 CPU backing，不保证每次都是 GPU image readback。DB 记录需要保留的资源，实际路径为 `bin/.l4d2bridge/resource-retention.db`。不要为了日常使用开启 `client.testReadbackRecovery`；保留参考副本的测试会使真实淘汰退回 KEEP。源码在缺少策略设置时仍采用保守的 `keep`，升级旧配置必须显式合并优化设置。

### 选择 x86 / x64

完全退出游戏和 Host，修改 `bin/.l4d2bridge/bridge.conf`，再从 Steam 启动。**两种模式都保持 `forceX64Server = True`**，这是运行目录选择；实际位数由现有名称 `client.testX86Server` 决定。

| 模式 | 设置 / EXE / 后端 | 主要优势 | 主要限制 |
| --- | --- | --- | --- |
| x64 Bridge | `client.testX86Server = False`；`L4D2Bridge64.exe`；`d3d9vk_x64.dll` | 大地址空间，当前主要路径；适合希望有更多余量、RAM 充足的重度资源配置 | 当前 DXVK x64 路径的 Host 内存较高 |
| x86 Bridge | `client.testX86Server = True`；`L4D2Bridge32.exe`；`d3d9vk_x86.dll` | 当前测试中内存明显较低，适合优先节省 RAM 且工作负载能容纳于 x86 Host 的用户 | LAA Host 在 64 位 Windows 上仍最多约 4 GiB 用户地址空间，连续空闲空间可能更少 |

客户端始终是 x86。x86 不是对所有负载都更好，x64 也不会使游戏引擎变为 64 位。可合并包内 `X86-HOST.conf` / `X64-HOST.conf`；模式切换不需要关闭 memory policy 或删除 DB。日志分别为 `bridge-host32.log` / `bridge64.log`，客户端始终是 `bridge32.log`。

### DXVK 版本与可选 mem1

**按自己的显卡、驱动与兼容性选择官方 DXVK 版本，不必固定在 2.6.1，也不保证最新版在你的配置上更合适。** 本项目完整包提供官方 **DXVK 2.6.1 x32/x64**，它是当前已测试的参考版本；其他版本并未全部验证。替换后端时保持位数匹配：官方 `x32/d3d9.dll` → `bin/.l4d2bridge/d3d9vk_x86.dll`，官方 `x64/d3d9.dll` → `bin/.l4d2bridge/d3d9vk_x64.dll`。不能替换桥客户端 `bin/dxvk_d3d9.dll`。

另提供基于 **2.6.1 x64** 的小幅 mem1 优化版，通过 [独立后端工作流](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/workflows/build-dxvk-experiment.yml) 的 `l4d2-bridge-memory-update-v1.1` artifact 获取。它限制普通可映射分配块，已观察到退图保留容量降低；不是重新设计纹理生命周期，也不能替代客户端优化。它是明确标记的修改版，首次安装不必使用。详见 [mem1 安装与回退](docs/DXVK-MEMORY-EXPERIMENT.md)。历史配置示例文件名仍为 `dxvk-memory-1.0.1.conf`；仅在 mem1 DLL 上，将它合并到生效的 **`dxvk.conf`**，不是 `bridge.conf`：

```ini
dxvk.bridgeMappedChunkSize = 16
dxvk.bridgeMemoryDiagnostics = False
```

### ReShade（可选）

已测试组合：**x64 Host + Vulkan ReShade 6.0.1**。在 ReShade 安装器选择 `bin/.l4d2bridge/L4D2Bridge64.exe`，API 选择 **Vulkan**；不要把 D3D9 ReShade 代理放到游戏侧桥客户端上。Vulkan 层 DLL 可由安装器安装到系统的 ReShade 数据目录；`ReShade.ini`、预设和 shader 路径应对应 Host，实测配置位于 `bin/.l4d2bridge/`。

将包内 [OVERLAY-INPUT.conf](config/OVERLAY-INPUT.conf) 合并到 `bridge.conf`：

```ini
server.presenterWindow = True
server.presenterInput = True
server.presenterOverlayKey = 36
server.presenterHotkeyFallback = False
client.hookMessagePump = True
client.overrideCustomWinHooks = True
client.DirectInput.forward.mousePolicy = 0
client.DirectInput.forward.keyboardPolicy = 0
```

保持窗口模式。Home 打开/关闭界面；公开开关事件协调输入捕获，不需要默认启用热键状态猜测。Home 重复开关已通过，鼠标操作、不同 ReShade 版本及 x86 ReShade 组合的验证范围不同，不能自动推广。Shader 包也要兼容所选 ReShade 版本。细节见 [输入实现与实测记录](docs/OVERLAY-INPUT-EXPERIMENT.md)。**Steam Shift+Tab 完整叠加层仍不可用，不属于 v1.1 已修复功能。**

### 恢复推荐设置 / 卸载

恢复包内 `bridge.conf` 的推荐值：`client.testX86Server=False`、`client.pageBlockRetentionPolicy=learned-aggressive`、`server.presenterWindow=False`、`client.hookMessagePump=False`、`client.overrideCustomWinHooks=False`，两项 DirectInput forwarding 为 `0`，诊断/参考 readback 关闭。需要排查 retention 问题时可单独设 `client.pageBlockRetentionPolicy=keep`，会增加冗余 backing；这是保守选项，不是优化配置。DB 无需删除。

退出后恢复备份的后端可撤销 mem1，同时移除 `dxvk.bridge*` 设置。彻底卸载则恢复原 DLL、桥目录和启动选项，恢复根目录旧 `d3d9.dll` 的原名；只处理本项目文件，保留其他 Mod。完整包含官方后端，升级时优先保留自己的后端/配置，**配对更新客户端和所用 Host**。

## v1.0 → v1.1

- **客户端内存优化**：`learned-aggressive` 在符合条件的静态纹理上传完成后真正释放冗余 PageBlock backing；需要旧内容时从服务器资源恢复，校验后学习为 KEEP。已在实际游戏中测试。一次诊断中首次上传后未再锁定的资源占累计 backing 字节 **99.77%**；后续一轮真实淘汰累计释放 **5.5935 GiB**，该轮未观察到 retention miss。这是累计逻辑字节，**不是同时节省的 RAM**，也不表示消除了 DXVK/Bridge 的全部内存。证据边界见 [验证记录](docs/V1.1-VALIDATION.md)。
- **ReShade Home / 输入修复**：原游戏 HWND 属于 `left4dead2.exe`，64 位 ReShade 无法直接捕获它的输入。桥现在可使用服务器拥有的呈现子窗口、受控键盘转发及 ReShade 公开接口协调输入。Vulkan ReShade 6.0.1 的接口注册和重复 Home 开关已实机通过。
- **新增 x86 Host 选择**：同一 32 位客户端和转发逻辑可搭配 `L4D2Bridge32.exe` / x86 DXVK，提供较低的实测内存占用；x64 Host 保留更大的地址空间。包含 x86 结构布局、Shader 能力传输和 ATI1/ATI2 压缩纹理传输修正。
- 保留命令队列事件唤醒、v1.0 的可回收纹理映射、可选 mem1 后端；详细诊断从日常安装流程移至开发文档。

## 内存：四类来源要分开

| 来源 | 含义 | v1.1 如何处理 |
| --- | --- | --- |
| 原游戏与 Mod | 引擎、模型、音频、其他程序的原有开销 | 不把它们归为桥新增占用 |
| Bridge 架构 | 独立 Host、代理对象、IPC 队列与必要传输 | 仍有开销，不承诺全部消除 |
| DXVK 自身 | CPU 可访问纹理 backing、映射、分配块及其保留行为 | 依 Host 位数和后端配置变化，正常生命周期继续由 DXVK 管理 |
| 客户端冗余 PageBlock | 为客户端锁定/上传而维护的额外 backing | `learned-aggressive` 释放符合条件且不必长期保留的副本 |

**作者报告的实机 A/B 观察：**同一总体游戏/Mod 场景下，总系统 RAM（包括后台程序）约为：

| 配置 | 总系统 RAM | 相对无桥差值 |
| --- | ---: | ---: |
| 无桥 | 16.5 GB | — |
| x86 Bridge，旧 KEEP | 17.3 GB | +0.8 GB |
| x86 Bridge，learned-aggressive | 16.7 GB | **+0.2 GB** |
| x64 Bridge，旧 KEEP | 19.4 GB | +2.9 GB |
| x64 Bridge，learned-aggressive | 18.5 GB | **+2.0 GB** |

优化前后 x86 约降低 **0.6 GB**，x64 约降低 **0.9 GB**。以上全部为约数和本次负载观察，**不是保证的固定开销、单个进程工作集或自动控制变量基准测试**。没有把所有剩余差值都归属到某一种分配。

x64 路径在此负载下观察到 **3 GB+ 的 Host/CPU 可访问纹理或映射内存**，不表示本项目新增了一个 3 GB 泄漏。DXVK 2.6.1 的可映射块计算包含：

```cpp
if (mappable)
  size /= env::is32BitHostPlatform() ? 16u : 4u;
```

同一初始尺寸下，x86 的块目标更保守；最终大小还受预算、堆大小和分配路径影响，不能把这两项除数解释为固定的内存占用比例。此外 Windows x86 的 MANAGED texture 可走分页 section/unmapping，而 x64 通常保留 host-visible Vulkan buffer。mem1 小块实验降低了部分保留容量，但游戏中大量存活纹理 CPU backing 仍存在。x86/x64 差异与这些后端策略和存活数据有关，不能简单解释为客户端又复制了一遍。

**3 GB+ 的内部/Host 观察与表中 +2.0 GB 总系统 RAM 差值是不同指标，不能相加。** 工作集、提交、分配容量、共享 GPU 内存也不能简单相加。v1.1 不为压低读数而改写 DXVK 正常 x64 生命周期；可选 mem1 只调整块上限。实际内存取决于 Mod、纹理、地图、GPU/驱动、DXVK 及配置。Host 几 GiB 占用本身不是泄漏证据。

## 测试配置与性能

参考环境由作者提供：**Intel Core i5-12600KF、Intel Arc B580、测试时的 L4N + Skeeto 环境、约 9 GB Mod**（人物、武器皮肤、物品等资源替换为主，自定义地图相对较少）、v1.1 Bridge。DXVK 参考为 2.6.1；x64 mem1 为另行测试的可选后端。L4N/Skeeto、驱动和 Mod 清单未记录精确固定版本，因此不把“测试时版本”称为持续保证的最新版。

该环境正常游戏可运行。作者在部分场景对比中观察到 **约 20 FPS 的性能损失**；这是场景相关观察，不能视为所有机器固定减 20 FPS，也没有据此计算平均 FPS / 1% low。性能受硬件、Mod、地图、分辨率、帧率上限、驱动和 DXVK 配置影响。测量来源与边界见 [v1.1 验证记录](docs/V1.1-VALIDATION.md)。

## 已知限制

- Steam Overlay / Shift+Tab 未修复，v1.1 不承诺支持。
- x64 DXVK 可占用明显更多 Host 内存；x86 Host 仍受 32 位地址空间限制。
- 性能开销随负载变化，不保证每种 Mod、自定义地图或插件兼容。
- D3D9 极端调用、设备 Reset、不同 DPI/窗口行为、异常第三方叠加层和罕见 Mod 组合未全部穷尽测试。
- PageBlock 优化不涵盖所有资源；首次恢复可能等待后端，失败会触发保守处理，不应把目前测试通过扩大为永不失败。

## 技术文档与构建

日常使用不需要启用详细诊断。开发/排查入口：

- [PageBlock 诊断](docs/PAGEBLOCK-DIAGNOSTICS.md) · [learned retention 实现与历史实验](docs/LEARNED-RETENTION-EXPERIMENT.md)
- [readback recovery 前置验证](docs/READBACK-RECOVERY-EXPERIMENT.md) · [DXVK/mem1 分配实验](docs/DXVK-MEMORY-EXPERIMENT.md)
- [Host 内存诊断](docs/HOST-MEMORY-DIAGNOSTICS.md) · [GPU 分配诊断](docs/GPU-ALLOCATION-DIAGNOSTICS.md)
- [x86/x64 实现与对照方法](docs/X86-HOST-COMPARISON.md) · [v1.0 首次验收](docs/FIRST-GAME-VALIDATION.md)
- [v1.1 发布、升级与构建](docs/RELEASE-V1.1.md) · [测量证据](docs/V1.1-VALIDATION.md)

源码由固定的上游 Bridge 提交和 [项目补丁](patches/l4d2-bridge.patch) 构成。Windows 构建使用 MSVC 14.29、Python 3.11、Meson 1.3.2、Ninja 1.11.1.1；[CI](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/main/.github/workflows/build.yml) 构建 x86 客户端和两种 Host，并验证命令队列、诊断、结构布局、压缩纹理、恢复与数据库。没有运行真实 Vulkan 游戏的 CI，硬件验证来自作者。诊断/参考 readback 开关只用于开发，配置方法在相应文档中。

---

<a id="english"></a>

## Purpose and release status

A Windows L4D2 bridge forwards D3D9 calls from the **32-bit game** to a separate **x64 or x86 Host**, where DXVK renders through Vulkan. x64 provides more renderer address-space headroom; the game engine remains 32-bit. There is no GPU-vendor whitelist or RTX requirement.

**v1.1 is the current author-confirmed, hardware-tested stable configuration**, with no known release-blocking issue in the tested configuration. This is not a bug-free or universal compatibility claim. Intel Arc B580 is the reference GPU.

## Quick Start

Requires 64-bit Windows 10/11, Steam L4D2 and a Vulkan-capable GPU/driver compatible with your chosen DXVK. Start windowed.

1. Obtain the complete v1.1 release package or **`l4d2-bridge-v1.1`** from a [successful v1.1 build](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/workflows/build.yml); verify `VERSION` is `1.1`. Back up the client, `bin/.l4d2bridge/` and Steam launch options.
2. Exit the game and hosts, then merge the supplied `bin` into the game directory, using the layout above. For an upgrade, preserve custom DXVK/ReShade settings and the retention DB, and merge configuration manually. The full package includes official backends and can overwrite a custom backend.
3. If using root-directory DXVK `d3d9.dll`, back it up and rename it to `d3d9.dll.before-bridge`. This project uses `bin/dxvk_d3d9.dll`, which must remain the **Bridge x86 client**, not an ordinary DXVK DLL. Never alter Windows system DLLs.
4. Set Steam launch options to `-vulkan -insecure -windowed`. Add `-console -condebug` only if console logs are needed. This selects the game's DXVK-named D3D9 loader and non-VAC-secure mode; restore the original installation for VAC-secure play.
5. Start L4D2 through Steam. The client launches the Host automatically; do not double-click the EXE. Verify actual rendering, input, entering a map and normal shutdown.

### Recommended settings and mode selection

[config/bridge.conf](config/bridge.conf) supplies **x64 + learned-aggressive**, with detailed diagnostics and the optional ReShade presenter disabled. Use the key configuration block above, retaining one value per key. An omitted policy still defaults to conservative `keep` in the implementation, so upgrades must explicitly merge `client.pageBlockRetentionPolicy = learned-aggressive`.

| Mode | Setting / executable / backend | Best suited to | Main limitation |
| --- | --- | --- | --- |
| x64 | `client.testX86Server = False`; `L4D2Bridge64.exe`; `d3d9vk_x64.dll` | More address-space headroom, sufficient RAM, large renderer workloads; primary Host path | Higher current x64 DXVK Host memory usage |
| x86 | `client.testX86Server = True`; `L4D2Bridge32.exe`; `d3d9vk_x86.dll` | Prioritizing RAM use when the workload fits x86 limits | At most approximately 4 GiB user address space with LAA on 64-bit Windows; contiguous availability can be lower |

**Keep `forceX64Server = True` in both modes**: it selects the runtime directory, while `client.testX86Server` selects the actual executable. Exit both processes before switching and restart through Steam. Both modes share the x86 client; changing mode does not require deleting the DB or disabling retention. Supplied `X86-HOST.conf` / `X64-HOST.conf` are merge snippets. `bridge-host32.log` is the x86 Host log, `bridge64.log` the x64 Host log, and `bridge32.log` always the client log.

The optimization applies to supported MANAGED, Usage=0 static 2D textures, not every resource. The DB resides at `bin/.l4d2bridge/resource-retention.db`. Recovery uses current server/DXVK resource contents, which can be DXVK's own CPU-visible buffer; it is not necessarily a GPU-image transfer. Keep `client.testReadbackRecovery = False`: the retained-reference experiment prevents real eviction. Detailed diagnostics are optional.

### Choosing DXVK and optional mem1

**Choose an official DXVK version compatible with your own GPU and driver.** The package supplies official **2.6.1 x32/x64**, the tested reference version; newer releases are not automatically more compatible and other versions have not all been tested. Install official `x32/d3d9.dll` as `bin/.l4d2bridge/d3d9vk_x86.dll` or `x64/d3d9.dll` as `d3d9vk_x64.dll`, matching the Host. Preserve the client DLL.

The separately distributed **2.6.1 x64 mem1** is a small, clearly marked modification that optionally caps ordinary mapped chunks. Obtain `l4d2-bridge-memory-update-v1.1` from the [backend workflow](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/workflows/build-dxvk-experiment.yml). It reduces some retained capacity, not all live texture backing, and does not replace client optimization. Follow [its guide](docs/DXVK-MEMORY-EXPERIMENT.md); the legacy example filename remains `dxvk-memory-1.0.1.conf`. Only with that modified DLL, merge `dxvk.bridgeMappedChunkSize = 16` and `dxvk.bridgeMemoryDiagnostics = False` into the effective **`dxvk.conf`**, not `bridge.conf`. The complete Bridge defaults to official DXVK.

### Optional ReShade

The tested combination is **x64 Host + Vulkan ReShade 6.0.1**. Select `bin/.l4d2bridge/L4D2Bridge64.exe` in the ReShade installer and choose Vulkan. Do not install a D3D9 ReShade proxy over the client. Vulkan layer DLLs can live in the installer's system data directory; the tested `ReShade.ini` and shader paths are under the Host directory.

Merge [OVERLAY-INPUT.conf](config/OVERLAY-INPUT.conf), matching the ReShade block above: presenter/input enabled, key `36` (Home), hotkey fallback disabled, message-pump/custom-window hooks enabled and both DirectInput forwarding policies `0`. Stay windowed. Home open/close is hardware-confirmed; this does not establish every mouse/reset scenario, other ReShade versions or x86 ReShade compatibility. Use compatible shader packages. **Steam Shift+Tab remains unsupported and unfixed.** See [input implementation](docs/OVERLAY-INPUT-EXPERIMENT.md).

### Restore recommended settings / uninstall

Restore the shipped config: x64 (`client.testX86Server=False`), `learned-aggressive`, presenter/message-pump/custom-window hooks disabled, both DirectInput forwarding policies `0`, diagnostic/reference tests off. `client.pageBlockRetentionPolicy=keep` is a conservative troubleshooting option that retains more backing. Preserve the DB.

Restore the backed-up backend and remove `dxvk.bridge*` options to undo mem1. For complete removal, restore the original DLLs/directory and launch options, including the old root `d3d9.dll` filename, leaving unrelated mods intact. Upgrade the client and selected Host together; preserve custom backends/configuration.

## v1.0 → v1.1

- **Client memory retention:** `learned-aggressive` genuinely releases redundant PageBlock backing after eligible static textures finish uploading, recovering old contents from server resources when necessary and learning KEEP decisions. In one diagnostic run, initial-upload-only backing accounted for **99.77% of cumulative bytes**. A later eviction run released **5.5935 GiB cumulatively**, with no observed retention misses in that run. This is neither simultaneous RAM savings nor elimination of all Bridge/DXVK memory. See [validation](docs/V1.1-VALIDATION.md).
- **ReShade Home/input:** a host-owned presentation child window, foreground-scoped keyboard forwarding and ReShade's public interface address input capture across the game/Host HWND ownership boundary. Vulkan ReShade 6.0.1 registration and repeated Home open/close capture cycles passed hardware testing.
- **x86 Host option:** the same client/protocol can use x86 DXVK for lower measured memory usage when the workload fits its address space. x64 remains the primary path for additional headroom. Includes native structure/capability and ATI1/ATI2 transfer fixes.
- Retains event-based queue wakeups, reclaimable texture views and the optional mem1 backend. Detailed diagnostics are separate from ordinary setup.

## Understanding memory

Separate original game/mod memory, necessary Bridge objects/IPC/Host costs, DXVK's CPU-accessible texture backing and allocator retention, and the **extra client PageBlock copies** optimized by v1.1. These are different ownership/accounting domains.

**Author-reported gameplay A/B observations**, for the same general workload, measuring total system RAM including background programs:

| Configuration | Approximate total system RAM | Difference from no Bridge |
| --- | ---: | ---: |
| No Bridge | 16.5 GB | — |
| x86, old KEEP | 17.3 GB | +0.8 GB |
| x86, learned-aggressive | 16.7 GB | **+0.2 GB** |
| x64, old KEEP | 19.4 GB | +2.9 GB |
| x64, learned-aggressive | 18.5 GB | **+2.0 GB** |

Observed reductions were **0.6 GB for x86** and **0.9 GB for x64**. These rounded, workload-specific observations are not fixed overhead, process working sets or an automated controlled benchmark. They do not assign every remaining byte to a particular allocator.

**3 GB+ of Host/CPU-accessible texture or mapped memory was observed in the tested x64 workload.** That alone does not demonstrate a project-added leak. DXVK 2.6.1 uses the mapped-chunk sizing expression shown above (`16u` divisor for x86 versus `4u` for x64); budget/heap constraints and dedicated allocations still affect final sizes. It is not a fixed ratio of total memory. Windows x86 also supports MANAGED texture section unmapping, whereas x64 typically retains host-visible Vulkan buffers. Smaller mem1 chunks reduced some retained capacity while substantial live texture CPU backing remained.

Much of the architecture difference is associated with these DXVK paths and live data, not simply another duplicate client copy. v1.1 does not rewrite normal x64 DXVK resource lifetime to minimize a reported RAM figure; optional mem1 adjusts chunk sizing only. **The 3 GB+ internal/Host observation must not be added to the +2.0 GB total-system A/B difference.** Working set, commit, allocator capacity and shared GPU usage can overlap. Actual usage varies with mods, textures, maps, GPU/driver and backend configuration.

## Tested configuration / performance

The author confirms **Intel Core i5-12600KF + Intel Arc B580**, the L4N + Skeeto setup used during testing, approximately **9 GB of mods**, primarily characters, weapon skins and items, with relatively few custom maps. The reference DXVK is 2.6.1; x64 mem1 was separately tested. Exact L4N/Skeeto/driver versions and the full mod list were not pinned, so this is not an ongoing “latest version” guarantee.

Normal gameplay works in this environment. An **approximately 20 FPS performance cost was observed in some comparisons**, depending on scene/workload. It is not a universal fixed −20 FPS and does not establish average or 1% low FPS. Hardware, maps, mods, graphics settings, frame caps, drivers and DXVK configuration materially affect results. See [measurement provenance](docs/V1.1-VALIDATION.md).

## Known limitations / developer documentation

Steam Overlay/Shift+Tab is not supported/fixed. x64 can use substantially more Host memory; x86 has address-space limits. Performance varies, and every mod/map/plugin is not guaranteed compatible. Extreme D3D9 calls, resets, unusual overlays, DPI/window behavior and uncommon mod combinations have not been exhaustively tested. Retention is selective; recovery can wait on the backend or fail with conservative handling.

Advanced documentation: [PageBlock](docs/PAGEBLOCK-DIAGNOSTICS.md), [learned retention](docs/LEARNED-RETENTION-EXPERIMENT.md), [readback recovery](docs/READBACK-RECOVERY-EXPERIMENT.md), [DXVK/mem1](docs/DXVK-MEMORY-EXPERIMENT.md), [Host memory](docs/HOST-MEMORY-DIAGNOSTICS.md), [GPU allocations](docs/GPU-ALLOCATION-DIAGNOSTICS.md), [x86/x64](docs/X86-HOST-COMPARISON.md), [v1.0 validation](docs/FIRST-GAME-VALIDATION.md) and [v1.1 release/build instructions](docs/RELEASE-V1.1.md). Diagnostic tests remain available but are not ordinary setup steps.

Builds use a pinned upstream Bridge plus the [fork patch](patches/l4d2-bridge.patch), MSVC 14.29, Python 3.11, Meson 1.3.2 and Ninja 1.11.1.1. [CI](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/main/.github/workflows/build.yml) builds the client and both Hosts and runs native protocol/layout/memory/recovery tests; it does not run L4D2 on a real GPU.

## Credits / 署名与归属

> All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.

需求、规格和实机验证由 [yeyunyyds](https://github.com/yeyunyyds) 提供。生成声明仅适用于本项目新增实现，不适用于保留的上游代码。Requirements, specifications and hardware validation were provided by yeyunyyds; upstream code remains credited to its original authors.

| 来源 / Source | 原作者与用途 / Authors and role | 许可 / License |
| --- | --- | --- |
| [NVIDIA RTX Remix Bridge / dxvk-remix](https://github.com/NVIDIAGameWorks/dxvk-remix) | NVIDIA CORPORATION & AFFILIATES and contributors; Bridge proxies, IPC, window/lifecycle foundation | Bridge MIT and original bundled notices |
| [DXVK](https://github.com/doitsujin/dxvk) | Philip Rebohle, Joshua Ashton, Robin Kertels, Jeffrey Ellison and contributors; D3D9 → Vulkan | zlib/libpng |
| [Microsoft Detours](https://github.com/microsoft/Detours) | Microsoft Corporation and contributors; API hooks | MIT |
| [Tracy](https://github.com/wolfpld/tracy) | Bartosz Taudul and contributors; upstream profiling component | BSD-3-Clause |
| [TXVK](https://github.com/tianxiaols/TXVK) | tianxiaols / TXVK contributors; public documentation/binary analysis reference, no custom code copied or binaries redistributed | MIT reference project |
| [ReShade 6.0.1](https://github.com/crosire/reshade/tree/v6.0.1) | Patrick Mours; public ABI and input reference, no SDK implementation or DLL redistributed | SDK: BSD-3-Clause OR MIT |
| L4D2 / Steam | Valve; game/platform, not distributed here | Valve's terms |

保留全部原作者版权与许可；完整清单见 [THIRD_PARTY.md](THIRD_PARTY.md) 与 `licenses/`。Preserve all upstream notices; third-party code is not claimed as original fork work.

## MIT License

本项目新增代码和修改采用 **MIT License**，Copyright © 2026 yeyunyyds，全文见 [LICENSE](LICENSE)。原代码继续遵循原许可证；本项目 MIT 不重新授权 DXVK、Tracy、游戏或显卡驱动。

New fork implementation and modifications are released under MIT, Copyright © 2026 yeyunyyds. Original upstream code retains its own copyrights/licenses; the project's MIT license does not relicense third-party components. Preserve the original notices when redistributing.
