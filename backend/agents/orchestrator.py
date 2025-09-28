# backend/agents/orchestrator.py
from typing import Dict, Any, Optional, List

from .ingestor_youtube import YouTubeIngestor          # NEW
from .claim_extractor import ClaimExtractor            # NEW
from .ingestor import IngestorAgent                    # legacy text-only fallback
from .query_expander import QueryExpanderAgent
from .retrievers.retriever_parallel import ParallelRetriever
from .reranker import RerankerAgent
from .verifier import VerifierAgent
from .harm_scorer import HarmScorerAgent
from .action import ActionAgent
from app.settings import SETTINGS


class Orchestrator:
    """
    Two modes:
      - URL (YouTube): extract transcript -> claims (with timestamps) -> run pipeline per claim -> list output
      - Text: treat as single claim -> run classic pipeline -> single output
    """
    def __init__(self):
        # Agents
        self.yt_ingestor = YouTubeIngestor()
        self.claim_extractor = ClaimExtractor()
        self.text_ingestor = IngestorAgent()   # existing
        self.expander = QueryExpanderAgent()
        self.retriever = ParallelRetriever()
        self.reranker = RerankerAgent()
        self.verifier = VerifierAgent()
        self.scorer = HarmScorerAgent()
        self.action = ActionAgent()

    # --------------------------- Public API ---------------------------

    def run_pipeline(
        self,
        text: Optional[str] = None,
        url: Optional[str] = None,
        media_type: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        if url:
            return self._run_youtube_pipeline(url=url, debug=debug)
        # fallback single-claim path for plain text
        return self._run_text_pipeline(text=text or "", media_type=media_type, debug=debug)

    # ------------------------ Internal: YouTube -----------------------

    def _run_youtube_pipeline(self, url: str, debug: bool) -> Dict[str, Any]:
        trace: List[Dict[str, Any]] = []

        # Ingest YouTube transcript
        p1 = self.yt_ingestor.run({"url": url})
        transcript = p1.get("transcript", [])
        video_id = p1.get("video_id")
        trace.append({"agent": "youtube_ingestor", "out": {"has_transcript": bool(transcript), "video_id": video_id}})

        # Extract claims with timestamps
        p2 = self.claim_extractor.run({"transcript": transcript})
        claims = p2.get("claim_candidates", [])
        trace.append({"agent": "claim_extractor", "out": {"claims_found": len(claims)}})

        results = []
        for c in claims:
            claim_text = c["claim_text"]
            start = c.get("start", 0.0)

            # Query expand
            qx = self.expander.run({"claim_text": claim_text})
            queries = qx.get("queries") or [claim_text]

            # Retrieve
            r = self.retriever.run({"claim_text": claim_text, "queries": queries})
            evidence = r.get("evidence", [])

            # Rerank (keeps & computes evidence_relevance)
            rr = self.reranker.run({"claim_text": claim_text, "evidence": evidence})
            kept = (rr.get("evidence") or [])[: SETTINGS.max_evidence]
            evidence_relevance = float(rr.get("evidence_relevance", 0.0))

            # Verify
            v = self.verifier.run({"claim_text": claim_text, "evidence": kept, "evidence_relevance": evidence_relevance})
            F = float(v.get("factual_confidence", 0.5))
            rationale = v.get("verifier_rationale", "")

            # Score
            s = self.scorer.run({"claim_text": claim_text, "evidence": kept, "factual_confidence": F, "evidence_relevance": evidence_relevance})
            harm = int(s.get("harm_score", 0))
            action = s.get("action", "inform")

            results.append({
                "claim_text": claim_text,
                "start": start,
                "evidence": kept,
                "evidence_relevance": evidence_relevance,
                "factual_confidence": F,
                "harm_score": harm,
                "action": action,
                "rationale": rationale
            })

        summary = {
            "max_harm": max((r["harm_score"] for r in results), default=0),
            "action": ("alert" if any(r["action"] == "alert" for r in results)
                       else "flag" if any(r["action"] == "flag" for r in results)
                       else "inform")
        }

        out = {"video_id": video_id, "claims": results, "summary": summary}
        if debug:
            out["trace"] = trace
        return out

    # ------------------------- Internal: Text -------------------------

    def _run_text_pipeline(self, text: str, media_type: Optional[str], debug: bool) -> Dict[str, Any]:
        trace: List[Dict[str, Any]] = []

        p1 = self.text_ingestor.run({"text": text, "media_type": media_type})
        claim_text = (p1.get("claim_text") or "").strip()
        trace.append({"agent": "ingestor", "out": {"claim_text": claim_text}})

        if not claim_text:
            res = {"claim_text": "", "text": "", "evidence": [], "factual_confidence": 0.5, "verifier_rationale": "No input", "harm_score": 0, "action": "inform"}
            if debug:
                res["trace"] = trace
            return res

        qx = self.expander.run({"claim_text": claim_text})
        queries = qx.get("queries") or [claim_text]
        trace.append({"agent": "query_expander", "out": {"queries": queries[:3], "total_queries": len(queries)}})

        r = self.retriever.run({"claim_text": claim_text, "queries": queries})
        evidence = r.get("evidence", [])
        trace.append({"agent": "parallel_retriever", "out": {"evidence_count": len(evidence)}})

        rr = self.reranker.run({"claim_text": claim_text, "evidence": evidence})
        kept = (rr.get("evidence") or [])[: SETTINGS.max_evidence]
        ev_rel = float(rr.get("evidence_relevance", 0.0))
        trace.append({"agent": "reranker", "out": {"kept": len(kept), "evidence_relevance": ev_rel}})

        v = self.verifier.run({"claim_text": claim_text, "evidence": kept, "evidence_relevance": ev_rel})
        F = float(v.get("factual_confidence", 0.5))
        rationale = v.get("verifier_rationale", "")
        trace.append({"agent": "verifier", "out": {"factual_confidence": F, "has_rationale": bool(rationale)}})

        s = self.scorer.run({"claim_text": claim_text, "evidence": kept, "factual_confidence": F, "evidence_relevance": ev_rel})
        harm = int(s.get("harm_score", 0))
        action = s.get("action", "inform")
        trace.append({"agent": "harm_scorer", "out": {"harm_score": harm}})

        final = {
            "claim_text": claim_text,
            "text": claim_text,
            "evidence": kept,
            "factual_confidence": F,
            "verifier_rationale": rationale,
            "harm_score": harm,
            "action": action
        }
        if debug:
            final["trace"] = trace
        return final
