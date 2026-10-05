# v1.1 ReShade 输入修复 / Input fix and retained experiment notes

**v1.1 状态：**Windows 窗口模式、标准 x64 DXVK、Vulkan ReShade 6.0.1 的 Home / 公开接口开关已经过实机验证；功能仍按需启用，正常资源策略不变。完整 Steam Shift+Tab 实机不可用，v1.1 不支持/不继续修复。鼠标操作、长期运行、其他版本与 Reset 仍按各自验证范围判断。正常安装见 [README](../README.md)，下文保留实现、回退和实验方法。

## 安装与启用

1. 完全退出游戏与桥，备份当前 `bin/dxvk_d3d9.dll` 和 `bin/.l4d2bridge/L4D2Bridge64.exe`。
2. 将实验包的 `bin` 合并到游戏根目录。包内不含 DXVK 后端和正式 `bridge.conf`，保留当前 `d3d9vk_x64.dll`、ReShade、retention DB 和策略设置。游戏根目录现有的 `d3d9.dll` 加载器保持现状。
3. 将 `OVERLAY-INPUT.conf` 的设置合并到 `bin/.l4d2bridge/bridge.conf`，同名键保留一份：

```ini
server.presenterWindow = True
server.presenterInput = True
server.presenterOverlayKey = 36
server.presenterHotkeyFallback = False
client.forceWindowed = True
client.hookMessagePump = True
client.overrideCustomWinHooks = True
client.DirectInput.forward.mousePolicy = 0
client.DirectInput.forward.keyboardPolicy = 0
```

4. 保持 `server.useVanillaDxvk = True`、`exposeRemixApi = False`，64 位正常使用时保持 `client.testX86Server = False`。ReShade 仍使用 Vulkan 安装方式，不在客户端假 D3D9 设备上安装 ReShade D3D9 代理。
5. 进入菜单，按 Home，检查能否打开、点击、关闭 ReShade，以及关闭后游戏鼠标/键盘是否恢复。再进图、退回菜单，测试 Alt+Tab、窗口尺寸变化。Steam Shift+Tab 已确认不可用，不是本版本的验收成功项。

请提供 `bridge64.log`、`ReShade.log` 和实际表现，不需要采样其他程序。日志应包含 `L4D2_OVERLAY event=presenter`，其中 `owner_pid` 等于 `host_pid`；`event=reshade-api registered=1` 表示公开事件注册成功。`steam-modules` 分别检测 `vulkan32` / `vulkan64` 和 renderer，并在延迟加载状态变化时重新记录；仅表示模块加载，不能证明 Steam UI 已工作。`steam-hotkey posted=1 reshade_capture=0` 表示游戏前台的 Shift+Tab 已成功投递且 ReShade 未捕获输入。旧包的 `vulkan_layer=0` 只检查了 32 位命名，不能用于判定 64 位 Vulkan 层缺失。

若出现 `registered=0`，标准 ReShade 构建可能拒绝插件注册。可单独尝试 `server.presenterHotkeyFallback = True`：此模式用 Home 推测 UI 状态，打开、关闭都用 Home，不用 Escape。修改 ReShade 的开关按键时同步修改 `server.presenterOverlayKey`（十进制 Windows virtual-key code）；注册成功时输入捕获跟随 ReShade 的公开开关事件，不依赖该推测。其他插件若否决开关事件，也可能造成捕获状态不一致。

回退：关闭游戏，设置 `server.presenterWindow = False`，恢复此前输入设置；必要时恢复备份二进制。此实验不写 retention DB 或更改纹理策略。

## 实现和边界

ReShade 6.0.1 的 `input::register_window` 拒绝其他进程拥有的 HWND。原桥的呈现 HWND 属于 32 位游戏，渲染发生在桥进程，因而能显示效果却无法接收 Home。实验在桥的独立消息线程创建一个属于桥的 Win32 子窗口，嵌入游戏客户区；D3D9 CreateDevice、Reset、额外 swapchain 及非空 Present override 一致使用它。原游戏窗口和游戏查询缓存保持原含义。

