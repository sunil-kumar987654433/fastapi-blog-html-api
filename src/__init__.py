from fastapi import FastAPI, Request, status, Depends
from fastapi.staticfiles import StaticFiles
from src.accounts.routs import account_router, account_html_router
from src.post_app.routes import post_router, post_html_router
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from src.db.database import engine
from src.db.redis import redis_client
from .middleware import register_middleware
@asynccontextmanager
async def lifespan(app: FastAPI):
    # await init_db()
    print("start server...")
    yield
    engine.dispose()
    await redis_client.aclose()
    print("stop server...")




app = FastAPI()
register_middleware(app)
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory='media'), name='media')

app.include_router(account_router, tags=['account'], prefix='/api/users')
app.include_router(account_html_router, tags=['account'], prefix='/users')

app.include_router(post_router, tags=['post'], prefix='/api/posts')
app.include_router(post_html_router, tags=['post'])



@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):

    # API request
    if (
        "/api" in request.url.path
        or "application/json" in request.headers.get("accept", "")
    ):

        return await http_exception_handler(
            request,
            exc
        )

    # HTML request
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "request": request,
            "message": exc.detail
        },
        status_code=exc.status_code
    )


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):

    # API request
    if (
        "/api" in request.url.path
        or "application/json" in request.headers.get("accept", "")
    ):

        return await request_validation_exception_handler(
            request,
            exc
        )

    errors = []

    for err in exc.errors():

        field = ".".join(
            str(x)
            for x in err.get("loc", [])
        )

        message = err.get("msg", "")

        errors.append(f"{field}: {message}")

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "request": request,
            "message": "Invalid input",
            "errors": errors
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request: Request, exc: StarletteHTTPException):

#     messages = (
#         exc.detail if exc.detail else 'A errored occured. Please request and try again.'
#     )
#     if "/api" in request.url.path or "application/json" in request.headers.get("accept", ""):
#         return JSONResponse(
#             {"detail": messages},
#             status_code=exc.status_code
#         )

#     return templates.TemplateResponse(
#         request=request,
#         name="error.html",
#         context={
#             "request": request,
#             "message": messages
#         },
#         status_code=exc.status_code
#     )
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):

#     errors = []
#     for err in exc.errors():
#         field = ".".join(str(x) for x in err.get("loc", []))
#         message = err.get("msg", "")
#         errors.append(f"{field}: {message}")

#     # API response
#     if "/api" in request.url.path or "application/json" in request.headers.get("accept", ""):
#         return JSONResponse(
#             content={"detail": errors},
#             status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
#         )

#     return templates.TemplateResponse(
#         request=request,
#         name="error.html",
#         context={
#             "request": request,
#             "message": "Invalid input",
#             "errors": errors  
#         },
#         status_code=422
#     )
