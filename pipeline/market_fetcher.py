"""
market_fetcher.py — Pulls live market data via Yahoo Finance API directly.
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from sources import MARKET_TICKERS

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DailyBriefingBot/1.0)"}
YF_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def _fmt_price(val: float, decimals: int = 2) -> str:
    if val is None:
        return "—"
    if val >= 10_000:
        return f"{val:,.0f}"
    if val >= 1_000:
        return f"{val:,.1f}"
    return f"{val:.{decimals}f}"


def _pct_change(current: float, previous: float) -> Optional[float]:
    if previous and previous != 0:
        return ((current - previous) / abs(previous)) * 100
    return None


def _fetch_ticker(symbol: str) -> Optional[dict]:
    try:
        r = requests.get(
            YF_URL.format(symbol=symbol),
            params={"range": "5d", "interval": "1d"},
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()["chart"]["result"]
        if not result:
            return None

        meta = result[0]["meta"]
        raw_closes = result[0]["indicators"]["quote"][0].get("close", [])
        closes = [c for c in raw_closes if c is not None]
        if not closes:
            return None

        price = closes[-1]
        prev = closes[-2] if len(closes) >= 2 else meta.get("chartPreviousClose")
        change_pct = _pct_change(price, prev) if prev else None

        return {
            "symbol":     symbol,
            "price":      price,
            "prev_close": prev,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "direction":  (
                "up"   if change_pct and change_pct > 0 else
                "down" if change_pct and change_pct < 0 else
                "flat"
            ),
            "price_fmt":  _fmt_price(price),
        }
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", symbol, exc)
        return None


def fetch_markets() -> dict:
    """Fetch all configured market tickers concurrently."""
    all_configs = [
        (group, cfg)
        for group, tickers in MARKET_TICKERS.items()
        for cfg in tickers
    ]
    symbols = [cfg["symbol"] for _, cfg in all_configs]

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_fetch_ticker, symbols))

    markets: dict = {group: [] for group in MARKET_TICKERS}
    for (group, ticker_cfg), data in zip(all_configs, results):
        if data:
            entry = {**ticker_cfg, **data}
            sign = "+" if entry.get("change_pct") and entry["change_pct"] > 0 else ""
            entry["change_str"] = (
                f"{sign}{entry['change_pct']:.2f}%"
                if entry.get("change_pct") is not None
                else "—"
            )
        else:
            entry = {**ticker_cfg, "price_fmt": "—", "change_str": "—", "direction": "flat"}
        markets[group].append(entry)

    for group in MARKET_TICKERS:
        ok = sum(1 for e in markets[group] if e.get("price"))
        logger.info("Markets/%s: %d/%d tickers", group, ok, len(markets[group]))

    return markets
