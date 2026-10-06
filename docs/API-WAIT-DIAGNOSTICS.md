# 地图加载 D3D9 API / IPC 等待诊断

这是默认关闭的诊断功能，用来判断加载期间的时间是否花在 Bridge 的资源 API、响应等待或队列背压上。它不识别 Source 地图事件，不实现异步加载，不改变 D3D9、PageBlock retention、Host 选择、IPC 协议、输入、ReShade 或渲染语义。尚无本功能的实机加载 benchmark；下面只有测量方法和实现事实。

## 安装与启用

1. 完全退出游戏和桥。安装 `l4d2-bridge-api-wait-diagnostics` 包，将包内 `bin` 合并到游戏根目录。包更新匹配的 x86 客户端、x64 Host 和 x86 Host；不包含 DXVK 后端 DLL 或覆盖用的 `bridge.conf`。保留官方或 mem1 后端、当前 Host 模式和内存策略。
2. 将以下内容合并到现有 `bin/.l4d2bridge/bridge.conf`，每个键只保留一项：

   ```ini
   client.apiWaitDiagnostics = True
   server.apiWaitDiagnostics = True
   client.apiWaitSnapshotMs = 1000
   server.apiWaitSnapshotMs = 1000
   ```

   两个诊断开关缺省均为 `False`。快照周期缺省 5000 ms，支持 1000–60000 ms（超界值夹到边界）；它不是 IPC 超时。加载测量推荐 1000 ms；日常游戏关闭诊断。无需开启 `logApiCalls`、`logServerCommands`、PageBlock detailed、强制 readback 或 Steam 输入实验。
3. 重启游戏，确认 `bridge32.log` 和对应 Host 日志分别出现 `L4D2 API wait diagnostics enabled`。初始化失败时不会启用计时，应检查目录是否可写及日志信息。
4. 日志自动生成在各自模块目录，PID 防止不同会话覆盖：

   | 文件 | 位置 |
   |---|---|
   | `l4d2-api-wait-client-<PID>.log` | 游戏 `bin` |
   | `l4d2-api-wait-host64-<PID>.log` | `bin/.l4d2bridge`，x64 模式 |
   | `l4d2-api-wait-host32-<PID>.log` | `bin/.l4d2bridge`，x86 模式 |

   这些是独立日志，不依赖 INFO 逐调用打印，也不会修改 `DXVK_LOG_PATH`。加载期间没有 Present，快照仍能由独立诊断线程写出。测试结束前至少等待两个快照周期，再保存日志；强制结束可能丢失最后一个不完整快照和仍未返回调用的最终耗时。

关闭：将两个 `apiWaitDiagnostics` 设置为 `False`（或移除），重启。保持其余设置。默认关闭时不启动线程、不创建日志、不调用 QPC、不更新计数；计时对象只做启用标志检查。可选诊断线程与日志句柄存活到进程结束，客户端模块仅在诊断模式下被 pin，避免卸载代码后线程继续运行或在 loader lock 下 join。

## 推荐 L4D2 实机 A/B 流程

1. 使用固定的 Cold Front 地图/章节、当前约 9 GB MOD、同一 DXVK（官方或 mem1）、Host 位数、retention policy、驱动、图形设置和帧率上限。记录实际版本与配置，不换后端或 MOD 后再称为同场景对比。
2. A 轮关闭这两个诊断开关；B 轮只开启它们。分别从新进程进入主菜单，等待稳定，再用相同入口加载同一地图。先验证诊断本身是否明显改变加载时间或稳定性。不要开逐 API/逐 command 日志。
3. 外部计时或录屏记录“触发加载”和“可正常操作游戏”的实际时刻及加载 wall time；Windows 无响应出现/恢复也可标记。Bridge 的 `Present` 不等于 gameplay begins，菜单、加载动画也可能 Present。不要以首个 Present 自动结束测量。
4. 测量前、可正常操作后各等待两个快照周期，保留对应时间段的两份诊断日志、`bridge32.log`、Host 日志、实际加载起止时刻与独立 wall time。日志同时记录本机时间及 `tick_ms=GetTickCount64`，便于选取边界。无需 ETL 或其他进程采样。
5. 冷启动和暖缓存分开记录。重复数次并交替 A/B 顺序，说明 Windows 文件缓存、DXVK shader cache 是否保留；重启游戏不等于清空 OS 文件缓存。不要主动改资源策略或清理缓存来制造新变量。
6. 先看实际调用线程的数据，再看全部线程。跨线程时间之和可能大于加载 wall time；Client 的等待和 Host 的处理也可能覆盖同一段时间，不能再相加。只有持续、可归因的等待占比较大，才值得讨论同步路径；一次结果不自动说明应该异步化。

