from src.config import Config
import jwt
from passlib.hash import argon2


class PASSLIB_CONFIGRATION:
    def create_password(self, password):
        return argon2.hash(password)
    
    def verify_password(self, password, hash_password):
        return argon2.verify( password, hash_password)

password_service = PASSLIB_CONFIGRATION()