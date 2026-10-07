# 实验：PageBlock drop、手动 GC 与 L4N v2 菜单

此功能属于开发实验，**不是已发布的 v1.1.1 补丁内容**。正常推荐配置保持 `learned-aggressive`；省略配置键时的兼容回退仍为 `keep`。不修改 Present、Host 位数选择、DXVK 或正式发布版本号。

## 安装和使用

1. 退出游戏与桥，备份客户端和两种 Host。
2. 使用 `l4d2-bridge-pageblock-drop-experiment` 构建产物，将 `bin` 合并进游戏目录。三个桥文件必须配套更新；保留现有 DXVK/mem1、ReShade 和 `bridge.conf`。
3. 可选菜单插件为 x86 `bin/neko/plugins/L4D2BridgePlugin.dll`。在支持此 SDK v2 的 L4N HUD 插件菜单内选择 **L4D2 Bridge**。插件只使用提供的 `IL4NPlugin`、`GetInterfaceVersion()=2`、`GetL4NPluginInstance` 和 `RequestHudMenu(bool)`；没有 Source 控制台命令、L4N 内部 hook 或自实现 GC。
4. 菜单提供 PageBlock Stats、Retention Policy（keep / learned-aggressive / drop [experimental]）及 GC Learned / Aggressive / Force。策略切换仅影响当前会话，不写入 bridge.conf；进入 drop 不自动清理已有 backing，需要另选 GC Aggressive/Force。
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

## 三种 GC 共用一个 walker

内部 C++ API：`l4d2_residency::RunPageBlockGc(Context&, PageBlockGcMode)`；生产包装：`RunPageBlockGc(PageBlockGcMode)`。所有真实释放最终调用同一个 `PagefileShadow::evictBacking`，它自身再次检查 game Lock 和 Bridge transfer pin。

| 模式 | 判定 |
|---|---|
| learned | 仅原 Parent learned 逻辑已经识别为可驱逐的 mip；不覆盖 KEEP、DB 命中、promotion 或 fallback |
| aggressive | 忽略 learned 历史，驱逐所有无 game pointer、无 active Bridge use 且能确认 Host 内容的 backing |
| force | 同样保留 game pointer；对可安全完成的 Bridge-owned 工作调用 drain，再确认 Host 并驱逐 idle backing |

force 的 drain 统计分别计数安全完成的 Bridge-only pin 和等待确认的 Host upload；缓存的 ack 不计一次新等待。当前 surface payload copy 在 Unlock 内同步完成，所以生产代码没有可独立挂起的 PageBlock copy 任务。force 会在 residency gate 等待先前 Lock/Unlock 操作结束，并使用有序 Host ack；不会取消游戏的 Lock，也不引入 GPU-wide idle。底层 drain callback 扩展点用于已知可安全完成的 Bridge-only operation，测试覆盖该路径；不能把仍未完成的 transfer 硬改为 idle。没有可安全 drain 的 transfer 会报告 skippedTransferring。

尚未上传成功、upload copy 失败、Host ack 失败的 backing 保留并报告 `implementation-gap stage=host-ack`，不以 KEEP 历史为理由跳过。这个例外保护尚未能证明 Host 已持有正确内容的数据。

## drop 策略

每次 Unlock 后，在无暴露指针／传输 pin、首次/本次 upload 已完成、Host ack 成功时，立即实际驱逐 backing。后续 CPU 访问：

- 完整 DISCARD：重建临时 backing，不恢复丢弃前的内容。
- READONLY、普通 Lock 或部分区域：先恢复**当前 Host 内容**，再返回 Client 指针；部分写入保留范围外逻辑像素。
- 不因为曾被访问而永久 KEEP，不使用 persistent DB。已有 learned 分类不阻止 drop/手动 aggressive。
- 恢复失败：Lock 返回错误，增加计数，明确记录 Bridge 恢复限制；禁止静默用全零或旧数据继续。

原 Phase 1 reference 比较和 learned 的 hash 验证、promotion、DB 格式保持原样。`client.testReadbackRecovery=True` 时禁用新驱逐／策略切换，以保留 ground truth。手动 learned 驱逐后的 miss 仍使用原 hash 验证和 promotion；aggressive/force/drop 恢复当前内容。原 strict recovery 与新 residency recovery 的 operation 分别是 0/1 与 2/3，结构 ABI 大小不变；必须使用匹配 Host，旧 Host 不识别新操作。

## 控制 ABI 与插件

