from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db
import ai_utils

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TeamSync - AI-First Coordination Platform")

# Mount static files for frontend
# Ensure the "static" directory exists
import os
os.makedirs("static", exist_ok=True)
app.mount("/app", StaticFiles(directory="static", html=True), name="static")

@app.get("/api/tasks", response_model=List[schemas.TaskResponse])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = db.query(models.Task).offset(skip).limit(limit).all()
    return tasks

@app.post("/api/tasks", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    db.commit()
    db.refresh(db_task)
    return db_task

@app.post("/api/tasks/{task_id}/comments", response_model=schemas.CommentResponse)
def create_comment(task_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db_comment = models.Comment(**comment.model_dump(), task_id=task_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@app.get("/api/ai/standup")
def ai_standup(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    task_strings = [f"[{t.status.upper()}] {t.title} - Assignee: {t.assignee} - Blocked: {t.is_blocked}" for t in tasks]
    standup = ai_utils.generate_standup(task_strings)
    return {"standup": standup}

@app.get("/api/ai/summarize/{task_id}")
def ai_summarize_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_details = f"Title: {task.title}\nDescription: {task.description}\nStatus: {task.status}\nAssignee: {task.assignee}"
    comments = [f"{c.author}: {c.content}" for c in task.comments]
    
    summary = ai_utils.summarize_task(task_details, comments)
    return {"summary": summary}
