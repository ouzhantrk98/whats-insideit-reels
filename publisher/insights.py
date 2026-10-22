"""Append a snapshot of every published Reel's metrics to insights.csv.

Metrics come from GET /<media-id>/insights (needs instagram_business_manage_insights). Meta
notes data can lag by up to 48 hours, so run this daily and compare snapshots over the week.

Environment: IG_ACCESS_TOKEN. Usage: python3 publisher/insights.py
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from publish import HERE, STATE, call, load

METRICS = [
    "views",
    "reach",
    "likes",
    "comments",
    "shares",
    "saved",
    "total_interactions",
    "ig_reels_avg_watch_time",
    "reels_skip_rate",
]
OUT = HERE / "insights.csv"


def main() -> None:
    state = load(STATE, {})
    if not state:
        sys.exit("nothing published yet")
    taken = datetime.now(timezone.utc).isoformat(timespec="minutes")
    new = not OUT.exists()
    with OUT.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["taken_at", "post_id", "media_id", *METRICS])
        if new:
            writer.writeheader()
        for post_id, info in state.items():
            data = call("GET", f"{info['media_id']}/insights", {"metric": ",".join(METRICS)}).get("data", [])
            values = {d["name"]: d["values"][0]["value"] if d.get("values") else d.get("total_value", {}).get("value") for d in data}
            writer.writerow({"taken_at": taken, "post_id": post_id, "media_id": info["media_id"], **values})
            print(json.dumps({"post": post_id, **values}))


if __name__ == "__main__":
    main()
