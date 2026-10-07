"""Publish only runtime files, license notices and a short installation guide."""
import argparse
from pathlib import Path
import shutil
import tempfile
from archive_release import archive

REQUIRED = ("bin/d3d9.dll", "bin/.l4d2bridge/L4D2Bridge64.exe",
            "bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/bridge.conf",
            "LICENSE", "THIRD_PARTY.md")

def runtime_archive(source, output, update=False):
    required = REQUIRED if not update else tuple(n for n in REQUIRED
        if n not in ("bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/bridge.conf"))
    required += ("UPSTREAM.json",)
    if output.exists():
        raise FileExistsError(f"Archive already exists: {output}")
    for name in required:
        if not (source / name).is_file():
            raise ValueError(f"Missing runtime package file: {name}")
    licenses = sorted((source / "licenses").glob("*.txt"))
    if not licenses:
        raise ValueError("Missing third-party licenses")
    with tempfile.TemporaryDirectory() as temporary:
        stage=Path(temporary)
        for name in required + tuple(p.relative_to(source).as_posix() for p in licenses):
            destination=stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
        if (source / "VERSION").is_file():
            shutil.copy2(source / "VERSION", stage / "VERSION")
        instruction = (
            "更新包：首次安装请使用完整包。退出游戏及 Host，备份后同时更新bin/d3d9.dll 和 bin/.l4d2bridge 中的 Host。\n"
            "本包不含配置或 DXVK 后端，保留已有配置、后端、ReShade 和 retention DB。\n"
            "故障回退时同时恢复旧客户端和 Host，不要混用。\n"
            if update else
            "完整包：退出游戏，将包内容合并到游戏根目录，客户端位于 bin/d3d9.dll，保留 bin/.l4d2bridge 结构。\n"
            "覆盖前备份；本包包含配置和后端，升级已有安装建议使用 update 包。\n")
        (stage / "README.txt").write_text(
            "L4D2 Bridge Nightly\n\n" + instruction +
            "默认移除 -vulkan 启动项。需要 -vulkan 时，自行把客户端改名为 dxvk_d3d9.dll ，文件仍留在 bin。\n"
            "从旧版迁移前备份 bin/dxvk_d3d9.dll；已有bin/d3d9.dll 也需先备份。\n"
            "卸载：移除本包安装的文件，并恢复备份。\n\n"
            "版本、上游提交及构建记录：\n"
            "https://github.com/Kudvvv/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases\n"
            "许可证与第三方来源见 LICENSE、THIRD_PARTY.md 和 licenses 文件夹。\n",
            encoding="utf-8")
        archive(stage, output)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--update", action="store_true")
    args=parser.parse_args()
    runtime_archive(args.source.resolve(),args.output.resolve(),args.update)
