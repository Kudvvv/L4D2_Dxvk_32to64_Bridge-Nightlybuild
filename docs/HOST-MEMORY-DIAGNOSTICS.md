# Host 内存与 CPU 诊断 / Host memory and CPU diagnostics

这是 v1.0.0 的诊断更新，用来定位 64 位桥进程的内存增长和 CPU 开销。当前 Host 日志使用 `schema=3`，新增资源分类／生命周期计数、地址空间提交量分类，以及桥自身的 GPU 内存统计。诊断不改变资源的创建／释放规则或 IPC 协议；尚未修复本轮观察到的反复进图内存增长。

## 安装与恢复

1. 完全退出游戏和 `L4D2Bridge64.exe`，备份原 `bin/.l4d2bridge/L4D2Bridge64.exe`。
2. 从 `l4d2-bridge-host-diagnostics` 更新包只替换这个 EXE。保留原客户端 DLL、`d3d9vk_x64.dll`、`bridge.conf`、ReShade 配置和着色器。已有 v1.0.0 客户端可以继续使用；新 EXE 不修改握手协议。
3. 启动游戏，确认生成 `bin/.l4d2bridge/l4d2-host-memory.log`。此文件不依赖逐调用日志开关。需要回退时，退出游戏后恢复备份 EXE。

## 当前推荐复测：同图往返

CPU 优化与额外纹理缓存暂缓。保持原来的帧率上限、Mod、分辨率和画质，使用同一个游戏／Host 进程：

1. 在首次主菜单记录时间、游戏／桥 RAM，以及 GPU 的**专用和共享**读数。
2. 进入同一地图，移动／开枪至少 30 秒，再回到菜单，等待五分钟。记录返回菜单和五分钟结束的时间及相同读数。
3. 连续做三至四轮，最后正常退出，并保存下述四份日志。各轮保持相同窗口活动方式，不在中间重启。
4. 无桥用相同条件至少做两轮，记录同样的 RAM 和专用／共享 GPU 读数。背景软件保持同样状态；无需采样其他进程。

任务管理器 GPU 性能页是整张显卡的统计；总量包含背景应用。**专用显存＋共享 GPU 内存**不是全部由显卡 VRAM 承担，共享部分使用系统 RAM，也不能与进程工作集简单相加当作独立物理内存。新日志的 GPU 字段是当前 Host 在选定适配器、节点 0 上的 WDDM 使用量，口径也不同于整张显卡的总量。

如果已有连续四轮的原始日志，先保存和发送，无需为了这个更新重做才能分析。

## 其他对照方法

- 使用同一地图、相同 Mod，关闭 ReShade 的加载后测试。只关闭效果仍会保留 ReShade 的钩子和运行环境；请使用 ReShade 安装器取消该应用的 Vulkan 启用，并保留配置备份。
- 先限制到 60 FPS，记录约 10 分钟，然后设回 300 FPS 上限，记录相同场景。记录调整帧率的时间，尽量保持分辨率和画质一致。
- 更换一次地图，观察游戏 AV、Host 内存和资源句柄数是否回落，继续记录约 10 分钟。
- 如需要比较 ReShade，另起一轮启用 ReShade 的测试；每轮结束后立即保存日志，下一次运行会覆盖文件。
- 发回四份日志：`bridge32.log`、`bridge64.log`、`bin/l4d2-memory.log`、`bin/.l4d2bridge/l4d2-host-memory.log`。说明地图切换、帧率调整时间和退出方式。

`l4n` 与服务器冲突若在无桥环境也复现，需与本轮内存变化分别判断；它导致客户端先退出时，Host 列出大量尚存对象不能直接作为桥接资源泄漏的证据。

## 字段与判断边界

所有内存字段按字节计。每个进程首次创建文件会覆盖上一轮；采样由设备命令处理线程触发，通常间隔至少五秒。没有设备命令时不持续采样，不使用额外后台线程。

