from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models import TaskStatus

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    """User response schema"""
    id: int

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING

class TaskCreate(TaskBase):
    """Task creation schema"""
    pass

class TaskUpdate(BaseModel):
    """Task update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    """Task response schema"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None