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
    assets = sorted(Path("assets").glob("*.zip"))
    if len(assets) != 2:
        raise ValueError("Expected a full package and a paired update package")
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
    notes = (
        f"L4D2 Bridge {os.environ.get('RELEASE_TITLE', tag)} Nightly\n\nUpstream commit: {upstream}\n"
        f"Build recipe: {recipe}\nRecipe digest: {os.environ['RECIPE_DIGEST']}\n\n"
        "包含 x86 客户端和配套 x64 Host；编译与原生测试通过，游戏验收尚待完成。\n\n"
        "- 完整包包含配置及固定 DXVK 后端，适合首次安装。\n"
        "- update 包同时更新客户端和 Host，保留已有配置、DXVK、ReShade 和 DB。\n"
        "- 客户端位于 bin/d3d9.dll，默认移除 -vulkan；需要该启动项时自行改名为 dxvk_d3d9.dll ，仍位于 bin。Host 仍在 bin/.l4d2bridge。\n"
        "- 两个 ZIP 均包含 UPSTREAM.json 并附带 SHA-256；旧发布包不被覆盖。\n\n"
        f"上游：[NVIDIA 提交](https://github.com/NVIDIAGameWorks/dxvk-remix/commit/{upstream})\n\n"
        f"本项目：[构建配置](https://github.com/{repo}/commit/{recipe}) · "
        f"[构建记录](https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']})\n\n"
        "偏色问题定位和原始修复 credits："
        "[keyou91 / PR #3](https://github.com/yeyunyyds/L4D2_Dxvk_32to64_Bridge/pull/3)。\n\n"
        "版本日期采用上游提交的 UTC 日期。测试步骤与性能记录工具见仓库 docs/GAME-VALIDATION.md。\n")
    Path("notes.md").write_text(notes, encoding="utf-8", newline="\n")
    if existing is None:
        subprocess.run(["gh", "release", "create", tag, "--target", recipe,
                        "--title", os.environ.get("RELEASE_TITLE", tag), "--notes-file", "notes.md", "--prerelease", "--draft"], check=True)
    # No --clobber: even draft assets must not be silently replaced.
    if uploads:
        subprocess.run(["gh", "release", "upload", tag, *uploads], check=True)
    subprocess.run(["gh", "release", "edit", tag, "--draft=false", "--prerelease",
                    "--title", os.environ.get("RELEASE_TITLE", tag), "--notes-file", "notes.md"], check=True)


if __name__ == "__main__":
    publish()
