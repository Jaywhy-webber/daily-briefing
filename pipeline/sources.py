"""
Feed sources configuration for the daily briefing pipeline.
"""

FEEDS = {
    "singapore": [
        {
            "name": "Channel NewsAsia",
            "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416",
            "category": "singapore",
        },
        {
            "name": "The Straits Times",
            "url": "https://www.straitstimes.com/news/singapore/rss.xml",
            "category": "singapore",
        },
        {
            "name": "Today Online",
            "url": "https://www.todayonline.com/rss",
            "category": "singapore",
        },
    ],
    "us": [
        {
            "name": "NPR",
            "url": "https://feeds.npr.org/1001/rss.xml",
            "category": "us",
        },
        {
            "name": "AP News",
            "url": "https://feeds.apnews.com/rss/apf-topnews",
            "category": "us",
        },
        {
            "name": "Reuters",
            "url": "https://feeds.reuters.com/reuters/topNews",
            "category": "us",
        },
        {
            "name": "The Hill",
            "url": "https://thehill.com/feed/",
            "category": "us",
        },
    ],
    "asia": [
        {
            "name": "CNA Asia",
            "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
            "category": "asia",
        },
        {
            "name": "South China Morning Post",
            "url": "https://www.scmp.com/rss/91/feed",
            "category": "asia",
        },
        {
            "name": "The Hindu",
            "url": "https://www.thehindu.com/news/international/?service=rss",
            "category": "asia",
        },
        {
            "name": "Bangkok Post",
            "url": "https://www.bangkokpost.com/rss/data/topstories.xml",
            "category": "asia",
        },
    ],
    "others": [
        {
            "name": "BBC World",
            "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "category": "others",
        },
        {
            "name": "Al Jazeera",
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "category": "others",
            "max_stories": 3,
        },
        {
            "name": "The Guardian",
            "url": "https://www.theguardian.com/world/rss",
            "category": "others",
        },
        {
            "name": "Deutsche Welle",
            "url": "https://rss.dw.com/rdf/rss-en-world",
            "category": "others",
        },
    ],
    "tech": [
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/index",
            "category": "tech",
        },
        {
            "name": "The Verge",
            "url": "https://www.theverge.com/rss/index.xml",
            "category": "tech",
        },
        {
            "name": "Hacker News (Top)",
            "url": "https://hnrss.org/frontpage?count=15",
            "category": "tech",
        },
        {
            "name": "MIT Tech Review",
            "url": "https://www.technologyreview.com/feed/",
            "category": "tech",
        },
        {
            "name": "The Economist (Tech)",
            "url": "https://www.economist.com/science-and-technology/rss.xml",
            "category": "tech",
        },
    ],
    "economist": [
        # Subscriber RSS: log in at economist.com → My Account → RSS feeds
        # Replace each URL below with your personal subscriber feed URL for full-text access
        {
            "name": "Leaders",
            "url": "https://www.economist.com/leaders/rss.xml",
            "category": "economist",
            "max_age_hours": 168,
        },
        {
            "name": "Briefing",
            "url": "https://www.economist.com/briefing/rss.xml",
            "category": "economist",
            "max_age_hours": 168,
        },
        {
            "name": "Finance",
            "url": "https://www.economist.com/finance-and-economics/rss.xml",
            "category": "economist",
            "max_age_hours": 168,
        },
        {
            "name": "Business",
            "url": "https://www.economist.com/business/rss.xml",
            "category": "economist",
            "max_age_hours": 168,
        },
        {
            "name": "Asia",
            "url": "https://www.economist.com/asia/rss.xml",
            "category": "economist",
            "max_age_hours": 168,
        },
        {
            "name": "International",
            "url": "https://www.economist.com/international/rss.xml",
            "category": "economist",
            "max_age_hours": 168,
        },
    ],
}

# Financial tickers to track
MARKET_TICKERS = {
    "indices": [
        {"symbol": "^STI",   "label": "STI",        "currency": "SGD"},
        {"symbol": "^GSPC",  "label": "S&P 500",    "currency": "USD"},
        {"symbol": "^HSI",   "label": "Hang Seng",  "currency": "HKD"},
        {"symbol": "^N225",  "label": "Nikkei 225", "currency": "JPY"},
        {"symbol": "^FTSE",  "label": "FTSE 100",   "currency": "GBP"},
        {"symbol": "^AXJO",  "label": "ASX 200",    "currency": "AUD"},
    ],
    "fx": [
        {"symbol": "USDSGD=X", "label": "USD/SGD"},
        {"symbol": "EURSGD=X", "label": "EUR/SGD"},
        {"symbol": "GBPSGD=X", "label": "GBP/SGD"},
        {"symbol": "JPYSGD=X", "label": "JPY/SGD"},
        {"symbol": "CNYSGD=X", "label": "CNY/SGD"},
    ],
    "commodities": [
        {"symbol": "BZ=F",  "label": "Brent Crude", "unit": "USD/bbl"},
        {"symbol": "GC=F",  "label": "Gold",         "unit": "USD/oz"},
        {"symbol": "SI=F",  "label": "Silver",       "unit": "USD/oz"},
        {"symbol": "NG=F",  "label": "Nat. Gas",     "unit": "USD/MMBtu"},
    ],
    "crypto": [
        {"symbol": "BTC-USD", "label": "Bitcoin",  "unit": "USD"},
        {"symbol": "ETH-USD", "label": "Ethereum", "unit": "USD"},
    ],
}
