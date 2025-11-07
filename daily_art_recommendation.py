import os
import datetime
import feedgenerator
import json
import re
from xml.etree import ElementTree as ET
from openai import OpenAI

# --- Setup ---
RSS_PATH = "index.xml"
FEED_URL = "https://laratliff-dev.github.io/daily-art-rss/daily_art_feed.xml"
MODEL = "gpt-5"    # Use GPT-5 (or gpt-4o-mini or gpt-4o, if needed)

# --- Generate artwork recommendation dynamically ---
BASE_PROMPT = """
You are an art historian and expert in global art history. 
Recommend one particularly interesting, game-changing, or historically significant artwork.
Rules:
- Do NOT repeat any artist or artwork from the list provided.

Include:
- Title of the artwork
- Artist name
- Year created
- A short paragraph explaining why it’s significant
- A public link to an image (Wikipedia Commons preferred)
- A creative prompt for making a derivative inspired artwork

Return JSON with keys: title, artist, year, image_url, description, derivative_prompt.
{
  "title": "Art Work Title",
  "artist": "Artist Name",
  "year": "YYYY",
  "image_url": "https://...",
  "description": "A short paragraph explaining why this artwork is exceptional.",
  "derivative_prompt": "A ChatGPT prompt to create a new derivative image."
}
"""

def get_recent_art(days=30):
    """Extract recently recommended art works from RSS feed (by title)."""
    if not os.path.exists(RSS_PATH):
        return []
    
    tree = ET.parse(RSS_FILE)
    root = tree.getroot()
    channel = root.find("channel")
    items = channel.findall("item")

    recent_titles = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

    for item in items:
        title = item.find("title").text if item.find("title") is not None else None
        pubdate = item.find("pubDate").text if item.find("pubDate") is not None else None

        if title and pubdate:
            try:
                parsed_date = datetime.datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S EST")
            except ValueError:
                parsed_date = None

            if not parsed_date or parsed_date >= cutoff_date:
                recent_titles.append(title)

    return recent_titles

def get_daily_art():
    """Fetch a fresh artwork recommendation, avoiding duplicates and handling malformed JSON."""
    recent_art = get_recent_art(30)
    history_context = "Artwork already recommended: " + ", ".join(recent_art)

    for attempt in range(3):  # up to 3 tries if bad JSON or duplicates
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": BASE_PROMPT},
                    {"role": "user", "content": history_context}
                ],
                response_format={"type": "json_object"}
            )

            art = response.choices[0].message.content.strip()
            if not art:
                print("⚠️ Empty response from API, retrying...")
                continue

            # Remove Markdown fences if present
            art = re.sub(r"^```(json)?|```$", "", art).strip()

            # Try parsing JSON
            artwork = json.loads(art)

#            full_title = f"{artwork['title']} - {artwork['artist']}"
            full_title = f"{artwork['title']} by {artwork['artist']} ({artwork['year']})"
            if full_title not in recent_art:
                return artwork
            else:
                print(f"⚠️ Duplicate detected ({full_title}), retrying...")

        except json.JSONDecodeError:
            print(f"⚠️ JSON parse error on attempt {attempt+1}. Raw content:\n{art}\nRetrying...")
            continue
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}, retrying...")

    raise RuntimeError("Could not generate valid artwork JSON after 3 attempts.")

def add_item_to_rss(artwork):
    """Insert a new <item> into the RSS feed."""
    if not os.path.exists(RSS_PATH):
        rss_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Daily Artwork Recommendations</title>
    <link>{FEED_URL}</link>
    <description>A daily exploration of influential artworks and creative inspiration.</description>
  </channel>
</rss>
"""
        with open(RSS_PATH, "w", encoding="utf-8") as f:
            f.write(rss_template)

    tree = ET.parse(RSS_PATH)
    root = tree.getroot()
    channel = root.find("channel")

    item = ET.Element("item")
    ET.SubElement(item, "title").text = f"{artwork['title']} by {artwork['artist']} ({artwork['year']})"
    ET.SubElement(item, "link").text = artwork["image_url"]
    ET.SubElement(item, "description").text = artwork["description"]
    ET.SubElement(item, "derivativePrompt").text = artwork["derivative_prompt"]
    ET.SubElement(item, "pubDate").text = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S EST")

    channel.insert(0, item)
    tree.write(RSS_PATH, encoding="utf-8", xml_declaration=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    artwork = get_daily_art()
    add_item_to_rss(artwork)
    print(f"✅ Added: {artwork['title']} by {artwork['artist']} ({artwork['year']})")

# response = client.chat.completions.create(
#     model=MODEL,
#     messages=[{"role": "system", "content": "You are a concise, authoritative art historian."},
#               {"role": "user", "content": BASE_PROMPT}],
#     response_format={"type": "json_object"}
# )
#
# art = response.choices[0].message.content
# import json
# art = json.loads(art)
#
## --- Build RSS feed ---
# feed = feedgenerator.Rss201rev2Feed(
#     title="Daily Art Recommendation",
#     link=FEED_URL,
#     description="A daily exploration of influential artworks and creative inspiration.",
#     language="en",
# )
#
# feed.add_item(
#     title=f"{art['title']} by {art['artist']} ({art['year']})",
#     link=art["image_url"],
#     description=f"""
#         <p><img src="{art['image_url']}" width="400"/></p>
#         <p><strong>{art['title']}</strong> ({art['year']}) by {art['artist']}.</p>
#         <p>{art['description']}</p>
#         <p><em>Derivative prompt:</em> {art['derivative_prompt']}</p>
#     """,
#     pubdate=datetime.datetime.now(),
# )
#
## --- Append to existing RSS if present ---
# if os.path.exists(RSS_PATH):
#     with open(RSS_PATH, "r", encoding="utf-8") as f:
#         old_content = f.read()
#     # naive approach: prepend new item
#     with open(RSS_PATH, "w", encoding="utf-8") as f:
#         feed.write(f, "utf-8")
#         f.write("\n" + old_content)
# else:
#     with open(RSS_PATH, "w", encoding="utf-8") as f:
#         feed.write(f, "utf-8")
#
# print(f"✅ Added: {art['title']} by {art['artist']} ({art['year']})")
