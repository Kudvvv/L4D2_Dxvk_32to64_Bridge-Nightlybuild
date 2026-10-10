# Runtime / diagnostics separation

本次基于 main/v1.2.0 `47c4da5403e3b8f1b1beca0ffa35474be3027394` 清理。实现前已完成 [逐路径分类审计](RUNTIME-DIAGNOSTICS-AUDIT.md)。本次不引入优化算法、修改渲染输出、资源生命周期、Host 选择、Reset 或 IPC 顺序。L4N 源码、菜单和控制 ABI 均未修改；不重编译/打包未修改插件。已发布 v1.2.0 构件保持原样，本文记录新的源码行为。

## 实现结果

| 子系统 | 关闭后的工作 | 开启时 |
|---|---|---|
| Client memoryMonitoring | 在时钟/锁/扫描/文件前返回；无 VA/进程采样、memory atomics/峰值、文件或异步任务。GC 的 forced sample 也不能绕过开关。 | 原 Present/分配驱动的约 5 秒采样与事件快照。 |
| Host memoryMonitoring | 不访问/构造 Recorder，不配置 GPU 观察，不建立 diagnostic inventory，不更新队列 observation atomics 或 processed-command 总数；无周期扫描/内存文件。 | 原 VA、CPU/commit/GPU budget、resource/queue 日志。 |
| Crash history | CallScope/CommandScope/recordCommand 在 TLS/history 前返回；无命令 ring 或 API context 更新、可选退出队列 dump。 | 原上下文与 ring，basic/detailed 报告保留。 |
| API wait | 既有 gate 保留；无 diagnostic QPC/TLS stats/atomic/histogram/线程/文件。 | 原阶段计时与周期输出，格式和控制流不变。 |
| Color | producer gate 与延迟初始化 metadata map；关闭时 map 不分配、不哈希/查表/擦除记录，原 Volume call sites 保持不变；无 payload 哈希、diagnostic Getter/COM refs/状态记录、线程或日志。 | 原纹理/状态摘要和 backend 快照。 |
| Data / VB / IB | 既有 detail/histogram/状态比较 gate 保留；无 detail 分配、载荷比较、timing/counters、线程/文件。另将 memory total/Trace buffer total 归到明确开关。 | 原数据追踪/直方图；FULL_SHADOW 和锁契约不变。 |
| PageBlock / learned details | 无资源诊断记录、历史/模拟 LRU、learned summary 计数和日志 formatting/file；纯 recovery profiling 计时关闭。 | 详细输出继续存在；选定策略的 DB/identity/恢复正确性独立于日志开关。 |
| Presenter / Input | 全部相关功能关闭时，不创建 Presenter window/thread/hook，不进入可选 input detour/DirectInput setup，不做 ReShade 模块扫描/binding/capture；输入消息保留核心窗口/session 通知。 | 原按需窗口/输入路由及 ReShade addon 协作。Input=False 的呈现窗口不初始化其输入。 |
| Steam input | 实验与诊断均关时无 callback/module polling、输入状态观察或日志。单独开启实验时不因 diagnostic=False 停止真实状态转发。 | 观察日志与实验状态转发分别启用；没有新增 Steam Overlay 修复。 |
| API / command / Debug / Trace logging | API 名使用 const char*，日志计数 map 延后至真正启用；server command 字符串原有 flag gate 保留；Debug/Trace 用 lazy producer，关闭后不求值、不格式化或分配字符串。 | 保留原输出。初始化前的一次性日志缓存不改。 |

新开关 `client/server.memoryMonitoring=False`、`client/server.crashDiagnostics=False` 均启动时读取，随包显式关闭。新 crashDiagnostics 缺失时，旧 Detailed=True 仍请求 history；显式 False 优先。PageBlock diagnostics 不自动开启 memory monitoring；`PB_POLICY_SUMMARY memory_monitoring=0` 时 global current/peak backing 观察字段为未采集的零值，不能解释为没有 backing。核心 control Stats 从真实 entries 查询，不受该零值影响。

## 保留的核心与检查

关闭后的入口仍有一次 bool/atomic enable 检查；部分调用点保留空 stack token 和必要 wire/layout 局部量。API wait 的大表和每线程 crash history 按需分配；剩余小型静态表/计数存储不更新。没有建立新诊断构建产品；Tracy 继续默认 compile-time 关闭。某些入口第一次调用会读取一次 Config 并缓存启动结果，没有周期 Config/UI 轮询。

