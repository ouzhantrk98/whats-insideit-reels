# whats.insideit — Reels

Videos and the publishing schedule for the Instagram account [@whats.insideit](https://www.instagram.com/whats.insideit/).

- `videos/` — finished Reels (1080×1920, H.264, AAC). Served by GitHub Pages so Instagram can fetch them.
- `publisher/posts.json` — schedule and captions. A post is only published when `"approved": true`.
- `publisher/publish.py` — publishes the next approved, due post (Instagram API with Instagram Login, v26.0).
- `publisher/insights.py` — appends a daily metrics snapshot to `publisher/insights.csv`.
- `.github/workflows/` — hourly publishing check and a daily insights run.

Secrets (`IG_USER_ID`, `IG_ACCESS_TOKEN`) live in the repository's Actions secrets; `PUBLIC_BASE_URL` is an Actions variable.
