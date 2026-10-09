import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import pymongo
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
MONGODB_URI = os.environ["MONGODB_URI"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# Connections
client = pymongo.MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=15000
)
db = client["vibeOS"]
trends_collection = db["trends"]

groq_client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-120b"
TODAY = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

PROMPT = """
Generate Instagram content ideas for a Gen-Z audience in India.

Return exactly valid JSON with these keys:
{
  "audios": [
    {
      "name": "audio name or search phrase",
      "vibe": "baddie, soft, funny, or cinematic",
      "use_case": "short suggested use-case"
    }
  ],
  "captions": [
    "short Instagram caption"
  ]
}

Requirements:
- Exactly 5 audio suggestions.
- Exactly 5 captions.
- Male and female aesthetic styles.
- Confident, stylish, Gen-Z-friendly ideas.
- Keep audio names or search phrases concise.
- Do not invent popularity statistics or claim an audio is verified
  as trending without evidence.
- These are suggestions, not verified live Instagram trends.
- Return JSON only.
"""


def main():
    # Fail early if MongoDB credentials or connection are incorrect.
    client.admin.command("ping")
    logger.info("MongoDB connected")

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON. Do not use Markdown."
            },
            {
                "role": "user",
                "content": PROMPT
            }
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    raw_result = response.choices[0].message.content

    if not raw_result:
        raise ValueError("Groq returned an empty response")

    result = json.loads(raw_result)

    audios = result.get("audios")
    captions = result.get("captions")

    if not isinstance(audios, list) or len(audios) != 5:
        raise ValueError("Expected exactly 5 audio suggestions")

    if not isinstance(captions, list) or len(captions) != 5:
        raise ValueError("Expected exactly 5 captions")

    document = {
        "date": TODAY,
        "data": {
            "audios": audios,
            "captions": captions
        },
        "created_at": datetime.now(ZoneInfo("Asia/Kolkata"))
    }

    # One document per India-local calendar date.
    trends_collection.update_one(
        {"date": TODAY},
        {"$set": document},
        upsert=True
    )

    logger.info("Level 1 Brain saved trends for %s", TODAY)
    logger.info("Audio suggestions: %s", len(audios))
    logger.info("Caption suggestions: %s", len(captions))


if __name__ == "__main__":
    try:
        main()
    finally:
        client.close()
