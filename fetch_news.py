import os
import json
import requests
from datetime import datetime, date
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def fetch_hn_fintech(max_items=15):
    """Fetch fintech-related stories from Hacker News Algolia API"""
    try:
        results = []
        for query in ["fintech", "open banking", "payments", "banking"]:
            r = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "tags": "story", "hitsPerPage": 5},
                timeout=10
            )
            for hit in r.json().get("hits", []):
                title = hit.get("title", "")
                url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID')}")
                author = hit.get("author", "")
                points = hit.get("points", 0)
                if title:
                    results.append(f"Title: {title}\nURL: {url}\nSource: Hacker News\nPoints: {points}")
        print(f"HN: fetched {len(results)} stories")
        return "\n\n".join(results[:max_items])
    except Exception as e:
        print(f"HN error: {e}")
        return ""

def fetch_newsdata(query, country=None):
    """Fetch from NewsData.io free tier - no key needed for basic RSS endpoint"""
    try:
        params = {"q": query, "language": "en"}
        if country:
            params["country"] = country
        # Use their free RSS-style endpoint
        url = "https://newsdata.io/api/1/news"
        # Fall back to a reliable public API
        raise Exception("skip")
    except:
        return ""

def fetch_mediastack_free(query):
    """Use a free public news endpoint"""
    try:
        r = requests.get(
            "https://api.currentsapi.services/v1/search",
            params={"keywords": query, "language": "en"},
            timeout=10
        )
        articles = r.json().get("news", [])
        results = []
        for a in articles[:8]:
            results.append(f"Title: {a.get('title','')}\nURL: {a.get('url','')}\nSource: {a.get('author','Unknown')}\nDate: {a.get('published','')}")
        return "\n\n".join(results)
    except Exception as e:
        print(f"Currents error: {e}")
        return ""

def fetch_rss_direct(url, label, max_items=8):
    """Try fetching RSS with different headers"""
    import xml.etree.ElementTree as ET
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"{label}: status {r.status_code}, size {len(r.content)} bytes")
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()[:200]
            pub = item.findtext("pubDate", "").strip()
            source_el = item.find("source")
            source = source_el.text if source_el is not None else label
            if title and link:
                items.append(f"Title: {title}\nURL: {link}\nSource: {source}\nDate: {pub}\nSummary: {desc}")
        print(f"{label}: parsed {len(items)} items")
        return "\n\n".join(items)
    except Exception as e:
        print(f"{label} error: {e}")
        return ""

# Collect from multiple reliable sources
print("Fetching news...")

global_news = fetch_hn_fintech(15)

# Try reliable RSS feeds
feeds = [
    ("https://feeds.reuters.com/reuters/businessNews", "Reuters Business"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml", "BBC Business"),
    ("https://rss.cbc.ca/lineup/business.xml", "CBC Business"),
    ("https://financialpost.com/feed", "Financial Post"),
    ("https://betakit.com/feed/", "BetaKit"),
]

feed_results = []
for url, label in feeds:
    result = fetch_rss_direct(url, label)
    if result:
        feed_results.append(f"=== {label} ===\n{result}")

all_feeds = "\n\n".join(feed_results)

all_raw = f"""
=== GLOBAL FINTECH / TECH NEWS (Hacker News) ===
{global_news}

=== NEWS FEEDS ===
{all_feeds if all_feeds else "[No feed content retrieved]"}
"""

print(f"\nTotal content length: {len(all_raw)} characters")
print("Sample:", all_raw[:500])

prompt = f"""You are a fintech news curator for Atlantic Fintech, growing the fintech ecosystem in Atlantic Canada (Nova Scotia, New Brunswick, PEI, Newfoundland & Labrador).

Atlantic Fintech covers: open banking, embedded finance, payments innovation, financial inclusion, fintech startups, credit unions, Canadian fintech regulation, ecosystem building, venture capital for fintech, and Atlantic Canadian tech companies.

Today is {date.today().strftime("%B %d, %Y")}.

Using the articles provided below, create a daily briefing in this EXACT format:

## 🌍 Top 5 Global Fintech News

- **[Article Title](URL)** — *Source* — One sentence summary.

## 🍁 Top 5 Canadian Fintech News

- **[Article Title](URL)** — *Source* — One sentence summary.

## 🌊 Bonus: Relevant to Atlantic Fintech's Focus (1–3 articles)

- **[Article Title](URL)** — *Source* — One sentence summary.

IMPORTANT: Use only articles from the data below with real titles and URLs. If there are not enough Canadian-specific articles, draw from the global pool and note relevance to Canada. Do not make up articles or URLs.

{all_raw}
"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)

briefing_text = message.content[0].text
today_str = date.today().isoformat()

# Add timestamp to force git to see a change
output = {
    "date": today_str,
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "run_id": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
    "briefing": briefing_text
}

os.makedirs("data", exist_ok=True)
with open("data/latest.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Briefing generated for {today_str}")
print(briefing_text)
