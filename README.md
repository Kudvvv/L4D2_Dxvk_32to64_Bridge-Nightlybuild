# L4D2 Bridge Nightly

> **本构建已包含 DXVK（GPLALL）、L4N 和 Bridge 桥接工具，一体整合，解压覆盖即可一键安装，无需另下这三项组件。请勿与其他同类项目或整合包混合安装。**
>
> **安装前移除 `-vulkan` 启动参数，并备份移走游戏根目录的 `d3d9.dll`；保留本包的 `bin/d3d9.dll`。** L4N / Left4Neko 原作者为 **Starfell（@Starfelll）**，感谢原作者的工作。

**简体中文** | [English](README.en.md)

## 下载与安装（先看这里）

**[前往 Releases 下载完整包](https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases)**。每次发布只提供一个 `l4d2-bridge-*.zip`，另附 `.sha256` 校验文件。包内包含 **L4N 2.51.0、DXVK-GPLALL、Bridge、`dxvk.conf`、L4N 的 `left4dead2/neko/config.vdf`** 和修复后的 `bin/studiorender.dll`，无需运行补丁工具或安装 Python。按维护者提供的整合目录布局交付，未附 `config_template.vdf`；组件来源见 [整合包说明](docs/L4N-BUNDLE.md)。

1. **退出游戏和 Bridge Host，备份现有文件。** 备份原 `left4dead2.exe`、L4N 文件、客户端、Host、`dxvk.conf`、`left4dead2/neko/config.vdf`、Bridge 配置和 `bin/studiorender.dll`，将完整 ZIP 解压到临时目录。若已安装 ThinFlex 修复，继续保留最初的原始 DLL 备份，勿用修复版覆盖它。已装其他同类项目时，先按其说明卸载或恢复原文件，再安装本包。
2. **已有用户先保留配置：** 从临时解压目录移除想保留的 `dxvk.conf`、`left4dead2/neko/config.vdf` 和 `bin/.l4d2bridge/bridge.conf`，再覆盖游戏目录。若自行修改过后端，同样从临时目录移除 `bin/.l4d2bridge/d3d9vk_x64.dll` 与 `d3d9vk_x86.dll`，避免覆盖。首次安装跳过此步；包内 L4N 附带的着色器等同路径文件也会覆盖，请备份个人修改。
3. **核对游戏引擎 DLL 版本：** 用 PowerShell 的 `Get-FileHash '你的游戏目录\bin\studiorender.dll' -Algorithm SHA256` 与下表比较。匹配原版时可覆盖；已是修复版时保留现有文件和原始备份。**若是其他哈希，先从临时目录移除 `bin/studiorender.dll`，只更新 Bridge，不覆盖未知游戏版本。**
4. **覆盖安装：** 移除 `-vulkan` 启动参数，备份移走游戏根目录的 `d3d9.dll`。将准备好的内容合并到游戏根目录（`left4dead2.exe` 所在目录），一起安装 L4N、DXVK 和配套 Client/Host；匹配版本的 `studiorender.dll` 随文件覆盖即应用 ThinFlex 修复。**不要删除 `bin/d3d9.dll`**，它是 Bridge 客户端；配套 x86/x64 Host、后端和配置位于 `bin/.l4d2bridge`。L4N 原说明中的普通 DXVK 安装路径不适用于此整合包，以本节为准。

| 游戏 `bin/studiorender.dll` | SHA-256 |
|---|---|
| 支持的原版 | `3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85` |
| 包内修复版 | `03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6` |

ThinFlex 修复已收到用户复测有效反馈，仍限定于以上精确版本。游戏更新后重新核对；直接复制文件不会自动检查目标版本。包内 `ENGINE-PATCH.json` 记录改动，`licenses/Valve-engine-NOTICE.txt` 保留引擎归属；修改后的 DLL 原数字签名失效。详细安装和恢复步骤见 [ThinFlex 说明](docs/THINFLEX-TEST-README.txt)。

如需 `-vulkan`，把客户端 `d3d9.dll` 改名为 `dxvk_d3d9.dll`，文件仍留在游戏 `bin`。从旧版切换到默认加载方式时，先备份旧 `bin/dxvk_d3d9.dll` 并移除 `-vulkan`。两种方式共用 `bin/.l4d2bridge`。

完整包同时包含 x64/x86 Host 与对应 GPLALL 后端，**默认仍为 x64**。切换 Host 可修改 `client.testX86Server`（`False` 为 x64，`True` 为 x86），保持 `forceX64Server=True`，退出整个游戏后重新启动。

L4N 本体已随包安装。另需 Bridge 常用设置菜单时，把包内 `optional/L4N/L4D2BridgePlugin.dll` 复制到游戏 `bin/neko/plugins/` 并重启；该菜单插件保持可选。无需另下插件包，详见 [L4N 设置说明](docs/L4N-BRIDGE-CONTROLS.md)。L4N 原始说明与作者署名原样保留在 `readme_l4n.txt`，另见 [Starfell 归属说明](licenses/L4N-NOTICE.txt)。

新安装配置包含上游的 learned-aggressive 内存策略，并默认关闭日常 memory/crash/data 诊断；已有用户升级继续保留自己的配置，新功能的键与开销见 [配置说明](docs/CONFIGURATION.md)。

回退 Bridge 时同时恢复配对的客户端和 Host；回退 ThinFlex 时恢复本机保存的原始 `studiorender.dll`。卸载时移除本包安装的文件并恢复备份。

