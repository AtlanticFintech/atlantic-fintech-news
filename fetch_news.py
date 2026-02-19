import os
import json
import requests
from datetime import datetime, date
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
NEWS_API_KEY = os.environ["NEWS_API_KEY"]

def fetch_news(query, language="en", page_size=10):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }
    r = requests.get(url, params=params)
    return r.json().get("articles", [])

def format_articles(articles):
    out = []
    for a in articles:
        out.append(f"Title: {a['title']}\nSource: {a['source']['name']}\nURL: {a['url']}\nDescription: {a.get('description','')}")
    return "\n\n".join(out)

# Fetch raw news
global_articles = fetch_news("fintech OR \"open banking\" OR \"embedded finance\" OR payments technology", page_size=20)
canada_articles = fetch_news("fintech Canada OR \"open banking Canada\" OR Canadian payments OR Canadian financial technology", page_size=15)
atlantic_articles = fetch_news("Atlantic Canada fintech OR Nova Scotia fintech OR New Brunswick fintech OR \"financial technology\" Canada ecosystem", page_size=10)

all_raw = f"""
=== GLOBAL FINTECH NEWS ===
{format_articles(global_articles)}

=== CANADIAN FINTECH NEWS ===
{format_articles(canada_articles)}

=== ATLANTIC CANADA / ECOSYSTEM NEWS ===
{format_articles(atlantic_articles)}
"""

prompt = f"""You are a fintech news curator for Atlantic Fintech, a sector initiative growing the fintech ecosystem in Atlantic Canada (Nova Scotia, New Brunswick, PEI, Newfoundland & Labrador). 

Atlantic Fintech covers these topics: open banking, embedded finance, payments innovation, financial inclusion, fintech startups, credit unions and financial cooperatives, Canadian fintech regulation, ecosystem building, venture capital for fintech, and Atlantic Canadian tech companies.

Today is {date.today().strftime("%B %d, %Y")}.

From the articles below, create a daily briefing with this exact structure:

## 🌍 Top 5 Global Fintech News

For each: bullet point with **[Article Title]** (hyperlinked with URL), Source Name, and 1-2 sentence summary.

## 🍁 Top 5 Canadian Fintech News

Same format. Prioritize news about Canadian open banking policy, Canadian payments, Canadian fintech companies, and regulatory developments.

## 🌊 Bonus: Relevant to Atlantic Fintech's Focus (1–3 articles)

Include 1-3 additional articles that are especially relevant to topics Atlantic Fintech covers: ecosystem building, financial inclusion, credit unions, embedded finance, Atlantic Canada startups, or any topics that would resonate with their LinkedIn and blog audience.

Use this format for each article:
- **[Title](URL)** — *Source* — Summary sentence.

If an article doesn't have a real URL or title, skip it. Prioritize recency and relevance. Do not repeat articles across sections.

Here are the raw articles to choose from:

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
