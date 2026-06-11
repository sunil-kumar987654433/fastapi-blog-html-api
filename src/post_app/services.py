
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text, or_
from datetime import date
from src.accounts.models import User
from src.db.database import get_session
from src.post_app.models import  Post
from src.post_app.schema import  PostCreate, PostUpdate

from pydantic import EmailStr
from starlette.exceptions import HTTPException
from fastapi import Depends, File, Form, status
import uuid
from sqlalchemy.orm import selectinload
from src.accounts.services import UserService


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
    

    async def CreatePost(self, 
                        #  user_uid:uuid.UUID, 
                         data: PostCreate, 
                         session: AsyncSession, 
                         user: User | None = None):
        # user =await UserService().fetch_user_by_email_or_uuid(session=session, key=user_uid)
        
        if data.date_posted is None:
            data.date_posted = date.today()
        post = Post(
            **(data.model_dump()),
            user_id=user.key
        )
        session.add(post)
        await session.commit()
        await session.refresh(post, attribute_names=['author'])
        return post
    
    async def full_update_post_by_uid(self, post_uid: uuid.UUID, data: PostCreate, session: AsyncSession ):
        post = await self.fetch_post_by_uid(post_uid=post_uid, session=session)
        
        
        for key , value in data.model_dump(exclude_unset=True).items():
            setattr(post, key, value)
        
        await session.commit()
        await session.refresh(post, attribute_names=['author'])
        return post
    

    async def update_post_patch(self,post_uid: uuid.UUID, data: PostUpdate, session: AsyncSession):
        post =await self.fetch_post_by_uid(post_uid=post_uid, session=session)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(post, k,v)
        await session.commit()
        await session.refresh(post)
        return post
    
    async def delete_posts(self, post_uid: uuid.UUID, session: AsyncSession):
        post =await self.fetch_post_by_uid(post_uid=post_uid, session=session)
        await session.delete(instance=post)
        await session.commit()