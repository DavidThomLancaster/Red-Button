from typing import Optional
import uuid
from Repositories.UserRepository import UserRepository
from fastapi import HTTPException, status
from Utils import AuthUtils
from Services.TokenService import TokenService


#_default_repo = UserRepository()

# Imagine this is your in-memory database for now



class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, email: str, password: str) -> str:
        if self.user_repo.find_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")
        password_hashed = AuthUtils.hash_password(password)
        user_id =  self.user_repo.create_user(email, password_hashed)
        return TokenService.create_token(user_id)

    def login(self, email: str, password: str) -> str:
        user = self.user_repo.find_by_email(email)
        if not user or not AuthUtils.verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return TokenService.create_token(user["user_id"])
 
    def get_user_id_from_token(token):
        pass
        # TODO...