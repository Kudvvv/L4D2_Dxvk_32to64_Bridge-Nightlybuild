# 进图崩溃诊断版

保持此前能运行的 DXVK 2.6.1 x64 后端。只替换新包里的 bin/dxvk_d3d9.dll；Host 无需替换。保留当前 bridge.conf 的 logLevel=Info、logApiCalls=False、logServerCommands=False。这版没有改变 shadow 保留、IPC 容量或资源生命周期，目标是定位崩溃。

退出游戏和 Host 后替换客户端。从 Steam 启动，使用原来的 Mod 和同一地图再次进图。采样文件为游戏 bin/l4d2-memory.log，与客户端 DLL 同目录，不跟随游戏工作目录或 DXVK_LOG_PATH。每次新进程首次采样覆盖旧文件，崩溃后立即复制保存，避免下次启动覆盖。

请提供 l4d2-memory.log、bridge32.log、bridge64.log；如果有崩溃 dump 或报错窗口，也一并提供。无需手动开启逐调用日志。

字段全部按字节记录：surface_bytes/count 是纹理表面 shadow；vertex_bytes/count、index_bytes/count 是顶点/索引缓冲 shadow（包括使用 shadow 的静态缓冲，不仅动态缓冲）。va_committed、va_reserved、va_free、largest_free 是 x86 地址空间扫描；va_limit 是扫描上界；scan_complete 表示扫描是否完成。private_bytes 和 working_set 通过系统 API 读取，counters_valid=0 时不可使用它们判断。

采样在 Present 和 shadow 分配时触发，间隔至少五秒，不创建后台轮询线程。没有这些调用的阶段不会持续产生日志；各 shadow 总量是同时读取的近似快照，不保证在多线程释放时完全一致。统计不包含队列、引擎模型/脚本、对象代理、临时复制和其他未插桩分配。

event=allocation-failed 会记录该 shadow 分配的类型、requested、width、height、format，并立即刷新文件。它保留原始异常，不把失败改成成功。没有该事件不能排除其他位置内存耗尽或访问错误。

该版本会增加少量采样开销，不是性能基准版本。我们将据此判断地址空间耗尽、碎片化或其他资源错误，再做针对性修复。
