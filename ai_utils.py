import os
import random

# Try to import google.generativeai, but mock if it fails (e.g. not installed or no API key)
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Setup Gemini API key
api_key = os.getenv("GEMINI_API_KEY", "")
model = None

if HAS_GEMINI and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

def generate_ai_response(prompt: str) -> str:
    if model:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"**AI Error:** {str(e)}"
    
    # Mock fallback
    return _generate_mock_response(prompt)

def _generate_mock_response(prompt: str) -> str:
    """Provides a dummy AI response if Gemini is not configured/installed."""
    
    if "daily standup report" in prompt:
        return """
**Here's your AI-generated Standup Report:**
* **Completed:** Team has finished designing the database schema and API endpoints.
* **In Progress:** The frontend Kanban board and integration with the backend API is currently being worked on by the UI team.
* **Blockers:** We need clarification on the exact requirements for the Google Calendar integration.
"""
    elif "Summarize the following task" in prompt:
        return """
**Task Summary:**
This task involves creating the core authentication module. The team has discussed using OAuth2.0 but there are currently concerns about securely storing the tokens. 
* **Next Steps:** Finalize the decision on whether to use JWT or session-based cookies.
* **Blockers:** None currently detected.
"""
    else:
        return "This is a mock AI response. To use real AI capabilities, ensure `google-generativeai` is installed and `GEMINI_API_KEY` is set."

def summarize_task(task_details: str, comments: list) -> str:
    prompt = f"Summarize the following task and its discussion thread to provide a quick update on its status, blockers, and next steps:\n\nTask: {task_details}\n\nComments:\n"
    for c in comments:
        prompt += f"- {c}\n"
    
    return generate_ai_response(prompt)

def generate_standup(tasks: list) -> str:
    prompt = "Based on the following tasks and their statuses, generate a brief daily standup report outlining what was done, what is in progress, and any blockers.\n\nTasks:\n"
    for t in tasks:
        prompt += f"- {t}\n"
        
    return generate_ai_response(prompt)
