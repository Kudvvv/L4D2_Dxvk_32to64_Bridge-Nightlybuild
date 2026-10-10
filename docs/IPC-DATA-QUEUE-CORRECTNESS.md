# IPC 数据队列正确性修复调查与验证记录

**当前建议：BLOCKED。保持 PR 为 Draft，不合并、不发布。**

最新生产修订的完整 Windows 构建、原生双向跨进程矩阵、故障/所有权回归和重复 A/B 均完成。正确性开发测试通过，但正常 IPC 热路径仍有明显可重复的额外成本，未达到性能门槛；不能因此认定可合并。当前环境没有 L4D2/GPU，游戏验收也尚未完成。当前累计补丁 SHA-256：`5651320c322ac731295e83cae5537a4ce3c4207362da88cbd730dfcf3c07520b`。

## 1. 基线与范围

- 正式版本：v1.2.1；从最新 main 的 `cf49175e8a3c6c2fe45c99aec0680b0d1c864d24` 建立独立分支 `codex/ipc-data-queue-correctness`。
- 上游：`9aa74f8dfad2188efbd0f717c64d9f8fa909787e`。
- 原始补丁 SHA-256：`8ce8005da14ea40a4a10d6d7be848be05ce8ac9da25676667fa67820178b87e3`。
- 一个 Draft PR：[PR #6](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/pull/6)。VERSION、正式 Tag/Release 均未修改。
- 使用仓库源码准备流程，另以 detached worktree 保存原始补丁对应的生产源码；未使用此前绑定过滤或 VB/IB 成本调查的工作区。
- 已阅读任务指定的七份文档、累计生产补丁及应用后的相关实现。旧 v1.1 计划只作调查入口。

本次不实施绑定同值过滤、VB/IB 零拷贝、FULL_SHADOW 缩减、DXVK 修改、GC 策略变化、Overlay 修复或 Host 重连。逐文件比对基线：237 个生产文件相同；变化集中在队列、分派、构建头文件列表以及任务要求的 D3D9 错误传播边界。`pageblock_residency.h`、`retention_policy.h`、Volume 布局 helper 和 ATI 布局 helper 保持相同。

## 2. 当前生产缺陷确实存在

### 丢失进度的等待

实际调用链：D3D9 API → `ClientMessage`/`Bridge::Command` → `send_data` / `send_many` / `begin_data_blob` → `syncDataQueue` → `CircularBuffer`。

原 `syncDataQueue` 首先读取普通共享 `int64_t serverDataPos`，随后缩窄到 `int serverCount`，最后才通过普通共享 `clientDataExpectedPos` 登记等待。Host Device 分派结束后更新消费位置、判断登记状态并释放 semaphore。登记后的空间条件没有重新读取，允许“Host 已消费但没有看到等待登记，Client 仍进入等待”的时序。共享 64 位位置还缺少 x86 原子访问保证。

原 Module 消费分派没有对应的进度发布；Host→Client 回复也不能直接套用仅更新 Device 正向消费位置的旧逻辑。需要修复双向通道生命周期，不能仅在 Client 原等待函数加一个条件。

### 同步失败仍写入和发布

原 `syncDataQueue` 返回 `void`。等待超时/系统失败达到重试次数只写日志，后续 serializer 仍写数据。Command 析构仍自动向 command queue 发布 Header，外层异步 API 或上传 helper 可继续报告成功。日志中的“overwrite condition resolved”不代表空间条件成立。

旧 CircularBuffer 的长度前缀、连续 Blob、尾部 skip 与 sync 空间估算分散；尾部恰好相等使用 `>=` 的绕回行为也必须统一。单独检查 payload 大小不足以覆盖 UID、长度字段、padding 及同批多次写入。

### 生产修改索引

以下路径相对于准备后的 `bridge/src`；完整增量见累计补丁，测试提取脚本会记录源哈希。

| 文件/入口 | 修改目的 |
|---|---|
| `util/data_ring_contract.h`、`util_circularbuffer.h` | 统一 reservation、`push` / `push_many` / Blob 与 `pull` 的对齐、padding、overflow 行为 |
| `util_ipcchannel.h`、`util_commands.h`、`util_atomiccircularqueue.h` | 64-byte control 初始化、整环 Header flag、有界 Header push |
| `util_bridgecommand.h/.cpp` | Command 构造/serializer/finish/析构、`syncDataQueue`、`startRead` / `ensureRead` / `end_read_data` / `pop_front`、poison 与 pin |
| `server/main.cpp`、`module_processing.cpp` | Device/Module 在 handler 完成后统一消费；同步/继续命令不绕开 UID；optimized VB/IB 的 Lock/Unlock/Destroy pin 生命周期 |
| `client/lockable_buffer.h`、VB/IB、Surface、Volume | `Lock` / `Unlock`、`sendDataToServer` 返回并检查提交结果；保留失败前 backing/lock 所有权 |
| `client/d3d9_device*.cpp`、Module、Texture/Cube/VolumeTexture、SwapChain、Query、StateBlock | 创建/响应异常清理、fault guard、别名引用和输出、Present/Reset 边界；仅本地 Getter 的正常规则保持 |
| `client/d3d9_surfacebuffer_helper.h`、`readback_recovery.h`、`pageblock_runtime.h`、`retention_runtime.h` | Readback 长度校验、请求提交失败停止；不进入完成等待或推进成功/可回收状态 |
| `client/d3d9_lss.h/.cpp`、`util/meson.build` | 原全局 running 改 atomic、启动设置一次 build identity、纳入 helper 头文件 |

原文档只讨论 Device 正向数据位置的假设不足以覆盖当前 Module 和回复；“默认 optimized Lock 字段值为 false”也不能说明运行时不可启用，该构造路径受既有选项控制。本次针对实际指针生命周期保留保护。

## 3. 修订的核心不变量

使用单调 DWORD 逻辑游标：`consumed <= published <= reserved`。可继续预留的必要条件是 `reservation.end - consumed <= capacity`，同时本批累计占用不得超过容量；发生溢出、过大申请、故障或取消即拒绝。未发布的预留空间也是占用，不回退后悄悄复用。

`data_ring_contract.h` 的统一 helper 计算标量、长度前缀、DWORD 对齐和 Blob 连续区域；舍弃的环尾 padding 计入占用。生产 serializer 使用本地已知环位置，避免 x86 热路径的 64 位取模。helper 的便利测试入口与这一入口做等价比较。

复用原通道开头 **64 字节**保留区：magic、protocol=2、layout bytes、capacity、fault、waiting、published、consumed、writer PID 及保留字段。共享块没有增长，Header 仍为 12 字节。32/64 位 atomic 的尺寸、偏移、对齐和始终 lock-free 均有静态断言。整环批次通过一个 Header flag 区分“末位置相同但占满一圈”和“空 payload”。

新旧配对拒绝有两层：原有启动构建 ID 包含补丁哈希，Host 在启动握手前拒绝不匹配构建；新 reader 还在取得 Header 后校验 control magic/version/layout/capacity。后者不能代替前者，旧 Host 本身不会理解新 control。

### 等待的次序

1. 使用保守缓存的 consumed 尝试快路径。
2. 真正不足时以 SC store 登记 waiting。
3. SC 重新读取 consumed，并重算完整预留条件。
4. 条件不成立才进行至多 25 ms 的 OS 等待片段；整体预算按现有配置计算，0/溢出不能变成无限等待，最多 120 s。
5. 每片之后检查取消、fault 和空间；系统等待失败及到达期限也作最后一次条件检查。
6. 消费方先 SC 发布 consumed，再 SC 检查 waiting、尝试通知。

两侧的登记、发布和相对重查形成 SC 顺序，不能同时遗漏对方的操作。通知只提示重查，重复、合并、丢失的 token 不能授予空间。Header 发布也使用有限预算，满队列时短暂阻塞，避免原 timeout=0 造成无限 yield 重试。没有扩大生产队列。

### 数据何时可以释放

Host Device/Module 必须在实际 handler 完成后验证 cursor 到达 Header 指定的完整批次末尾，再发布 consumed。回复由 Client 复制/读取完整 payload 后完成消费。

Client 最新修订在移除回复 Header **之前**完成 payload 消费；下一个匹配 UID 的等待者通过既有 command queue release/acquire 次序观察完成状态。设备创建原先的 early-pop 改为先读取 HRESULT。这里没有添加回复 mutex。低层 `Any` 消费仍遵循单消费者契约，不能把它解释为支持任意并发消费者。

可选 optimized dynamic Lock 把 IPC 指针保留到后续 Unlock：这类指针不能在 Lock handler 结束时释放。Host 对这类活跃指针保留最早 cursor，Unlock 完成使用或资源销毁后解除；正常 FULL_SHADOW 路径没有此 pin 分配。该路径可能产生真实背压，但不能通过提前释放掩盖它。

## 4. 提交及 D3D9 失败边界

Command 保存提交结果、完成标记、起始 cursor 及构造时异常计数。`finish()` 幂等，仅完整构造、通道健康、Blob 已闭合且非异常展开时发布。reserve 或写入失败后停止后续写入；Blob 申请返回 null；失败批次不发布 Header。Header 发布失败可以留下不可继续使用的 reserved/published 数据，但通道立即 poisoned，不会让新批次复用。析构的故障报告不得抛异常或遗留既有 Client mutex。

| 路径 | 本地修订的失败行为 |
|---|---|
| VB/IB | Lock 不输出失败的 IPC 指针；Unlock 返回提交 HRESULT；失败时保留 lock record、Shadow 和 discard 所有权；不改 DISCARD/NOOVERWRITE 的原上传内容 |
| Surface/ATI | blob/copy/finish 失败提前返回；不 pop lock、不释放 discard、不推进 uploaded；Transfer RAII 保留 backing 生命周期；ATI 格式/范围检查保留 |
| Volume | buffer 与 lock record 在 finish 成功前保留；layout/行复制/字节 pitch 不变；预留失败返回 DEVICELOST |
| 资源创建 | 已创建的 Client wrapper 在提交/回复失败时清空输出并 Release；不追加正常异步 Host 等待 |
| Getter/别名 | 涉及转发的 RT/depth/backbuffer 失败释放已经增加的外部引用；纯本地 Getter 保持原本的引用规则 |
| StateBlock | Begin 失败清理 recording；End 提交失败不转交输出；已经转交但回复失败则清空并 Release |
| Readback | 先验证返回 Blob 和尺寸，再复制；不完整读取触发通道故障，COM 边界返回受控失败 |
| PageBlock / Retention | 两套 Runtime exchange 均在提交失败时立即 DEVICELOST，不进入完成事件等待；原 ACK/恢复策略保持不变 |
| Present / 后续设备调用 | 观察到通道故障后返回 DEVICELOST；原本的异步成功不被转换成无条件同步 RPC |

一次故障日志记录运行 GUID、构建 ID、协议、通道、自身及对端 PID、命令及 UID、申请 words、capacity、reserved/published/consumed、等待起点/时长、进度是否变化及对端存活查询结果。对端存活为 unknown/yes/no，与进度变化分别记录；不把 alive 当作正在处理。正常提交不格式化该日志，不增加诊断线程。

## 5. 原生测试证据

开发测试提取实际生产实现，边界适配器并不等同于 GPU 或游戏执行。

| 证据 | 结果与边界 |
|---|---|
| 原 v1.2.1 生产控制流，Windows x86/x64 | 1000/1000 次登记前进度竞态仍等待；超时和系统失败后仍写入并发布。测试成功表示捕获旧缺陷 |
| 统一 helper / ABI，Windows x86/x64 | 各检查 **70,631,385** 个空间状态；通知不是许可、登记后重查、cached-position 等价、overflow、大小/对齐和 ABI 拒绝均通过 |
| API 所有权，Windows x86/x64 | 提取实际 VB/IB/VS/PS/StateBlock 创建、Begin/End，提交失败、回复失败、读异常及正常异步/同步；每次 `released=25`、无失败成功返回、无输出引用泄漏 |
| 原生 x86→x86 / x86→x64 | Device/Module 正向各 100001 包，反向抽样及最终回复；128 DWORD 小环、多 Blob、零长度、字节完整性/UID/顺序通过 |
| 原生多线程 | 四线程各队列 4000 次提交及最终回复；另四线程各队列 4000 次同步匹配 UID RPC 及最终回复；两种 Host 位数均通过 |
| 原生 serializer | 容量 2..67 DWORD、全部起始位置、0..capacity*4 的 Blob，共 412313 个 native case，实际 push/pull、canary、无效申请无游标移动通过 |
| 原生故障 | 超大、停止消费超时、部分批次、满 Header、Win32 等待失败、真实子进程正常/异常退出、协议错误均断言停止写入/发布和有界结束 |
| Host 活跃指针 | x86/x64 pin → 多批消费 → Unlock 解除及 Destroy 清理，消费位置和 payload 生命周期断言通过 |
| Buffer contract | 动态 FULL_SHADOW 历史内容、多 Lock、失败 Unlock 保留所有权、失败 Lock 不输出 IPC 指针通过 |
| Runtime 请求提交失败 | 实际 residency 与 retention exchange 无等待、无完成推进、原 backing 保留、100 次 Temporary 句柄平衡通过；retained-reference 生产入口提交失败只尝试一次、停止后续 repeats、无恢复成功通过 |
| 既有回归 | Reset、Volume 59 项、ATI、Readback/Recovery、PageBlock/Retention、Input/Overlay、诊断默认关闭、DXVK x86 原生 DLL 加载、原生 command queue、Python 均通过完整 Windows job |
| Python 总回归 | 本地 **39 项通过**；Volume Lock/layout 保留独立哈希保护 |
| L4D2 启动/过图/Reset/退出 | **未运行**，当前环境没有 L4D2/GPU |

完整生产构建和上表已通过项目的证据为 [run 38036943950](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38036943950)，提交 `84ff2d9482915a1166ae3a0e8d627c5240b497e6`；此 run 的两个 job 最终均成功。[run 38037222599](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38037222599)（`b160540e`）全部成功，包含修正后的 retained-reference 用例。最终 [run 38037527938](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38037527938)（`086ab720b3c43ebe4ba8ac7545e34c0c9bc41aad`）两个 job 全部成功，包含快路径修订和 reference 用例。CI green 表示测试命令完成，不表示性能幅度已可接受。插件源码未变，跳过无关 L4N 插件重建；不声称重测插件运行环境。

旧复现 fixture 提取旧 Command、serializer 和 sync 决策，用可控队列/通知边界重放竞态。新跨进程 fixture 用实际 SharedMemory、NamedSemaphore、AtomicCircularQueue、CircularBuffer、Command 及读写生命周期；仅配置/logger、应用分派、退出信号和故障注入为适配器。故障注入不改生产 semaphore；提取生成 source-manifest。

验证过程有失败记录，均保留 CI：最早 PowerShell 没有正确收集子进程退出码，改用 Python；util 库误 include 生成的 version.h，改为启动设置 build identity；API fixture 重复 exception/UID 定义，改用生产类型。四线程 RPC 用默认 2 s 的 wrong-UID sleep 超出整组期限，测试改配置为 1 ms、2000 次上限，**没有减少调用量或数据断言，也没有改变生产策略**。新增 reference 用例曾使用不受 Selection 支持的 64×64，改为生产支持的 256×256，没有放宽选择逻辑。较早失败不能作为最终通过；对应修正由后续 run 复核。

## 6. 性能方法、首轮结果与成本

### 条件和测量范围

Windows Server 2022 runner（系统报告 `Windows-10-10.0.20348-SP0`），AMD64 Family 25 Model 1，4 个逻辑 CPU；同一个 job、MSVC 14.29 `/O2`、x86 Client/x64 Host、诊断关闭。每场景 A、B 各一次预热，11 轮交替 A/B 与 B/A。计时仅在批次外层；记录 wall、GetThreadTimes CPU、QueryThreadCycleTime cycles 和 Client 端到端完成时间。原始样本、源哈希和完整 summary 在 run 的 `ipc-baseline-evidence` 构件中。

批次无竞争场景先完成 Client 提交，再允许 Host 消费；测试 arena 为 32 MiB，批次小于半环。不改变游戏容量。连续/绕回并发消费；近满载使用 4096 DWORD 中 4080（99.6%）；慢 Host 每 64 包 Sleep(1)。Host 校验传输 metadata 和 payload 首末字节，**没有运行 D3D9/DXVK、GPU 或完整 Host 分派**。独立数据完整性测试检查全部字节。

短批次 wall 仅数毫秒，线程 CPU 时间的约 15.625 ms 量化会产生 0 或一个 tick，不能把 0 解释为没有 CPU 成本。因此同时报告 cycles；其差异可验证额外执行成本，但不能转换为游戏 FPS。500 ms idle 仅评价 Host 空队列等待，Client 的空循环“每 call”数值没有提交含义。

### 首轮测量发现明显正常路径退化

[run 38036943950](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38036943950)，生产补丁 `da55bdcf25acf96b...`，均 11 个有效配对：

| 场景 | Client A→B 中位 ns/包 | Host A→B 中位 ns/包 | 配对 Client wall 变化（中位，min..max） |
|---|---:|---:|---:|
| 空 Blob 批次 | 102.7→188.0 | 34.5→141.4 | +83.1%（−1.2..+85.2%） |
| 64 B 批次 | 124.5→230.4 | 36.3→139.6 | +85.0%（+80.1..+90.3%） |
| 1 KiB 批次 | 423.7→536.1 | 39.9→151.9 | +25.7%（+21.8..+36.0%） |
| 4 KiB 批次 | 1349.9→1484.6 | 41.2→169.0 | +10.0%（+5.1..+35.9%） |
| 64 KiB 批次 | 20063.7→20063.7 | 66.8→206.8 | +0.23%（−2.22..+5.73%） |
| 连续 64 B | 241.0→348.0 | 240.1→347.6 | +43.4%（+37.5..+140.6%） |

64 B 批次 Client cycles 中位 304.7→564.0；Host 89.1→341.5。差异不只是调度等待。该结果不满足“没有明显退化”的门槛，不能因 correctness 用例通过就交付为可合并状态。

原 A 的绕回 11 次中 1 次超过 8 s 整组期限；慢 Host 11 次均超过期限，B 均完成。失败样本没有有效性能值，不计算速度提升比例；超时样本本身也不能精确定位其卡住阶段。B 慢 Host 中位端到端 2.875 s，主要为调度阻塞；线程 CPU 量化为 0，cycles 非零。

### 消除不必要成本的尝试

`086ab720` 将 syncDataQueue 的已缓存空间检查及 ensureRead 边界判断移入头文件，真实等待/首次取 Header 才调用慢函数；避免已 active 的重复 startRead ABI 检查。这样让 MSVC 跨原生产 translation unit 内联，也允许合并紧邻 serializer 的重复 reservation 表达式；**没有删除 reservation、批次跨度、完整 payload、overflow 或失败检查，没有降低原子同步要求**。以下为该生产修订的最终 native A/B。首轮与最终测量分属两个 runner，只能使用各自同机配对判定 A/B，不能把 B 的跨 run 差值解释为确定的优化收益。

### 最终配对结果：仍有性能阻碍

[run 38037527938 的原始证据](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38037527938/artifacts/11664630837)：240 个样本（10 场景 × 2 variant × 12 次含预热）；正常和绕回均 11 个有效配对。下表单位为 ns/包，中位数后括号为 min..max；百分比来自各轮配对，不能用两个独立中位数重新计算。

| 场景 | Client A | Client B | Host A→B 中位 | 配对 Client wall Δ 中位（min..max） |
|---|---:|---:|---:|---:|
| 空 Blob 批次 | 102.4（101.5..115.5） | 183.9（179.7..201.4） | 35.4→138.8 | +79.4%（+64.1..+90.2%） |
| 64 B 批次 | 122.3（121.0..128.7） | 221.2（219.5..224.3） | 39.1→134.8 | +81.2%（+72.4..+85.3%） |
| 1 KiB 批次 | 405.0（400.3..506.7） | 524.2（511.3..537.7） | 41.5→137.7 | +27.4%（+6.0..+31.0%） |
| 4 KiB 批次 | 1276.3（1259.3..1345.3） | 1407.8（1387.9..1477.6） | 40.6→160.8 | +9.8%（+3.9..+16.2%） |
| 64 KiB 批次 | 18818.4（18570.0..18970.5） | 18983.2（18776.8..19750.5） | 66.8→193.7 | +1.5%（-0.8..+4.5%） |
| 连续 64 B | 241.2（191.2..281.3） | 343.6（337.3..353.4） | 240.6→343.1 | +42.4%（+22.7..+76.4%） |
| 99.6% 占用 | 149.0（146.1..158.3） | 248.5（245.6..260.8） | 52.5→182.4 | +65.7%（+58.7..+75.6%） |
| 4096 DWORD 绕回 | 233.9（199.5..241.8） | 334.8（324.4..347.5） | 233.4→334.2 | +44.1%（+35.8..+72.4%） |

64 B 无竞争批次 Client cycles 为 **299.2→541.3**，Host **95.4→329.8**；连续场景分别为 **588.8→839.6**、**584.4→836.6**。64 B 批次 Client 的端到端中位 **163.7→356.9 ns/包**；连续端到端 **241.3→343.7 ns/包**。无竞争传输 wall 增量约为 Client 99 ns、Host 96 ns/包，cycles 的增加确认其中包含实际执行开销；受 CPU 时间量化限制，不把这两个 wall 差值宣称为精确 CPU ns。批次串行完成增加约 193 ns/包；并发连续传输约增加 102 ns/包，不能把两侧百分比相加。

64 B 批次最终配对 Client **+81.2%**，连续 **+42.4%**，绕回 **+44.1%**；cycles 同样增加。64 KiB 的 Client 配对 +1.53%（−0.82..+4.50%）在波动内，不能宣称性能提升或完全没有额外成本。这里观察的是最小传输处理，Host 相对百分比很大，完整 D3D9 分派和 GPU 工作会改变占比。

慢 Host：A 的 11 个正式样本均超过测试的 8 s 期限，B 11 个全部有效，端到端中位 **2.891 s**（2.843..2.936 s）/12000 包；无合法 A/B 比例。B cycles 为 Client 1406、Host 1911/包，wall 大部分是 Sleep/背压，不能拿 wall 当 CPU。

Idle Host：A 495.340 ms（479.972..497.889）、B 495.938 ms（494.436..510.567），线程 CPU 两者均量化为 **0 ms**；总 cycles 中位 A 800807、B 862449，范围分别 711387..1040736、741787..1068467，重叠明显，没有显示新的常驻忙循环。0 ms 仍不是严格零 CPU。完整 CPU/cycles、Host min/max 和端到端范围保存在 summary/raw。

这些 min/max 是观察波动范围，不是统计置信区间。两次同机配对都显示小命令正向退化；有限快路径调整没有消除它，不能用诊断关闭、额外同步或略过边界检查掩盖。

无法把旧的普通共享 64 位位置、失败后继续写入或提前释放数据作为更快的合法替代方案。成功提交 published、完成消费 consumed、等待登记与重查的同步承担正确性职责。沿用现有 Command mutex、信号量和 Header wake event；不新增逐调用时钟、正常路径 OS 等待或一般 payload 分配。optimized Lock pin 是特殊生命周期状态；普通路径没有活跃 pin 节点分配。

成本模型：`ΔCPU ≈ N_client × Δsubmit + N_host × Δconsume + Δ阻塞/缓存竞争`。每个包有 UID、metadata 和 Blob，此处不能用它直接代表所有 D3D9 API。游戏帧时间还取决于 Host/Client 并行、GPU 和等待位置；尚无每帧命令分布和实机数据，不能声称固定 FPS 降幅或提升。复测仍存在明显退化，已保持 BLOCKED，把幅度和必要性交由用户审核。没有增加新锁或复杂状态机继续扩大范围。

## 7. 原生复现命令与实机交付门槛

在具备 Visual Studio 2019 v142 14.29、Windows SDK、Python 3.11 的 Windows 环境，从本 PR 分支运行：

```powershell
python scripts/prepare_bridge.py
./scripts/test_ipc_baseline.ps1
./scripts/test_data_ring_contract.ps1
./scripts/test_ipc_api_failure.ps1
./scripts/test_ipc_transport.ps1
./scripts/test_ipc_performance.ps1
./scripts/test_runtime_observation.ps1
python -m unittest discover -s tests -p 'test_*.py'
```

完整相关构建和旧回归由 `.github/workflows/ipc-correctness.yml` 执行，`windows-build` 产出 `ipc-correctness-paired-test-build`。本地脚本进一步扩充的用例必须随最新源上传后重跑，不应只运行旧 SHA。

最新配对测试构件：[ipc-correctness-paired-test-build](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/38037527938/artifacts/11664263515)。它对应 `086ab720b3c43ebe4ba8ac7545e34c0c9bc41aad`，构建 ID **`l4d2-1.2.1+5651320c322ac731`**，`gameplay_validated=false`；已下载核对包内累计补丁哈希、三个文件的 SHA-256、PE 架构及嵌入 build ID。

| 文件 | SHA-256 |
|---|---|
| `bin/dxvk_d3d9.dll`（x86 Client） | `e37bb6212dac5ed81ab29dd6a56d7cefbfeb7aaa73de5d860c9bd1cbb3f9ca2a` |
| `bin/.l4d2bridge/L4D2Bridge64.exe` | `2e41d385dd63014b592f1c45d9059898c90fdf2623c46a2c23aee34ea123eb57` |
| `bin/.l4d2bridge/L4D2Bridge32.exe` | `cc390496133f59c6ddfeeb46d0180e7754d21abe6deaf951ee0c9f3369464bcf` |

构件 ZIP 的 GitHub digest 为 `sha256:3ac34a9e35c9619d71e693aa46cba5c2d80b559127bc09473e03acda49a475fb`。原始证据 ZIP digest 为 `sha256:ac2a2304ed6aa8dabd25dd770ba92441d3571e72dd75b22f572291bfdaa2db58`。构件不是正式发布；报告更新只改文档，验证源与包的提交以这里所列为准。

测试构件是基于已有 v1.2.1 安装的配对更新包，不是全新完整安装包；DXVK 与根目录启动链保留既有版本。包内 BUILD-INFO 的 distribution 字段沿用现有打包默认值，GitHub 没有创建 Release，`gameplay_validated=false`。

在当前 BLOCKED 状态下，构件供审查和后续受控验收，不能作为正式更新推荐。若用户接受剩余成本并开始游戏测试：

1. 完全退出游戏与 Host；备份 `bin/dxvk_d3d9.dll`、整个 `bin/.l4d2bridge` 和原配置。
2. 从同一个 paired 构件替换 Client DLL、`L4D2Bridge32.exe`、`L4D2Bridge64.exe`；核对 BUILD-INFO / SHA256.json，保留 backend DLL、bridge.conf 与 retention DB，禁止混用旧 Client/Host。
3. `forceX64Server=True`；先 `client.testX86Server=False` 跑 x64，之后完全退出，改为 True 跑 x86；其余设置、地图、MOD、画质、上限与诊断状态保持相同。
4. 各跑正常进图/游玩、退图重载、连续至少 5 次过图、大量资源创建销毁、窗口切换/Reset、正常退出；记录每项成功或失败，不能只写“能启动”。
5. 启动后检查两侧相同 `Project build`；每轮保存 `bridge32.log` 和 x64 `bridge64.log` / x86 `bridge-host32.log`、对应 DXVK 日志。故障时保留 `IPC_DATA_FAULT` 前后日志、地图/切换序列、位数和发生时间。失败后不要把同一 poisoned 进程的继续调用当作正常运行，重新启动属于下一轮。
6. 如要比较游戏性能，用同地图/演示、相同安装配置做重复交替运行，报告帧时间分布；该游戏对照尚未执行，不能用 native ns/包代替。

没有自动开启大范围诊断，没有删除 DB，没有改 retention 策略，也没有自动安装到用户游戏目录。

## 8. 最终状态与继续条件

累计补丁上传曾被自动审批拒绝，原因是累计文件包含基线已有的其他功能。逐文件确认范围后，用户明确授权更新累计补丁并继续原生验证；此阻碍已解除。保留全部基线内容，未绕过审批。

最终建议为 **BLOCKED**，原因是明显、可重复的正常 IPC 路径退化，不是未取得测试结果。必要 Windows 原生 correctness 与既有回归已通过，有限成本削减也已尝试；剩余原子发布/消费、批次和读边界检查承担具体正确性职责。本次不通过删除检查、引入新回复锁、扩大环或更多复杂状态来换取表面通过。

替代选择是：继续在本 Draft 审查传输快路径以验证是否还能合并重复 reservation；或用户明确接受报告中的正确性成本后开展上述实机对照。后一选择仍不等同于 READY FOR REVIEW，也不能未经游戏证据声称过图卡死已经修复。当前不建议合并，不推荐作为正式玩家更新。

PR 始终为 Draft，main、VERSION、Tag、Release 均未改变。只有性能阻碍解决/经用户明确接受，且开发侧证据成立，才能进入 **AWAITING GAME VALIDATION**；实机验收完成后才可建议 **READY FOR REVIEW**，最终合并仍需用户批准。
