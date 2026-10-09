# v1.0.0 纹理 shadow 地址空间回收与诊断

旧版进图采样中，纹理表面 shadow 达到 2,231,984,860 字节（约 2.08 GiB），加上顶点和索引 shadow 约 2.25 GiB。x86 进程空闲地址空间只剩约 147 MiB，最大连续空闲块约 55 MiB。这证明 bridge 的 CPU 副本造成严重地址空间压力；日志未记录最终异常，不能据此确定具体崩溃指令。

新版将非共享堆路径的纹理表面 shadow 改为 Windows 分页文件支持的 section。Lock 时映射并保持指针有效，Unlock 将写入数据复制到现有 IPC 后解除锁定。缓存超出预算时，优先取消最久未使用且未锁定的映射；section 保留全部内容，下次 Lock 重新映射，不依赖 GPU 回读。资源销毁时关闭 section。预算按 Windows 分配粒度计入对齐开销，避免大量小 mip 映射消耗过多地址空间。

默认 client.surfaceShadowCacheMB=128，可在现有 bridge.conf 添加该项；不添加也默认 128。0 表示解锁后不缓存映射；最大有效值为 1024 MiB。正在锁定的资源不会回收，所以同时锁定的大资源可以暂时超过预算。此版本减少的是 x86 映射和地址空间占用，保留数据的系统提交量和物理内存/分页文件需求仍然存在，顶点/索引 shadow 保留方式没有改变。它不是完整的资源迁移方案，游戏性能和兼容性仍须实测。

## 安装与复测

当前 Nightly 只提供完整包：关闭游戏及 Host，备份原有客户端、Host、配置和 bin/studiorender.dll，按 [README](../README.md) 从临时解压目录移除会覆盖已有配置或自定义后端的文件，再同时更新 bin/d3d9.dll 与 bin/.l4d2bridge/L4D2Bridge64.exe。包内 bin/studiorender.dll 已包含 ThinFlex 修复；先核对已安装 DLL 的 SHA-256，仅在匹配支持的原版时替换，已修复版本可保留，未知版本应从临时解压目录移除此 DLL、仅更新 Bridge。已打补丁的玩家须保留最初原版备份，不能用修复文件覆盖它。默认移除 -vulkan；需要该启动项时自行改名客户端并移到 bin/dxvk_d3d9.dll。本文其他首次实测数据属于历史配置；当前三项优化的对照见[性能报告](PERFORMANCE-2026-10-10.md)，该测试没有安装 ThinFlex。保持 logLevel=Info、logApiCalls=False、logServerCommands=False。

从 Steam 用原来的 Mod 和同一地图再次进图。尝试正常游玩并退出后重新进图一次，检查贴图是否正常、是否崩溃及帧率。请提供 l4d2-memory.log、bridge32.log、bridge64.log，说明能否进图和实际表现；如有崩溃 dump 或报错窗口也一并提供。

采样文件是游戏 bin/l4d2-memory.log，与客户端 DLL 同目录，不跟随游戏工作目录或 DXVK_LOG_PATH。每个新进程首次采样覆盖旧文件，退出或崩溃后立即复制保存，避免下次启动覆盖。不需要逐调用日志。

## 日志字段

字段按字节记录：surface_bytes/count 现在是**当前映射**的纹理 shadow；surface_backing_bytes/count 是保留数据的 section 总量；surface_view_budget_bytes 是映射缓存计入对齐后的预算占用。后两者用于区分“内容仍保留”和“x86 映射已经回收”。无活动锁时，预算占用应不超过默认 128 MiB；加载后要结合 va_free、largest_free 判断地址空间是否恢复。

vertex_bytes/count、index_bytes/count 是顶点/索引缓冲 shadow，包括使用 shadow 的静态缓冲。va_committed、va_reserved、va_free、largest_free 是 x86 地址空间扫描；va_limit 是扫描上界；scan_complete 表示扫描是否完成。private_bytes 和 working_set 通过系统 API 读取，counters_valid=0 时不可使用它们判断。系统对映射内存的统计与旧版堆分配不同，不能只比较 private_bytes 判断所有资源占用。

采样由 Present 和 shadow 分配/映射触发，最小触发间隔仍为五秒；普通采样交给 Windows 线程池执行，没有这些调用的阶段不会持续记录。同一时刻最多有一项未完成的普通采样：若上次任务超过五秒仍未完成，本次普通触发合并到已有任务，不在渲染线程重复扫描或排队。这不是严格每五秒必有一行日志的保证。线程池提交或模块引用获取失败时，退回原来的同步扫描，保留诊断记录。

普通 event（包括 before-allocation、surface-mapped）记录的是触发原因，时间戳、内存计数和地址空间字段对应后台实际扫描时刻；before-allocation 不再表示扫描发生在分配之前。字段和单位不变，统计仍是近似快照，不包含引擎其他内存、IPC 和代理对象。失败事件不合并、不依赖后台调度：event=allocation-failed、section-create-failed、section-map-failed 仍在失败调用线程同步扫描，保留失败参数和 win32_error，并在返回前刷新文件。它们可能等待正在进行的扫描释放日志锁，和原有并发采样的序列化规则一致。没有失败事件不能排除其他位置的内存耗尽或访问错误。

排队任务持有客户端 DLL 的临时引用，回调返回后由 Windows 释放；因此正常动态卸载可能延后到这一次任务结束。采样器没有常驻线程、没有永久固定模块，也不在 DllMain 增加线程等待。后台任务只拥有事件文本和标量参数，不保留游戏资源指针。强制失败路径仍使用栈存储和 Win32 I/O，不创建线程池任务或分配请求对象。

Windows x86 自动测试覆盖：映射回收后内容恢复、活动锁和嵌套锁保持指针有效、128 个小映射的预算控制、资源销毁时清零计数，以及原来的诊断分配失败路径。通过这些测试不能替代 L4D2 实测。

`scripts/test_memory_sampling_async.ps1` 另外在 x86/x64 的真实 DLL 中测试排队/执行中卸载、请求文本所有权、五秒最小间隔、忙时合并、调度失败同步回退，以及与后台任务并发时强制失败记录仍同步刷新且不调用 C++ new。它使用真实 Windows 线程池及模块引用 API，并以固定容量测试日志接收器验证字段。[性能报告](PERFORMANCE-2026-10-10.md) 记录了包含此改动的三项优化合并后、三对固定 L4N 回放的实测；这些结果不能单独归因于内存采样器，也不代表已安装 ThinFlex 时的性能。
