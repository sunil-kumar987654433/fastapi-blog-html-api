from fastapi import APIRouter, Request, HTTPException, status, Depends, status
import uuid
from fastapi.templating import Jinja2Templates
from .schema import PostCreate, PostResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from src.db.database import get_session
from src.accounts.schema import UserCreate, UserResponse, PostCreate, PostResponse
from typing import Annotated
from .services import UserService, PostService
from .models import User, Post




user_service = UserService()
post_service = PostService()

account_router = APIRouter()
templates = Jinja2Templates(directory="templates")



@account_router.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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

@account_router.post("/api/users/{user_uuid}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_a_user(user_uuid: uuid.UUID, session: AsyncSession =  Depends(get_session)):
    """
        get any user by email or user uuid
    """
    return await user_service.GetAUser(user_uuid, session)


@account_router.get("/api/posts", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def all_post(session:AsyncSession =  Depends(get_session)):
    """
        fetch all post
    """
    statement = select(Post)
    result = await session.execute(statement)
    return result.scalars().fetchall()

@account_router.get("/", include_in_schema=False, name="home")
async def home(request: Request, session:AsyncSession = Depends(get_session)):
    """
        show all post
    """
    statement = select(Post)
    result = await session.execute(statement)
    posts = result.scalars().fetchall()
    print("==================")
    print("==================")
    print(posts)
    print("==================")
    print("==================")
    print("==================")

    context = {
        "posts": posts,
        "title": 'Home'
    }
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=context
    )


@account_router.get("/posts/{post_uuid}", include_in_schema=False, name="post_detail")
async def post_by_key(request: Request, post_uuid:uuid.UUID, session:AsyncSession = Depends(get_session)):
    """
        get particular post by uuid
    """
    statement = select(Post).where(
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


@account_router.get("/users/{user_key}/posts", include_in_schema=False, name='user_posts')
async def user_post_page(request: Request, user_uuid:uuid.UUID, session:AsyncSession =  Depends(get_session)):
    """
        particular post of user
    """
    result = await user_service.all_post_by_user(session=session, key=user_uuid)
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

@account_router.get("/api/users/{user_key}/posts")
async def user_post_page(user_uuid:uuid.UUID, session:AsyncSession =  Depends(get_session)):
    """
        all post of user
    """
    print("user_uuid----", user_uuid)
    result = await user_service.all_post_by_user(session=session, key=user_uuid)
    posts = result.get("posts")
    return posts


@account_router.post("/api/posts", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(data: PostCreate, session: AsyncSession = Depends(get_session)):
    return await post_service.CreatePost(data, session)

@account_router.post("/api/posts/{post_uid}", status_code=status.HTTP_200_OK)
async def fetch_post_by_post_uid(post_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await post_service.fetch_post_by_uid(post_uid, session)