| 字段 | 含义 |
| --- | --- |
| `private_bytes` | Host 私有提交量，不等于实际驻留 RAM |
| `working_set` / `peak_working_set` | Host 当前／峰值总工作集，含可共享页；不等于任务管理器的私有工作集列 |
| `system_commit_bytes` / `system_commit_limit` | 整台机器的提交量／上限，含其他应用和保留的纹理 section |
| `physical_available` / `physical_total` | 系统可用／总物理内存，不能直接归因于桥进程 |
| `handles` | Host 进程持有的 Windows 句柄数量 |
| `resource_handles` / `volume_handles` | Host 中资源／体积对象映射表的条目数；包含纹理、子表面与缓冲等，可能有同一底层对象的不同映射，不是独立 GPU 分配数量或字节数 |
| `texture_handles`、`cube_texture_handles`、`volume_texture_handles`、`vertex_buffer_handles`、`index_buffer_handles`、`surface_handles` | 资源表按类型的存活条目数；表面可能是纹理子表面或隐式后缓冲，不能与纹理数相加当作独立分配数 |
| `resource_inventory_valid` | 分类统计是否与资源表条目总数一致；0 时需要检查未注册的查找条目等情况 |
| `resource_register_total` / `resource_rebind_total` | 累计写入映射次数／同 ID、同对象的重复登记，不等于 GPU 分配次数 |
| `resource_replace_total` | 同 ID 在尚未删除时被不同对象或类型替换的次数；用于发现可疑覆盖，本身不能证明泄漏 |
| `resource_destroy_total` / `resource_unlink_total` / `resource_missing_erase_total` | 累计 Destroy／Unlink 命令处理次数及其中找不到分类记录的次数；不是 DXVK 内部释放完成的计数 |
| `address_private_commit` / `address_mapped_commit` / `address_image_commit` | `VirtualQuery` 扫描 Host 的 `MEM_COMMIT` 区域，按 PRIVATE、MAPPED、IMAGE 类型分类。不是 RAM 驻留量，也不能直接归因于某个分配器；mapped 扫描量不等于本进程承担的独占提交量 |
| `address_regions` / `address_query_ms` / `address_memory_valid` | 扫描区域数量／扫描耗时／是否完成；扫描期间其他线程可能分配或释放，因此是近似快照 |
| `gpu_local_usage` / `gpu_nonlocal_usage` | 原生 DXGI `QueryVideoMemoryInfo` 返回的**当前 Host 进程**本地／非本地段使用量。在 B580 等独显上主要对应专用／共享 GPU 内存，不能当作整卡总量或纹理净数据量 |
| `gpu_local_budget` / `gpu_nonlocal_budget` | 当前进程的 WDDM 预算，不是显卡容量或占用量 |
| `gpu_vendor` / `gpu_device` / `gpu_node` / `gpu_adapter_result` / `gpu_*_result` | 适配器匹配信息、节点及查询 HRESULT；按后端 D3D9 的 vendor/device 匹配原生 DXGI，存在多张相同型号显卡时不猜测，统计无效 |
| `gpu_local_valid` / `gpu_nonlocal_valid` | 相应 GPU 查询成功才为 1；0 不能理解为 GPU 占用为零 |
| `devices`、`declarations`、`state_blocks`、`vertex_shaders`、`pixel_shaders`、`swapchains`、`queries` | 对应 Host 对象表条目数 |
| `cpu_kernel_100ns` / `cpu_user_100ns` | Host 累计内核／用户 CPU 时间，单位 100 纳秒 |
| `processors` | 活动逻辑处理器数量 |
| `cpu_cores` | 两次采样间 CPU 用时除以实际经过时间；1 约等于持续占满一个逻辑核 |
| `cpu_percent` | `cpu_cores / processors * 100`；Host 所有线程的平均占用，不包含游戏进程；任务管理器的频率修正与采样窗口可能造成差异 |
| `commands_total` / `commands_per_second` | 累计／每秒处理的设备通道命令数，包含绘制、资源等命令，不等于 draw call 数；不包含模块通道 |
| `tick_ms` | Windows 启动以来经过的毫秒，用于计算采样间隔 |
| `client_exit_code` | 最后一次采样尝试读取客户端退出码；`0x103` 表示仍在运行，不能据此判定崩溃 |
| `*_valid` | 对应查询或时间差是否有效，0 时不要按数值下结论；第一条 CPU／命令速率记录无上一条基准，正常为无效 |

