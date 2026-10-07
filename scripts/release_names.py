"""Name immutable build instances by upstream, recipe, and Actions run."""
from datetime import datetime
import re

def classify(commit, date, recipe, run_id, attempt):
    datetime.fromisoformat(date.replace("Z", "+00:00"))
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid upstream SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", recipe):
        raise ValueError("Invalid recipe digest")
    if not re.fullmatch(r"[1-9][0-9]*", str(run_id)) or not re.fullmatch(r"[1-9][0-9]*", str(attempt)):
        raise ValueError("Build requires a positive Actions run ID and attempt")
    stamp = date[:10].replace("-", "")
    if not re.fullmatch(r"\d{8}", stamp):
        raise ValueError("Invalid upstream commit date")
    short = commit[:8]
    identifier = f"nightly-{stamp}-{short}-r{recipe[:12]}-b{run_id}.{attempt}"
    return {"group": "nightly", "kind": "nightly", "distance": None,
            "date": date[:10], "release_tag": identifier,
            "archive": "l4d2-bridge-" + identifier + ".zip",
            "update_archive": "l4d2-bridge-update-" + identifier + ".zip",
            "title": identifier}
