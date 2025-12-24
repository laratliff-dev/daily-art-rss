# Daily Art RSS Feed

An automated RSS feed that generates daily artwork recommendations using OpenAI's GPT models. Each entry features a historically significant artwork with detailed information and a creative prompt for generating derivative images.

## Features

- 🎨 **Daily Artwork Recommendations**: Automatically selects historically significant artworks with dedicated Wikipedia articles
- 📚 **Detailed Information**: Includes artist name, creation year, and historical significance
- 🖼️ **Image Links**: Direct links to Wikimedia Commons or Wikipedia images when available
- ✨ **Creative Prompts**: Each artwork includes a derivative prompt for AI image generation
- 🔄 **Duplicate Prevention**: Tracks recent recommendations to avoid repetition within 30 days
- 📡 **RSS 2.0 Compliant**: Standards-compliant feed format with proper GUID and date formatting

## How It Works

The script uses OpenAI's GPT models to:
1. Generate artwork recommendations from verifiable sources (Wikipedia/Wikimedia)
2. Ensure no artwork is repeated within a 30-day window
3. Include rich descriptions of historical significance
4. Provide creative prompts for generating derivative artwork
5. Format everything as a valid RSS 2.0 feed

## RSS Feed Structure

Each feed item includes:
- **Title**: Artwork title, artist, and year
- **Link**: Direct link to the artwork image
- **GUID**: Unique identifier for the entry
- **Description**: Historical context and significance
- **Creative Derivative Prompt**: AI prompt for generating inspired artwork
- **Publication Date**: GMT timestamp

## Setup

### Prerequisites

- Python 3.7+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/laratliff-dev/daily-art-rss.git
cd daily-art-rss
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

### Usage

Run the script to generate a new artwork recommendation:
```bash
python daily_art_recommendation.py
```

The script will:
- Generate a new artwork recommendation
- Add it to `index.xml`
- Avoid duplicating any artwork from the past 30 days

### Automation

To run daily, set up a scheduled task:

**Windows (Task Scheduler)**:
```powershell
# Create a scheduled task to run daily
schtasks /create /tn "DailyArtRSS" /tr "python C:\path\to\daily_art_recommendation.py" /sc daily /st 09:00
```

**Linux/Mac (Cron)**:
```bash
# Add to crontab (runs daily at 9:00 AM)
0 9 * * * cd /path/to/daily-art-rss && python daily_art_recommendation.py
```

**GitHub Actions** (included in repo):
- Automatically runs daily via scheduled workflow
- Commits updated RSS feed to the repository

## Configuration

Edit `daily_art_recommendation.py` to customize:

- `MODEL`: Change the OpenAI model (default: `gpt-4o-mini`)
- `RSS_PATH`: Output file path (default: `index.xml`)
- `FEED_URL`: Your RSS feed URL
- `days` parameter in `get_recent_art()`: Duplicate prevention window (default: 30 days)

## RSS Feed URL

Once deployed, subscribe to the feed at:
```
https://laratliff-dev.github.io/daily-art-rss/index.xml
```

## Example Output

```xml
<item>
  <title>The Starry Night by Vincent van Gogh (1889)</title>
  <link>https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night.jpg</link>
  <guid isPermaLink="false">https://...#20251224120000</guid>
  <description><![CDATA[
    <p>The Starry Night is one of Vincent van Gogh's most famous works...</p>
    <hr/>
    <h3>Creative Derivative Prompt</h3>
    <p><em>Create a night scene painting inspired by Vincent van Gogh's style...</em></p>
  ]]></description>
  <pubDate>Tue, 24 Dec 2025 12:00:00 GMT</pubDate>
</item>
```

## Dependencies

- `openai>=1.0.0`: OpenAI API client

All other imports (`os`, `datetime`, `json`, `re`, `xml.etree`) are from Python's standard library.

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
