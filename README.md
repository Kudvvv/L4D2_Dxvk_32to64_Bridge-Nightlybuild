# L4D2_Dxvk_32to64_Bridge

面向 Windows、以 Intel Arc B580 为首个验收平台的 x86 → x64 D3D9 桥接实验。L4D2 保持 x86，x64 Host 使用普通上游 DXVK。

首轮基于 NVIDIA RTX Remix Bridge 的普通 DXVK 后端分支，保留窗口协调、IPC 和资源代理，禁用 Remix API 暴露。名称中的 NVIDIA 不构成兼容性证明；B580 支持需要实测。

当前状态：用户用 DXVK 2.6.1 在 Arc B580 上带全部原有 Mod 正常进入战役，主观反馈流畅、未观察到掉帧。可回收映射版本的日志确认缓存预算不超过 128 MiB、战役阶段 x86 空闲地址空间约 2.11 GiB，并正常退出。首次进图和地址空间回收已验证，长时间运行、连续换图及性能对照仍待验证。实测依据见 [FIRST-GAME-VALIDATION.md](docs/FIRST-GAME-VALIDATION.md)，安装及日志说明见 [MEMORY-DIAGNOSTICS.md](docs/MEMORY-DIAGNOSTICS.md)。

构建和验收步骤见 [TESTING.md](docs/TESTING.md)。Windows 构建工具采用 VS2022 + MSVC v142（14.29）+ Windows SDK、Python、Meson、Ninja。上游固定提交为 `9aa74f8dfad2188efbd0f717c64d9f8fa909787e`，补丁位于 `patches/l4d2-experiment.patch`。
