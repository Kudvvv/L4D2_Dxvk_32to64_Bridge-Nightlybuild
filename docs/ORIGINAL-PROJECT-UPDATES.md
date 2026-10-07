# 原项目更新跟踪

已检查基准：`6c6dc09d7b1053f304ff6d7b353edadb46d6ca78`（2026-10-07）。来源：[L4D2 原项目](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/tree/6c6dc09d7b1053f304ff6d7b353edadb46d6ca78)。

## 本批移植

- `494bc3f`：2D 纹理创建失败返回真实 HRESULT，清空输出并释放客户端 wrapper；明确失败不销毁不存在的服务器对象，超时保留有序销毁。移植时去掉 retention fingerprint 和 Host 内存诊断依赖。
- `13183fa`：ATI1/ATI2 压缩布局、较小 mip、区域上传与回传边界修复，包含客户端、Host 和布局辅助头文件。
- `1e2d7e2`、`f9fbecc` 及后续修正：使用跨进程事件等待空队列，合并通知，按值复制待消费命令避免队列回绕覆盖。使用基准版本的最终实现与测试。

版权与原始声明保留。现有三维纹理偏色修复继续保留；GPLALL 后端、x64 Host 和默认配置未改变。

## 验证

完整补丁以 NVIDIA 基准 `9aa74f8dfad2188efbd0f717c64d9f8fa909787e` 重新生成，在上游 `e4e7303d6d9cf2cb9e53029277c62f8f7d8c5a98` 上通过应用检查。现有 Python 测试通过。

CI 增加纹理失败处理测试、ATI1/ATI2 x86/x64 边界测试，以及真实 x86/x64 跨进程队列压力、空闲 CPU、取消与超时测试。编译和原生测试结果以对应 Actions 为准。

游戏复测：固定后端与配置，对比菜单 Host CPU，进入带 Mod 地图检查纹理与色调，连续换图、截图并正常退出。原项目的实测结果不能替代本 Nightly/GPLALL 组合复测。

## 延后项目

learned-aggressive retention、readback recovery、ReShade presenter、x86 Host 和自定义 DXVK 内存后端未合入。本批也未加入依赖 x86 Host 的 adapter/caps 扩展和额外资源诊断。后续检查应识别这些已延后的内容，不能将它们当作遗漏自动覆盖现有补丁。
