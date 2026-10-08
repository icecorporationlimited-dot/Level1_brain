from groq import Groq
import pymongo
from datetime import datetime
import json

# MongoDB
client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = client["vibeOS"]

#groq
groq_client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

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
