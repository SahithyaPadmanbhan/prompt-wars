# TeamSync - AI-First Coordination Platform

TeamSync is an intelligent project management and team coordination platform built to solve fragmented communication and improve workflow visibility. It includes a smart "AI-first coordination" layer.

## Features
- **Kanban Board:** Drag and drop tasks across stages (To Do, In Progress, Review, Done).
- **Task Management:** Assign tasks, set priorities, track blockers.
- **In-Context Comments:** Keep task discussions in one place.
- **AI Standups:** Automatically generate daily standup summaries based on task status.
- **AI Task Summarization:** Quickly summarize long comment threads and task details to identify blockers and next steps.

## Tech Stack
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite (Development) / PostgreSQL (Production)
- **Frontend:** Vanilla HTML, CSS (Glassmorphism & Dark Mode), JavaScript
- **AI Integration:** Google Gemini API (`google-generativeai`)
- **Deployment:** Docker, Google Cloud Run

## How to Run Locally

1. Create a virtual environment and install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic python-multipart
   # Optional: For AI Features
   pip install google-generativeai
   ```

2. Set your Google Gemini API Key (optional, will use mock data if not set):
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8080
   ```

4. Open your browser and navigate to:
   [http://localhost:8080/app/index.html](http://localhost:8080/app/index.html)

## Deployment to Google Cloud Run

This repository includes a `Dockerfile` and a `cloudbuild.yaml` file for easy deployment to Google Cloud Run.

Using gcloud CLI:
```bash
gcloud run deploy team-sync --source . --region us-central1 --allow-unauthenticated
```
