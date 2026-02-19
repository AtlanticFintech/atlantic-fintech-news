import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def fetch_rss(url, max_items=8):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AtlanticFintechBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub = item.findtext("pubDate", "").strip()
            if title and link:
                items.append(f"Title: {title}\nURL: {link}\nDate: {pub}\nSummary: {desc[:200]}")
        return "\n\n".join(items)
    except Exception as e:
        return f"[Could not fetch {url}: {e}]"

# Global fintech RSS feeds
global_feeds = [
    "https://www.finextra.com/rss/headlines.aspx",
    "https://feeds.feedburner.com/Techcrunch",
    "https://www.pymnts.com/feed/",
]

# Canadian fintech / business feeds
canada_feeds = [
    "https://financialpost.com/feed",
    "https://betakit.com/feed/",
    "https://www.thestar.com/business.rss",
]

# Atlantic Canada / ecosystem
atlantic_feeds = [
    "https://betakit.com/feed/",
    "https://www.cbc.ca/cmlink/rss-business",
]

def collect(feeds, max_each=6):
    parts = []
    for url in feeds:
        parts.append(fetch_rss(url, max_each))
    return "\n\n---\n\n".join(parts)

global_news = collect(global_feeds)
canada_news = collect(canada_feeds)
atlantic_news = collect(atlantic_feeds)

all_raw = f"""
=== GLOBAL FINTECH / TECH NEWS ===
{global_news}

=== CANADIAN BUSINESS / FINTECH NEWS ===
{canada_news}

=== ATLANTIC CANADA / ECOSYSTEM NEWS ===
{atlantic_news}
"""

prompt = f"""You are a fintech news curator for Atlantic Fintech, a sector initiative growing the fintech ecosystem in Atlantic Canada (Nova Scotia, New Brunswick, PEI, Newfoundland & Labrador).

Atlantic Fintech covers: open banking, embedded finance, payments innovation, financial inclusion, fintech startups, credit unions, Canadian fintech regulation, ecosystem building, venture capital for fintech, and Atlantic Canadian tech companies.

Today is {date.today().strftime("%B %d, %Y")}.

From the articles below, create a daily briefing in this EXACT format:

## 🌍 Top 5 Global Fintech News

- **[Article Title](URL)** — *Source Name* — One sentence summary.

(repeat for 5 articles)

## 🍁 Top 5 Canadian Fintech News

- **[Article Title](URL)** — *Source Name* — One sentence summary.

(repeat for 5 articles — focus on Canadian payments, open banking, Canadian fintech companies, regulation)

## 🌊 Bonus: Relevant to Atlantic Fintech's Focus (1–3 articles)

- **[Article Title](URL)** — *Source Name* — One sentence summary.

(1-3 articles especially relevant to ecosystem building, financial inclusion, credit unions, embedded finance, Atlantic Canada startups)

Rules:
- Only use articles from the raw data below with real titles and URLs
- Do not repeat articles across sections
- Prioritize fintech-relevant content; if a feed has no fintech news, skip those articles
- If there are fewer than 5 relevant articles in a section, include what's available

Raw articles:

{all_raw}
"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)

briefing_text = message.content[0].text
today_str = date.today().isoformat()

output = {
    "date": today_str,
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "briefing": briefing_text
}

os.makedirs("data", exist_ok=True)
with open("data/latest.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Briefing generated for {today_str}")
print(briefing_text)
