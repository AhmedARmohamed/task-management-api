from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional, Annotated
import os
import logging
from contextlib import asynccontextmanager

from app.database import get_db, create_tables
from app.models import User, Task
from app.schemas import UserCreate, UserResponse, TaskCreate, TaskResponse, TaskUpdate, Token
from app.auth import verify_password, get_password_hash, create_access_token, verify_token, get_current_user
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Task Management API...")

    # Only create tables if not in test environment
    if not settings.DATABASE_URL.endswith(":memory:"):
        await create_tables()
        logger.info("Database tables created successfully")
    else:
        logger.info("Test environment detected - skipping table creation")

    yield

    # Shutdown
    logger.info("Shutting down Task Management API...")

app = FastAPI(
    title="Task Management API",
    description="A secure, production-ready task management system with user authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API Key dependency


async def verify_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None):
    """Verify API key from header - exactly as specified in assessment"""
    if not x_api_key or x_api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {x_api_key}")
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
    """Verify both JWT token and API key as required by assessment"""
    return await get_current_user(token, db)

# Global exception handler


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development"
    }

# Auth endpoints


@app.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account - stores securely with hashed password"""
    try:
        logger.info(f"Signup attempt for username: {user.username}")

        # Check if user already exists
        result = await db.execute(select(User).where(User.username == user.username))
        if result.scalar_one_or_none():
            logger.warning(
                f"Signup failed - username already exists: {user.username}")
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

        logger.info(f"User created successfully: {user.username}")
        return UserResponse(id=db_user.id, username=db_user.username)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login with username and password (OAuth2 password flow) - exactly as specified"""
    try:
        logger.info(f"Login attempt for username: {form_data.username}")

        # Get user
        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Login failed for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        logger.info(f"Login successful for username: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during authentication"
        )

# Task endpoints - All protected as required


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a task - Protected endpoint requiring JWT + API Key"""
    try:
        logger.info(
            f"Creating task for user {current_user.username}: {task.title}")

        db_task = Task(
            title=task.title,
            description=task.description,
            status=task.status,
            user_id=current_user.id
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)

        logger.info(f"Task created successfully: ID {db_task.id}")
        return TaskResponse(
            id=db_task.id,
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            user_id=db_task.user_id,
            created_at=db_task.created_at
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating task"
        )


@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def get_tasks(
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tasks for the logged-in user - Protected endpoint"""
    try:
        logger.info(f"Fetching tasks for user: {current_user.username}")

        result = await db.execute(
            select(Task).where(Task.user_id == current_user.id).order_by(
                Task.created_at.desc())
        )
        tasks = result.scalars().all()

        logger.info(
            f"Retrieved {len(tasks)} tasks for user {current_user.username}")
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
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching tasks"
        )


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task - Protected endpoint"""
    try:
        logger.info(
            f"Fetching task {task_id} for user {current_user.username}")

        result = await db.execute(
            select(Task).where(Task.id == task_id,
                               Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(
                f"Task {task_id} not found for user {current_user.username}")
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
        logger.error(f"Error fetching task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching task"
        )


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Update task status - Protected endpoint"""
    try:
        logger.info(
            f"Updating task {task_id} for user {current_user.username}")

        result = await db.execute(
            select(Task).where(Task.id == task_id,
                               Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(
                f"Task {task_id} not found for user {current_user.username}")
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

        logger.info(f"Task {task_id} updated successfully")
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
        logger.error(f"Error updating task: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating task"
        )


@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete task - Protected endpoint"""
    try:
        logger.info(
            f"Deleting task {task_id} for user {current_user.username}")

        result = await db.execute(
            select(Task).where(Task.id == task_id,
                               Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(
                f"Task {task_id} not found for user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        await db.delete(task)
        await db.commit()

        logger.info(f"Task {task_id} deleted successfully")
        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting task"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info" if settings.DEBUG else "warning"
    )
