from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from typing import List, Optional
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/lms")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="LMS Query API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/assignments")
def get_assignments(course_id: Optional[int] = None):
    db = SessionLocal()
    query = "SELECT a.id, a.title, a.deadline, a.max_score, c.name as course_name FROM assignments a JOIN courses c ON a.course_id = c.id"
    if course_id:
        query += f" WHERE a.course_id = {course_id}"
    
    result = db.execute(text(query)).mappings().all()
    db.close()
    return result

@app.get("/grades")
def get_grades(student_id: str = "student_01"):
    db = SessionLocal()
    query = """
    SELECT a.title, g.score, a.max_score, c.name as course_name 
    FROM grades g 
    JOIN assignments a ON g.assignment_id = a.id 
    JOIN courses c ON a.course_id = c.id
    WHERE g.student_id = :student_id
    """
    result = db.execute(text(query), {"student_id": student_id}).mappings().all()
    db.close()
    return result

@app.get("/courses")
def get_courses():
    db = SessionLocal()
    result = db.execute(text("SELECT * FROM courses")).mappings().all()
    db.close()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
