"""YouTube Data API v3 adapter (official). Most-popular videos in India.

Needs YOUTUBE_API_KEY. Without it the source is skipped, never faked.
Popularity here is *YouTube* popularity; it is stored as topic/audio evidence,
not as an Instagram trend, and audio rights stay unverified.
"""
import logging
import requests
from trends.schema import make_item, utcnow

log = logging.getLogger(__name__)
URL = "https://www.googleapis.com/youtube/v3/videos"
# (label, categoryId or None, kind)
FEEDS = [("popular", None, "topic"), ("music", "10", "audio")]


def _conf(rank, n):
    # rank 1 -> 0.85, last -> 0.45 (single source: never above 0.85)
    return 0.85 if n <= 1 else 0.85 - 0.4 * (rank - 1) / (n - 1)


def fetch(api_key, region="IN", per_feed=15, session=None):
    http = session or requests
    items, now = [], utcnow()
    for label, cat, kind in FEEDS:
        params = {"part": "snippet,statistics", "chart": "mostPopular",
                  "regionCode": region, "maxResults": per_feed, "key": api_key}
        if cat:
            params["videoCategoryId"] = cat
        try:
            r = http.get(URL, params=params, timeout=20)
            r.raise_for_status()
            vids = r.json().get("items", [])
        except Exception as exc:  # one failing feed must not kill the run
            log.warning("YouTube feed %s failed: %s", label, type(exc).__name__)
            continue
        for rank, v in enumerate(vids, start=1):
            sn, st = v.get("snippet", {}), v.get("statistics", {})
            try:
                items.append(make_item(
                    kind=kind, title=sn.get("title", ""),
                    source_type="sourced", source_name=f"youtube_{label}_{region}",
                    source_url=f"https://www.youtube.com/watch?v={v['id']}",
                    evidence={"rank": rank, "feed": label, "channel": sn.get("channelTitle"),
                              "views": int(st.get("viewCount", 0)),
                              "published_at": sn.get("publishedAt")},
                    ttl_hours=36, confidence=_conf(rank, len(vids)),
                    niche_tags=sn.get("tags", [])[:5], observed_at=now,
                    rights_note="YouTube popularity only; Instagram audio availability/licence not verified",
                ))
            except (ValueError, KeyError) as exc:
                log.debug("skip video: %s", exc)
    return items
