import os
import datetime
import json
import re
from xml.etree import ElementTree as ET
from openai import OpenAI

# --- Setup ---
RSS_PATH = "index.xml"
FEED_URL = "https://laratliff-dev.github.io/daily-art-rss/daily_art_feed.xml"
# MODEL = "gpt-5"    # Use GPT-5 (or gpt-4o-mini or gpt-4o, if needed)
MODEL = "gpt-5-mini" #"gpt-4.1-mini"

MAX_TOKENS = 400
TEMPERATURE = 1.3  # Higher temperature for more variability (default: 1.0)
TOP_P = 0.97       # Nucleus sampling for diverse outputs

# --- Generate artwork recommendation dynamically ---
BASE_PROMPT = """
System Prompt:
You are an art historian and expert in global art history.
You must only provide information that you can confirm with high confidence from well-established, widely documented artworks.
If the requested output cannot be produced without guessing or inventing details, you must decline using the format described below.

User Prompt:
Rules:
- Do NOT invent or guess any artwork, artist, title, year, or link.
- Only choose artworks that have a dedicated Wikipedia article, ensuring verifiable existence.
- If you cannot find any valid artwork that meets all constraints (e.g., due to previous exclusions), return: {"error": "no_valid_artwork_available"}
- Do NOT repeat any artwork or artist from the provided exclusion list.
  - (Assume the provided list is authoritative. If uncertain whether repetition occurs, err on the side of excluding.)
- For the image URL:
  - Prefer a recognized museum website URL only if it exists and is clearly associated with the artwork.
  - Alternatively a Wikimedia Commons URL only if it exists and is clearly associated with the artwork.
  - Secondary source from Wikipedia is an acceptable alternative.
  - If no valid museum, Wikimedia, or Wikipedia image exists, return "image_url": null (do NOT fabricate or approximate URLs).
- All information must be verifiable and historically accurate.
- If at any point confidence drops below 95%, return the error JSON above.

Include the following fields in the reponse:
- title: Exact artwork title as listed in Wikipedia.
- artist: Artist's full name.
- year: Year of creation (or range), only if historically verified.
- image_url: Valid URL from an authoritative source such as a musueum site, or null if unavailable.
- description: A short paragraph explaining the work’s historical significance.
- derivative_prompt: A detailed creative prompt for generating a derivative artwork.

Return JSON with keys: title, artist, year, image_url, description, derivative_prompt.
{
  "title": "Art Work Title",
  "artist": "Artist Name",
  "year": "YYYY",
  "image_url": "https://... or null",
  "description": "A short paragraph explaining why this artwork is exceptional.",
  "derivative_prompt": "A ChatGPT prompt to create a new derivative image."
}
"""

def get_recent_art(days=30):
    """Extract recently recommended art works from RSS feed (by title)."""
    if not os.path.exists(RSS_PATH):
        return []
    
    tree = ET.parse(RSS_PATH)
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
                    {
                        "role": "system", 
                        "content": f"{BASE_PROMPT}\n\n{history_context}"
                    },
                    {
                        "role": "user", 
                        "content": "Please recommend one artwork following the rules above."
                    }
                ],
                max_completion_tokens=MAX_TOKENS, #max_tokens=MAX_TOKENS,
                #temperature=TEMPERATURE, --> skip for gpt-5 reasoning model, not supported for anything other than 1
                #top_p=TOP_P, --> skip for gpt-5 reasoning model, not supported for anything other than 1
                response_format={"type": "json_object"}
            )

            art = response.choices[0].message.content.strip()
            if not art:
                print("⚠️ Empty response from API, retrying...")
                continue

            if "no_valid_artwork_available" in art:
                print("⚠️ No valid artwork available, retrying...")
                continue

            # Remove Markdown fences if present
            art = re.sub(r"^```(json)?|```$", "", art).strip()

            # Try parsing JSON
            artwork = json.loads(art)

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

    # Create item with proper structure
    item = ET.Element("item")
    
    # Title
    title = f"{artwork['title']} by {artwork['artist']} ({artwork['year']})"
    ET.SubElement(item, "title").text = title
    
    # Link to image
    ET.SubElement(item, "link").text = artwork["image_url"] or ""
    
    # GUID for unique identification (RSS compliance)
    guid = ET.SubElement(item, "guid")
    guid.text = f"{FEED_URL}#{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    guid.set("isPermaLink", "false")
    
    # Combined description with derivative prompt
    description_html = f"""<![CDATA[
<p>{artwork["description"]}</p>
<hr/>
<h3>Creative Derivative Prompt</h3>
<p><em>{artwork["derivative_prompt"]}</em></p>
]]>"""
    desc_elem = ET.SubElement(item, "description")
    desc_elem.text = description_html
    
    # Publication date in RFC-822 format with GMT
    pubdate = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    ET.SubElement(item, "pubDate").text = pubdate

    # Insert at the beginning of the feed
    channel.insert(0, item)
    
    # Pretty print the XML
    indent_xml(root)
    tree.write(RSS_PATH, encoding="utf-8", xml_declaration=True)

def indent_xml(elem, level=0):
    """Add proper indentation to XML for readability."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    artwork = get_daily_art()
    add_item_to_rss(artwork)
    print(f"✅ Added: {artwork['title']} by {artwork['artist']} ({artwork['year']})")
