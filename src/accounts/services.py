import os
import io
import boto3
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageOps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text, or_, func
from botocore.exceptions import NoCredentialsError, ClientError
from src.db.database import get_session
from src.accounts.models import User
from src.post_app.models import Post
from src.accounts.schema import UserCreate, UserLogin, UserUpdate
from .utils import password_service, create_access_token, create_refresh_token
from pydantic import EmailStr
from starlette.exceptions import HTTPException
from fastapi import Depends, File, Form, UploadFile, status
import uuid
from sqlalchemy.orm import selectinload
from src.config import Config

class UserService:
    async def get_all_users(self, session: AsyncSession):
        user = select(User)
        result = await session.execute(user)
        return result.scalars().all()
    
    async def fetch_user_by_email_or_uuid_with_post(self, session: AsyncSession, email: EmailStr | None = None, key: uuid.UUID | None = None):
        statement  = select(User) \
            .options(selectinload(User.posts).selectinload(Post.author)) \
            .where(
            or_(
            User.email == email.lower() if email else False,
            User.key == key
            )
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def fetch_user_by_email_or_uuid(self, session: AsyncSession, email: EmailStr | None = None, key: uuid.UUID | None = None):
        statement  = select(User) \
            .where(
            or_(
            User.email == email.lower() if email else False,
            User.key == key
            )
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    
    async def create_login_user(self, data: UserLogin, session: AsyncSession):
        """
            signin user
        """
        user = await self.fetch_user_by_email_or_uuid(session=session, email=data.email)
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
        if not password_service.verify_password(data.password, user.hashed_password):
            raise HTTPException(
                detail="Invalid password",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = create_access_token(user=user)
        refresh_token = create_refresh_token(user=user)
        return {
            "access_token_detail": access_token,
            "refresh_token_detail": refresh_token,
        }
        
        
    
    async def all_post_by_user(self, session: AsyncSession, key: uuid.UUID):
        try:
            user = await self.fetch_user_by_email_or_uuid_with_post(session=session, key=key)
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
            email=data.email.lower(),
            hashed_password=password_service.create_password(data.password1)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    async def UpdateUser(self, user_id: uuid.UUID, email: EmailStr | None = None, image_file: str | None = None,  session: AsyncSession = Depends(get_session)):
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
                
                if os.path.exists(
                    old_path
                ):
                  
                    os.remove(old_path)
            #save file
            user.image_file = filename


        await session.commit()
        await session.refresh(user)
        return user
    
    async def delete_user(self, user_id: uuid.UUID,  session: AsyncSession):
        user = await self.fetch_user_by_email_or_uuid(session=session, key=user_id)
        if user is None:
            raise HTTPException(
                detail="user not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
 
        try:
            await session.delete(user)
            
            media_dir = 'media/profile_pics'
            if user.image_file:
                image_path = os.path.join(
                    media_dir,
                    user.image_file
                )
                if os.path.exists(image_path):
                    os.remove(image_path)
            await session.commit()
        except Exception as e:
            raise HTTPException(
                detail=f"error: {e}",
                status_code=status.HTTP_403_FORBIDDEN
            )



    async def GetAUser(self, user_uuid: uuid.UUID, session: AsyncSession):
        user = await self.fetch_user_by_email_or_uuid(session=session, key=user_uuid)
        if user is None:
            raise HTTPException(
                detail="this email already exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return user
    

    
    def _get_s3_client(self):
        return boto3.client(
            's3', 
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_S3_ACCESS_KEY.get_secret_value(),
            aws_secret_access_key=Config.AWS_S3_SECRET_KEY.get_secret_value(),
            endpoint_url=Config.S3_ENDPOINT_URL
        )
    
    async def UpdateUser_form(
        self,
        current_user,
        image_file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session)
    ):
        if not image_file.content_type.startswith("image/"):
            raise HTTPException(
                detail="File must be an Image",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            s3_client = self._get_s3_client()

            # 1. इमेज डेटा को रीड करें और Pillow में लोड करें
            file_bytes = await image_file.read()
            image = Image.open(io.BytesIO(file_bytes))
            
            # 2. EXIF के आधार पर इमेज का ओरिएंटेशन सीधा (Rotate) करें
            corrected_image = ImageOps.exif_transpose(image)
            
            # 3. सीधी की हुई इमेज को नए मेमोरी बफर (BytesIO) में सेव करें
            in_memory_file = io.BytesIO()
            file_format = image.format if image.format else "JPEG"
            corrected_image.save(in_memory_file, format=file_format)
            in_memory_file.seek(0) # पॉइंटर को वापस 0 पर लाएं ताकि S3 इसे पढ़ सके

            # 4. यूनिक नाम और S3 की (Path) तैयार करें
            ext = image_file.filename.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{ext}"
            s3_object_key = f"profile_pics/{file_name}"
            
            # 5. बहुत ज़रूरी सुधार: यहाँ image_file.file की जगह 'in_memory_file' अपलोड करें 
            s3_client.upload_fileobj(
                in_memory_file,  # <-- यह बदलाव सबसे ज़रूरी था
                Config.AWS_BUCKET_NAME,
                s3_object_key,
                ExtraArgs={
                    "ContentType": image_file.content_type 
                }
            )
            
            # 6. पुरानी प्रोफाइल इमेज को S3 से डिलीट करें
            if current_user.image_file:
                try:
                    old_s3_key = f"profile_pics/{current_user.image_file}"
                    s3_client.delete_object(
                        Bucket=Config.AWS_BUCKET_NAME,
                        Key=old_s3_key
                    )
                except Exception as e:
                    print(f"Old file delete failed: {e}") 
                    
            # 7. डेटाबेस में रिकॉर्ड सेव करें
            current_user.image_file = file_name
            session.add(current_user)
            await session.commit()
            await session.refresh(current_user)
            
            return current_user
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            image_file.file.close()