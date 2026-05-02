from database import SessionLocal, engine
from models import Task, Comment, User, Project, Base
import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing data (optional, but good for a fresh start)
db.query(Comment).delete()
db.query(Task).delete()
db.query(Project).delete()
db.query(User).delete()
db.commit()

# Create Users
manager1 = User(name="Alice (Manager)", role="manager")
emp1 = User(name="Sahithya", role="employee")
emp2 = User(name="Bob", role="employee")

db.add_all([manager1, emp1, emp2])
db.commit()

db.refresh(manager1)
db.refresh(emp1)
db.refresh(emp2)

# Create Projects
proj1 = Project(name="Project Alpha", scheduled_call_time="Daily at 10:00 AM")
proj2 = Project(name="Project Beta", scheduled_call_time="Weekly on Tuesdays at 2:00 PM")

# Link Users to Projects
proj1.users.extend([manager1, emp1, emp2])
proj2.users.extend([manager1, emp1])

db.add_all([proj1, proj2])
db.commit()
db.refresh(proj1)
db.refresh(proj2)

# Create tasks
tasks = [
    Task(
        title="Setup Google Cloud Run deployment",
        description="We need to write the Dockerfile and configure cloudbuild.yaml for continuous deployment.",
        status="done",
        assignee="Sahithya",
        assignee_id=emp1.id,
        project_id=proj1.id,
        priority="high"
    ),
    Task(
        title="Implement AI Summarization",
        description="Integrate the Gemini API to summarize long comment threads.",
        status="review",
        assignee="Bob",
        assignee_id=emp2.id,
        project_id=proj1.id,
        priority="high"
    ),
    Task(
        title="Design Kanban Board UI",
        description="Use glassmorphism and modern dark mode styling for the main dashboard.",
        status="in_progress",
        assignee="Sahithya",
        assignee_id=emp1.id,
        project_id=proj2.id,
        priority="medium"
    ),
    Task(
        title="Fix database connection timeout",
        description="The app sometimes loses connection to SQLite under load.",
        status="todo",
        assignee="Bob",
        assignee_id=emp2.id,
        project_id=proj2.id,
        priority="low",
        is_blocked=True
    )
]

db.add_all(tasks)
db.commit()

# Refresh to get IDs
for task in tasks:
    db.refresh(task)

# Add comments
comments = [
    Comment(
        task_id=tasks[1].id,
        content="I have set up the basic Gemini prompts, but we need an API key to test.",
        author="Bob"
    ),
    Comment(
        task_id=tasks[1].id,
        content="Make sure you handle cases where the API returns an error or is unconfigured.",
        author="Alice (Manager)"
    ),
    Comment(
        task_id=tasks[2].id,
        content="The drag-and-drop is working perfectly now!",
        author="Sahithya"
    ),
    Comment(
        task_id=tasks[3].id,
        content="Waiting for the DevOps team to increase the connection pool size before I can proceed.",
        author="Bob"
    )
]

db.add_all(comments)
db.commit()

print("Database seeded successfully with Users, Projects, and Tasks!")
db.close()
