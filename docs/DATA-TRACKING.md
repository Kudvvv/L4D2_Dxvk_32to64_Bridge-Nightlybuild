# Bridge 数据和资源追踪实验

本轮只补充证据采集，供下一版本评估 VB、IB、Volume 3D 等优化。没有更改资源容量、Lock/Unlock 返回值、PageBlock 回收/恢复、GC、DXVK、Host 生命周期、控制 ABI 或 L4N 插件。不能根据锁标志、短期未使用或上传次数直接认定资源可安全卸载。

静态 WRITEONLY 缓冲仍保留 FULL_SHADOW：WRITEONLY 不保证写满 Lock 范围，D3D9 允许多次 Lock。新增 BUFFER 分类、动态锁直方图、绑定/常量同值摘要及契约测试见 [BUFFER-SHADOW-CONTRACT.md](BUFFER-SHADOW-CONTRACT.md)。`candidate` 是候选容量，`avoided` 本轮为 0；未启用 RANGE_STAGING。

## 启用与采集

四项设置见 [DATA-TRACKING.conf](../config/DATA-TRACKING.conf)，合并到已有 `bin/.l4d2bridge/bridge.conf`，完整重启游戏。默认配置中两侧 `dataDiagnostics=False`；追踪关闭时没有该诊断的线程、文件、元数据表或计时查询，仍有少量开关判断和 wrapper/命令内的追踪字段。开启后有计数锁、后台摘要线程、约 3 MiB 固定元数据和日志开销，不宜直接用开启追踪的帧率评估最终优化收益。

Client 在游戏 EXE 所在目录写 `l4d2-data-client.log`；Host 在 Host EXE 所在目录写 `l4d2-data-host.log`（通常是 `bin/.l4d2bridge/`）。使用 Unicode Windows 路径；初始化失败只报告失败，不中止 Bridge。日志每次完整启动重新创建，复制上一轮日志后再重启。

建议一轮连续采集：主菜单 → 本地进图 → 正常走动/开枪 1–2 分钟 → 联机服务器 → 过图 → 正常退出。另开一轮重复相同动作比较 x86/x64 Host，勿把不同进程或不同配置的计数相加。保留已有 memory、host-memory、PageBlock 和 bridge32/bridge-host32/bridge64 日志；无需开启偏色、readback test 或额外 L4N 诊断菜单。

分析命令：

```console
python scripts/analyze_data_diagnostics.py l4d2-data-client.log l4d2-data-host.log --json data-report.json
```

## 覆盖内容与指标

| 路径 | 当前追踪 | 限制 |
|---|---|---|
| VB / IB | 创建/释放、长度、usage/pool/format、Client 影子字节和峰值；Lock 范围、次数、READONLY/DISCARD/NOOVERWRITE、部分锁、非法范围/失败；提交上传量、shared/reserved 方式；Host Lock/Unlock 结果 | API shadow 是 Bridge 所有，不表示引擎还有同内容副本；上传是 Client 提交意图，Host 成功/失败另看后端记录 |
| Volume 3D | Volume 层对象、尺寸、格式、pool/usage；LockBox 申请字节、失败/READONLY、提交量；临时缓冲当前/峰值、分配/释放（含未 Unlock 就销毁和移动所有权）；Host LockBox/UnlockBox 结果 | 不按 width×height×depth 猜压缩资源存储；`logical_bytes=0` 表示未估计整层大小，实际临时布局字节是有效指标；本轮不增加 readback |
| Vertex / Pixel shader | 最终 wrapper 的字节码大小、vector capacity、生命周期、GetFunction 本地查询/复制次数和字节 | 构造过程的短期字节码副本、DXVK 编译后的 shader 内存未统计 |
| Vertex declaration | 元素字节、vector capacity、生命周期、GetDeclaration 查询/复制 | 不测引擎内部顶点格式副本 |
| StateBlock | 对象数、固定 State/DirtyFlags 存储、生命周期；相关 IPC | `shadow_bytes` 只包含已知固定结构，不含 map/vector 的动态节点容量及引用资源本身 |
| 所有 Device/Module Command 发送 | 标量、UID、结构体/数组 blob、blob 预留、成功/失败发布、头部；每条命令的累计序列化量 | 共享堆正文不在 inline wire 中；队列绕回空隙不算有效数据；serializer 成功表示写入 API 接受，不是后端完成 |
| 所有 Device/Module Command 接收/Host 分派 | 接收次数、Host handler 累计/单次最大耗时 | handler 包含解包、复制、后端调用、同步和响应，不能等同 GPU 耗时或只归因于 DXVK |
| 纹理、Surface、DrawPrimitiveUP / DrawIndexedPrimitiveUP、常量/状态、Query/GetData、caps、readback、创建/绘制/Present | 通用命令量和 blob/序列化量；Surface shadow/backing 复用现有 PageBlock/memory 日志 | 命令覆盖不等于这些路径已有独立内存生命周期表；Host 的 Bridge_Response 按响应命令合计，未按原请求拆响应字节 |
| ProcessVertices | 命令和 Host handler | Host 在后端写目的 VB，不代表 Client 上传；不能据此证明 Client shadow 最新 |

