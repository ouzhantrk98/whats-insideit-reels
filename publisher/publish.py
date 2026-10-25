"""Publish the next due Reel to Instagram (Instagram API with Instagram Login, v26.0).

Instagram fetches the video itself, so each file must be reachable at PUBLIC_BASE_URL/<file>
(for example GitHub Pages). Steps: create a REELS container, wait until it is FINISHED,
publish it, then record the media id and permalink in state.json.

Environment: IG_USER_ID, IG_ACCESS_TOKEN, PUBLIC_BASE_URL; DRY_RUN=1 prints instead of posting.
Usage: python3 publisher/publish.py            # publishes at most one due post
       python3 publisher/publish.py --check    # verifies the token and the publishing quota
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://graph.instagram.com/v26.0"
HERE = Path(__file__).resolve().parent
POSTS = HERE / "posts.json"
STATE = HERE / "state.json"


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"{name} is not set")
    return value


def call(method: str, path: str, params: dict) -> dict:
    params = {**params, "access_token": env("IG_ACCESS_TOKEN")}
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} failed: HTTP {e.code} {e.read().decode()[:500]}")


def load(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def check() -> None:
    me = call("GET", "me", {"fields": "user_id,username,account_type"})
    quota = call("GET", f"{env('IG_USER_ID')}/content_publishing_limit", {"fields": "quota_usage,config"})
    print(json.dumps({"account": me, "publishing_limit": quota}, indent=2))


def publish(post: dict) -> dict:
    user = env("IG_USER_ID")
    video_url = f"{env('PUBLIC_BASE_URL').rstrip('/')}/{post['file']}"
    if os.environ.get("DRY_RUN"):
        print(f"[dry run] would publish {post['id']} from {video_url}")
        return {}
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": post["caption"],
        "share_to_feed": "true",
        "thumb_offset": str(post.get("thumb_offset_ms", 0)),
    }
    # A designed cover image (e.g. covers/<id>.jpg) replaces the video frame on the grid.
    if post.get("cover"):
        params["cover_url"] = f"{env('PUBLIC_BASE_URL').rstrip('/')}/{post['cover']}"
    container = call("POST", f"{user}/media", params)["id"]
    # Meta suggests polling about once a minute; Reels usually finish within a few minutes.
    for _ in range(20):
        status = call("GET", container, {"fields": "status_code,status"})
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit(f"container {container} failed: {status}")
        time.sleep(30)
    else:
        sys.exit(f"container {container} not ready after 10 minutes")
    media = call("POST", f"{user}/media_publish", {"creation_id": container})["id"]
    info = call("GET", media, {"fields": "permalink,timestamp"})
    return {"media_id": media, "permalink": info.get("permalink"), "published_at": info.get("timestamp")}


def main() -> None:
    if "--check" in sys.argv:
        check()
        return
    posts = load(POSTS, [])
    state = load(STATE, {})
    now = datetime.now(timezone.utc)
    # Only posts the owner has approved ("approved": true in posts.json) are ever published.
    due = [
        p for p in posts
        if p.get("approved") and p["id"] not in state and datetime.fromisoformat(p["publish_at"]) <= now
    ]
    if not due:
        print("nothing due")
        return
    post = sorted(due, key=lambda p: p["publish_at"])[0]
    result = publish(post)
    if result:
        state[post["id"]] = result
        STATE.write_text(json.dumps(state, indent=2) + "\n")
        print(f"published {post['id']}: {result['permalink']}")


if __name__ == "__main__":
    main()
