import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text, or_

from src.db.database import get_session
from .models import User, Post
from src.accounts.schema import UserCreate, PostCreate, PostUpdate, UserUpdate
from .utils import password_service
from pydantic import EmailStr
from starlette.exceptions import HTTPException
from fastapi import Depends, File, Form, status
import uuid
class UserService:
    async def get_all_users(self, session: AsyncSession):
        user = select(User)
        result = await session.execute(user)
        return result.scalars().all()

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
        try:
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
        
            return {
                "posts":user.posts,
                "user": user
            }
        except Exception as e:
            print(f"{str(e)}")
            raise HTTPException(
                detail=f"error: {str(e)}",
                status_code=status.HTTP_403_FORBIDDEN
            )

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
    
    async def UpdateUser(self, user_id: uuid.UUID, email: str | None = None, image_file: str | None = None,  session: AsyncSession = Depends(get_session)):
        user = await self.fetch_user_by_email_or_uuid(session=session, key=user_id)
        if not user:
            raise HTTPException(
                detail="this user already exist",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if email:
            if user.email != email:
                check_duplicate_email =  await self.fetch_user_by_email_or_uuid(session=session, email=email)
                
                if check_duplicate_email:
                    raise HTTPException(
                        detail="Email already exist",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                user.email = email
        if image_file:
            ext = image_file.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            base_image_dir = "media/profile_pics"
            file_path = os.path.join(
                base_image_dir, filename
            )
            #save image
            with open(file_path, 'wb') as buffer:
                buffer.write(await image_file.read())
            
            #old image file delete
            if user.image_file:
                print("old file---", user.image_file)
                old_path = os.path.join(
                    base_image_dir,
                    user.image_file
                )
                print("old_path=====", old_path)
                if os.path.exists(
                    old_path
                ):
                    print("is old_path=====", old_path)
                    os.remove(old_path)
            #save file
            user.image_file = filename


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
    
    async def full_update_post_by_uid(self, post_uid: uuid.UUID, data: PostCreate, session: AsyncSession ):
        post = await self.fetch_post_by_uid(post_uid=post_uid, session=session)
        
        
        for key , value in data.model_dump(exclude_unset=True).items():
            setattr(post, key, value)
        
        await session.commit()
        await session.refresh(post)
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