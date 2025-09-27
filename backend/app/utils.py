import json
import re
from typing import Any

def normalize_text(t: str) -> str:
    """Clean and normalize input claim text."""
    return " ".join(t.split()).strip().lower()

def clamp(x: float, a: float, b: float) -> float:
    """Clamp a number between a and b."""
    return max(a, min(b, x))

def safe_json_extract(s: str, default: Any) -> Any:
    """
    Try to parse strict JSON from an LLM string.
    If the LLM responds with extra text around the JSON, 
    extract the first {...} block.
    """
    try:
        return json.loads(s)
    except Exception:
        # Try to extract the first {...} block
        m = re.search(r'\{.*\}', s, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return default
# app/utils.py
import re
from typing import List

def extract_keywords(text: str, max_words: int = 6) -> str:
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    stop = {"the","and","a","of","to","in","for","on","with","is","it","this","that","are","be","an","as","by","from"}
    kws = [w for w in words if w not in stop]
    return " ".join(kws[:max_words]) or text.lower()

def number_to_ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20: suffix = "th"
    else: suffix = {1:"st",2:"nd",3:"rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def normalize_ordinals(text: str) -> str:
    # "44 president" -> "44th president" ; "president 44" -> "44th president"
    t = text
    # president <num>
    t = re.sub(r"\bpresident\s+(\d{1,3})\b", lambda m: f"{number_to_ordinal(int(m.group(1)))} president", t, flags=re.I)
    # <num> president
    t = re.sub(r"\b(\d{1,3})\s+president\b", lambda m: f"{number_to_ordinal(int(m.group(1)))} president", t, flags=re.I)
    return t

def canonical_hints(text: str) -> List[str]:
    t = text.lower()
    hints: List[str] = []
    if re.search(r"\bobama\b", t):
        hints += ["Barack Obama", "List of presidents of the United States"]
    if re.search(r"\b(\d+)(st|nd|rd|th)?\s+president\b", normalize_ordinals(t)):
        hints += ["List of presidents of the United States", "President of the United States"]
    if re.search(r"\bbleach\b", t):
        hints += ["Bleach", "Sodium hypochlorite", "Toxicity", "Chemical burn"]
    if re.search(r"\b(detox|toxins?)\b", t) and re.search(r"\bskin\b", t):
        hints += ["Skin whitening", "Chemical burn", "Dermatology"]
    if re.search(r"\b(election|vote|ballot|polling|register)\b", t):
        hints += ["Elections in the United States", "Voter registration in the United States"]
    # dedupe, keep order
    seen = set()
    out = []
    for h in hints:
        if h not in seen:
            out.append(h); seen.add(h)
    return out
