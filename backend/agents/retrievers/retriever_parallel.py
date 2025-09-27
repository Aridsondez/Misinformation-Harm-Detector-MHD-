# backend/agents/retrievers/retriever_parallel.py
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from ..base import Agent
from .retriever_wikipedia import WikipediaRetriever
from .retriever_news import NewsRetriever       # optional
from .retriever_websearch import WebSearchRetriever  # new
from .retriever_openalex import OpenAlexRetriever    # new


def _normalize_url(u: str) -> str:
    if not u:
        return ""
    try:
        p = urlparse(u)
        # strip utm_* params and fragments; lowercase host
        q = [(k, v) for (k, v) in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
        p2 = p._replace(netloc=p.netloc.lower(), query=urlencode(q, doseq=True), fragment="")
        return urlunparse(p2)
    except Exception:
        return u


class ParallelRetriever(Agent):
    name = "parallel_retriever"

    def __init__(self, per_future_timeout: float = 7.0, max_workers_cap: int = 8, per_source_cap: int = 8):
        self.per_future_timeout = per_future_timeout
        self.max_workers_cap = max_workers_cap
        self.per_source_cap = per_source_cap

        # Add the retrievers you want to run in parallel:
        self.retrievers = [WikipediaRetriever(), WebSearchRetriever(), OpenAlexRetriever()]
        try:
            self.retrievers.append(NewsRetriever())  # optional; requires NEWSAPI_KEY
        except Exception:
            # Keep going even if News retriever can't init
            pass

    def _submit(self, ex: ThreadPoolExecutor, claim: str, queries: List[str]):
        tasks = []
        for q in queries:
            for r in self.retrievers:
                # Important: pass the expanded query through
                fut = ex.submit(r.run, {"claim_text": claim, "query": q})
                rname = getattr(r, "name", r.__class__.__name__)
                tasks.append((fut, rname, q))
        return tasks

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        claim = payload.get("claim_text", "") or ""
        queries = payload.get("queries") or [claim]

        total_calls = max(1, len(self.retrievers) * len(queries))
        max_workers = min(self.max_workers_cap, total_calls)

        ev: List[Dict[str, Any]] = []
        errors: List[Tuple[str, str]] = []  # (retriever, error_type)
        per_source_counts: Dict[str, int] = {}

        if not claim.strip():
            return {"claim_text": claim, "evidence": [], "retrieval_stats": {
                "total_calls": 0, "per_source": {}, "errors": []
            }}

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            tasks = self._submit(ex, claim, queries)
            for fut, rname, q in tasks:
                try:
                    part = fut.result(timeout=self.per_future_timeout)
                    items = part.get("evidence", []) if isinstance(part, dict) else []
                    kept = 0
                    for e in items:
                        # ensure source + clean URL
                        e["source"] = e.get("source") or rname
                        if e.get("url"):
                            e["url"] = _normalize_url(e["url"])
                        ev.append(e)
                        kept += 1
                        if kept >= self.per_source_cap:
                            break
                    per_source_counts[rname] = per_source_counts.get(rname, 0) + kept
                except Exception as e:
                    errors.append((rname, type(e).__name__))

        # Deduplicate: by URL if present, else by (source,title,snippet[:80])
        seen = set()
        dedup: List[Dict[str, Any]] = []
        for e in ev:
            key = e.get("url") or f"{e.get('source','')}|{e.get('title','')}|{(e.get('snippet','') or '')[:80]}"
            if not key or key in seen:
                continue
            seen.add(key)
            dedup.append(e)

        return {
            "claim_text": claim,
            "evidence": dedup,  # let the Reranker trim to top-N
            "retrieval_stats": {
                "total_calls": total_calls,
                "max_workers": max_workers,
                "per_source": per_source_counts,
                "raw_items": len(ev),
                "dedup_items": len(dedup),
                "errors": errors,
                "queries_preview": queries[:3],
            }
        }
