# v1.1.1 补丁 / Patch release

主要修复：打开 ReShade，切换到其他程序，再点击 L4D2 画面时，原 Host 子窗口禁止鼠标激活，游戏未回到前台，Home 也无法关闭面板。v1.1.1 在这个用户点击路径请求激活游戏主窗口；保留子窗口不取得键盘焦点的策略，不通过定时器抢前台。

作者已完成修复版实机验证并报告正常运行。Windows 原生测试覆盖两种跨位数组合、后台移动不激活、点击恢复游戏 root 和关闭后释放捕获；它们不替代所有 GPU、ReShade 版本和 MOD 组合的验证。现有 ReShade 实机基线为 x64 / Vulkan 6.0.1，不能据此声称 6.0.0 或所有 x86 ReShade 组合都已验证。

## 从 v1.1 升级

1. 完全退出游戏和桥，备份客户端和两种 Host。
2. 优先下载 `l4d2-bridge-patch-v1.1.1.zip`，将其 `bin` 合并到游戏根目录。仅替换：
   - `bin/dxvk_d3d9.dll`（x86 客户端）；
   - `bin/.l4d2bridge/L4D2Bridge64.exe`；
   - `bin/.l4d2bridge/L4D2Bridge32.exe`。
3. 保留 DXVK / mem1、ReShade、`bridge.conf`、`resource-retention.db` 和当前 Host 位数。这个补丁包不提供替换用的后端或活动配置。
4. 保留现有 ReShade 配置；默认完整包仍关闭 presenter。需要 ReShade 的用户确认以下三项为 True，每个键只留一份：

```ini
server.presenterWindow = True
client.hookMessagePump = True
client.overrideCustomWinHooks = True
```

同时保留 `server.presenterInput=True`、窗口模式、原 ReShade 安装和鼠标/键盘 policy 0。参考包内可选 `OVERLAY-INPUT.conf`，手动合并，不能用它替换整份 bridge.conf。

首次安装用 `l4d2-bridge-v1.1.1.zip`，它包含客户端、两种 Host、官方 DXVK 2.6.1 x86/x64 和默认配置。完整覆盖会替换已有后端和输入配置；已有安装推荐三文件补丁。完整安装说明：https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/blob/main/README.md

Host 选择不变：`forceX64Server=True`，`client.testX86Server=False` 为 x64，True 为 x86；切换后完全重启。

## 范围与限制

- 保持 v1.1 的 learned-aggressive 和上游资源策略，不新增退图清空 backing。
- 后续开发的 API 等待和上传细分诊断保留，但默认关闭；加载提速已暂缓。本补丁没有新的 FPS、RAM 或加载秒数承诺。
- Steam Overlay 输入调查未成功，功能仍不支持。关闭 `client.steamOverlayInput`、`server.steamOverlayInput`、`server.steamNativeInput` 及两端 `steamInputDiagnostics`；这些实验不属于正常配置。
- TXVK Credits 更正为历史思路/参考来源、当前闭源且保留所有权利。没有分发 TXVK 二进制；本项目仍基于获授权的 NVIDIA Bridge、DXVK 和其他上游组件，保留原版权声明。
- 可选 mem1 后端没有修改或重新宣称验证；保留当前兼容后端即可。

## English

v1.1.1 fixes returning to an open ReShade overlay by clicking the game after switching to another application. The presenter requests foreground activation of the original game window on that click, without focusing the Host child or periodically stealing focus. The author completed hardware testing and confirmed normal operation. Native cross-process tests passed in both architecture combinations; other ReShade versions and x86 hardware combinations are not automatically validated.

For existing installations, use **l4d2-bridge-patch-v1.1.1.zip**. Exit both processes, back up the Bridge binaries, and merge its `bin` into the game directory. It updates the x86 client and both Hosts, preserving your DXVK/mem1, ReShade, active configuration and retention database. Optional ReShade input still requires the three True settings above; preserve the remaining overlay settings and windowed mode. The complete package includes official DXVK 2.6.1 backends and a default configuration with the presenter disabled, so an unqualified full overwrite can disable your previous ReShade setup.

Retention and Host selection are unchanged. Loading diagnostics and unsuccessful Steam input experiments remain off by default. This patch does not claim loading acceleration, Steam Overlay input support or new performance/memory benchmarks. TXVK credit retains historical inspiration/reference while correctly recording its current closed-source license; upstream notices remain intact.
