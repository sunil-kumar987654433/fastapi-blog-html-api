from fastapi import FastAPI, Request, status, Depends
from fastapi.staticfiles import StaticFiles
from src.accounts.routs import account_router
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.templating import Jinja2Templates
from typing import Annotated
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("start server...")
    yield
    print("stop server...")



app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory='media'), name='media')

app.include_router(account_router, tags=['account'])





@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):

    messages = (
        exc.detail if exc.detail else 'A errored occured. Please request and try again.'
    )
    if "/api" in request.url.path or "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            {"detail": messages},
            status_code=exc.status_code
        )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "request": request,
            "message": messages
        },
        status_code=exc.status_code
    )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    errors = []
    for err in exc.errors():
        field = ".".join(str(x) for x in err.get("loc", []))
        message = err.get("msg", "")
        errors.append(f"{field}: {message}")

    # API response
    if "/api" in request.url.path or "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            content={"detail": errors},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "request": request,
            "message": "Invalid input",
            "errors": errors  
        },
        status_code=422
    )
