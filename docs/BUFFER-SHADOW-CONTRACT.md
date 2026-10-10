# 静态 VB/IB 副本的契约边界

本轮按用户确认的范围保留现有 FULL_SHADOW，只增加契约回归测试及只读数据诊断。没有启用 RANGE_STAGING，没有新的静态回收或恢复路径，也没有修改动态缓冲、上传顺序、IPC、PageBlock、GC、Host 生命周期或 L4N 插件。

## 为什么 static + WRITEONLY 仍不足以证明安全

`D3DUSAGE_WRITEONLY` 表示应用只写缓冲，不承诺应用会覆盖每次 Lock 返回范围中的全部字节。静态缓冲不能依靠 `D3DLOCK_DISCARD` 获得丢弃旧内容的契约；DISCARD/NOOVERWRITE 只适用于 DYNAMIC VB/IB。

合法的反例是：先把 64 字节缓冲写满，再 `Lock(0, 64, 0)`，只修改第 12 字节，随后 Unlock。当前 Client 完整 shadow 保留其余 63 字节，并通过现有协议上传全部 64 字节。若换成没有旧内容的 64 字节暂存，上传将破坏未修改部分。清零不能恢复历史字节；读取 WRITEONLY 内容也不能凭空成为受保证的通用后端恢复来源。

D3D9 还明确允许多次 Lock，只要求与 Unlock 次数对应。现有 Client 以队列顺序处理 Unlock，重叠 Lock 的指针指向同一份 shadow。独立的范围暂存不能自动保持这种已有行为；不能简单把第二次 Lock 一律判成错误。

官方契约参考：

