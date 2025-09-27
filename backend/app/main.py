# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db import SessionLocal, Result
from app.schemas import AnalyzeRequest, ResultOut, EvidenceItem
from agents.orchestrator import Orchestrator
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # for hackathon demo; lock down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orch = Orchestrator()


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()

@app.post("/analyze", response_model=ResultOut)
def analyze(payload: AnalyzeRequest, response: Response, db: Session = Depends(get_db)):
    norm = normalize(payload.text)

    existing = db.query(Result).filter(Result.text == norm).first()
    if existing:
        return existing

    # Run local agent pipeline
    out = orch.run_pipeline(norm)

    # Persist
    new = Result(
        text=norm,
        harm_score=int(out["harm_score"]),
        action=out["action"],
        evidence=out["evidence"],  # JSONB
    )
    db.add(new); db.commit(); db.refresh(new)

    response.status_code = status.HTTP_201_CREATED
    response.headers["Location"] = f"/results/{new.id}"
    return new

@app.get("/results/{result_id}", response_model=ResultOut)
def get_result(result_id: int, db: Session = Depends(get_db)):
    r = db.query(Result).get(result_id)
    if not r:
        raise HTTPException(status_code=404, detail="Result not found")
    return r

@app.get("/results", response_model=list[ResultOut])
def list_results(limit: int = 20, offset: int = 0, text: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Result)
    if text:
        q = q.filter(Result.text == normalize(text))
    return q.order_by(Result.id.desc()).offset(offset).limit(limit).all()

@app.post("/debug/analyze")
def debug_analyze(payload: AnalyzeRequest):
    norm = normalize(payload.text)
    return orch.run_pipeline(norm, debug=True)