from src.config import Config
import jwt
from pwdlib.exceptions import PwdlibError
from pwdlib.hashers import argon2
from pwdlib import PasswordHash
from datetime import timedelta, datetime, timezone
import uuid
from fastapi import HTTPException, status
from src.accounts.models import User
from zoneinfo import ZoneInfo


class PASSLIB_CONFIGRATION:
    password_hash = PasswordHash.recommended()
    def create_password(self, password):
        return PASSLIB_CONFIGRATION.password_hash.hash(password)
    
    def verify_password(self, password, hash_password):
        return PASSLIB_CONFIGRATION.password_hash.verify( password, hash_password)

password_service = PASSLIB_CONFIGRATION()





class JWT_TOKEN:
    def encode_data(self, data: dict):        
        return jwt.encode(payload=data, key=Config.JWT_SECRET.get_secret_value(), algorithm=Config.JWT_ALGORITHM)
    
    def decode_data(self, decode_jwt):
        try:
            return jwt.decode(decode_jwt, key=Config.JWT_SECRET.get_secret_value(), 
                              algorithms=[Config.JWT_ALGORITHM],
                              )
        except jwt.ExpiredSignatureError:
            print("expired")
    
    def create_token(self, data: dict):
        encode_data = data.copy()
        encode_data['jti'] = f'{str(uuid.uuid4())}'
        return self.encode_data(data=encode_data)

def create_access_token(user: User):
    expired_time = datetime.now(timezone.utc) + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRY_MINUTE)
    user_detail = {   
            "user":{
                "sub":str(user.key),
                "email": str(user.email),
                "id": str(user.id),
                "role": str(user.user_role)
            },
            "type": 'access',
            "exp": expired_time
        }
    
    token = JWT_TOKEN().create_token(user_detail)
    if expired_time.tzinfo is None:
         expired_time = expired_time.replace(tzinfo=timezone.utc)
    expired_time_indian = expired_time.astimezone(ZoneInfo("Asia/Kolkata"))
    return {
        "access_token": token,
        "expired_at": expired_time,
        "expired_time_indian": expired_time_indian
    }

def create_refresh_token(user: User):
    expired_time = datetime.now(timezone.utc) + timedelta(days=Config.REFRESH_TOKEN_EXPIRY_DAYS)
    user_detail = {   
            "user":{
                "sub":str(user.key),
                "email": str(user.email),
                "id": str(user.id),
                "role": str(user.user_role)
            },
            "type": 'refresh',
            "exp": expired_time
        }
    
    token = JWT_TOKEN().create_token(user_detail)
    if expired_time.tzinfo is None:
         expired_time = expired_time.replace(tzinfo=timezone.utc)
    expired_time_indian = expired_time.astimezone(ZoneInfo("Asia/Kolkata"))
    return {
        "refresh_token": token,
        "expired_at": expired_time,
        "expired_time_indian": expired_time_indian
    }

def decode_token(token):
    payload = JWT_TOKEN().decode_data(token)
    if payload and type(payload) is dict and payload.get("user")['sub'] and payload.get("user")['id']:
        return True
    return False
    