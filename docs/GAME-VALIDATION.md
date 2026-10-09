# 游戏验收与性能基线

状态：流程和工具已提供，尚无本批更新的游戏实测结果。CI 的 volume 测试执行真实 lock/unlock 源码，但模拟传输与后端，不替代画面对比。偏色定位与原修复 credits：[keyou91 / PR #3](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/pull/3)。

2026-10-08 的候选版本已尝试启动，受到 Source 单实例限制，未进入渲染阶段；原有配对文件已恢复。详情及独立 CPU 微基准见 [资源清理与传输优化验证](RUNTIME-RELIABILITY.md)。该次尝试不计为游戏验收通过。

## 固定测试条件

备份安装与 Steam 启动参数。记录 UPSTREAM.json 中 release_tag、上游 SHA、recipe_digest，以及后端 DLL SHA-256、显卡、驱动、游戏构建、Mod 清单、配置、分辨率、画质和帧率上限。基线用正常可运行的无桥安装；Bridge 用同一后端版本及相同配置。无桥与 Bridge 位数可能不同，应记录这一差异。

用三组配对场景：旧 Bridge、新 Bridge、无桥。每组至少重复三次，固定地图、位置、视角和路线；预热至少 60 秒，剔除载入与预热时段。首轮保留相同 Mod 验证真实问题，另做无 Mod 对照排查。

## 功能验收

| 项目 | 步骤 | 合格条件 | 证据 |
|---|---|---|---|
| 原偏色地图 | 相同地点/视角分别截图旧桥、新桥、无桥 | 新桥色调接近无桥基线，无新色带/贴图异常 | 未压缩截图，地图及构建信息 |
| 纹理与截图 | 检查人物/武器/法线贴图，截图，切换窗口和分辨率 | 无新增花屏、缺图、黑屏或崩溃 | 截图与两侧日志 |
| 连续换图 | 至少换图 3–5 次，包含官方地图及原问题地图 | 不挂起，贴图正确 | 日志、内存采样 |
| 稳定性 | 至少游戏 30 分钟后正常退出 | 无崩溃，Host 正常退出；内存趋势有记录 | 两侧日志及进程 CSV |
| 回退 | 同时恢复备份的客户端与 Host | 能正常进入同一场景 | 回退版本和结果 |

升级已有安装使用 `l4d2-bridge-update-*` ZIP，合并到游戏根目录，同时更新 `bin/d3d9.dll` 和 `bin/.l4d2bridge` 中的 Host。默认移除 `-vulkan`。需要该启动项时自行把客户端改名为 `dxvk_d3d9.dll`，文件仍留在 `bin`。更新包不含 bridge.conf、DXVK 后端、ReShade 或 DB。首次安装使用完整包；完整包会替换配置与后端，覆盖前备份。

## 采样

先进入稳定的菜单或地图，再在仓库根目录打开 PowerShell。工具只读取当前 L4D2 和对应 Host，输出新目录，不覆盖既有结果。

```powershell
./scripts/collect_baseline.ps1 -Mode bridge -Label 'new-map-run1' -OutputDirectory './results/new-map-run1' -Seconds 120
./scripts/collect_baseline.ps1 -Mode no-bridge -Label 'baseline-map-run1' -OutputDirectory './results/baseline-map-run1' -Seconds 120
python scripts/analyze_baseline.py ./results/new-map-run1
```

分别记录菜单（评估空闲 Host CPU）和固定战役路线（评估负载）。CSV 含归一化到全部逻辑处理器的 CPU 百分比、working set、private bytes 和句柄数。它不测帧率、GPU 内存或剩余 x86 虚拟地址空间；后者参考同一会话的 `l4d2-memory.log`，不能把 working set 当成地址空间。

需要帧时间时使用已有的帧时间采集工具，导出稳定测试时段、单一进程和单一交换链的 CSV。**Bridge 的实际 Present 来自 `L4D2Bridge64.exe`；无桥时取游戏进程。** 不混合游戏侧与 Host 事件，不混入桌面、加载或预热帧；游戏内 FPS 计数应单独记录，不能当作 Host 的实际显示帧率。记录采集工具版本、进程 ID、交换链、帧时间列及其含义；例如 Present 间隔衡量提交节奏，不一定等于屏幕实际显示的帧间隔。按实际列名和单位分析：

```powershell
python scripts/analyze_baseline.py ./results/new-map-run1 --frames ./captures/new-map-run1.csv --column FrameTimeMs --unit ms
```

分析器在 CSV 保留 `Application`、`ProcessID`、`SwapChainAddress` 等身份列时检查其单一性，发现混合进程或交换链会拒绝汇总；输出 `source` 保存可识别的身份值。未提供这些列时无法自动验证来源，必须先在采集或导出环节筛选，不能直接汇总多个进程的 CSV。

统计口径如下，N 是本轮有效帧数，帧时间均换算为毫秒：

| 输出 | 公式与含义 |
|---|---|
| `average_fps` | 1000 / 全部 N 帧的平均帧时间。 |
| `low_1_percent_fps`、`low_0_1_percent_fps` | 分别取最慢 `ceil(N × 0.01)`、`ceil(N × 0.001)` 帧，计算 **1000 / 这些帧的平均帧时间**。不是百分位帧时间的倒数，也不是逐帧 FPS 的算术平均。 |
| `low_*_percent_tail_frames`、`low_*_percent_sample_status` | 报告实际选取的尾部帧数。少于 10 帧标为 `insufficient_tail_samples`，仍保留计算值便于复核；达到 10 帧标为 `minimum_tail_samples_met`，仅达到最低报告门槛，不表示统计结果已稳定。 |
| `p99_frame_time_ms`、`p99_9_frame_time_ms` | 帧时间升序排列后，在下标 `(N−1) × p` 处线性插值，p 分别为 0.99、0.999；样本尾部稀疏时估计同样不可靠。 |
| `fps_at_p99_frame_time` | 保留原字段：1000 / p99 帧时间，**不称作 1% low**。 |
| `maximum_instantaneous_fps` | 1000 / 最短单帧时间；易受单个异常样本影响，不代表可持续最高帧率。 |

先保证足够的尾部样本（至少约 1,000 帧用于 1% low、10,000 帧用于 0.1% low），同时保留原始帧时间，避免把少量尖峰或偶然短帧解释成优化收益。每组至少三次，用单轮结果的中位数比较，并保留全部单轮结果。优先比较 low 帧和尖峰，再看平均帧率，最高瞬时 FPS 仅作附带记录；不预设一定提高性能。

填写每个结果目录的 session.json；截图、帧时间、bridge32.log、bridge64.log、l4d2-memory.log 和 console.log 放入对应会话目录。崩溃保留部分采样与可用 dump。性能测试关闭逐调用日志，其他配置保持一致。

## 结果记录

使用 [基线表](BASELINE-RESULTS.csv) 的副本记录测试，每行对应一个场景的一轮运行。基线表只有表头，空表不表示测试通过。
