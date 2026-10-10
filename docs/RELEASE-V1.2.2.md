# v1.2.2（Optional / 可选更新）

**本版以地图加载稳定性为重点，是可选更新。** 如果你使用 v1.2.1 时没有遇到进图或切图闪退，可以继续使用原版本，无需升级。

v1.2.2 修复了多项可能在地图加载和切换期间触发的 IPC 问题，包括数据队列覆盖风险、遗漏唤醒、等待失败后仍继续提交，以及大数据包在特定回绕位置被错误拒绝。已在用户本次 x64 Host 实机测试中验证枪店图与训练图可以来回切换；这不代表所有地图和长时间游玩均已验证。

## 性能取舍

本版优先保证传输正确性和加载稳定性，部分场景可能出现约 **10% 的 FPS 下降**，实际幅度因地图、场景与系统负载而异，个别场景可能更高。本次初步截图对照中，相对 v1.2.1 的 Avg FPS 降幅约为 **1%～19%**；样本未使用统一回放和逐帧采样，不能视为固定损耗或归因到单一 IPC 改动。1% Low / 0.1% Low 尚无一致结论。

用户另反馈从枪店切换到训练图时，加载时间相比 v1.2.1 增加约 20 秒；原因仍在调查。选择本版时请同时考虑加载时间与 FPS 的取舍。烟花粒子炸面/花屏、Steam Overlay/Shift+Tab 等问题不在本次已确认修复范围内。

## 下载与升级

- `l4d2-bridge-patch-v1.2.2.zip`：已有安装优先使用，更新匹配的 x86 Client、x86 Host、x64 Host，保留现有配置、DXVK、ReShade、L4N 插件和 retention DB。
- `l4d2-bridge-v1.2.2.zip`：首次安装用完整包，包含配套 Bridge、官方 DXVK 2.6.1 和默认配置；已有定制配置/后端的用户使用补丁包。
- `SHA256SUMS.txt`：下载附件校验；包内另有三个二进制的哈希和构建版本。

退出游戏及所有 Host，备份 `bin/dxvk_d3d9.dll`、`bin/.l4d2bridge/L4D2Bridge32.exe` 和 `L4D2Bridge64.exe`，然后一起替换。若原安装使用另一 Client DLL 名称，沿用原加载方式。IPC 协议为 3，不能混用旧 Client/Host。回退时退出游戏并将三个备份文件一起恢复。

L4N 插件本次未修改，继续使用现有插件或 [v1.2.0 独立插件包](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/releases/tag/v1.2.0)。详细安装见 [README](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/v1.2.2/README.md)。

## 验证范围

正式版本保持当前 PR #6 生产修复不变，累计补丁 SHA-256 为 `e8a61ece359546f8b1ca815f3e708b8bb8caef12b3be8f46de0d3b46201a3ee9`。三个正式二进制重新编译，构建 ID 为 `l4d2-1.2.2+e8a61ece359546f8`。

发布前运行完整 Windows 构建、IPC 原生 x86/x86 与 x86/x64、回绕/满载/故障及资源生命周期回归。实机地图切换结果来自同生产补丁的 v1.2.1 测试包，正式 v1.2.2 二进制尚未单独实机复测。性能资料见 [本次实机原始记录](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/v1.2.2/docs/LDB-PR6-GAMEPLAY-PERFORMANCE-2026-10-10.md) 和 [IPC 性能调查](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/v1.2.2/docs/IPC-NORMAL-PATH-PERFORMANCE.md)。

## English

Optional update focused on map-loading stability. If v1.2.1 works without map-entry or map-switch crashes, you can keep using it. This release fixes IPC overwrite, wakeup, failed-submission and large-upload wrap issues. The tested gun-range/training-map transitions now work with the same production patch.

Some scenes may lose roughly 10% FPS, with larger losses possible; the preliminary screenshots showed approximately 1–19% lower average FPS. Loading may also take longer. This is a stability/performance tradeoff, not a universal performance improvement. Update all three matched Bridge binaries together and preserve your existing configuration and backends.
