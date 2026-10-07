# 提议引入可追踪的 Nightly 构建与发布流程

希望将 [L4D2 Bridge Nightly](https://github.com/Kudvvv/L4D2_Dxvk_32to64_Bridge-Nightlybuild) 中已经运行并通过 CI 的构建、版本追踪和发布机制反馈给原项目，为测试 NVIDIA Bridge 新提交提供一个独立于稳定版发布的渠道。

Nightly 项目由 YuuMJ 与 Kudvvv 合作维护，目前仓库位于 Kudvvv 名下。项目建立在 [yeyunyyds 的 L4D2 Bridge](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) 和 [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix) 之上，原项目的 L4D2 适配、内存管理、兼容性修复和测试是重要基础。

## 可以反馈给原项目的价值

### 1. 持续跟踪 NVIDIA Bridge 更新

GitHub Actions 配置为每小时第 23 分钟检查 NVIDIA 仓库的默认分支，解析实际提交 SHA，对尚未发布的提交应用 L4D2 补丁、编译 x86 客户端和 x64 Host，再运行测试。默认分支名称由 API 查询，不固定写死为 `main`。

这使维护者和测试者更容易获取新上游版本，减少手动拉取、应用补丁、编译和打包的重复工作。GitHub 定时调度可能延迟，不能保证每小时准时运行。

### 2. 版本可追踪，问题更容易复现

Nightly 版本采用 `nightly-YYYYMMDD-上游短SHA-r输入指纹-b运行ID.重试号`，日期取自 NVIDIA 上游提交的 UTC 日期。去重同时考虑上游 SHA 与构建输入指纹，补丁或后端配置变化也会构建。Release 说明和包内 UPSTREAM.json 记录完整提交、输入指纹及构建实例。

手动构建支持指定完整 40 位上游 SHA，便于重建已知版本进行故障对照。`force_rebuild` 支持同输入再次构建，并生成独立版本。旧发布附件不会被自动覆盖，方便回退与对照。发布器校验附件 SHA-256 并拒绝替换已发布版本。

### 3. 编译与测试形成发布门槛

发布流程执行补丁应用检查、客户端与 Host 编译，并运行相关测试。当前 Nightly 包含 Python 发布检测测试、内存诊断与影子映射测试、纹理创建失败清理测试、ATI1/ATI2 x86/x64 布局与复制边界测试，以及跨进程队列通信、回绕、取消和超时测试。

编译或测试失败时，该轮构建不会产生可供发布的新附件。自动流程采用已发布上游提交去重，默认避免重复编译；GitHub API 请求失败会使检查失败，不会将错误响应误判为新提交。

这些渲染与队列测试主要来自原项目，我们的贡献是将适用测试接入跟踪上游的 Nightly 流程，并在当前上游版本上验证其可构建性。

### 4. Bridge 与 DXVK 后端分别管理

Nightly 使用独立的 `config/backend.json` 固定后端版本、下载来源及归档 SHA-256。更新 NVIDIA Bridge 不会同时隐式更新 DXVK 后端，有助于缩小画面异常、兼容性和性能问题的排查范围。

本 Nightly 当前采用 DXVK-GPLALL 2.6.8-2 x64，原项目 v1.1 采用官方 DXVK 2.6.1 并提供两种 Host。这里的价值是独立固定与校验机制，不能据此声称 GPLALL 普遍更快、更稳定或更省内存。原项目可以复用这套机制并继续使用自己的官方后端。

### 5. 精简且可校验的分发包

完整 ZIP 与配对更新 ZIP 保留运行文件、简短安装说明、来源元数据及许可证，默认将客户端放在 `bin/d3d9.dll`，无需 `-vulkan` 启动项；Host、配置和后端保留在 `bin/.l4d2bridge`，并提供独立 `.sha256` 附件。更新包同时更新客户端和 Host，不携带配置、后端、ReShade 或 DB。构建脚本在打包前检查 PE 位数，避免把普通 DXVK 后端误装为 Bridge 客户端。

源码、实验文档和开发元数据保留在仓库中，用户下载的运行包更容易安装、备份和核对来源。中英文 README 分别说明安装路径、自动构建和手动重建方法。如需使用 `-vulkan`，用户自行将客户端改名为 `dxvk_d3d9.dll` ，文件仍留在 `bin`。客户端会按安装位置定位共享运行目录，相关路径测试在 x86/x64 上通过。

## 偏色问题与 Credits

**偏色问题首先由 [keyou91](https://github.com/keyou91) 在原项目 [PR #3：修复三维纹理上传步长错误导致的服务器偏色](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/pull/3) 中提出并提供修复。问题定位、原始修复和原偏色服务器的成功实测应归功于 keyou91。**

该 PR 指出三维纹理的 `RowPitch`、`SlicePitch` 错把块数作为字节步长，可能破坏颜色校正查色表；修复调整字节步长和上传偏移，保持 Host 原有字段含义，并正确释放数组。Nightly 移植了提交 `fb1507d` 的修复，将其与当前 NVIDIA 上游及配套构建流程集成，已通过编译。我们不将其表述为 Nightly 首次发现或独立原创的修复，也不将作者的游戏实测视为本 Nightly/GPLALL 组合已完成实测。

PR #3 应保留独立的贡献记录。如本 PR 涉及同一修复，应引用该 PR 和原作者，避免重复归属或以 Nightly 的名义取代其贡献。

其他 Credits：

- **yeyunyyds 及原项目贡献者**：L4D2 Bridge 适配、影子内存管理、纹理创建失败处理、ATI1/ATI2 修复、命令队列优化及配套测试。
- **NVIDIA 及 dxvk-remix/Bridge 贡献者**：Bridge 基础实现。
- **DXVK、DXVK-GPLALL 及依赖贡献者**：后端和相关组件，保留各自许可证及版权声明。
- **YuuMJ、Kudvvv**：Nightly 项目的合作维护、上游跟踪构建、发布组织与修复集成。保留原项目已有的 OpenAI Codex 生成来源声明，该声明不应覆盖 keyou91 或其他作者的原始贡献。

## 已验证的范围

[2026-10-07 成功构建记录](https://github.com/Kudvvv/L4D2_Dxvk_32to64_Bridge-Nightlybuild/actions/runs/37573218752)：

- Nightly 构建配置提交：`e486a46`。
- NVIDIA Bridge 上游提交：`e4e7303d6d9cf2cb9e53029277c62f8f7d8c5a98`。
- x86 客户端与 x64 Host 编译成功，相关原生测试与发布步骤通过。
- 三维纹理测试执行实际 lock/unlock 代码，在 x86/x64 的逐行和整块上传模式通过；模拟传输/后端。负向测试确认可捕获旧 RowPitch 错误，并补充尺寸边界与溢出检查。
- [独立发布版本](https://github.com/Kudvvv/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases/tag/nightly-20261006-e4e7303d-r1db6d95be939-b37573218752.1)提供完整包和配对更新包，已核对校验值及包内容；旧附件保留。
- 已提供固定游戏复测流程、进程采样和帧时间分析工具，结果表待实际测试填写。

当前证据支持构建与自动化测试通过，尚不足以证明所有显卡、Mod、地图、叠加层或长时间游戏都兼容。Nightly 的主要优势是更方便地测试和追踪新上游版本，不代表其性能或稳定性超过原项目 v1.1。

## 建议的 PR 范围

建议先引入可独立审阅的 Nightly 构建工作流、提交检测与去重、版本命名、后端固定与校验、运行包归档及相关文档，沿用原项目自己的补丁和测试。稳定版发布保持现有流程，Nightly 使用预发布渠道。

原项目已有的修复不需要从我们的简化补丁重复反向合入；偏色修复优先沿用 PR #3 的贡献记录。原项目 v1.1 的 learned-aggressive 内存策略、ReShade presenter、x86 Host 等功能也应保留。我们的构建机制可以按原项目架构调整，不应直接用 Nightly 的补丁或配置覆盖原项目功能。

本文是一份供 PR 描述使用的提案；实际 PR 标题、变更说明和验证记录应与提交的 diff 保持一致。