## 快照与区间分析

每轮输出 `L4D2_API_WAIT_SUMMARY`、按线程/API/metric 的聚合行和 `L4D2_API_WAIT_END`。完整 END 才标记完成快照。计数从诊断初始化累计，不 reset，不建立 Source-level loading state。后台读取不暂停任何 producer，快照是近似值；不同字段不是全局原子快照。

使用 Python 3（包内带 `analyze_api_wait.py`）：

```powershell
python .\analyze_api_wait.py --client .\l4d2-api-wait-client-1234.log --host .\l4d2-api-wait-host64-5678.log
```

这里的 PID 是示例占位，替换为实际文件名。默认比较各自第一与最后完整快照，**这只是进程区间，不是自动识别的地图加载时间**。加载区间明确后，可用日志中同一台机器的实际 tick 边界：

```powershell
python .\analyze_api_wait.py --client .\client.log --host .\host.log --begin-tick-ms <实际起点tick> --end-tick-ms <实际终点tick> --observed-loading-ms <独立计时毫秒数> > .\api-wait-result.json
```

尖括号参数需替换成数字；第二条是参数模板。脚本为两个进程分别选择最近的完整快照，显示实际区间、边界偏差、进行中调用和丢弃线程数；不允许边界超出日志范围，不接受混合 PID 会话。若要固定一个实际调用线程，加 `--client-thread <实际TID>`。所有 TID 均来自测量，不自动称最大耗时线程为 Source 主线程。

`total_us`、calls、slow bucket 做累计差值；区间 avg 从 inclusive 差值重新计算。`max_us` 是进程生命周期峰值，不能相减成区间最大值，分析输出因此明确命名 `lifetime_max_us_at_end`。不输出未经证明的 p50/p95/p99。

## 各指标的含义

