"""Publish only runtime files, license notices and a short installation guide."""
import argparse
from pathlib import Path
import shutil
import tempfile
from archive_release import archive
from engine_payload import staged_engine_files

REQUIRED = ("bin/d3d9.dll", "bin/.l4d2bridge/L4D2Bridge64.exe",
            "bin/.l4d2bridge/L4D2Bridge32.exe", "bin/.l4d2bridge/d3d9vk_x86.dll",
            "optional/L4N/L4D2BridgePlugin.dll",
            "bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/bridge.conf",
            "LICENSE", "THIRD_PARTY.md")
SUPPORT_FILES = (
    "BACKEND.json", "BUILD-INFO.json", "SHA256.json",
    "docs/L4N-BRIDGE-CONTROLS.md", "docs/CONFIGURATION.md", "docs/API.md", "docs/ARCHITECTURE.md",
    "docs/PAGEBLOCK-DROP-GC.md", "docs/LEARNED-RETENTION-EXPERIMENT.md", "docs/READBACK-RECOVERY-EXPERIMENT.md",
    "docs/X86-HOST-COMPARISON.md", "docs/OVERLAY-INPUT-EXPERIMENT.md", "docs/STEAM-INPUT-INVESTIGATION.md",
    "docs/API-WAIT-DIAGNOSTICS.md", "docs/NETWORK-COLOR-DIAGNOSTICS.md", "docs/DATA-TRACKING.md",
    "docs/MEMORY-DIAGNOSTICS.md", "docs/HOST-MEMORY-DIAGNOSTICS.md", "docs/RUNTIME-DIAGNOSTICS-SEPARATION.md",
    "config/X64-HOST.conf", "config/X86-HOST.conf", "config/OVERLAY-INPUT.conf",
    "config/STEAM-INPUT-DIAGNOSTICS.conf", "config/API-WAIT-DIAGNOSTICS.conf",
    "config/NETWORK-COLOR-DIAGNOSTICS.conf", "config/DATA-TRACKING.conf", "config/PAGEBLOCK-DROP.conf",
    "scripts/analyze_api_wait.py", "scripts/analyze_color_diagnostics.py", "scripts/analyze_data_diagnostics.py",
    "scripts/install_color_diagnostics.ps1")

def runtime_archive(source, output):
    source, output = Path(source), Path(output)
    required = REQUIRED + SUPPORT_FILES + ("UPSTREAM.json",)
    if output.exists():
        raise FileExistsError(f"Archive already exists: {output}")
    for name in required:
        if not (source / name).is_file():
            raise ValueError(f"Missing runtime package file: {name}")
    licenses = sorted((source / "licenses").glob("*.txt"))
    if not licenses:
        raise ValueError("Missing third-party licenses")
    engine_files = staged_engine_files(source)
    with tempfile.TemporaryDirectory() as temporary:
        stage=Path(temporary) / "runtime"
        stage.mkdir()
        for name in required + tuple(p.relative_to(source).as_posix() for p in licenses):
            destination=stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
        if (source / "VERSION").is_file():
            shutil.copy2(source / "VERSION", stage / "VERSION")
        for name, data in engine_files.items():
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        instruction = (
            "完整包：先退出游戏及 Host，备份现有安装，再将本包解压到临时目录。\n"
            "本包已含 ThinFlex 修复后的 bin/studiorender.dll，无需运行修复工具；适用版本及原文件 SHA-256 见 ENGINE-PATCH.json。\n"
            "覆盖前单独备份原始 bin/studiorender.dll。已修复的用户保留原始备份，不要把它替换成修复版；游戏更新后文件版本不同则先跳过该 DLL。\n"
            "升级已有安装时，先从临时目录移除 bin/.l4d2bridge/bridge.conf；使用自定义后端的用户同时移除临时目录中的 bin/.l4d2bridge/d3d9vk_x64.dll 和 d3d9vk_x86.dll。\n"
            "然后将临时目录内容合并到游戏根目录，客户端位于 bin/d3d9.dll，保留 bin/.l4d2bridge 结构。\n"
            "首次安装可保留包内默认配置和 GPLALL 后端。已有 dxvk.conf、bridge.conf、ReShade 和 retention DB 应予保留。\n"
            "客户端和 x86/x64 两个 Host 必须配对更新，故障回退时也同时恢复，不要混用。默认使用 x64 Host；切换说明见 docs/X86-HOST-COMPARISON.md。\n"
            "可选 L4N 控制插件位于 optional/L4N/L4D2BridgePlugin.dll，需要时复制到游戏 bin/neko/plugins/；普通 Bridge 不依赖它。详见 docs/L4N-BRIDGE-CONTROLS.md。\n"
            "附带 config/ 片段只用于手动启用相关功能，不会自动覆盖配置。诊断分析脚本位于 scripts/；普通安装不运行 install_color_diagnostics.ps1。\n"
            "回退 ThinFlex 时恢复原始 studiorender.dll，相关来源说明见 licenses/Valve-engine-NOTICE.txt。\n")
        (stage / "README.txt").write_text(
            "L4D2 Bridge Nightly\n\n" + instruction +
            "默认移除 -vulkan 启动项。需要 -vulkan 时，自行把客户端改名为 dxvk_d3d9.dll ，文件仍留在 bin。\n"
            "从旧版迁移前备份 bin/dxvk_d3d9.dll；已有bin/d3d9.dll 也需先备份。\n"
            "卸载：移除本包安装的文件，并恢复备份。\n\n"
            "版本、上游提交及构建记录：\n"
            "https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases\n"
            "许可证与第三方来源见 LICENSE、THIRD_PARTY.md 和 licenses 文件夹。\n",
            encoding="utf-8")
        temporary_zip = Path(temporary) / "runtime.zip"
        archive(stage, temporary_zip)
        created_output = False
        try:
            with output.open("xb") as target:
                created_output = True
                with temporary_zip.open("rb") as source_zip:
                    shutil.copyfileobj(source_zip, target)
        except BaseException:
            if created_output:
                output.unlink(missing_ok=True)
            raise

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    runtime_archive(args.source.resolve(),args.output.resolve())
