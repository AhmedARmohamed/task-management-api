import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_create_task():
    """Test task creation"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login user
        await ac.post("/signup", json={
            "username": "taskuser",
            "password": "taskpass123"
        })

        login_response = await ac.post("/token", data={
            "username": "taskuser",
            "password": "taskpass123"
        })

        token = login_response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": "123456"
        }

        # Create task
        response = await ac.post("/tasks", json={
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending"
        }, headers=headers)

    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"
    assert response.json()["status"] == "pending"

@pytest.mark.asyncio
async def test_get_tasks():
    """Test getting user tasks"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login user
        await ac.post("/signup", json={
            "username": "gettaskuser",
            "password": "taskpass123"
        })

        login_response = await ac.post("/token", data={
            "username": "gettaskuser",
            "password": "taskpass123"
        })

        token = login_response.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": "123456"
        }

        # Create a task first
        await ac.post("/tasks", json={
            "title": "Test Task",
            "description": "Test Description"
        }, headers=headers)

        # Get tasks
        response = await ac.get("/tasks", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test Task"

@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test unauthorized access to protected endpoints"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Try to access tasks without token
        response = await ac.get("/tasks")
        assert response.status_code == 401

        # Try to access tasks without API key
        response = await ac.get("/tasks", headers={
            "Authorization": "Bearer invalid-token"
        })
        assert response.status_code == 401