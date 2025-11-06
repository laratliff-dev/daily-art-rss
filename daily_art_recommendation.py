import os
import datetime
import feedgenerator
from openai import OpenAI

# --- Setup ---
RSS_PATH = "index.xml"
FEED_URL = "https://<YOUR_GITHUB_USERNAME>.github.io/<YOUR_REPO>/daily_art_feed.xml"
MODEL = "gpt-5"    # Use GPT-5 (or gpt-4o-mini or gpt-4o, if needed)

# --- Generate artwork recommendation dynamically ---
BASE_PROMPT = """
You are an art historian and expert in global art history. 
Recommend one particularly interesting, game-changing, or historically significant artwork.
Include:
- Title of the artwork
- Artist name
- Year created
- A short paragraph explaining why it’s significant
- A public link to an image (Wikipedia Commons preferred)
- A creative prompt for making a derivative inspired artwork

Return JSON with keys: title, artist, year, image_url, description, derivative_prompt.
"""

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "system", "content": "You are a concise, authoritative art historian."},
              {"role": "user", "content": BASE_PROMPT}],
    response_format={"type": "json_object"}
)

art = response.choices[0].message.content
import json
art = json.loads(art)

# --- Build RSS feed ---
feed = feedgenerator.Rss201rev2Feed(
    title="Daily Art Recommendation",
    link=FEED_URL,
    description="A daily exploration of influential artworks and creative inspiration.",
    language="en",
)

feed.add_item(
    title=f"{art['title']} by {art['artist']} ({art['year']})",
    link=art["image_url"],
    description=f"""
        <p><img src="{art['image_url']}" width="400"/></p>
        <p><strong>{art['title']}</strong> ({art['year']}) by {art['artist']}.</p>
        <p>{art['description']}</p>
        <p><em>Derivative prompt:</em> {art['derivative_prompt']}</p>
    """,
    pubdate=datetime.datetime.now(),
)

# --- Append to existing RSS if present ---
if os.path.exists(RSS_PATH):
    with open(RSS_PATH, "r", encoding="utf-8") as f:
        old_content = f.read()
    # naive approach: prepend new item
    with open(RSS_PATH, "w", encoding="utf-8") as f:
        feed.write(f, "utf-8")
        f.write("\n" + old_content)
else:
    with open(RSS_PATH, "w", encoding="utf-8") as f:
        feed.write(f, "utf-8")

print(f"✅ Added: {art['title']} by {art['artist']} ({art['year']})")
