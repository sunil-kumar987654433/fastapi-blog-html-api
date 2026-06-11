from fastapi.security import HTTPBearer
from fastapi import Request, status
from fastapi import HTTPException
from src.accounts.utils import decode_token
from src.accounts.utils import JWT_TOKEN
from src.db.redis import token_in_blocklist


class TokenBearer(HTTPBearer):
    def __init__(self, *, bearerFormat = None, scheme_name = None, description = None, auto_error = True):
        super().__init__(bearerFormat=bearerFormat, scheme_name=scheme_name, description=description, auto_error=auto_error)

    async def __call__(self, request: Request):
        cred = await super().__call__(request)
        token = cred.credentials.split(" ")[-1]
        if self.token_valid(token) is False:
            raise HTTPException(
                detail={
                    "error": "Token is is Invalid or expired.",
                    "resolution": "Please get new token"
                },
                status_code=status.HTTP_403_FORBIDDEN
            )
        token_data = JWT_TOKEN().decode_data(token)
        c = await token_in_blocklist(token_data['jti'])
        if c:
            raise HTTPException(
                detail={
                    "error": "Token is is Invalid or has been revoked.",
                    "resolution": "Please get new token"
                },
                status_code=status.HTTP_403_FORBIDDEN
            )

        self.verify_token_data(token_data)
        
        
        
        return token_data
    
    def token_valid(self, token):
        return decode_token(token)
    
    def verify_token_data(self, token_data):
        raise NotImplemented("Please override child class")
        


class AccessTokenBearer(TokenBearer):
    
    def verify_token_data(self, token_data: dict)->None:
        if token_data and token_data.get("type") != "access":
            raise HTTPException(
                detail="Please provide exact access token",
                status_code=status.HTTP_403_FORBIDDEN
            )

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict)->None:
        if token_data and token_data.get("type") != "refresh":
            raise HTTPException(
                detail="Please provide refresh token",
                status_code=status.HTTP_403_FORBIDDEN
            )