客户端新增命名导出 `L4D2BridgePageBlockControl`（WINAPI/stdcall），见 `pageblock_control.h`：ABI version 1 的固定大小 Request/Response；操作 Stats、SetPolicy、Gc，枚举分别为 0/1/2。L4N **插件接口 version 2** 与 Bridge **控制 ABI version 1** 是两个不同版本号。

插件枚举当前已加载模块，查找命名导出，不主动 LoadLibrary 一个 D3D9 runtime。HUD menu 的 callback/user_data 指针按 SDK KeyValues 格式生成。失败显示 HRESULT；GC 返回统计子菜单。插件不持有 D3D9 资源引用，不操作资源内存。未来其他 UI 可复用同一控制 ABI。

## 诊断

输出在客户端 DLL 同目录的 `l4d2-pageblock-gc.log`。显式 GC 总会输出一行 `PB_GC`，至少包含：

`mode`、`pageBlocksScanned`、`pageBlocksEvicted`、`pageBlocksSkippedLocked`、`pageBlocksSkippedTransferring`、`pageBlocksSkippedPolicy`、`bytesUnmapped`、`mappedBytesBefore`、`mappedBytesAfter`；额外输出 `pageBlocksSkippedUnsynchronized`、`failures`、`backingBytesReleased`。force 还有 `transfersDrained`、`drainWaitCount`、`drainWaitTimeMs`。

`bytesUnmapped` 和 mapped before/after 统计实际 view 的 VirtualQuery region 大小，**不等于 RAM 工作集或 section backing 字节数**。只有 view 映射着才能释放 mapped VA；已由预算 trim 解除 view 的 backing 被关闭时，backingBytesReleased 可以非零而 bytesUnmapped 为零。既有 `surfaceViewBudgetBytes` 的 64 KiB 对齐预算收费仍保留。

`PB_DROP_SUMMARY`：`dropEvictionCount`、`dropEvictedBytes`、`remapCountAfterDrop`、`remapBytesAfterDrop`、`reconstructionFailures`。累计释放可重复计算同一资源的多轮 eviction，不能当作同时省下的内存。

开启 `client.pageBlockDiagnostics` 后，新专用日志才逐资源记录 `PB_RESIDENCY event=lock/host-result/evicted/remapped`，包含 ID/type/format/pool/usage/size/mip/face、flags/rect、old_contents_required、previously_evicted 和 reconstruction_required。它们不逐资源刷普通 Info 日志；明确的恢复错误才进入普通 error log。

## 当前范围和已知实现限制

- 注册范围是非 shared-heap 的 surface PagefileShadow：普通 2D mip、cube face mip、独立 surface、backbuffer。VB/IB 使用其他 shadow allocator，volume 使用 per-Lock heap；此任务不把它们重做成第二套 PageBlock allocator。
- current-content recovery 支持原 DXT1/3/5、A8R8G8B8/X8R8G8B8 及显式列举的常见线性颜色格式。先用 `residencyLayout` 验证逻辑行，再处理 Client 最小 4-byte pitch；不比较／依赖 padding。
- ATI1/ATI2 特殊布局、深度、未知 FOURCC、大于 64 MiB 的 subresource 尚无此路径的完整恢复支持。实际 readback 是否可用还取决于该资源的 backend Lock 能力；DEFAULT/RT/MSAA 特例可能返回错误，当前未新增通用 staging/GetRenderTargetData 回退。不是所有 D3D9 资源都已能恢复。
- aggressive/drop 可释放已经由 Host ack 的上述资源；若其后合法 CPU 访问缺少恢复实现，会明确报 implementation-gap。这是实验要揭示的 Bridge 限制，不能描述成 L4D2 本身不允许恢复。
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

## 本轮构建验证

[Windows CI 37598250948](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/actions/runs/37598250948) 在代码提交 `5951831` 全部通过：x86 Client、x64/x86 Host、x86 L4N plugin 编译；x86/x64 residency/GC 原生测试；SDK v2 HUD callback + mock 控制导出测试；既有 Phase 1、真实删除/hash恢复/DB promotion 回归；ATI、adapter、window/input、queue、API-wait 等现有原生检查。Linux 上逻辑布局测试和 6 项 Python 分析测试也通过。

下载的实验产物已校验四个二进制 SHA256、PE 架构和命名导出；不包含替换用 backend 或活动 bridge.conf。没有在云环境执行 L4D2、真实 L4N HUD 或 GPU gameplay，仍待实机验证。

## 仓库文件变更清单

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