- [D3DUSAGE](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dusage)
- [D3DLOCK](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dlock)
- [VertexBuffer Lock](https://learn.microsoft.com/en-us/windows/win32/api/d3d9/nf-d3d9-idirect3dvertexbuffer9-lock)
- [IndexBuffer Lock](https://learn.microsoft.com/en-us/windows/win32/api/d3d9/nf-d3d9-idirect3dindexbuffer9-lock)

本轮不会按时间、锁次数、上传历史、WRITEONLY 标志或无 READONLY 的短期观察删副本。未来如果没有完整的旧字节来源和多锁兼容方案，资源继续保留 FULL_SHADOW。原有 shared heap/optimizedDynamicLock 配置按其既有规则执行，本轮不启用、不改变这些路径。

## 内存和失败行为

普通 VB/IB 创建时仍由 Client 申请完整 shadow；Lock 返回原有 shadow 指针；Unlock 仍发送原 offset、有效 size、flags 和字节，随后按原有队列弹出锁记录。Host 保留真实后端资源。Client shadow 在原有资源销毁路径释放。

没有新暂存、迁移备份、范围读回或 A/B 开关。原有错误、断线及后端处理保持原样；新的 invalid/Unlock-without-Lock/Destroy-while-locked 计数是观察，不是新的验证、错误返回或容错实现。原有 benign Unlock-without-Lock 仍返回成功。日志中的 invalid 范围不代表本轮已修复旧路径的边界检查。

## 新摘要记录

沿用 `schema=1`，新增字段/事件为加法扩展。所有字节都是 Bridge 已知 CPU 存储或累计逻辑载荷，不是 VRAM、引擎内存或进程实际释放的 VA。更新后的分析器兼容没有新事件的旧日志。

### BUFFER：每个 VB/IB 类型

| 字段 | 含义 |
|---|---|
| `full_shadow_live_bytes` / `full_shadow_resource_count` | 当前满尺寸 Client shadow 字节和有非零 shadow 的对象数，包含动态缓冲 |
| `dynamic_shadow_live_bytes` | 上述字节中 DYNAMIC 缓冲的部分 |
| `candidate_writeonly_static_bytes` / `peak_candidate_writeonly_static_bytes` | 有本地 shadow 的非 DYNAMIC、WRITEONLY 候选字节及事件级峰值；不是可安全回收容量 |
| `eligible_writeonly_static_bytes` / `range_staging_enabled` | 本轮均为 0，尚未证明范围模式的完整契约 |
| `avoided_persistent_shadow_bytes_current/peak` | 本轮均为 0，没有实际消除副本 |
| `skipped_dynamic_count/bytes` | 累计创建的 DYNAMIC 对象及描述字节 |
| `skipped_not_writeonly_count/bytes` | 累计非 DYNAMIC、非 WRITEONLY 对象及描述字节 |
| `skipped_no_local_shadow_count/bytes` | 非 DYNAMIC、WRITEONLY 但无本地 shadow 的对象，如现有共享堆路径；不猜测实际共享堆容量 |
| `skipped_historical_contents_count/bytes` | 累计静态 WRITEONLY、有 shadow 的对象及描述字节；缺少无需旧内容的保证，继续保留 |
| `full_shadow_lock_count/bytes` | 有 shadow 的成功、有效 Lock 及归一化字节 |
| `unlock_count` | 存在锁记录时的 Unlock 调用，不承诺后端完成 |
| `unlock_without_lock` / `destroy_while_locked` | 无锁 Unlock 次数 / 销毁时仍有锁记录的对象数 |

current/count 随销毁减少，峰值保留；skip、Lock、错误观察是累计计数。分组聚合不依赖 128 个对象的抽样或释放明细队列，逐对象队列溢出不损失这些总数。

### DYNAMIC_LOCK：每个 VB/IB 类型

只统计原路径返回成功、范围有效的 DYNAMIC Lock。`SizeToLock=0` 按 offset 到末尾归一化。

- `lock_count`、`total_lock_bytes`、`min_lock_bytes`、`max_lock_bytes`。
- 七个互斥桶：0–64、65–256、257–1024、1025–4096、4097–16384、16385–65536、>65536 字节。
- 平均值由累计字节除次数得到；没有样本时分析器返回 null。
- 原 KIND/RESOURCE 的 DISCARD、NOOVERWRITE、partial、invalid、failures 继续保留。

不检测或合并相邻 Unlock，不改变动态分配、锁指针、标志或上传。

### STATE：本地状态同值测量

覆盖 SetStreamSource、SetIndices、SetTexture 及 VS/PS 的 F/I/B 常量设置。`total_calls`、`compared_calls`、`same_value_calls`、`total_payload_bytes` 和 `same_value_payload_bytes` 均为累计计数。

`recording=0/1` 分开正常状态与 StateBlock 录制。绑定比较资源身份及有效参数；空 stream 不比较被忽略的 offset/stride。F/I 常量比较原始字节，包含浮点 NaN 与正负零的位差异；B 常量比较当前存储的布尔语义。常量的字节数是 Client 实际接受/比较的寄存器载荷，受既有数量归一化影响，不包括命令头、寄存器起点和长度前缀。

诊断有效性标记仅在追踪已启用时为 Device 分配，不保存第二份状态载荷。首次设置、Reset/ResetEx、StateBlock Apply 后，不读取未知缓存；随后有效设置才建立可比性。StateBlock 首次未录制的字段也不进行比较。诊断分配失败时正常 API 继续执行，未验证的状态不计为同值。接受的零长度常量更新计为同值、载荷 0。

这些结果表示 Client 本地值相同，不等于 Host 已确认的渲染状态，更不能直接把同值请求删掉。全部 API、引用计数更新、状态记录和 IPC 照常执行。禁用追踪时不比较载荷，不创建该有效性表；启用后有 memcmp、布尔循环和计数锁开销，不用于推算最终 FPS。

## 验证

`scripts/test_buffer_contract.ps1` 在 x86 MSVC 中机械提取当前补丁生成的真实 LockableBuffer 模板，使用确定性的 COM/IPC 适配器执行；不复制一份缓冲算法作为测试替身。测试覆盖 DEFAULT/MANAGED VB、INDEX16、INDEX32 的满锁、只改大 Lock 内一部分字节、非零 offset、size=0 到末尾和重叠多锁，复现空暂存与旧行为不等价；另验证动态 DISCARD/NOOVERWRITE 的原有上传、非 WRITEONLY READONLY、无锁 Unlock 和带锁销毁的存储平衡。适配器捕获现有上传的 offset/size/flags 和已复制载荷，并按同一范围更新规则检查未修改的 Host 字节；它不是实际共享队列、真实 GPU 或后端恢复测试。

`scripts/test_data_diagnostics.ps1` 的 extended 模式在 x86/x64 验证分类生命周期、候选与实际避免字节分离、直方图边界、非法/失败锁排除、无锁 Unlock/带锁销毁观察、并发状态计数、正常/录制域分离和不可比状态排除。分析器测试验证累计摘要不重复相加及旧日志兼容。

同一脚本还提取生产常量更新和诊断失效方法，在 x86/x64 用固定存储适配器验证首次/失效/录制比较、F/I 位相等、NaN、正负零、BOOL 归一化、零长度、既有验证失败，以及诊断关闭时正常更新继续执行。这不依赖 GPU。原方法已有的有符号循环比较和常量 enum 条件警告只在提取方法内局部隔离，生产实现保持原样，其余测试及诊断源以 `/W4 /WX` 编译。

实机沿用 [DATA-TRACKING.conf](../config/DATA-TRACKING.conf)，重启后采集本地进图、正常游戏、联机和过图，正常退出。上传两份 data 日志及原有 memory、host-memory、PageBlock、Bridge 日志。此版预计 shadow 仍接近旧基线；重点是得到静态/动态占用、同值比例和锁大小分布，不能把 `candidate` 当成已节省内存。
