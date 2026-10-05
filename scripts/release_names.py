"""Classify source revisions by the newest reachable Remix version tag."""
import re
import urllib.parse


def classify(api, upstream, commit, date):
    tags = []
    page = 1
    while True:
        batch = api(f"{upstream}/tags?per_page=100&page={page}")
        if not batch:
            break
        tags.extend(batch)
        page += 1
    def version(tag):
        match = re.fullmatch(r"remix-(\d+)\.(\d+)\.(\d+)", tag["name"])
        return tuple(map(int, match.groups())) if match else (-1, -1, -1)
    group, distance = "untagged", None
    for tag in sorted(tags, key=version, reverse=True):
        if version(tag)[0] < 0:
            continue
        if tag["commit"]["sha"] == commit:
            group, distance = tag["name"], 0
            break
        comparison = api(f"{upstream}/compare/{urllib.parse.quote(tag['name'], safe='')}...{commit}")
        if comparison["status"] in ("ahead", "identical"):
            group, distance = tag["name"], comparison["ahead_by"]
            break
    kind = "tag" if distance == 0 else "nightly"
    stamp = date[:10].replace("-", "")
    if not re.fullmatch(r"\d{8}", stamp):
        raise ValueError("Invalid upstream commit date")
    short = commit[:8]
    identifier = f"{group}-{kind}-{stamp}-{short}"
    return {"group": group, "kind": kind, "distance": distance,
            "date": date[:10], "release_tag": "bridge-" + identifier,
            "archive": "l4d2-bridge-" + identifier + ".zip",
            "title": f"[{group}] {'Tag 构建' if kind == 'tag' else 'Nightly'} · {date[:10]} · {short}"}
