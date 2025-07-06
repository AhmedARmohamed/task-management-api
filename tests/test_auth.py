import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from tests.test_helpers import generate_random_user, user_manager

@pytest.mark.asyncio
async def test_signup():
    """Test user registration"""
    # Generate random user to avoid conflicts
    user_data = generate_random_user()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/signup", json=user_data)

    assert response.status_code == 201
    assert response.json()["username"] == user_data["username"]
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_signup_duplicate_username():
    """Test registration with duplicate username"""
    # Generate random user
    user_data = generate_random_user()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First registration
        response1 = await ac.post("/signup", json=user_data)
        assert response1.status_code == 201

        # Duplicate registration (same username)
        response2 = await ac.post("/signup", json=user_data)

    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_login():
    """Test user login"""
    # Generate random user
    user_data = generate_random_user()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register user first
        signup_response = await ac.post("/signup", json=user_data)
        assert signup_response.status_code == 201

        # Login
        response = await ac.post("/token", data=user_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    # Use random credentials that don't exist
    fake_user = generate_random_user()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/token", data=fake_user)

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]