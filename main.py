from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import engine, get_db
import ai_utils
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Conexión - AI-First Coordination Platform")

# Security: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
os.makedirs("static", exist_ok=True)
app.mount("/app", StaticFiles(directory="static", html=True), name="static")

@app.get("/api/users", response_model=List[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.get("/api/projects", response_model=List[schemas.ProjectResponse])
def read_projects(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Project)
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user and user.role != 'manager':
            # Employees only see their own projects
            return user.projects
        # Managers see all projects, so fall through to query.all()
    return query.all()

@app.get("/api/tasks", response_model=List[schemas.TaskResponse])
def read_tasks(skip: int = 0, limit: int = 100, project_id: Optional[int] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Task)
    
    # If a user is provided, we might want to filter tasks based on role.
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            if user.role == 'manager':
                # managers can see all tasks, or filter by project if provided
                pass
            else:
                # employees see tasks for their projects
                project_ids = [p.id for p in user.projects]
                query = query.filter(models.Task.project_id.in_(project_ids))
    
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
        
    return query.offset(skip).limit(limit).all()

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
def ai_standup(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Task)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    tasks = query.all()
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

@app.post("/api/ai/query")
def ai_query(request: schemas.AIRequest, project_id: Optional[int] = None, db: Session = Depends(get_db)):
    # Fetch relevant project data to provide context to the AI
    query_context = ""
    if project_id:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            query_context = f"Project: {project.name}\n"
            tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
            for t in tasks:
                query_context += f"- [{t.status}] {t.title} (Assigned to: {t.assignee})\n"
    
    prompt = f"Context about the team coordination platform:\n{query_context}\n\nUser Question: {request.prompt}\n\nPlease provide a helpful and concise answer based on the context."
    response = ai_utils.generate_ai_response(prompt)
    return {"response": response}
