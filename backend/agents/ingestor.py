# agents/ingestor_agent.py
import re, requests
from typing import Dict, Any
from .base import Agent

def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:2000]  # keep it short for downstream

def _extract_main_text_html(url: str) -> str:
    try:
        import lxml.html
        from readability import Document
        html = requests.get(url, timeout=10).text
        doc = Document(html)
        content = lxml.html.fromstring(doc.summary()).text_content()
        title = doc.short_title()
        return f"{title}\n\n{content}"
    except Exception:
        # fallback: plain text from body
        try:
            from bs4 import BeautifulSoup
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(" ")
        except Exception:
            return ""

def _extract_youtube_transcript(url: str) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
        import urllib.parse as u
        q = u.urlparse(url)
        vid = u.parse_qs(q.query).get("v", [None])[0]
        if not vid: return ""
        parts = YouTubeTranscriptApi.get_transcript(vid)
        return " ".join([p["text"] for p in parts])
    except Exception:
        return ""

class IngestorAgent(Agent):
    name = "ingestor"
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text")
        url  = payload.get("url")
        media_type = (payload.get("media_type") or "auto").lower()

        if url:
            txt = ""
            if media_type in ("youtube","auto") and "youtube.com" in url or "youtu.be" in url:
                txt = _extract_youtube_transcript(url)
            if not txt:
                txt = _extract_main_text_html(url)
            text = txt or text

        if not text:
            return {"claim_text": "", "context": ""}

        # crude “claim” condensation: first sentence or ~25 words
        claim = re.split(r"[\.!\?]\s", text.strip(), maxsplit=1)[0]
        if len(claim.split()) > 25:
            claim = " ".join(claim.split()[:25])
        return {"claim_text": _clean(claim), "context": _clean(text)}
