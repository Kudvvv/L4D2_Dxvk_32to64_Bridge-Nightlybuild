# v1.1 x86 Host：使用、实现与历史对照方法

**v1.1 状态：**x86 Host 已实机确认正常启动/进图，现为正式可选模式。完整包同时包含 x86/x64 Host 和官方 DXVK 2.6.1 两种位数；一般使用保持 `learned-aggressive`，仅切换 `client.testX86Server`。作者观察到优化后 x86 总系统 RAM 约 16.7 GB、无桥约 16.5 GB；不是固定 +0.2 GB 保证。正常安装见 [README](../README.md)，证据见 [验证记录](V1.1-VALIDATION.md)。

以下保留独立对照包及 KEEP 控制变量测试方法，**不是 v1.1 推荐配置的替代说明**。

## 安装与切换

先完全退出游戏和桥，备份目前的 `bin/dxvk_d3d9.dll` 以及整个 `bin/.l4d2bridge` 文件夹。将本包的 `bin` 合并到游戏安装目录的 `bin`，保留现有配置和根目录 DLL 启动链。本包不覆盖 `bridge.conf`。

文件布局：

```text
Left 4 Dead 2/
└─ bin/
   ├─ dxvk_d3d9.dll                     # 同一份 32 位桥客户端
   └─ .l4d2bridge/
      ├─ bridge.conf                   # 现有配置，手动合并下面的片段
      ├─ L4D2Bridge32.exe               # 新编译的 32 位 SERVER
      ├─ L4D2Bridge64.exe               # 同提交的 64 位 SERVER
      ├─ d3d9vk_x86.dll                 # 官方 DXVK 2.6.1 x32/d3d9.dll
      └─ d3d9vk_x64.dll                 # 官方 DXVK 2.6.1 x64/d3d9.dll
```

本包自带的两个 DXVK DLL 来自同一官方归档，均未修改。若当前使用 mem1 或其他定制后端，先备份，再使用本包的两个官方 DLL 完成这一轮对照。不要将游戏客户端 DLL 当作后端 DLL，也不要只给 64 位 EXE 改名。

把 `X86-HOST.conf` 中的配置合并到 `bin/.l4d2bridge/bridge.conf`，同名键只保留一个有效值：

```ini
server.useVanillaDxvk = True
forceX64Server = True
useSharedHeap = False
client.testX86Server = True
client.pageBlockRetentionPolicy = keep
client.testReadbackRecovery = False
```

从 Steam 正常启动游戏，桥客户端会自动启动 `L4D2Bridge32.exe`。`forceX64Server` 在此用于保持既有运行目录选择；实验开关选择实际的服务器 EXE。不要单独双击桥服务器。

64 位对照只把 `client.testX86Server` 改为 `False`，其余片段相同（见 `X64-HOST.conf`），完全退出后重新启动。两轮均使用 `keep`，避免 learned-aggressive 和已学习 DB 对架构对照引入额外变量。现有 DB 无需删除。测试结束后可恢复备份，或者将开关保持 `False` 继续使用同提交的 64 位服务器。

## 验证加载的位数

32 位运行应同时满足：

- 任务管理器中的服务器进程名为 `L4D2Bridge32.exe`。
- 桥日志 `bridge-host32.log` 显示 `Running in x86 mode!`，后端加载路径为 `d3d9vk_x86.dll`。
- DXVK 后端日志名为 `L4D2Bridge32_d3d9.log`，应显示 DXVK 2.6.1 和 x86 构建信息。

64 位服务器名为 `L4D2Bridge64.exe`，桥日志为 `bridge64.log`，后端路径为 `d3d9vk_x64.dll`。客户端日志仍是 `bridge32.log`，不是 32 位服务器日志。

Host 内存日志仍位于 `bin/.l4d2bridge/l4d2-host-memory.log`，游戏客户端内存日志为 `bin/l4d2-memory.log`。桥普通日志和 DXVK 日志可能受现有日志目录设置影响，可在游戏目录搜索上述文件名。

## 最小对照步骤

