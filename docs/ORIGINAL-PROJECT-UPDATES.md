# L4D2 原项目完整同步

当前隔离候选完整功能基准：[`de74cd7d5dd546bfd4f03ab451d0565f1fff0107`](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/tree/de74cd7d5dd546bfd4f03ab451d0565f1fff0107)，即上游 **1.2.2 可选稳定性更新**。本分支 v1.2 在此前完整基准 `cf49175` 上同步全部新增源码、测试与说明；两者版本号独立。候选尚未合入 main 或发布；正式版完整基准仍为 `cf49175`，默认下载保持 v1.1.10，性能/加载取舍与验证范围见 [本次集成说明](UPSTREAM-1.2.2-INTEGRATION.md)。

用户于 2026-10-10 明确授权完整合并上游，包括上游新增功能。“不自行增加功能”不再作为筛除上游能力的理由。Git 合并保留两侧提交历史；以完整上游 Bridge 源码为基础融合 Nightly 修复，后续在此基准上增量同步。

## 本次功能范围

2026-10-11 完整同步双向数据环完整预留、消费进度原子发布与等待重查、失败批次中止、Header 有界提交、请求/回复所有权清理、optimized Lock 指针保留、已知包完整规划及环尾 padding 消费。IPC 协议为 3，Client 与两个 Host 必须配套。保留原有 FULL_SHADOW、画质、后端和配置选择；不恢复已撤回的 Nightly 绑定引用优化。上游正常路径/实机性能报告原文保留，但不能作为本分支性能提升证明。

完整保留上游 PageBlock residency、keep/learned-aggressive/drop、LGC/AGC/FGC、retention DB、Host ACK 和 readback recovery；Reset 状态机及等待；Presenter/ReShade 与 Steam 输入路径；x86/x64 Host、adapter/caps；L4N v2 设置/保存 API 与插件；memory/crash/data/color/API-wait 诊断及关闭时零观察开销；相关配置、实验源码、分析工具、文档与测试。

## Nightly 兼容差异

- 默认仍为 x64 Host，x86 Host 与匹配后端随完整包提供。GPLALL 2.6.8-2 两种架构按固定归档与文件哈希校验，实验 DXVK 后端仍通过独立手动实验入口构建。
- 继续使用 `bin/d3d9.dll` 的默认客户端路径，支持用户为 `-vulkan` 改名；Host 与后端位于 `bin/.l4d2bridge`。新诊断工具与 L4N 接口兼容两种客户端名称。
- 保留纹理字节布局/偏色修复、额外资源创建失败清理、buffer lock 边界、连续上传复制、Logger 名称所有权与队列优化。内存监控开启时沿用异步普通采样，关闭时遵循上游新开关，不调度采样。
- 新安装采用上游的新增 Bridge 配置与策略，唯 Host 默认保持 x64。L4N 与 DXVK 配置按用户提供的整合目录随包；升级先从临时目录移除想保留的配置，再覆盖，操作见 README。retention DB 不随包。
- 只发布一个完整 ZIP 及 SHA256，包含配套 Client、两种 Host/GPLALL、固定 ThinFlex `studiorender.dll`、Starfelll 的 L4N 2.51.0、用户提供的 `dxvk.conf`/`config.vdf` 及直接安装的 `bin/neko/plugins/L4D2BridgePlugin.dll`；不附 `config_template.vdf`，不恢复 update 包或独立插件/ThinFlex 工具包。L4N 来源与归属见 [整合说明](L4N-BUNDLE.md)。玩家 ZIP 保留运行组件、实际配置、L4N 配套 VDF 模板与 QC/VMT 范例、安装说明与合并归属文本；文档、JSON、SDK、诊断脚本及离线 Mod 制作工具留在仓库。加载设置插件本身不改配置或执行 GC，需玩家主动操作；不需要菜单时可退出游戏后移走该 DLL。
- 保留精确源码/暂存区校验、构建指纹、发布草稿重试及附件不可覆盖保护；增加三程序共同 build ID、PE 架构和 x86 Host LARGEADDRESSAWARE 验证。

## 验证边界

2026-10-10 后续完成[手电专项对照与命令热路径优化](FLASHLIGHT-PERFORMANCE-2026-10-10.md)。仅减少就绪队列计时和进程内保护标志的冗余开销；没有添加绑核策略、替换后端或更改默认配置。实测受本机双 CCD 调度影响，尚未证实稳定 FPS 增益；详细数据和发布重建边界见该报告。上游完整同步基准不变。

补丁必须分别对 NVIDIA 原始基准 `9aa74f8dfad2188efbd0f717c64d9f8fa909787e` 和固定构建源 `5fd30eae2d397f369bdf5660f3ddd0bc0bd1fa58` 通过应用校验。完整 Python 回归、上游原生测试和 Nightly 的资源/边界/日志/异步/ThinFlex 回归是发布门槛；CI 构建 x86 Client、x64/x86 Host 和 L4N 设置插件，再下载核验最终全量包。

本地验证：164 项 Python 回归全部通过（包含实际 ThinFlex 原生工具和准备后的 runtime separation，无跳过）；上游 Volume、Reset、PageBlock、配置与跨进程 readback/adapter 测试在 GCC x86/x64 通过。Nightly 上传、资源清理、日志、输入、异步 DLL 及原缺陷负对照通过。正式 MSVC 完整编译和测试仍由对应 Actions 判定，未用 GCC 的兼容参数降低 CI `/W4 /WX` 门槛。

本次不自动启动游戏。此前 v1.0.11 的三对 L4N 回放不是当前完整合并版本的性能证明，不承诺帧率上涨；上游实测也不能替代本 Nightly/GPLALL 组合的运行验证。具体结果以本提交对应 Actions 和 Release 为准。

完整合并的首轮 MSVC 构建 `38020218495` 完成各主程序编译，但本地 Reset 生命周期回归的链接命令缺少 `user32.lib`，未发布。已为正向与负对照补齐该依赖，并严格要求负对照返回预期的断言失败码。本次整合包与修正共同重新构建，结果以新提交的 Actions 为准。

后续构建 `38021878907` 通过完整编译、上游原生回归和 Reset 测试，在本分支三维纹理分配故障夹具失败，未发布。夹具需显式拦截上游改用的 `nothrow new[]`，并区分协议容量与 MSVC x86 数组长度限制；普通分配故障仍必须实际进入拦截器，超限数据仍必须在分配前拒绝。这项修正只调整测试适配，不修改游戏运行补丁。

之前的选择性移植与延期决策保留为 [历史记录](ORIGINAL-PROJECT-UPDATES-HISTORY.md)，已不再限制后续完整同步。
