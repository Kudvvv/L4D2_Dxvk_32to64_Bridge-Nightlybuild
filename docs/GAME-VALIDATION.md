# 游戏验收与性能基线

状态：流程和工具已提供，尚无本批更新的游戏实测结果。CI 的 volume 测试执行真实 lock/unlock 源码，但模拟传输与后端，不替代画面对比。偏色定位与原修复 credits：[keyou91 / PR #3](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/pull/3)。

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

需要帧时间时使用已有的帧时间采集工具，导出**仅包含 L4D2** 的稳定测试时段 CSV，按实际列名和单位分析，不混入 Host、桌面或加载帧：

```powershell
python scripts/analyze_baseline.py ./results/new-map-run1 --frames ./captures/new-map-run1.csv --column FrameTimeMs --unit ms
```

`average_fps` 为 1000 / 平均帧时间；另报告 p99 帧时间及其对应 FPS，明确不称为“最慢 1% 平均 FPS”。每组用三次结果的中位数比较，同时保留单轮结果。先记录差异，不预设一定提高性能。

填写每个结果目录的 session.json；截图、帧时间、bridge32.log、bridge64.log、l4d2-memory.log 和 console.log 放入对应会话目录。崩溃保留部分采样与可用 dump。性能测试关闭逐调用日志，其他配置保持一致。

## 结果记录

使用 [基线表](BASELINE-RESULTS.csv) 的副本记录测试，每行对应一个场景的一轮运行。基线表只有表头，空表不表示测试通过。
