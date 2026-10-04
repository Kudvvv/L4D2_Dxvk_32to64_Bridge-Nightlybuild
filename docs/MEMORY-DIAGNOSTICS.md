# v1.0.0 纹理 shadow 地址空间回收与诊断

旧版进图采样中，纹理表面 shadow 达到 2,231,984,860 字节（约 2.08 GiB），加上顶点和索引 shadow 约 2.25 GiB。x86 进程空闲地址空间只剩约 147 MiB，最大连续空闲块约 55 MiB。这证明 bridge 的 CPU 副本造成严重地址空间压力；日志未记录最终异常，不能据此确定具体崩溃指令。

新版将非共享堆路径的纹理表面 shadow 改为 Windows 分页文件支持的 section。Lock 时映射并保持指针有效，Unlock 将写入数据复制到现有 IPC 后解除锁定。缓存超出预算时，优先取消最久未使用且未锁定的映射；section 保留全部内容，下次 Lock 重新映射，不依赖 GPU 回读。资源销毁时关闭 section。预算按 Windows 分配粒度计入对齐开销，避免大量小 mip 映射消耗过多地址空间。

默认 client.surfaceShadowCacheMB=128，可在现有 bridge.conf 添加该项；不添加也默认 128。0 表示解锁后不缓存映射；最大有效值为 1024 MiB。正在锁定的资源不会回收，所以同时锁定的大资源可以暂时超过预算。此版本减少的是 x86 映射和地址空间占用，保留数据的系统提交量和物理内存/分页文件需求仍然存在，顶点/索引 shadow 保留方式没有改变。它不是完整的资源迁移方案，游戏性能和兼容性仍须实测。

## 安装与复测

更新已有兼容安装时，下载 l4d2-bridge-client-only 更新包。关闭游戏及 Host，**只替换新包里的 bin/dxvk_d3d9.dll**，保留兼容的后端、L4D2Bridge64.exe 和原有 bridge.conf。首次安装使用 l4d2-bridge-v1.0.0 完整包，其默认后端为已验证的 DXVK 2.6.1 x64。保持 logLevel=Info、logApiCalls=False、logServerCommands=False。

从 Steam 用原来的 Mod 和同一地图再次进图。尝试正常游玩并退出后重新进图一次，检查贴图是否正常、是否崩溃及帧率。请提供 l4d2-memory.log、bridge32.log、bridge64.log，说明能否进图和实际表现；如有崩溃 dump 或报错窗口也一并提供。

采样文件是游戏 bin/l4d2-memory.log，与客户端 DLL 同目录，不跟随游戏工作目录或 DXVK_LOG_PATH。每个新进程首次采样覆盖旧文件，退出或崩溃后立即复制保存，避免下次启动覆盖。不需要逐调用日志。

## 日志字段

字段按字节记录：surface_bytes/count 现在是**当前映射**的纹理 shadow；surface_backing_bytes/count 是保留数据的 section 总量；surface_view_budget_bytes 是映射缓存计入对齐后的预算占用。后两者用于区分“内容仍保留”和“x86 映射已经回收”。无活动锁时，预算占用应不超过默认 128 MiB；加载后要结合 va_free、largest_free 判断地址空间是否恢复。

vertex_bytes/count、index_bytes/count 是顶点/索引缓冲 shadow，包括使用 shadow 的静态缓冲。va_committed、va_reserved、va_free、largest_free 是 x86 地址空间扫描；va_limit 是扫描上界；scan_complete 表示扫描是否完成。private_bytes 和 working_set 通过系统 API 读取，counters_valid=0 时不可使用它们判断。系统对映射内存的统计与旧版堆分配不同，不能只比较 private_bytes 判断所有资源占用。

采样由 Present 和 shadow 分配/映射触发，间隔至少五秒，没有后台线程；没有这些调用的阶段不会持续记录。统计是近似快照，不包含引擎其他内存、IPC 和代理对象。event=allocation-failed 记录缓冲 shadow 分配失败；section-create-failed、section-map-failed 记录 section 或映射失败，并附带 win32_error，立即刷新文件。没有失败事件不能排除其他位置的内存耗尽或访问错误。

Windows x86 自动测试覆盖：映射回收后内容恢复、活动锁和嵌套锁保持指针有效、128 个小映射的预算控制、资源销毁时清零计数，以及原来的诊断分配失败路径。通过这些测试不能替代 L4D2 实测。
