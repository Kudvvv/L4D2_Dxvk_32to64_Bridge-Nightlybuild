# L4N 整合包

本构建包含 DXVK-GPLALL、L4N 2.51.0 和 Bridge 桥接工具，按 [README 的下载与安装步骤](../README.md) 解压覆盖即可安装。不要与其他同类项目或整合包混装；先移除 `-vulkan`，备份移走游戏根目录的 `d3d9.dll`，保留本包的 `bin/d3d9.dll`。

**L4N / Left4Neko 原作者为 Starfelll，原文件署名为 @Starfelll。** 本仓库负责组合交付和 Bridge 构建，不将 L4N 标为本项目或 Codex 原创。原 `readme_l4n.txt` 与 [L4N 归属说明](../licenses/L4N-NOTICE.txt) 的原文收录于包内唯一的 `THIRD-PARTY-NOTICES.txt`。原说明涉及普通 DXVK 的安装路径时，以本整合包的 Bridge 路径为准。

## 文件来源

- 原始 L4N 2.51.0 包由维护者提供，归档 SHA-256 为 `5a530a24ee0e8a3014ab99df35e22279e410bed1a1f4cca1a08c2eb058eb0d4c`。源码校验材料从原 76 个文件保留 75 个，按用户要求省略 `left4dead2/neko/config_template.vdf`；保留的文件均不修改。
- 维护者提供的 `L4N+64位补丁_10101041` 整合目录另外贡献三个文件：根目录 `dxvk.conf`、实际使用的 `left4dead2/neko/config.vdf`、`left4dead2/shaders/fxc/neko_floattoscreen_ps20b.vcs`。这些是用户提供的预设，不表示 L4N 原版默认值，也不是本次新增的性能优化。
- 源码中的 L4N 校验集合共 78 个文件，`runtime/l4n/manifest.json` 记录来源及每个文件的大小和 SHA-256。归档前仍逐个验证完整来源，玩家 ZIP 只输出其中 53 个运行文件，共 10,015,177 字节，不包含 JSON 清单。
- Bridge Client、x64/x86 Host 和可选设置插件来自本次源码构建，GPLALL 与 ThinFlex DLL 分别使用固定校验的版本。不会使用桌面整合目录里的旧 Bridge 二进制。
- SDK、离线模型/音频转换工具、`other_tools.7z`、仅供另存的示例模板与开发说明不随玩家包提供，仍保留在源码。`server_name_filter_template.txt` 是实际默认服务器过滤规则，`crashpad_handler.exe` 用于保留原有崩溃转储功能，两者继续随包。外层原版归档、玩家日志及转储不随包。

## 安装包精简

玩家 ZIP 共 63 个文件：53 个 L4N 运行文件、7 个 Bridge/后端/配置/可选插件文件、ThinFlex DLL、`README.txt` 和合并的 `THIRD-PARTY-NOTICES.txt`。没有 MD、JSON、开发脚本、独立许可证目录或额外压缩包。完整技术文档与诊断工具通过仓库获取，游戏运行功能与实际配置不变。

v1.1.4 本次仅重新打包，沿用成功构建 `38022671369` 的二进制，不改程序版本或 Git 发布标签；原 Release 记录打包提交和新附件校验值。

## 配置与安装

首次安装可直接使用包内 `dxvk.conf` 和 `left4dead2/neko/config.vdf`。升级时先备份个人配置，并从临时解压目录移除想保留的同名配置，再覆盖游戏目录。这里使用的配置与参考整合目录逐字节相同；`config_template.vdf` 不随包，避免与实际配置混淆。

`dxvk.conf` 内保留维护者提供的 `dxvk.bridgeMappedChunkSize`、`dxvk.bridgeMemoryDiagnostics` 等键；前两项属于可选 mem1 后端的扩展，不表示默认 GPLALL 实现了这些键。默认后端仍是 GPLALL，默认 Host 仍为 x64。

L4N 本体随完整包安装。`optional/L4N/L4D2BridgePlugin.dll` 是额外的 Bridge 设置菜单插件；需要时复制到 `bin/neko/plugins/` 并重启，见 [菜单说明](L4N-BRIDGE-CONTROLS.md)。

安装前仍须按 README 核对 `studiorender.dll` 的适用版本并保留原始备份。本次没有新增游戏实测，不将既往版本的 FPS 数据作为此整合包的性能结论。
