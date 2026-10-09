# 2026-10-10 完整包体积精简

玩家完整包直接包含已验证的 `bin/studiorender.dll`，移除随包的 Python 补丁工具。下载后按 README 备份、核对游戏 DLL 版本并复制安装。Bridge 补丁、GPLALL 后端和默认配置未在这次精简中改变。

## 体积记录

| 对象 | 字节数 | 说明 |
| --- | ---: | --- |
| v1.0.13 已发布完整 ZIP | 10,906,091 | 对照基准；包含 Python 工具 |
| 原发布 ThinFlex 工具 EXE | 8,096,402 | 工具在 ZIP 中占 7,905,199 字节 |
| Python 依赖精简后的实验 EXE | 6,093,159 | 移除未使用的 OpenSSL、bz2、lzma 依赖，较原工具小 24.74% |
| 原生维护工具，GCC 严格编译 | 262,144 | 仅依赖 Windows 系统 DLL；不放进玩家 ZIP |
| 固定修复结果 studiorender.dll | 634,672 | 与原 DLL 文件长度相同；新增缓存是零填充虚拟节 |
| 新完整包本地预览 ZIP | 3,136,296 | 复用 v1.0.13 Bridge 二进制，加入固定修复 DLL，ZIP Deflate 级别 9 |

本地预览较发布基准减少 7,769,795 字节，约 **71.24%**。这不是新 CI 产物的最终大小；新构建的精确大小及 SHA-256 以 GitHub Release 附件为准。只把旧包压缩级别提高到 9 的独立实验节省 13,588 字节，主要收益来自移除玩家包中的 Python 运行时。没有采用可执行文件壳压缩。

## 验证与复现

- 四种 Python 工具构建共 52 项检查通过，包括实际受支持 DLL 输出等价、Unicode 路径、显式实验选项、拒绝覆盖和篡改拒绝。
- 原生实现与 Python 参考进行 13 项等价及失败路径测试：合成 PE、双向校验、JSON 语义、Unicode 路径、并发创建、写入失败清理及生产工具拒绝测试输入。GCC 使用 `-Wall -Wextra -Werror`；MSVC 使用 `/W4 /WX`，并作为发布前 CI 门槛。
- 本机匹配原 DLL 的原生输出与 Python 输出及仓库中修复 DLL 逐字节一致；原游戏文件未修改。
- 包装验证固定 DLL 与补丁记录的哈希，只把列出的运行文件和归属说明放入 ZIP；旧工具、其他引擎 DLL、日志和 dump 均不进入玩家包。
- 精简过程未启动游戏，未重测帧率。已有性能结果的适用范围见 [性能报告](PERFORMANCE-2026-10-10.md)。

维护者可运行：

```powershell
python -m unittest discover -s tests -p 'test_*.py'
./scripts/build_thinflex_native.ps1
./scripts/test_thinflex_native.ps1
```

普通测试发现流程在没有原生 EXE 时会跳过原生测试；Windows 发布任务会编译生产版与隔离的测试版，显式执行全部 13 项，缺失或跳过都会使该门槛失败。维护工具的 `create` / `verify` 操作见 [ThinFlex 说明](THINFLEX-CRASH-FIX.md)。