1. 先使用 32 位服务器，进入此前占用约 3 GB 的同一地图，保留相同 MOD、画质、分辨率、FPS 上限和后台程序。
2. 加载结束后保持活动窗口，正常游玩两分钟，记录游戏和服务器各自的内存。若已启用 DXVK HUD，同时记录 Sysmem allocated / used。不要使用清空工作集工具。
3. 返回主菜单等待两分钟，然后正常退出。立刻将这一轮日志复制到单独的 `x86` 文件夹，避免下次启动覆盖。
4. 改为 64 位服务器，重复相同步骤，将日志保存到 `x64` 文件夹。

两轮分别提供客户端 / 服务器桥日志、`l4d2-memory.log`、`l4d2-host-memory.log`、对应服务器的 DXVK 后端日志，以及地图内稳定时的任务管理器或 HUD 数字。对照进程工作集、Private Bytes、WDDM 非本地使用和游戏可用地址空间；这些指标不直接相加。实验不会采样其他应用。

若 32 位服务器加载失败或出现地址空间不足，请保留失败日志；不要将一次启动失败解释为内存结论。服务器标记 LARGEADDRESSAWARE，在 64 位 Windows 上仍受最多 4 GiB 用户地址空间限制，不能替代本项目的 64 位目标。

## 实现与验证边界

ATI1/ATI2（BC4/BC5）纹理的游戏可见 `LockRect.Pitch` 保留官方 DXVK 2.6.1 的兼容值，实际上传和返回数据使用真正的 4×4 压缩块布局。1024×1024 ATI1 上传 512 KiB，ATI2 上传 1 MiB，服务器不再用兼容 Pitch 乘以像素高度计算复制大小。客户端 backing 保持兼容布局的空间，并确保小 mip 至少能容纳一个完整压缩块；这项修复不会启用 DROP 或更改 retention policy。

部分区域的 `pBits` 字节偏移遵循官方 DXVK 的 ATI 特例，行复制使用实际压缩存储跨度。范围超出实际压缩存储时，客户端返回 `D3DERR_INVALIDCALL`；服务器也验证 descriptor、payload 大小与 Pitch，拒绝不匹配的上传。通用 surface 返回路径同样按实际压缩布局复制。普通 DXT 和未压缩纹理沿用既有路径。

首次成功处理每种 ATI 格式时，服务器记录一条 `L4D2_ATI_UPLOAD event=success`，包含资源 ID、格式、尺寸、API/storage Pitch、行数和字节数。失败记录 `event=rejected` 及原因。安装此修复时必须同时更新客户端 `bin/dxvk_d3d9.dll` 和两个服务器 EXE；旧客户端的 ATI1 payload 与新服务器不匹配，不能只替换服务器。

验证包括 x86/x64 原生受保护内存页测试：1×1 至 4096×4096 mip 尺寸、非方形纹理、完整与部分区域、shared heap 对应的存储复制，以及上传/返回的数据一致性和截短 buffer 拒绝。它们验证内存边界和复制内容，不代替 Arc B580 上的实际 Vulkan 游戏验证。进图是否正常、是否出现纹理异常，以及稳定内存占用仍需同地图测试。

ATI1/ATI2 (BC4/BC5) transfers preserve upstream DXVK 2.6.1's game-visible compatibility Pitch while copying actual 4×4 compressed blocks. A 1024×1024 ATI1 upload carries 512 KiB; ATI2 carries 1 MiB. Small mips allocate at least one complete block. Partial locks follow DXVK's ATI byte-offset convention and reject ranges outside compressed storage. Upload and surface-return paths validate and copy the real layout on both host architectures. The first successful transfer per format emits `L4D2_ATI_UPLOAD event=success`; rejected transfers log their reason. Update the client DLL and both host EXEs together. Guard-page tests on native x86/x64 cover full mips, partial regions, shared storage and returned bytes; actual Vulkan gameplay on the target GPU still needs verification. Retention policy and the official DXVK DLLs are unchanged.

