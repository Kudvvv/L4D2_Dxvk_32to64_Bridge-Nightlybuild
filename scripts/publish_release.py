"""Publish a new build instance without replacing a published release."""
import hashlib
import os
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from detect_release import api


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
                or fields[0] != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise ValueError(f"Invalid archive checksum: {path}")
        uploads.extend([str(path), str(checksum)])
    try:
        existing = api(f"repos/{repo}/releases/tags/{tag}")
    except HTTPError as error:
        if error.code != 404:
            raise
        existing = None
    if existing and not existing["draft"]:
        raise RuntimeError("Published release already exists; refusing to replace it")
    upstream = os.environ["UPSTREAM_COMMIT"]
    recipe = os.environ["RECIPE_COMMIT"]
    notes = (
        f"L4D2 Bridge Nightly\n\nUpstream commit: {upstream}\n"
        f"Build recipe: {recipe}\nRecipe digest: {os.environ['RECIPE_DIGEST']}\n\n"
        "包含 x86 客户端和配套 x64 Host；编译与原生测试通过，游戏验收尚待完成。\n\n"
        "- 完整包包含配置及固定 DXVK 后端，适合首次安装。\n"
        "- update 包同时更新客户端和 Host，保留已有配置、DXVK、ReShade 和 DB。\n"
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
                        "--title", tag, "--notes-file", "notes.md", "--prerelease", "--draft"], check=True)
    # No --clobber: even draft assets must not be silently replaced.
    subprocess.run(["gh", "release", "upload", tag, *uploads], check=True)
    subprocess.run(["gh", "release", "edit", tag, "--draft=false", "--prerelease",
                    "--title", tag, "--notes-file", "notes.md"], check=True)


if __name__ == "__main__":
    publish()
