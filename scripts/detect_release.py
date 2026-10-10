"""Follow the latest Remix default-branch commit, or a manually selected SHA."""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from release_names import classify
from pathlib import Path
from build_identity import recipe_digest

UPSTREAM = "repos/NVIDIAGameWorks/dxvk-remix"


def api(path):
    request = urllib.request.Request("https://api.github.com/" + path, headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(2 ** attempt)


def pending():
    force = os.environ.get("FORCE_REBUILD", "false").lower() == "true"
    thinflex = os.environ.get("THINFLEX_TEST", "false").lower() == "true"
    channel = "thinflex-test" if thinflex else "nightly"
    digest_label = "Experimental recipe digest" if thinflex else "Recipe digest"
    manual = os.environ.get("UPSTREAM_COMMIT", "").strip()
    if manual:
        if not re.fullmatch(r"[0-9a-fA-F]{40}", manual):
            raise ValueError("Manual builds require a full 40-character commit SHA")
        ref, branch = manual, "manual"
    else:
        branch = api(UPSTREAM)["default_branch"]
        ref = branch
    info = api(f"{UPSTREAM}/commits/{urllib.parse.quote(ref, safe='')}")
    commit = info["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid resolved upstream SHA")
    recipe = recipe_digest()
    if not force:
        page = 1
        while True:
            releases = api(f"repos/{os.environ['GITHUB_REPOSITORY']}/releases?per_page=100&page={page}")
            for release in releases:
                lines = (release.get("body") or "").splitlines()
                release_channel = next((line.split(": ", 1)[1] for line in lines
                                        if line.startswith("Release channel: ")), "nightly")
                if (not release["draft"] and f"Upstream commit: {commit}" in lines
                        and release_channel == channel
                        and f"{digest_label}: {recipe}" in lines):
                    print(f"Already published upstream and recipe as {release['tag_name']}")
                    return []
            if len(releases) < 100:
                break
            page += 1
    else:
        print(f"Force rebuild enabled for upstream {branch}: {commit}")
    names = classify(commit, info["commit"]["committer"]["date"], recipe,
                     os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"])
    version = (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", version):
        raise ValueError("Invalid project version")
    identifier = "v" + version + ("-thinflex-test-" if thinflex else "-") + names["release_tag"]
    original = json.loads((Path(__file__).resolve().parents[1] / "config/original-project.json").read_text(encoding="utf-8"))
    title = "v" + version + " L4N 整合包 · 完整同步上游 " + original["version"] + (" + ThinFlex 测试版" if thinflex else "")
    names.update(release_tag=identifier, title=title,
                 archive="l4d2-bridge-" + identifier + ".zip")
    return [{"tag": names["group"], "commit": commit, "branch": branch,
             "recipe_digest": recipe, **names}]


if __name__ == "__main__":
    rows = pending()
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("matrix=" + json.dumps({"include": rows}) + "\n")
        output.write("pending=" + str(bool(rows)).lower() + "\n")
    print(json.dumps(rows, indent=2))


