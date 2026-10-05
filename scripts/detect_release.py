"""Follow the latest Remix default-branch commit, or a manually selected SHA."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from release_names import classify

UPSTREAM = "repos/NVIDIAGameWorks/dxvk-remix"


def api(path):
    request = urllib.request.Request("https://api.github.com/" + path, headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def pending():
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
    local = "bridge-commit-" + commit
    try:
        existing = api(f"repos/{os.environ['GITHUB_REPOSITORY']}/releases/tags/{local}")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    else:
        if not existing["draft"]:
            print(f"Already built upstream {branch}: {commit}")
            return []
    names = classify(api, UPSTREAM, commit, info["commit"]["committer"]["date"])
    try:
        existing = api(f"repos/{os.environ['GITHUB_REPOSITORY']}/releases/tags/{names['release_tag']}")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    else:
        if not existing["draft"]:
            return []
    return [{"tag": names["group"], "commit": commit, "branch": branch, **names}]


if __name__ == "__main__":
    rows = pending()
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("matrix=" + json.dumps({"include": rows}) + "\n")
        output.write("pending=" + str(bool(rows)).lower() + "\n")
    print(json.dumps(rows, indent=2))

