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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            return user.projects
    return query.all()

@app.post("/api/projects", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.put("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: int, project_update: schemas.ProjectBase, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in project_update.model_dump().items():
        setattr(db_project, key, value)
        
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/api/tasks", response_model=List[schemas.TaskResponse])
def read_tasks(
    skip: int = 0, 
    limit: int = 100, 
    project_id: Optional[int] = None, 
    user_id: Optional[int] = None, 
    filter_type: str = "team", # "me" or "team"
    db: Session = Depends(get_db)
):
    query = db.query(models.Task)
    
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            if filter_type == "me":
                query = query.filter(models.Task.assignee_id == user_id)
            elif user.role == 'manager':
                # Managers see all tasks for the team/projects
                pass
            else:
                # Employees see tasks for their projects (team view)
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
def ai_query(request: schemas.AIRequest, project_id: Optional[int] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    # Enhanced context for AI query
    context = "System Context: You are an AI coordination assistant for a platform called Conexión.\n"
    
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            context += f"Current User: {user.name} (Role: {user.role})\n"
            if user.role == 'manager':
                context += "You are helping a manager who can see all tasks and employees.\n"
            else:
                context += "You are helping an employee. They should focus on their tasks and their team's action items.\n"

    if project_id:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            context += f"Project context: {project.name}\n"
            tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
            context += "Tasks in this project:\n"
            for t in tasks:
                context += f"- {t.title} (Status: {t.status}, Assignee: {t.assignee}, Priority: {t.priority}, Blocked: {t.is_blocked})\n"
    else:
        # Global context if no project selected
        tasks = db.query(models.Task).limit(20).all()
        context += "Recent tasks across all projects:\n"
        for t in tasks:
            context += f"- {t.title} (Project: {t.project.name if t.project else 'N/A'}, Status: {t.status}, Assignee: {t.assignee})\n"

    prompt = f"{context}\nUser Question: {request.prompt}\n\nProvide a detailed and helpful response based on the data above. If the user asks 'where am I' or 'who am I', refer to the Current User info."
    response = ai_utils.generate_ai_response(prompt)
    return {"response": response}
