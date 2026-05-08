from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text, or_
from .models import User, Post
from src.accounts.schema import UserCreate, UserResponse, PostCreate, PostResponse
from .utils import password_service
from pydantic import EmailStr
from starlette.exceptions import HTTPException
from fastapi import status
import uuid
class UserService:
    async def fetch_user_by_email_or_uuid(self, session: AsyncSession, email: EmailStr | None = None, key: uuid.UUID | None = None):
        statement  = select(User).where(
            or_(
            User.email == email,
            User.key == key
            )
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    
    async def all_post_by_user(self, session: AsyncSession, key: uuid.UUID):
        user = await self.fetch_user_by_email_or_uuid(session=session, key=key)

        if user is None:
            raise HTTPException(
                detail="user not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if user.is_active is False:
            raise HTTPException(
                detail="Inactive user.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        statement = select(Post).where(
            Post.user_id == user.key
        )
        result = await session.execute(statement)
        return {
            "posts":result.scalars().fetchall(),
            "user": user
        }

    async def CreateUser(self, data: UserCreate, session: AsyncSession):
        is_user = await self.fetch_user_by_email_or_uuid(session=session, email=data.email)
        if is_user:
            raise HTTPException(
                detail="this email already exist",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user  = User(
            email=data.email,
            hashed_password=password_service.create_password(data.password1)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


    async def GetAUser(self, user_uuid: uuid.UUID, session: AsyncSession):
        user = await self.fetch_user_by_email_or_uuid(session=session, key=user_uuid)
        if user is None:
            raise HTTPException(
                detail="this email already exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return user
    
class PostService:
    async def fetch_post_by_uid(self, post_uid: uuid.UUID, session: AsyncSession):
        statament = select(Post).where(Post.key == post_uid)
        result = await session.execute(statament)
        post =  result.scalar_one_or_none()
        if post is None:
            raise HTTPException(
                detail="post not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return post
    

    async def CreatePost(self, data: PostCreate, session: AsyncSession):
        user =await UserService().fetch_user_by_email_or_uuid(session=session, key=data.user_id)
        if user is None:
            raise HTTPException(
                detail="user not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if user.is_active is False:
            raise HTTPException(
                detail="Inactive user.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        post = Post(
            **(data.model_dump())
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post
