# backend/agents/ingestor_youtube.py
from typing import Dict, Any, List
from .base import Agent
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from app.settings import SETTINGS
import urllib.parse as urlparse
import requests
from bs4 import BeautifulSoup

def _yt_id_from_url(u: str) -> str:
    p = urlparse.urlparse(u)
    if "youtu.be" in p.netloc:
        return p.path.lstrip("/")
    qs = urlparse.parse_qs(p.query)
    return (qs.get("v") or [None])[0]

def _fetch_description(url: str) -> str:
    """Very light HTML scrape of the video description as a last resort."""
    try:
        html = requests.get(url, timeout=8).text
        soup = BeautifulSoup(html, "html.parser")
        # YouTube’s HTML is dynamic, but the og:description often contains decent text
        og = soup.find("meta", {"property": "og:description"})
        if og and og.get("content"):
            return og.get("content").strip()
    except Exception:
        pass
    return ""

class YouTubeIngestor(Agent):
    name = "youtube_ingestor"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = payload.get("url") or ""
        vid = _yt_id_from_url(url) or ""
        if not vid:
            return {"video_id": None, "transcript": [], "fallback_description": ""}

        # Try multiple transcript strategies
        sentences: List[Dict[str, Any]] = []
        have_transcript = False

        try:
            # 1) Try standard English (manual or auto)
            parts = YouTubeTranscriptApi.get_transcript(vid, languages=["en"])
            have_transcript = True
        except (TranscriptsDisabled, NoTranscriptFound):
            parts = None
        except Exception:
            parts = None

        if not have_transcript:
            # 2) Try listing all and picking any language, then translate to English
            try:
                listing = YouTubeTranscriptApi.list_transcripts(vid)
                # Prefer English if present
                try:
                    tr_en = listing.find_transcript(["en"])
                    parts = tr_en.fetch()
                    have_transcript = True
                except Exception:
                    # Try first available + translate to English
                    for tr in listing:
                        try:
                            tr_en = tr.translate("en")
                            parts = tr_en.fetch()
                            have_transcript = True
                            break
                        except Exception:
                            continue
            except Exception:
                pass

        # If we got transcript parts, chunk into sentence-ish segments
        if have_transcript and parts:
            buf = []
            buf_start = None
            max_words = SETTINGS.sentence_max_words

            def flush():
                if not buf:
                    return
                text = " ".join(buf).strip()
                if text:
                    sentences.append({"text": text, "start": float(buf_start or 0.0)})
                buf.clear()

            for seg in parts:
                t = seg.get("text", "").strip()
                if not t:
                    continue
                if not buf:
                    buf_start = seg.get("start", 0.0)
                buf.extend(t.split())
                if any(t.endswith(x) for x in (".", "!", "?")) or len(buf) >= max_words:
                    flush()
                    buf_start = None
            flush()

        # Fallback: use page description so we at least have some text to scan
        fallback_desc = ""
        if not sentences:
            fallback_desc = _fetch_description(url)
            if fallback_desc:
                # fake one “sentence” with start=0
                sentences = [{"text": fallback_desc, "start": 0.0}]

        return {
            "video_id": vid,
            "transcript": sentences,
            "has_transcript": have_transcript,
            "fallback_description": bool(fallback_desc)
        }