| metric / 字段 | 测量内容与限制 |
|---|---|
| `api` | Client 顶层已插桩 API wall time，Host 对应 command handler wall time。calls/total/avg/max/阈值桶均保留。不是 CPU usage 或 GPU time。 |
| `ipc_submit` | 构造 Command → 销毁后提交/解锁的范围，含序列化及上传数据复制。exclusive `total_us` 去掉其内嵌的已测等待；不是纯 IPC syscall 开销。 |
| `server_response_wait` | Client 的 `waitForCommand` 和响应 `pop_front/pull` 调用范围，包含 UID 验证、现有重试/调度。调用可立即成功，wait calls 不等于阻塞次数；不包含 Host 空闲等下一条 command。 |
| `data_queue_full_wait` | `syncDataQueue` 已触发覆盖风险时，原有 data semaphore 等待循环。是真实数据队列空间等待，不是从 API total 推算。 |
| `command_queue_full_wait` | AtomicCircularQueue 已检测满后的等待区间，到空间可用或超时。calls 即实际 full episodes；一个 push 的多次检查不反复计数。它保留现有 yield/timeout/wake 行为。 |
| `command_mutex_wait` | 已有 Client command 序列化 mutex 的 lock wall time。含无争用 lock 调用，不等于 Host response wait，不计入直接 Host wait。设备/其他未插桩 mutex 留在 unattributed。 |
| `present_semaphore_wait` | Present 同步启用时已有 Present semaphore 范围；未启用则无该项，不为诊断打开它。 |
| `resource_completion_wait` | PageBlock retention/readback 恢复路径的现有完成 event 等待。没有发起新的 readback、GPU flush 或 event 等待。 |
| `shared_heap_retry` | SharedHeap 找不到块后原有重试/扩容范围，含本地 allocator work，不等同于 Host 或 GPU wait。PageBlock 映射/分配等未拆分工作留在 unattributed。 |
| `queue_drain` | 既有 `ensureQueueEmpty` drain/poll 范围，可能含现有 Sleep。不是新增 sleep；不把它自动称为 GPU completion。 |
| `backend_call` | Host 上现有 D3D9 backend 调用的 wall duration，可能包含 DXVK CPU work、内部等待或调度；**不是 GPU execution time**。不修改调用参数、返回值、顺序。 |
| `unattributed` | 顶层 API/handler 内未落到显式 phase 的 wall time，包含本地工作、未测锁、调度和既有日志/内存诊断。不能直接称 `local_client_CPU_time`。 |
| `commands` | 当前进程 writer 成功 push 的累计次数；Client 通常是请求，Host 是响应，不能把两者相加当请求数。Module/Device 提交都计入。Host Device handler 的调用数可另按 API 汇总。 |
| `queue_delay=unknown` | 原 IPC 没有提交 timestamp；未添加 wire 字段或同步 side channel，不能可靠测得“提交→handler开始”。 |
| `gpu_time=unknown` | 未添加 GPU timestamp/query、flush、device idle 或 GPU completion 测量。 |

每行 `inclusive_us`/`max_us`/avg 和 `ge_1ms/ge_5ms/ge_10ms/ge_50ms/ge_100ms` 按该 span 的完整 wall duration统计；五桶是“≥阈值”的累计计数，不能再加成调用总数。phase 的 `total_us` 是 exclusive，去掉嵌套 phase 的时间；API 行 `total_us` 仍是完整 API time。因此不能把 `api`、所有 inclusive phase 和 unattributed 相加。

例如 Command 内等待队列空间时，该等待会从 `ipc_submit.total_us` 中扣除并归入对应 full wait。直接等待汇总只取响应、两类 full wait、Present semaphore 和恢复 completion 的 exclusive totals，排除 mutex、共享堆重试和 unattributed。原始独立等待函数可马上返回；“等待路径耗时”不等于线程在 kernel 中睡眠的精确时长。

顶层 Texture/Cube/VolumeTexture 的 Lock/Unlock 会调用 Surface/Volume 方法，Device Present 会调用 SwapChain Present。嵌套插桩 API scope 不再另计总调用，phase 归入外层 API，避免重复统计。直接调用 Surface/Volume/SwapChain 时仍计数。内部辅助 GetSurfaceLevel 创建、initial upload 拷贝、正常 PageBlock 内容提交仍在当前顶层 API 内。

Host 根据真实 command 分类。常见 TextureUnlockRect 的上传 command 是 **SurfaceUnlockRect**；Device Present/PresentEx 常走 **SwapChainPresent**。因此 Client/Host 同名次数不应强行一一匹配。`Readback` handler 计入 processing，其内部既有 helper 的调用拆分不包含在本次 main.cpp 的 45 个 backend 边界内。非目标 Device commands 归入 `Other`；不假装它们是纹理上传。

线程快照同时显示 `inflight`、`active_api`、`active_metric` 和 `active_span_elapsed_us`。它们是近似即时状态，不是已经完成的调用总时长或 Source loading state。跨快照边界的长调用可能先完成 phase、后完成 API，导致短区间 phase totals 与 API total 暂时不匹配；需结合 active markers 和稳定后快照解释，不能强制凑成等式。实现保留最多 64 个 TID slots，超出记录 `dropped_threads`；非零时覆盖不完整，不作完整线程归因结论。Windows TID 复用会聚合到同一 TID。

## 具体 timing points / 修改文件

