# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db import SessionLocal, Result
from app.schemas import AnalyzeRequest, ResultOut, EvidenceItem

app = FastAPI()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()

@app.post("/analyze", response_model=ResultOut)
def analyze(payload: AnalyzeRequest, response: Response, db: Session = Depends(get_db)):
    norm = normalize(payload.text)

    # Return existing if found
    existing = db.query(Result).filter(Result.text == norm).first()
    if existing:
        return existing

    # Dummy pipeline; replace with agents later
    # --- begin placeholder ---
    from random import randint
    harm = randint(0, 100)
    action = "inform" if harm < 25 else "flag" if harm < 60 else "alert"
    evidence = [
        {"source":"Wikipedia","confidence":0.92,"snippet":"Summary snippet...", "url":"https://en.wikipedia.org/..."}
    ]
    # --- end placeholder ---

    new = Result(text=norm, harm_score=harm, action=action, evidence=evidence)
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
