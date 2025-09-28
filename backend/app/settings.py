# backend/app/settings.py
from dataclasses import dataclass

@dataclass(frozen=True)
class MHDSettings:
    # Retrieval / reranking
    max_evidence: int = 6
    tfidf_max_features: int = 8000
    tfidf_ngram_lo: int = 1
    tfidf_ngram_hi: int = 2
    min_cosine: float = 0.12         # evidence must meet this similarity to be kept
    abstain_cosine: float = 0.12     # if avg relevance below this => unknown (F=0.5)

    # Harm guardrails (health-first)
    unknown_harm_cap: int = 45       # cap harm when abstaining
    alert_floor_high_risk: int = 80  # floor harm for explicit dangerous instructions
    inform_cutoff: int = 40          # < 40 => inform
    alert_cutoff: int = 70           # > 70 => alert

    # YouTube ingestor
    sentence_max_words: int = 25

    # Trusted domains for health retrieval
    trusted_domains: tuple = ("cdc.gov", "who.int", "nih.gov", "nhs.uk")

SETTINGS = MHDSettings()