[性能实测](docs/PERFORMANCE-2026-10-10.md) 记录三组同场景对照与适用范围；更多验证步骤见 [游戏验收与性能基线](docs/GAME-VALIDATION.md)。

基于 [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix)，沿用 [L4D2 原项目](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) 的补丁，自动构建适用于 32 位《求生之路 2》的 x86 客户端与 x86/x64 Host。

## 与上游的区别

- 仅构建 Bridge，不构建或分发 RTX Remix 渲染器。
- 应用 L4D2 补丁：调整 Host 和后端加载路径，加入表面／缓冲区影子内存管理及诊断日志，并使用游戏专用配置。补丁见 [patches/l4d2-bridge.patch](patches/l4d2-bridge.patch)。
- 默认使用 **DXVK-GPLALL 2.6.8-2 x64** 后端，版本和下载校验值独立固定在 [config/backend.json](config/backend.json)，不随 Bridge 自动升级。
- 本仓库增加上游检查、自动编译、测试、Nightly 发布和精简安装包规则。
- 修复三维纹理字节步长及上传偏移，避免颜色校正查色表损坏造成的偏色。来源与复测步骤见 [偏色修复说明](docs/VOLUME-TEXTURE-COLOR-FIX.md)。
- 完整同步原项目 **1.2.1 / `cf49175`**，包括 PageBlock 保留/回收/恢复、手动 GC、Reset 状态机、Presenter/输入路径、诊断分离、x86 Host 与 L4N 常用设置。源码、配置片段、测试和可选 DXVK 内存实验均保留，实验后端不替换默认 GPLALL。同步基准与本地兼容差异见 [更新跟踪](docs/ORIGINAL-PROJECT-UPDATES.md)。
- 将创建失败清理扩展到三维/立方体纹理、顶点/索引缓冲区及独立表面，释放客户端对象并清空输出；响应超时仍保留有序的服务器清理。
- 加固缓冲区锁边界和三维纹理临时内存管理，优化连续纹理复制与队列读取；验证方法见 [资源清理与传输优化](docs/RUNTIME-RELIABILITY.md)。

`bin/d3d9.dll` 是 32 位 Bridge 客户端；`.l4d2bridge/d3d9vk_x64.dll` 和 `d3d9vk_x86.dll` 分别供对应位数的 Host 使用。

## 自动与手动构建

项目版本从 **v1.0** 起，重大更新递增次版本号，小改动递增补丁号；当前版本见 [VERSION](VERSION)，维护者设置见 [版本规则](docs/VERSIONING.md)。

每小时第 23 分钟检查 NVIDIA 构建源的默认分支（当前为 `main`）。L4D2 原项目功能同步另记于 [更新跟踪](docs/ORIGINAL-PROJECT-UPDATES.md)。发现未发布的提交后构建；相同提交已发布时跳过。GitHub 调度可能延迟。

在 **Actions → Build latest upstream Bridge → Run workflow** 中：

- `upstream_commit` 留空跟随最新代码；填写完整 40 位 SHA 可指定提交。
- 勾选 `force_rebuild` 可强制编译并创建新的独立版本；已有版本和附件保留，默认关闭。
- 勾选 `validation_only` 仅构建、测试和运行 A/B 基准，保存结果供检查，跳过发布。
- 手动勾选 `thinflex_test` 标记为完整上游同步与 ThinFlex 修复测试版（Pre-release，不设为 Latest）。所有构建均提供包含固定 ThinFlex 修复 DLL 的单一完整包；安装时先核对游戏版本。

去重同时检查上游提交和构建输入指纹；补丁、后端配置、脚本或测试更新会触发新构建。版本名为 `nightly-YYYYMMDD-上游短SHA-r输入指纹-b运行ID.重试号`，日期采用上游提交日期（UTC）。强制重建和重新运行均产生独立版本；旧附件不覆盖。Release 说明及包内 `UPSTREAM.json` 记录完整提交、输入指纹和构建实例。补丁冲突、编译或测试失败时不发布。

复用本地源码目录时，构建脚本核对完整补丁和暂存区，拒绝混入额外源码修改并保留现场。发布中断后重跑失败的发布作业，会分页查找尚未发布的草稿，校验已有附件的内容，只上传缺失附件；内容冲突时停止，已有附件不覆盖。

## License

- 项目特有的新增与修改：**MIT**，见 [LICENSE](LICENSE)，保留 `yeyunyyds` 的原版权声明。
- NVIDIA Bridge：**MIT**，见 [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt)。
- L4N / Left4Neko 2.51.0：原作者 **Starfell（@Starfelll）**，原文件与说明保留作者归属，不属于本项目原创或根目录 MIT 授权，见 [L4N-NOTICE](licenses/L4N-NOTICE.txt)。
- DXVK／DXVK-GPLALL：随附 **zlib/libpng** 许可，见 [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) 和 [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt)。
- Bridge 所含 Detours、Tracy 等依赖继续遵循各自许可，见 [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt)。
- 包内修改版 `studiorender.dll` 来自维护者本机的匹配游戏文件，按用户要求应用限定 ThinFlex 修复。原引擎归 Valve，不属于根目录 MIT 授权；见 [引擎归属说明](licenses/Valve-engine-NOTICE.txt)。

根目录 MIT 许可不替代第三方许可。发布包保留版权及许可文件；完整归属见 [THIRD_PARTY.md](THIRD_PARTY.md)。L4D2 游戏本体不在本项目授权范围内。
