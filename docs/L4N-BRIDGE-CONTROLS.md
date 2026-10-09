# L4N Bridge 常用设置

本页对应 `codex/development-1.1.2-dev.1` 分支新增的常用设置功能，尚不在已经发布的 `v1.2.0-dev.1` 附件中。请使用本次提交的配套 Client、两种 Host 和插件构建。Bridge 本体不依赖 L4N；x86 `L4D2BridgePlugin.dll` 是可选组件，安装到 `bin/neko/plugins/`，需要支持随仓库提供的 SDK v2 的 L4N HUD。

## 分发规则

GitHub Release 中，L4N 插件必须以独立的 `l4d2-bridge-l4n-v<版本>.zip` 分发，不放进 Bridge 完整包或升级补丁。插件仍是可选组件。ZIP 专用下载分支的实验包可继续携带 `optional/L4N/L4D2BridgePlugin.dll`，不要求额外拆包。

发布脚本会自动拆分包含插件的已核验 ZIP；手动 Release 打包可运行 `scripts/separate_l4n_release.py --version <版本> --output <新输出目录> <完整ZIP> <补丁ZIP>`。它保留原输入，核对构建标识与文件哈希，从两个本体包删除插件 DLL，更新清单并生成独立插件 ZIP。

## 菜单与生效时机

```text
L4D2 Bridge
├─ Status
├─ GC
│  ├─ Learned
│  ├─ Aggressive
│  └─ Force
├─ Memory Policy
│  ├─ keep
│  ├─ learned-aggressive
│  └─ drop [experimental]
├─ ReShade Presenter
│  ├─ Enable
│  └─ Disable
└─ Host
   ├─ x86 Host
   └─ x64 Host
```

| 菜单 | 立即生效 | 保存配置 | 需要完整重启 |
|---|---|---|---|
| Status | 每次进入重新查询 | 否 | 显示当前是否需要 |
| GC | 执行原 learned/aggressive/force GC | 否 | 否 |
| Memory Policy | 调用原 runtime SetPolicy | 是 | 两项均成功时不需要 |
| ReShade Presenter | 不重建当前 Presenter | 是 | 是 |
| Host | 不更换当前 Host | 是 | 是 |

菜单不包含测试/诊断开关。PageBlock coverage 和 GC 结果是现有功能的状态信息。说明文字的 callback 返回 nullptr，不能意外打开新页面；返回导航由 L4N HUD 处理。根菜单的 `Last action result` 只表示上一次动作结果。Status、Host、Presenter 当前值在每次进入时重新查询。

Status 区分 `Runtime Host` 与 `Configured Host`。前者在 Host 握手成功后查询实际进程架构，后者重新读取持久配置。运行 x86 时选择 x64，只会变成 `Runtime Host: x86 / Configured Host: x64 / Restart Required: Yes`。无法查询架构或配置时显示 unavailable，不猜测目标已经应用。Memory Policy 显示运行策略，同时显示已保存的策略；ReShade Presenter 显示已保存的目标状态。

## Memory Policy

菜单先执行原 PageBlock SetPolicy，再独立保存 `client.pageBlockRetentionPolicy`。两步都尝试，返回各自 HRESULT：

- 两项成功：运行策略已改变，配置已保存。
- 运行成功、写入失败：运行策略已改变，明确提示保存失败及错误；下次启动仍按原配置。
- 运行失败、写入成功：明确提示运行失败，配置已保存；下次启动才采用目标策略。
- 两项失败：分别报告原因。

运行中选择 drop 不会自动清空 backing，也不会放宽现有 capability/safety/recovery 检查。GC 算法、等待与回收语义均未改变。旧 `L4D2BridgePageBlockControl::SetPolicy` 仍是 session only；只有新通用控制会额外保存。

## Host 和 ReShade Presenter

Host 选择保持现有规则：x86 写 `forceX64Server=True`、`client.testX86Server=True`；x64 写 `forceX64Server=True`、`client.testX86Server=False`。两者都不能使用 `forceX64Server=False` 模拟切换。不杀进程、不 reconnect、不 Reset、不搬迁资源；退出整个游戏后重新启动才应用。

Presenter Enable 保存以下九项：

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

Disable 只保存 `server.presenterWindow=False`、`client.hookMessagePump=False`、`client.overrideCustomWinHooks=False`，其余配置保留。Enable/Disable 都只修改 Bridge Presenter/输入支持，不安装、卸载或重载 ReShade 本体，也不改 Host 选择。当前已验证的 ReShade 组合仍是 **x64 Host + Vulkan ReShade 6.0.1**；x86 配置允许启用，只显示非阻塞提示。

