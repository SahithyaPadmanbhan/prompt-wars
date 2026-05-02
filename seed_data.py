from database import SessionLocal, engine
from models import Task, Comment, User, Project, Base
import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing data
db.query(Comment).delete()
db.query(Task).delete()
db.query(Project).delete()
db.query(User).delete()
db.commit()

# Create Users
users = [
    User(name="Alice (Manager)", role="manager"),
    User(name="Sahithya", role="employee"),
    User(name="Bob", role="employee"),
    User(name="Charlie", role="employee"),
    User(name="Diana", role="employee")
]
db.add_all(users)
db.commit()
for u in users: db.refresh(u)

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
projects[0].users.extend([users[0], users[1], users[2]])
projects[1].users.extend([users[0], users[1], users[3]])
projects[2].users.extend([users[0], users[2], users[4]])
db.commit()

# Create tasks
tasks_data = [
    # Project Alpha
    {"title": "Implement Gemini API wrapper", "desc": "Create a robust wrapper for the generative AI SDK.", "status": "done", "assignee": users[1], "project": projects[0], "priority": "high"},
    {"title": "Design AI Standup Prompts", "desc": "Refine prompts to get more accurate standup reports.", "status": "review", "assignee": users[2], "project": projects[0], "priority": "high"},
    {"title": "Test AI summarization", "desc": "Run edge cases for very long comment threads.", "status": "in_progress", "assignee": users[1], "project": projects[0], "priority": "medium"},
    
    # Project Beta
    {"title": "Setup GCP Cloud Build", "desc": "Configure triggers for automatic deployment to Cloud Run.", "status": "done", "assignee": users[1], "project": projects[1], "priority": "high"},
    {"title": "Hardened Security Headers", "desc": "Add CORS and other security middleware to FastAPI.", "status": "in_progress", "assignee": users[3], "project": projects[1], "priority": "medium"},
    {"title": "Database Migration Script", "desc": "Create a script to migrate from SQLite to Postgres.", "status": "todo", "assignee": users[1], "project": projects[1], "priority": "low", "blocked": True},
    
    # Project Gamma
    {"title": "Main Dashboard Design", "desc": "Create high-fidelity mockups for the coordination board.", "status": "done", "assignee": users[4], "project": projects[2], "priority": "medium"},
    {"title": "Accessibility Audit", "desc": "Ensure all elements have proper ARIA labels.", "status": "in_progress", "assignee": users[2], "project": projects[2], "priority": "high"},
    {"title": "Responsive Layout Fixes", "desc": "Fix the sidebar behavior on mobile devices.", "status": "todo", "assignee": users[4], "project": projects[2], "priority": "low"}
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
    Comment(task_id=tasks[0].id, content="API wrapper is ready and tested.", author="Sahithya"),
    Comment(task_id=tasks[1].id, content="Working on the system prompt today.", author="Bob"),
    Comment(task_id=tasks[1].id, content="Please include a section for 'Next Steps'.", author="Alice (Manager)"),
    Comment(task_id=tasks[4].id, content="CORS middleware is added. Testing with the frontend now.", author="Charlie"),
    Comment(task_id=tasks[5].id, content="Blocked until we have the production DB credentials.", author="Sahithya")
]

db.add_all(comments)
db.commit()

print("Database seeded with extensive dummy data!")
db.close()
