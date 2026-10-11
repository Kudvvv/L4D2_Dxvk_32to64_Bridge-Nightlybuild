"""Publish a new build instance without replacing a published release."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from detect_release import api

ROOT = Path(__file__).resolve().parents[1]


def current_release_notes(root=None):
    """Require notes for this VERSION, so later releases cannot reuse old prose."""
    root = ROOT if root is None else root
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    heading, separator, body = (root / "docs/RELEASE-NOTES.md").read_text(encoding="utf-8").partition("\n")
    if heading.strip() != f"# v{version}" or not separator or not body.strip():
        raise ValueError("Current release notes must match VERSION and contain this release's changes")
    return body.strip()


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
    changes = current_release_notes()
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
    original = json.loads((ROOT / "config/original-project.json").read_text(encoding="utf-8"))
    channel = "thinflex-test" if experimental else "nightly"
    digest_label = "Experimental recipe digest" if experimental else "Recipe digest"
    notes = (
        f"L4D2 Bridge {title}\n\n{changes}\n\n"
        f"[安装与回退说明](https://github.com/{repo}/blob/{recipe}/README.md) · "
        f"[本次构建记录](https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']})\n\n"
        "<details>\n<summary>构建指纹</summary>\n\n"
        f"Release channel: {channel}\nUpstream commit: {upstream}\n"
        f"L4D2 original project: {original['repository']}\nL4D2 original commit: {original['commit']}\nL4D2 original version: {original['version']}\n"
        f"Build recipe: {recipe}\n{digest_label}: {os.environ['RECIPE_DIGEST']}\n\n"
        "</details>\n")
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
