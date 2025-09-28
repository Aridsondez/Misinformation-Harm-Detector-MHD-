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


@app.post("/analyze", status_code=201)
def analyze(req: AnalyzeRequest):
    # IMPORTANT: pass req.url and req.media_type
    text = (req.text or "").strip()
    url = str(req.url) if req.url else None
    try:
        res = orch.run_pipeline(text=text, url=url, media_type=req.media_type, debug=False)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/analyze", status_code=201)
def debug_analyze(req: AnalyzeRequest):
    text = (req.text or "").strip()
    url = str(req.url) if req.url else None
    try:
        res = orch.run_pipeline(text=text, url=url, media_type=req.media_type, debug=True)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=ResultOut)
def analyze(payload: AnalyzeRequest, response: Response, db: Session = Depends(get_db)):
    norm = payload.text or ""

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
