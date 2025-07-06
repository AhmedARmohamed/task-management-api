import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app


@pytest.mark.asyncio
async def test_signup():
    """Test user registration"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/signup", json={
            "username": "testuser",
            "password": "testpass123"
        })

    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_signup_duplicate_username():
    """Test registration with duplicate username"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First registration
        await ac.post("/signup", json={
            "username": "testuser2",
            "password": "testpass123"
        })

        # Duplicate registration
        response = await ac.post("/signup", json={
            "username": "testuser2",
            "password": "testpass456"
        })

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login():
    """Test user login"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register user first
        await ac.post("/signup", json={
            "username": "loginuser",
            "password": "loginpass123"
        })

        # Login
        response = await ac.post("/token", data={
            "username": "loginuser",
            "password": "loginpass123"
        })

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/token", data={
            "username": "nonexistent",
            "password": "wrongpass"
        })

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
