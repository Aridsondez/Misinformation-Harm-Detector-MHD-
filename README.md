# Misinformation Harm Detector (MHD)

### Tagline
An autonomous-agent system that ingests claims or social media posts, fact-checks across trusted sources, computes a **harmfulness score**, and proposes actions (inform, flag, alert). Built for **ShellHacks 2025** as part of the Google Cloud Autonomous AI Agent Challenge + Google AI for Social Good.

---

## 🚀 Overview
Misinformation spreads faster than facts, harming public trust, health, and safety.  
Our project leverages **Google’s Agent Development Kit (ADK)** and the **A2A protocol** to create a system of autonomous agents that collaborate to:

1. **Ingest** claims from user input (or demo social posts).  
2. **Retrieve & Verify** information from multiple sources (Wikipedia, News APIs, fact-checking databases).  
3. **Score Harmfulness** based on factual accuracy, reach potential, and public safety risk.  
4. **Take Action** by recommending whether to simply inform, flag with warning, or escalate for human review.  
5. **Explain Results** with clear provenance (citations, snippets, and agent reasoning logs).  

This combats misinformation while demonstrating how **parallel agents** and **continuous loops** can coordinate for impactful social good.

---

## 🎯 Scope

### What we’re building
- A **backend orchestration system** of autonomous agents in Python (via ADK).  
- A **React frontend** for input + results visualization.  
- A **Postgres database** to store claims, evidence, and scores.  
- A **harmfulness scoring system** (0–100) that drives agent actions.  

### What we’re NOT building (for MVP)
- A full production-scale crawler of Twitter/TikTok/Instagram.  
- Automated posting/takedowns.  
- Complex legal/defamation adjudication.  

### Stretch Goals
- Background loop agent that monitors trending topics continuously.  
- Predictive model for which claims are likely to trend next.  
- Browser extension mockup to show real-time annotations on posts.

---

## 🧠 Harmfulness Score Design

We compute a composite **Harm Score (0–100)** using signals from multiple agents:

- **Factual accuracy (0–50):** confidence based on retrieved evidence.  
- **Reach potential (0–20):** estimated virality/trending score.  
- **Public safety risk (0–20):** danger to health, safety, or elections.  
- **Source credibility modifier (-10 to +10):** adjust score by source trustworthiness.  

### Threshold Actions
- `0–25` → **Inform** (provide fact summary with citations).  
- `26–60` → **Flag** (display warning + sources).  
- `61–100` → **Alert** (recommend human review / escalation).  

---

## 🛠️ Tech Stack

### Languages
- **Python 3.10+** — agents + backend.  
- **React (JavaScript/TypeScript)** — frontend UI.  

### Frameworks & Tools
- **FastAPI** — backend REST API.  
- **PostgreSQL** — claim/evidence database.  
- **Redis** — lightweight job queue & agent message bus.  
- **FAISS** — vector similarity search for past claims.  
- **Docker Compose** — orchestrate services.  

### External APIs
- [Google ADK](https://google.github.io/adk-docs/) (Agent Dev Kit) for loop + parallel agent design.  
- [A2A Protocol](https://a2a-protocol.org/latest/#what-is-a2a-protocol) for agent-to-agent communication.  
- **NewsAPI**, **Wikipedia API**, and **fact-check datasets** (PolitiFact, Snopes, etc.).  

---

## 🏗️ System Architecture
              +---------------------------+
              |  React Frontend           |
              |  - Input post/claim       |
              |  - View harm score        |
              +-----------+---------------+
                          |
                          v
                  +--------------------+
                  | FastAPI Backend    |
                  | - /analyze POST    |
                  | - /result GET      |
                  +--------------------+
                          |
                  +--------------------+
                  | Loop Controller    | <-- ADK loop agent
                  +--------------------+
            /      /       |       \       \
    Ingestor   Retriever  Verifier  Harm    Action
    Agent      Agents     Agent     Scorer  Agent
                           |
                 Evidence + Confidence

- **Loop Controller Agent**: manages continuous monitoring and job lifecycle.  
- **Ingestor Agent**: normalizes input, extracts claims.  
- **Retriever Agents**: query fact-check sources, Wikipedia, news APIs in parallel.  
- **Verifier Agent**: matches claims with evidence, calculates factual confidence.  
- **Harm Scorer Agent**: computes overall harmfulness score.  
- **Action Agent**: maps score → action (`inform`, `flag`, `alert`).  
- **DB + Vector Store**: store results, embeddings, provenance logs.

---

## 🖥️ Demo Plan

1. **Input a claim** (e.g., “5G causes COVID”).  
2. Agents collaborate: retrievers pull evidence, verifier matches, scorer computes harm.  
3. **Frontend displays**:  
   - Harmfulness score (e.g., 82 → ALERT).  
   - Evidence cards with snippets + links.  
   - Recommended action.  
   - Agent trace (why it made the decision).  
4. **Explain thresholds**: show how different harm scores trigger different actions.  

---

## 📂 Repo Structure

/mhd
├─ /frontend # React app
├─ /backend # FastAPI app
│ ├─ app/
│ │ ├─ main.py
│ │ ├─ routes.py
│ │ └─ db.py
├─ /agents # ADK agent implementations
│ ├─ loop_controller.py
│ ├─ ingestor_agent.py
│ ├─ retriever_agent.py
│ ├─ verifier_agent.py
│ ├─ harm_scorer_agent.py
│ └─ action_agent.py
├─ /fixtures # sample claims + evidence
├─ docker-compose.yml
└─ README.md

## ⚡ Quickstart

```bash
# Clone repo
git clone https://github.com/yourusername/mhd.git
cd mhd

# Copy environment example
cp .env.example .env   # add API keys here

# Build & run with Docker Compose
docker-compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000