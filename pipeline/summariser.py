"""
summariser.py — Local AI summaries via Ollama.
"""

import logging
import os
import requests
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

_LABEL_MAP = {
    "singapore": "Singapore local news",
    "us":        "United States news and politics",
    "asia":      "Asia-Pacific news",
    "others":    "European, Middle Eastern, and international news",
    "tech":      "technology and innovation",
    "economist": "The Economist's analysis and long-read journalism",
}


def check_ollama() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def _chat(prompt: str, max_tokens: int = 300) -> str:
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model":  OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.3},
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def _headlines_text(stories: list[dict]) -> str:
    lines = []
    for i, s in enumerate(stories, 1):
        summary = f" — {s['summary']}" if s.get("summary") else ""
        lines.append(f"{i}. [{s['source']}] {s['title']}{summary}")
    return "\n".join(lines)


def generate_morning_briefing(news: dict[str, list[dict]]) -> str:
    all_headlines = []
    for stories in news.values():
        all_headlines.extend(stories[:4])

    prompt = (
        "You are an elite briefing writer for a Singapore-based executive audience. "
        "Based on the following headlines from today, write a concise morning briefing "
        "of exactly 3-4 sentences. Cover the most significant global, Singapore, "
        "financial, and technology developments. Be specific - name indices, figures, "
        "or key actors where relevant. Write in a confident, neutral, editorial voice. "
        "No bullet points. No headings. Plain prose only. Output the briefing text only, "
        "no preamble.\n\n"
        f"HEADLINES:\n{_headlines_text(all_headlines)}\n\nMORNING BRIEFING:"
    )

    try:
        return _chat(prompt, max_tokens=300)
    except Exception as exc:
        logger.error("Morning briefing failed: %s", exc)
        return ""


def generate_category_digest(category: str, stories: list[dict]) -> str:
    if not stories:
        return ""

    label = _LABEL_MAP.get(category, category)
    prompt = (
        f"Summarise the key themes from the following {label} headlines in 2-3 sentences. "
        "Be specific and analytical. No fluff. No bullet points. Plain prose only. "
        "Output the digest text only, no preamble.\n\n"
        f"HEADLINES:\n{_headlines_text(stories)}\n\nDIGEST:"
    )

    try:
        return _chat(prompt, max_tokens=200)
    except Exception as exc:
        logger.warning("Digest failed for %s: %s", category, exc)
        return ""


def generate_all_summaries(news: dict[str, list[dict]]) -> tuple[str, dict[str, str]]:
    """Run briefing first (largest prompt), then all digests concurrently."""
    briefing = generate_morning_briefing(news)

    with ThreadPoolExecutor(max_workers=len(news)) as executor:
        digest_futures = {
            cat: executor.submit(generate_category_digest, cat, stories)
            for cat, stories in news.items()
        }
    digests = {cat: f.result() for cat, f in digest_futures.items()}
    return briefing, digests
