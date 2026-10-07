"""Publish only runtime files, license notices and a short installation guide."""
import argparse
from pathlib import Path
import shutil
import tempfile
from archive_release import archive

REQUIRED = ("bin/dxvk_d3d9.dll", "bin/.l4d2bridge/L4D2Bridge64.exe",
            "bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/bridge.conf",
            "LICENSE", "THIRD_PARTY.md")

def runtime_archive(source, output):
    for name in REQUIRED:
        if not (source / name).is_file():
            raise ValueError(f"Missing runtime package file: {name}")
    licenses = sorted((source / "licenses").glob("*.txt"))
    if not licenses:
        raise ValueError("Missing third-party licenses")
    with tempfile.TemporaryDirectory() as temporary:
        stage=Path(temporary)
        for name in REQUIRED + tuple(p.relative_to(source).as_posix() for p in licenses):
            destination=stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, destination)
        (stage / "README.txt").write_text(
            "L4D2 Bridge Nightly\n\n"
            "安装：退出游戏，将本包 bin 文件夹合并到游戏根目录的 bin 文件夹，保留 .l4d2bridge 目录结构。覆盖前备份原文件。\n"
            "卸载：移除本包安装的文件，并恢复备份。\n\n"
            "版本、上游提交及构建记录：\n"
            "https://github.com/YuuMJ/L4D2_Dxvk_32to64_Bridge-Nightlybuild/releases\n"
            "许可证与第三方来源见 LICENSE、THIRD_PARTY.md 和 licenses 文件夹。\n",
            encoding="utf-8")
        archive(stage, output)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    runtime_archive(args.source.resolve(),args.output.resolve())
