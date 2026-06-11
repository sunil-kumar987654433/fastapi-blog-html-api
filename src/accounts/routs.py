from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, status, Depends, status, File, UploadFile, Form, Cookie
import uuid
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from src.accounts.utils import JWT_TOKEN, create_access_token, decode_token
from src.db.database import get_session
from src.accounts.schema import UserCreate, UserResponse, UserLogin, Token
from typing import Annotated

from src.db.redis import add_jti_to_blocklist
from .services import UserService
from src.accounts.models import User
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from .dependancy import AccessTokenBearer, RefreshTokenBearer

user_service = UserService()
account_router = APIRouter()
account_html_router = APIRouter()
access_token_bearer = AccessTokenBearer()

templates = Jinja2Templates(directory="templates")

@account_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, name="register-new-user")
async def create_user(data: UserCreate, session: AsyncSession =  Depends(get_session)):
    """
        create user
    """
    if data.password1 != data.password2:
        raise HTTPException(
            detail="Both password must be eaual",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    result = await user_service.CreateUser(data, session)
    return result

@account_html_router.get("/register-user/", include_in_schema=False, name="register-user-form")
async def create_user_form(request: Request, session:AsyncSession =  Depends(get_session)):
    """
    login user form
    """
    context = {}
    return templates.TemplateResponse(
        request=request,
        name="register_user.html",
        context=context
    )


@account_router.post("/token-normal", name="get-token-url")
async def login_user(data: UserLogin, session: AsyncSession = Depends(get_session)):
    result = await user_service.create_login_user(data, session)
    max_age_refresh = str(int((result.get("refresh_token_detail")['expired_at'] - datetime.now(timezone.utc) ).total_seconds()))
    max_age_access = str(int((result.get("access_token_detail")['expired_at'] - datetime.now(timezone.utc) ).total_seconds()))

    response = JSONResponse(
        content={
            "access_token": result.get("access_token_detail")['access_token'],
            "access_token_expired": result.get("access_token_detail")['expired_time_indian'].isoformat(),
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=result.get("refresh_token_detail")['refresh_token'],
        max_age=max_age_refresh,
        secure=True,
        httponly=True,
        samesite="lax"
    )
    response.set_cookie(
        key="access_token",
        value=result.get("access_token_detail")['access_token'],
        max_age=max_age_access,
        secure=True,
        httponly=True,
        samesite="lax"
    )
    return response

async def get_current_user( session: AsyncSession = Depends(get_session), user_detail=Depends(access_token_bearer)):
    user_uid = user_detail.get("user")['sub']
    user = await user_service.fetch_user_by_email_or_uuid(key=user_uid, session=session)
    return user





async def get_current_user_optional(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    

    try:
        token = request.cookies.get(
            "access_token"
        )

        if decode_token(token) is False:
            return None
        payload = JWT_TOKEN().decode_data(token)
        user_uid = payload.get("user")["sub"]
        
        user = await user_service.fetch_user_by_email_or_uuid(session=session, key=user_uid)
        return user

    except Exception as e:
        print(e)
        return None
    


@account_router.get("/me")
async def current_user(
    request: Request
):
    current_user = request.state.user if request.state.user else None
    return UserResponse.model_validate(
        current_user
    )


@account_html_router.get("/login/", include_in_schema=False, name="login-user-form")
async def create_user_form(request: Request, session:AsyncSession =  Depends(get_session)):
    """
    login user form
    """
    context = {}
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=context
    )

@account_router.post("/{user_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def update_a_user(user_id: uuid.UUID, email: EmailStr | None = Form(default=None), image_file: UploadFile | None = File(default=None),  session: AsyncSession =  Depends(get_session)):
    """
        update user
    """

    result = await user_service.UpdateUser(
        user_id=user_id,
        email=email,
        image_file=image_file,
        session=session
    )
    return result


@account_html_router.patch("/upload-profile-image", name="update-user-image")
async def update_user_image(
    request: Request,
    image_file: UploadFile | None = File(default=None),  
    session: AsyncSession =  Depends(get_session)
    ):
    """
        update user for html
    """
    current_user = request.state.user
    if not current_user:
            raise HTTPException(
                detail="user not exist",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    # fetch again in THIS session
    db_user = await user_service.fetch_user_by_email_or_uuid(
        session=session,
        key=current_user.key
    )

    result = await user_service.UpdateUser_form(
        db_user,
        image_file,
        session,
    )


    return UserResponse.model_validate(current_user)

@account_html_router.get("/user-profile", name="user-profile")
async def user_profile(request: Request, session: AsyncSession =  Depends(get_session)):
    """
        user profile
    """
   
    if not request.state.user and request.state.user is None:
            raise HTTPException(
                detail="this user already exist",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    context = {
        "user": request.state.user,
        "title": 'user profile'
    }

    return templates.TemplateResponse(
        request=request,
        name="user-profile.html",
        context=context
    )

@account_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_user(user_id: uuid.UUID,  session: AsyncSession =  Depends(get_session)):
    """
        delete user
    """
    return await user_service.delete_user(user_id,  session)


@account_router.get("/", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def fetach_all_user(session: AsyncSession =  Depends(get_session)):
    """
        get all user
    """
   
    return await user_service.get_all_users(session)
    

@account_router.post("/{user_uuid}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_a_user(user_uuid: uuid.UUID, session: AsyncSession =  Depends(get_session)):
    """
        get any user by email or user uuid
    """
    return await user_service.GetAUser(user_uuid, session)







@account_html_router.get("/{user_key}/posts", include_in_schema=False, name='user_posts')
async def user_post_page(request: Request, user_key:uuid.UUID, session:AsyncSession =  Depends(get_session)):
    """
        particular post of user
    """
    result = await user_service.all_post_by_user(session=session, key=user_key)
    posts  =  result.get("posts")
    user = result.get("user")
    context = {
        "posts": posts,
        'user': user,
        'title': f"{user.email}'s posts"
    }
    return templates.TemplateResponse(
        request=request,
        name="user_posts.html",
        context=context
    )

@account_router.get("/{user_key}/posts")
async def user_post_page(user_uuid:uuid.UUID, session:AsyncSession =  Depends(get_session)):
    """
        all post of user
    """
    result = await user_service.all_post_by_user(session=session, key=user_uuid)
    posts = result.get("posts")
    return posts


@account_router.get("/refresh-token")
async def get_new_access_token(token_detauils: dict= Depends(RefreshTokenBearer()), session: AsyncSession = Depends(get_session)):
  
    user_uuid = token_detauils['user']['sub']
    user = await user_service.fetch_user_by_email_or_uuid(key=user_uuid, session=session)
    access_token_detail = create_access_token(user)
    return {
        "access_token_detail": access_token_detail
    }


@account_router.get("/logout")
async def revoke_token(token_detail: dict =Depends(access_token_bearer)):
    jti = token_detail.get("jti")
    await add_jti_to_blocklist(jti)

    response = JSONResponse(
        content={
            "message": "logout success"
        }
    )

    response.delete_cookie(
        key="refresh_token"
    )

    return response
