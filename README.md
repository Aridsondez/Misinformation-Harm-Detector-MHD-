# YouTube Health-Misinformation Detector (YT-HMD)
### Tagline

### Find and flag dangerous health advice in YouTube videos—fast, explainable, and grounded in trusted sources.

## 🚀 Overview

We focus on one high-impact workflow: given a YouTube URL, we extract the transcript, detect health advice claims (e.g., “drink X”, “this cures Y”), retrieve evidence from trusted health sources (CDC, WHO, NIH/NHS) + open research (OpenAlex), verify support/contradiction, and output a verdict with citations and timestamps.

Why this scope? YouTube has transcripts (easy ingest), health misinformation is high-risk, and there are clear, trustworthy sources—so we can be accurate, fast, and auditable.

## 🎯 Scope
- What we’re building (MVP)

- YouTube-only backend pipeline (FastAPI)

- Claim extraction from transcripts with timestamps

- Trusted-only retrieval (site-limited health orgs) + OpenAlex

- Evidence re-ranking & relevance filtering

- Verifier (rule-first, LLM optional) → factual_confidence (F)

- Health-tuned Harm Scorer → inform / flag / alert

- React frontend to visualize per-claim verdicts over time

- Not included (for MVP)

- Crawling other platforms

- General open-web fact-checking

- Legal/defamation adjudication

- Stretch goals

- Optional LLM reasoning to summarize multi-snippet evidence

- Caching & batched evaluation on a labeled set

- Simple browser extension mock (overlay markers at timestamps)

## 🧠 Decision & Scoring

Verifier (F in [0,1])

If no relevant evidence → abstain: F = 0.5 (“unknown”).

If trusted evidence contradicts (e.g., “do NOT ingest bleach”) → F ≈ 0.0–0.3.

If trusted evidence supports (e.g., “recommended by CDC/NHS”) → F ≈ 0.7–0.95.

Harm Scorer (health-tuned guardrails)

Unknown (abstain) never spikes: harm is capped ≤ 45.

Explicit dangerous advice (ingest/inject/dosage) + low F → force alert ≥ 80.

Otherwise logistic mapping over (1 − F) with gentle curvature.

Actions

0–39 → Inform

40–70 → Flag

71–100 → Alert

🛠️ Tech Stack

## Backend

Python 3.11, FastAPI

Agents: YouTube ingestor, claim extractor, site-limited retriever(s), reranker, verifier, harm scorer, action

(Optional) Postgres to persist results

Frontend

React + Vite + Tailwind

APIs

youtube_transcript_api (transcripts)

Trusted web search (site-limited to cdc.gov, who.int, nih.gov, nhs.uk) via your search provider

OpenAlex (paper abstracts)

Infra

Docker Compose

Note: We removed ADK/A2A/Redis/FAISS for MVP simplicity.

## 🏗️ Architecture (YouTube-only)

YouTube URL → Ingest transcript → Extract health claims (+timestamps) → Expand queries → Retrieve (trusted only) → Rerank & filter (min cosine) → Verify (rule-first, LLM optional) → Score harm → Action + Explain

Agents:

YouTubeIngestor → sentences with start time

ClaimExtractor → health advice candidates

QueryExpander → mechanism-aware queries (e.g., dosage/safety/guidelines)

ParallelRetriever → TrustedWebRetriever, OpenAlexRetriever

Reranker → TF-IDF cosine, evidence_relevance

VerifierHealth → sets F, rationale

HarmScorerHealth → harm + action

Action → final inform/flag/alert

## 📡 API
POST /analyze

Body:

{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }


Response:

{
  "video_id": "VIDEO_ID",
  "claims": [
    {
      "claim_text": "Drink bleach to detox your body",
      "start": 152.3,
      "evidence": [
        {"source":"cdc","title":"...", "url":"...", "snippet":"..."}
      ],
      "evidence_relevance": 0.78,
      "factual_confidence": 0.12,
      "harm_score": 92,
      "action": "alert",
      "rationale": "Trusted sources state bleach ingestion is dangerous."
    }
  ],
  "summary": { "max_harm": 92, "action": "alert" }
}

POST /debug/analyze

Same shape + "trace":[{agent, out}, ...].

📂 Repo Structure
/backend
├─ app/
│  ├─ main.py
│  ├─ schemas.py
│  ├─ config.py
│  └─ settings.py        # NEW: thresholds & guardrails
├─ agents/
│  ├─ base.py
│  ├─ orchestrator.py    # UPDATED: YouTube-only chain
│  ├─ ingestor_youtube.py# NEW
│  ├─ claim_extractor.py # NEW
│  ├─ query_expander.py  # UPDATED: health/guidelines focused
│  ├─ retrievers/
│  │  ├─ retriever_trusted_web.py  # NEW (site-limited)
│  │  └─ retriever_openalex.py     # NEW
│  ├─ reranker.py        # UPDATED: min cosine filter + relevance
│  ├─ verifier.py        # UPDATED: health rules + abstain on low relevance
│  ├─ harm_scorer.py     # UPDATED: health guardrails (cap unknown, floor for danger)
│  └─ action.py
├─ requirements.txt
└─ README.md

⚡ Quickstart
# 1) Env
cp .env.example .env
# Add keys if needed (search provider). YouTube transcripts need none.

# 2) Build & run
docker compose up --build

# 3) Test
curl -s -X POST http://localhost:8000/debug/analyze \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}' | jq


Healthy behavior

If no relevant evidence → factual_confidence=0.5, harm_score ≤ 45, action="inform".

Contradicted dangerous advice → action="alert", harm ≥ 80.

🧪 Golden tests (suggested)

Unknown neutral: “This fruit grants immortality.” → inform, harm ≤ 45

True guideline: “NHS recommends X for Y” (actually supported) → inform, F high

Dangerous: “Drink bleach to detox” → alert, harm ≥ 80

🔍 Explainability

Each claim shows:

Timestamp in video

Citations (trusted domains)

Relevance score

Confidence (F), Harm, Action

Rationale (short)