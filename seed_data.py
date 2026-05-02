from database import SessionLocal, engine
from models import Task, Comment, User, Project, Base
import datetime
import random

# Reset DB
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

names = ["Sahithya", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah"]
employees = []
for name in names:
    emp = User(name=name, role="employee", manager_id=manager.id)
    db.add(emp)
    employees.append(emp)
db.commit()
for e in employees: db.refresh(e)

# Create Projects
projects = [
    Project(name="Project Alpha (AI)", scheduled_call_time="Daily at 10:00 AM"),
    Project(name="Project Beta (Infrastructure)", scheduled_call_time="Weekly on Tuesdays at 2:00 PM"),
    Project(name="Project Gamma (UI/UX)", scheduled_call_time="Bi-weekly at 11:00 AM"),
    Project(name="Project Delta (Security)", scheduled_call_time="Fridays at 4:00 PM"),
    Project(name="Project Epsilon (Marketing)", scheduled_call_time="Mondays at 9:00 AM")
]
db.add_all(projects)
db.commit()
for p in projects: db.refresh(p)

# Link Users to Projects (Randomly)
for p in projects:
    p.users.append(manager)
    team = random.sample(employees, k=random.randint(2, 4))
    p.users.extend(team)
db.commit()

# Create 40 tasks
statuses = ["todo", "in_progress", "review", "done"]
priorities = ["low", "medium", "high"]
task_titles = [
    "Implement Gemini API wrapper", "Design AI Standup Prompts", "Test AI summarization", "Evaluate Model Performance",
    "Setup GCP Cloud Build", "Hardened Security Headers", "Database Migration Script", "Network Configuration",
    "Main Dashboard Design", "Accessibility Audit", "Responsive Layout Fixes", "SVG Icon System",
    "OAuth2.0 Integration", "JWT Token Handling", "API Documentation (Swagger)", "Performance Benchmarking",
    "User Onboarding Flow", "Notification Service", "Email Template Design", "Error Logging Middleware",
    "Unit Test Coverage", "Integration Testing", "Load Testing for API", "Documentation for Deployment",
    "Mobile App Wireframes", "Android App Shell", "iOS App Shell", "Push Notification Setup",
    "Landing Page Copy", "Social Media Graphics", "Marketing Strategy Plan", "SEO Optimization",
    "Dependency Audit", "Package Security Scans", "Secret Rotation Script", "Firewall Rules Review",
    "CI/CD Pipeline Optimization", "Docker Image Minimization", "Cache Strategy Implementation", "Web Analytics Setup"
]

tasks = []
for i in range(len(task_titles)):
    project = random.choice(projects)
    # Pick a user assigned to this project
    assignee = random.choice(project.users)
    
    task = Task(
        title=task_titles[i],
        description=f"Detailed description for {task_titles[i]}. This is an automated task generated for demonstration purposes.",
        status=random.choice(statuses),
        assignee=assignee.name,
        assignee_id=assignee.id,
        project_id=project.id,
        priority=random.choice(priorities),
        is_blocked=random.random() < 0.15,
        created_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 10))
    )
    tasks.append(task)

db.add_all(tasks)
db.commit()
for t in tasks: db.refresh(t)

# Add some comments to first 20 tasks
authors = [u.name for u in [manager] + employees]
for i in range(20):
    for _ in range(random.randint(1, 4)):
        comment = Comment(
            task_id=tasks[i].id,
            content=random.choice([
                "Good progress here.", "I'm blocked on this.", "Can we review this together?", 
                "Added more details to the description.", "Finished the initial draft.", 
                "Need input from the manager.", "Looking great!"
            ]),
            author=random.choice(authors),
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=random.randint(1, 48))
        )
        db.add(comment)
db.commit()

print(f"Database seeded with {len(tasks)} tasks and {len(projects)} projects!")
db.close()
