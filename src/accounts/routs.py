from fastapi import APIRouter, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from typing import TYPE_CHECKING
# # if TYPE_CHECKING:
# from src import templates
account_router = APIRouter()
templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "name": "sunil",
        "age":37
    },
    {
        "id": 2,
        "name": "ravi",
        "age":42
    },
]




@account_router.get("/posts", include_in_schema=False, name='home')
async def get_data(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="accounts/index.html",
        context={
            "request": request,
            "posts": posts,
            "title": "Index"
        }
    )
@account_router.get("/api/posts")
async def get_data_api():
    return posts


@account_router.get("/api/{post_id}", status_code=status.HTTP_200_OK)
async def post_page_api(post_id: int):
    for post in posts:
        if post['id'] == post_id:
            return post
    raise HTTPException(
        detail="post id not exist",
        status_code=status.HTTP_404_NOT_FOUND
    )

@account_router.get("/{post_id}", include_in_schema=False, name='post')
async def post_page(post_id: int, request: Request):
    for post in posts:
        if post['id'] == post_id:
            return templates.TemplateResponse(
                request=request,
                name="accounts/post.html",
                context={
                    "request": request,
                    "post": post,
                    "title": "post"
                }
            )

    raise HTTPException(
        status_code=404,
        detail="Post not exist"
    )