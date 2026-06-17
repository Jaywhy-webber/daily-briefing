#!/usr/bin/env python3
"""
run_pipeline.py — Daily Briefing Pipeline Orchestrator

Fetches news + markets, generates local AI summaries via Ollama,
renders the HTML dashboard, and writes output/index.html.

Usage:
    python run_pipeline.py [--output-dir PATH] [--skip-ai] [--debug]
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

logger = logging.getLogger("pipeline")

# ── SGT helpers ───────────────────────────────────────────────────────────────
SGT = timezone(timedelta(hours=8))

def now_sgt() -> datetime:
    return datetime.now(SGT)


# ── Renderer ──────────────────────────────────────────────────────────────────
def render_html(
    *,
    news: dict,
    markets: dict,
    briefing: str,
    digests: dict,
    failed_sources: list[str],
    output_path: Path,
) -> None:
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    template = env.get_template("template.html")

    now = now_sgt()
    html = template.render(
        news=news,
        markets=markets,
        briefing=briefing,
        digests=digests,
        failed_sources=failed_sources,
        date=f"{now.strftime('%A')}, {now.day} {now.strftime('%B %Y')}",
        time=now.strftime("%H:%M"),
        datetime_generated=now.strftime("%Y-%m-%d %H:%M SGT"),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("Dashboard written → %s", output_path)


# ── JSON snapshot ─────────────────────────────────────────────────────────────
def save_snapshot(data: dict, output_dir: Path) -> None:
    snap_path = output_dir / "snapshot.json"
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Snapshot saved → %s", snap_path)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Daily Briefing Pipeline")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--skip-ai", action="store_true", help="Skip Ollama AI summaries")
    parser.add_argument("--debug", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    output_dir = Path(args.output_dir)

    # ── Step 1: Fetch news ─────────────────────────────────────────────────
    logger.info("═══ Step 1/3 · Fetching news feeds ═══")
    from news_fetcher import fetch_all_news
    news, failed_sources = fetch_all_news()
    total = sum(len(v) for v in news.values())
    logger.info("Total stories: %d  |  Failed sources: %d", total, len(failed_sources))

    # ── Step 2: Fetch markets ──────────────────────────────────────────────
    logger.info("═══ Step 2/3 · Fetching market data ═══")
    from market_fetcher import fetch_markets
    markets = fetch_markets()

    # ── Step 3: AI summaries ───────────────────────────────────────────────
    briefing = ""
    digests: dict[str, str] = {}

    if not args.skip_ai:
        from summariser import check_ollama, generate_all_summaries, OLLAMA_MODEL, OLLAMA_URL
        if check_ollama():
            logger.info("═══ Step 3/3 · Generating AI summaries (%s) ═══", OLLAMA_MODEL)
            briefing, digests = generate_all_summaries(news)
            logger.info("Briefing + %d digests generated", len(digests))
        else:
            logger.warning("Ollama not reachable at %s — skipping AI (run: ollama serve)", OLLAMA_URL)
    else:
        logger.info("═══ Step 3/3 · Skipping AI (--skip-ai) ═══")

    # ── Render ─────────────────────────────────────────────────────────────
    index_path = output_dir / "index.html"
    render_html(
        news=news,
        markets=markets,
        briefing=briefing,
        digests=digests,
        failed_sources=failed_sources,
        output_path=index_path,
    )

    # ── Archive dated copy ─────────────────────────────────────────────────
    now = now_sgt()
    archive_path = output_dir / f"{now.strftime('%Y-%m-%d')}.html"
    shutil.copy(index_path, archive_path)
    logger.info("Archive saved → %s", archive_path)

    save_snapshot(
        {"news": news, "markets": markets, "briefing": briefing, "digests": digests},
        output_dir,
    )

    logger.info("✓ Pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
