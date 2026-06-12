from fastapi import FastAPI
from fastapi import Request
from sqlalchemy import select
from src.accounts.models import User
from src.accounts.utils import JWT_TOKEN
from src.db.database import async_session
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
def register_middleware(app: FastAPI):


    app.add_middleware(
        CORSMiddleware, 
        # allow_origins = ["*"],
        allow_origins = ["http://begining.fun", "https://begining.fun"],
        allow_methods = ["*"],
        allow_headers = ['*'],
        allow_credentials = True
        )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts = [
            "begining.fun", 
            "www.begining.fun", 
            "168.144.185.166",
            "localhost",
            "127.0.0.1"
            ]
    )

    @app.middleware("http")
    async def inject_user(
        request: Request,
        call_next
        ):

        # default user
        request.state.user = None

        # skip static/media files
        path = request.url.path

        if (
            path.startswith("/static")
            or path.startswith("/media")
        ):

            response = await call_next(request)

            return response

        try:

            # get access token from cookies
            token = request.cookies.get(
                "access_token"
            )

            if token:

                # decode token
                payload = JWT_TOKEN().decode_data(
                    token
                )

                if payload:

                    user_uid = uuid.UUID(
                        payload["user"]["sub"]
                    )

                    # db session
                    async with async_session() as session:

                        statement = select(User).where(
                            User.key == user_uid
                        )

                        result = await session.execute(
                            statement
                        )

                        user = result.scalar_one_or_none()

                        # attach user to request
                        request.state.user = user

        except Exception as e:

            print("middleware error:", str(e))

            request.state.user = None

        # continue request
        response = await call_next(request)

        return response