资源分类仅在原来的映射登记和删除位置记录类型与对象身份，不调用资源 COM 方法，不新增资源引用或强行释放对象。GPU 诊断动态加载系统 DXGI 并查询适配器接口，不枚举或采样其他进程；匹配／API 不可用时输出无效标志，游戏仍可运行。扫描和 GPU 查询沿用至少五秒的采样间隔，无额外后台线程。

判断顺序：菜单阶段同类资源数量是否逐轮增长；游戏侧 shadow backing 是否同步增长；资源数量稳定时 Host 私有／映射提交量和本地／非本地 GPU 使用量是否增长。计数下降只证明桥已处理相关命令，GPU 仍可能有未完成工作、内部引用或分配块保留；不能据此声称资源的物理内存已全部归还。

当资源分类稳定、GPU 非本地使用量仍逐轮增长时，下一步可复用标准 DXVK 的分配器 HUD，查看申请量、使用量和块分布，参见 [GPU 分配诊断](GPU-ALLOCATION-DIAGNOSTICS.md)。

## English

This is a diagnostic update for v1.0.0, not a memory/performance fix. Exit the game and Host, back up `bin/.l4d2bridge/L4D2Bridge64.exe`, and replace only that executable from the `l4d2-bridge-host-diagnostics` artifact. Keep the client, DXVK, configuration and ReShade files. The existing v1.0.0 client remains compatible. Restore the executable backup to revert.

The Host writes `bin/.l4d2bridge/l4d2-host-memory.log`, replacing the previous session. Schema 3 adds per-type resource-handle counts, registration/rebinding/replacement/destruction/unlink totals, committed address-region categories, and native DXGI process-local GPU usage/budgets. GPU queries cover the current Host only, node 0, matching the backend vendor/device; ambiguous identical GPUs or unavailable APIs produce invalid counters. Local/nonlocal usage is not card-wide VRAM or texture payload size. Object entries include aliases, not unique GPU allocations. Address categories are approximate committed virtual regions, not physical residency or allocator ownership.

For the current memory investigation, pause CPU changes and texture pooling. In one process, enter the same map, play for at least 30 seconds, return to the menu and wait five minutes; repeat three or four times and exit normally. Record timestamps, game/Host RAM and dedicated/shared GPU readings at each settled menu. Compare at least two cycles without the bridge under the same conditions. Save all four logs before restarting. Existing four-cycle logs remain useful and should be sent first. Card-wide GPU totals include background applications; shared GPU memory uses system RAM and must not simply be added to process working sets as separate physical usage. No other processes need to be sampled.

Compare the same map/mods at 60 FPS and a 300 FPS cap, initially with the ReShade Vulkan layer disabled for this executable (disabling effects alone leaves its hooks active). Then change map and check whether counts and memory return. Record phase times and save all four logs before restarting. A separate ReShade-enabled run can help isolate its impact. These observations can narrow the source of growth or CPU cost, but cannot prove a leak or attribute allocations inside DXVK, the driver or ReShade without further profiling.

Once the long-wait comparison confirms growth with stable resource counts, use the existing DXVK allocator HUD to inspect allocated/used capacity and chunk distribution; see [GPU allocation diagnostics](GPU-ALLOCATION-DIAGNOSTICS.md). Repeating the initial three-cycle comparison is unnecessary for this next step.

## License and attribution

New diagnostic implementation and tests: Copyright (c) 2026 yeyunyyds, MIT.

All newly added implementation code in this fork was generated by OpenAI Codex from prompts and specifications provided by yeyunyyds.

The existing NVIDIA Bridge, DXVK and third-party notices remain unchanged; see [THIRD_PARTY.md](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/main/THIRD_PARTY.md) and [LICENSE](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/main/LICENSE), also included at the root of each package.
