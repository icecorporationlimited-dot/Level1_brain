"""level1_brain.py — daily Trend Brain job (GitHub Actions). REAL SOURCES ONLY.

Fetches Reels-relevant signals from YouTube (music chart + top Shorts hashtags) into the
`trend_items` collection. Needs MONGODB_URI and YOUTUBE_API_KEY. No AI-written ideas.
"""
import logging
import os
import sys

import pymongo

from trends import store
from trends.sources import youtube

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trend_brain")


def main():
    yt_key = os.environ.get("YOUTUBE_API_KEY")
    if not yt_key:
        logger.error("YOUTUBE_API_KEY is not set — no real source available, nothing stored")
        return 1
    client = pymongo.MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=15000)
    try:
        client.admin.command("ping")
        db = client["vibeOS"]
        store.ensure_indexes(db)
        items = youtube.fetch(yt_key)
        if not items:
            logger.error("YouTube returned no usable trends (quota/key problem?)")
            return 1
        n = store.upsert_items(db, items)
        audio = sum(1 for i in items if i["kind"] == "audio")
        logger.info("Saved %s trends (%s audio, %s hashtags)", n, audio, n - audio)
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
