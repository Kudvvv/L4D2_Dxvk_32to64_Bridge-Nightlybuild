"""Publish only validated game runtime files and two concise text documents."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from archive_release import archive
from engine_payload import (staged_engine_files, read_regular, ORIGINAL_SHA256,
                            PATCHED_SHA256)
from l4n_payload import staged_l4n_files

PLUGIN_SOURCE = "optional/L4N/L4D2BridgePlugin.dll"
PLUGIN_DESTINATION = "bin/neko/plugins/L4D2BridgePlugin.dll"
REQUIRED = ("bin/d3d9.dll", "bin/.l4d2bridge/L4D2Bridge64.exe",
            "bin/.l4d2bridge/L4D2Bridge32.exe", "bin/.l4d2bridge/d3d9vk_x86.dll",
            PLUGIN_SOURCE,
            "bin/.l4d2bridge/d3d9vk_x64.dll", "bin/.l4d2bridge/bridge.conf")
NOTICE_INPUTS = ("LICENSE", "THIRD_PARTY.md", "licenses/Bridge-MIT.txt",
                "licenses/Bridge-third-party.txt", "licenses/DXVK-LICENSE.txt",
                "licenses/DXVK-GPLALL-LICENSE.txt", "licenses/L4N-NOTICE.txt",
                "licenses/Valve-engine-NOTICE.txt", "readme_l4n.txt")
L4N_RUNTIME_FIXED = frozenset((
    "left4dead2.exe", "dxvk.conf", "bin/left4neko.dll", "crash_dumps/crashpad_handler.exe",
    "left4dead2/bin/game_shader_generic_neko", "left4dead2/bin/game_shader_generic_neko.dll",
    "left4dead2/neko/config.vdf", "left4dead2/neko/key_bind_acts.vdf",
    "left4dead2/neko/l4ngui_english.vdf", "left4dead2/neko/l4ngui_schinese.vdf",
    # Preserve L4N's configuration templates and model/material reference files.
    # A template name or QC extension does not make these disposable build files.
    "left4dead2/neko/localize_overrides_template.vdf", "left4dead2/neko/mdl_extension.qc",
    "left4dead2/neko/neko_proxy.vmt", "left4dead2/neko/scheme_overrides_template.vdf",
    "left4dead2/neko/sequence_event_template.vdf",
    # L4N reads this fallback at runtime when server_name_filter.txt is absent.
    "left4dead2/neko/server_name_filter_template.txt",
    "reshade-shaders/Shaders/L4N/L4N_Util.fx"))
L4N_RUNTIME_PREFIXES = ("left4dead2/materials/l4n/", "left4dead2/shaders/fxc/")
L4N_RUNTIME_COUNT = 58
L4N_RUNTIME_SIZE = 10023581


def select_l4n_runtime(files):
    selected = {name: data for name, data in files.items()
                if name in L4N_RUNTIME_FIXED or name.startswith(L4N_RUNTIME_PREFIXES)}
    if (not L4N_RUNTIME_FIXED.issubset(selected) or len(selected) != L4N_RUNTIME_COUNT
            or sum(map(len, selected.values())) != L4N_RUNTIME_SIZE):
        raise ValueError("L4N runtime selection differs from the audited distribution")
    return selected


def combined_notices(source, verified):
    header = (
        "L4D2 Bridge / DXVK-GPLALL / L4N / Valve engine notices\n"
        "L4N original author: Starfelll (@Starfelll).\n\n"
        "The documents below retain their original text. Referenced Markdown, JSON,\n"
        "source and tool paths identify repository or original-distribution files;\n"
        "those support files are not included in this runtime package.\n"
        "Installation of this integration package follows README.txt. The original\n"
        "L4N instructions below also describe standalone DXVK and developer tools.\n"
        "Repository: https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild\n"
    ).encode("utf-8")
    sections = [header]
    for name in NOTICE_INPUTS:
        data = verified[name] if name in verified else read_regular(source / name)
        if not data.strip():
            raise ValueError(f"Missing required notice text: {name}")
        # Keep each original license/readme byte sequence, including its line endings.
        sections.extend((f"\n\n===== {name} =====\n\n".encode("utf-8"), data))
    return b"".join(sections)


def runtime_archive(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError(f"Archive already exists: {output}")
    for name in REQUIRED:
        if not (source / name).is_file():
            raise ValueError(f"Missing runtime package file: {name}")
    # Full source records remain mandatory, even for files excluded from the ZIP.
    engine_files = staged_engine_files(source)
    l4n_files = staged_l4n_files(source)
    bridge_files = {name: read_regular(source / name) for name in REQUIRED}
    verified = {**engine_files, **l4n_files, **bridge_files}
    hashes = json.loads(read_regular(source / "SHA256.json"))
    version = read_regular(source / "VERSION").decode("utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", version):
        raise ValueError("Invalid source package version")
    # bridge.conf was historically outside the binary manifest. Every shipped
    # Client/Host/backend/plugin must still match the full package's receipt.
    for name in REQUIRED:
        if name.endswith((".dll", ".exe")):
            if hashes.get(name) != hashlib.sha256(verified[name]).hexdigest():
                raise ValueError(f"Runtime binary differs from the source package receipt: {name}")
    notices = combined_notices(source, verified)
    files = {**bridge_files, "bin/studiorender.dll": engine_files["bin/studiorender.dll"],
             **select_l4n_runtime(l4n_files)}
    # The original build receipt verifies the plugin at its staging path;
    # the player ZIP installs that same verified snapshot into L4N directly.
    files[PLUGIN_DESTINATION] = files.pop(PLUGIN_SOURCE)
    files["THIRD-PARTY-NOTICES.txt"] = notices
    files["README.txt"] = (
        f"L4D2 Bridge v{version} runtime package\n\n"
        "可选稳定性更新：修复地图加载/切换时的 IPC 问题。上游初步对照报告平均 FPS 可能下降、切图可能更慢；本 GPLALL 整合包尚未实机复测。没有加载问题时可继续使用 v1.1.10。\n"
        "IPC 协议为 3：bin/d3d9.dll 与 L4D2Bridge32.exe、L4D2Bridge64.exe 必须一起更新或回退，不能混用旧版。\n"
        "已包含 DXVK（GPLALL）、L4N 和桥接工具；退出游戏后备份原文件，将本包解压覆盖到游戏根目录即可安装。请勿与其他类似整合项目混装。\n"
        "移除 -vulkan 启动参数，备份移走游戏根目录的 d3d9.dll；保留本包 bin/d3d9.dll 和 bin/.l4d2bridge 目录。\n"
        "升级时先解压到临时目录，保留原有 dxvk.conf、bin/.l4d2bridge/bridge.conf、left4dead2/neko/config.vdf、自定义后端、ReShade 和 retention DB，再合并覆盖。客户端与两个 Host 一并更新、回退。\n"
        "L4N 原作者：Starfelll（@Starfelll）。Bridge 设置菜单插件已放在 bin/neko/plugins/L4D2BridgePlugin.dll，随包安装；不需要菜单时退出游戏后移走该 DLL。\n"
        "已含 ThinFlex 修复，无需运行修复工具。覆盖前备份原始 bin/studiorender.dll；已修复玩家保留最初原始备份。只有下列原版或修复版身份匹配时才替换，未知游戏版本请从临时目录移除该 DLL。回退时恢复对应原版备份。\n"
        f"ThinFlex 原版 SHA-256：{ORIGINAL_SHA256}\n"
        f"ThinFlex 修复版 SHA-256：{PATCHED_SHA256}\n\n"
        "完整文档、配置说明与来源校验：\n"
        "https://github.com/NPCodex/L4D2_Dxvk_32to64_Bridge-Nightlybuild\n"
        "第三方许可及原作者说明见 THIRD-PARTY-NOTICES.txt。\n"
    ).encode("utf-8")
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary) / "runtime"
        stage.mkdir()
        for name, data in files.items():
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    runtime_archive(args.source.resolve(), args.output.resolve())
