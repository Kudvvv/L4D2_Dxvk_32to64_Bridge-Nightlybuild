"""Publish a new build instance without replacing a published release."""
import hashlib
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
    introduction = (
        f"L4D2 Bridge {title}\n\n"
        "**只提供一个完整 ZIP：包含配套 Client/Host、固定 GPLALL 后端、默认配置及 `tools/thinflex` 修复工具。解压或更新 Bridge 不会自动应用 ThinFlex 引擎补丁。**\n\n"
        "- Bridge 包含三项性能优化：关闭 API 日志时避免临时字符串分配、完整且紧密排列的表面整块复制、普通定期内存扫描移出 Present 线程。\n"
        "- 固定 L4N 回放的三对对照中，配对提升中位数为 1% low **4.57%**、0.1% low **33.09%**、平均 FPS **10.14%**、一秒 Present 峰值 **7.89%**。"
        "p99 帧时间同时增加 **3.48%**，并非所有帧时间指标均改善。性能测试未安装 ThinFlex，不能将这些数据当作合并安装后的性能结果。\n"
        f"- 测试条件、逐对数据与限制见[性能报告](https://github.com/{repo}/blob/{recipe}/docs/PERFORMANCE-2026-10-10.md)。这是单台机器、固定回放的短时对照，不保证其他场景获得相同幅度。\n"
        "- 包内 `tools/thinflex/ThinFlexPatch.exe` 为 Windows 工具，无需安装 Python；"
        "按 `tools/thinflex/README.txt` 运行 `create` 生成单独 DLL 副本和清单，再运行 `verify` 校验，备份后手工安装；工具不会自动安装。\n"
        "- 只接受原始 `studiorender.dll` SHA-256："
        "`3f5f5b0f539e8ad22bcfc4381be41571257c0c29e8061057682f9b8525ca7b85`；未知或已修改版本拒绝处理。\n"
        "- ThinFlex 缓存从 10000 项扩为 65536 项，新增 2 MiB 缓存；保留原有表情计算。"
        "修改后的 DLL 原数字签名失效，恢复方法见工具包说明。\n"
        "- 2026-10-10 收到用户反馈：**v1.0.10 ThinFlex 修复有效**。本次保留相同补丁算法和 DLL 哈希；反馈未提供游玩时长及完整模型范围，不能据此确认所有场景的长期稳定性。\n"
        "- 附件不分发 Valve 游戏 DLL 或玩家私有 dump。Bridge 偏色修复、GPLALL 后端、x64 Host 及默认配置保持原有设计。\n\n")
    channel = "thinflex-test" if experimental else "nightly"
    digest_label = "Experimental recipe digest" if experimental else "Recipe digest"
    notes = introduction + (
        f"Release channel: {channel}\nUpstream commit: {upstream}\n"
        f"Build recipe: {recipe}\n{digest_label}: {os.environ['RECIPE_DIGEST']}\n\n"
        "包含 x86 客户端和配套 x64 Host；编译与原生测试通过。游戏性能对照及 ThinFlex 用户反馈的范围见上述说明与报告。\n\n"
        "- 首次安装按包内说明合并到游戏目录。升级前备份，成对替换客户端和 Host，保留已调整的配置、后端、ReShade 和 DB；不要直接覆盖自己的配置。\n"
        "- 客户端位于 bin/d3d9.dll，默认移除 -vulkan；需要该启动项时自行改名为 dxvk_d3d9.dll ，仍位于 bin。Host 仍在 bin/.l4d2bridge。\n"
        "- 完整 ZIP 包含 UPSTREAM.json 和工具 BUILD.json，附件另提供完整 ZIP 的 SHA-256；旧发布包不被覆盖。\n\n"
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
