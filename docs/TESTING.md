# Nightly 构建与验收

当前源码完整同步原项目 1.2.1，同时保留 Nightly 修复；对应关系见 [更新跟踪](ORIGINAL-PROJECT-UPDATES.md)。下载、备份与 ThinFlex 精确版本核对见 [README](../README.md)。本次合并的自动测试不等于已经完成本地 L4N 长时间实测。

## 构建

Windows 10/11 x64，Visual Studio 2022，MSVC v142 / 14.29 x86/x64 工具、Windows SDK、Python 3.11 和 Git。

```powershell
python -m pip install meson==1.3.2 ninja==1.11.1.1
./scripts/build_bridge.ps1
```

默认下载并核验固定 GPLALL 后端的 x86/x64 DLL。构建配套 x86 Client、x64 Host、隔离构建目录中的 x86 Host 和 L4N v2 插件；只初始化所需 Detours 子模块，不构建 RTX 渲染器。源码复用必须完全符合固定 NVIDIA 提交与当前补丁，不允许混入本地源码更改。输出的主安装目录为 `dist/l4d2-bridge`，Release 仅压缩成一个完整包及 SHA256；没有 update 或独立插件 ZIP。Host32 检查 LARGEADDRESSAWARE，三主程序检查共同 build ID。

主流水线是 **Build latest upstream Bridge**。手动运行可指定完整 `upstream_commit`、启用 `force_rebuild`，或用 `validation_only` 只验证并保留测试结果。可选 DXVK 内存实验有独立手动构建入口，其后端不替换 GPLALL 默认值。

## 自动回归范围

准备源码后，CI 运行 Python 发布、精确源码保护、打包及分析器测试，并编译运行以下生产代码回归：

- PageBlock residency / GC / retention / readback recovery、L4N modern/legacy/missing ABI 和配置保存。
- runtime observation 关闭门与失败隔离、memory/host/exception/data/color/API-wait 诊断、VA schema=3。
- Reset 状态机、adapter 信息、真实 x86 后端载入和跨进程 Presenter。
- 纹理/缓冲/表面创建失败清理、ATI 布局、Volume 锁与上传、Surface 连续复制、buffer contract。
- 队列跨进程唤醒/取消/超时、多容量顺序、输入 hook/DirectInput/Query。
- Logger 名称所有权、禁用时无格式化、buffer lazy logging 与必要分配。
- 异步内存采样的真实线程池/模块引用、卸载生命周期、失败同步刷新和故障注入。
- 原生 ThinFlex create/verify 与 Python 等价性；最终 DLL 固定哈希与 PE 架构。

Nightly 已有负对照继续作为门槛，不以纯粹的固定代码字符串检查代替行为回归。测试矩阵的准确入口以 `.github/workflows/upstream-release.yml` 为准；脚本失败阻止发布。下载后的最终 ZIP 再核对 SHA256、文件清单、PE 位数、build ID、GPLALL 和 ThinFlex 哈希。

## 游戏验收边界

以 [GAME-VALIDATION.md](GAME-VALIDATION.md) 为准，保留同场景、配置、画质及驱动条件。关闭 VSync/GSYNC 等外部限制后才能测量未封顶帧率。按菜单、进图、联机过图、切换窗口/分辨率、退出顺序检查，分别记录 x64/x86 Host；可选 Presenter/ReShade 和 L4N 菜单要另验。

性能目标仍为 1%/0.1% low、平均帧和最高帧，实测需要重复对照与帧时间分布。既有 [三对 L4N 回放](PERFORMANCE-2026-10-10.md) 属于早前 v1.0.11，不能外推为这次完整上游合并的性能收益。此轮不自动启动游戏或更改玩家安装。

## 诊断分离回归

`scripts/test_input_hooks.ps1` 从生产 Client 文件提取实际 hook 安装/卸载、DirectInput A/W 创建与 Query AddRef/Release 方法，在 x86/x64 上使用确定性 Win32/COM 适配器。覆盖关闭时不安装、仅三个线程 hook、失败后继续安装其他 hook、即时捕获 GetLastError、仅卸载有效 handle、日志失败不阻断安装；旧版请求和失败的原参数/HRESULT 保持不变、关闭 Debug 时不格式化成功提示、Query 委托基类且不打印 missing-call。COM 适配器验证委托调用，并不代替真实 GPU Query 生命周期验收。

准备源码后运行 `scripts/test_runtime_observation.ps1`（x86/x64）。测试从生产文件提取 startup/logger/input 函数，结合真实诊断、PageBlock 和 Presenter 实现，仅用确定性适配器替代 detour 安装及 runtime 环境。仅测试二进制强制包含 Win32 计数器，并替换堆分配入口；发行构建没有这些计数器。

off 模式重复 1000 次调用，断言诊断扫描/时钟/文件/线程/hook/HWND/模块查询/SRW 锁/分配均为零，command ring、memory 与 queue 计数不更新；用不可解引用 Device 指针证明没有诊断 Getter。随后调用真实 control ABI 的 GC handler，分别运行 shadow + AGC/FGC，区分每次单个实际 mapped-view VirtualQuery 和 GC 结果计时。独立进程的 monitor-on/input-on/crash-on/logging-on 是正对照。OFF 进程必须没有新 .log 文件。各启用诊断的既有回归仍必须通过。

另覆盖 init-failure、allocation-failure、data-on、observer-failure、lg-off、retention-log-failure、retention-write-failure、retention-callback-failure，总共 13 个独立进程模式。OFF 要求 API wait 表、TLS crash history 和 Data Resource metadata 不存在；随后真实 Core VB/IB 分配仍正常。启用失败注入文件/线程/堆分配与抛异常回调；retention 测试使用生产 Runtime/Database/Parent/Entry 和 Host `runShared` 验证驱逐、preserve miss、独立 mock 内容恢复、KEEP 提升及新 Runtime 的持久 DB 命中，不能进入 fallback KEEP。buffer contract 使用生产 Core allocator，仍保留 FULL_SHADOW 原契约。

`python -m unittest discover -s tests -p test_runtime_separation.py` 检查受保护 Volume 生产代码/测试的基线哈希、配置/ABI/关闭门和默认 Tracy 构建。其余 PageBlock GC、readback、buffer contract、Reset、queue、ATI/adapter 与原 Volume suite 不改变语义。实机仍需双 Host、联机过图、窗口切换及启用 Presenter/ReShade 输入验证；计数器测试不代表真实游戏/驱动已覆盖。
