# backend/agents/orchestrator.py
from typing import Dict, Any, Optional

from .ingestor import IngestorAgent
from .query_expander import QueryExpanderAgent   # <-- your new expander file
from .retrievers.retriever_parallel import ParallelRetriever
from .reranker import RerankerAgent               # <-- your new reranker file
from .verifier import VerifierAgent
from .harm_scorer import HarmScorerAgent          # <-- your updated scorer file
from .action import ActionAgent


class Orchestrator:
    def __init__(self, max_evidence: int = 6):
        self.max_evidence = max_evidence

        self.ingestor = IngestorAgent()
        self.expander = QueryExpanderAgent()
        self.retriever = ParallelRetriever()
        self.reranker = RerankerAgent()
        self.verifier = VerifierAgent()
        self.scorer = HarmScorerAgent()
        self.action = ActionAgent()

    def run_pipeline(
        self,
        text: Optional[str] = None,
        url: Optional[str] = None,
        media_type: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        End-to-end pipeline:
        Ingest (text|url) -> QueryExpand -> ParallelRetrieve -> Rerank -> Verify -> Score -> Action
        """
        trace = []

        # -------------------- Ingest --------------------
        payload: Dict[str, Any] = {"text": text, "url": url, "media_type": media_type}
        p1 = self.ingestor.run(payload)
        claim_text = p1.get("claim_text", "") or ""
        context = p1.get("context", "")

        trace.append({
            "agent": "ingestor",
            "out": {"claim_text": claim_text, "has_context": bool(context)}
        })

        # Short-circuit if we somehow got nothing to analyze
        if not claim_text.strip():
            result = {
                "claim_text": "",
                "text": "",
                "factual_confidence": 0.5,
                "verifier_rationale": "No input provided or failed to ingest.",
                "evidence": [],
                "harm_score": 0,
                "action": "inform",
            }
            if debug:
                result["trace"] = trace
            return result

        # Carry forward minimal payload
        work = {"claim_text": claim_text, "context": context}

        # -------------------- Query Expansion --------------------
        p2 = self.expander.run(work)
        queries = p2.get("queries") or [claim_text]
        trace.append({
            "agent": "query_expander",
            "out": {"queries": queries[:3], "total_queries": len(queries)}
        })
        work.update({"queries": queries})

        # -------------------- Retrieval (parallel over sources) --------------------
        p3 = self.retriever.run(work)
        evidence = p3.get("evidence", []) or []
        trace.append({
            "agent": "parallel_retriever",
            "out": {"evidence_count": len(evidence)}
        })
        work.update({"evidence": evidence})

        # -------------------- Rerank (TF-IDF, keep best N) --------------------
        p4 = self.reranker.run(work)
        reranked = p4.get("evidence", [])[: self.max_evidence]
        trace.append({
            "agent": "reranker",
            "out": {"kept": len(reranked)}
        })
        work.update({"evidence": reranked})

        # -------------------- Verify (LLM if evidence, abstain if none) --------------------
        p5 = self.verifier.run(work)
        F = p5.get("factual_confidence")
        rationale = p5.get("verifier_rationale")
        trace.append({
            "agent": "verifier",
            "out": {"factual_confidence": F, "has_rationale": bool(rationale)}
        })
        work.update({"factual_confidence": F, "verifier_rationale": rationale})

        # -------------------- Harm Score (category-aware, breakdown) --------------------
        p6 = self.scorer.run(work)
        harm = int(p6.get("harm_score", 0))
        category = p6.get("category")
        breakdown = p6.get("harm_breakdown")
        action_tmp = p6.get("action")  # scorer may set it; action agent finalizes

        trace.append({
            "agent": "harm_scorer",
            "out": {"harm_score": harm, "category": category, "breakdown": breakdown}
        })
        work.update({
            "harm_score": harm,
            "category": category,
            "harm_breakdown": breakdown,
            "action": action_tmp
        })

        # -------------------- Action (inform/flag/alert) --------------------
        p7 = self.action.run(work)
        action = p7.get("action", "inform")
        trace.append({"agent": "action", "out": {"action": action}})

        # -------------------- Final payload --------------------
        final = {
            "claim_text": claim_text,
            "text": claim_text,  # keep for backward compat with existing schemas
            "evidence": reranked,
            "factual_confidence": F,
            "verifier_rationale": rationale,
            "harm_score": harm,
            "action": action,
            "category": category,
            "harm_breakdown": breakdown,
        }
        if debug:
            final["trace"] = trace
        return final