保留真实 PageBlock registry、capability/safety、view LRU/预算、locks/transfers/pins、resource map、command UID、ordered Host ACK 和恢复同步。drop/remap/reconstruction failure 的少量普通整数是已公开控制状态，用户触发 GC 的 scan/skip/byte/ACK/drain 结果计数和计时仍存在；没有 diagnostic memory/queue atomics。FGC 等待语义不变，不解除游戏持有的锁。

保留 learned 内容指纹、创建来源 fingerprint、KEEP DB 读取/学习写入和 recovery hash 验证；它们决定分类、安全或恢复结果，不能作为 profiling 删除。恢复命名用 QPC nonce 保留；纯 readback/rebuild timing 只在 PageBlock diagnostics/reference test 请求时运行。GC 的既有 ACK/drain 计时按 ABI 保留。真正 queue timeout 和 readback event-query deadline 的时钟/轮询继续执行。

保留窗口 WndProc/Set/GetWindowLong 协作、游戏窗口/session 活动通知，以维持窗口/Reset 与超时正确性；它们不是 disabled Presenter-specific input hooks。单独启用 forwarding/message-pump/exclusive-input/Remix 时仍执行明确请求的功能。省略旧 DirectInput policy 保持上游缺省 2，完整全关需显式 policy=0；随包已是该组合。

Fatal handler 的一次性准备、有界故障时寄存器/堆栈/模块报告、peer exit、flush 和终止语义保留；关闭 history 后不再有命令/API 归因信息，故障时仍可能做地址/模块查询及创建 crash report。普通 startup/build/handshake/Device/Reset/shutdown、用户 GC/配置动作和真实 warning/error 仍写普通日志，正常帧间不产生可选周期观察日志。

## 验证

`scripts/test_runtime_observation.ps1` 使用生产 helper 和从生产文件提取的 startup/input/logger 函数，测试对象中拦截 Win32，并统计分配；release 没有测试 hooks。独立 OFF 进程 1000 次调用要求诊断 scan/clock/file/thread/hook/HWND/module/SRW lock/allocation 全为 0，内存/queue/history 无更新；不可解引用 Device 哨兵用于证明没有 Getter。随后调用真实 control ABI 的 GC handler，PagefileShadow + AGC 仍 evict 1 / release 4096 bytes；其 1 次 VirtualQuery 是实际 mapped view，结果计时属于用户请求结果。monitor-on/input-on/crash-on/logging-on 为正对照；OFF 后不能有新诊断日志。

基线对照在同一套 x64 MSVC/Wine 计数器中，仅重复原 sampler/queue 1000 次：关闭其他诊断的 v1.2.0 仍有 54 次 VirtualQuery、1 次文件创建、1000 次时钟读取和 1000 次 queue atomic 更新；新 OFF 路径这些诊断操作均为 0。扫描次数依地址空间布局变化，不作为跨机器性能数值。

第一轮运行时代码 `29a36bf4f37304e4b20e5d544804894150d5a529` 的 [Windows CI 37994479224](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/37994479224) 全部成功。构建使用 MSVC 14.29；本次 CI 生成本体/匹配补丁 artifact，未构建 L4N DLL/ZIP，也未替换 Release。运行时 build ID 为 `l4d2-1.2.0+4a3127cb7761dfc2`，不能与旧正式发布构件混同。该记录对应第一轮；PR #4 第二轮的代码与验证见下节。