低级键盘钩子仅在目标游戏处于前台时向桥窗口投递按键；不记录按键，不处理其他前台程序，保留 Windows/Alt+Tab 切换快捷键。独立线程的消息泵供 ReShade 处理输入。UI 关闭时子窗口禁用，鼠标继续交给游戏；UI 开启时启用子窗口，并通过已有的 Bridge UI-active 消息通知客户端暂停游戏输入。ReShade API 10 的 `reshade_open_overlay` 事件用于观察开关请求；只动态绑定公开 ABI，不附带 ReShade SDK 实现或 DLL。默认不使用 Home 状态推测。模块探测最多每秒一次，已注册后不再枚举模块。

目前仅支持一个主要游戏 HWND 和窗口模式。原生跨进程测试检查窗口归属、输入捕获切换、Present override 路由、尺寸同步和销毁；实际 Vulkan 输入、游戏独占鼠标、不同 DPI 设置及叠加层兼容性仍需实机验证。

## TXVK 参考核对

参考固定提交 [`7d466d794926ce26c113d810172c2abc37058319`](https://github.com/tianxiaols/TXVK/tree/7d466d794926ce26c113d810172c2abc37058319)。公开 Host 二进制的字符串和反汇编引用显示服务器呈现窗口、`server.presenterInput`、`server.substituteFocusWindow` 和独立 presenter 线程；这支持窗口归属方案，但不代表已恢复其完整源码。本项目独立实现，不分发 TXVK 二进制。

该版本 README 明确标注完整 Steam 叠加层不可用，以好友邀请面板替代。我们没有复制替代面板或伪造 `IsOverlayEnabled`。本实验保留正常 Steam Vulkan 层，仅保留诊断，不继续实施 Steam 修复；如未来重启该目标，需要另外调查 Steam 的进程/游戏身份和注入路径，不能把好友面板当作 Shift+Tab 修复。

ReShade 参考：https://github.com/crosire/reshade/tree/v6.0.1 。作者 Patrick Mours，SDK 标识 BSD-3-Clause OR MIT；本实验仅参考公开 ABI。上游版权和许可见 [THIRD_PARTY.md](../THIRD_PARTY.md)，本项目新增实现遵循 [MIT](../LICENSE)。

## English

The v1.1 optional, hardware-confirmed Home fix gives the Bridge a server-owned child presentation window. ReShade 6.0.1 rejects input registration for windows owned by another process; the original game-owned HWND crosses this boundary. CreateDevice, Reset, additional swapchains and non-null Present overrides now consistently target the host-owned child in windowed vanilla-DXVK mode.

Merge the supplied `bin` folder into the game directory after backing up the client and host. Preserve your installed DXVK backend, ReShade, retention database and policy. Merge the settings above into `bin/.l4d2bridge/bridge.conf`, removing duplicate keys. Test Home, overlay mouse interaction, closing the overlay, entering/leaving a map, Alt+Tab and resizing. Steam Shift+Tab is a known unsupported limitation, not a passed validation item. Submit `bridge64.log` and `ReShade.log`; profiling other processes is unnecessary.

Keyboard forwarding is limited to the foreground game and does not record keys. ReShade's public API 10 overlay event controls capture; registration failure is logged. The optional Home fallback estimates state and requires closing via Home. Other add-ons can veto the observed event. Disable `server.presenterWindow` and restore the previous input settings to roll back.

Steam's full overlay was confirmed nonfunctional and is not supported in v1.1. Latest TXVK also documents that it is unavailable and provides a separate friends invitation UI. This experiment does not substitute that UI or fake Steam overlay availability. Native tests cover cross-process ownership, capture switching, override routing, resizing and teardown; real GPU/input validation remains necessary.

All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.

## 实机反馈 / Hardware feedback

ReShade 6.0.1：用户确认 Home 可用。23:35:46–23:36:23 的一次 36 秒日志显示 presenter owner PID 与 host PID 一致、公开 API 10 注册成功、三次 capture 开关完整、正常退出，未出现跨进程 input registration 拒绝。此结论仅确认 Home/开关事件，不代替鼠标操作、进图及长期测试。

同轮 Shift+Tab 用户确认不可用，Steam 仍未修复。旧检测遗漏了 `SteamOverlayVulkanLayer64.dll`，无法据旧 `vulkan_layer=0` 判断其是否加载。该轮另有 35 个 ReShade effect 编译失败，错误包括版本太旧、未定义标识符和宏重定义，需要独立核对 shader 包与 ReShade 版本；它们不构成桥输入恢复失败的证据。
