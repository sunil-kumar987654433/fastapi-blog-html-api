from pydantic import BaseModel, Field, ConfigDict, EmailStr
from sqlmodel import Field
from datetime import datetime, date
import uuid

class UserBase(BaseModel):
    email: EmailStr = Field(min_length=1, max_length=50, description="Name of user")


class UserCreate(UserBase):
    password1: str
    password2: str

class UserResponse(UserBase):
    id: int
    key: uuid.UUID
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    user_role: str
    image_file: str | None = None
    image_path: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )



class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str= Field(min_length=1)
    

class PostCreate(PostBase):
    user_id: uuid.UUID
    date_posted: date

class PostResponse(PostBase):
    id: int | None = None
    key: uuid.UUID
    user_id: uuid.UUID
    date_posted: date
    author: UserResponse 
    model_config = ConfigDict(from_attributes=True)