| 执行内容 | 结果 |
|---|---|
| x86 Client DLL、x86 Host、x64 Host 完整原生构建/链接/打包 | 全部成功；本地 MSVC/Wine 初轮三目标也通过。 |
| 新 OFF 工作计数 + control ABI GC（x86/x64） | 两端各 1000 次调用，诊断扫描/时钟/文件/线程/hook/HWND/模块查询/SRW lock/堆分配为 0；内存/queue/history 无更新、没有新日志；AGC evict=1 / 4096 bytes，1 次 intrinsic mapped-view query。 |
| 新开启正对照（x86/x64） | Monitor 分别 scan=183/145、file=1、clock=1；input detour adapter calls=6 / setup=7；crash history entries=3；lazy log producers=2。 |
| Source 保护与默认配置（Python 3 项） | 通过；Volume、ABI、Reset helper、Host bootstrap 与 L4N 源码未改；原始 project 文本 hash 仅归一化 Git checkout 的 CRLF/LF。 |
| `test_pageblock_gc.ps1 -SkipPluginTests`（x86/x64） | learned/aggressive/force、KEEP/pins/VA/drop/current-content recovery、coverage；原 Config/设置持久化、Host/Presenter target、ABI 检查通过。L4N DLL callback fixture 本次按未改插件约定跳过。 |
| `test_exception_diagnostics.ps1` | Client/两种 Host 的异常归因、detailed、故障/坏记录、flush、peer attribution 与有界退出通过；开启 history 的旧 fixture 保持原结果。 |
| `test_device_reset.ps1`（x86/x64） | 失败/重试/timeout、隐式 surface 引用/有序销毁及 150000 次查询引用平衡通过。 |
| `test_color_diagnostics.ps1`（x86/x64） + color analysis 2 项 | 禁用/开启诊断、wire/hash/ring/file/异步退出与临时 COM 引用通过。 |
| `test_data_diagnostics.ps1`（x86/x64） + data analysis 16 项 | disabled/normal/extended/overflow/cap/periodic、生产 constants 比较与现有统计通过。 |
| `test_buffer_contract.ps1`（x86） | VB/IB 历史内容、多次 Lock/Unlock、部分/READONLY/DISCARD 与 FULL_SHADOW 契约通过。 |
| **原 `test_volume_layout.ps1`（x86/x64）** | **每端 59 项通过**：API byte pitch、wire、padding、partial box 和无效 stride；原测试/脚本保持不变。 |
| `test_diagnostics.ps1`（x86） | 显式开启的 memory/pageblock 观察、shadow lifetime、10000 次创建失败清理通过。 |
| `test_host_diagnostics.ps1`（x86/x64） | 显式开启的 inventory、VA/process/CPU/GPU-invalid-adapter、queue 观察通过。 |
| `test_x86_backend.ps1` | 官方 DXVK 2.6.1 x86 DLL 加载/导出通过；未以 DLL 加载冒充 GPU 渲染验证。 |
| `test_adapter_information.ps1` + `test_ati_texture_layout.ps1` | x86/x64 identifier/caps transport 与 ATI1/ATI2 guarded layout/upload/readback 通过。 |
| `test_overlay_presenter.ps1`（x86/x64 Host） | 跨进程 child HWND、捕获、Reset routing、resize、teardown 通过（fake ReShade addon）。 |
| `test_api_wait_diagnostics.ps1`（x86/x64） + analysis 6 项 | 启用归因/快照、禁用入口与原周期输出通过。 |
| `test_command_queue.ps1`（x86/x64） | idle/wait/timeout/wakeup、跨进程 x86→x64 队列通过；观测 fixture 显式开启 counter。 |
| `test_readback_recovery.ps1` | 独立 child-process readback、18 个格式恢复、25 个 mock readback、真实 backing deletion/hash/full mip/永久 KEEP/跨次 DB 命中/失败与 fallback 通过。 |
| release packaging Python 8 项；本地全部 Python 35 项 | 通过；L4N 分包规则继续有效，未重建插件。 |

首次 Windows run 的运行时 OFF/正对照已通过，但新增源码保护测试遗漏 UTF-8 和 checkout 换行处理导致失败；已修正测试后完整重跑成功。验收依据是操作调用停止与契约回归，没有 FPS 提升结论。

受保护源码哈希检查覆盖 Volume Client/Host UnlockBox、volume_layout、wire helpers、原 Volume 测试/脚本、Reset helper、Host bootstrap、控制 ABI 与插件；同时执行原 Volume 回归。native fixtures 和 fake backend 不代表实际 L4D2/DXVK 驱动已覆盖。

## PR #4 第二轮：状态与失败隔离

