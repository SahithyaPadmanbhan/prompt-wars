from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Table
from sqlalchemy.orm import relationship, backref
from database import Base
import datetime

user_project_association = Table(
    'user_projects', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('project_id', Integer, ForeignKey('projects.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String, default="employee") # employee, manager
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    projects = relationship("Project", secondary=user_project_association, back_populates="users")
    subordinates = relationship("User", backref=backref("manager", remote_side=[id]))

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    scheduled_call_time = Column(String, nullable=True)
    users = relationship("User", secondary=user_project_association, back_populates="projects")
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="todo") # todo, in_progress, review, done
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assignee = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String, default="medium") # low, medium, high
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="tasks")
    user = relationship("User", foreign_keys=[assignee_id])

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    content = Column(Text)
    author = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Task", back_populates="comments")
