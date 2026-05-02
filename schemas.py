from pydantic import BaseModel
from typing import List, Optional
import datetime

class CommentBase(BaseModel):
    content: str
    author: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    task_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    assignee: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: str = "medium"
    is_blocked: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: Optional[str] = None
    is_blocked: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    created_at: datetime.datetime
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True

class AIRequest(BaseModel):
    prompt: str