| 位置（应用 `patches/l4d2-bridge.patch` 后） | 插桩 |
|---|---|
| `bridge/src/client/d3d9_device.cpp` | CreateTexture/Cube/Volume/VB/IB、UpdateTexture/Surface、三类 Surface create（含 Ex）、Reset/ResetEx、Present/PresentEx 顶层 scope；`syncOnPresent` 已有 semaphore 区间。 |
| `d3d9_texture.cpp`、`d3d9_cubetexture.cpp`、`d3d9_volumetexture.cpp` | LockRect/UnlockRect、LockBox/UnlockBox 的函数入口/所有出口。 |
| `d3d9_surface.cpp`、`d3d9_volume.cpp`、`d3d9_vertexbuffer.cpp`、`d3d9_indexbuffer.cpp`、`d3d9_swapchain.cpp` | Surface/Volume/VB/IB Lock/Unlock、直接 SwapChain Present；作为嵌套 helper 时不重复计总 API。 |
| `bridge/src/util/util_bridgecommand.h/.cpp` | Command scope（包括数据提交/复制）、现有 client writer mutex、响应 wait/pull、data overwrite semaphore、drain、成功 push count。 |
| `bridge/src/util/util_atomiccircularqueue.h` | 实际 command queue full 首次检测 → 可写或原超时，lazy timer；不改变 queue layout。 |
| `bridge/src/util/util_sharedheap.cpp` | 首次找块失败后才计 allocator retry。 |
| `bridge/src/util/readback_transport.h` | `Temporary::wait` 的原 `WaitForSingleObject` 范围；Request/Response layout 不变。 |
| `bridge/src/server/main.cpp` | `pop_front` 后、dispatch 前开始 Device handler scope；原 handler 及后处理结束时停止。45 个既有 D3D9 调用用透明 backend timing wrapper，包括创建/更新/映射/解锁、相关 descriptor helper、Reset、Present。Host 空闲 wait 不计 processing。 |
| `bridge/src/client/d3d9_lss.cpp`、server `main.cpp` | config/logger 初始化后读取新选项并启动可选诊断；不改变已有清理或同步。 |
| `bridge/src/util/api_wait_diagnostics.h`、`api_wait_commands.h`、`util/meson.build` | QPC、按线程固定聚合、嵌套 exclusive 归因、33 个命令分类、独立累计快照文件。无每调用 heap allocation、文件 I/O、日志 mutex 或诊断 IPC。 |
| 项目 `scripts/analyze_api_wait.py`、`config/API-WAIT-DIAGNOSTICS.conf` | 完整 snapshot/delta 分析、启用示例。 |
| 项目测试、CI、打包脚本 | x86/x64 disabled path、嵌套分区、提前返回、full episodes、并发计数、进行中状态和独立 worker 输出测试；Python partial snapshot、区间边界和差值测试；专用三文件更新包。 |

## 如何解释结果

CreateTexture 是否同步等 Host 取决于现有 `sendCreateFunctionServerResponses/sendAllServerResponses` 配置；诊断不改变它们。UnlockRect 主要提交原有上传 command/data，不因本次诊断自动等 GPU 上传完成；队列满或恢复 miss 等情况可产生真实等待。应以该次日志中的对应 wait metric 回答，而不是只看 API total。Create/Unlock/Update 的长尾从 call count、avg、lifetime max 与阈值桶判断；区间慢调用次数可由桶差值取得，区间精确 max 和百分位未实现。

如果实际调用线程的已归因等待很小，只能说明**当前测量范围内**同步等待不是主要耗时证据；unattributed、未覆盖 API、文件读取、解析、DataCache、声音和模型等尚需分别检查。若等待显著，也先区分 response、队列背压、mutex 和恢复路径，重复受控测量后再决定是否值得异步化。没有本功能的实机日志之前，不提供优化结论或编造加载秒数。

新增诊断实现遵循项目 MIT License；NVIDIA Bridge、DXVK 和其他上游 notices 保持各自归属与许可证。

`All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.`
