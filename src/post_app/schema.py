
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from sqlmodel import Field
from datetime import datetime, date
import uuid
from src.accounts.schema import UserResponse

class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str= Field(min_length=1)
    

class PostCreate(PostBase):
    date_posted: date | None = None

class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    user_id: uuid.UUID


class PostResponse(PostBase):
    id: int | None = None
    key: uuid.UUID
    user_id: uuid.UUID
    date_posted: date
    author: UserResponse 
    model_config = ConfigDict(from_attributes=True)