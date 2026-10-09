"""Publish only runtime files, license notices and a short installation guide."""
import argparse
from pathlib import Path
import shutil
import tempfile
from archive_release import archive
from package_thinflex_test import read_tool_directory

REQUIRED = ("bin/d3d9.dll", "bin/.l4d2bridge/L4D2Bridge64.exe",
            "bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/bridge.conf",
            "LICENSE", "THIRD_PARTY.md")

def runtime_archive(source, output):
    source, output = Path(source), Path(output)
    required = REQUIRED + ("UPSTREAM.json",)
    if output.exists():
        raise FileExistsError(f"Archive already exists: {output}")
    for name in required:
        if not (source / name).is_file():
            raise ValueError(f"Missing runtime package file: {name}")
    licenses = sorted((source / "licenses").glob("*.txt"))
    if not licenses:
        raise ValueError("Missing third-party licenses")
    tool_files = read_tool_directory(source / "tools/thinflex")
    with tempfile.TemporaryDirectory() as temporary:
        stage=Path(temporary) / "runtime"
        stage.mkdir()
        for name in required + tuple(p.relative_to(source).as_posix() for p in licenses):
            destination=stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
        if (source / "VERSION").is_file():
            shutil.copy2(source / "VERSION", stage / "VERSION")
        for name, data in tool_files.items():
            destination = stage / "tools/thinflex" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        instruction = (
            "完整包：先退出游戏及 Host，备份现有安装，再将本包解压到临时目录。\n"
            "升级已有安装时，先从临时目录移除 bin/.l4d2bridge/bridge.conf；使用自定义后端的用户同时移除临时目录中的 bin/.l4d2bridge/d3d9vk_x64.dll。\n"
            "然后将临时目录内容合并到游戏根目录，客户端位于 bin/d3d9.dll，保留 bin/.l4d2bridge 结构。\n"
            "首次安装可保留包内默认配置和 GPLALL 后端。已有 dxvk.conf、bridge.conf、ReShade 和 retention DB 应予保留。\n"
            "客户端和 Host 必须配对更新，故障回退时也同时恢复，不要混用。\n"
            "ThinFlex 修复工具和说明位于 tools/thinflex；它不会自动修改游戏引擎文件，需要时按该目录 README.txt 操作。\n")
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
