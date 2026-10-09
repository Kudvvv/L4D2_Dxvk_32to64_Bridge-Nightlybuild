# L4D2 Bridge Nightly

**简体中文** | [English](README.en.md)

## 下载与安装（先看这里）

**[前往 Releases 下载完整包](https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases)**。每次发布只提供一个 `l4d2-bridge-*.zip`，另附 `.sha256` 校验文件；不再区分 update 包，也不用另下载 ThinFlex 工具。

1. **退出游戏和 Bridge Host，备份现有文件。** 将完整 ZIP 解压到临时目录。
2. **已有用户先保留配置：** 从临时解压目录移除包内 `bin/.l4d2bridge/bridge.conf`，保留游戏里正在使用的配置。若自行修改过后端，同样从临时目录移除 `bin/.l4d2bridge/d3d9vk_x64.dll`，避免覆盖。首次安装跳过此步；已有 `dxvk.conf`、ReShade 和 DB 不在包内，不受覆盖。
3. **安装 Bridge：** 将准备好的内容合并到游戏根目录（`left4dead2.exe` 所在目录），同时更新客户端和 Host。客户端位于 `bin/d3d9.dll`；配套 x64 Host、后端和配置位于 `bin/.l4d2bridge`。默认移除 `-vulkan` 启动项。
4. **需要 ThinFlex 崩溃修复：** 工具已在包内 `tools/thinflex/ThinFlexPatch.exe`，无需安装 Python。按 [工具说明](docs/THINFLEX-TEST-README.txt) 或包内 `tools/thinflex/README.txt` 生成副本、校验并备份安装。**仅解压完整包不会自动修改 `studiorender.dll`。** 已安装并验证有效的 ThinFlex 修复可保留，无需重复应用。

ThinFlex 修复已收到用户复测有效反馈，仍限定于说明中精确匹配的原始 DLL；其他版本会拒绝处理。游戏更新后应重新核对，不能覆盖未知版本。

如需 `-vulkan`，把客户端 `d3d9.dll` 改名为 `dxvk_d3d9.dll`，文件仍留在游戏 `bin`。从旧版切换到默认加载方式时，先备份旧 `bin/dxvk_d3d9.dll` 并移除 `-vulkan`。两种方式共用 `bin/.l4d2bridge`。

回退 Bridge 时同时恢复配对的客户端和 Host；ThinFlex 的恢复步骤见工具说明。卸载时移除本包安装的文件并恢复备份。

[性能实测](docs/PERFORMANCE-2026-10-10.md) 记录三组同场景对照与适用范围；更多验证步骤见 [游戏验收与性能基线](docs/GAME-VALIDATION.md)。

基于 [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix)，沿用 [L4D2 原项目](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) 的补丁，自动构建适用于 32 位《求生之路 2》的 x86 客户端与 x64 Host。

## 与上游的区别

- 仅构建 Bridge，不构建或分发 RTX Remix 渲染器。
- 应用 L4D2 补丁：调整 Host 和后端加载路径，加入表面／缓冲区影子内存管理及诊断日志，并使用游戏专用配置。补丁见 [patches/l4d2-bridge.patch](patches/l4d2-bridge.patch)。
- 默认使用 **DXVK-GPLALL 2.6.8-2 x64** 后端，版本和下载校验值独立固定在 [config/backend.json](config/backend.json)，不随 Bridge 自动升级。
- 本仓库增加上游检查、自动编译、测试、Nightly 发布和精简安装包规则。
- 修复三维纹理字节步长及上传偏移，避免颜色校正查色表损坏造成的偏色。来源与复测步骤见 [偏色修复说明](docs/VOLUME-TEXTURE-COLOR-FIX.md)。
- 移植原项目的纹理创建失败处理、ATI1/ATI2 压缩纹理边界修复和命令队列事件唤醒，带配套原生测试。移植基准见 [更新跟踪](docs/ORIGINAL-PROJECT-UPDATES.md)。
- 将创建失败清理扩展到三维/立方体纹理、顶点/索引缓冲区及独立表面，释放客户端对象并清空输出；响应超时仍保留有序的服务器清理。
- 加固缓冲区锁边界和三维纹理临时内存管理，优化连续纹理复制与队列读取；验证方法见 [资源清理与传输优化](docs/RUNTIME-RELIABILITY.md)。

`d3d9.dll` 是 32 位 Bridge 客户端；`d3d9vk_x64.dll` 是 64 位 DXVK 后端，两者用途不同。

## 自动与手动构建

项目版本从 **v1.0** 起，重大更新递增次版本号，小改动递增补丁号；当前版本见 [VERSION](VERSION)，维护者设置见 [版本规则](docs/VERSIONING.md)。

每小时第 23 分钟检查上游默认分支（当前为 `main`）。发现未发布的提交后构建；相同提交已发布时跳过。GitHub 调度可能延迟。

在 **Actions → Build latest upstream Bridge → Run workflow** 中：

- `upstream_commit` 留空跟随最新代码；填写完整 40 位 SHA 可指定提交。
- 勾选 `force_rebuild` 可强制编译并创建新的独立版本；已有版本和附件保留，默认关闭。
- 勾选 `validation_only` 仅构建、测试和运行 A/B 基准，保存结果供检查，跳过发布。
- 手动勾选 `thinflex_test` 标记为性能优化与 ThinFlex 修复测试版（Pre-release，不设为 Latest）。所有构建均提供内含 `tools/thinflex` 的单一完整包；是否应用引擎修复由玩家按说明操作。

去重同时检查上游提交和构建输入指纹；补丁、后端配置、脚本或测试更新会触发新构建。版本名为 `nightly-YYYYMMDD-上游短SHA-r输入指纹-b运行ID.重试号`，日期采用上游提交日期（UTC）。强制重建和重新运行均产生独立版本；旧附件不覆盖。Release 说明及包内 `UPSTREAM.json` 记录完整提交、输入指纹和构建实例。补丁冲突、编译或测试失败时不发布。

复用本地源码目录时，构建脚本核对完整补丁和暂存区，拒绝混入额外源码修改并保留现场。发布中断后重跑失败的发布作业，会分页查找尚未发布的草稿，校验已有附件的内容，只上传缺失附件；内容冲突时停止，已有附件不覆盖。

## License

- 项目特有的新增与修改：**MIT**，见 [LICENSE](LICENSE)，保留 `yeyunyyds` 的原版权声明。
- NVIDIA Bridge：**MIT**，见 [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt)。
- DXVK／DXVK-GPLALL：随附 **zlib/libpng** 许可，见 [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) 和 [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt)。
- Bridge 所含 Detours、Tracy 等依赖继续遵循各自许可，见 [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt)。

根目录 MIT 许可不替代第三方许可。发布包保留版权及许可文件；完整归属见 [THIRD_PARTY.md](THIRD_PARTY.md)。L4D2 游戏本体不在本项目授权范围内。
