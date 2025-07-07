import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from tests.test_helpers import generate_random_user, generate_random_task


@pytest.mark.asyncio
async def test_create_task():
    """Test task creation"""
    # Generate random user and task
    user_data = generate_random_user()
    task_data = generate_random_task("CreateTest")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login user
        await ac.post("/signup", json=user_data)

        login_response = await ac.post("/token", data=user_data)
        token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "X-API-Key": "123456"
        }

        # Create task
        response = await ac.post("/tasks", json=task_data, headers=headers)

    assert response.status_code == 201
    assert response.json()["title"] == task_data["title"]
    assert response.json()["description"] == task_data["description"]
    assert response.json()["status"] == task_data["status"]


@pytest.mark.asyncio
async def test_get_tasks():
    """Test getting user tasks"""
    # Generate random user and task
    user_data = generate_random_user()
    task_data = generate_random_task("GetTest")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login user
        await ac.post("/signup", json=user_data)

        login_response = await ac.post("/token", data=user_data)
        token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "X-API-Key": "123456"
        }

        # Create a task first
        await ac.post("/tasks", json=task_data, headers=headers)

        # Get tasks
        response = await ac.get("/tasks", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == task_data["title"]


@pytest.mark.asyncio
async def test_user_isolation():
    """Test that users can only see their own tasks"""
    # Generate two different users
    user1_data = generate_random_user()
    user2_data = generate_random_user()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register both users
        await ac.post("/signup", json=user1_data)
        await ac.post("/signup", json=user2_data)

        # Login both users
        user1_login = await ac.post("/token", data=user1_data)
        user2_login = await ac.post("/token", data=user2_data)

        user1_headers = {
            "Authorization": f"Bearer {user1_login.json()['access_token']}",
            "X-API-Key": "123456"
        }
        user2_headers = {
            "Authorization": f"Bearer {user2_login.json()['access_token']}",
            "X-API-Key": "123456"
        }

        # User 1 creates a task
        user1_task = generate_random_task("User1Task")
        await ac.post("/tasks", json=user1_task, headers=user1_headers)

        # User 2 creates a task
        user2_task = generate_random_task("User2Task")
        await ac.post("/tasks", json=user2_task, headers=user2_headers)

        # User 1 should only see their own task
        user1_tasks = await ac.get("/tasks", headers=user1_headers)
        assert user1_tasks.status_code == 200
        user1_data_response = user1_tasks.json()
        assert len(user1_data_response) == 1
        assert user1_data_response[0]["title"] == user1_task["title"]

        # User 2 should only see their own task
        user2_tasks = await ac.get("/tasks", headers=user2_headers)
        assert user2_tasks.status_code == 200
        user2_data_response = user2_tasks.json()
        assert len(user2_data_response) == 1
        assert user2_data_response[0]["title"] == user2_task["title"]


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


@pytest.mark.asyncio
async def test_task_validation():
    """Test task input validation"""
    # Generate random user
    user_data = generate_random_user()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register and login user
        await ac.post("/signup", json=user_data)

        login_response = await ac.post("/token", data=user_data)
        token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "X-API-Key": "123456"
        }

        # Test empty title
        response = await ac.post("/tasks", json={
            "title": "",  # Empty title
            "description": "Valid description"
        }, headers=headers)
        assert response.status_code == 422

        # Test invalid status
        response = await ac.post("/tasks", json={
            "title": "Valid title",
            "status": "invalid_status"
        }, headers=headers)
        assert response.status_code == 422