`shadow_bytes` 是当前已知 Client 存储，`logical_bytes` 是资源描述/固定结构大小，均不是 VRAM。`upload_bytes` 是累计提交的逻辑字节。`data_bytes` 是发送端 serializer 成功接受的 footprint（含标量/UID/blob 长度前缀/4 字节对齐）；`blob_bytes` 不含这些元数据。`reserved_bytes` 在 COMMAND 中表示 arena blob 预留，在 KIND/RESOURCE 中表示优化 VB/IB reserved 上传路径；不要相加。backend_bytes 是 Host 成功 Lock 的逻辑请求字节，Unlock 成功仍需单独看失败计数。

Shader/declaration 的 `reads` 含只查询长度的调用（字节为 0），有返回内容时才累计 `read_bytes`。VB/IB 的 `readonly` 表示游戏请求读取 Bridge 本地 Lock 存储，不意味着本轮已从 Host 读回。

新 STATE 比较只读取 Client 已有的有效本地状态，不写入日志正文，也不留第二份值缓存。首次未知状态及 Reset/StateBlock Apply 后先失效，正常与录制域分开计数。启用后增加载荷比较、动态直方图计数及每个 Device 的有效性标记开销；关闭时不进行这些比较或分配。统计不能直接证明状态调用可删除。

尚未量化：Source/L4N 私有容量和内存、Client 私有数据字典和 Device 本地缓存的全部动态节点、共享堆实际 committed/reserved 峰值、输入旁路消息、驱动/DXVK 内部资源和 VRAM。新追踪不读取这些私有实现，也不扫描或复制资源正文。

## 证据完整性与开销

固定表最多 8192 个同时存活的目标 wrapper。表满后聚合计数继续有效，逐资源信息缺失用 `resource_overflow` 标记。释放记录在最多 2048 条的释放记录缓冲中交给工作线程，溢出用 `retired_dropped` 标记。每份摘要最多轮转采样 128 个存活对象；聚合 KIND 不受采样影响。不要把没有出现在某份摘要中的 ID 当作已释放。

摘要间隔最低 1000 ms，默认 5000 ms。每个进程日志最大 64 MiB，预留 END 空间；`file_discarded` 和 `write_failures` 表示文件证据不完整。正常退出生成最终摘要和 END；崩溃/强杀可能缺少 END。分析器按 CONFIG 分会话，只取每项最新累计值，明确提示溢出、缺 END、角色混杂或未知记录格式；报告还列出较大的已观察存活对象和已释放对象。已观察列表不是完整实时清单，`lock_idle_ms` 只表示距离最近 CPU Lock 尝试的时间，不能当作 GPU 未使用时间。

## 下一版本决策

优先检查：VB/IB 当前/峰值影子占用与活跃锁范围是否相差很大；静态缓冲是否只上传一次且长时间不再锁；READONLY 或后端生成内容是否存在；Volume 峰值是否来自很多同时未结束的锁；DrawUP、常量/状态、查询的累计传输及 Host handler 占比。跨图看旧对象是否正常释放，不能只看上传累计增长。

追踪提示候选优化之后，还需明确 D3D9 可恢复来源、所有后续访问路径、错误传播和实机一致性测试，才可决定范围式影子、暂存复用、去重/批量传输等方案。L4N 的引擎容量配置不构成 Bridge 可以安全删副本的依据。