本轮审计见 [第二轮路径分类](RUNTIME-DIAGNOSTICS-AUDIT.md#pr-4-第二轮审计实施前)。变化只涉及 observer 存储/通知与失败边界，没有新增优化算法或更改策略、回收、恢复、Reset、Volume、IPC 及资源契约。

- API wait 的 64 线程统计表启动时为 null，仅显式启用且文件/事件/诊断线程创建成功后发布。失败前的临时表自动释放。成功启用后的表按诊断 worker/span 的原有进程寿命保留，防止 detach/free 与使用者竞争。
- Crash history 的 TLS 仅保留指针与失败标记；首次真正启用的 scope/command 才创建 history，并在正常线程退出时先清空已发布指针并禁止重新记录，再释放；退出后的诊断 scope 不访问已销毁状态。关闭入口和故障报告不创建 history；分配失败只跳过追踪。
- Data `Resource` 从内嵌 slot/kind/byte/usage 字段缩为单指针；首次启用 open 创建 metadata，失败不加入观察统计。Device 的 `m_dataKnown` 原本已按需，保持该实现。Volume 等 D3D 调用点未修改。
- VB/IB 实际 `new[]`/零初始化/`bad_alloc` 契约归于 Core `buffer_shadow.h`；`memory_diagnostics.h` 不再拥有 allocator，只观察 before/success/failure/free。真实生产 Buffer 模板回归不再用假 memory allocator。
- Retention 的 Core 初始化和诊断初始化分开。诊断 log 创建、写入或 callback 异常仅停用 log，不触发 fallback KEEP。KEEP DB 路径/校验/写入、恢复失败等真实 Core 故障仍保留原安全规则。
- Retention/residency 日志通知、PageBlock sidecar 观察、API/Debug/Trace producer、Color map 与 Host inventory 的诊断分配/通知异常被隔离；Data worker/退出摘要异常不能以未捕获异常终止 Bridge。诊断状态不持有 COM 引用。已发布日志回调失败时以原子标记停用，保留存储供在途调用使用；不在并发通知中清空或释放回调。Presenter/Steam 观察回调失败也不阻断已启用的输入状态转发。

仍保留开关/null 检查、空 timing token、小型 TLS 指针/标记、静态名字表和小型内存/queue 观察原子存储（OFF 不更新）。PageBlock nullable sidecar 与已有固定模拟观察表保留，未重构 core registry 或 residency gate。Core 指纹/DB、资源/锁/transfer 状态、超时与 intrinsic GC/恢复数据继续存在。

新增 13 个独立进程测试模式，覆盖 OFF/启用正对照、可选状态缺失与故障注入。故障注入和闭环：文件创建拒绝、诊断线程创建拒绝、诊断分配失败、retention 写入失败、抛异常的日志回调及其并发停用；使用生产 Runtime/Parent/Entry/Database 与 Host `runShared` 传输和独立 mock 数据源，验证 DB miss→Evictable→LGC 驱逐→preserve miss→恢复→KEEP→重新打开 DB 命中。另在 memoryMonitoring=False 下分别运行 AGC/FGC，要求仅实际 mapped view 查询，无 whole-process 扫描。真实 DXVK/L4D2 仍需实机验证。

本地 MSVC/Wine x64 的 13 个模式及 PageBlock/旧观察回归通过；x86/x64 fixture 编译通过。本地 Python 37 项通过（API wait analysis 6、color 2、data 16、packaging 8、源码保护 5）。

本轮最终 [Windows CI 38002144011](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38002144011) **全部通过**，验证提交 `86b577d1bedbe4f8196b04535e685bb7a63611e3`。其运行时补丁与 `62729f7` 相同，SHA256 为 `716f2d66161f9c9aa5ef24c6ef656ae8b9b6d216bfe6820af4a8c48725ebfed2`，build ID 为 `l4d2-1.2.0+716f2d66161f9c9a`。随后提交仅同步文档，不修改已验证补丁。

| 本轮执行 | 结果 |
|---|---|
| x86 Client / x86 Host / x64 Host 完整原生构建与链接 | 全部通过；生成本体与匹配补丁 artifact。未构建 L4N DLL/ZIP。 |
| 13 个观察测试模式（x86/x64） | 全部通过；OFF 1000 次调用的诊断 scan/clock/file/thread/hook/HWND/module/SRW lock/allocation 为 0，API wait 表、history 与每资源 metadata 均未创建。 |
| memoryMonitoring=False 的 Core allocation 与 GC | VB/IB 分配、零初始化、释放与 bad_alloc 契约通过；AGC/FGC 各 evict=1 / release=4096，每次仅查询 1 个实际 mapped view，无全进程扫描。LGC 在 LG 闭环中通过。 |
| LG OFF / log-create / log-write / callback-failure（x86/x64） | 四个模式均完成驱逐、Host 恢复、KEEP 提升、持久 DB 命中，fallback=0。使用独立 mock 后端内容，不冒充真实 DXVK 驱动验证。 |
| 初始化/分配失败与并发/线程退出边界 | 文件/线程失败不发布 ApiWait 表；诊断堆失败不改变 Core allocation 契约；失败回调停止后保持存储稳定；TLS history 释放后不重建、不访问旧指针。 |
| PageBlock policy/GC/settings/control ABI（x86/x64） | learned/aggressive/force、keep/drop、pins/transfer、真实 backing 卸载、恢复及旧 ABI 回归通过；未改插件 callback fixture 按约定跳过。 |
| 原 `test_volume_layout.ps1` | x86/x64 各 59 项通过；原脚本、测试和 Volume 路径未修改。 |
| x86 VB/IB production buffer contract | 历史内容、多次 Lock/Unlock、部分/READONLY/DISCARD 与 FULL_SHADOW 通过；采用 Core allocator。 |
| Reset / exception / color / data / 原 memory/PageBlock diagnostics | 原生测试全部通过；包括启用观察输出、引用平衡和创建失败清理。 |
| x86+x64 Host memory / adapter / ATI / Presenter / API wait / queue | 全部通过；跨进程 Presenter 使用 fake addon，原 queue 同步/timeout/唤醒不变。 |
| readback recovery | 独立子进程 18 个格式恢复 + 25 个 mock 回读、实际 backing deletion、全 mip 恢复、持久 KEEP、失败与 fallback 原规则全部通过。 |
| x86 DXVK backend / Python analysis + packaging + source checks | 官方 2.6.1 DLL 加载/导出通过；分组 Python 共 37 项通过。DLL 加载不等于 GPU 渲染验证。 |

中间验证发现了测试夹具对齐警告、日志回调复制契约及旧分配失败测试未更新 allocator 名称；已修正后完整重跑，未跳过相关回归或降低正式测试的 `/W4 /WX` 要求。

在审计及故障注入覆盖的诊断初始化、分配、日志和回调路径中，未发现残留的诊断失败改变 Core 策略/结果路径。真正 Core DB、身份 metadata、资源分配或 recovery 失败继续执行原有安全处理；没有将它们当作可忽略的诊断错误。开启观察时正常输出与统计语义保持原样；新增差异只发生于观察失败、未启用状态存储和线程退出后的 history 停用边界。

## 实机验证与后续边界

本轮 x86 实机日志的后续修正仅涉及 Client：取消以线程方式安装的 `WH_KEYBOARD_LL`（Windows 规定为 global-only），保留三个有效线程 hook 与 Host Presenter 已有的 foreground-filtered 全局键盘 hook；安装失败立即保存 Win32 error，卸载只处理有效 handle。没有新增 Client 全局 hook、Presenter 线程或输入路径。

DirectInput A/W 仍按原参数调用系统并原样返回 HRESULT。成功的非 7.0 请求只在显式 Debug 日志开启时显示原始版本值；不再用“Unsupported”误判调用失败或声称已验证所有旧接口。真正失败记录原始版本/HRESULT，观察异常不能改变结果。Query AddRef/Release 改用普通调用日志，移除上游遗留 missing-call 标记；引用计数、销毁 IPC 与 Host 资源释放未改。L4N 插件、Reset、PageBlock、Volume 和 Host 实现均未修改。

此修正的 [Windows CI 38007197537](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38007197537) 全部通过，验证提交 `4b07438271eaa3292c1dbfd957749cc88230316b`，build ID 为 `l4d2-1.2.0+8ce8005da14ea40a`。x86 Client / x86+x64 Host 构建、新增 x86/x64 生产方法回归、13 个观察模式及全部既有核心回归通过；本地 Python 37 项通过。L4N DLL/ZIP 按未修改组件约定跳过。随后文档提交不改变已验证运行时补丁。

这次实机日志还暴露了审计范围的一个剩余项：Host `SurfaceQueries::finish()` 仍累计 `count/mismatches`，这些观察计数尚未按诊断开关分离。本次三项 Client 修正没有处理它。实际 Getter、IUnknown 身份校验和临时引用 Release 是正确性工作，不能一并关闭；此前 OFF 测试的零计数结论仅适用于其覆盖的诊断入口，不能推导为全部 Host 路径没有观察计数。

仍需真实 L4D2 + DXVK 在 x86/x64 Host 上复测联机过图、Reset/切窗、所选策略和三种 GC/恢复；开 Presenter/Input 后复测已验证 ReShade 组合（x64 + Vulkan ReShade 6.0.1）及实际键鼠。验证 OFF 运行没有新 diagnostics 文件，再逐项启用观察确认需要的输出。

本次未清理上游整个 Remix 产品，也不改 DXVK 自己的 monitoring/HUD。若以后裁剪 compile-time diagnostics 或进一步消除空 stack token/固定表，需另行验证，不以这些存储或核心观察为理由删除正确性行为。Steam Overlay 的既有不完整支持仍为已知限制。
