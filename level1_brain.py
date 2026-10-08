from groq import Groq
import pymongo
from datetime import datetime
import json

# MongoDB
client = pymongo.MongoClient("mongodb://vibeossupport_db_user:T5MgK81nVoZk50bc@ac-kryc93r-shard-00-00.ibuc0rv.mongodb.net:27017,ac-kryc93r-shard-00-01.ibuc0rv.mongodb.net:27017,ac-kryc93r-shard-00-02.ibuc0rv.mongodb.net:27017/?ssl=true&replicaSet=atlas-fmry30-shard-0&authSource=admin&appName=Cluster0")
db = client["vibeOS"]

# Groq
groq_client = Groq(api_key="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")

prompt = """
Generate content for Instagram trends in India.

I need:
- 5 currently popular/trending Instagram audio names
- 5 Gen-Z captions

Style:
- Male / Female aesthetic
- Confident
- Stylish
- Gen-Z
- Suitable for Instagram Reels

Return ONLY valid JSON in this format:

{
  "audios": ["...", "...", "...", "...", "..."],
  "captions": ["...", "...", "...", "...", "..."]
}
"""

response = groq_client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.8
)

result = response.choices[0].message.content

print(result)

# MongoDB me save
db.trends.insert_one({
    "date": datetime.now().strftime("%Y-%m-%d"),
    "data": result,
    "created_at": datetime.now()
})

print("Level 1 Brain Saved!")