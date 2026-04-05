from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
    grade_letter: str = Field(..., min_length=1, max_length=1)
    min_score: int = Field(..., ge=0, le=100)

class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)

class AssignmentCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1, max_length=200)
    weight: float = Field(..., ge=0, le=1)
    deadline: str 

class AssignmentUpdate(BaseModel):
    id: int
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    weight: Optional[float] = Field(None, ge=0, le=1)
    deadline: Optional[str] = None
    score: Optional[float] = Field(None, ge=0, le=100)

@app.get("/courses/performance")
def get_performance():
    db = SessionLocal()
    try:
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
            result.append({
                "course_info": dict(course), 
                "thresholds": [dict(t) for t in thresholds], 
                "assignments": [dict(a) for a in assignments]
            })
        return result
    finally:
        db.close()

@app.get("/deadlines")
def get_all_deadlines():
    db = SessionLocal()
    try:
        query = """
            SELECT a.id, a.title, a.deadline, c.name as course_name, a.weight, g.score
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
            LEFT JOIN grades g ON g.assignment_id = a.id
            ORDER BY a.deadline ASC
        """
        result = db.execute(text(query)).mappings().all()
        return [dict(r) for r in result]
    finally:
        db.close()

@app.get("/grades")
def get_grades():
    db = SessionLocal()
    try:
        query = """
            SELECT a.title, c.name as course_name, g.score, a.weight
            FROM grades g
            JOIN assignments a ON g.assignment_id = a.id
            JOIN courses c ON a.course_id = c.id
            ORDER BY c.name, a.deadline
        """
        result = db.execute(text(query)).mappings().all()
        return [dict(r) for r in result]
    finally:
        db.close()

@app.post("/courses/add")
def add_course(data: CourseCreate):
    db = SessionLocal()
    try:
        course_code = data.code or f"CRSE-{int(datetime.now().timestamp())}"
        result = db.execute(text("INSERT INTO courses (name, code) VALUES (:n, :c) RETURNING id"), 
                           {"n": data.name, "c": course_code[:20]})
        course_id = result.fetchone()[0]
        db.execute(text("""
            INSERT INTO grade_thresholds (course_id, grade_letter, min_score) 
            VALUES (:cid, 'A', 90), (:cid, 'B', 80), (:cid, 'C', 70)
        """), {"cid": course_id})
        db.commit()
        return {"status": "created", "id": course_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/add/assignment")
def add_assignment(data: AssignmentCreate):
    db = SessionLocal()
    try:
        db.execute(text("INSERT INTO assignments (course_id, title, weight, deadline) VALUES (:cid, :t, :w, CAST(:d AS TIMESTAMP))"),
                   {"cid": data.course_id, "t": data.title, "w": data.weight, "d": data.deadline})
        db.commit()
        return {"status": "created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/update/assignment")
def update_assignment(data: AssignmentUpdate):
    db = SessionLocal()
    try:
        update_dict = data.model_dump(exclude_unset=True)
        if any(k in update_dict for k in ["title", "weight", "deadline"]):
            db.execute(text("""
                UPDATE assignments 
                SET title = COALESCE(:t, title), 
                    weight = COALESCE(:w, weight),
                    deadline = COALESCE(CAST(:d AS TIMESTAMP), deadline)
                WHERE id = :id
            """), {"t": data.title, "w": data.weight, "d": data.deadline, "id": data.id})
        
        if "score" in update_dict:
            if data.score is None:
                db.execute(text("DELETE FROM grades WHERE assignment_id = :id"), {"id": data.id})
            else:
                db.execute(text("INSERT INTO grades (assignment_id, score) VALUES (:id, :s) ON CONFLICT (assignment_id) DO UPDATE SET score = :s"),
                           {"id": data.id, "s": data.score})
        db.commit()
        return {"status": "updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/update/threshold")
def update_threshold(data: ThresholdUpdate):
    db = SessionLocal()
    try:
        db.execute(text("UPDATE grade_thresholds SET min_score = :score WHERE course_id = :cid AND grade_letter = :letter"), 
                {"score": data.min_score, "cid": data.course_id, "letter": data.grade_letter})
        db.commit()
        return {"status": "updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/delete/assignment")
def delete_assignment(data: dict):
    db = SessionLocal()
    try:
        assignment_id = data.get("id")
        if not assignment_id:
            raise HTTPException(status_code=400, detail="ID required")
        db.execute(text("DELETE FROM assignments WHERE id = :id"), {"id": assignment_id})
        db.commit()
        return {"status": "deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
