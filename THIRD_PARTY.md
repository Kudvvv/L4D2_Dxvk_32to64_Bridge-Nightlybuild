# 第三方归属与许可

本项目新增及修改的代码由 yeyunyyds（GitHub 用户名）完全使用 ChatGPT-6.1 Sol 生成，采用根目录 [LICENSE](LICENSE) 的 MIT 许可。该声明不包含上游原始代码；原始代码归对应原作者所有。

## NVIDIA RTX Remix Bridge

- 来源：https://github.com/NVIDIAGameWorks/dxvk-remix
- 固定提交：`9aa74f8dfad2188efbd0f717c64d9f8fa909787e`。
- Copyright 2022–2024 NVIDIA CORPORATION & AFFILIATES，以及各文件声明的权利人。
- 使用范围：Bridge 子项目及其依赖，不构建或分发 RTX 渲染器。
- Bridge MIT 原文：[licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt)。
- 上游第三方许可原文：[licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt)。其中还包括 DXVK 来源的配置代码、Tracy 等组件，适用原声明。
- 本项目补丁保留原文件版权声明，仅在修改部分添加项目署名。

## DXVK

- 来源：https://github.com/doitsujin/dxvk
- 第一版默认随包使用官方 v2.6.1 的 x64 `d3d9.dll`，仅改名为 `d3d9vk_x64.dll`，不修改该 DLL。
- 原版权归 Philip Rebohle、Joshua Ashton、Robin Kertels、Jeffrey Ellison 及对应贡献者。
- zlib/libpng 许可原文：[licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt)。
- 发布归档 SHA-256：`7ee0bef415910c943d3bda47d9d6821b9c8ca7a74f1e9f6151707d268cf3ce7f`，CI 在解压前检查。

## Microsoft Detours

- 来源：https://github.com/microsoft/Detours
- 通过上游子模块固定到 `ea6c4ae7f3f1b1772b8a7cda4199230b932f5a50`。
- Copyright Microsoft Corporation；MIT 许可。
- 许可原文见 [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt) 中 Detours 部分。

## Tracy 与上游所含其他组件

- Tracy 来源：https://github.com/wolfpld/tracy
- Copyright Bartosz Taudul；BSD-3-Clause 许可。
- 完整条款及上游其他组件声明见 [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt)。
- 这些许可随完整包和客户端更新包一并分发，不能以根目录 MIT 许可替代。

## TXVK 参考与游戏平台

TXVK（https://github.com/tianxiaols/TXVK，作者 tianxiaols）的公开文档、配置和发布二进制用于静态行为分析与实现思路参考。本项目没有恢复或复制其完整定制源码，不分发其客户端、Host 或定制 DXVK 二进制，也不声称拥有其原始代码。

L4D2 与 Steam 属于 Valve，游戏及平台不包含在本项目的授权范围内。显卡驱动亦遵循各厂商自己的许可。