Client 保存启动时的九项 Presenter 配置，并在查询时与磁盘目标比较；或目标 Host 与真实运行 Host 不同时，显示需要重启。Memory Policy 的运行与保存成功不会单独产生重启提示。恢复全部启动值后不继续显示过期提示；关闭 Presenter 不会回滚用户其他设置。

## 控制接口与向后兼容

新增独立的 WINAPI/stdcall 导出 **`L4D2BridgeControl`**（ordinal 42），见补丁生成的 `bridge/src/util/bridge_control.h`。通用 ABI v1 与既有 PageBlock ABI v1/v2 是独立协议：

- Request 16 字节：bytes、version、operation、value。
- Response 64 字节，pack(8)，全部固定宽度；无跨 DLL 的 STL、路径或指针字段。
- 操作 0..6：GetStatus、SetMemoryPolicy、GetMemoryPolicy、SetHostMode、GetHostMode、SetReShadePresenter、GetReShadePresenter。
- Host 值：Unknown=0、x86=1、x64=2；Policy 保持 keep=0、learned-aggressive=1、drop=2。
- 响应包含 runtime/configured Host、runtime/configured Policy、Presenter configured/startup、restartRequired、flags、runtimeResult、configResult、queryResult、configWriteSucceeded。
- flags 区分是否尝试 runtime 修改与配置写入。完整成功返回 S_OK；已处理的部分失败返回 S_FALSE，并保留独立错误码；错误请求/未初始化分别返回 E_INVALIDARG/E_PENDING。S_FALSE 不代表“全部成功”。

保留 `L4D2BridgePageBlockControl` ordinal 41、Request=16、v1 Response=208、v2 DetailedResponse=656、所有枚举和写入范围；原导出实现与头文件未改变。旧插件在新 Bridge 上继续使用原语义。新插件在已加载模块中枚举并查找控制导出；优先使用该 Bridge 同一模块的新导出，Stats/GC 继续使用旧导出并按 v2→v1 回退。旧 Bridge 下 Stats/GC/运行策略保留，策略明确提示不保存，Host/Presenter 显示 unavailable。没有控制导出也安全返回失败；插件不加载另一个 D3D9 runtime，不访问配置文件或游戏私有接口。

## Client 保存配置

配置路径使用 Client 初始化 Config 时实际读取的路径，并用同一路径读取目标/写入更新；不依赖插件路径、工作目录或 Host 位数。标准路径为 `<L4D2>/bin/.l4d2bridge/bridge.conf`。Host 进程的 Config 拒绝调用新增持久化接口。保存不修改启动配置缓存，因此不会在当前 session 动态应用 Host、窗口或输入设置。

编辑器复用 Config 的 key/value 词法规则，按行只更新指定键，保留注释、空行、顺序、未知键、UTF-8 Unicode/BOM、原有 CRLF/LF。目标重复键只保留第一个有效定义，其余原行改为注释，避免继续产生有效重复；不存在的键追加。无关 DXVK/ReShade/custom/diagnostic 值保持原样。UTF-16 等不支持的文本返回编码错误，保留原文件。

Client 内部序列化读写。用同目录 `bridge.conf.tmp` 的 CREATE_NEW 防止覆盖已有临时文件，写完检查长度、FlushFileBuffers、close，再检查原文件是否发生外部变化，最后 MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH) 同卷替换。失败清理自己创建的临时文件，保留原配置；已存在的临时文件不会被删除。返回 Win32→HRESULT 和 HUD 英文错误说明。原子替换是 Windows 本地文件系统的正常语义，不保证网络盘、断电或第三方编辑器的所有竞争场景；不覆盖检测到的外部修改。

## 验证与实机检查

自动测试包含：新/旧/缺失控制导出的 SDK v2 菜单回调、严格菜单顺序和 GC 映射、说明文字不新增层级、100 轮导航、新鲜 Status、三种策略及部分失败、Host 目标与运行值分离、Presenter 九项启用和三项关闭、restart 判定、配置文本保留/重复键/换行/Unicode、实际 Config 路径与缓存隔离、写入和替换失败、Host 拒绝写配置、旧 ABI 大小和边界。Windows 脚本为 `scripts/test_pageblock_gc.ps1`；构建保留 x86 插件。

仍需真实 L4D2 + L4N 检查 HUD 布局/文字容量、保存失败提示、操作后返回导航、完整重启后的 Host/Presenter 应用，以及 x64 Vulkan ReShade 6.0.1 与用户配置组合。原生 mock/unit 检查不代替游戏和 GPU 验证。
