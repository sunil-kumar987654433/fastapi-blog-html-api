from fastapi import APIRouter, Request, HTTPException, status, Depends, status, File, UploadFile, Form, Body
import uuid
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from src.accounts.models import User
from src.accounts.services import UserService
from src.accounts.utils import JWT_TOKEN
from src.db.database import get_session
from src.post_app.schema import PostCreate, PostResponse, PostUpdate
from typing import Annotated
from src.accounts.dependancy import AccessTokenBearer, RefreshTokenBearer
from src.accounts.routs import get_current_user, get_current_user_optional
from sqlalchemy.orm import selectinload
from src.post_app.models import Post
from src.post_app.services import PostService

post_service = PostService()
access_token_bearar = AccessTokenBearer()
post_router = APIRouter()
post_html_router = APIRouter()

templates = Jinja2Templates(directory="templates")


@post_router.get("/", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def fetch_all_post(session:AsyncSession =  Depends(get_session)):
    """
        fetch all post
    """
    statement = select(Post).options(selectinload(Post.author))
    result = await session.execute(statement)
    return result.scalars().fetchall()




@post_html_router.get("/", include_in_schema=False, name="home")
async def home(
    request: Request, 
    session:AsyncSession = Depends(get_session),

    ):
    """
        show all post
    """
    print("current_user----", request.state.user)
    statement = select(Post).options(selectinload(Post.author))
    result = await session.execute(statement)
    posts = result.scalars().fetchall()

    context = {
        "posts": posts,
        "title": 'Home',
        "current_user": request.state.user
    }
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=context
    )


@post_html_router.get("/posts/{post_uuid}", include_in_schema=False, name="post_detail")
async def post_by_key(
    request: Request, 
    post_uuid:uuid.UUID, 
    session:AsyncSession = Depends(get_session), 
    # current_user: User = Depends(get_current_user)
    ):
    """
        get particular post by uuid
    """
    statement = select(Post) \
    .options(selectinload(Post.author)) \
    .where(
        Post.key == post_uuid
    )
    result = await session.execute(statement)
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    context = {
        "post": post,
        "title": post.title[:20]
    }
    return templates.TemplateResponse(
        request=request,
        name="post.html",
        context=context
    )


@post_router.post("/", name="create-post")
async def create_post(request: Request, data: PostCreate, 
                      session: AsyncSession = Depends(get_session), 
                    #   user_detail=Depends(access_token_bearar)
                      ):
    
    # user_uid = uuid.UUID(user_detail.get("user")['sub'])
    current_user = request.state.user

    if current_user is None:
            raise HTTPException(
                detail="user not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
    if current_user.is_active is False:
        raise HTTPException(
            detail="Inactive user.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return await post_service.CreatePost(
        # user_uid, 
        data, 
        session, 
        current_user
        )


@post_router.get("/{post_uid}", status_code=status.HTTP_200_OK, response_model=PostResponse)
async def fetch_post_by_post_uid(post_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await post_service.fetch_post_by_uid(post_uid, session)


@post_router.put("/{post_uid}", status_code=status.HTTP_200_OK, response_model=PostResponse)
async def update_post_full(post_uid: uuid.UUID, data: PostCreate, session: AsyncSession = Depends(get_session), user_detail=Depends(access_token_bearar)):
    return await post_service.full_update_post_by_uid(post_uid = post_uid, session=session, data=data)


@post_router.patch("/{post_uid}", status_code=status.HTTP_200_OK, response_model=PostResponse)
async def update_post_patch(post_uid: uuid.UUID, data: PostUpdate, session: AsyncSession = Depends(get_session), user_detail=Depends(access_token_bearar)):
    return await post_service.update_post_patch(post_uid, data, session)


@post_router.delete("/{post_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def update_post_patch(post_uid: uuid.UUID, session: AsyncSession = Depends(get_session), user_detail=Depends(access_token_bearar)):
    return await post_service.delete_posts(post_uid, session)
