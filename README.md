# L4D2 DXVK Bridge

[中文](#chinese) | [English](#english) · [v1.2.0 发布说明](docs/RELEASE-V1.2.0.md) · [简明版本记录](LDBREADME.md) · [详细更新历史](CHANGELOG.md)

**当前正式版：v1.2.0。** 修复已确认的窗口/全屏切换黑屏和联机 Volume 蓝绿偏色，扩展 PageBlock 管理与恢复，并提供可选 L4N 常用设置菜单。完整包默认 **x86 Host + learned-aggressive**，x64 Host 保留；详细诊断默认关闭。

[下载 v1.2.0](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/releases/tag/v1.2.0)：首次安装选完整包，已有安装选三件套补丁，L4N 插件单独下载。旧开发版附件保持原样。

开发者参考：[当前技术架构](docs/ARCHITECTURE.md) · [API 与 ABI](docs/API.md) · [配置说明](docs/CONFIGURATION.md)。

<a id="chinese"></a>

## 项目作用

在 Windows《Left 4 Dead 2》的 **32 位游戏进程**中接收 D3D9 调用，通过共享内存和命令队列交给独立 x86/x64 Bridge Host，由 DXVK 转为 Vulkan 渲染。游戏引擎和 Bridge Client 始终是 32 位；x64 Host 提供更大的渲染端地址空间。

桥负责 D3D9 接口、桥接资源、跨进程传输与呈现，以及这些实现引起的问题。它不修改 Source 游戏逻辑、私有对象或任务队列。项目没有显卡厂商白名单，不要求 NVIDIA/RTX，实际支持取决于所选 DXVK、GPU 和驱动。

## v1.2.0 的变化

- **切屏修复：**平衡隐式 swapchain/backbuffer 与 RT/depth getter 引用，修复已确认的黑屏；Reset/ResetEx 失败返回真实结果，成功后才提交 Client 状态。
- **联机偏色修复：**Volume LockBox/UnlockBox 使用正确的字节行距、层距和上传偏移，反馈用户已确认蓝绿偏色消失。
- **PageBlock 管理：**统一回收能力与安全检查，提供 Learned/Aggressive/Force GC，扩展符合条件的 Q8W8V8U8、ATI1/ATI2、mip、Cube face 和独立 Surface 恢复。`drop [experimental]` 默认未选。
- **默认 x86 Host：**降低已测试负载下的 Host 内存使用，保留 x64 选择；升级包不覆盖已有选择。
- **可选 L4N 设置：**Status、GC、Memory Policy、ReShade Presenter、Host。配置由 Bridge Client 安全保存，插件不直接编辑文件。
- **诊断与兼容：**扩展异常归因、内存、API/IPC 等待、偏色和数据追踪；可选详细诊断默认关闭，旧 PageBlock 控制 ABI 保持兼容。

包含 v1.1.1 的 ReShade 点击返回游戏激活修复。各版本的功能和修复见 [LDBREADME](LDBREADME.md)，验证范围见 [累计更新](docs/CHANGES-SINCE-V1.1.md)。

## 下载与安装

需要 **64 位 Windows 10/11**、Steam 版 L4D2，以及能运行所选 DXVK 的 Vulkan 显卡和驱动。

| Release 文件 | 选择方式 |
|---|---|
| `l4d2-bridge-v1.2.0.zip` | 首次安装；包含 Client、x86/x64 Host、官方 DXVK 2.6.1 和默认配置 |
| `l4d2-bridge-patch-v1.2.0.zip` | 已有安装；只更新三个桥二进制，保留运行配置、后端、ReShade 和 retention DB |
| `l4d2-bridge-l4n-v1.2.0.zip` | 可选 L4N SDK v2 菜单插件，独立于本体和补丁 |
| `SHA256SUMS.txt` | 下载文件校验；包内另有二进制 SHA256 和构建记录 |

1. 完全退出游戏与所有 Host，备份 `bin/dxvk_d3d9.dll` 和 `bin/.l4d2bridge/`。已有用户优先使用补丁包，完整包会覆盖同路径默认配置与 DXVK。
2. 解压后将包内 `bin` 合并到游戏根目录。三个桥文件必须同批更新；不要只替换 Client 或一种旧 Host。补丁包的 `config/` 是参考片段，不会自动替换运行配置。
3. 本项目通过 `bin/dxvk_d3d9.dll` 加载。如果原来在游戏根目录安装了 DXVK `d3d9.dll`，先备份并改名为 `d3d9.dll.before-bridge`，避免加载链混用。不要修改 Windows 系统 DLL。
4. Steam 启动选项：

```text
-vulkan -insecure -windowed
```

`-vulkan` 选择游戏的 DXVK 命名加载路径，桥 Client 接口仍是 D3D9；`-insecure` 使用非 VAC 安全模式。需要恢复 VAC 安全模式时恢复原始安装。

```text
Left 4 Dead 2/
├─ left4dead2.exe
└─ bin/
   ├─ dxvk_d3d9.dll                  # x86 Bridge Client
   └─ .l4d2bridge/
      ├─ bridge.conf
      ├─ L4D2Bridge32.exe            # x86 Host，随包默认
      ├─ d3d9vk_x86.dll              # x86 DXVK
      ├─ L4D2Bridge64.exe            # x64 Host
      └─ d3d9vk_x64.dll              # x64 DXVK
```

5. 从 Steam 启动。Client 自动启动 Host，**不要单独双击桥 EXE**。检查画面、进图、输入与正常退出。

## 常用配置

完整说明见 [CONFIGURATION](docs/CONFIGURATION.md)。运行配置是 **`bin/.l4d2bridge/bridge.conf`**，配置片段需要合并到该文件，每个键保留一个有效定义。手动修改后完整重启游戏和 Host；`dxvk.conf` 是另一个后端配置文件。

```ini
server.useVanillaDxvk = True
exposeRemixApi = False
forceX64Server = True
client.testX86Server = True
client.forceWindowed = True
useSharedHeap = False
useShadowMemoryForDynamicBuffers = True
clientChannelMemSize = 96MB
threadSafetyPolicy = 1
client.pageBlockRetentionPolicy = learned-aggressive
client.pageBlockRetentionDb = .l4d2bridge/resource-retention.db
client.testReadbackRecovery = False
client.pageBlockDiagnostics = False
client.dataDiagnostics = False
server.dataDiagnostics = False
server.presenterWindow = False
logApiCalls = False
logServerCommands = False
logLevel = Info
```

learned-aggressive 按能力、完整上传和 KEEP 历史选择性释放 Client 副本，后续需要旧内容时从 Host/DXVK 当前资源恢复。它不等于回收全部资源；指纹库不保存纹理正文。省略策略键时实现仍回退保守的 `keep`，升级旧配置应保留显式策略。参考 readback test 会保留副本并阻止真实回收，不用于日常运行。

| Host | 设置 | 使用条件 |
|---|---|---|
| x86，默认 | `client.testX86Server=True` | 优先节省 Host 内存，负载能容纳于 32 位地址空间 |
| x64，可选 | `client.testX86Server=False` | 需要更多渲染端地址空间余量，RAM 充足 |

**两种模式都保持 `forceX64Server=True`**，它选择运行目录，实际位数由 `client.testX86Server` 决定。完全退出再切换；省略该键仍有旧的 x64 兼容回退，因此保留显式选择。x86 Host 是 LAA，在 64 位 Windows 上最多约 4 GiB 用户地址空间，连续空闲块可能更小。

## 可选 L4N 菜单

Bridge 本体不依赖 L4N。需要支持仓库所附 SDK v2 的 L4N HUD；将独立插件包安装到 `bin/neko/plugins/L4D2BridgePlugin.dll`。旧插件先备份。

```text
L4D2 Bridge
├─ Status
├─ GC
├─ Memory Policy
├─ ReShade Presenter
└─ Host
```

- Status 仅显示实时查询的 PageBlock 信息；GC 子菜单提供 Learned、Aggressive、Force。
- Memory Policy 的 keep、lg、drop 立即改变当前会话，点击 `save to configure` 才保存。`drop` 继续标记实验性质。
- Host 只显示配置值；选择 x86/x64 后点击 Save，完整退出并重启才应用。
- ReShade Presenter 保存配套呈现/输入配置，下次启动应用；不负责安装或卸载 ReShade。

菜单不包含测试/诊断开关。旧 Bridge 下按兼容接口保留原有 Stats/GC/运行策略，新增保存功能不可用。详见 [L4N 控制说明](docs/L4N-BRIDGE-CONTROLS.md)。

## DXVK 与 ReShade

按自己的 GPU、驱动和兼容性选择官方 DXVK。完整包提供官方 **2.6.1 x32/x64** 作为已测试参考；替换后端时匹配位数：官方 `x32/d3d9.dll` → `d3d9vk_x86.dll`，`x64/d3d9.dll` → `d3d9vk_x64.dll`。不要替换桥 Client 为普通 DXVK DLL。

另有基于 2.6.1 x64 的可选 mem1 后端，只限制普通可映射分配块；不随本次本体升级重编，安装和历史观察见 [内存实验说明](docs/DXVK-MEMORY-EXPERIMENT.md)。相关 `dxvk.bridge*` 键写入 `dxvk.conf`，不能写入 `bridge.conf`。

已验证 ReShade 组合：**x64 Host + Vulkan ReShade 6.0.1**。在安装器选择 `bin/.l4d2bridge/L4D2Bridge64.exe`，API 选 Vulkan；保持窗口模式。不要把 D3D9 ReShade 代理覆盖到游戏侧 Client 上。

合并 [OVERLAY-INPUT.conf](config/OVERLAY-INPUT.conf)，或通过 L4N 的 Presenter 菜单保存配套配置。Home 开关面板，Host 选择独立设置，菜单不会自动切换为 x64。ReShade 本体、shader 和预设需要另行安装。说明见 [输入文档](docs/OVERLAY-INPUT-EXPERIMENT.md)。

## 已知问题与使用限制

- **Steam Overlay / Shift+Tab 的完整叠加层和输入支持仍未解决。** 相关实验默认关闭。
- IPC 超时或会话断开不能自动重连，需要完整退出并重新启动。
- x86 Host 受地址空间限制；x64 DXVK 可能使用更多 Host 内存。
- PageBlock 回收是选择性的，恢复可能等待后端；`drop` 反复恢复可能带来停顿，日常推荐 learned-aggressive。
- 实际兼容性和性能取决于 GPU、驱动、DXVK、MOD、地图及其他叠加层。

切屏和偏色修复有 x86 实机确认；ReShade 已验证组合见上文。原生回归与真实 GPU 验证的范围分别记录于 [发布说明](docs/RELEASE-V1.2.0.md)。历史 [v1.1 内存/FPS 观察](docs/V1.1-VALIDATION.md) 不作为所有配置的固定收益。

## 回退、日志与构建

完全退出后恢复备份的 DLL、桥目录和启动选项即可回退，保留其他 MOD。恢复原根目录 `d3d9.dll` 时先退出当前桥加载链。升级默认保留自己的后端、配置和 DB。

Client 日志为 `bridge32.log`，x86/x64 Host 分别为 `bridge-host32.log` / `bridge64.log`。报告桥相关问题时保留同次运行的两端日志，并说明 GPU、后端、Host 位数和操作步骤。可选详细诊断见 [配置文档](docs/CONFIGURATION.md)，日常无需启用。

源码使用固定上游 Bridge 提交和 [项目补丁](patches/l4d2-bridge.patch)。Windows 构建采用 MSVC 14.29、Python 3.11、Meson 1.3.2、Ninja 1.11.1.1；[CI](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/workflows/build.yml) 构建 x86 Client、x86/x64 Host，执行原生协议、布局、回收和诊断回归。L4N 未修改时复用已验证构件。构建方法见 [TESTING](docs/TESTING.md)。

<a id="english"></a>

## English

**v1.2.0 is the current stable release.** This Windows bridge forwards D3D9 calls from the 32-bit L4D2 process to an independent x86/x64 Host running DXVK. The game engine and Client remain 32-bit. There is no NVIDIA/RTX requirement; use a compatible Vulkan GPU, driver and DXVK backend.

The release fixes confirmed fullscreen/windowed Reset failures and Volume byte-pitch corruption behind the reported network colour tint. It expands selective PageBlock management/recovery, adds optional L4N common settings and Client-owned configuration persistence, and retains the ReShade reactivation fix. Detailed diagnostics default off. See [release notes](docs/RELEASE-V1.2.0.md) and the [version ledger](LDBREADME.md).

Download the full ZIP for a fresh installation, the matched three-binary patch for an existing installation, and the **separate optional L4N ZIP** only if needed. Exit L4D2 and all Hosts before updating. Merge `bin` into the game directory and preserve custom backends, configuration, ReShade and retention DB files. The full package includes official DXVK 2.6.1 and default configuration; the patch preserves installed runtime configuration and backends. Start through Steam with `-vulkan -insecure -windowed`; do not launch Host EXEs directly.

Fresh installations default to **x86 Host + learned-aggressive**. Keep `forceX64Server=True` for both modes; set `client.testX86Server=True/False` for x86/x64 and fully restart. Both modes use the same x86 Client. The x86 Host has at most approximately 4 GiB user address space with LAA; x64 provides more renderer headroom with workload-dependent memory costs.

Optional L4N SDK v2 controls install to `bin/neko/plugins/`. Menu order is Status, GC, Memory Policy, ReShade Presenter, Host. Policy selection changes runtime only until explicitly saved; Host selection also requires Save and a full restart. Presenter settings apply after a full restart and do not install ReShade. Bridge works without the plugin.

The validated ReShade combination remains **x64 Host + Vulkan ReShade 6.0.1**. Select the x64 Host EXE and Vulkan in its installer, use windowed mode and the presenter configuration described above. Replace only matching DXVK backend DLLs, never the Bridge Client.

**Steam Overlay/Shift+Tab remains unsupported/unfixed.** IPC failures require a full restart; there is no automatic reconnection. Recovery is selective, experimental drop may cause repeated recovery stalls, and performance/compatibility depend on hardware, drivers, maps, MODs and overlays. Native CI and recorded gameplay checks have separate scopes.

Client/Host logs are `bridge32.log` and `bridge-host32.log`/`bridge64.log`. Keep paired logs from the same run when reporting a Bridge issue. See [configuration](docs/CONFIGURATION.md), [architecture](docs/ARCHITECTURE.md) and [API/ABI reference](docs/API.md) for technical details.


## Credits / 署名与归属

> All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.

需求、规格和实机验证由 [yeyunyyds](https://github.com/yeyunyyds) 提供。生成声明仅适用于本项目新增实现，不适用于保留的上游代码。Requirements, specifications and hardware validation were provided by yeyunyyds; upstream code remains credited to its original authors.

| 来源 / Source | 原作者与用途 / Authors and role | 许可 / License |
| --- | --- | --- |
| [NVIDIA RTX Remix Bridge / dxvk-remix](https://github.com/NVIDIAGameWorks/dxvk-remix) | NVIDIA CORPORATION & AFFILIATES and contributors; Bridge proxies, IPC, window/lifecycle foundation | Bridge MIT and original bundled notices |
| [DXVK](https://github.com/doitsujin/dxvk) | Philip Rebohle, Joshua Ashton, Robin Kertels, Jeffrey Ellison and contributors; D3D9 → Vulkan | zlib/libpng |
| [Microsoft Detours](https://github.com/microsoft/Detours) | Microsoft Corporation and contributors; API hooks | MIT |
| [Tracy](https://github.com/wolfpld/tracy) | Bartosz Taudul and contributors; upstream profiling component | BSD-3-Clause |
| [TXVK](https://github.com/tianxiaols/TXVK) | tianxiaols / TXVK contributors; public documentation/binary analysis reference, no custom code copied or binaries redistributed | Closed source; current TXVK license reserves all rights; reference only |
| [ReShade 6.0.1](https://github.com/crosire/reshade/tree/v6.0.1) | Patrick Mours; public ABI and input reference, no SDK implementation or DLL redistributed | SDK: BSD-3-Clause OR MIT |
| L4N plugin SDK v2 | User-provided official interface header; preserved verbatim, optional HUD controls | License unspecified in supplied header; not relicensed as MIT |
| L4D2 / Steam | Valve; game/platform, not distributed here | Valve's terms |

保留全部原作者版权与许可；完整清单见 [THIRD_PARTY.md](THIRD_PARTY.md) 与 `licenses/`。Preserve all upstream notices; third-party code is not claimed as original fork work.

## MIT License

本项目新增代码和修改采用 **MIT License**，Copyright © 2026 yeyunyyds，全文见 [LICENSE](LICENSE)。原代码继续遵循原许可证；本项目 MIT 不重新授权 DXVK、Tracy、游戏或显卡驱动。

New fork implementation and modifications are released under MIT, Copyright © 2026 yeyunyyds. Original upstream code retains its own copyrights/licenses; the project's MIT license does not relicense third-party components. Preserve the original notices when redistributing.
