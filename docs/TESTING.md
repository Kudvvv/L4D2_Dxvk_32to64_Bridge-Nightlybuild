# Arc B580 实验包验收

这是复用 RTX Remix Bridge、接普通上游 DXVK 的实验版本。已完成 Windows 编译，尚未完成游戏实测；构建成功不代表游戏兼容或显存/地址空间收益已验证。首版不包含 TXVK 定制后端、vscript 修补或帧生成。

## 构建

Windows 10/11 x64，Visual Studio 2022（安装 MSVC v142 / 14.29 的 x86/x64 工具和 Windows SDK），Python 3.11、Git。

```powershell
python -m pip install meson==1.3.2 ninja==1.11.1.1
./scripts/build_demo.ps1 -DxvkDll C:/dxvk-2.7.1/x64/d3d9.dll
```

使用 DXVK 官方 v2.7.1 发布包中的 x64/d3d9.dll。构建脚本使用固定上游 Bridge 提交，只初始化 Detours 子模块；不构建 RTX 渲染器。输出 dist/l4d2-experiment。重新打包前请保留或移走旧输出；脚本拒绝覆盖。也可以在将改动推送到 GitHub 后手动运行 Build experimental L4D2 bridge 工作流，获取 artifact；该工作流已成功完成 Windows 编译。

## 建立基线

先备份游戏 bin/dxvk_d3d9.dll 及现有桥接配置。使用同一 DXVK 发布包中的 x32/d3d9.dll 作为 bin/dxvk_d3d9.dll，以 -vulkan -insecure -windowed 启动 L4D2，确认 B580 上菜单和官方地图正常，记录 Intel 驱动版本。这个步骤验证驱动和 DXVK x86，不验证桥接。

## 部署与验收

1. 退出游戏，把实验包的 bin 目录内容复制到游戏 bin。不要与已有 TXVK 或 RTX Remix 桥混装；先保留它们的备份。
2. 游戏启动选项使用 -vulkan -insecure -windowed -console -condebug。保持默认画质、不加载 Mod，进行短时诊断。
3. 检查 L4D2Bridge64.exe 是否启动，bridge64.log 是否出现 L4D2 backend、D3D9 interface object creation succeeded、L4D2 CreateDevice/result。后端路径应为 bin/.l4d2bridge/d3d9vk_x64.dll。
4. 按菜单有效画面 → 官方地图 → 切换窗口 → 分辨率变化 → 正常退出的顺序测试。任何失败都保留两侧日志；不要把 Host 存在或设备创建成功当作渲染成功。
5. 上游默认日志位于游戏工作目录的 rtx-remix/logs/bridge32.log、bridge64.log，DXVK 日志位置看启动输出。若未找到，搜索游戏目录下同名文件；不要预期 TXVK 的 RUN_OK.txt，本实验没有实现它。
6. 记录显卡/驱动、游戏构建号、分辨率、最后成功步骤及表现。提交两侧日志和 left4dead2/console.log。逐调用日志可能很大，先只跑到菜单。

确认初步运行后，将 bin/.l4d2bridge/bridge.conf 的 logApiCalls、logServerCommands 改为 False，并把 logLevel 改为 Info，再进行性能与地址空间测量。不能用诊断模式的帧率评价最终性能。

## 已知未解决项

- 上游保留 Remix 相关代码；配置禁用 API 暴露不等于彻底裁剪。普通 DXVK 分支已隔离初始化查询，后续消息路径仍需实测。
- 没有复制 TXVK 的所有 L4D2 专用补丁；其成功不能保证本实验直接进图。
- 当前设备创建诊断覆盖普通 CreateDevice；CreateDeviceEx 和 Reset 可由上游逐调用日志定位，详细参数日志尚未扩展。
- Arc B580 呈现、退出、Reset 和内存收益尚未验证。

上游 Bridge 来源 https://github.com/NVIDIAGameWorks/dxvk-remix ，MIT；DXVK 来源 https://github.com/doitsujin/dxvk ，zlib。实验补丁修改了原始 Bridge。
