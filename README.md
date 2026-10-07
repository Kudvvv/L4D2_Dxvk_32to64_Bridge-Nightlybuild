# L4D2 Bridge Nightly

**简体中文** | [English](README.en.md)

基于 [NVIDIA dxvk-remix Bridge](https://github.com/NVIDIAGameWorks/dxvk-remix)，沿用 [L4D2 原项目](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge) 的补丁，自动构建适用于 32 位《求生之路 2》的 x86 客户端与 x64 Host。

## 与上游的区别

- 仅构建 Bridge，不构建或分发 RTX Remix 渲染器。
- 应用 L4D2 补丁：调整 Host 和后端加载路径，加入表面／缓冲区影子内存管理及诊断日志，并使用游戏专用配置。补丁见 [patches/l4d2-bridge.patch](patches/l4d2-bridge.patch)。
- 默认使用 **DXVK-GPLALL 2.6.8-2 x64** 后端，版本和下载校验值独立固定在 [config/backend.json](config/backend.json)，不随 Bridge 自动升级。
- 本仓库增加上游检查、自动编译、测试、Nightly 发布和精简安装包规则。
- 修复三维纹理字节步长及上传偏移，避免颜色校正查色表损坏造成的偏色。来源与复测步骤见 [偏色修复说明](docs/VOLUME-TEXTURE-COLOR-FIX.md)。

`dxvk_d3d9.dll` 是 32 位 Bridge 客户端；`d3d9vk_x64.dll` 是 64 位 DXVK 后端，两者用途不同。

## 自动与手动构建

每小时第 23 分钟检查上游默认分支（当前为 `main`）。发现未发布的提交后构建；相同提交已发布时跳过。GitHub 调度可能延迟。

在 **Actions → Build latest upstream Bridge → Run workflow** 中：

- `upstream_commit` 留空跟随最新代码；填写完整 40 位 SHA 可指定提交。
- 勾选 `force_rebuild` 可重新编译已发布的提交并覆盖同版本附件；默认关闭。

版本名为 `nightly-YYYYMMDD-短提交号`，日期采用上游提交日期（UTC），不是运行日期。Release 说明提供实际上游提交和构建配置链接。补丁冲突或编译失败时不发布。

## 下载与安装

从 [Releases](https://github.com/YuuMJ/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases) 下载 ZIP。安装包仅包含运行文件、简短说明及许可证，旁附 `.sha256` 校验文件。

退出游戏，备份原文件，将包内 `bin` 合并到游戏目录的 `bin`，保留隐藏目录 `.l4d2bridge` 的结构。卸载时移除本包安装的文件并恢复备份。

自动测试验证编译和诊断逻辑，不代表已完成游戏实测。

## License

- 项目特有的新增与修改：**MIT**，见 [LICENSE](LICENSE)，保留 `yeyunyyds` 的原版权声明。
- NVIDIA Bridge：**MIT**，见 [licenses/Bridge-MIT.txt](licenses/Bridge-MIT.txt)。
- DXVK／DXVK-GPLALL：随附 **zlib/libpng** 许可，见 [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) 和 [licenses/DXVK-GPLALL-LICENSE.txt](licenses/DXVK-GPLALL-LICENSE.txt)。
- Bridge 所含 Detours、Tracy 等依赖继续遵循各自许可，见 [licenses/Bridge-third-party.txt](licenses/Bridge-third-party.txt)。

根目录 MIT 许可不替代第三方许可。发布包保留版权及许可文件；完整归属见 [THIRD_PARTY.md](THIRD_PARTY.md)。L4D2 游戏本体不在本项目授权范围内。
