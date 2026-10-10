# 实验：PageBlock drop、手动 GC 与 L4N v2 菜单

完整进程/资源架构见 [ARCHITECTURE.md](ARCHITECTURE.md)；控制 ABI v1/v2 的字段、偏移、错误和调用示例见 [API.md](API.md#pageblock-control)。

此功能属于开发实验，**不是已发布的 v1.1.1 补丁内容**。正常推荐配置保持 `learned-aggressive`；省略配置键时的兼容回退仍为 `keep`。不修改 Present、Host 位数选择、DXVK 或正式发布版本号。

v1.2.0 的可选 L4N 插件已扩展为 [常用设置菜单](L4N-BRIDGE-CONTROLS.md)，保持 PageBlock reclaim、capability/safety/learned 分类和三种 GC 语义。正式 Release 的插件单独提供 ZIP，安装到 `bin/neko/plugins/`；Bridge 本体不依赖插件。此前 [1.1.2-dev.3 residency 实验](PAGEBLOCK-RESIDENCY-EXPERIMENT.md)、`v1.2.0-dev.1` 和下文 `5951831` CI 均为历史记录，不代表最新菜单和构件。

## 安装和使用

1. 退出游戏与桥，备份客户端和两种 Host。
2. 使用 `l4d2-bridge-pageblock-drop-experiment` 构建产物，将 `bin` 合并进游戏目录。三个桥文件必须配套更新；保留现有 DXVK/mem1、ReShade 和 `bridge.conf`。
3. 可选菜单插件为 x86 `bin/neko/plugins/L4D2BridgePlugin.dll`。在支持此 SDK v2 的 L4N HUD 插件菜单内选择 **L4D2 Bridge**。插件只使用提供的 `IL4NPlugin`、`GetInterfaceVersion()=2`、`GetL4NPluginInstance` 和 `RequestHudMenu(bool)`；没有 Source 控制台命令、L4N 内部 hook 或自实现 GC。
4. 根菜单固定为 Status、GC、Memory Policy、ReShade Presenter、Host。Status 仅显示 PageBlock；GC 子菜单提供 Learned / Aggressive / Force。Memory Policy 的 keep / lg / drop 仅改变 runtime，底部 `save to configure` 才由 Client 保存当前策略。Host 只显示配置值，选择后点击 Save；Host 和 Presenter 保存后下次完整启动生效。旧 Bridge 回退仍只影响当前会话，保存不可用。进入 drop 不自动清理已有 backing，需要另选 GC Aggressive/Force。
5. 若需启动即启用 drop，手动合并 `PAGEBLOCK-DROP.conf`：

```ini
client.pageBlockRetentionPolicy = drop
client.pageBlockDiagnostics = True
client.pageBlockDiagnosticsDetailed = False
client.testReadbackRecovery = False
```

恢复推荐配置：`client.pageBlockRetentionPolicy = learned-aggressive`，完全重启。临时选择 keep 不会使已驱逐的数据凭空恢复；下一次合法 CPU 访问仍须恢复。重新选择 learned-aggressive 后，已有 promoted/KEEP 决策不被清除，之前在 keep/drop 中创建而未学习指纹的资源保持保守处理；新创建的合格纹理继续正常学习。

菜单动作可能等待 Host 的有序确认或 readback。先在主菜单、小地图中测试；不要把显式 GC 的耗时当作正常帧耗时。菜单显示“不支持”或 API 不可用时不加载替代 D3D9 DLL。

## 四种寿命独立

- D3D9 资源和 Client 代理由原 AddRef/Release 路径管理。
- Host/DXVK 资源由原 Host 创建、销毁路径管理。
- `PagefileShadow` 持有 CPU backing 的 section 句柄以及可选映射。
- **只驱逐最后一项**：解除 view、关闭 section，保留代理、ID、描述符、Host 资源。正常 draw 不需重新创建纹理。

客户端 Lock 成功后，`acquire` 的计数固定住暴露给游戏的指针。Unlock 复制 payload 时另有 Bridge transfer pin。所有新 GC 与 surface Lock/Unlock/注册注销由 residency gate 串行化；锁顺序为 residency gate → learned Context → PagefileShadow。GC 不持有父 device mutex，因此不会反向获取 device 锁。

实际 surface 上传是同步复制到 IPC 所有的 payload。Host 不保存 Client view 的指针；新驱逐路径还请求 Host 有序 ack，确认前序命令被处理。ack 不等待 GPU idle。以后恢复当前内容，复用原 Host D3D9 READONLY Lock 与 EVENT query/flush/wait，随后按逻辑行布局重建 backing。没有 client 历史数据、缓存复制或零填充替代恢复。

## 所有自动策略与三种 GC 共用 reclaim

内部 C++ API：`l4d2_residency::RunPageBlockGc(Context&, PageBlockGcMode)`；生产包装：`RunPageBlockGc(PageBlockGcMode)`。所有自动/手动释放都经过 `Entry::queryCapability/queryLearnedDecision/querySafety/reclaim`，最终调用同一个 `PagefileShadow::evictBacking`；它自身再次检查 game Lock 和 Bridge transfer pin。Parent 保留 hash/DB/promotion，通知 Entry，不再独立驱逐。

| 模式 | 判定 |
|---|---|
| learned | 能力/安全检查通过且 learned 已识别为可驱逐的 mip；KEEP 与 unclassified 分开，不覆盖 DB 命中、promotion 或 fallback |
| aggressive | 忽略 learned 历史，驱逐所有具备恢复能力、无 game pointer、无 active Bridge use 且完整 upload/Host ACK 成功的 backing |
| force | 同样保留 game pointer；对可安全完成的 Bridge-owned 工作调用 drain，再确认 Host 并驱逐 idle backing |

force 的 drain 统计分别计数安全完成的 Bridge-only pin 和等待确认的 Host upload；缓存的 ack 不计一次新等待。当前 surface payload copy 在 Unlock 内同步完成，所以生产代码没有可独立挂起的 PageBlock copy 任务。force 会在 residency gate 等待先前 Lock/Unlock 操作结束，并使用有序 Host ack；不会取消游戏的 Lock，也不引入 GPU-wide idle。底层 drain callback 扩展点用于已知可安全完成的 Bridge-only operation，测试覆盖该路径；不能把仍未完成的 transfer 硬改为 idle。没有可安全 drain 的 transfer 会报告 skippedTransferring。

尚未完整上传、upload copy 失败、Host ack 失败的 backing 保留并报告 `unsafe-unsynchronized`，不以 KEEP 历史为理由跳过。不支持的类型与缺少恢复布局分别为 unsupported-capability 和 recovery-unavailable。这个例外保护尚未能证明 Host 已持有正确内容的数据。

## drop 策略

每次 Unlock 后，在 capability 检查通过、无暴露指针／传输 pin、完整首次 upload 和本次 upload 已完成、Host ack 成功时，立即实际驱逐 backing。后续 CPU 访问：

- 完整 DISCARD：重建临时 backing，不恢复丢弃前的内容。
- READONLY、普通 Lock 或部分区域：先恢复**当前 Host 内容**，再返回 Client 指针；部分写入保留范围外逻辑像素。
- 不因为曾被访问而永久 KEEP，不使用 persistent DB。已有 learned 分类不阻止 drop/手动 aggressive。
- 恢复失败：Lock 返回错误，增加计数，明确记录 Bridge 恢复限制；禁止静默用全零或旧数据继续。

原 Phase 1 reference 比较和 learned 的 hash 验证、promotion、DB 格式保持原样。`client.testReadbackRecovery=True` 时禁用新驱逐／策略切换，以保留 ground truth。手动 learned 驱逐后的 miss 仍使用原 hash 验证和 promotion；aggressive/force/drop 恢复当前内容。原 strict recovery 与新 residency recovery 的 operation 分别是 0/1 与 2/3，结构 ABI 大小不变；必须使用匹配 Host，旧 Host 不识别新操作。

## 控制 ABI 与插件

客户端新增命名导出 `L4D2BridgePageBlockControl`（WINAPI/stdcall），见 `pageblock_control.h`：ABI v1 的 Request=16/Response=208 和 Stats/SetPolicy/Gc 枚举 0/1/2 保持不变。新增详细 v2 Response=656，按版本/大小选择写入；旧插件 buffer 不会被扩大。插件的 Stats/GC 优先 v2，旧 Bridge 拒绝后回退 v1；新增通用 `L4D2BridgeControl` 不改变这个导出及 session-only SetPolicy。L4N **插件接口 version 2** 与 Bridge **控制 ABI version 2** 是独立协议。

插件枚举当前已加载模块，查找命名导出，不主动 LoadLibrary 一个 D3D9 runtime。HUD menu 的 callback/user_data 指针按 SDK KeyValues 格式生成。失败显示 HRESULT；GC 返回统计子菜单。插件不持有 D3D9 资源引用，不操作资源内存。未来其他 UI 可复用同一控制 ABI。

菜单返回由 L4N HUD 自身管理，不再生成插件自己的 `Back` 项。SDK 的非空 callback 返回值代表进入子菜单，不能用“再次返回根菜单”模拟退回上一级。说明/统计文字回调返回 nullptr，点击不会新增层级或执行 Bridge 操作；统计在重新进入 Status 时重新查询，不再用递归 Refresh。`common-settings-2` 策略菜单首行显示当前 runtime/configure 来源，选择和保存结果页也重新查询。已打开的父页面由 HUD 缓存，退回后需要重新进入菜单刷新；结果页只提供保存，不递归列出其他选择。GC 结果页返回 GC，Status 返回 L4D2 Bridge。

导航修正不属于下文历史 `5951831` 产物。本轮实际 Windows DLL 的 x64 Wine mock 回归包括 100 轮父菜单导航与 v1/v2 fallback；x86 编译通过但本地未执行。该检查不能替代真实 L4N HUD 验证。根菜单明确显示 `Last action result`，是上次 GC/动作的静态结果，不是实时残余；Stats 需重新进入获取新快照。

## 诊断

当前源码中，显式 GC 总在普通 Bridge 日志输出一行 `PB_GC`；只有 client.pageBlockDiagnostics=True 才另写 Client DLL 同目录的 `l4d2-pageblock-gc.log`。memoryMonitoring=False 时 GC 不做前后全进程 VA/内存快照，回收、安全门、计数与 ACK/drain 结果不变。PB_GC 至少包含：

`mode`、`pageBlocksScanned`、`pageBlocksEvicted`、`pageBlocksSkippedLocked`、`pageBlocksSkippedTransferring`、`pageBlocksSkippedPolicy`、`bytesUnmapped`、`mappedBytesBefore`、`mappedBytesAfter`；额外输出 `pageBlocksSkippedUnsynchronized`、`failures`、`backingBytesReleased`。force 还有 `transfersDrained`、`drainWaitCount`、`drainWaitTimeMs`。所有模式另有 `hostAckWaitCount/TimeMs`，旧 force drain 可能计入相同 ACK，不要将两者相加。新增独立 skip：unsupported-capability、recovery-unavailable、unclassified、reference-test、no-backing；只有真实 learned KEEP 计 skippedPolicy。Stats/GC 另写 `PB_COVERAGE` 和八类 `PB_COVERAGE_CATEGORY`，见统一实验说明。

`bytesUnmapped` 和 mapped before/after 统计实际 view 的 VirtualQuery region 大小，**不等于 RAM 工作集或 section backing 字节数**。只有 view 映射着才能释放 mapped VA；已由预算 trim 解除 view 的 backing 被关闭时，backingBytesReleased 可以非零而 bytesUnmapped 为零。既有 `surfaceViewBudgetBytes` 的 64 KiB 对齐预算收费仍保留。

`PB_DROP_SUMMARY`：`dropEvictionCount`、`dropEvictedBytes`、`remapCountAfterDrop`、`remapBytesAfterDrop`、`reconstructionFailures`。累计释放可重复计算同一资源的多轮 eviction，不能当作同时省下的内存。

菜单 “Cumulative released” 是 `dropEvictedBytes`，不含原 learned 自动释放、一般资源销毁或手动 GC 的独立统计。未启用 drop 时为零符合实现；learned 的释放/恢复计数看 `PB_POLICY_SUMMARY`。`reconstructionFailures` 也不是全部 learned recovery 的失败总数。

开启 `client.pageBlockDiagnostics` 后，新专用日志才逐资源记录 `PB_RESIDENCY event=lock/host-result/evicted/remapped`，包含 ID/type/format/pool/usage/size/mip/face、flags/rect、old_contents_required、previously_evicted 和 reconstruction_required。它们不逐资源刷普通 Info 日志；明确的恢复错误才进入普通 error log。

## 当前范围和已知实现限制

- 注册范围是非 shared-heap 的 surface PagefileShadow：普通 2D mip、cube face mip、独立 surface、backbuffer。VB/IB 使用其他 shadow allocator，volume 使用 per-Lock heap；此任务不把它们重做成第二套 PageBlock allocator。
- current-content recovery 支持 DXT1/3/5、A8R8G8B8/X8R8G8B8、Q8W8V8U8、ATI1/ATI2 及显式列举的线性格式。`residencyBackingLayout` 同时校验逻辑行与 Client allocation；ATI 区分兼容 API Pitch 和压缩 storage Pitch，传回原始压缩块，额外 padding 不作为像素。
- 深度、未知 FOURCC、逻辑或实际 backing 大于 64 MiB 的 subresource 尚无此路径的完整恢复支持。实际 readback 还取决于 backend Lock 能力；DEFAULT/非零 Usage/RT/depth/MSAA/backbuffer 为 unsupported-capability，未新增通用 staging/GetRenderTargetData 回退。
- aggressive/drop/force 在释放前检查恢复 capability。未知格式、不匹配/超限大小等 recovery-unavailable 保留 backing；能力范围内若实际 backend readback 失败，仍明确报错。加入三格式不等于所有 D3D9 路径已覆盖。
- SharedHeap 或非 vanilla backend 不启用新策略／驱逐。策略日志不可写不改变数据语义；控制失败可见，不能保证日志可用。
- 菜单接口已按提供的 SDK v2 接入；原生 mock 菜单测试不能替代真实 L4N 的 HUD 调用和游戏渲染验证。

## 实机验证建议

先用 learned-aggressive 进图，打开 Stats，确认插件 API 可用。主菜单依次运行三种 GC，记录 skipped 与 freed，再进同一地图检查纹理和操作。随后单独测试 drop，多次进图、退出、切地图，观察 remap/reconstructionFailures；遇到错误保留 gc/pageblock/bridge32/Host 日志，恢复 learned-aggressive 后重启。不要同时开启 Phase 1 reference test，也不要启用已暂缓的 Steam 输入实验。

原生测试覆盖 pin、实际 VirtualQuery MEM_FREE、三种 GC、Host 当前内容变化、重复 drop、完整 DISCARD、部分/READONLY、row padding、未同步数据保护和 SDK v2 callbacks。Host mock 与真实 DXVK 实机结果须分别记录。测试没有证明全部 MOD/overlay/device-reset 组合兼容。

## 实现前路径核对

- 创建与所有权：`d3d9_surface.h/.cpp`；texture/cube 子资源保留原 parent/proxy。
- 映射/pin/trim/真正关闭 section：`pagefile_shadow.h`。
- 原 learned 指纹/资格/DB/promotion：`retention_policy.h`、`retention_runtime.h`、`retention_database.h`。
- 原实验、传输和 Host READONLY/query：`readback_recovery.h`、`readback_transport.h`、`readback_backend.h`、Host main 的 readback command。
- 新共用 residency registry/walker：`pageblock_residency.h`；配置与生产交换：`pageblock_runtime.h`。
- 无 Source 依赖的控制：`pageblock_control.cpp/.h`；L4N SDK v2 UI：`plugins/l4n/L4D2BridgePlugin.cpp`。

以上 Bridge 源码在仓库中由 `patches/l4d2-bridge.patch` 保存，构建时应用到固定上游。新实现署名与第三方来源见 LICENSE / THIRD_PARTY.md；提供的 L4N SDK header 原样保留，不将其声称为项目原创或自行赋予 MIT 授权。

## 原实验的历史构建验证

[Windows CI 37598250948](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/37598250948) 在代码提交 `5951831` 全部通过：x86 Client、x64/x86 Host、x86 L4N plugin 编译；x86/x64 residency/GC 原生测试；SDK v2 HUD callback + mock 控制导出测试；既有 Phase 1、真实删除/hash恢复/DB promotion 回归；ATI、adapter、window/input、queue、API-wait 等现有原生检查。Linux 上逻辑布局测试和 6 项 Python 分析测试也通过。

下载的实验产物已校验四个二进制 SHA256、PE 架构和命名导出；不包含替换用 backend 或活动 bridge.conf。没有在云环境执行 L4D2、真实 L4N HUD 或 GPU gameplay，仍待实机验证。

后续作者提供了 [x86 learned-aggressive 的 c2m2→c2m5 实机跨图观察](PAGEBLOCK-CROSS-MAP-OBSERVATION.md)：旧实验构建、没有启用 drop/手动 GC。四个样本映射约 57–59 MiB、backing 约 60 MiB，后三张图 AV 为 2445/2442/2456 MB，没有明显累积。它不属于 1.1.2-dev.1 新修正的实机验收，也不验证独立 drop/手动 GC。

## 原实验的历史文件变更清单

Bridge 的 17 个源码／构建文件修改由一个 patch 保存：Client surface/.def/summary、PagefileShadow、retention policy/runtime、residency/runtime/control；util control ABI、readback layout/transport、meson；Host readback backend/main。固定上游和版权不变。

实际仓库文件：

- `patches/l4d2-bridge.patch`
- `plugins/l4n/L4D2BridgePlugin.cpp`
- `plugins/l4n/sdk/l4n_plugin.h`
- `scripts/build_l4n_plugin.ps1`
- `scripts/test_pageblock_gc.ps1`
- `scripts/package_pageblock_experiment.py`
- `tests/pageblock_residency.cpp`
- `tests/l4n_plugin.cpp`
- `tests/readback_layout.cpp`
- `tests/readback_recovery.cpp`
- `.github/workflows/build.yml`
- `config/PAGEBLOCK-DROP.conf`
- `config/bridge.conf`（仅新增实验说明注释，默认值未改）
- `docs/PAGEBLOCK-DROP-GC.md`
- `README.md`（高级实验链接与 SDK credit）
- `THIRD_PARTY.md`（提供的 SDK header 来源／许可证状态）
