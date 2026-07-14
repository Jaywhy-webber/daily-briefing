"""
summariser.py — AI summaries via Ollama (local) or Groq (hosted).
"""

import logging
import os
import requests
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

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


def select_provider() -> str | None:
    if GROQ_API_KEY:
        return "groq"
    if check_ollama():
        return "ollama"
    return None


def _chat_ollama(prompt: str, max_tokens: int = 300) -> str:
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


def _chat_groq(prompt: str, max_tokens: int = 300) -> str:
    resp = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model":       GROQ_MODEL,
            "messages":    [{"role": "user", "content": prompt}],
            "max_tokens":  max_tokens,
            "temperature": 0.3,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _chat(prompt: str, provider: str, max_tokens: int = 300) -> str:
    if provider == "groq":
        return _chat_groq(prompt, max_tokens)
    return _chat_ollama(prompt, max_tokens)


def _headlines_text(stories: list[dict]) -> str:
    lines = []
    for i, s in enumerate(stories, 1):
        summary = f" — {s['summary']}" if s.get("summary") else ""
        lines.append(f"{i}. [{s['source']}] {s['title']}{summary}")
    return "\n".join(lines)


def generate_morning_briefing(news: dict[str, list[dict]], provider: str) -> str:
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
        return _chat(prompt, provider, max_tokens=300)
    except Exception as exc:
        logger.error("Morning briefing failed: %s", exc)
        return ""


def generate_category_digest(category: str, stories: list[dict], provider: str) -> str:
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
        return _chat(prompt, provider, max_tokens=200)
    except Exception as exc:
        logger.warning("Digest failed for %s: %s", category, exc)
        return ""


def generate_all_summaries(news: dict[str, list[dict]], provider: str) -> tuple[str, dict[str, str]]:
    """Run briefing first (largest prompt), then all digests concurrently."""
    briefing = generate_morning_briefing(news, provider)

    with ThreadPoolExecutor(max_workers=len(news)) as executor:
        digest_futures = {
            cat: executor.submit(generate_category_digest, cat, stories, provider)
            for cat, stories in news.items()
        }
    digests = {cat: f.result() for cat, f in digest_futures.items()}
    return briefing, digests
