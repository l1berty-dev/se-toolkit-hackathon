from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from typing import List, Optional
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/lms")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="LMS Professional Management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ThresholdUpdate(BaseModel):
    course_id: int
    grade_letter: str
    min_score: int

class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    weight: float
    deadline: str # ISO format string

class AssignmentUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    weight: Optional[float] = None
    deadline: Optional[str] = None
    score: Optional[float] = None

@app.get("/courses/performance")
def get_performance():
    db = SessionLocal()
    query = """
        SELECT 
            c.id, c.name, c.code,
            COALESCE(SUM(g.score * a.weight), 0) as current_weighted_score,
            SUM(CASE WHEN g.score IS NOT NULL THEN a.weight ELSE 0 END) as completed_weight
        FROM courses c
        LEFT JOIN assignments a ON a.course_id = c.id
        LEFT JOIN grades g ON g.assignment_id = a.id
        GROUP BY c.id, c.name, c.code
        ORDER BY c.id
    """
    courses = db.execute(text(query)).mappings().all()
    result = []
    for course in courses:
        thresholds = db.execute(text("SELECT grade_letter, min_score FROM grade_thresholds WHERE course_id = :cid ORDER BY min_score DESC"), {"cid": course["id"]}).mappings().all()
        assignments = db.execute(text("SELECT a.id, a.title, a.weight, a.deadline, g.score FROM assignments a LEFT JOIN grades g ON g.assignment_id = a.id WHERE a.course_id = :cid ORDER BY a.deadline"), {"cid": course["id"]}).mappings().all()
        result.append({"course_info": course, "thresholds": thresholds, "assignments": assignments})
    db.close()
    return result

@app.get("/deadlines")
def get_all_deadlines():
    db = SessionLocal()
    query = """
        SELECT a.id, a.title, a.deadline, c.name as course_name, a.weight, g.score
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        LEFT JOIN grades g ON g.assignment_id = a.id
        ORDER BY a.deadline ASC
    """
    result = db.execute(text(query)).mappings().all()
    db.close()
    return result

@app.post("/add/assignment")
def add_assignment(data: AssignmentCreate):
    db = SessionLocal()
    try:
        db.execute(text("INSERT INTO assignments (course_id, title, weight, deadline) VALUES (:cid, :t, :w, :d)"),
                   {"cid": data.course_id, "t": data.title, "w": data.weight, "d": data.deadline})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
    return {"status": "created"}

@app.post("/update/assignment")
def update_assignment(data: AssignmentUpdate):
    db = SessionLocal()
    try:
        if any([data.title, data.weight is not None, data.deadline]):
            db.execute(text("""
                UPDATE assignments 
                SET title = COALESCE(:t, title), 
                    weight = COALESCE(:w, weight),
                    deadline = COALESCE(:d, deadline::timestamp)
                WHERE id = :id
            """), {"t": data.title, "w": data.weight, "d": data.deadline, "id": data.id})
        
        if data.score is not None:
            db.execute(text("INSERT INTO grades (assignment_id, score) VALUES (:id, :s) ON CONFLICT (assignment_id) DO UPDATE SET score = :s"),
                       {"id": data.id, "s": data.score})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
    return {"status": "updated"}

@app.post("/update/threshold")
def update_threshold(data: ThresholdUpdate):
    db = SessionLocal()
    db.execute(text("UPDATE grade_thresholds SET min_score = :score WHERE course_id = :cid AND grade_letter = :letter"), 
               {"score": data.min_score, "cid": data.course_id, "letter": data.grade_letter})
    db.commit()
    db.close()
    return {"status": "updated"}

@app.post("/delete/assignment")
def delete_assignment(data: dict):
    db = SessionLocal()
    assignment_id = data.get("id")
    if not assignment_id:
        raise HTTPException(status_code=400, detail="ID required")
    db.execute(text("DELETE FROM assignments WHERE id = :id"), {"id": assignment_id})
    db.commit()
    db.close()
    return {"status": "deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
