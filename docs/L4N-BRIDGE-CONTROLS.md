# L4N Bridge 常用设置

开发接入见 [完整 API 参考](API.md)，进程/资源/配置的技术边界见 [当前架构](ARCHITECTURE.md)。本文描述最终 HUD 行为；控制 ABI 仍提供 runtime Host 等字段，插件按当前菜单要求不显示这些字段。

本页描述完整上游 1.2.1 的常用设置功能。Nightly 1.1 从同一源码编译 x86 `L4D2BridgePlugin.dll`，随唯一全量 ZIP 放在 `optional/L4N/`。Bridge 本体不依赖插件，需支持随仓库提供的 SDK v2 的 L4N HUD。

## 安装可选插件

需要菜单时，将完整包里的 `optional/L4N/L4D2BridgePlugin.dll` 复制到游戏 `bin/neko/plugins/`，重启游戏。仅解压完整包不会自动启用插件。不使用 L4N 的玩家可忽略 `optional/`。每次升级使用同一包中配套的 Client、Host 和插件。

上游历史版本的独立插件 ZIP 与拆包脚本保留在源码资料中；本 Nightly 发布不使用独立插件或 update 包。下载、默认 Host 和 ThinFlex 安装规则以 [README](../README.md) 为准。

## 菜单与生效时机

```text
L4D2 Bridge
├─ Status
├─ GC
│  ├─ Learned
│  ├─ Aggressive
│  └─ Force
├─ Memory Policy
│  ├─ 当前策略: keep / lg / drop (configure 或 runtime)
│  ├─ keep
│  ├─ lg
│  ├─ drop [experimental]
│  └─ save to configure
├─ ReShade Presenter
│  ├─ Enable
│  └─ Disable
└─ Host
   ├─ Configured Host: x86 / x64
   ├─ x86 Host
   ├─ x64 Host
   └─ Save
```

| 菜单 | 立即生效 | 保存配置 | 需要完整重启 |
|---|---|---|---|
| Status | 每次进入重新查询 PageBlock | 否 | 否 |
| GC | 执行原 learned/aggressive/force GC | 否 | 否 |
| Memory Policy: keep / lg / drop | 调用原 runtime SetPolicy | 否 | 否 |
| Memory Policy: save to configure | 确认当前 runtime 值 | 是 | 否 |
| ReShade Presenter | 不重建当前 Presenter | 是 | 是 |
| Host: x86 / x64 | 仅暂存选择 | 否 | 否 |
| Host: Save | 不更换当前 Host | 是 | 是 |

菜单不包含测试/诊断开关。PageBlock coverage 和 GC 结果是现有功能的状态信息。说明文字的 callback 返回 nullptr，不能意外打开新页面；返回导航由 L4N HUD 处理。根菜单的 `Last action result` 只表示上一次动作结果。Status、Host、Presenter 当前值在每次进入时重新查询。

Status 仅显示 PageBlock 的策略、blocks、locked/transferring、映射 VA、backing、drop/remap/reconstruction 与 coverage；不显示 Host、Presenter、配置目标或重启状态，也不调用通用设置查询。Host 页只显示 `Configured Host`，不显示运行 Host。Presenter 的已保存目标状态仍在其自身菜单中显示。

## Memory Policy

`common-settings-2` 插件将修改和保存分开。首行显示 `当前策略: keep / lg / drop`：运行策略与配置值相同则标记 `(configure)`，不同则显示运行策略并标记 `(runtime)`。配置读取失败或旧 Bridge 没有通用 API 时，只显示已成功查询的 runtime 值；不会把缺省响应误当成配置值。`lg` 是 `learned-aggressive` 的菜单缩写，配置键的完整值不变。

keep、lg、drop 三项仅调用旧 PageBlock `SetPolicy`，当前会话立即生效，文件保持原样。结果页提供底部的 `save to configure`。保存先重新查询实时 runtime 策略，再通过 Client 的既有通用 `SetMemoryPolicy` 写入 `client.pageBlockRetentionPolicy`；保存使用即时查询值，不使用打开菜单时的快照。该既有接口会重新确认同一个 runtime 值，本次没有改变 Bridge 控制 ABI 或 Client/Host 实现。若 runtime 查询失败，不尝试写配置。

保存操作分别报告运行确认与持久化结果：

- 两项成功：当前运行策略已确认，配置已保存，首行更新为 `(configure)`。
- 运行确认成功、写入失败：当前策略仍只用于会话，明确提示保存失败及错误；下次启动仍按原配置。
- 运行确认失败、写入成功：分别报告确认失败和保存成功，不把结果统称为成功。
- 两项失败：分别报告原因。

运行中选择 drop 不会自动清空 backing，也不会放宽现有 capability/safety/recovery 检查。GC 算法、等待与回收语义均未改变。旧 `L4D2BridgePageBlockControl::SetPolicy` 仍是 session only；只有新通用控制会额外保存。

## Host 和 ReShade Presenter

Host 每次进入重新读取配置，首行显示 `Configured Host`。点击 x86/x64 仅暂存选择，选择结果页底部有 Save；点击 Save 才由 Client 持久化，并重新读取、显示新的配置值。离开而未保存的选择在再次进入 Host 时丢弃。保存规则保持现有实现：x86 写 `forceX64Server=True`、`client.testX86Server=True`；x64 写 `forceX64Server=True`、`client.testX86Server=False`。两者都不能使用 `forceX64Server=False` 模拟切换。不杀进程、不 reconnect、不 Reset、不搬迁资源；退出整个游戏后重新启动才应用。

SDK v2 的非空回调返回值会打开结果子页，不能原地替换已经打开的父菜单。选择结果页可直接保存，保存结果显示重新读取的值；若返回到先前缓存的页面，需要退出并重新进入对应菜单以刷新。说明行继续返回 nullptr，不新增层级；结果页不递归提供其他选择。

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

Client 的通用状态仍保存启动时的 Presenter 配置、真实 Host 架构与重启判定，供控制 ABI 使用；精简后的插件不在 Status 显示这些字段。Host 和 Presenter 的保存结果继续明确提示完整重启。关闭 Presenter 不会回滚用户其他设置。

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

自动测试包含：新/旧/缺失控制导出的 SDK v2 菜单回调、严格菜单顺序和 GC 映射、Status 仅查询 PageBlock、说明文字不新增层级、100 轮导航、新鲜状态、策略 configure/runtime 来源、三种选择不写配置、保存实时策略及部分失败、Host 暂存/保存/放弃选择、保存后重新读取配置、Presenter 行为、配置读失败和旧 Bridge 保存不可用。既有 Client 测试继续覆盖 Presenter 配套键、restart 判定、配置文本保留/重复键/换行/Unicode、实际 Config 路径与缓存隔离、写入和替换失败、Host 拒绝写配置、旧 ABI 大小和边界。Windows 脚本为 `scripts/test_pageblock_gc.ps1`；构建保留 x86 插件。

仍需真实 L4D2 + L4N 检查 HUD 布局/文字容量、保存失败提示、操作后返回导航、完整重启后的 Host/Presenter 应用，以及 x64 Vulkan ReShade 6.0.1 与用户配置组合。原生 mock/unit 检查不代替游戏和 GPU 验证。
