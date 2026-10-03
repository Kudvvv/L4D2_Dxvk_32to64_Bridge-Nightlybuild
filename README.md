# L4D2_Dxvk_32to64_Bridge

面向 Windows、以 Intel Arc B580 为首个验收平台的 x86 → x64 D3D9 桥接实验。L4D2 保持 x86，x64 Host 使用普通上游 DXVK。

首轮基于 NVIDIA RTX Remix Bridge 的普通 DXVK 后端分支，保留窗口协调、IPC 和资源代理，禁用 Remix API 暴露。名称中的 NVIDIA 不构成兼容性证明；B580 支持需要实测。

当前状态：已完成源码检查、后端初始化适配、Windows 构建及打包流程；**尚未完成 Windows 编译或 L4D2 实测，没有已验证可运行的 Demo**。

构建和验收步骤见 [TESTING.md](docs/TESTING.md)。Windows 构建工具采用 VS2022 + MSVC v142（14.29）+ Windows SDK、Python、Meson、Ninja。上游固定提交为 `9aa74f8dfad2188efbd0f717c64d9f8fa909787e`，补丁位于 `patches/l4d2-experiment.patch`。
