"""Name main and manual source builds by upstream commit date and SHA."""
import re

def classify(api, upstream, commit, date):
    stamp = date[:10].replace("-", "")
    if not re.fullmatch(r"\d{8}", stamp):
        raise ValueError("Invalid upstream commit date")
    short = commit[:8]
    identifier = f"nightly-{stamp}-{short}"
    return {"group": "nightly", "kind": "nightly", "distance": None,
            "date": date[:10], "release_tag": identifier,
            "archive": "l4d2-bridge-" + identifier + ".zip",
            "title": identifier}
