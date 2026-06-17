"""
news_fetcher.py — Ingests RSS feeds and returns cleaned, deduplicated stories.
"""

import feedparser
import requests
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from sources import FEEDS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DailyBriefingBot/1.0; "
        "+https://github.com/your-org/daily-briefing)"
    )
}

MAX_AGE_HOURS = 36
MAX_STORIES_PER_FEED = 6


def _strip_html(raw: str) -> str:
    soup = BeautifulSoup(raw or "", "html.parser")
    return " ".join(soup.get_text().split())


def _story_id(title: str, source: str) -> str:
    key = f"{source}::{title}".lower()
    return hashlib.md5(key.encode()).hexdigest()


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _fetch_feed(source: dict) -> list[dict]:
    """Fetch and parse one RSS feed; raises on network/HTTP error."""
    max_age = source.get("max_age_hours", MAX_AGE_HOURS)
    cap = source.get("max_stories", MAX_STORIES_PER_FEED)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age)

    resp = requests.get(source["url"], headers=HEADERS, timeout=12)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)

    stories = []
    for entry in feed.entries[:cap]:
        title = _strip_html(getattr(entry, "title", "")).strip()
        if not title:
            continue

        published = _parse_date(entry)
        if published is None or published < cutoff:
            continue

        summary = _strip_html(
            getattr(entry, "summary", "") or getattr(entry, "description", "")
        )[:500]

        stories.append({
            "id":        _story_id(title, source["name"]),
            "title":     title,
            "summary":   summary,
            "source":    source["name"],
            "category":  source["category"],
            "url":       getattr(entry, "link", "") or "",
            "published": published.isoformat(),
        })

    return stories


def fetch_all_news() -> tuple[dict[str, list[dict]], list[str]]:
    """
    Fetch all configured feeds concurrently.
    Returns (stories_by_category, failed_source_names).
    Deduplicates within each category by story ID.
    """
    all_sources = [s for sources in FEEDS.values() for s in sources]
    category_buckets: dict[str, list[dict]] = {cat: [] for cat in FEEDS}
    failed: list[str] = []

    with ThreadPoolExecutor(max_workers=min(len(all_sources), 12)) as executor:
        future_to_src = {executor.submit(_fetch_feed, src): src for src in all_sources}
        for future in as_completed(future_to_src):
            src = future_to_src[future]
            try:
                stories = future.result()
                for story in stories:
                    category_buckets[story["category"]].append(story)
                logger.info("  %s → %d stories", src["name"], len(stories))
            except Exception as exc:
                logger.warning("Failed to fetch %s: %s", src["name"], exc)
                failed.append(src["name"])

    result: dict[str, list[dict]] = {}
    seen: set[str] = set()

    for category in FEEDS:
        sorted_stories = sorted(
            category_buckets[category],
            key=lambda s: s["published"],
            reverse=True,
        )
        deduped = []
        for story in sorted_stories:
            if story["id"] not in seen:
                seen.add(story["id"])
                deduped.append(story)
        result[category] = deduped[:8]
        logger.info("Category %s: %d stories", category, len(result[category]))

    return result, failed
