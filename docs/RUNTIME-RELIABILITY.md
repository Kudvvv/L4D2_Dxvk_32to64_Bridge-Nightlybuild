# 资源清理与传输优化验证

本批修改保留原有接口、线协议、GPLALL 后端、x64 Host 路径及默认配置。验证对象是以下五项修复和优化，游戏帧率需要另行实测。

| 项目 | 修改 | 验证 |
|---|---|---|
| 创建失败清理 | 顶点/索引缓冲区、渲染目标、深度和离屏表面及现有 Ex 接口，在明确失败时释放客户端对象并清空输出；超时仍按顺序发送清理命令。Host 返回失败结果，不因可恢复的创建错误触发断言。 | 提取实际 8 个 Create、Release、销毁和 Host 分支，检查错误码、父对象引用、影子内存计数、成功/失败/超时/异步及重复失败。 |
| 缓冲区 Lock 边界 | 在指针计算和减法之前拒绝越界偏移；保留超大请求长度的截断容错。优化锁预留与上传使用相同范围。共享堆策略直接读取构造参数，避免读取尚未初始化的成员。 | 实际 LockableBuffer 覆盖普通、整缓冲、优化锁、共享堆路径，含零长度、尾端、UINT_MAX、readonly 和策略初始化。 |
| 三维纹理缓冲所有权 | 锁队列使用 unique_ptr 持有数据，输出在成功入队后发布；分配失败返回 E_OUTOFMEMORY。 | 实际 LockBox/UnlockBox 与锁记录，注入缓冲分配、真实队列扩容和传输异常，检查旧锁保留及带锁销毁。 |
| 三维纹理连续复制 | blob 上传把已经连续存放的行和切片一次复制。 | 保留 LUT 字节步长、压缩格式、部分区域和线字段回归；与原逐行复制路径做相同编译参数的 A/B。 |
| 队列读取内存屏障 | 移除成功 peek 中多余的全屏障；保留发布/读取配对及唤醒协议中的原子操作。 | x86↔x64、容量 2/3/8/63、变化的 64 字节负载，反复 peek/peek/pull 与回绕；保留空闲、取消、超时、兼容唤醒检查。 |

## 运行检查

在具有 MSVC v142 / 14.29 与 Windows SDK 的环境，先运行构建脚本准备补丁后的源码，再执行：

```powershell
python -m unittest discover -s tests -p "test_*.py"
./scripts/test_resource_lifecycle.ps1
./scripts/test_command_queue.ps1
./scripts/test_volume_texture.ps1
./scripts/test_command_queue.ps1 -Benchmark
./scripts/test_volume_texture.ps1 -Benchmark
```

测试驱动从补丁后的源码提取生产实现。资源测试包含恢复旧创建路径、偏移校验、策略初始化和 Host 断言的负对照；三维纹理测试包含恢复旧 RowPitch 错误的负对照。负对照必须失败，否则测试作业失败。传输、COM 存储及后端由测试替身提供，这些检查不等于 GPU 或游戏验收。

GitHub Actions 的 `validation_only` 选项执行完整构建、测试及基准并保留产物，跳过发布。使用 `force_rebuild` 和完整 `upstream_commit` 可固定比较对象。

## 性能测量范围

队列基准只在成功 peek 路径插入/移除同一条屏障，两版使用相同 `/O2 /W4 /WX` 编译参数。默认每组预热 25,000 条消息，测量 2,000,000 条；两种位宽方向、容量 8/256、6 轮配对交替执行。结果保存吞吐、生产者/消费者 CPU 时间和入队尝试至成功 peek 的 p50/p95/p99 延迟，包含排队时间。检查负载字节及顺序是通过条件；性能采用分布和配对中位数分析，不设置易受运行环境影响的绝对门槛。

三维纹理基准使用实际上传方法，仅替换连续复制或旧逐行复制的代码段。x86/x64 各 5 轮交替顺序，覆盖 64 KiB、512 KiB 和 2 MiB，每次改变输入并检查完整输出。计时从目标 blob 分配完成开始，到复制结束为止，排除分配、填充和校验。

原始结果分别保存在 `.deps/queue-test/benchmark-*.csv/json` 和 `.deps/volume-test/volume-copy-*.csv/json`；验证工作流将结果与测试程序上传为 `validation-*` artifact。CPU 计时具有操作系统计时粒度，共享 CI 主机存在调度波动；这些数据不能换算为游戏 FPS 提升。

游戏验收范围及记录方式见 [GAME-VALIDATION.md](GAME-VALIDATION.md)。
