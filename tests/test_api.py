from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_read_users():
    response = client.get("/api/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_projects():
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_task_validation():
    # Test missing required field (title)
    response = client.post("/api/tasks", json={"description": "Test"})
    assert response.status_code == 422 # Unprocessable Entity

def test_ai_query_structure():
    # Test AI query endpoint structure
    response = client.post("/api/ai/query", json={"prompt": "Hello"})
    assert response.status_code == 200
    assert "response" in response.json()
