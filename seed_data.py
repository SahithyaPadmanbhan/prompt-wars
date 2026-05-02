from database import SessionLocal, engine
from models import Task, Comment, User, Project, Base
import datetime

# Reset DB to apply schema changes
import os
if os.path.exists("teamsync_v2.db"):
    os.remove("teamsync_v2.db")

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Create Users
manager = User(name="Alice (Manager)", role="manager")
db.add(manager)
db.commit()
db.refresh(manager)

employees = [
    User(name="Sahithya", role="employee", manager_id=manager.id),
    User(name="Bob", role="employee", manager_id=manager.id),
    User(name="Charlie", role="employee", manager_id=manager.id),
    User(name="Diana", role="employee", manager_id=manager.id)
]
db.add_all(employees)
db.commit()
for e in employees: db.refresh(e)

# Create Projects
projects = [
    Project(name="Project Alpha (AI)", scheduled_call_time="Daily at 10:00 AM"),
    Project(name="Project Beta (Infrastructure)", scheduled_call_time="Weekly on Tuesdays at 2:00 PM"),
    Project(name="Project Gamma (UI/UX)", scheduled_call_time="Bi-weekly at 11:00 AM")
]
db.add_all(projects)
db.commit()
for p in projects: db.refresh(p)

# Link Users to Projects
projects[0].users.extend([manager, employees[0], employees[1]])
projects[1].users.extend([manager, employees[0], employees[2]])
projects[2].users.extend([manager, employees[1], employees[3]])
db.commit()

# Create tasks with detailed data for queries
tasks_data = [
    # Project Alpha
    {"title": "Implement Gemini API wrapper", "desc": "Create a robust wrapper for the generative AI SDK using Python.", "status": "done", "assignee": employees[0], "project": projects[0], "priority": "high"},
    {"title": "Design AI Standup Prompts", "desc": "Refine prompts to get more accurate standup reports. Focus on status, blockers, and next steps.", "status": "review", "assignee": employees[1], "project": projects[0], "priority": "high"},
    {"title": "Test AI summarization", "desc": "Run edge cases for very long comment threads and handle API timeouts.", "status": "in_progress", "assignee": employees[0], "project": projects[0], "priority": "medium"},
    {"title": "Evaluate Model Performance", "desc": "Compare Gemini 1.5 Flash vs Pro for summarization tasks.", "status": "todo", "assignee": employees[1], "project": projects[0], "priority": "low"},
    
    # Project Beta
    {"title": "Setup GCP Cloud Build", "desc": "Configure triggers for automatic deployment to Cloud Run on every git push.", "status": "done", "assignee": employees[0], "project": projects[1], "priority": "high"},
    {"title": "Hardened Security Headers", "desc": "Add CORS and other security middleware to FastAPI. Ensure XSS protection on frontend.", "status": "in_progress", "assignee": employees[2], "project": projects[1], "priority": "medium"},
    {"title": "Database Migration Script", "desc": "Create a script to migrate from SQLite to Postgres. Blocked by lack of prod credentials.", "status": "todo", "assignee": employees[0], "project": projects[1], "priority": "low", "blocked": True},
    
    # Project Gamma
    {"title": "Main Dashboard Design", "desc": "Create high-fidelity mockups for the coordination board using Glassmorphism.", "status": "done", "assignee": employees[3], "project": projects[2], "priority": "medium"},
    {"title": "Accessibility Audit", "desc": "Ensure all elements have proper ARIA labels and sufficient color contrast.", "status": "in_progress", "assignee": employees[1], "project": projects[2], "priority": "high"},
    {"title": "Responsive Layout Fixes", "desc": "Fix the sidebar behavior on mobile devices and tablet orientations.", "status": "todo", "assignee": employees[3], "project": projects[2], "priority": "low"}
]

tasks = []
for t in tasks_data:
    task = Task(
        title=t["title"],
        description=t["desc"],
        status=t["status"],
        assignee=t["assignee"].name,
        assignee_id=t["assignee"].id,
        project_id=t["project"].id,
        priority=t["priority"],
        is_blocked=t.get("blocked", False)
    )
    tasks.append(task)

db.add_all(tasks)
db.commit()
for t in tasks: db.refresh(t)

# Add comments
comments = [
    Comment(task_id=tasks[0].id, content="API wrapper is ready and tested with mock data.", author="Sahithya"),
    Comment(task_id=tasks[1].id, content="Working on the system prompt today. Need review from Alice.", author="Bob"),
    Comment(task_id=tasks[5].id, content="CORS middleware is added. Need to test with production domains.", author="Charlie"),
    Comment(task_id=tasks[6].id, content="Waiting for the DevOps team to provide the Cloud SQL connection string.", author="Sahithya")
]

db.add_all(comments)
db.commit()

print("Database seeded with hierarchy and detailed data!")
db.close()
