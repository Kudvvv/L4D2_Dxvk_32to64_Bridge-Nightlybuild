"""Publish a new build instance without replacing a published release."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from detect_release import api


def file_sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def find_release(repo, tag):
    match = None
    page = 1
    while True:
        releases = api(f"repos/{repo}/releases?per_page=100&page={page}")
        for release in releases:
            if release["tag_name"] == tag:
                if match is not None:
                    raise RuntimeError(f"Multiple releases use tag: {tag}")
                match = release
        if len(releases) < 100:
            return match
        page += 1


def verify_existing_asset(repo, asset, path):
    if asset.get("state") != "uploaded" or asset.get("size") != path.stat().st_size:
        raise RuntimeError(f"Existing draft asset is incomplete or differs: {path.name}")
    expected = file_sha256(path)
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        actual = digest.removeprefix("sha256:")
    else:
        # Older assets have no digest. Read their actual bytes before reusing them;
        # a matching filename, size or adjacent checksum file is insufficient.
        with tempfile.TemporaryFile() as downloaded:
            subprocess.run(["gh", "api", f"repos/{repo}/releases/assets/{asset['id']}",
                            "-H", "Accept: application/octet-stream"],
                           check=True, stdout=downloaded)
            downloaded.seek(0)
            actual = hashlib.file_digest(downloaded, "sha256").hexdigest()
    if actual != expected:
        raise RuntimeError(f"Existing draft asset content differs: {path.name}")


def pending_uploads(repo, release, uploads):
    remote = {}
    page = 1
    while True:
        assets = api(f"repos/{repo}/releases/{release['id']}/assets?per_page=100&page={page}")
        for asset in assets:
            name = asset["name"]
            if name in remote:
                raise RuntimeError(f"Duplicate draft asset: {name}")
            remote[name] = asset
        if len(assets) < 100:
            break
        page += 1
    if set(remote) - {Path(name).name for name in uploads}:
        raise RuntimeError("Unexpected draft attachment; refusing to publish it")
    missing = []
    # Verify every existing attachment before changing the draft at all.
    for filename in uploads:
        path = Path(filename)
        if path.name in remote:
            verify_existing_asset(repo, remote[path.name], path)
        else:
            missing.append(filename)
    return missing


def publish():
    tag = os.environ["RELEASE_TAG"]
    repo = os.environ["GITHUB_REPOSITORY"]
    experimental = os.environ.get("THINFLEX_TEST", "false").lower() == "true"
    title = os.environ.get("RELEASE_TITLE", tag)
    if experimental:
        if "-thinflex-test-" not in tag:
            raise ValueError("ThinFlex test release requires a -thinflex-test- tag")
        if "ThinFlex" not in title or "测试" not in title:
            raise ValueError("ThinFlex test release title must include ThinFlex and 测试")
    elif "-thinflex-test-" in tag:
        raise ValueError("ThinFlex test tag requires the experimental release channel")
    name = os.environ.get("ARCHIVE_NAME", "")
    expected_names = {name, name + ".sha256"}
    files = list(Path("assets").iterdir())
    if (not name.endswith(".zip") or "/" in name or "\\" in name
            or {path.name for path in files} != expected_names
            or any(not path.is_file() or path.is_symlink() for path in files)):
        raise ValueError("Expected exactly the named full package and its SHA-256 sidecar")
    assets = [Path("assets") / name]
    uploads = []
    for path in assets:
        checksum = Path(str(path) + ".sha256")
        fields = checksum.read_text(encoding="ascii").split()
        if (len(fields) != 2 or fields[1] != path.name
                or fields[0] != file_sha256(path)):
            raise ValueError(f"Invalid archive checksum: {path}")
        uploads.extend([str(path), str(checksum)])
    existing = find_release(repo, tag)
    if existing and not existing["draft"]:
        raise RuntimeError("Published release already exists; refusing to replace it")
    if existing:
        uploads = pending_uploads(repo, existing, uploads)
    upstream = os.environ["UPSTREAM_COMMIT"]
    recipe = os.environ["RECIPE_COMMIT"]
    original = json.loads((Path(__file__).resolve().parents[1] / "config/original-project.json").read_text(encoding="utf-8"))
    introduction = (
        f"L4D2 Bridge {title}\n\n"
        "**只提供一个完整 ZIP：已包含 DXVK（GPLALL）、L4N 2.51.0、完整桥接工具和已修复的 `bin/studiorender.dll`。备份后解压覆盖到游戏根目录即可安装，请勿与其他类似整合项目混装。核对游戏 DLL 版本并备份后，复制文件即可应用 ThinFlex 修复，无需运行补丁工具或安装 Python。**\n\n"
        "- L4N / Left4Neko 原作者：**Starfelll**。运行所需的启动器、模块、着色器、素材及原配套 VDF 模板和 QC/VMT 范例原样保留；开发 SDK 与离线转换工具不随安装包提供。作者原始说明原文合并到 `THIRD-PARTY-NOTICES.txt`；另含用户提供的 `dxvk.conf`、L4N `config.vdf` 及配套 shader 预设，不能将这些预设当作作者原始默认值。逐文件来源及 SHA-256 保留在仓库 `runtime/l4n/manifest.json`，包内归属见 `THIRD-PARTY-NOTICES.txt`。\n"
        f"- 完整合并 L4D2 原项目 **{original['version']}**（`{original['commit']}`），包括 PageBlock/retention/readback、ReShade Presenter、Steam 输入支持、诊断体系、x86 Host 和 L4N 控制插件。\n"
        f"- 合并范围及本分支保留项见[更新记录](https://github.com/{repo}/blob/{recipe}/docs/ORIGINAL-PROJECT-UPDATES.md)。默认继续使用 GPLALL 后端和 x64 Host；可选功能按仓库文档启用。\n"
        "- 同一完整包包含配套 x86 Client、x86/x64 Host、两种架构的 GPLALL 后端，以及 `bin/neko/plugins/L4D2BridgePlugin.dll`。Bridge 设置菜单随包安装；不需要菜单时退出游戏后移走该 DLL。\n"
        f"- 本次完整合并版本尚未进行游戏 FPS 对照，不宣称性能提升。此前[性能报告](https://github.com/{repo}/blob/{recipe}/docs/PERFORMANCE-2026-10-10.md)对应旧版与固定回放，性能测试未安装 ThinFlex，不能当作本次完整合并后的性能结果。\n"
        f"- 玩家包不包含补丁工具；先阅读包内 `README.txt`，详细安装与回退见[说明](https://github.com/{repo}/blob/{recipe}/docs/THINFLEX-TEST-README.txt)。升级前关闭游戏及 Host，备份原文件，保留已有配置及自定义后端。已打补丁的玩家须保留最初原版 DLL 备份，不能用修复文件覆盖它。\n"
        "- 支持的原始 `studiorender.dll` SHA-256："
        "`3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85`；"
        "包内修复 DLL SHA-256：`03964dedcf8b7f4ebde24cd3d0738873d37c075a7a9b313dad001bb937f9d1b6`。"
        "原始哈希匹配时可替换；已是修复哈希时可保留；未知版本应从临时解压目录移除 `bin/studiorender.dll`，仅更新 Bridge。\n"
        "- ThinFlex 缓存从 10000 项扩为 65536 项，新增 2 MiB 缓存；保留原有表情计算。"
        "修改后的 DLL 原数字签名失效；回退前须核对原版备份及当前 DLL 身份，不能用旧备份覆盖游戏更新后的未知版本。\n"
        "- 2026-10-10 收到用户反馈：**v1.0.10 ThinFlex 修复有效**。本次保留相同补丁算法和 DLL 哈希；反馈未提供游玩时长及完整模型范围，不能据此确认所有场景的长期稳定性。\n"
        "- 包内引擎 DLL 归属 Valve，不适用项目根目录 MIT 许可；公开 Source SDK 的常量参考不代表其许可覆盖整个游戏 DLL。见包内 `THIRD-PARTY-NOTICES.txt` 与仓库 `runtime/engine/studiorender.manifest.json`。附件不包含玩家私有 dump。Bridge 偏色修复、GPLALL 后端和默认 x64 Host 保留。\n\n")
    channel = "thinflex-test" if experimental else "nightly"
    digest_label = "Experimental recipe digest" if experimental else "Recipe digest"
    notes = introduction + (
        f"Release channel: {channel}\nUpstream commit: {upstream}\n"
        f"L4D2 original project: {original['repository']}\nL4D2 original commit: {original['commit']}\nL4D2 original version: {original['version']}\n"
        f"Build recipe: {recipe}\n{digest_label}: {os.environ['RECIPE_DIGEST']}\n\n"
        "包含 x86 客户端和配套 x86/x64 Host；编译与原生测试通过。游戏性能对照及 ThinFlex 用户反馈的范围见上述说明与报告。\n\n"
        "- 首次安装按包内说明合并到游戏目录。升级前备份，一并替换客户端和两种 Host，先从临时目录移除已有的 `dxvk.conf`、`bin/.l4d2bridge/bridge.conf` 和 `left4dead2/neko/config.vdf`，保留已调整的配置、后端、ReShade 和 DB。\n"
        "- 安装前移除 -vulkan，备份移走游戏根目录的 d3d9.dll；保留本包的 bin/d3d9.dll 桥接客户端。Host 位于 bin/.l4d2bridge。随包保留用户提供的 L4N config.vdf，不附 config_template.vdf。\n"
        "- 完整 ZIP 包含运行组件、实际配置、L4N 配套模板和 QC/VMT 范例、README.txt 和合并的 THIRD-PARTY-NOTICES.txt；不含 MD、JSON、开发 SDK、诊断脚本、离线 Mod 工具、私人日志或 dump。附件另提供完整 ZIP 的 SHA-256；旧发布包不被覆盖。\n\n"
        f"上游：[NVIDIA 提交](https://github.com/NVIDIAGameWorks/dxvk-remix/commit/{upstream})\n\n"
        f"本项目：[构建配置](https://github.com/{repo}/commit/{recipe}) · "
        f"[构建记录](https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']})\n\n"
        "偏色问题定位和原始修复 credits："
        "[keyou91 / PR #3](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/pull/3)。\n\n"
        "版本日期采用上游提交的 UTC 日期。测试步骤与性能记录工具见仓库 docs/GAME-VALIDATION.md。\n")
    Path("notes.md").write_text(notes, encoding="utf-8", newline="\n")
    if existing is None:
        subprocess.run(["gh", "release", "create", tag, "--target", recipe,
                        "--title", title, "--notes-file", "notes.md", "--prerelease", "--latest=false", "--draft"], check=True)
    # No --clobber: even draft assets must not be silently replaced.
    if uploads:
        subprocess.run(["gh", "release", "upload", tag, *uploads], check=True)
    subprocess.run(["gh", "release", "edit", tag, "--draft=false", "--prerelease", "--latest=false",
                    "--title", title, "--notes-file", "notes.md"], check=True)


if __name__ == "__main__":
    publish()