客户端对零宽度 / 零高度的 `CreateTexture` 返回 `D3DERR_INVALIDCALL`，输出指针为 null，并记录 `L4D2 CreateTexture rejected on client` 的原始调用参数，不创建包装对象，也不改写成 1 像素。服务器对其他 `CreateTexture` 失败保留真实 HRESULT，记录 `L4D2 CreateTexture failed`，包含命令 UID、资源 / 设备 ID、尺寸、mip 数、usage、format、pool 和位数，并强制写入 `event=create-texture-failed` 内存快照。创建失败作为 D3D9 API 结果返回游戏，不触发桥的成功断言。客户端收到失败响应后置空输出、释放包装对象，且不向服务器发送不存在资源的 Destroy；如果响应超时，仍发送排在 CreateTexture 后的 Destroy，以清理可能已创建的资源。

失败快照中的 `address_free_bytes` 是可用虚拟地址空间总量，`address_largest_free_block` 是最大连续空闲地址块，均不代表可用 RAM 或显存。请在再次启动前保存客户端 / 服务器日志、DXVK 日志和 Host 内存日志。20:20 的失败日志实际记录 `4×0`、`D3DERR_INVALIDCALL`，当时工作集约 67 MiB、可用地址空间约 3.48 GiB；这次失败不能归因于内存耗尽，也不能作为地图内 x86 / x64 内存对照结果。客户端记录用于确认零尺寸是否直接来自游戏调用。

32 位服务器使用独立 Meson 构建目录，并为所有服务器与 util 代码设置 `REMIX_BRIDGE_SERVER`，避免复用客户端编译对象造成 IPC 方向错误。服务器名称、日志名称及后端文件名按位数区分；资源、命令协议及正常保留策略复用当前实现。进程地址扫描使用当前进程可见范围，以适配 x86。

适配器信息接收支持 x86 与 x64 的原生 `D3DADAPTER_IDENTIFIER9` 布局，仅忽略结构体尾部对齐填充；客户端不再固定要求服务器比自己多 4 字节。报文通过长度校验后才会写入输出和缓存。`D3DCAPS9` 按完整原生长度校验后复制，失败查询不使用未初始化的设备缓存。日志 `L4D2_ADAPTER` 记录两端报文长度及 vendor/device；`L4D2_CAPS` 记录 adapter/device 查询两端的原始 VS/PS 版本和纹理尺寸上限，不修改后端能力值。原生测试交换 x86/x64 生成的结构体，覆盖四种读写组合、非法长度和 Shader 值保留。若仍出现 Shader 2.0 弹窗，请提供客户端与 Host 日志，结合两端记录定位，不能把弹窗视为显卡实际只支持低版本 Shader。

CI 构建实际 x86 / x64 服务器，校验每个 EXE / DLL 的 PE 架构与 x86 EXE 的 LARGEADDRESSAWARE 属性，并在两种位数运行现有内存诊断测试。另在原生 32 位 Windows PowerShell 进程中加载官方 x86 DXVK，检查 D3D9 导出。上述检查不代表 L4D2 渲染已通过；硬件渲染、稳定性和约 3 GB 占用的差额需要游戏实测。

## License 与 Credits

新增实现遵循 [MIT License](../LICENSE)：

> All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.

原 Bridge 来自 NVIDIA RTX Remix Bridge，原作者版权与 MIT 通知完整保留。两个 DXVK DLL 来自 doitsujin/dxvk v2.6.1 官方发布，原作者包括 Philip Rebohle、Joshua Ashton、Robin Kertels、Jeffrey Ellison 及贡献者，遵循 zlib/libpng 许可证。本实验没有修改 DXVK。包内 `BACKEND-SOURCES.json`、`SHA256.json`、`licenses/` 和 [第三方说明](../THIRD_PARTY.md) 提供来源、校验值及许可。

---

# x86 bridge host / DXVK memory comparison

The x86 Host is a hardware-tested optional v1.1 mode; ordinary setup is in the [README](../README.md), with measured results in [validation](V1.1-VALIDATION.md). The following preserves the historical comparison-package methodology, including KEEP for controlled comparisons. This package compares an x86 host with official x86 DXVK 2.6.1 against an x64 host with official x64 DXVK 2.6.1, using the same x86 bridge client and command forwarding logic. The current author-reported x86 learned-aggressive result is approximately 16.7 GB total system RAM versus 16.5 GB without Bridge, not a fixed overhead guarantee.

