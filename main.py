from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional, Annotated
import os
from contextlib import asynccontextmanager

from app.database import get_db, create_tables
from app.models import User, Task
from app.schemas import UserCreate, UserResponse, TaskCreate, TaskResponse, TaskUpdate, Token
from app.auth import verify_password, get_password_hash, create_access_token, verify_token, get_current_user
from app.config import settings

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Task Management API",
    description="A secure task management system with user authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API Key dependency
async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None):
    """Verify API key from header"""
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return x_api_key

# Combined authentication dependency
async def get_authenticated_user(
    token: str = Depends(oauth2_scheme),
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """Verify both JWT token and API key"""
    return await get_current_user(token, db)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Auth endpoints
@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account"""
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.username == user.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            hashed_password=hashed_password
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return UserResponse(id=db_user.id, username=db_user.username)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 password flow - get JWT token"""
    try:
        # Get user
        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during authentication"
        )

# Task endpoints
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    try:
        db_task = Task(
            title=task.title,
            description=task.description,
            status=task.status,
            user_id=current_user.id
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        return TaskResponse(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            user_id=db_task.user_id,
            created_at=db_task.created_at
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating task"
        )

@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks for the current user"""
    try:
        result = await db.execute(
            select(Task).where(Task.user_id == current_user.id).order_by(Task.created_at.desc())
        )
        tasks = result.scalars().all()

        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                user_id=task.user_id,
                created_at=task.created_at
            )
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching tasks"
        )

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task"""
    try:
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            user_id=task.user_id,
            created_at=task.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching task"
        )

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a task"""
    try:
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Update fields
        if task_update.title is not None:
            task.title = task_update.title
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.status is not None:
            task.status = task_update.status

        await db.commit()
        await db.refresh(task)

        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            user_id=task.user_id,
            created_at=task.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating task"
        )

@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task"""
    try:
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        await db.delete(task)
        await db.commit()

        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting task"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)