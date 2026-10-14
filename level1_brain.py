"""level1_brain.py — daily Trend Brain job (GitHub Actions).

1. AI ideas   -> trend_items (source_type="ai_generated")   [needs GROQ_API_KEY]
2. YouTube    -> trend_items (source_type="sourced")        [needs YOUTUBE_API_KEY, optional]
3. Legacy doc -> `trends` collection, so the old bot code keeps working during rollout.
"""
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pymongo
from groq import Groq

from trends import store
from trends.sources import ai_ideas, youtube

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("level1_brain")
IST = ZoneInfo("Asia/Kolkata")


def main():
    client = pymongo.MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=15000)
    try:
        client.admin.command("ping")
        db = client["vibeOS"]
        store.ensure_indexes(db)

        audios, captions = ai_ideas.generate(Groq(api_key=os.environ["GROQ_API_KEY"]))
        n_ai = store.upsert_items(db, ai_ideas.to_items(audios, captions))

        n_src = 0
        yt_key = os.environ.get("YOUTUBE_API_KEY")
        if yt_key:
            n_src = store.upsert_items(db, youtube.fetch(yt_key))
        else:
            logger.warning("YOUTUBE_API_KEY not set — skipping sourced trends")

        today = datetime.now(IST).strftime("%Y-%m-%d")
        db["trends"].update_one(
            {"date": today},
            {"$set": {"date": today, "data": {"audios": audios, "captions": captions},
                      "created_at": datetime.now(IST)}},
            upsert=True)
        logger.info("Saved %s AI ideas, %s sourced trends for %s", n_ai, n_src, today)
    finally:
        client.close()


if __name__ == "__main__":
    main()