Close the game and hosts, back up `bin/dxvk_d3d9.dll` and `bin/.l4d2bridge`, then merge the package's `bin` directory into the game installation. The package preserves your existing `bridge.conf`. Both supplied DXVK DLLs are unmodified official files; use them for the comparison instead of mixing the x86 official backend with an x64 customized backend.

Merge `X86-HOST.conf` into `bin/.l4d2bridge/bridge.conf`, with only one value per key. Launch the game normally through Steam. `client.testX86Server = True` selects `L4D2Bridge32.exe` and `d3d9vk_x86.dll`; `False` selects `L4D2Bridge64.exe` and `d3d9vk_x64.dll`. Keep all other comparison settings equal, including `client.pageBlockRetentionPolicy = keep` and `client.testReadbackRecovery = False`. Preserve the existing retention DB. Do not manually launch the host.

Check the x86 host process name and `bridge-host32.log` for x86 mode and the x86 backend path. Its DXVK log is `L4D2Bridge32_d3d9.log`. The x64 host uses `bridge64.log` and `L4D2Bridge64_d3d9.log`. `bridge32.log` always refers to the game-side client. Memory logs are `bin/l4d2-memory.log` and `bin/.l4d2bridge/l4d2-host-memory.log`.

Use the same map, mods, graphics settings, FPS limit and background applications. Play with the game window active for two minutes after loading, record stable game/host memory and optional DXVK Sysmem HUD statistics, return to the menu for two minutes, then exit normally. Save the logs into separate x86/x64 folders before starting the other run. Working set, private bytes and WDDM usage overlap and must not be added together. Preserve failure logs if the x86 host cannot load the map. Its LARGEADDRESSAWARE executable is still limited to at most 4 GiB of user address space on 64-bit Windows.

CI verifies actual Windows builds, PE architecture, the x86 address-space flag, memory diagnostics in both architectures, and loading the official x86 backend in a native x86 process. Actual GPU rendering and memory reduction remain subject to L4D2 testing. Upstream copyrights and licenses are preserved; newly added fork implementation uses the MIT License and the attribution stated above. The original DXVK binaries retain their zlib/libpng license.

Zero-width/height `CreateTexture` calls return `D3DERR_INVALIDCALL` with a null output before allocating a wrapper, logging the original client parameters without replacing zero by one. Other backend texture-creation failures are logged with a forced `create-texture-failed` memory sample and their actual HRESULT is returned, without a success assertion. The client clears the output and releases a rejected wrapper without sending Destroy for a resource explicitly reported as not created. A timed-out creation retains an ordered Destroy because backend ownership is unresolved. Successful creation and retention policy are unchanged. Native tests exercise 10,000 explicit failures, timeout cleanup and successful synchronous/asynchronous ownership using a mock wrapper; they do not prove GPU rendering.

`address_free_bytes` and `address_largest_free_block` describe total free virtual address space and the largest contiguous free region, not available RAM or VRAM. Save the client, host, DXVK and Host memory logs before restarting. The observed 20:20 failure is a `4×0` texture rejected with `D3DERR_INVALIDCALL`, at approximately 67 MiB working set and 3.48 GiB free virtual address space. It is not evidence of memory exhaustion or a gameplay memory comparison. Client-side logging helps establish whether the zero dimension originates in the game call.

Adapter identifier decoding accepts the native x86/x64 layouts and ignores only trailing alignment padding; it no longer requires the server payload to be four bytes larger than the client structure. Only validated payloads enter the output and cache. Full D3DCAPS9 payloads are checked before copying, and failed device queries cannot expose uninitialized cached values. L4D2_ADAPTER records lengths and vendor/device IDs on both sides; L4D2_CAPS records actual adapter/device VS/PS versions and maximum texture dimensions without changing capabilities. Native tests exchange x86/x64 generated structures in all four reader/writer combinations and reject malformed lengths while preserving Shader versions. A Shader 2.0 popup requires checking these client/server records; it does not establish the physical GPU capability.
