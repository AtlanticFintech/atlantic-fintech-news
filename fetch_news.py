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
    (
